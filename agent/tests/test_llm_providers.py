import pytest
from maestro_agent.config import Settings, ConfigError
from maestro_agent.providers import available_llms, create_llm_provider


def test_llms_embutidos_registrados():
    assert {"local", "anthropic", "openai"} <= set(available_llms())


def test_stub_local_e_deterministico():
    p = create_llm_provider("local", Settings.from_env(env={}))
    out = p.complete("sys", "FATO 1: x\nFATO 2: y")
    assert "2 fato(s)" in out and out == p.complete("sys", "FATO 1: x\nFATO 2: y")


def test_resolucao_auto_de_llm():
    assert Settings.from_env(env={}).llm_provider_resolved() == "local"
    assert Settings.from_env(env={"ANTHROPIC_API_KEY": "x"}).llm_provider_resolved() == "anthropic"
    assert Settings.from_env(env={"OPENAI_API_KEY": "x"}).llm_provider_resolved() == "openai"


def test_llm_explicito_sem_chave_falha_cedo():
    with pytest.raises(ConfigError, match="ANTHROPIC_API_KEY"):
        Settings.from_env(env={"MAESTRO_LLM_PROVIDER": "anthropic"})
