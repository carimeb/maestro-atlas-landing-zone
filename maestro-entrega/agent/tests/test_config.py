import pytest
from maestro_agent.config import Settings, ConfigError


def test_defaults_validos():
    s = Settings.from_env(env={})
    assert s.memory_backend == "local"
    assert s.resolved_embedding_provider() == "local"


def test_auto_resolve_por_chave():
    s = Settings.from_env(env={"VOYAGE_API_KEY": "x"})
    assert s.resolved_embedding_provider() == "voyage"
    s = Settings.from_env(env={"OPENAI_API_KEY": "x"})
    assert s.resolved_embedding_provider() == "openai"


def test_atlas_sem_uri_falha_cedo():
    with pytest.raises(ConfigError, match="MONGODB_URI"):
        Settings.from_env(env={"MAESTRO_MEMORY_BACKEND": "atlas"})


def test_backend_invalido_falha():
    with pytest.raises(ConfigError):
        Settings.from_env(env={"MAESTRO_MEMORY_BACKEND": "redis"})


def test_repr_mascara_segredo():
    s = Settings.from_env(env={"MONGODB_URI": "mongodb+srv://u:SENHA@h", 
                               "MAESTRO_MEMORY_BACKEND": "atlas"})
    assert "SENHA" not in repr(s)
    assert "***" in repr(s)
