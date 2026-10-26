# Argo Workflows

## OpenMetadata Governance Portal frontend

`deploy-openmetadata-governance-portal-frontend` clones the public portal repository,
builds `frontend/` with Vite, and uploads `frontend/dist` to Cloudflare Pages. The
workflow is installed when Argo CD reconciles this folder; a deployment itself only
happens when you submit the workflow.

### One-time setup

Add these values to the existing encrypted `argo-workflows-secret-keys` Secret in
`secrets.enc.yaml`, using the repository's SOPS/AGE workflow:

- `CLOUDFLARE_API_TOKEN` — a scoped Cloudflare API token with permission to deploy
  to the `openmetadata-governance-portal` Pages project.
- `CLOUDFLARE_ACCOUNT_ID` — the Cloudflare account that owns that Pages project.

Do not put either value in this Makefile, a Workflow parameter, or the portal
repository. `VITE_API_URL` is different: it is the public HTTPS backend URL and is
compiled into browser JavaScript.

### Quick commands

```bash
# Confirm Argo CD has reconciled the template.
make -C gitops/argo-workflows app-status

# List and inspect workflow executions.
make -C gitops/argo-workflows workflow-list
make -C gitops/argo-workflows workflow-status WORKFLOW=<workflow-name>
make -C gitops/argo-workflows workflow-logs WORKFLOW=<workflow-name>

# Deploy the main revision to Cloudflare Pages. This creates a real deployment.
make -C gitops/argo-workflows workflow-submit \
  VITE_API_URL=https://api.example.com
```

Use `SOURCE_REVISION=<git-ref>` to build another revision and `PAGES_BRANCH=<branch>`
to select the Cloudflare Pages deployment branch. After a change to this folder is
merged, inspect `app-status` before submitting a workflow.

## OpenMetadata Governance Portal backend

`build-and-deploy-openmetadata-governance-portal-backend` clones the backend
repository's `main` branch, builds `backend/Dockerfile`, and pushes
`docker-registry.docker-registry.svc.cluster.local:5000/governance-portal/backend:main`.
It then stops at an Argo manual approval node. Resuming that node restarts the
GitOps-managed backend Deployment and waits for its health check. The workflow's
cross-namespace RBAC is deliberately restricted to that one Deployment.

Submit the build with:

```bash
make -C gitops/argo-workflows backend-workflow-submit
```

Before submitting, make sure the Argo CD Application
`openmetadata-governance-portal-backend` has synchronized and that its encrypted
runtime Secret has been added. The build does not deploy until the manual approval
node is resumed.
