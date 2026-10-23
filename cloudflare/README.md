# Cloudflare Pages

This Terraform configuration creates the `openmetadata-governance-portal` Pages
project only. It does **not** connect a Git repository or upload a deployment;
the Argo Workflow deploys `dist` with Wrangler.

## Real Cloudflare credentials

```bash
export CLOUDFLARE_API_TOKEN=<Pages-Write-token>
```

The Cloudflare token needs **Account → Pages → Edit** for the target account.
Run `terraform -chdir=cloudflare init`, then select the intended
`cloudflare-<workspace>` workspace before `plan` or `apply`.
