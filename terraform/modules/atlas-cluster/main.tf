terraform {
  required_providers {
    mongodbatlas = {
      source  = "mongodb/mongodbatlas"
      version = "~> 1.18"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

# ---------------------------------------------------------------------------
# Projeto Atlas — um por workload/time (boa prática de landing zone).
# Os guardrails (backup, rede, encryption) são herdados deste módulo.
# ---------------------------------------------------------------------------
resource "mongodbatlas_project" "this" {
  name   = var.project_name
  org_id = var.org_id
}

# ---------------------------------------------------------------------------
# Cluster dedicado (replica set). Sintaxe de blocos do provider 1.x.
# ---------------------------------------------------------------------------
resource "mongodbatlas_advanced_cluster" "this" {
  project_id             = mongodbatlas_project.this.id
  name                   = var.cluster_name
  cluster_type           = "REPLICASET"
  mongo_db_major_version = var.mongo_version
  backup_enabled         = var.backup_enabled
  pit_enabled            = var.pit_enabled

  replication_specs {
    region_configs {
      provider_name = var.cloud_provider
      region_name   = var.region
      priority      = 7

      electable_specs {
        instance_size = var.instance_size
        node_count    = var.node_count
        disk_size_gb  = var.disk_size_gb
      }

      auto_scaling {
        disk_gb_enabled = true
        compute_enabled = false
      }
    }
  }

  # Tags = base do chargeback de FinOps e da governança por classificação.
  tags {
    key   = "environment"
    value = var.environment
  }
  tags {
    key   = "cost-center"
    value = var.team
  }
  tags {
    key   = "data-classification"
    value = var.data_classification
  }
  tags {
    key   = "managed-by"
    value = "maestro-landing-zone"
  }

  lifecycle {
    precondition {
      condition     = !(var.environment == "prod" && var.pit_enabled == false)
      error_message = "Guardrail: PITR (pit_enabled) é obrigatório em produção."
    }
  }
}

# ---------------------------------------------------------------------------
# Senha gerada para o usuário inicial (entregue como output sensível).
# Em produção, prefira X.509 ou AWS IAM database auth.
# ---------------------------------------------------------------------------
resource "random_password" "db" {
  length  = 24
  special = true
  override_special = "_-"
}

resource "mongodbatlas_database_user" "app" {
  project_id         = mongodbatlas_project.this.id
  username           = var.db_username
  password           = random_password.db.result
  auth_database_name = "admin"

  roles {
    role_name     = "readWrite"
    database_name = var.app_database
  }

  scopes {
    name = mongodbatlas_advanced_cluster.this.name
    type = "CLUSTER"
  }
}

# ---------------------------------------------------------------------------
# IP Access List (em prod, prefira Private Endpoint — ver módulo network-aws).
# ---------------------------------------------------------------------------
resource "mongodbatlas_project_ip_access_list" "this" {
  for_each   = { for e in var.ip_access_list : e.cidr => e }
  project_id = mongodbatlas_project.this.id
  cidr_block = each.value.cidr
  comment    = each.value.comment
}

# ---------------------------------------------------------------------------
# Política de backup + PITR.
# ---------------------------------------------------------------------------
resource "mongodbatlas_cloud_backup_schedule" "this" {
  count        = var.backup_enabled ? 1 : 0
  project_id   = mongodbatlas_project.this.id
  cluster_name = mongodbatlas_advanced_cluster.this.name

  reference_hour_of_day    = 3
  reference_minute_of_hour = 0
  restore_window_days      = var.pit_enabled ? var.backup_retention_days : 1

  policy_item_daily {
    frequency_interval = 1
    retention_unit     = "days"
    retention_value    = var.backup_retention_days
  }
}

# ---------------------------------------------------------------------------
# Search Nodes dedicados (opcional) — base para Atlas Vector Search em escala.
# ---------------------------------------------------------------------------
resource "mongodbatlas_search_deployment" "this" {
  count        = var.enable_search_nodes ? 1 : 0
  project_id   = mongodbatlas_project.this.id
  cluster_name = mongodbatlas_advanced_cluster.this.name

  specs = [
    {
      instance_size = "S20_HIGHCPU_NVME"
      node_count    = 2
    }
  ]
}
