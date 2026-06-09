# Ops Copilot — MongoDB MCP Server + Agent Skills

A operação Day-2 do Maestro usa um agente de IA para **operar o Atlas em produção** com segurança. A arquitetura tem quatro peças:

| Peça | Papel | Analogia |
|------|-------|----------|
| **MongoDB MCP Server** | Ferramentas para o agente ler e agir no Atlas | As "mãos" |
| **Agent Skills** | Playbooks que ensinam procedimentos repetíveis | Os "manuais" |
| **LLM** (Claude ou OpenAI) | Raciocínio, correlação e decisão | O "cérebro" |
| **Memória em MongoDB** | Continuidade entre passos e entre sessões (curto + longo prazo, editável) | A "memória" |

> O provider de LLM é plugável: Claude (Anthropic) ou OpenAI. A arquitetura não muda.
> A camada de memória está documentada em [`agent-memory.md`](./agent-memory.md).

> O MCP Server resolve a dúvida clássica de "como um agente complementa o Grafana": o Grafana detecta o **quê** (alerta), o agente usa o MCP para investigar o **porquê** (métricas, `explain`, schema) e propor o **e agora** (ação com aprovação).

## MongoDB MCP Server

Servidor oficial que expõe o MongoDB/Atlas como ferramentas MCP. Roda via `npx` e atende tanto o **control plane** (Atlas Admin API) quanto o **data plane**.

Ferramentas típicas usadas pelo Ops Copilot:

| Ferramenta | Uso |
|------------|-----|
| `atlas-list-clusters` / `atlas-create-cluster` | Inventário e provisionamento |
| `atlas-get-metrics` | Métricas do cluster (CPU, conexões, opcounters) |
| `atlas-performance-advisor` | Sugestões de índice |
| `find` / `aggregate` / `explain` | Inspecionar queries e planos de execução |
| `collection-schema` / `db-stats` | Amostrar schema (detecção de anti-patterns) |
| `create-index` | Aplicar índice recomendado (com aprovação) |

### Configuração de exemplo

Veja [`mcp/mongodb-mcp.example.json`](../mcp/mongodb-mcp.example.json). Resumo:

```jsonc
{
  "mcpServers": {
    "mongodb": {
      "command": "npx",
      "args": ["-y", "mongodb-mcp-server"],
      "env": {
        "MDB_MCP_API_CLIENT_ID": "<atlas-service-account-id>",
        "MDB_MCP_API_CLIENT_SECRET": "<atlas-service-account-secret>",
        "MDB_MCP_CONNECTION_STRING": "mongodb+srv://...",
        "MDB_MCP_READ_ONLY": "true"
      }
    }
  }
}
```

> `MDB_MCP_READ_ONLY=true` é o padrão recomendado: o agente observa e recomenda, mas não executa escrita sem aprovação. As credenciais devem ter **menor privilégio** e ser separadas por ambiente.

## Agent Skills

Skills são pastas com `SKILL.md` (instruções) e, opcionalmente, scripts. Elas tornam o comportamento do agente **consistente e auditável**. As deste repo:

| Skill | O que faz | Reutiliza |
|-------|-----------|-----------|
| [`atlas-sizing`](../skills/atlas-sizing) | Recomenda tier + custo a partir do workload | `sizing/sizing_copilot.py` |
| [`schema-anti-pattern-review`](../skills/schema-anti-pattern-review) | Audita modelagem da coleção | `sizing/sizing_copilot.py --json` |
| [`atlas-incident-triage`](../skills/atlas-incident-triage) | Correlaciona métricas + slow query e propõe causa raiz | MCP `explain`, `atlas-get-metrics` |

## Tiering de segurança (produção)

A mesma filosofia de guardrail da landing zone:

1. **Advisory (read-only)** — padrão. O agente só observa e recomenda (`MDB_MCP_READ_ONLY=true`).
2. **Ação com aprovação humana** — mudanças de risco médio (criar índice, ajustar alerta) ficam atrás de aprovação — reaproveitando o fluxo de aprovação do Maestro.
3. **Autônomo em prod** — desabilitado. Ações destrutivas (escalar, dropar, restore) nunca são autônomas; o agente gera um plano e um humano aprova.

Toda ação é registrada no **SIEM** com a credencial de menor privilégio do agente.

## Referências

- MongoDB MCP Server: https://www.mongodb.com/docs/mcp-server/
- Anthropic Agent Skills: https://docs.claude.com/en/docs/agents-and-tools/agent-skills
