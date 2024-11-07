""" Main module for the application. """

import os
import shutil

import boto3
import botocore
import click
import pystac
from botocore.client import Config
from loguru import logger
from pystac.stac_io import StacIO
from datetime import datetime
import sys
from app.stac import CustomStacIO, upload_file_with_chunk_size
from app.usersettings import UserSettings
from pystac.extensions.item_assets import ItemAssetsExtension, AssetDefinition


@click.command()
@click.option(
    "--stac-catalog",
    help="Local path to a folder containing catalog.json STAC Catalog",
    required=True,
)
@click.option("--user-settings", help="S3 user settings", required=True)
@click.option("--bucket", "bucket", help="S3 bucket", required=True)
@click.option("--subfolder", "subfolder", help="S3 subfolder", required=True)
def main(stac_catalog, user_settings, bucket, subfolder):
    user_settings_config = UserSettings.from_file(user_settings)

    s3_settings = user_settings_config.get_s3_settings(f"s3://{bucket}/{subfolder}")

    if not s3_settings:
        raise ValueError("No S3 settings found for this bucket")

    # set the environment variables for S3 from the user settings
    os.environ["aws_access_key_id"] = s3_settings["aws_access_key_id"]
    os.environ["aws_secret_access_key"] = s3_settings["aws_secret_access_key"]
    os.environ["aws_region_name"] = s3_settings["region_name"]
    os.environ["aws_endpoint_url"] = s3_settings["endpoint_url"]

    client = boto3.client(
        "s3",
        **s3_settings,
        config=Config(s3={"addressing_style": "path", "signature_version": "s3v4"}),
    )

    shutil.copytree(stac_catalog, "/tmp/catalog")
    cat = pystac.read_file(os.path.join("/tmp/catalog", "catalog.json"))

    StacIO.set_default(CustomStacIO)

    # create a STAC collection for the process
    collection_id = subfolder
    date = datetime.now().strftime("%Y-%m-%d")

    dates = [
        datetime.strptime(f"{date}T00:00:00", "%Y-%m-%dT%H:%M:%S"),
        datetime.strptime(f"{date}T23:59:59", "%Y-%m-%dT%H:%M:%S"),
    ]

    collection = pystac.Collection(
        id=collection_id,
        description="description",
        extent=pystac.Extent(
            spatial=pystac.SpatialExtent([[-180, -90, 180, 90]]),
            temporal=pystac.TemporalExtent(intervals=[[min(dates), max(dates)]]),
        ),
        title="Processing results",
        href=f"s3://{bucket}/{subfolder}/collection.json",
        stac_extensions=[],
        keywords=["eoepca"],
        license="proprietary",
    )

    for item in cat.get_items():

        item.set_collection(collection)

        collection.add_item(item)

        for key, asset in item.get_assets().items():
            s3_path = os.path.normpath(
                os.path.join(os.path.join(subfolder, item.id, asset.href))
            )
            logger.info(f"upload {asset.href} to s3://{bucket}/{s3_path}")

            upload_file_with_chunk_size(
                client, asset.get_absolute_href(), bucket, s3_path
            )

            asset.href = f"s3://{bucket}/{s3_path}"
            item.add_asset(key, asset)

        for index, link in enumerate(item.links):
            if link.rel in ["root"]:
                item.links.pop(index)

    collection.update_extent_from_items()

    # Access the item-assets extension
    item_assets_ext = ItemAssetsExtension.ext(collection, add_if_missing=True)
    if ItemAssetsExtension.get_schema_uri() not in collection.stac_extensions:
        collection.stac_extensions.append(ItemAssetsExtension.get_schema_uri())

    item_assets = {}
    for item in collection.get_items():
        # Loop over the assets in the item and create AssetDefinitions for each
        for asset_key, asset in item.assets.items():
            # Create AssetDefinition from existing asset properties
            # remove the statistics and histogram from the extra fields (raster extension)
            asset.extra_fields["raster:bands"][0].pop("statistics")
            asset.extra_fields["raster:bands"][0].pop("histogram")
            asset_definition = AssetDefinition.create(
                title=asset.title,
                description=asset.description,
                media_type=asset.media_type,
                roles=asset.roles,
                extra_fields=asset.extra_fields,
            )
            # Add the asset definition to the collection's item assets
            item_assets[asset_key] = asset_definition

    item_assets_ext.item_assets = item_assets

    cat.clear_items()

    cat.add_child(collection)

    cat.normalize_hrefs(f"s3://{bucket}/{subfolder}")

    for item in collection.get_items():
        for index, link in enumerate(item.links):
            if link.rel in ["root"]:
                item.links.pop(index)
        # upload item to S3
        logger.info(f"upload {item.id} to s3://{bucket}/{subfolder}")
        pystac.write_file(item, item.get_self_href())

    # upload collection to S3
    logger.info(f"upload collection.json to s3://{bucket}/{subfolder}")
    for index, link in enumerate(collection.links):
        if link.rel in ["root"]:
            collection.links.pop(index)
    pystac.write_file(collection, collection.get_self_href())

    # upload catalog to S3
    logger.info(f"upload catalog.json to s3://{bucket}/{subfolder}")
    for index, link in enumerate(cat.links):
        if link.rel in ["root"]:
            cat.links.pop(index)
    pystac.write_file(cat, cat.get_self_href())

    logger.info("Done!")

    print(f"s3://{bucket}/{subfolder}/catalog.json", file=sys.stdout)


if __name__ == "__main__":
    main()
