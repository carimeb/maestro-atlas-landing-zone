# Arquitetura — Maestro Atlas Landing Zone

A landing zone organiza o acesso ao MongoDB Atlas em planos de controle, espelhando a arquitetura de referência do Enterprise Flywheel.

## Planos de controle

| Plano | Responsabilidade | Neste repo |
|-------|------------------|------------|
| **Developer Control Plane** | Portal/catálogo self-service | `demo/maestro.html` (protótipo) |
| **Integration & Delivery** | Orquestração e CI/CD | `.github/workflows/` + `terraform/` |
| **Security & Identity** | SSO, RBAC, BYOK, secrets | `docs/identity-azure-ad.md` + guardrails nos módulos |
| **Observability** | Métricas, logs, alertas | `docs/observability-grafana.md` |
| **Agent Plane (Day-2)** | Ops Copilot: MCP + Skills + LLM + memória | `docs/agents-mcp-skills.md`, `docs/agent-memory.md` |
| **Resource Plane** | Cluster Atlas + rede | `terraform/modules/*` |

## Fluxo de provisionamento (Day 1)

```
Dev autentica (Azure AD/SSO)
        │
        ▼
Escolhe template no catálogo (Maestro)  ──►  vira -var-file=*.tfvars
        │
        ▼
Pull Request  ──►  GitHub Actions: terraform plan  (revisão + guardrails)
        │
        ▼
Merge na main ──►  Aprovação no Environment "production"
        │
        ▼
terraform apply  ──►  Atlas Admin API cria projeto, cluster, backup, rede
        │
        ▼
Connection string + observabilidade entregues ao time
```

## Guardrails codificados

Os controles são herdados automaticamente do módulo `atlas-cluster`:

- **Tags obrigatórias** (`environment`, `cost-center`, `data-classification`) — base do chargeback de FinOps.
- **PITR obrigatório em produção** (precondition no Terraform — bloqueia o apply se faltar).
- **Backup** com retenção por ambiente.
- **Rede privada** (VPC Peering) recomendada em prod via `enable_private_networking`.

## Mapa de classificação → template

| Classificação | Templates | BYOK | Backup | Rede |
|---------------|-----------|------|--------|------|
| Interno | web-std, sandbox | Opcional | Snapshot 7d | IP Access List |
| Confidencial | oltp-prod, analytics, genai | Recomendado | PITR 7d | Private Endpoint |
| Restrito (PII/PCI) | finserv | Obrigatório | PITR + DR | Private Link + data residency |
