terraform {
  required_version = ">= 1.5"

  required_providers {
    mongodbatlas = {
      source  = "mongodb/mongodbatlas"
      version = "~> 1.18"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

# As credenciais do Atlas vêm das variáveis de ambiente:
#   MONGODB_ATLAS_PUBLIC_KEY  e  MONGODB_ATLAS_PRIVATE_KEY
provider "mongodbatlas" {}

# Só é usado quando enable_private_networking = true.
provider "aws" {
  region = var.aws_region
}
