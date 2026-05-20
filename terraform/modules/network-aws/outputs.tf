output "peering_connection_id" {
  description = "ID da conexão de peering criada"
  value       = mongodbatlas_network_peering.this.connection_id
}

output "container_id" {
  description = "ID do container de rede do Atlas"
  value       = mongodbatlas_network_container.this.container_id
}
