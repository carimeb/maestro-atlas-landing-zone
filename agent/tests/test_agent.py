"""Testes do agente de triagem (passo 3). Offline: LLM stub + tudo local."""
import pytest

pytest.importorskip("langgraph")

from maestro_agent.agent import build_triage_agent
from maestro_agent.config import Settings
from maestro_agent.memory import MemoryFact

NS = {"org": "contoso", "project": "payments", "cluster": "fraud-ml-prod"}


def make_agent():
    settings = Settings.from_env(env={"MAESTRO_AUDIT_SINK": "null"})
    agent = build_triage_agent(settings, namespace=NS)
    agent.store.ingest([MemoryFact(
        "cluster", "decisão",
        "Índice { user_id: 1 } resolveu COLLSCAN na coleção transactions.",
        "atlas-incident-triage", NS,
    )])
    return agent


def test_para_no_gate_e_recall_popula_fatos():
    agent = make_agent()
    cfg = agent.config("t-1")
    agent.graph.invoke({"incident": "queries lentas em transactions",
                        "recalled": [], "analysis": "", "log": []}, cfg)
    state = agent.graph.get_state(cfg)
    assert state.next == ("apply",)
    assert len(state.values["recalled"]) >= 1
    assert state.values["analysis"]            # reason rodou antes do gate


def test_aprovacao_conclui_e_learn_grava_na_ltm():
    agent = make_agent()
    cfg = agent.config("t-2")
    agent.graph.invoke({"incident": "CPU alta em transactions",
                        "recalled": [], "analysis": "", "log": []}, cfg)
    final = agent.graph.invoke(None, cfg)      # aprovacao humana
    assert any("learn" in line for line in final["log"])
    hits = agent.store.search("CPU alta em transactions", k=3)
    assert any(h["source"] == "ops-copilot-triage" for h in hits)


def test_eventos_de_auditoria_do_agente():
    agent = make_agent()
    cfg = agent.config("t-3")
    agent.graph.invoke({"incident": "x", "recalled": [], "analysis": "", "log": []}, cfg)
    agent.graph.invoke(None, cfg)
    actions = [e["action"] for e in agent.audit._sink.events]
    for expected in ("agent.recall", "agent.reason", "agent.apply", "agent.learn"):
        assert expected in actions
