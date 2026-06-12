"""Testes da memoria de curto prazo. Pulam se langgraph nao estiver
instalado (extra [graph]); a suite do nucleo continua rodando sem ele."""
import pytest

langgraph = pytest.importorskip("langgraph")

from typing import Annotated, TypedDict
import operator

from langgraph.graph import StateGraph, START, END

from maestro_agent.config import Settings
from maestro_agent.memory.short_term import build_checkpointer, session_config


class S(TypedDict):
    log: Annotated[list[str], operator.add]


def two_step_graph(checkpointer, interrupt=()):
    g = StateGraph(S)
    g.add_node("a", lambda s: {"log": ["a"]})
    g.add_node("b", lambda s: {"log": ["b"]})
    g.add_edge(START, "a")
    g.add_edge("a", "b")
    g.add_edge("b", END)
    return g.compile(checkpointer=checkpointer, interrupt_before=list(interrupt))


def test_backend_local_e_memorysaver():
    cp = build_checkpointer(Settings.from_env(env={}))
    assert type(cp).__name__ in ("MemorySaver", "InMemorySaver")


def test_estado_persiste_e_retoma_na_mesma_thread():
    cp = build_checkpointer(Settings.from_env(env={}))
    cfg = session_config("t-1")
    g1 = two_step_graph(cp, interrupt=("b",))
    g1.invoke({"log": []}, cfg)                       # roda "a", para antes de "b"
    assert g1.get_state(cfg).next == ("b",)

    g2 = two_step_graph(cp, interrupt=("b",))          # "outro processo"
    assert g2.get_state(cfg).values["log"] == ["a"]    # recuperou
    final = g2.invoke(None, cfg)                       # retoma
    assert final["log"] == ["a", "b"]


def test_threads_diferentes_nao_se_misturam():
    cp = build_checkpointer(Settings.from_env(env={}))
    g = two_step_graph(cp)
    g.invoke({"log": []}, session_config("t-A"))
    g.invoke({"log": []}, session_config("t-B"))
    a = g.get_state(session_config("t-A")).values["log"]
    b = g.get_state(session_config("t-B")).values["log"]
    assert a == ["a", "b"] and b == ["a", "b"]
    assert g.get_state(session_config("t-C")).values == {}
