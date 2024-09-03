#!/bin/bash

ARGO_WORKFLOWS_VERSION="3.5.5"

mkdir -p manifests/crds
mkdir -p manifests/namespaced
mkdir -p manifests/cluster

manifest_url="https://github.com/argoproj/argo-workflows/releases/download/v${ARGO_WORKFLOWS_VERSION}/namespace-install.yaml"

# get the CRDs
curl -L $manifest_url | yq e 'select(.kind == "CustomResourceDefinition")' - > manifests/crds/argo-workflows-crds.yaml

# get the namespaced manifests
curl -L $manifest_url | yq e 'select(.kind != "CustomResourceDefinition")' - > manifests/namespaced/argo-workflows-namespaced.yaml

# add the namespaced flag (and auth-mode) to the argo-server and workflow-controller
yq e 'select(.kind == "Deployment" and .metadata.name == "argo-server").spec.template.spec.containers[0].args = ["server", "--auth-mode=server", "--namespaced", "--secure=false"]' -i manifests/namespaced/argo-workflows-namespaced.yaml
yq e 'select(.kind == "Deployment" and .metadata.name == "argo-server").spec.template.spec.containers[0].env = [
      { "name": "FIRST_TIME_USER_MODAL", "value": "false" },
      { "name": "FEEDBACK_MODAL", "value": "false" },
      { "name": "NEW_VERSION_MODAL", "value": "false" }
    ]' -i manifests/namespaced/argo-workflows-namespaced.yaml
yq e 'select(.kind == "Deployment" and .metadata.name == "argo-server").spec.template.spec.containers[0].readinessProbe.httpGet.scheme ="HTTP"' -i manifests/namespaced/argo-workflows-namespaced.yaml
yq e 'select(.kind == "Deployment" and .metadata.name == "workflow-controller").spec.template.spec.containers[0].args = ["--namespaced"]' -i manifests/namespaced/argo-workflows-namespaced.yaml

# argo events
ARGO_EVENTS_VERSION="1.9.1"
manifest_url="https://github.com/argoproj/argo-events/releases/download/v${ARGO_EVENTS_VERSION}/namespace-install.yaml"

# get the CRDs
curl -L $manifest_url | yq e 'select(.kind == "CustomResourceDefinition")' - > manifests/crds/argo-events-crds.yaml

# get the namespaced manifests
curl -L $manifest_url | yq e 'select(.kind != "CustomResourceDefinition")' - > manifests/namespaced/argo-events-namespaced.yaml

ns="ns1"
ns="${ns}" yq e '.metadata.namespace = env(ns)' -i manifests/namespaced/argo-events-namespaced.yaml
ns="${ns}" yq e 'select(.kind == "RoleBinding").subjects[].namespace = env(ns)' -i manifests/namespaced/argo-events-namespaced.yaml
