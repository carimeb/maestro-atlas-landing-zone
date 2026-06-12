from .base import (
    EmbeddingProvider,
    register_embedding,
    available_embeddings,
    create_embedding_provider,
)
from . import embeddings  # noqa: F401  (registra os provedores embutidos)

__all__ = [
    "EmbeddingProvider",
    "register_embedding",
    "available_embeddings",
    "create_embedding_provider",
]
