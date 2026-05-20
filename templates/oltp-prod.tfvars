# Template: OLTP Produção  (PITR + rede privada)
org_id       = "REPLACE_WITH_ATLAS_ORG_ID"
project_name = "oltp-prod"
cluster_name = "oltp-core"
environment  = "prod"
team         = "Pagamentos"
data_classification = "restrito"

instance_size = "M50"
disk_size_gb  = 160
mongo_version = "7.0"

backup_enabled        = true
pit_enabled           = true
backup_retention_days = 30

enable_private_networking = true
aws_account_id            = "REPLACE_WITH_AWS_ACCOUNT_ID"
aws_region                = "sa-east-1"
aws_vpc_id                = "REPLACE_WITH_VPC_ID"
vpc_cidr                  = "10.20.0.0/16"
