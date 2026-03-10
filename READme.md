### To do tasks

- Backup /etcd
- Add statefulset application
- Add role/role binding resource and testing
- Testing helm
- Add Grafana & datasources
- Add Telemetry
- Istio testing with Istio Bookinfo
- Host Bitwarden for internal use with Tailscale
- Build gateway for game
- Host Minecraft servers for 2 players
- Enable Interoperability to access Window from WSL

### Completed tasks

- [x] Add infra app to manage infrastructure resources. (DONE)
- [x] Add secrets using AGE key
- [x] Added the Nginx as Ingress
- [x] Added Prometheus & Grafana

## Commands

```
### Using your generated age key and encrypt admin/password using the public key
sops --encrypt --age {{age_public_key}} gitops/clusters/apse2/local/platform/monitoring/grafana/grafana-admin.yaml > gitops/clusters/apse2/local/platform/monitoring/grafana/secrets.enc.yaml
```

#### Generate cookie secrets

```bash
# Generate OAUTH2_PROXY_COOKIE_SECRET for the Oauth2 Proxy authentication server
openssl rand -base64 24
```

### Useful commands

#### Generate cookie secrets

```bash
### Test the postgreSQL
kubectl run psql-test \
  -it --rm \
  --image=postgres:17 \
  -n authentik \
  -- bash

kubectl run curl \
  --rm -it \
  --image=curlimages/curl \
  -n authentik -- sh

```
