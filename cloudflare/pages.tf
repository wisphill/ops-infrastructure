# This intentionally has no source or build configuration: deployments are uploaded
# by the Argo Workflow with `wrangler pages deploy`, not by Cloudflare's Git integration.
resource "cloudflare_pages_project" "openmetadata_governance_portal" {
  account_id        = var.cloudflare_account_id
  name              = "openmetadata-governance-portal"
  production_branch = "main"
}

# `governance-portal.foolosophy.dev` serves the production branch of this Pages project.
resource "cloudflare_pages_domain" "openmetadata_governance_portal" {
  account_id   = var.cloudflare_account_id
  project_name = cloudflare_pages_project.openmetadata_governance_portal.name
  name         = "governance-portal.foolosophy.dev"
}

# This proxied CNAME sends the portal subdomain to Cloudflare Pages.
resource "cloudflare_dns_record" "openmetadata_governance_portal" {
  zone_id = var.cloudflare_foolosophy_zone_id
  name    = "governance-portal"
  type    = "CNAME"
  content = cloudflare_pages_project.openmetadata_governance_portal.subdomain
  ttl     = 1
  proxied = true
  comment = "OpenMetadata Governance Portal on Cloudflare Pages"
}

resource "cloudflare_pages_project" "phil_portal" {
  account_id        = var.cloudflare_account_id
  name              = "phil"
  production_branch = "main"
}

# `governance-portal.foolosophy.dev` serves the production branch of this Pages project.
resource "cloudflare_pages_domain" "phil_portal" {
  account_id   = var.cloudflare_account_id
  project_name = cloudflare_pages_project.phil_portal.name
  name         = "phil.foolosophy.dev"
}

# This proxied CNAME sends the portal subdomain to Cloudflare Pages.
resource "cloudflare_dns_record" "phil_portal" {
  zone_id = var.cloudflare_foolosophy_zone_id
  name    = "phil"
  type    = "CNAME"
  content = cloudflare_pages_project.phil_portal.subdomain
  ttl     = 1
  proxied = true
  comment = "Phil porfolio on the Cloudflare Pages"
}

output "openmetadata_governance_portal_pages_url" {
  description = "Default Cloudflare Pages URL for the project."
  value       = "https://${cloudflare_pages_project.openmetadata_governance_portal.subdomain}"
}

output "openmetadata_governance_portal_custom_domain_url" {
  description = "Production custom domain for the Pages project."
  value       = "https://${cloudflare_pages_domain.openmetadata_governance_portal.name}"
}
