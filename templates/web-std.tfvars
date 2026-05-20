# Template: Web App Standard  (espelha o catálogo do Maestro)
# Uso: terraform apply -var-file=../templates/web-std.tfvars
org_id       = "REPLACE_WITH_ATLAS_ORG_ID"
project_name = "web-std"
cluster_name = "web-app"
environment  = "stage"
team         = "E-commerce"
data_classification = "interno"

instance_size = "M30"
disk_size_gb  = 40
mongo_version = "7.0"

backup_enabled        = true
pit_enabled           = false
backup_retention_days = 7

enable_private_networking = false
enable_search_nodes       = false
