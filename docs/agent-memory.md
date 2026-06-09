# Memória do agente — arquitetura de referência

> **Estado atual:** desenho + UI mockada (tela "Memória do agente" em `demo/maestro.html`).
> Este documento define a arquitetura **antes** da implementação, para servir de
> referência na fase de código. Nada aqui está implementado ainda.

A camada de memória dá **continuidade** ao Ops Copilot. Ela espelha os componentes de
um agente (**percepção · ferramentas · memória**) e a interface do Claude
(**memória · instruções · arquivos**). O princípio que a diferencia: a memória é
**editável, observável e auditável** — não é uma caixa-preta.

## Três conceitos → três peças de infraestrutura

Confundir estes três é o erro mais comum. Eles são distintos:

### 1. Memória de curto prazo (estado da sessão)

O estado da investigação em andamento (Research → Plan → Implement). Se a sessão cair,
o agente retoma de onde parou.

- **Implementação:** checkpointer do LangGraph com persistência em MongoDB
  (`langgraph-checkpoint-mongodb`).
- **Onde mora:** uma coleção no Atlas, com um documento de checkpoint por passo da *thread*.
- **Ciclo de vida:** efêmero — expira ao fim da sessão.

### 2. Memória de longo prazo (fatos persistentes)

Fatos que valem entre sessões: decisões de tuning, baselines, políticas, pendências.
Precisam ser recuperáveis por **significado**, não só por palavra-chave.

- **Implementação:** coleção `agent_memory` no Atlas + índice de **Atlas Vector Search**
  sobre os embeddings + um modelo de embedding (Voyage AI ou OpenAI).
- **Editável:** operações de CRUD expostas na UI — ver / editar / fixar / esquecer.
  Correções humanas não são sobrescritas pelo agente.

### 3. Namespaces hierárquicos (escopo dos fatos)

`org → projeto → cluster`, com **herança**: um fato no escopo da organização vale para
todos os clusters abaixo; um cluster pode ter fatos específicos que complementam.

## Schema proposto (memória de longo prazo)

> Rascunho para a fase de código — sujeito a refinamento.

```jsonc
// coleção: agent_memory
{
  "_id": ObjectId,
  "scope": "cluster",                 // "org" | "project" | "cluster"
  "namespace": {                       // identifica o nó na hierarquia
    "org": "contoso-atlas-prod",
    "project": "payments",
    "cluster": "fraud-ml-prod"
  },
  "kind": "decisão",                   // decisão | baseline | política | pendência | fato
  "text": "Índice { user_id: 1 } resolveu COLLSCAN na coleção transactions.",
  "embedding": [/* vetor do campo text */],
  "source": "atlas-incident-triage",   // skill ou "dev (manual)" / "dev (editado)"
  "pinned": true,                       // fixado pelo humano (não expira)
  "created_at": ISODate,
  "updated_at": ISODate
}
```

Índice de Vector Search sobre `embedding`, com filtro por `namespace` para respeitar o escopo.

## Fluxo

1. **Escrita** — skills (ex.: `memory-curator`) e o resultado de cada triagem gravam
   fatos relevantes. Nunca segredos.
2. **Recuperação** — antes de raciocinar, o agente faz *vector search* no namespace
   ativo (e herda do escopo pai).
3. **Edição humana** — o dev edita / apaga / fixa fatos pela UI.
4. **Auditoria** — toda escrita/edição é registrada no SIEM com autor e timestamp.

## Tech stack para a implementação

| Componente | Ferramenta |
|------------|------------|
| Orquestração do agente | LangGraph (Python) |
| Memória de curto prazo | `langgraph-checkpoint-mongodb` |
| Memória de longo prazo | `langchain-mongodb` (`MongoDBStore`) + Atlas Vector Search |
| Driver | `pymongo` |
| Embeddings | `voyageai` ou `openai` |
| LLM | `anthropic` ou `openai` (plugável) |
| Ferramentas do agente | MongoDB MCP Server |

## Ordem de aprendizado recomendada

Não montar tudo junto. Sequência que evita frustração:

1. **Vector search puro** — sem agente: salvar documentos com embeddings e fazer busca
   semântica. É o coração da memória de longo prazo.
2. **Checkpointer** — um grafo LangGraph mínimo que salva estado no Mongo (curto prazo).
3. **Juntar os dois** — um agente que busca na memória longa antes de raciocinar e
   grava o que aprendeu ao terminar.
4. **MCP + Skills** — conectar as ferramentas reais do Atlas e a skill `memory-curator`.

## Referências (fornecidas pelo cliente)

- Build AI memory systems with MongoDB Atlas + Claude
- Long-term memory for agents with LangGraph + MongoDB
- Checkpointers e retrievers nativos com LangChain + MongoDB
- Atlas Vector Search: https://www.mongodb.com/docs/atlas/atlas-vector-search/
- LangGraph: https://langchain-ai.github.io/langgraph/
