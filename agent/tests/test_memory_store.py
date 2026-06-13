import pytest
from maestro_agent.config import Settings
from maestro_agent.memory import MemoryFact, LocalMemoryStore
from maestro_agent.providers import create_embedding_provider
from maestro_agent.security.audit import AuditLog, NullSink
from maestro_agent.security.redaction import SecretDetected

NS = {"org": "contoso", "project": "payments", "cluster": "fraud-ml-prod"}


def make_store():
    settings = Settings.from_env(env={"MAESTRO_AUDIT_SINK": "null"})
    embedder = create_embedding_provider("local", settings)
    sink = NullSink()
    store = LocalMemoryStore(settings, embedder, AuditLog(sink))
    return store, sink


def fact(text, scope="cluster", kind="fato"):
    return MemoryFact(scope=scope, kind=kind, text=text, source="teste", namespace=NS)


def test_ingest_e_search():
    store, sink = make_store()
    store.ingest([
        fact("Baseline de CPU em horario comercial: 55-65%.", kind="baseline"),
        fact("Restore de PITR testado, RTO 18 minutos."),
    ])
    hits = store.search("qual o uso normal de CPU?", k=1)
    assert hits[0]["kind"] == "baseline"
    actions = [e["action"] for e in sink.events]
    assert actions.count("memory.write") == 2
    assert "memory.search" in actions


def test_filtro_de_scope():
    store, _ = make_store()
    store.ingest([
        fact("Politica de FinOps da organizacao.", scope="org", kind="política"),
        fact("Fato do cluster.", scope="cluster"),
    ])
    hits = store.search("finops", k=5, scope="org")
    assert all(h["scope"] == "org" for h in hits)


def test_segredo_negado_e_auditado():
    store, sink = make_store()
    with pytest.raises(SecretDetected):
        store.ingest([fact("connection: mongodb+srv://u:Hunter2@h/db")])
    denied = [e for e in sink.events if e["action"] == "memory.write_denied"]
    assert denied and denied[0]["reason"] == "secret_detected"
    assert "Hunter2" not in str(sink.events)


def test_schema_rejeita_invalido():
    with pytest.raises(ValueError):
        MemoryFact(scope="datacenter", kind="fato", text="x", source="t", namespace=NS)
    with pytest.raises(ValueError):
        MemoryFact(scope="cluster", kind="fato", text="x", source="t", namespace={"org": "a"})
