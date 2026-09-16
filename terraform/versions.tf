terraform {
  required_version = ">= 1.5"
  required_providers {
    aws        = { source = "hashicorp/aws",       version = "~> 5.70" }
    helm       = { source = "hashicorp/helm",       version = "~> 2.15" }
    kubernetes = { source = "hashicorp/kubernetes", version = "~> 2.33" }
    kubectl    = { source = "gavinbunney/kubectl",  version = "~> 1.19" }
  }
}

provider "aws" {
  region  = var.region
  profile = var.aws_profile
  default_tags {
    tags = {
      Project = "gpu-observability-talk"
      Owner   = "gpu-observability-demo"
      Purpose = "kubecon-demo-reproduction"
    }
  }
}
