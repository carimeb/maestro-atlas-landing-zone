"""
Implementacoes de embedding sob o contrato EmbeddingProvider.

Migradas do passo 1 (step1_vector_search/embeddings.py) para o padrao de
registro. Mesmos tres caminhos: Voyage (recomendado para Atlas), OpenAI e
fallback local deterministico para validacao offline.
"""

from __future__ import annotations

import hashlib
import math

from .base import register_embedding


@register_embedding("voyage")
class VoyageEmbedding:
    dimensions = 1024  # voyage-3

    def __init__(self, settings):
        import voyageai  # extra: maestro-agent[voyage]
        self._client = voyageai.Client(api_key=settings.voyage_api_key)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._client.embed(texts, model="voyage-3", input_type="document").embeddings

    def embed_query(self, text: str) -> list[float]:
        return self._client.embed([text], model="voyage-3", input_type="query").embeddings[0]


@register_embedding("openai")
class OpenAIEmbedding:
    dimensions = 1536  # text-embedding-3-small

    def __init__(self, settings):
        from openai import OpenAI  # extra: maestro-agent[openai]
        self._client = OpenAI(api_key=settings.openai_api_key)

    def _embed(self, texts: list[str]) -> list[list[float]]:
        resp = self._client.embeddings.create(model="text-embedding-3-small", input=texts)
        return [d.embedding for d in resp.data]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embed(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._embed([text])[0]


@register_embedding("local")
class LocalHashEmbedding:
    """Hashing vectorizer deterministico, sem rede e sem dependencia.

    Valida o pipeline de ponta a ponta, mas nao captura sinonimos: o ranking
    semantico real exige Voyage ou OpenAI. Uso restrito a desenvolvimento."""

    dimensions = 256

    def __init__(self, settings=None):
        pass

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vector(text)

    # -- internos -----------------------------------------------------
    def _vector(self, text: str) -> list[float]:
        vec = [0.0] * self.dimensions
        for tok in self._tokens(text):
            h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
            vec[h % self.dimensions] += 1.0 if (h >> 8) % 2 == 0 else -1.0
        norm = math.sqrt(sum(v * v for v in vec))
        return [v / norm for v in vec] if norm else vec

    @staticmethod
    def _tokens(text: str) -> list[str]:
        out, cur = [], []
        for ch in text.lower():
            if ch.isalnum():
                cur.append(ch)
            elif cur:
                out.append("".join(cur)); cur = []
        if cur:
            out.append("".join(cur))
        return out
