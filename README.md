# Maestro: Atlas Landing Zone com camada de agentes

Plataforma de self-service, governança e operação assistida por IA para MongoDB Atlas. Combina uma landing zone em Infraestrutura como Código (Day 0/1) com uma camada de agentes para operação em produção (Day 2).

Aviso: Maestro é um protótipo não oficial. Não é um produto da MongoDB. Baseia-se publicamente nos conceitos de Atlas Landing Zone e Developer Acceleration.

## Posicionamento

O Maestro é a camada de domínio Atlas, projetada para se plugar no Internal Developer Portal (IDP) que o usuário já opera, como o Backstage. A interface em `demo/maestro.html` simula esse portal. A camada de agentes é headless e será exposta por API HTTP para consumo por plugins de portal. Decisão registrada em `docs/adr/0001-integracao-backstage.md`.

## Estrutura do repositório

| Pasta | Conteúdo |
|-------|----------|
| `terraform/` | Módulos para provisionar a landing zone (projeto, cluster, rede, backup) |
| `templates/` | Templates de cluster por perfil de workload (`.tfvars`) |
| `agent/` | Pacote Python `maestro_agent`: memória, agente de triagem, segurança e auditoria |
| `skills/` | Agent Skills: atlas-sizing, schema-anti-pattern-review, atlas-incident-triage, memory-curator |
| `mcp/` | Configuração de exemplo do MongoDB MCP Server |
| `sizing/` | Copilot de recomendação de tier e estimativa de custo |
| `.github/workflows/` | Pipeline CI/CD: plan no pull request, apply com aprovação |
| `docs/` | Arquitetura, ADRs, identidade, observabilidade, memória do agente |
| `demo/` | Simulação do portal (IDP) em HTML único |

## Pré-requisitos

1. Terraform 1.5 ou superior.
2. Conta MongoDB Atlas com Programmatic API Key.
3. Python 3.10 ou superior.
4. Para raciocínio e embeddings reais: `ANTHROPIC_API_KEY` ou `OPENAI_API_KEY`, e `VOYAGE_API_KEY` ou `OPENAI_API_KEY`.
5. Para as camadas plugáveis de identidade, observabilidade e rede: credenciais do ambiente do usuário.

## Reprodução

### 1. Provisionar a landing zone

```bash
cd terraform
export MONGODB_ATLAS_PUBLIC_KEY="xxxx"
export MONGODB_ATLAS_PRIVATE_KEY="xxxx"
terraform init
terraform plan  -var-file=environments/dev.tfvars
terraform apply -var-file=environments/dev.tfvars
```

Para usar um perfil do catálogo, aponte para o template correspondente, por exemplo `-var-file=../templates/oltp-prod.tfvars`.

### 2. Pipeline CI/CD

Configure os secrets `MONGODB_ATLAS_PUBLIC_KEY` e `MONGODB_ATLAS_PRIVATE_KEY` no repositório GitHub. O workflow executa `terraform plan` em pull requests e `terraform apply` após aprovação no environment de produção.

### 3. Camada de agentes

```bash
cd agent
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,graph]"
pytest
```

Os três passos da ordem de aprendizado executam offline, sem chave ou cluster:

```bash
python examples/step1_vector_search.py   # memória de longo prazo (vector search)
python examples/step2_checkpointer.py    # memória de curto prazo (checkpointer)
python examples/step3_agent.py           # agente completo com gate de aprovação
```

Para o caminho de produção, defina as variáveis de `agent/.env.example` (backend Atlas, embeddings Voyage ou OpenAI, LLM Anthropic ou OpenAI) e crie o índice de Vector Search na coleção `agent_memory` com a definição gerada por `maestro_agent.memory.index_definition`.

### 4. Copilot de sizing

```bash
cd sizing
pip install -r requirements.txt
export ANTHROPIC_API_KEY="sk-ant-..."
python sizing_copilot.py "app de pedidos, 400GB de dados, working set 50GB, 3000 ops/s, pico 5000 conexões, prod em São Paulo"
```

Os números de tier e custo são calculados de forma determinística. O LLM apenas redige a recomendação a partir dos fatos calculados.

## Day 2: Ops Copilot

O agente opera o Atlas em produção sobre quatro peças:

| Peça | Papel |
|------|-------|
| MongoDB MCP Server | Ferramentas de leitura e ação no Atlas (métricas, explain, schema, índices) |
| Agent Skills | Playbooks de procedimentos repetíveis |
| LLM (Claude ou OpenAI) | Raciocínio e correlação, plugável por configuração |
| Memória em MongoDB | Curto prazo (checkpointer LangGraph) e longo prazo (Atlas Vector Search), editável e auditável |

O ciclo implementado em `agent/` segue recall, reason, apply e learn: o agente recupera fatos da memória de longo prazo antes de raciocinar, para em um gate de aprovação humana antes de qualquer ação, e grava o resultado da triagem como fato novo. Arquitetura de referência em `docs/agent-memory.md`.

## Camadas plugáveis

O núcleo é estável; integrações entram como módulo parametrizado mais documentação, conforme o ambiente do usuário:

1. Identidade: Microsoft Entra ID, Okta, AWS IAM, Google Workspace.
2. Observabilidade: Atlas metrics, Grafana, Prometheus, Datadog.
3. Base de conhecimento: Atlas Vector Search com Confluence ou SharePoint.
4. Rede: AWS, GCP e Azure, com Private Endpoint ou PSC por padrão.

## Segurança

1. Nenhum segredo em código ou commit. Credenciais entram por variável de ambiente, secret manager ou secrets do GitHub.
2. O agente é read-only por padrão. Ações de risco exigem aprovação humana. Ações destrutivas em produção nunca são autônomas.
3. Toda escrita, negação e busca na memória do agente emite evento de auditoria em JSON Lines, pronto para coleta por SIEM.
4. Textos candidatos a fato passam por detecção de segredos antes da escrita. Connection strings com credencial, chaves de API e material de chave privada são bloqueados.

## Licença

Protótipo para fins de demonstração e aprendizado. Adapte livremente ao seu ambiente.
