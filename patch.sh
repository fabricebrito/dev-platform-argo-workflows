kubectl patch deployment \
		argo-server \
		--namespace ns1 \
		--type='json' \
		-p='[{"op": "replace", "path": "/spec/template/spec/containers/0/args", "value": [
            "server",
            "--auth-mode=server",
            "--secure=false", 
            "--namespaced"
    ]},
    {"op": "replace", "path": "/spec/template/spec/containers/0/readinessProbe/httpGet/scheme", "value": "HTTP"},
    {"op": "add", "path": "/spec/template/spec/containers/0/env", "value": [
      { "name": "FIRST_TIME_USER_MODAL", "value": "false" },
      { "name": "FEEDBACK_MODAL", "value": "false" },
      { "name": "NEW_VERSION_MODAL", "value": "false" }
    ]}
    ]' >/dev/null