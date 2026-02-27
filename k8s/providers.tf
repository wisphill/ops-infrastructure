terraform {
  cloud {
    organization = "ywisper"
    workspaces {
      name = "dev"
    }
  }

  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.6.0"
    }
  }
}

# access directly with terraform
provider "kubernetes" {
  config_path    = "~/.kube/config"
  config_context = "default" # the context on .kube file
}

# Provider dùng để cài đặt Argo CD qua Helm
provider "helm" {
  kubernetes {
    config_path    = "~/.kube/config"
    config_context = "default"
  }
}
