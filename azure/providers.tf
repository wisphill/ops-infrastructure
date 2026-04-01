terraform {
  // remote support the workspace prefix
  // use this for the Google cloud and cloud resources only
  backend "remote" {
    organization = "ywisper"
    workspaces {
      prefix = "azure-"
    }
  }

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0" # Using the latest v4.x series
    }
  }
}

provider "azurerm" {
  # This tells Terraform to use your current 'az login' session
  features {}
  subscription_id = "2376fa10-99be-4e8e-b292-8b25c61b03ea"
}
