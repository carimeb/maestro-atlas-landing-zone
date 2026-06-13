"""
Agente de triagem (passo 3): memoria longa + memoria curta + LLM plugavel.

O ciclo completo de docs/agent-memory.md, em quatro nos:

  recall  -> busca semantica na memoria de LONGO prazo (passo 1) com o texto
             do incidente. Os fatos recuperados entram no estado. Isto e
             contextual engineering na pratica: o agente nao raciocina no
             vacuo, raciocina sobre o que a operacao ja sabe.
  reason  -> o LLM (anthropic | openai | stub local) recebe incidente +
             fatos e produz diagnostico e acao recomendada.
  apply   -> gate de APROVACAO HUMANA (interrupt_before, passo 2). No passo
             3 o no apenas registra a acao aprovada; a execucao real via
             MongoDB MCP Server entra no passo 4.
  learn   -> o resultado da triagem vira um fato novo na memoria de longo
             prazo. Passa pelas mesmas garantias de qualquer escrita:
             validacao de schema, deteccao de segredos e auditoria. Na
             proxima triagem parecida, o recall encontra este fato.

A memoria CURTA (checkpointer) sustenta tudo: o estado sobrevive entre o
gate e a aprovacao, e a queda de processo nao perde a investigacao.
"""

from __future__ import annotations

import operator
from dataclasses import dataclass
from typing import Annotated, TypedDict

from langgraph.graph import StateGraph, START, END

from ..config import Settings
from ..memory.schema import MemoryFact
from ..memory.short_term import build_checkpointer
from ..memory.store import MemoryStore, build_memory_store
from ..providers.base import LLMProvider, create_llm_provider
from ..security.audit import AuditLog, build_audit

SYSTEM_PROMPT = (
    "Você é o Ops Copilot do Maestro, responsável por triagem de incidentes "
    "em clusters MongoDB Atlas. Receberá um incidente e fatos da memória "
    "operacional (decisões anteriores, baselines, políticas, pendências). "
    "Responda em português, em dois itens curtos: (1) causa provável, "
    "fundamentada nos fatos quando aplicável; (2) ação recomendada. "
    "Nunca proponha ação destrutiva. Toda ação será submetida a aprovação humana."
)


class TriageState(TypedDict):
    incident: str
    recalled: list[dict]
    analysis: str
    log: Annotated[list[str], operator.add]


@dataclass
class TriageAgent:
    """Agente compilado + dependencias expostas (util em exemplo e teste)."""

    graph: object
    store: MemoryStore
    llm: LLMProvider
    audit: AuditLog
    namespace: dict[str, str]

    def config(self, thread_id: str) -> dict:
        return {"configurable": {"thread_id": thread_id}}


def build_triage_agent(
    settings: Settings | None = None,
    namespace: dict[str, str] | None = None,
    store: MemoryStore | None = None,
) -> TriageAgent:
    settings = settings or Settings.from_env()
    namespace = namespace or {"org": "default"}
    store = store or build_memory_store(settings)
    llm = create_llm_provider(settings.llm_provider_resolved(), settings)
    audit = build_audit(settings)

    # -- nos ----------------------------------------------------------------
    def recall(state: TriageState) -> dict:
        hits = store.search(state["incident"], k=3)
        audit.emit("agent.recall", hits=len(hits), incident=state["incident"][:80])
        lines = [f"recall: {len(hits)} fato(s) recuperado(s) da memória longa"]
        lines += [f"  [{h['score']}] ({h['kind']}) {h['text']}" for h in hits]
        return {"recalled": hits, "log": lines}

    def reason(state: TriageState) -> dict:
        facts_block = "\n".join(
            f"FATO {i} ({h['kind']}, fonte {h['source']}): {h['text']}"
            for i, h in enumerate(state["recalled"], 1)
        ) or "FATO nenhum recuperado."
        prompt = f"INCIDENTE: {state['incident']}\n\nMEMÓRIA OPERACIONAL:\n{facts_block}"
        analysis = llm.complete(SYSTEM_PROMPT, prompt)
        audit.emit("agent.reason", provider=llm.name)
        return {"analysis": analysis, "log": [f"reason ({llm.name}): {analysis}"]}

    def apply(state: TriageState) -> dict:
        # Passo 4 substitui este corpo por chamadas reais ao MongoDB MCP Server.
        audit.emit("agent.apply", mode="registro", note="execução real entra no passo 4 via MCP")
        return {"log": ["apply: ação aprovada e registrada (execução via MCP no passo 4)"]}

    def learn(state: TriageState) -> dict:
        summary = state["analysis"].strip().replace("\n", " ")
        fact = MemoryFact(
            scope="cluster",
            kind="decisão",
            text=f"Triagem concluída. Incidente: {state['incident']}. Resultado: {summary}"[:2000],
            source="ops-copilot-triage",
            namespace=namespace,
        )
        store.ingest([fact])  # mesmas garantias: schema, redaction, auditoria
        audit.emit("agent.learn", kind=fact.kind, source=fact.source)
        return {"log": ["learn: resultado gravado na memória de longo prazo"]}

    # -- grafo ----------------------------------------------------------------
    g = StateGraph(TriageState)
    g.add_node("recall", recall)
    g.add_node("reason", reason)
    g.add_node("apply", apply)
    g.add_node("learn", learn)
    g.add_edge(START, "recall")
    g.add_edge("recall", "reason")
    g.add_edge("reason", "apply")
    g.add_edge("apply", "learn")
    g.add_edge("learn", END)

    compiled = g.compile(
        checkpointer=build_checkpointer(settings),
        interrupt_before=["apply"],
    )
    return TriageAgent(graph=compiled, store=store, llm=llm, audit=audit, namespace=namespace)
