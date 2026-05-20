# ---------- Atlas / cluster ----------
variable "org_id" {
  description = "MongoDB Atlas Organization ID"
  type        = string
}

variable "project_name" {
  description = "Nome do projeto Atlas"
  type        = string
}

variable "cluster_name" {
  description = "Nome do cluster"
  type        = string
}

variable "environment" {
  description = "dev | test | stage | prod"
  type        = string
}

variable "team" {
  description = "Time / centro de custo (tag de FinOps)"
  type        = string
}

variable "data_classification" {
  description = "interno | confidencial | restrito"
  type        = string
  default     = "confidencial"
}

variable "cloud_provider" {
  type    = string
  default = "AWS"
}

variable "region" {
  description = "Região no formato Atlas (ex: SA_EAST_1)"
  type        = string
  default     = "SA_EAST_1"
}

variable "instance_size" {
  type    = string
  default = "M30"
}

variable "disk_size_gb" {
  type    = number
  default = 40
}

variable "mongo_version" {
  type    = string
  default = "7.0"
}

variable "backup_enabled" {
  type    = bool
  default = true
}

variable "pit_enabled" {
  type    = bool
  default = true
}

variable "backup_retention_days" {
  type    = number
  default = 7
}

variable "app_database" {
  type    = string
  default = "appdb"
}

variable "db_username" {
  type    = string
  default = "app_user"
}

variable "ip_access_list" {
  type = list(object({
    cidr    = string
    comment = string
  }))
  default = []
}

variable "enable_search_nodes" {
  type    = bool
  default = false
}

# ---------- Rede privada (opcional — preenchido pelo cliente) ----------
variable "enable_private_networking" {
  description = "Habilita VPC Peering com a AWS (requer credenciais e IDs do cliente)"
  type        = bool
  default     = false
}

variable "atlas_cidr_block" {
  type    = string
  default = "192.168.248.0/21"
}

variable "aws_account_id" {
  type    = string
  default = ""
}

variable "aws_region" {
  description = "Região AWS no formato AWS (ex: sa-east-1)"
  type        = string
  default     = "sa-east-1"
}

variable "aws_vpc_id" {
  type    = string
  default = ""
}

variable "vpc_cidr" {
  type    = string
  default = ""
}
