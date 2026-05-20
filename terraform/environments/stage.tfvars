# Ambiente STAGE.
org_id       = "REPLACE_WITH_ATLAS_ORG_ID"
project_name = "maestro-stage"
cluster_name = "app-stage"
environment  = "stage"
team         = "Plataforma"

cloud_provider = "AWS"
region         = "SA_EAST_1"
instance_size  = "M30"
disk_size_gb   = 40
mongo_version  = "7.0"

backup_enabled        = true
pit_enabled           = true
backup_retention_days = 14

ip_access_list = [
  { cidr = "10.0.0.0/16", comment = "STAGE — CIDR interno" }
]

enable_private_networking = false
