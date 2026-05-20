terraform {
  required_providers {
    mongodbatlas = {
      source  = "mongodb/mongodbatlas"
      version = "~> 1.18"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# ---------------------------------------------------------------------------
# VPC Peering Atlas <-> AWS.
# 🟡 PREENCHIDO PELO CLIENTE: requer credenciais AWS e os IDs do VPC dele.
#    O provider AWS usa as credenciais padrão (env / perfil / role).
# ---------------------------------------------------------------------------

resource "mongodbatlas_network_container" "this" {
  project_id       = var.project_id
  atlas_cidr_block = var.atlas_cidr_block
  provider_name    = "AWS"
  region_name      = var.atlas_region
}

resource "mongodbatlas_network_peering" "this" {
  project_id             = var.project_id
  container_id           = mongodbatlas_network_container.this.container_id
  provider_name          = "AWS"
  accepter_region_name   = var.aws_region
  aws_account_id         = var.aws_account_id
  route_table_cidr_block = var.vpc_cidr
  vpc_id                 = var.aws_vpc_id
}

# Aceite do peering no lado da AWS.
resource "aws_vpc_peering_connection_accepter" "this" {
  vpc_peering_connection_id = mongodbatlas_network_peering.this.connection_id
  auto_accept               = true

  tags = {
    Name      = "atlas-peering"
    ManagedBy = "maestro-landing-zone"
  }
}
