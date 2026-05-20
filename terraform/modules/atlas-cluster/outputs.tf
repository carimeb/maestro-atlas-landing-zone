output "project_id" {
  description = "ID do projeto Atlas criado"
  value       = mongodbatlas_project.this.id
}

output "cluster_name" {
  description = "Nome do cluster"
  value       = mongodbatlas_advanced_cluster.this.name
}

output "connection_string_srv" {
  description = "Connection string SRV padrão (sem credenciais)"
  value       = mongodbatlas_advanced_cluster.this.connection_strings[0].standard_srv
}

output "db_username" {
  description = "Usuário de banco inicial"
  value       = mongodbatlas_database_user.app.username
}

output "db_password" {
  description = "Senha gerada do usuário inicial"
  value       = random_password.db.result
  sensitive   = true
}
