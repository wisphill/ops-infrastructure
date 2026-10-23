# Cloudflare Pages

This Terraform configuration creates the `openmetadata-governance-portal` Pages
project only. It does **not** connect a Git repository or upload a deployment;
the Argo Workflow deploys `dist` with Wrangler.

## Real Cloudflare credentials

```bash
export CLOUDFLARE_API_TOKEN=<Pages-Write-token>
export TF_VAR_cloudflare_foolosophy_zone_id=<foolosophy.dev-zone-id>
```

The Cloudflare token needs **Account → Pages → Edit** and **Zone → DNS → Edit**
for `foolosophy.dev`. Terraform creates the
`governance-portal.foolosophy.dev` CNAME and does not modify the root-domain
record.

Run `terraform -chdir=cloudflare init`, then select the intended
`cloudflare-<workspace>` workspace before `plan` or `apply`.
