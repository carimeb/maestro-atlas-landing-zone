"""
Auditoria estruturada.

docs/agent-memory.md exige: "toda escrita/edicao e registrada no SIEM com
autor e timestamp". Este modulo implementa o lado do produtor: eventos JSON
por linha (JSON Lines), formato que qualquer coletor Enterprise ingere
(Splunk, Datadog, Elastic, CloudWatch).

Sinks disponiveis: stdout (default, capturado pelo coletor de logs do
container), file (caminho fixo) e null (testes). Um sink novo (ex.: HTTP
direto para o SIEM) e uma classe com .write(dict), registrada do lado de
fora; nada aqui muda.

Eventos nunca carregam o texto integral de segredos nem payloads brutos:
quem chama e responsavel por passar apenas metadados.
"""

from __future__ import annotations

import datetime as dt
import json
import sys
import threading
from typing import Any, Protocol


class AuditSink(Protocol):
    def write(self, event: dict[str, Any]) -> None: ...


class StdoutSink:
    def write(self, event: dict[str, Any]) -> None:
        sys.stdout.write(json.dumps(event, ensure_ascii=False) + "\n")


class FileSink:
    def __init__(self, path: str):
        self._path = path
        self._lock = threading.Lock()

    def write(self, event: dict[str, Any]) -> None:
        line = json.dumps(event, ensure_ascii=False) + "\n"
        with self._lock, open(self._path, "a", encoding="utf-8") as fh:
            fh.write(line)


class NullSink:
    def __init__(self):
        self.events: list[dict] = []  # retidos para assercao em teste

    def write(self, event: dict[str, Any]) -> None:
        self.events.append(event)


class AuditLog:
    """Produtor de eventos de auditoria.

    Convencao de nomes de acao: dominio.verbo
      memory.write | memory.write_denied | memory.search | memory.delete
    """

    def __init__(self, sink: AuditSink, actor: str = "maestro-agent"):
        self._sink = sink
        self._actor = actor

    def emit(self, action: str, **details: Any) -> None:
        event = {
            "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
            "actor": self._actor,
            "action": action,
            **details,
        }
        self._sink.write(event)


def build_audit(settings, actor: str = "maestro-agent") -> AuditLog:
    if settings.audit_sink == "file":
        return AuditLog(FileSink(settings.audit_file), actor)
    if settings.audit_sink == "null":
        return AuditLog(NullSink(), actor)
    return AuditLog(StdoutSink(), actor)
