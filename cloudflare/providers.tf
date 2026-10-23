terraform {
  required_version = "1.17.0"

  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 5.0"
    }
  }

  // remote support the workspace prefix
  // use this for the Google cloud and cloud resources only
  backend "remote" {
    organization = "ywisper"
    workspaces {
      prefix = "cloudflare-"
    }
  }
}

# Authentication is supplied by the CLOUDFLARE_API_TOKEN environment variable.
provider "cloudflare" {}
