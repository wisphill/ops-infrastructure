# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## High-Level Architecture

This repository uses a GitOps approach to manage Kubernetes cluster configuration.

- **Provisioning**: The underlying Kubernetes cluster infrastructure is managed by Terraform, with configuration located in the `k8s/` directory.
- **GitOps Engine**: ArgoCD is used as the GitOps engine. The manifests for bootstrapping ArgoCD are in `gitops/bootstrap/argocd/`.
- **App of Apps Pattern**: The repository follows the "app of apps" pattern. A root ArgoCD `Application` custom resource, defined in `gitops/clusters/apse2/local/app.yaml`, points to the `gitops/clusters/apse2/local` directory.
- **Configuration Management**: Kustomize is used to manage and customize the Kubernetes manifests. The main Kustomization file is at `gitops/clusters/apse2/local/kustomization.yaml`.
- **Application Manifests**: Manifests for various applications are organized into subdirectories under `gitops/clusters/apse2/local/`. Each subdirectory typically contains a YAML file with the application's resources, which is then referenced in the main `kustomization.yaml`.
- **Secret Management**: Secrets are encrypted using `sops` with `age` encryption.

## Project Structure

- `k8s/`: Contains Terraform configuration for the Kubernetes cluster.
- `gitops/bootstrap/`: Contains the initial manifests to bootstrap ArgoCD.
- `gitops/clusters/`: Contains the configuration for the Kubernetes clusters.
  - `apse2/`: Represents a specific cluster (likely in the `ap-southeast-2` region).
    - `local/`: Contains the configuration for the "local" environment of the `apse2` cluster. This is the main directory for application manifests.

## Common Commands

Here are some common commands used in this repository.

### Encrypting secrets with sops

To encrypt a file with `sops` and an `age` public key:

```bash
# Example for Grafana admin secrets
sops --encrypt --age {{age_public_key}} gitops/clusters/apse2/local/platform/monitoring/grafana/grafana-admin.yaml > gitops/clusters/apse2/local/platform/monitoring/grafana/secrets.enc.yaml

# Example for ArgoCD values
sops --encrypt --age age1fg2mcvwuztl4cgycxhdlfzu584uslnfznmgunqgw99znwmqhjq3quxdmw3 gitops/bootstrap/argocd/values.yaml > gitops/bootstrap/argocd/values.enc.yaml
```

### Generating secrets

To generate a cookie secret for OAuth2 Proxy:

```bash
openssl rand -base64 24
```

### Interacting with the cluster

Some useful `kubectl` commands for testing services:

```bash
# Test PostgreSQL connection
kubectl run psql-test \
  -it --rm \
  --image=postgres:17 \
  -n authentik \
  -- bash

# Run a curl container for testing network connectivity
kubectl run curl \
  --rm -it \
  --image=curlimages/curl \
  -n authentik -- sh
```
