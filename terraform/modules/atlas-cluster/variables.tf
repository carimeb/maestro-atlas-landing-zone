variable "org_id" {
  description = "MongoDB Atlas Organization ID"
  type        = string
}

variable "project_name" {
  description = "Nome do projeto Atlas (um por workload/time é a boa prática da landing zone)"
  type        = string
}

variable "cluster_name" {
  description = "Nome do cluster"
  type        = string
}

variable "environment" {
  description = "Ambiente: dev | test | stage | prod"
  type        = string
  validation {
    condition     = contains(["dev", "test", "stage", "prod"], var.environment)
    error_message = "environment deve ser um de: dev, test, stage, prod."
  }
}

variable "team" {
  description = "Time / centro de custo (vira tag para chargeback de FinOps)"
  type        = string
}

variable "data_classification" {
  description = "Classificação do dado: interno | confidencial | restrito"
  type        = string
  default     = "confidencial"
}

variable "cloud_provider" {
  description = "Provedor de nuvem do cluster"
  type        = string
  default     = "AWS"
}

variable "region" {
  description = "Região no formato Atlas (ex: SA_EAST_1, US_EAST_1, EU_WEST_1)"
  type        = string
  default     = "SA_EAST_1"
}

variable "instance_size" {
  description = "Tier do cluster (ex: M10, M30, M50)"
  type        = string
  default     = "M30"
}

variable "node_count" {
  description = "Número de nós eletivos do replica set"
  type        = number
  default     = 3
}

variable "mongo_version" {
  description = "Versão maior do MongoDB"
  type        = string
  default     = "7.0"
}

variable "disk_size_gb" {
  description = "Storage provisionado em GB"
  type        = number
  default     = 40
}

variable "backup_enabled" {
  description = "Habilita Cloud Backup"
  type        = bool
  default     = true
}

variable "pit_enabled" {
  description = "Habilita Point-in-Time Recovery (recomendado em prod)"
  type        = bool
  default     = true
}

variable "backup_retention_days" {
  description = "Retenção dos snapshots diários (dias)"
  type        = number
  default     = 7
}

variable "app_database" {
  description = "Nome do banco da aplicação (escopo do usuário criado)"
  type        = string
  default     = "appdb"
}

variable "db_username" {
  description = "Usuário de banco inicial da aplicação"
  type        = string
  default     = "app_user"
}

variable "ip_access_list" {
  description = "Lista de CIDRs autorizados (em prod, prefira Private Endpoint)"
  type = list(object({
    cidr    = string
    comment = string
  }))
  default = []
}

variable "enable_search_nodes" {
  description = "Provisiona Search Nodes dedicados (necessário para Vector Search em escala)"
  type        = bool
  default     = false
}
