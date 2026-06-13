"""Testes do modo auto-embedding (provedor 'atlas')."""
import pytest
from maestro_agent.config import Settings, ConfigError
from maestro_agent.memory.atlas_index import index_definition
from maestro_agent.memory.store import build_vector_search_stage

ENV_AUTO = {
    "MAESTRO_EMBEDDING_PROVIDER": "atlas",
    "MAESTRO_MEMORY_BACKEND": "atlas",
    "MONGODB_URI": "mongodb+srv://h",
}


def test_auto_embedding_exige_backend_atlas():
    with pytest.raises(ConfigError, match="auto-embedding"):
        Settings.from_env(env={"MAESTRO_EMBEDDING_PROVIDER": "atlas"})


def test_indice_autoembed_aponta_para_o_texto():
    d = index_definition(Settings.from_env(env=ENV_AUTO))
    f = d["definition"]["fields"][0]
    assert f["type"] == "autoEmbed" and f["path"] == "text" and f["model"] == "voyage-4"
    assert "numDimensions" not in f


def test_estagio_modo_cliente_usa_queryVector():
    s = Settings.from_env(env={})
    stage = build_vector_search_stage(s, query_vector=[0.1], query_text="x", k=3)["$vectorSearch"]
    assert stage["path"] == "embedding" and "queryVector" in stage and "query" not in stage


def test_estagio_modo_auto_usa_texto_puro():
    s = Settings.from_env(env=ENV_AUTO)
    stage = build_vector_search_stage(s, query_vector=None, query_text="cpu alta", k=3,
                                      scope="cluster")["$vectorSearch"]
    assert stage["path"] == "text"
    assert stage["query"] == {"text": "cpu alta"}
    assert stage["model"] == "voyage-4"
    assert "queryVector" not in stage and stage["filter"] == {"scope": "cluster"}


def test_modelo_configuravel():
    env = dict(ENV_AUTO, MAESTRO_AUTOEMBED_MODEL="voyage-4-lite")
    d = index_definition(Settings.from_env(env=env))
    assert d["definition"]["fields"][0]["model"] == "voyage-4-lite"
