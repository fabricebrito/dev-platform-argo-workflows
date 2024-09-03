# Argo Workflows CWL Runner

This folder contains an example of an Argo Workflows CWL runner.

There are two sub-folders: 

* `argo-cwl-runner`: a Helm chart deploying an Argo Workflows WorkflowTemplate implemented as a generic WorkflowTemplate that:

* Takes a CWL document encoded in JSON and a set of input parameters encoded as JSON
* Saves the CWL document and input parameters to the RWX volume `/calrissian`
* Create a kubernetes Job invoking `calrissian`
* Gets the `calrissian` stdout, stderr and execution report (resource consumption)
* Creates artifacts for the tool logs and calrissian stdout, stderr and execution report
* Invokes a stage out step to stage the STAC Catalog to an S3 object storage

The `argo-cwl-runner` input parameteres are: 

* `parameters`: a JSON containing the CWL input parameters
* `cwl`: a JSON containing the CWL document
* `max_ram`: the maximum amount of RAM to use for processing the CWL document on kubernetes
* `max_cores`: the maximum number of cores to use for processing the CWL document on kubernetes

The `argo-cwl-runner` output parameters are:

* `results` with the expression: `"steps['argo-cwl'].outputs.parameters['results']"`
* `logs` with the expression: `"steps['argo-cwl'].outputs.parameters['logs']"`
* `usage-report` with the expression: `"steps['argo-cwl'].outputs.parameters['usage-report']"`
* `stac-catalog` with the expression: `"steps['argo-cwl'].outputs.parameters['stac-catalog']"`
       
The `argo-cwl-runner` workflow produce the artifacts:

* `tool-logs` with the expression `"steps['argo-cwl'].outputs.artifacts['tool-logs']"`
* `calrissian-output` with the expression `"steps['argo-cwl'].outputs.artifacts['calrissian-output']"`
* `calrissian-stderr` with the expression `"steps['argo-cwl'].outputs.artifacts['calrissian-stderr']"`
* `calrissian-report` with the expression `"steps['argo-cwl'].outputs.artifacts['calrissian-report']"`

The `argo-cwl-runner` WorkflowTemplate can be used in an Workflow with, e.g.: 

```yaml
- name: argo-cwl # this steps invokes a WorkflowTemplate
  templateRef: 
    name: argo-cwl-runner
    template: calrissian-runner
  arguments:
    parameters:
    - name: max_ram
      value: "{{ .Values.maxRam }}"
    - name: max_cores
      value: "{{ .Values.maxCores }}"
    - name: parameters
      value: {{ `"{{steps.prepare.outputs.parameters.inputs}}"` }}
    - name: cwl
      value: {{ `"{{steps.prepare.outputs.parameters.workflow}}"` }}
```

## Water bodies detection example


`spec.parameters` contains the list of the application package inputs defined as:

```yaml
- name: <parameter name>
  value: <parameter default value>
```

* `main` template

The **main** template, `spec.templates[0]`, orchestrates the processing steps.

`spec.templates[0].inputs.parameters` contains the list of parameters' names.

`spec.templates[0].steps[0][0].arguments.parameters` contains the list of parameters defined as:

```yaml
- name: <parameter name>
  value: {{ `"{{inputs.parameters.<parameter name>}}"` }}
```

* `prepare` template

The **prepare** template, `spec.templates[1]`, prepares the input parameters and is invoked as a processing step in the `main` template.

`spec.templates[1].inputs.parameters` contains the list of parameters' names.

`spec.templates[1].script.source` contains a bash script that produces two files (outputs):

  * `/tmp/cwl_parameters.json`: a JSON file with the input parameters and their values.
  * `/tmp/cwl_workflow.json`: a JSON file with the Application Package. In this example, we chose to mount the Application Package as a ConfigMap and simply copy its content to `/tmp/cwl_workflow.json`.

* `validate-inputs` template

The **validate-inputs** template, `spec.templates[2]`, validates the input values against the Application Package input parameters JSON schema. This schema is mounted on the pod as a ConfigMap.

`spec.templates[2].script.source` contains a Python code that validates the input parameters against the provided JSON schema.

## Running the example

* Open the Argo Workflows workflow template user interface at: http://127.0.0.1:2746/workflow-templates?namespace=ns1. Inspect the two workflow templates listed
* The open the _water-bodies-detection_ workflow template user interface: http://127.0.0.1:2746/workflow-templates/ns1/water-bodies-detection
* Click **"+ Submit"**
* Under **Entrypoint**, select `main`
* Under **Parameters**, provide the values:
  * items: `["https://earth-search.aws.element84.com/v0/collections/sentinel-s2-l2a-cogs/items/S2A_10TFK_20210708_0_L2A"]`
  * aoi: `-121.399,39.834,-120.74,40.472`
  * epsg: `EPSG:4326`
* Click **"+ Submit"** to submit the workflow
* Wait for the processing to end
* Click the first workflow element
* Click **INPUTS/OUTPUTS**
* Inspect the outputs and artifacts













Deploy the workflow template with:

```
kubectl apply -n ns1 -f argo-calrissian.yaml
```


## Using the Argo Workflows API

Get the token and verify it:

```
ARGO_TOKEN="Bearer $(kubectl get -n ns1 secret argo.service-account-token -o=jsonpath='{.data.token}' | base64 --decode)"

curl --insecure http://0.0.0.0:2746/api/v1/workflows/ns1 -H "Authorization: $ARGO_TOKEN"
```

Now submit an instance of a Workflow Template;

```
JSON_PARAM='{"stac_items":["https://earth-search.aws.element84.com/v0/collections/sentinel-s2-l2a-cogs/items/S2A_10TFK_20210708_0_L2A"],"aoi":"-121.399,39.834,-120.74,40.472","epsg":"EPSG:4326"}'
ESCAPED_JSON_PARAM=$(echo $JSON_PARAM | sed 's/"/\\"/g')

curl --insecure \
    -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: $ARGO_TOKEN" \
    -d '{
          "namespace": "ns1",
          "resourceKind": "WorkflowTemplate",
          "resourceName": "water-bodies-detection",
          "submitOptions": {
            "parameters": [
              "parameters='"$ESCAPED_JSON_PARAM"'"
            ]
          }
        }' \
    http://0.0.0.0:2746/api/v1/workflows/ns1/submit
```

Using a JSON parameters file:

```
JSON_PARAM=$(jq -c . params.json | sed 's/"/\\"/g')

curl --insecure \
    -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: $ARGO_TOKEN" \
    -d '{
          "namespace": "ns1",
          "resourceKind": "WorkflowTemplate",
          "resourceName": "water-bodies-detection",
          "submitOptions": {
            "parameters": [
              "parameters='"$JSON_PARAM"'"
            ]
          }
        }' \
    http://0.0.0.0:2746/api/v1/workflows/ns1/submit
```



Convert the CWL to json

```
JSON_CWL=$( curl -L "https://github.com/eoap/mastering-app-package/releases/download/1.0.0/app-water-bodies-cloud-native.1.0.0.cwl" | yq e . -o=json - | jq -c . - | sed 's/"/\\"/g')
JSON_PARAM=$(jq -c . params.json | sed 's/"/\\"/g')

curl --insecure \
    -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: $ARGO_TOKEN" \
    -d '{
          "namespace": "ns1",
          "resourceKind": "WorkflowTemplate",
          "resourceName": "argo-cwl-runner",
          "submitOptions": {
            "parameters": [
              "parameters='"$JSON_PARAM"'", 
              "cwl='"$JSON_CWL"'"
            ]
          }
        }' \
    http://0.0.0.0:2746/api/v1/workflows/ns1/submit
```



JSON_CWL=$( curl -L "https://github.com/eoap/mastering-app-package/releases/download/1.0.0/app-water-bodies-cloud-native.1.0.0.cwl" | yq e . -o=json - | jq -c . - | sed 's/"/\\"/g')
JSON_PARAM=$(jq -c . params.json | sed 's/"/\\"/g')
VOLUME="15Gi"

curl --insecure \
    -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: $ARGO_TOKEN" \
    -d '{
          "namespace": "ns1",
          "resourceKind": "WorkflowTemplate",
          "resourceName": "argo-cwl-runner",
          "submitOptions": {
            "parameters": [
              "parameters='"$JSON_PARAM"'", 
              "cwl='"$JSON_CWL"'", 
              "max_ram='"16G"'",
              "max_cores='"1"'"
            ]
          }
        }' \
    http://0.0.0.0:2746/api/v1/workflows/ns1/submit


  ## Get information about a completed workflow

  ```
  WF_ID="argo-cwl-runner-wvqmw"

  curl --insecure \
    -H "Authorization: $ARGO_TOKEN" \
    http://0.0.0.0:2746/api/v1/workflows/ns1/${WF_ID} > workflow.json



{"stac_items":["https://earth-search.aws.element84.com/v0/collections/sentinel-s2-l2a-cogs/items/S2A_10TFK_20210708_0_L2A"],"aoi":"-121.399,39.834,-120.74,40.472","epsg":"EPSG:4326"}


{"cwlVersion":"v1.0","$namespaces":{"s":"https://schema.org/"},"s:softwareVersion":"1.0.0","schemas":["http://schema.org/version/9.0/schemaorg-current-http.rdf"],"$graph":[{"class":"Workflow","id":"main","label":"Water bodies detection based on NDWI and otsu threshold","doc":"Water bodies detection based on NDWI and otsu threshold applied to Sentinel-2 COG STAC items","requirements":[{"class":"ScatterFeatureRequirement"},{"class":"SubworkflowFeatureRequirement"}],"inputs":{"aoi":{"label":"area of interest","doc":"area of interest as a bounding box","type":"string"},"epsg":{"label":"EPSG code","doc":"EPSG code","type":"string","default":"EPSG:4326"},"stac_items":{"label":"Sentinel-2 STAC items","doc":"list of Sentinel-2 COG STAC items","type":"string[]"},"bands":{"label":"bands used for the NDWI","doc":"bands used for the NDWI","type":"string[]","default":["green","nir"]}},"outputs":[{"id":"stac_catalog","outputSource":["node_stac/stac_catalog"],"type":"Directory"}],"steps":{"node_water_bodies":{"run":"#detect_water_body","in":{"item":"stac_items","aoi":"aoi","epsg":"epsg","bands":"bands"},"out":["detected_water_body"],"scatter":"item","scatterMethod":"dotproduct"},"node_stac":{"run":"#stac","in":{"item":"stac_items","rasters":{"source":"node_water_bodies/detected_water_body"}},"out":["stac_catalog"]}}},{"class":"Workflow","id":"detect_water_body","label":"Water body detection based on NDWI and otsu threshold","doc":"Water body detection based on NDWI and otsu threshold","requirements":[{"class":"ScatterFeatureRequirement"}],"inputs":{"aoi":{"doc":"area of interest as a bounding box","type":"string"},"epsg":{"doc":"EPSG code","type":"string","default":"EPSG:4326"},"bands":{"doc":"bands used for the NDWI","type":"string[]"},"item":{"doc":"STAC item","type":"string"}},"outputs":[{"id":"detected_water_body","outputSource":["node_otsu/binary_mask_item"],"type":"File"}],"steps":{"node_crop":{"run":"#crop","in":{"item":"item","aoi":"aoi","epsg":"epsg","band":"bands"},"out":["cropped"],"scatter":"band","scatterMethod":"dotproduct"},"node_normalized_difference":{"run":"#norm_diff","in":{"rasters":{"source":"node_crop/cropped"}},"out":["ndwi"]},"node_otsu":{"run":"#otsu","in":{"raster":{"source":"node_normalized_difference/ndwi"}},"out":["binary_mask_item"]}}},{"class":"CommandLineTool","id":"crop","requirements":{"InlineJavascriptRequirement":{},"EnvVarRequirement":{"envDef":{"PATH":"/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin","PYTHONPATH":"/app"}},"ResourceRequirement":{"coresMax":1,"ramMax":512}},"hints":{"DockerRequirement":{"dockerPull":"ghcr.io/eoap/mastering-app-package/crop@sha256:61c2f37b3a1bd56a3eddd0f4224c72de665d42957d3325dd0397845cff198dab"}},"baseCommand":["python","-m","app"],"arguments":[],"inputs":{"item":{"type":"string","inputBinding":{"prefix":"--input-item"}},"aoi":{"type":"string","inputBinding":{"prefix":"--aoi"}},"epsg":{"type":"string","inputBinding":{"prefix":"--epsg"}},"band":{"type":"string","inputBinding":{"prefix":"--band"}}},"outputs":{"cropped":{"outputBinding":{"glob":"*.tif"},"type":"File"}}},{"class":"CommandLineTool","id":"norm_diff","requirements":{"InlineJavascriptRequirement":{},"EnvVarRequirement":{"envDef":{"PATH":"/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin","PYTHONPATH":"/app"}},"ResourceRequirement":{"coresMax":1,"ramMax":512}},"hints":{"DockerRequirement":{"dockerPull":"ghcr.io/eoap/mastering-app-package/norm_diff@sha256:641ab55968d7f500b641969d0a7422c4c9a80dd5cc1459ee07f3e0c5ee4fa230"}},"baseCommand":["python","-m","app"],"arguments":[],"inputs":{"rasters":{"type":"File[]","inputBinding":{"position":1}}},"outputs":{"ndwi":{"outputBinding":{"glob":"*.tif"},"type":"File"}}},{"class":"CommandLineTool","id":"otsu","requirements":{"InlineJavascriptRequirement":{},"EnvVarRequirement":{"envDef":{"PATH":"/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin","PYTHONPATH":"/app"}},"ResourceRequirement":{"coresMax":1,"ramMax":512}},"hints":{"DockerRequirement":{"dockerPull":"ghcr.io/eoap/mastering-app-package/otsu@sha256:ec02baf6a007ebb5a2dc037af2da8ef94db67bb8a6139682ad61041f9d27c779"}},"baseCommand":["python","-m","app"],"arguments":[],"inputs":{"raster":{"type":"File","inputBinding":{"position":1}}},"outputs":{"binary_mask_item":{"outputBinding":{"glob":"*.tif"},"type":"File"}}},{"class":"CommandLineTool","id":"stac","requirements":{"InlineJavascriptRequirement":{},"EnvVarRequirement":{"envDef":{"PATH":"/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin","PYTHONPATH":"/app"}},"ResourceRequirement":{"coresMax":1,"ramMax":512}},"hints":{"DockerRequirement":{"dockerPull":"ghcr.io/eoap/mastering-app-package/stac@sha256:8ad7e7d6999c0c4c91c2b19ce231f24734d2af8f41b855ef9a06276d23345601"}},"baseCommand":["python","-m","app"],"arguments":[],"inputs":{"item":{"type":{"type":"array","items":"string","inputBinding":{"prefix":"--input-item"}}},"rasters":{"type":{"type":"array","items":"File","inputBinding":{"prefix":"--water-body"}}}},"outputs":{"stac_catalog":{"outputBinding":{"glob":"."},"type":"Directory"}}}],"s:codeRepository":{"URL":"https://github.com/eoap/mastering-app-package.git"},"s:author":[{"class":"s:Person","s.name":"Jane Doe","s.email":"jane.doe@acme.earth","s.affiliation":"ACME"}]}