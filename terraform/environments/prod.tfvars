# Ambiente PROD — PITR obrigatório (guardrail) e rede privada recomendada.
# TEMPLATE: substitua os REPLACE_WITH_* e NÃO faça commit de segredos reais.
org_id       = "REPLACE_WITH_ATLAS_ORG_ID"
project_name = "maestro-prod"
cluster_name = "app-prod"
environment  = "prod"
team         = "Plataforma"
data_classification = "restrito"

cloud_provider = "AWS"
region         = "SA_EAST_1"
instance_size  = "M50"
disk_size_gb   = 160
mongo_version  = "7.0"

backup_enabled        = true
pit_enabled           = true
backup_retention_days = 30

# Em prod, prefira Private Endpoint a IP Access List pública.
ip_access_list = []

# 🟡 Preencha com os dados da AWS do cliente:
enable_private_networking = true
aws_account_id            = "REPLACE_WITH_AWS_ACCOUNT_ID"
aws_region                = "sa-east-1"
aws_vpc_id                = "REPLACE_WITH_VPC_ID"
vpc_cidr                  = "10.20.0.0/16"
