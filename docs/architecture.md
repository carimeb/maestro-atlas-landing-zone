# Arquitetura: Maestro Atlas Landing Zone

A landing zone organiza o acesso ao MongoDB Atlas em planos de controle, espelhando a arquitetura de referência do Enterprise Flywheel. O Maestro é a camada de domínio Atlas, plugável no IDP do usuário (ver `adr/0001-integracao-backstage.md`).

## Planos de controle

| Plano | Responsabilidade | Neste repositório |
|-------|------------------|-------------------|
| Developer Control Plane | Portal e catálogo self-service | IDP do usuário (Backstage); `demo/maestro.html` como simulação |
| Integration and Delivery | Orquestração e CI/CD | `.github/workflows/` e `terraform/` |
| Security and Identity | SSO, RBAC, BYOK, secrets | `docs/identity-azure-ad.md` e guardrails nos módulos |
| Observability | Métricas, logs, alertas | `docs/observability-grafana.md` |
| Agent Plane (Day 2) | Ops Copilot: MCP, Skills, LLM, memória | `agent/` (implementado), `docs/agents-mcp-skills.md`, `docs/agent-memory.md` |
| Resource Plane | Cluster Atlas e rede | `terraform/modules/` |

## Fluxo de provisionamento (Day 1)

```
Dev autentica (SSO)
        |
Escolhe template no catálogo  ->  vira -var-file=*.tfvars
        |
Pull Request  ->  GitHub Actions: terraform plan (revisão e guardrails)
        |
Merge na main ->  aprovação no environment de produção
        |
terraform apply  ->  Atlas Admin API cria projeto, cluster, backup, rede
        |
Connection string e observabilidade entregues ao time
```

## Camada de agentes (Day 2)

Pacote Python `maestro_agent` em `agent/`, headless por decisão de arquitetura. Componentes:

| Componente | Implementação |
|------------|---------------|
| Configuração | `config.py`: env-driven, validação fail-fast, segredos mascarados em logs |
| Provedores plugáveis | `providers/`: contrato e registro para embeddings (Voyage, OpenAI, local) e LLM (Anthropic, OpenAI, stub local) |
| Memória de longo prazo | `memory/store.py`: coleção `agent_memory` com Atlas Vector Search; schema validado; backend local para desenvolvimento |
| Memória de curto prazo | `memory/short_term.py`: checkpointer LangGraph com persistência em MongoDB; sustenta retomada de sessão e gate de aprovação |
| Agente de triagem | `agent/triage.py`: ciclo recall, reason, apply, learn com interrupção antes da ação |
| Segurança | `security/`: auditoria estruturada em JSON Lines e detecção de segredos no caminho de escrita |

Fluxo do agente:

```
Incidente
   |
recall   ->  vector search na memória de longo prazo (namespace ativo)
   |
reason   ->  LLM produz causa provável e ação recomendada, fundamentado nos fatos
   |
[gate]   ->  execução interrompida; estado persistido aguardando aprovação humana
   |
apply    ->  ação registrada (execução via MongoDB MCP Server na próxima fase)
   |
learn    ->  resultado vira fato novo na memória de longo prazo
```

Garantias aplicadas a toda escrita na memória, independentemente do backend: validação de schema, detecção de segredos e evento de auditoria com autor e timestamp.

## Guardrails codificados

Herdados automaticamente do módulo `atlas-cluster`:

1. Tags obrigatórias (`environment`, `cost-center`, `data-classification`), base do chargeback de FinOps.
2. PITR obrigatório em produção, com precondition no Terraform que bloqueia o apply se ausente.
3. Backup com retenção por ambiente.
4. Rede privada recomendada em produção via `enable_private_networking`.

## Mapa de classificação para template

| Classificação | Templates | BYOK | Backup | Rede |
|---------------|-----------|------|--------|------|
| Interno | web-std, sandbox | Opcional | Snapshot 7d | IP Access List |
| Confidencial | oltp-prod, analytics, genai | Recomendado | PITR 7d | Private Endpoint |
| Restrito (PII/PCI) | finserv | Obrigatório | PITR e DR | Private Link e data residency |
