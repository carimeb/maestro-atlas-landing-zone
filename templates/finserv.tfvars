# Template: FinServ Regulado  (compliance-ready, rede privada obrigatória)
org_id       = "REPLACE_WITH_ATLAS_ORG_ID"
project_name = "finserv-regulated"
cluster_name = "finserv-core"
environment  = "prod"
team         = "Risco"
data_classification = "restrito"

instance_size = "M60"
disk_size_gb  = 320
mongo_version = "7.0"

backup_enabled        = true
pit_enabled           = true
backup_retention_days = 35

enable_private_networking = true
aws_account_id            = "REPLACE_WITH_AWS_ACCOUNT_ID"
aws_region                = "sa-east-1"
aws_vpc_id                = "REPLACE_WITH_VPC_ID"
vpc_cidr                  = "10.30.0.0/16"
