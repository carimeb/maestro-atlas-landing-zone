# Ambiente DEV — cluster pequeno, sem rede privada.
org_id       = "REPLACE_WITH_ATLAS_ORG_ID"
project_name = "maestro-dev"
cluster_name = "app-dev"
environment  = "dev"
team         = "Plataforma"

cloud_provider = "AWS"
region         = "SA_EAST_1"
instance_size  = "M10"
disk_size_gb   = 10
mongo_version  = "7.0"

backup_enabled        = true
pit_enabled           = false
backup_retention_days = 7

ip_access_list = [
  { cidr = "0.0.0.0/0", comment = "DEV — restrinja para o CIDR da sua VPN" }
]

enable_private_networking = false
