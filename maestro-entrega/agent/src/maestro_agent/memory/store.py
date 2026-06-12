"""
Store de memoria de longo prazo.

Evolucao do passo 1 com as garantias das fundacoes aplicadas em TODO
caminho de escrita e leitura, independentemente do backend:

  - validacao de schema (MemoryFact) na borda;
  - politica "nunca segredos": redaction.ensure_clean antes de gravar;
  - auditoria: memory.write, memory.write_denied e memory.search emitidos
    com metadados (nunca o conteudo de segredos).

Backends sob a mesma interface:
  - LocalMemoryStore: vetores em processo + cosseno; desenvolvimento.
  - AtlasMemoryStore: pymongo + $vectorSearch; producao.
"""

from __future__ import annotations

from typing import Protocol

from ..config import Settings
from ..providers.base import EmbeddingProvider, create_embedding_provider
from ..security.audit import AuditLog, build_audit
from ..security.redaction import SecretDetected, ensure_clean
from .schema import MemoryFact


class MemoryStore(Protocol):
    def ingest(self, facts: list[MemoryFact]) -> int: ...
    def search(self, query: str, k: int = 3, scope: str | None = None) -> list[dict]: ...


# ===========================================================================
class _BaseStore:
    """Logica comum: embeddings, redaction e auditoria. Subclasses so
    implementam persistencia (_persist) e busca vetorial (_vector_search)."""

    def __init__(self, settings: Settings, embedder: EmbeddingProvider, audit: AuditLog):
        self._settings = settings
        self._embedder = embedder
        self._audit = audit

    # -- escrita --------------------------------------------------------
    def ingest(self, facts: list[MemoryFact]) -> int:
        clean: list[MemoryFact] = []
        for fact in facts:
            try:
                ensure_clean(fact.text)
                clean.append(fact)
            except SecretDetected as exc:
                self._audit.emit(
                    "memory.write_denied",
                    reason="secret_detected",
                    rules=[f.rule for f in exc.findings],
                    scope=fact.scope,
                    source=fact.source,
                )
                raise

        vectors = self._embedder.embed_documents([f.text for f in clean])
        n = self._persist(clean, vectors)
        for fact in clean:
            self._audit.emit(
                "memory.write",
                scope=fact.scope,
                kind=fact.kind,
                source=fact.source,
                pinned=fact.pinned,
                namespace=fact.namespace,
                embedder=self._embedder.name,
            )
        return n

    # -- leitura --------------------------------------------------------
    def search(self, query: str, k: int = 3, scope: str | None = None) -> list[dict]:
        qvec = self._embedder.embed_query(query)
        results = self._vector_search(qvec, k=k, scope=scope)
        self._audit.emit("memory.search", k=k, scope=scope, hits=len(results))
        return results

    # -- a implementar por backend ---------------------------------------
    def _persist(self, facts: list[MemoryFact], vectors: list[list[float]]) -> int:
        raise NotImplementedError

    def _vector_search(self, qvec: list[float], k: int, scope: str | None) -> list[dict]:
        raise NotImplementedError


# ===========================================================================
class LocalMemoryStore(_BaseStore):
    """Backend de desenvolvimento: tudo em processo, zero dependencia."""

    def __init__(self, settings, embedder, audit):
        super().__init__(settings, embedder, audit)
        self._docs: list[dict] = []

    def _persist(self, facts, vectors) -> int:
        for fact, vec in zip(facts, vectors):
            doc = fact.to_document()
            doc["embedding"] = vec
            self._docs.append(doc)
        return len(facts)

    def _vector_search(self, qvec, k, scope):
        scored = []
        for doc in self._docs:
            if scope and doc["scope"] != scope:
                continue
            scored.append((_cosine(qvec, doc["embedding"]), doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        out = []
        for score, doc in scored[:k]:
            hit = {key: doc[key] for key in ("scope", "kind", "text", "source", "pinned")}
            hit["score"] = round(score, 4)
            out.append(hit)
        return out


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


# ===========================================================================
class AtlasMemoryStore(_BaseStore):
    """Backend de producao: Atlas Vector Search via $vectorSearch."""

    def __init__(self, settings, embedder, audit):
        super().__init__(settings, embedder, audit)
        from pymongo import MongoClient  # extra: maestro-agent[atlas]
        client = MongoClient(settings.mongodb_uri)
        self._col = client[settings.mongodb_db][settings.memory_collection]

    def _persist(self, facts, vectors) -> int:
        import datetime as dt
        now = dt.datetime.now(dt.timezone.utc)
        docs = []
        for fact, vec in zip(facts, vectors):
            doc = fact.to_document()
            doc.update(embedding=vec, created_at=now, updated_at=now)
            docs.append(doc)
        self._col.insert_many(docs)
        return len(docs)

    def _vector_search(self, qvec, k, scope):
        stage = {
            "$vectorSearch": {
                "index": self._settings.vector_index_name,
                "path": "embedding",
                "queryVector": qvec,
                "numCandidates": max(100, k * 20),
                "limit": k,
            }
        }
        if scope:
            stage["$vectorSearch"]["filter"] = {"scope": scope}
        pipeline = [
            stage,
            {"$project": {
                "_id": 0,
                "scope": 1, "kind": 1, "text": 1, "source": 1, "pinned": 1,
                "score": {"$meta": "vectorSearchScore"},
            }},
        ]
        return list(self._col.aggregate(pipeline))


# ===========================================================================
def build_memory_store(settings: Settings | None = None) -> MemoryStore:
    """Fabrica unica: resolve config, provedor, auditoria e backend."""
    settings = settings or Settings.from_env()
    embedder = create_embedding_provider(settings.resolved_embedding_provider(), settings)
    audit = build_audit(settings)
    cls = AtlasMemoryStore if settings.memory_backend == "atlas" else LocalMemoryStore
    return cls(settings, embedder, audit)
