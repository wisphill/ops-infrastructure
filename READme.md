# Ops Infrastructure

> **GitOps · Cloud Infrastructure · Kubernetes · Bare Metal**

![Unity Engine](https://camo.githubusercontent.com/b78d5ccca8241ceacaeba2a3489ddd031359bde4fb617a6e0f35cb27ee451d4c/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f556e6974792d456e67696e652d3030666638383f7374796c653d666c61742d737175617265266c6f676f3d756e697479)
![Mod Multiplayer](https://camo.githubusercontent.com/1334306d29049e4b0765091af40ae65004371419b9969a1c89ccc78bf5793109/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f4d6f64652d4d756c7469706c617965722d3030636666663f7374796c653d666c61742d737175617265)
![Status In Development](https://camo.githubusercontent.com/9185738247fddb75f8d0f426bb0be2dfd54d6388c334e8b2ded3385ab95dc4a3/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f5374617475732d496e253230446576656c6f706d656e742d6666653630303f7374796c653d666c61742d737175617265)
![Language C#](https://camo.githubusercontent.com/aa7498783a6cbb90ff2902be98209f49fb6408f41f9216cc2cbaf0691df908c1/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f4c616e67756167652d432532332d626c756576696f6c65743f7374796c653d666c61742d737175617265)

## Project Structure

```text
ops-infrastructure/
├── aws/                                # AWS infrastructure files
├── azure/                              # Azure infrastructure files
│   ├── cosmosdb.tf
│   ├── func.tf
│   ├── local.tf
│   ├── providers.tf
│   ├── vpc.tf
│   └── READme.md
├── gcloud/                             # Google Cloud infrastructure files
│   ├── cloud_run.tf
│   ├── providers.tf
│   ├── variables.tf
│   └── READme.md
├── gitops/                             # GitOps manifests and ArgoCD configuration
│   ├── bootstrap/
│   │   └── argocd/                     # ArgoCD bootstrap manifests
│   │       ├── argocd-helm-app.yaml
│   │       ├── cluster-role-binding.yaml
│   │       ├── cmp.yaml
│   │       ├── generator.yaml
│   │       ├── kustomization.yaml
│   │       ├── oci-setting.yaml
│   │       ├── READme.md
│   │       ├── secrets.enc.yaml
│   │       ├── service-account.yaml
│   │       └── values.yaml
│   ├── clusters/
│   │   └── apse2/
│   │       └── local/                  # Local cluster GitOps app set
│   │           ├── app.yaml
│   │           ├── kustomization.yaml
│   │           ├── cluster-resources/
│   │           ├── metal-lb/
│   │           ├── nginx-helm.yaml
│   │           ├── prometheus/
│   │           ├── oauth2-proxy/
│   │           ├── glance/
│   │           ├── argo-workflows/
│   │           └── mcp-playwright/
│   ├── docker-registry/               # Docker registry resources
│   ├── grafana/                        # Grafana GitOps resources
│   └── tempo/                          # Tempo observability resources
├── helm-charts/                        # Shared Helm charts
│   ├── api-hello/
│   └── base-service-chart/
├── k8s/                                # Kubernetes Terraform configuration
│   ├── main.tf
│   └── providers.tf
├── Dockerfile                          # Container build definition
├── READme.md                           # Project documentation
└── terraform-sa-key.json               # Terraform service account key
```

---

## 🔲 To do tasks

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

## Completed

- [x] Add infra app to manage infrastructure resources. (DONE)
- [x] Add secrets using AGE key
- [x] Added the Nginx as Ingress
- [x] Added Prometheus & Grafana

## Commands

```
### Using your generated age key and encrypt admin/password using the public key
sops --encrypt --age {{age_public_key}} gitops/clusters/apse2/local/platform/monitoring/grafana/grafana-admin.yaml > gitops/clusters/apse2/local/platform/monitoring/grafana/secrets.enc.yaml

sops --encrypt --age age1fg2mcvwuztl4cgycxhdlfzu584uslnfznmgunqgw99znwmqhjq3quxdmw3 gitops/bootstrap/argocd/values.yaml > gitops/bootstrap/argocd/values.enc.yaml
```

### Generate cookie secrets

```bash
# Generate OAUTH2_PROXY_COOKIE_SECRET for the Oauth2 Proxy authentication server
openssl rand -base64 24
```

### Useful commands

#### Generate cookie secrets

```bash
kubectl run curl \
  --rm -it \
  --image=curlimages/curl \
  -n checker -- sh
```

## Notes

- ArgoWorkflows uses the K8S SA for RBAC
- AgroCD processes the RBAC itself

---

## License

MIT License

Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
