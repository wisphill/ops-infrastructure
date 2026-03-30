terraform {
  // remote support the workspace prefix
  // use this for the Google cloud and cloud resources only
  backend "remote" {
    organization = "ywisper"
    workspaces {
      prefix = "gcloud-"
    }
  }

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.0"
    }
  }
}

provider "google" {
  project = "chat-491404"
  region  = "asia-southeast1"
}
