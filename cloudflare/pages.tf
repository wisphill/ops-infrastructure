# This intentionally has no source or build configuration: deployments are uploaded
# by the Argo Workflow with `wrangler pages deploy`, not by Cloudflare's Git integration.
resource "cloudflare_pages_project" "openmetadata_governance_portal" {
  account_id        = var.cloudflare_account_id
  name              = "openmetadata-governance-portal"
  production_branch = "main"
}

output "openmetadata_governance_portal_pages_url" {
  description = "Default Cloudflare Pages URL for the project."
  value       = "https://${cloudflare_pages_project.openmetadata_governance_portal.subdomain}"
}
