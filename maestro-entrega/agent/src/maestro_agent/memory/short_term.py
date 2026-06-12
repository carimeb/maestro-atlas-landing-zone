"""
Memoria de curto prazo (passo 2 da ordem de aprendizado).

Conceito. A memoria LONGA (store.py) guarda fatos que valem entre sessoes.
A memoria CURTA guarda o estado da sessao em andamento: em que passo da
triagem o agente esta, o que ja descobriu, o que falta. No LangGraph isso e
papel do CHECKPOINTER: a cada passo do grafo, o estado inteiro e salvo como
um checkpoint associado a um thread_id. Se o processo cair, outro processo
com o mesmo thread_id retoma exatamente de onde parou.

O checkpointer tambem habilita o gate de aprovacao humana: o grafo pode ser
compilado para INTERROMPER antes de um no sensivel (ex.: aplicar mudanca em
producao). O estado fica persistido aguardando; a aprovacao retoma a
execucao. E a regra do Maestro ("acoes em producao exigem aprovacao
humana") implementada pelo mesmo mecanismo da persistencia.

Backends, mesmo padrao da memoria longa:
  - local: MemorySaver, em processo. Valida a mecanica; nao sobrevive a
    restart (essa e a limitacao didatica que o backend atlas resolve).
  - atlas: MongoDBSaver (langgraph-checkpoint-mongodb), um documento de
    checkpoint por passo da thread, no mesmo Atlas da memoria longa.
"""

from __future__ import annotations

from ..config import Settings


def build_checkpointer(settings: Settings):
    """Devolve o checkpointer conforme o backend configurado.

    Retorno tipado como Any de proposito: o LangGraph so exige a interface
    BaseCheckpointSaver, e nao queremos import obrigatorio de langgraph no
    nucleo do pacote (segue o principio de extras opcionais)."""
    if settings.memory_backend == "atlas":
        from langgraph.checkpoint.mongodb import MongoDBSaver  # extra: [graph,atlas]
        from pymongo import MongoClient

        client = MongoClient(settings.mongodb_uri)
        return MongoDBSaver(
            client,
            db_name=settings.mongodb_db,
            checkpoint_collection_name=settings.checkpoint_collection,
            writes_collection_name=settings.checkpoint_collection + "_writes",
        )

    from langgraph.checkpoint.memory import MemorySaver  # extra: [graph]
    return MemorySaver()


def session_config(thread_id: str) -> dict:
    """Config de execucao do LangGraph para uma sessao (thread).

    O thread_id e a chave da memoria curta: mesma thread, mesmo estado.
    Convencao do Maestro: '<skill>-<identificador>', ex. 'triage-PAY-1042'."""
    return {"configurable": {"thread_id": thread_id}}
