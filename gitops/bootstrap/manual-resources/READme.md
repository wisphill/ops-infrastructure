```
kustomize build --enable-alpha-plugins gitops/bootstrap/manual-resources | kubectl apply -f -  --dry-run=client
```
