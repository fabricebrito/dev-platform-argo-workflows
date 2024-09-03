ARGO_TOKEN="Bearer $(kubectl get -n ns1 secret argo.service-account-token -o=jsonpath='{.data.token}' | base64 --decode)"

echo $ARGO_TOKEN


