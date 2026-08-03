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

### Tests

```bash
k create namespace test
k run test --image=curlimages/curl -n test --create-namespace --command -- sleep 3600
k exec --it pod/test -n test -- /bin/sh
curl http://api-hello.backend.svc.cluster.local
```
