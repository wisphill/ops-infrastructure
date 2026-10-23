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
