# Maestro — Atlas Landing Zone Starter Kit

> **Self-service Atlas, orchestrated.**
> Plataforma de automação de deployments e governança para MongoDB Atlas — protótipo de UX + starter kit de Infraestrutura como Código (IaC) pronto para começar a implantar.

Este repositório acompanha o protótipo **Maestro** e entrega artefatos reais para iniciar uma *Atlas Landing Zone* (acesso self-service, frictionless e governado ao MongoDB Atlas), inspirada na arquitetura de referência do programa Enterprise Flywheel da MongoDB.

> ⚠️ **Aviso:** "Maestro" é um nome de protótipo **não-oficial**. Não é um produto da MongoDB. Baseia-se publicamente nos conceitos de *Atlas Landing Zone / Developer Acceleration*.

---

## O que tem aqui

| Pasta | O que é | Status |
|-------|---------|--------|
| [`demo/`](./demo) | Protótipo **Maestro** (HTML único) — abre no navegador, demonstra a experiência completa | 🟢 Demo navegável |
| [`terraform/`](./terraform) | Módulos Terraform reais para provisionar a landing zone | 🟢 Atlas runnable · 🟡 Rede precisa de credenciais |
| [`templates/`](./templates) | Templates do catálogo (`.tfvars`) espelhando os do Maestro | 🟢 Runnable |
| [`sizing/`](./sizing) | Copilot de sizing/custo via **Anthropic API (Claude)** | 🟢 Runnable |
| [`.github/workflows/`](./.github/workflows) | Esteira CI/CD (GitHub Actions) — `plan` no PR, `apply` com aprovação | 🟢 Pronto |
| [`skills/`](./skills) | **Agent Skills** (playbooks): atlas-sizing, schema-review, incident-triage | 🟢 Pronto |
| [`mcp/`](./mcp) | Config de exemplo do **MongoDB MCP Server** (Ops Copilot Day-2) | 🟢 Pronto |
| [`docs/`](./docs) | Arquitetura, Azure AD, Grafana e [Ops Copilot (MCP + Skills)](./docs/agents-mcp-skills.md) | 📄 Guia para o cliente |

### O que é genuinamente "rodável hoje" vs. o que o cliente preenche

Tudo que depende **apenas do MongoDB Atlas + Claude** já está pronto para executar (você tem essas credenciais):

- ✅ Provisionar projeto, cluster, usuários, IP access list e backup/PITR via Terraform.
- ✅ Recomendação de tier e estimativa de custo via Claude.
- ✅ Pipeline de `plan`/`apply` no GitHub Actions.

O que depende de acessos do **ambiente do cliente** vai como **módulo parametrizado + documentação** (formato padrão de entrega de uma landing zone):

- 🟡 **VPC Peering / PrivateLink (AWS):** precisa das credenciais AWS e dos IDs de VPC do cliente → [`terraform/modules/network-aws`](./terraform/modules/network-aws).
- 🟡 **Identidade federada (Azure AD):** configurada no tenant do cliente → [`docs/identity-azure-ad.md`](./docs/identity-azure-ad.md).
- 🟡 **Observabilidade (Grafana):** datasource na instância do cliente → [`docs/observability-grafana.md`](./docs/observability-grafana.md).

---

## Arquitetura (planos de controle)

Baseado nas camadas da Atlas Landing Zone:

```
┌──────────────────────────────────────────────────────────────┐
│  Developer Control Plane   → Maestro (catálogo + portal)       │
├──────────────────────────────────────────────────────────────┤
│  Integration & Delivery    → GitHub Actions + Terraform        │
├──────────────────────────────────────────────────────────────┤
│  Security & Identity Plane → Azure AD (SSO) + BYOK + RBAC      │
├──────────────────────────────────────────────────────────────┤
│  Observability Plane       → Grafana / Atlas metrics           │
├──────────────────────────────────────────────────────────────┤
│  Resource Plane            → MongoDB Atlas (cluster + rede)     │
└──────────────────────────────────────────────────────────────┘
```

Os 6 pilares de design (Infra, Application, Security, IaC/Tooling, **Financial/FinOps**, People) estão refletidos nos templates e guardrails.

### Day-2: Ops Copilot (agentes de IA)

Além de provisionar (Day 0/1), o Maestro opera o Atlas em produção com um agente: o **MongoDB MCP Server** dá as ferramentas (métricas, schema, `explain`, índices), as **Agent Skills** são os playbooks, e o Claude raciocina — sempre com **ação em prod sob aprovação humana**. Veja [`docs/agents-mcp-skills.md`](./docs/agents-mcp-skills.md).

---

## Quickstart (Day 1)

### 1. Demo
Abra `demo/maestro.html` no navegador. Não precisa instalar nada.

### 2. Provisionar um cluster Atlas (real)

```bash
cd terraform

# Credenciais do Atlas (Programmatic API Key da sua Organização/Projeto)
export MONGODB_ATLAS_PUBLIC_KEY="xxxx"
export MONGODB_ATLAS_PRIVATE_KEY="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

terraform init
terraform plan  -var-file=environments/dev.tfvars
terraform apply -var-file=environments/dev.tfvars
```

> Para usar um template do catálogo, passe `-var-file=../templates/oltp-prod.tfvars` (veja [`templates/`](./templates)).

### 3. Recomendação de sizing com Claude

```bash
cd sizing
pip install -r requirements.txt
export ANTHROPIC_API_KEY="sk-ant-..."
python sizing_copilot.py "app de pedidos, 400GB de dados, working set 50GB, 3000 ops/s, pico 5000 conexões, prod em São Paulo"

# Ou analise um documento JSON (estima volume + detecta anti-patterns de modelagem):
python sizing_copilot.py --json sample-order.json --docs 10000000
```

---

## Day 2 — Ops Copilot (operação com IA)

Provisionar é só o começo (Day 0/1). O **Ops Copilot** opera o Atlas **em produção** com segurança, usando três peças:

| Peça | Papel | Analogia |
|------|-------|----------|
| **MongoDB MCP Server** | Ferramentas para o agente ler e agir no Atlas (métricas, schema, `explain`, índices) | As "mãos" |
| **Agent Skills** | Playbooks que ensinam procedimentos repetíveis | Os "manuais" |
| **Claude** | Raciocínio, correlação e decisão | O "cérebro" |

> Resolve a dúvida clássica de "como um agente complementa o Grafana": o Grafana detecta o **quê** (o alerta), o agente usa o MCP para investigar o **porquê** (métricas, `explain`, schema) e propor o **e agora** (ação com aprovação humana).

**Ferramentas do MongoDB MCP Server** usadas pelo Ops Copilot: `atlas-list-clusters`, `atlas-create-cluster`, `atlas-get-metrics`, `atlas-performance-advisor`, `find`, `aggregate`, `explain`, `collection-schema`, `create-index`.

**Agent Skills incluídas:** [`atlas-sizing`](./skills/atlas-sizing), [`schema-anti-pattern-review`](./skills/schema-anti-pattern-review), [`atlas-incident-triage`](./skills/atlas-incident-triage).

**Segurança em camadas:** o agente é *read-only* por padrão; ações de risco (criar índice, escalar) exigem **aprovação humana**; ações destrutivas em produção nunca são autônomas. Toda ação é auditada no SIEM com credencial de menor privilégio.

📖 Arquitetura completa + configuração do MCP Server: [`docs/agents-mcp-skills.md`](./docs/agents-mcp-skills.md).

---

## Pré-requisitos

- [Terraform](https://developer.hashicorp.com/terraform/downloads) >= 1.5
- Conta MongoDB Atlas + [Programmatic API Key](https://www.mongodb.com/docs/atlas/configure-api-access/)
- (Sizing) Python 3.10+ e uma `ANTHROPIC_API_KEY`
- (Rede/AD/Grafana) credenciais do ambiente do cliente

## Segurança

Nunca faça commit de segredos. As API keys entram via variáveis de ambiente ou *secrets* do GitHub. Veja `.gitignore` — `*.tfstate`, `*.tfvars` de produção e arquivos `.env` são ignorados por padrão.

## Licença

Protótipo para fins de demonstração. Adapte livremente ao seu cliente.
