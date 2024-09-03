ARGO_TOKEN="Bearer $(kubectl get -n ns1 secret argo.service-account-token -o=jsonpath='{.data.token}' | base64 --decode)"

curl --insecure https://0.0.0.0:2746/api/v1/workflows/ns1 -H "Authorization: $ARGO_TOKEN"
