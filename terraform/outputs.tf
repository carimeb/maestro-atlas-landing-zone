output "project_id" {
  description = "ID do projeto Atlas"
  value       = module.atlas.project_id
}

output "cluster_name" {
  value = module.atlas.cluster_name
}

output "connection_string_srv" {
  description = "Connection string SRV (adicione usuário/senha)"
  value       = module.atlas.connection_string_srv
}

output "db_username" {
  value = module.atlas.db_username
}

output "db_password" {
  description = "Senha gerada (terraform output -raw db_password)"
  value       = module.atlas.db_password
  sensitive   = true
}

output "peering_connection_id" {
  description = "ID do peering (null se rede privada desabilitada)"
  value       = var.enable_private_networking ? module.network[0].peering_connection_id : null
}
