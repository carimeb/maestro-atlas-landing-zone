# Template: GenAI / Vector Search  (Search Nodes dedicados)
org_id       = "REPLACE_WITH_ATLAS_ORG_ID"
project_name = "genai-rag"
cluster_name = "rag-vector"
environment  = "dev"
team         = "IA Generativa"
data_classification = "confidencial"

instance_size = "M40"
disk_size_gb  = 80
mongo_version = "7.0"

backup_enabled        = true
pit_enabled           = true
backup_retention_days = 7

# Search Nodes para Atlas Vector Search em escala.
enable_search_nodes = true

enable_private_networking = false
