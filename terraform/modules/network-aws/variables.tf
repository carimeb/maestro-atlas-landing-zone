variable "project_id" {
  description = "ID do projeto Atlas (vem do módulo atlas-cluster)"
  type        = string
}

variable "atlas_cidr_block" {
  description = "CIDR do container de rede do Atlas (não pode sobrepor o VPC do cliente)"
  type        = string
  default     = "192.168.248.0/21"
}

variable "atlas_region" {
  description = "Região do Atlas no formato Atlas (ex: SA_EAST_1)"
  type        = string
}

variable "aws_account_id" {
  description = "AWS Account ID do cliente"
  type        = string
}

variable "aws_region" {
  description = "Região AWS no formato AWS (ex: sa-east-1)"
  type        = string
}

variable "aws_vpc_id" {
  description = "VPC ID do cliente para o peering"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR do VPC do cliente (route table)"
  type        = string
}
