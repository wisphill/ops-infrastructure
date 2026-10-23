terraform {
  required_version = "1.17.0"

  // remote support the workspace prefix
  // use this for the Google cloud and cloud resources only
  backend "remote" {
    organization = "ywisper"
    workspaces {
      prefix = "cloudflare-"
    }
  }
}