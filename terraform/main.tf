# ===========================================================================
# Maestro — Atlas Landing Zone (root module)
# Provisiona o cluster Atlas (sempre) e, opcionalmente, o VPC Peering AWS.
# ===========================================================================

module "atlas" {
  source = "./modules/atlas-cluster"

  org_id                = var.org_id
  project_name          = var.project_name
  cluster_name          = var.cluster_name
  environment           = var.environment
  team                  = var.team
  data_classification   = var.data_classification
  cloud_provider        = var.cloud_provider
  region                = var.region
  instance_size         = var.instance_size
  disk_size_gb          = var.disk_size_gb
  mongo_version         = var.mongo_version
  backup_enabled        = var.backup_enabled
  pit_enabled           = var.pit_enabled
  backup_retention_days = var.backup_retention_days
  app_database          = var.app_database
  db_username           = var.db_username
  ip_access_list        = var.ip_access_list
  enable_search_nodes   = var.enable_search_nodes
}

# 🟡 Rede privada — só roda com enable_private_networking = true.
module "network" {
  source = "./modules/network-aws"
  count  = var.enable_private_networking ? 1 : 0

  project_id       = module.atlas.project_id
  atlas_cidr_block = var.atlas_cidr_block
  atlas_region     = var.region
  aws_account_id   = var.aws_account_id
  aws_region       = var.aws_region
  aws_vpc_id       = var.aws_vpc_id
  vpc_cidr         = var.vpc_cidr
}
