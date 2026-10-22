# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository purpose

This is a personal GitOps / infrastructure-as-code monorepo: a home Kubernetes cluster managed via ArgoCD, plus Terraform for AWS/Azure/GCloud cloud resources, shared Helm charts, and one application (`portal`, a Go service). There is no single build for the whole repo — each subdirectory is its own unit with its own tooling.

## Repository structure

- `gitops/` — ArgoCD Applications and Kustomize manifests for the `apse2/local` cluster. This is the main area of ongoing work.
  - `gitops/bootstrap/argocd/` — bootstraps ArgoCD itself (Helm release via `argocd-helm-app.yaml`, RBAC, the KSOPS config management plugin in `cmp.yaml`).
  - `gitops/clusters/apse2/local/` — the "app of apps" for the local cluster. `app.yaml` is the root ArgoCD Application pointing at this directory; `kustomization.yaml` lists every sub-app (each sub-app is its own `app.yaml` ArgoCD Application + manifests, e.g. `http-test/`, `oracle/`, `dbt/`, `seaweedfs/`, `openmetadata/`, `argo-rollouts/`, `prometheus/`, `metal-lb/`, `oauth2-proxy/`, `glance/`, `cluster-resources/`, `istio/`).
  - Top-level `gitops/grafana/`, `gitops/tempo/`, `gitops/docker-registry/`, `gitops/argo-workflows/` are standalone apps outside the local cluster tree.
  - To add a new workload to the local cluster: create a new directory under `gitops/clusters/apse2/local/<name>/` with its own ArgoCD `app.yaml` (same `source`/`destination`/`syncPolicy` shape as existing ones) and add it to `gitops/clusters/apse2/local/kustomization.yaml`.
- `helm-charts/` — Helm charts hosted in this repo. `base-service-chart` is a generic chart (deployment/service/serviceaccount) other apps are meant to build on; `api-hello` is a sample consumer.
- `k8s/` — Terraform that installs ArgoCD itself into the cluster (`helm_release.argocd`).
- `aws/`, `azure/`, `gcloud/` — Terraform per cloud provider, each self-contained with its own `providers.tf`. GCloud auth is via `GOOGLE_APPLICATION_CREDENTIALS=terraform-sa-key.json` (see `gcloud/READme.md`).
- `portal/` — a standalone Go web app: Google OIDC login issuing a signed session cookie. See `portal/READme.md` for the full auth flow (state/nonce/PKCE, ID token verification against Google's JWKS, HMAC-signed `portal_session` cookie). Routes, setup, and Docker instructions are documented there — read it before touching `portal/backend/*.go`.
- `docker-images/argocd-ksops/` — custom ArgoCD repo-server image bundling the KSOPS plugin (used by `gitops/bootstrap/argocd/cmp.yaml`) for decrypting SOPS secrets during manifest rendering.
- `scripts/mi_router/` — Lua scripts for a MikroTik router (Telegram bot listener, wake script).
- `windows-server/` — PowerShell + Makefile for a Windows command server.

## Secrets (SOPS)

Secrets in `gitops/**` are committed encrypted as `secrets.enc.yaml`, encrypted with `sops` using an AGE key (`.sops.yaml` encrypts the `data`/`stringData` fields of a manifest). ArgoCD decrypts them at sync time via the KSOPS CMP plugin. To create/update one:

```bash
sops --encrypt --age <age_public_key> path/to/secret.yaml > path/to/secrets.enc.yaml
```

`sops-age-key.txt` and `terraform-sa-key.json` in the repo root are real credential material — never print their contents, and treat any file matching `*secrets.enc.yaml` as already-encrypted (don't try to "fix" or reformat it by hand).

## Common commands

### Helm (`helm-charts/`)

```bash
helm upgrade --install api-hello ./api-hello --namespace backend --create-namespace
helm rollback api-hello 1 -n backend
helm history api-hello -n backend
helm uninstall api-hello -n backend
```

Smoke-test a deployed service from inside the cluster:
```bash
kubectl run test --image=curlimages/curl -n test --create-namespace --command -- sleep 3600
kubectl exec -it pod/test -n test -- /bin/sh
curl http://<service>.<namespace>.svc.cluster.local
```

### Portal (`portal/`)

```bash
cd portal
cp .env.example .env   # fill in GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET / SESSION_SECRET
cd backend
set -a && source ../.env && set +a
go run .                       # serves on LISTEN_ADDR, default :8080
go test ./...                  # run tests (e.g. session_test.go)
```

Docker:
```bash
cd portal
docker build -t portal .
docker run --rm -p 8080:8080 --env-file .env -e WEB_DIR=/web portal
```

### Terraform (`aws/`, `azure/`, `gcloud/`, `k8s/`)

Standard `terraform init` / `plan` / `apply` inside the relevant directory — each cloud has its own state and providers, they are not a single root module. For GCloud, export `GOOGLE_APPLICATION_CREDENTIALS=terraform-sa-key.json` first.

### Docker images (`docker-images/argocd-ksops/`)

```bash
docker login ghcr.io
docker run --rm -it --platform=linux/amd64 --entrypoint=/bin/sh ghcr.io/wisphill/argocd-repo-server:latest
```

## Notes

- ArgoCD manages its own RBAC; ArgoWorkflows relies on the Kubernetes service account for RBAC instead.
- `targetRevision: main` is used throughout ArgoCD Applications — merges to `main` are what the cluster actually syncs to, so treat changes under `gitops/` as effectively live once merged.
