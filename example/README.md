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

