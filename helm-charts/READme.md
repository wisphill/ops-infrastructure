### Commands

```bash
helm upgrade --install api-hello ./api-hello --namespace backend --create-namespace
helm dependency build
# rollback
helm rollback api-hello 1 -n backend
# list versions that're stored in the K8S secrets
helm history api-hello -n backend
# uninstall
helm uninstall api-hello -n backend
```
