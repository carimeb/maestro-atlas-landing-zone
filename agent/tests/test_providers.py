import pytest
from maestro_agent.config import Settings
from maestro_agent.providers import (
    available_embeddings, create_embedding_provider, register_embedding,
)


def test_provedores_embutidos_registrados():
    assert {"local", "voyage", "openai"} <= set(available_embeddings())


def test_local_document_query_dimensoes():
    p = create_embedding_provider("local", Settings.from_env(env={}))
    docs = p.embed_documents(["um", "dois"])
    q = p.embed_query("um")
    assert len(docs) == 2 and len(docs[0]) == p.dimensions == len(q)


def test_provedor_desconhecido_erra_com_lista():
    with pytest.raises(KeyError, match="local"):
        create_embedding_provider("inexistente", Settings.from_env(env={}))


def test_registro_de_novo_provedor():
    @register_embedding("fake")
    class Fake:
        dimensions = 2
        def __init__(self, settings): pass
        def embed_documents(self, texts): return [[1.0, 0.0]] * len(texts)
        def embed_query(self, text): return [1.0, 0.0]

    p = create_embedding_provider("fake", Settings.from_env(env={}))
    assert p.embed_query("x") == [1.0, 0.0]
