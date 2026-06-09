# Changelog da demo — camadas plugáveis, memória do agente e LLM swappable

Este documento registra as modificações feitas no protótipo (`demo/maestro.html`)
na rodada de extensão da tech stack. O objetivo foi tornar o Maestro adaptável
ao ambiente de produção de cada cliente, sem alterar o core da plataforma.

> Princípio central: **core estável + conectores plugáveis.** Adicionar um provider
> (um IdP, um backend de métricas, uma nuvem) não muda o Maestro — muda apenas a
> configuração específica do ambiente.

---

## 1. Tela de boas-vindas / onboarding (nova)

Uma tela de apresentação aparece **antes do login** (`#welcome → #login → #app`;
o logout retorna ao `#welcome`). Ela serve como a "capa" do protótipo: o
desenvolvedor entende o que existe antes de entrar.

- **Definição de landing zone** logo abaixo do tagline, baseada na
  [documentação oficial](https://www.mongodb.com/docs/atlas/architecture/current/landing-zone/):
  um ambiente de nuvem pré-configurado e *well-architected* que define, de antemão,
  os requisitos de segurança, confiabilidade, performance e custo da organização.
- **Catálogo de 6 camadas plugáveis** (cards), cada uma listando os conectores já
  codados, com indicador de prontidão e um *hint* de deployment apontando onde
  configurar aquilo no repo.
- **Legenda de prontidão** (ver seção 4).
- CTAs: **Começar** (`enterLogin()`) e **Já conheço — ir direto à demo** (`skipToApp()`).
- Link para a documentação oficial do Atlas Landing Zone no selo "Protótipo não-oficial".

## 2. Camadas plugáveis estendidas

A tech stack foi expandida para cobrir os ambientes de produção mais comuns:

| Camada | Conectores codados | Roda só com Atlas? |
|--------|--------------------|--------------------|
| **Autenticação & Identidade** | Microsoft Entra ID / AD, Okta, AWS IAM, Google Workspace | Não — requer IdP do cliente |
| **Observabilidade** | Atlas metrics (Prometheus nativo), Grafana, Prometheus, Datadog | Atlas metrics sim; demais não |
| **Base de conhecimento (RAG)** | Atlas Vector Search, Confluence, SharePoint | Vector Search sim; fontes não |
| **Cloud & Pareamento de rede** | AWS, GCP, Azure | Não — requer credencial da nuvem |
| **FinOps** | Atlas Billing APIs, chargeback por tag, right-sizing | Sim |
| **Camada de agentes (IA)** | MCP Server, Agent Skills, memória curto/longo prazo | Sim (Atlas + chave de LLM) |

Essas opções aparecem também na tela **Guardrails & Segurança** (seção "Conectores
plugáveis") e nas telas de **Observabilidade** e **Base de conhecimento**.

## 3. Memória do agente (nova tela)

A peça que conecta os quatro conceitos de agente (MCP, Skills, Context Engineering,
memória) num lugar concreto e didático. Acessível pelo item de menu **"Memória do agente"**.

Inspirada nos componentes de um agente (**percepção · ferramentas · memória**) e na
interface do Claude (**memória · instruções · arquivos**). A característica central é
que **tudo é editável, observável e auditável** — o desenvolvedor vê o que o agente
"sabe", corrige o que estiver errado e expira o que não vale mais.

Três conceitos, três peças de infraestrutura:

- **Memória de longo prazo** — fatos persistentes (decisões de tuning, baselines,
  políticas), recuperáveis por *vector search*. Editáveis: ver / editar / fixar / esquecer.
- **Memória de curto prazo** — estado da sessão de triagem em andamento
  (Research → Plan → Implement). Efêmera, vive no *checkpointer*.
- **Namespaces hierárquicos** — `org → projeto → cluster`, com herança: um fato no
  escopo da organização vale para todos os clusters abaixo.

O **Ops Copilot** agora descreve a memória como a **4ª peça** (mãos / manuais /
cérebro / **memória**), ao lado das ferramentas (MCP), playbooks (Skills) e
raciocínio (LLM).

> **Importante:** nesta tela tudo ainda é *mock*. A implementação real (schema MongoDB,
> checkpointer LangGraph, índice de Vector Search, skill `memory-curator`) é a próxima
> fase do projeto. Ver "Próximos passos".

## 4. Legenda de prontidão

A cor da bolinha em cada conector indica prontidão **real**, não um estado arbitrário:

- 🟢 **Roda com MongoDB Atlas e suas APIs** — funciona com as credenciais que você já tem.
- 🟡 **Requer instalação da ferramenta ou credencial de acesso no seu ambiente** —
  o conector está codado, mas precisa de acesso à ferramenta do cliente.

Essa distinção é coerente com a divisão "rodável hoje vs. cliente preenche" que o
formato de entrega de uma landing zone já assume.

## 5. Provider de LLM plugável (Claude ou OpenAI)

O provider de raciocínio deixou de ser fixo no Claude. Agora é **swappable**:

- No protótipo: `Providers.llm` com `provider: 'claude' | 'openai'`
  (`Providers.claude` foi mantido como *alias* retrocompatível).
- A camada de agentes precisa de `ANTHROPIC_API_KEY` (Claude) **ou** `OPENAI_API_KEY` (OpenAI).
- A UI não muda ao trocar de provider.

---

## Aderência à Atlas Landing Zone oficial

As mudanças seguem as sete considerações do framework oficial (hierarquia
org/projeto/cluster, segurança, compliance, confiabilidade/DR, billing/FinOps,
retenção de dados e observabilidade/auditoria).

**Nota para a fase de código:** os três exemplos oficiais de landing zone
(GCP FAST, AWS Landing Zone, Azure baseline) usam **Private Endpoints** como padrão
de conectividade. Portanto, os futuros módulos `network-gcp` e `network-azure`
devem ter Private Endpoint / PSC como padrão, não peering simples.

---

## Próximos passos (não feitos ainda)

1. **Módulos Terraform** para os novos providers, para que os caminhos citados nos
   *hints* da tela de boas-vindas sejam reais (hoje só existe `network-aws`):
   - `terraform/modules/identity/` → Okta, AWS IAM, Google Workspace
   - `terraform/modules/network-gcp` e `network-azure` (Private Endpoint por padrão)
   - módulos de observabilidade para Datadog e Prometheus
2. **Dar vida à camada de agentes** (sai do mock):
   - Schema MongoDB para a memória de longo prazo
   - Checkpointer LangGraph (`langgraph-checkpoint-mongodb`) para a memória de curto prazo
   - Índice de Atlas Vector Search + modelo de embedding (Voyage AI ou OpenAI)
   - Skill `memory-curator` (escreve / edita / expira fatos)
