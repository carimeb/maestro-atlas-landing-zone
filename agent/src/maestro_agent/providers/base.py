"""
Contrato de provedores plugaveis.

Padrao do Maestro elevado a regra de arquitetura: qualquer servico externo
(embedding, LLM, futuramente observabilidade ou identidade) entra por uma
interface estavel + um registro nomeado.

Para adicionar um provedor novo NAO se edita codigo existente:

    @register_embedding("meu-provedor")
    class MeuProvedor:
        name = "meu-provedor"
        dimensions = 768
        def embed_documents(self, texts): ...
        def embed_query(self, text): ...

O registro resolve o resto. Open/closed na pratica.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Texto -> vetor. A distincao document/query importa: modelos como o
    voyage-3 otimizam o embedding conforme o lado da busca."""

    name: str
    dimensions: int

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    def embed_query(self, text: str) -> list[float]: ...


# ---------------------------------------------------------------------------
# Registro
# ---------------------------------------------------------------------------
_EMBEDDINGS: dict[str, type] = {}


def register_embedding(name: str):
    def deco(cls):
        cls.name = name
        _EMBEDDINGS[name] = cls
        return cls
    return deco


def available_embeddings() -> list[str]:
    return sorted(_EMBEDDINGS)


def create_embedding_provider(name: str, settings) -> EmbeddingProvider:
    try:
        cls = _EMBEDDINGS[name]
    except KeyError:
        raise KeyError(
            f"Provedor de embedding desconhecido: {name!r}. "
            f"Registrados: {', '.join(available_embeddings())}."
        ) from None
    return cls(settings)


@runtime_checkable
class LLMProvider(Protocol):
    """Raciocinio: system + prompt -> texto. Espelha o Providers.llm do
    demo (provider: claude | openai), agora como contrato de pacote."""

    name: str

    def complete(self, system: str, prompt: str) -> str: ...


_LLMS: dict[str, type] = {}


def register_llm(name: str):
    def deco(cls):
        cls.name = name
        _LLMS[name] = cls
        return cls
    return deco


def available_llms() -> list[str]:
    return sorted(_LLMS)


def create_llm_provider(name: str, settings) -> LLMProvider:
    try:
        cls = _LLMS[name]
    except KeyError:
        raise KeyError(
            f"Provedor de LLM desconhecido: {name!r}. "
            f"Registrados: {', '.join(available_llms())}."
        ) from None
    return cls(settings)
