# maestro-agent

Camada de agentes do Maestro. Este pacote contém as fundações transversais
sobre as quais os módulos do agente (memória, futuramente checkpointer,
MCP e skills) são construídos.

## Estrutura

```
src/maestro_agent/
  config.py        Configuração central. Env-driven, fail-fast, segredos mascarados.
  providers/       Contrato EmbeddingProvider + registro. Voyage, OpenAI, local.
  security/        Auditoria estruturada (JSON Lines) e detecção de segredos.
  memory/          Memória de longo prazo (schema validado, store local e Atlas)
                   e de curto prazo (checkpointer LangGraph, local e Atlas).
  agent/           Agente de triagem: recall, reason (LLM plugável), gate de
                   aprovação humana e learn (grava o aprendido na LTM).
examples/          Passo 1 da ordem de aprendizado, executável offline.
tests/             Suíte pytest, executável offline.
```

## Instalação

```bash
pip install -e .              # núcleo, sem dependência externa
pip install -e ".[atlas,voyage]"   # produção: pymongo + Voyage AI
pip install -e ".[graph]"          # memória de curto prazo e agente (LangGraph)
pip install -e ".[anthropic]"      # raciocínio via Claude
pip install -e ".[dev]"       # + pytest
```

## Execução

```bash
python examples/step1_vector_search.py     # passo 1: memória longa (offline)
python examples/step2_checkpointer.py      # passo 2: memória curta (offline, requer [graph])
python examples/step3_agent.py             # passo 3: agente completo (offline, requer [graph])
pytest                                      # testes
```

Para o caminho de produção, defina as variáveis de `.env.example` e crie o
índice de Vector Search na coleção `agent_memory`. A definição é gerada por:

```python
from maestro_agent.config import Settings
from maestro_agent.memory import index_definition
print(index_definition(Settings.from_env()))
```

## Princípios

1. Configuração entra por variável de ambiente; nenhum módulo lê `os.environ`
   diretamente. Validação derruba o processo na inicialização, não no meio
   de uma operação.
2. Serviço externo entra por contrato + registro (`providers/base.py`).
   Provedor novo é uma classe registrada, sem editar código existente.
3. Segurança no caminho, não na convenção: todo texto candidato a fato passa
   por detecção de segredos antes da escrita; toda escrita, negação e busca
   emite evento de auditoria em JSON Lines, pronto para coleta por SIEM.
4. Núcleo sem dependência obrigatória. Integrações são extras opcionais.
5. Módulo novo entra com testes. A suíte roda offline.

## Adicionando um módulo novo

1. Crie o subpacote em `src/maestro_agent/<modulo>/`.
2. Consuma `Settings` (novos campos entram em `config.py` com validação).
3. Serviço externo novo: defina o contrato em `providers/` e registre.
4. Escreva eventos de auditoria para ações relevantes (`dominio.verbo`).
5. Adicione testes em `tests/` que rodem offline.
