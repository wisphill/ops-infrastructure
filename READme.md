## Project Structure

### GitOps (`gitops/`)

| Path | Description |
|------|-------------|
| `gitops/bootstrap/argocd/` | Manifests to bootstrap ArgoCD onto the cluster |
| `gitops/clusters/apse2/local/app.yaml` | Root ArgoCD Application (app of apps entry point) |
| `gitops/clusters/apse2/local/kustomization.yaml` | Main Kustomization referencing all apps |
| `gitops/clusters/apse2/local/cluster-resources/` | Namespaces and cluster-wide resources |
| `gitops/clusters/apse2/local/metal-lb/` | MetalLB load balancer configuration |
| `gitops/clusters/apse2/local/nginx-helm.yaml` | Nginx ingress controller (Helm) |
| `gitops/clusters/apse2/local/prometheus/` | Prometheus monitoring stack |
| `gitops/clusters/apse2/local/authentik/` | Authentik identity provider (SSO) |
| `gitops/clusters/apse2/local/oauth2-proxy/` | OAuth2 Proxy for authentication |
| `gitops/clusters/apse2/local/glance/` | Glance dashboard |
| `gitops/clusters/apse2/local/argo-workflows/` | Argo Workflows |
| `gitops/clusters/apse2/local/mcp-playwright/` | MCP Playwright service |
| `gitops/clusters/grafana/` | Grafana Helm app and resources |

### Infrastructure (`k8s/`)

| Path | Description |
|------|-------------|
| `k8s/` | Terraform configuration for the Kubernetes cluster |

---

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

### Authentik

- First time logging in, let's use /if/flow/initial-setup/ for setting up the admin
- Authentik uses the PostgreSQL for storage, consider to back it up usually

## Commands

```
### Using your generated age key and encrypt admin/password using the public key
sops --encrypt --age {{age_public_key}} gitops/clusters/apse2/local/platform/monitoring/grafana/grafana-admin.yaml > gitops/clusters/apse2/local/platform/monitoring/grafana/secrets.enc.yaml

sops --encrypt --age age1fg2mcvwuztl4cgycxhdlfzu584uslnfznmgunqgw99znwmqhjq3quxdmw3 gitops/bootstrap/argocd/values.yaml > gitops/bootstrap/argocd/values.enc.yaml
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
