"""
Camada unica de configuracao.

Regras:
  1. Toda configuracao entra por variavel de ambiente (12-factor). Em
     producao, o secret manager do usuario (Vault, AWS Secrets Manager,
     Azure Key Vault) injeta as variaveis; o codigo nao sabe a origem.
  2. Nenhum modulo le os.environ por conta propria. Todos recebem um
     objeto Settings. Isso torna a configuracao testavel e auditavel.
  3. Validacao fail-fast: combinacao invalida derruba o processo na
     inicializacao, com mensagem clara, em vez de falhar no meio de uma
     operacao.
  4. Segredos nunca aparecem em repr(), log ou erro.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field, fields


def _clean_secret(v: str | None) -> str | None:
    """Remove espacos invisiveis (incl. non-breaking space de copy/paste)."""
    if not v:
        return None
    return v.strip(" \t\r\n\u00a0\u200b") or None


class ConfigError(RuntimeError):
    """Configuracao ausente ou inconsistente. Mensagem orientada a acao."""


_VALID_EMBEDDING = ("auto", "voyage", "openai", "local", "atlas")
_VALID_BACKEND = ("local", "atlas")
_VALID_LLM = ("auto", "anthropic", "openai", "local")
_VALID_AUDIT_SINK = ("stdout", "file", "null")

# Campos tratados como segredo: mascarados em repr e nunca logados.
_SECRET_FIELDS = {"mongodb_uri", "voyage_api_key", "openai_api_key", "anthropic_api_key"}


@dataclass(frozen=True)
class Settings:
    # Provedores
    embedding_provider: str = "auto"
    llm_provider: str = "auto"
    llm_model: str | None = None

    # Memoria
    memory_backend: str = "local"
    mongodb_uri: str | None = None
    mongodb_db: str = "maestro"
    memory_collection: str = "agent_memory"
    auto_embed_model: str = "voyage-4"
    vector_index_name: str = "agent_memory_vidx"
    checkpoint_collection: str = "agent_checkpoints"

    # Auditoria
    audit_sink: str = "stdout"
    audit_file: str | None = None

    # Chaves (presenca usada para autodetectar provedor)
    voyage_api_key: str | None = field(default=None, repr=False)
    openai_api_key: str | None = field(default=None, repr=False)
    anthropic_api_key: str | None = field(default=None, repr=False)

    # ------------------------------------------------------------------
    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "Settings":
        """Constroi e valida a partir do ambiente (ou de um dict, em teste)."""
        e = os.environ if env is None else env
        s = cls(
            embedding_provider=e.get("MAESTRO_EMBEDDING_PROVIDER", "auto").lower(),
            llm_provider=e.get("MAESTRO_LLM_PROVIDER", "auto").lower(),
            llm_model=e.get("MAESTRO_LLM_MODEL") or None,
            memory_backend=e.get("MAESTRO_MEMORY_BACKEND", e.get("MEM_BACKEND", "local")).lower(),
            mongodb_uri=_clean_secret(e.get("MONGODB_URI")),
            mongodb_db=e.get("MONGODB_DB", "maestro"),
            memory_collection=e.get("MAESTRO_MEMORY_COLLECTION", "agent_memory"),
            auto_embed_model=e.get("MAESTRO_AUTOEMBED_MODEL", "voyage-4"),
            vector_index_name=e.get("MAESTRO_VECTOR_INDEX", "agent_memory_vidx"),
            checkpoint_collection=e.get("MAESTRO_CHECKPOINT_COLLECTION", "agent_checkpoints"),
            audit_sink=e.get("MAESTRO_AUDIT_SINK", "stdout").lower(),
            audit_file=e.get("MAESTRO_AUDIT_FILE") or None,
            voyage_api_key=_clean_secret(e.get("VOYAGE_API_KEY")),
            openai_api_key=_clean_secret(e.get("OPENAI_API_KEY")),
            anthropic_api_key=_clean_secret(e.get("ANTHROPIC_API_KEY")),
        )
        s.validate()
        return s

    # ------------------------------------------------------------------
    def validate(self) -> None:
        if self.embedding_provider not in _VALID_EMBEDDING:
            raise ConfigError(
                f"MAESTRO_EMBEDDING_PROVIDER invalido: {self.embedding_provider!r}. "
                f"Valores aceitos: {', '.join(_VALID_EMBEDDING)}."
            )
        if self.memory_backend not in _VALID_BACKEND:
            raise ConfigError(
                f"MAESTRO_MEMORY_BACKEND invalido: {self.memory_backend!r}. "
                f"Valores aceitos: {', '.join(_VALID_BACKEND)}."
            )
        if self.audit_sink not in _VALID_AUDIT_SINK:
            raise ConfigError(
                f"MAESTRO_AUDIT_SINK invalido: {self.audit_sink!r}. "
                f"Valores aceitos: {', '.join(_VALID_AUDIT_SINK)}."
            )
        if self.memory_backend == "atlas" and not self.mongodb_uri:
            raise ConfigError(
                "MAESTRO_MEMORY_BACKEND=atlas exige MONGODB_URI. "
                "Defina a connection string via secret manager ou variavel de ambiente."
            )
        if self.audit_sink == "file" and not self.audit_file:
            raise ConfigError("MAESTRO_AUDIT_SINK=file exige MAESTRO_AUDIT_FILE.")
        if self.embedding_provider == "voyage" and not self.voyage_api_key:
            raise ConfigError("MAESTRO_EMBEDDING_PROVIDER=voyage exige VOYAGE_API_KEY.")
        if self.embedding_provider == "openai" and not self.openai_api_key:
            raise ConfigError("MAESTRO_EMBEDDING_PROVIDER=openai exige OPENAI_API_KEY.")
        if self.embedding_provider == "atlas" and self.memory_backend != "atlas":
            raise ConfigError(
                "MAESTRO_EMBEDDING_PROVIDER=atlas (auto-embedding) exige "
                "MAESTRO_MEMORY_BACKEND=atlas: o embedding e gerado pelo proprio "
                "Atlas Vector Search, nao existe no backend local."
            )
        if self.llm_provider not in _VALID_LLM:
            raise ConfigError(
                f"MAESTRO_LLM_PROVIDER invalido: {self.llm_provider!r}. "
                f"Valores aceitos: {', '.join(_VALID_LLM)}."
            )
        if self.llm_provider == "anthropic" and not self.anthropic_api_key:
            raise ConfigError("MAESTRO_LLM_PROVIDER=anthropic exige ANTHROPIC_API_KEY.")
        if self.llm_provider == "openai" and not self.openai_api_key:
            raise ConfigError("MAESTRO_LLM_PROVIDER=openai exige OPENAI_API_KEY.")

    # ------------------------------------------------------------------
    def resolved_embedding_provider(self) -> str:
        """Resolve 'auto' pela presenca de chave: voyage > openai > local."""
        if self.embedding_provider != "auto":
            return self.embedding_provider
        if self.voyage_api_key:
            return "voyage"
        if self.openai_api_key:
            return "openai"
        return "local"

    # ------------------------------------------------------------------
    def llm_provider_resolved(self) -> str:
        """Resolve 'auto' pela presenca de chave: anthropic > openai > local."""
        if self.llm_provider != "auto":
            return self.llm_provider
        if self.anthropic_api_key:
            return "anthropic"
        if self.openai_api_key:
            return "openai"
        return "local"

    # ------------------------------------------------------------------
    def __repr__(self) -> str:  # nunca vazar segredo em log/traceback
        parts = []
        for f in fields(self):
            v = getattr(self, f.name)
            if f.name in _SECRET_FIELDS and v:
                v = "***"
            parts.append(f"{f.name}={v!r}")
        return f"Settings({', '.join(parts)})"
