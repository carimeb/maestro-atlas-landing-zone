"""Definicao do indice de Vector Search para a colecao agent_memory.

Criar via Atlas UI, Atlas CLI ou API de admin. numDimensions deve casar com
o provedor de embedding em uso (config central decide qual e)."""

from ..config import Settings
from ..providers.base import create_embedding_provider


def index_definition(settings: Settings) -> dict:
    name = settings.resolved_embedding_provider()
    if name == "atlas":
        # Auto-embedding: o indice aponta para o campo de TEXTO; o Atlas gera
        # e gerencia os vetores (ficam em colecao de sistema, nao no documento).
        return {
            "name": settings.vector_index_name,
            "type": "vectorSearch",
            "definition": {
                "fields": [
                    {
                        "type": "autoEmbed",
                        "modality": "text",
                        "path": "text",
                        "model": settings.auto_embed_model,
                    },
                    {"type": "filter", "path": "scope"},
                    {"type": "filter", "path": "namespace.cluster"},
                ]
            },
        }
    provider = create_embedding_provider(name, settings)
    return {
        "name": settings.vector_index_name,
        "type": "vectorSearch",
        "definition": {
            "fields": [
                {
                    "type": "vector",
                    "path": "embedding",
                    "numDimensions": provider.dimensions,
                    "similarity": "cosine",
                },
                {"type": "filter", "path": "scope"},
                {"type": "filter", "path": "namespace.cluster"},
            ]
        },
    }
