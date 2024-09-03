# argo-workflows

Bootstraps an Argo Workflows and Argo Events deployment on minikube using skaffold

## Requirements

* Minikube [installation](https://minikube.sigs.k8s.io/docs/start/?arch=%2Flinux%2Fx86-64%2Fstable%2Fbinary+download)
* skaffold [installation](https://skaffold.dev/docs/install/#standalone-binary)

## Setup

Start your minikube cluster:

```
minikube start
```

Create the `ns1` namespace:

```
kubectl create namespace ns1
```

Install Argo Workflows and Events:

```
skaffold dev
```

Wait for the deployment to stabilize, the logs will show:

```
Completed post-deploy hooks
Port forwarding service/argo-server in namespace ns1, remote port 2746 -> http://127.0.0.1:2746
Port forwarding service/minio in namespace ns1, remote port 9000 -> http://127.0.0.1:9000
Port forwarding service/minio in namespace ns1, remote port 9001 -> http://127.0.0.1:9001
No artifacts found to watch
Press Ctrl+C to exit
Watching for changes...
```

Open the browser on http://127.0.0.1:2746 to access the Argo UI
Open the browser on http://127.0.0.1:9001 to access the Minio console (minio-admin/minio-admin)


## Using the API 

See the example below:

```
ARGO_TOKEN="Bearer $(kubectl get -n ns1 secret argo.service-account-token -o=jsonpath='{.data.token}' | base64 --decode)"

curl --insecure http://0.0.0.0:2746/api/v1/workflows/ns1 -H "Authorization: $ARGO_TOKEN"
```

## Event bus

Deploy the event bus with:

```
kubectl apply -n ns1 -f events/event-bus.yaml
```

**Note**: To delete the event bus you may have to set the event bus `finalizers` to `[]`

## Getting started with Argo Workflows

Follow the tutorials below:

- [Learn Argo Workflows with 8 Simple Examples](https://codefresh.io/learn/argo-workflows/learn-argo-workflows-with-8-simple-examples/)
- [Argo WorkflowTemplates: Types, Examples & Basic Operations](https://codefresh.io/learn/argo-workflows/argo-workflowtemplates/)