"""
Passo 2: memoria de curto prazo com checkpointer LangGraph.

O grafo abaixo e a triagem de incidente da tela do demo (Research, Plan,
Implement) reduzida ao minimo. Os nos sao deterministicos de proposito:
o objetivo do passo 2 e entender o CHECKPOINTER, nao o LLM. O cerebro
entra no passo 3.

O script demonstra as duas propriedades que justificam a memoria curta:

  1. RETOMADA: executa Research e Plan, "morre", e um SEGUNDO grafo (como
     se fosse outro processo) retoma a mesma thread do ponto exato.
  2. APROVACAO HUMANA: o grafo e compilado com interrupt_before no no
     implement. O estado fica persistido aguardando o humano; a aprovacao
     retoma a execucao.

Execucao offline:   python examples/step2_checkpointer.py
Execucao no Atlas:  MAESTRO_MEMORY_BACKEND=atlas + MONGODB_URI
                    (os checkpoints viram documentos na colecao
                    agent_checkpoints; abra no Atlas e inspecione)
"""

from typing import Annotated, TypedDict
import operator

from langgraph.graph import StateGraph, START, END

from maestro_agent.config import Settings
from maestro_agent.memory.short_term import build_checkpointer, session_config
from maestro_agent.security.audit import build_audit


# ---------------------------------------------------------------------------
# Estado da sessao: e ISTO que o checkpointer persiste a cada passo.
# Annotated[..., operator.add] = campo acumulativo (cada no anexa).
# ---------------------------------------------------------------------------
class TriageState(TypedDict):
    incident: str
    log: Annotated[list[str], operator.add]
    recommendation: str


# ---------------------------------------------------------------------------
# Nos da triagem (deterministicos no passo 2)
# ---------------------------------------------------------------------------
def research(state: TriageState) -> dict:
    return {"log": [
        "Research: CPU 91%, opcounters de query +320% vs baseline",
        "Research: explain na query quente indica COLLSCAN em transactions",
    ]}


def plan(state: TriageState) -> dict:
    return {"log": [
        "Plan: confirmar indice ausente em user_id e propor create-index",
    ]}


def implement(state: TriageState) -> dict:
    rec = "Criar indice { user_id: 1 } em transactions (impacto estimado: p95 -65%)"
    return {"log": [f"Implement: {rec}"], "recommendation": rec}


def build_graph(checkpointer):
    g = StateGraph(TriageState)
    g.add_node("research", research)
    g.add_node("plan", plan)
    g.add_node("implement", implement)
    g.add_edge(START, "research")
    g.add_edge("research", "plan")
    g.add_edge("plan", "implement")
    g.add_edge("implement", END)
    # interrupt_before: o gate de aprovacao humana ANTES da acao.
    return g.compile(checkpointer=checkpointer, interrupt_before=["implement"])


# ---------------------------------------------------------------------------
def main():
    settings = Settings.from_env()
    audit = build_audit(settings)
    checkpointer = build_checkpointer(settings)
    config = session_config("triage-PAY-1042")

    print(f"# backend de memoria curta: {settings.memory_backend}\n")

    # -- Processo 1: comeca a triagem e "morre" antes de terminar ----------
    graph_a = build_graph(checkpointer)
    audit.emit("session.start", thread_id="triage-PAY-1042", graph="triage")
    graph_a.invoke({"incident": "CPU alta no fraud-ml-prod", "log": []}, config)
    print("processo 1 executou e parou no gate de aprovacao. estado salvo:")
    state = graph_a.get_state(config)
    for line in state.values["log"]:
        print(f"  - {line}")
    print(f"  proximo no aguardando: {state.next}\n")

    del graph_a  # simula a queda do processo

    # -- Processo 2: nova instancia, mesma thread, retoma do checkpoint ----
    graph_b = build_graph(checkpointer)
    resumed = graph_b.get_state(config)
    audit.emit("session.resume", thread_id="triage-PAY-1042",
               pending=list(resumed.next))
    print(f"processo 2 recuperou a thread: {len(resumed.values['log'])} passos no log, "
          f"pendente: {resumed.next}")

    # -- Aprovacao humana: retomar a execucao do ponto interrompido --------
    print("aprovacao humana concedida; retomando...\n")
    audit.emit("session.approve", thread_id="triage-PAY-1042", node="implement")
    final = graph_b.invoke(None, config)  # None = continue de onde parou

    print("triagem concluida:")
    for line in final["log"]:
        print(f"  - {line}")
    print(f"\nRECOMENDACAO: {final['recommendation']}")


if __name__ == "__main__":
    main()
