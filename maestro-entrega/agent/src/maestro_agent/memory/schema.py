"""
Schema da memoria de longo prazo (colecao agent_memory).

Validacao na borda: um fato malformado e rejeitado na construcao, antes de
chegar ao banco. Os valores validos espelham docs/agent-memory.md e a tela
de memoria do demo.
"""

from __future__ import annotations

from dataclasses import dataclass, field

VALID_SCOPES = ("org", "project", "cluster")
VALID_KINDS = ("decisão", "baseline", "política", "pendência", "fato")
MAX_TEXT_LEN = 4000  # limite defensivo; fato nao e documento


@dataclass(frozen=True)
class MemoryFact:
    scope: str
    kind: str
    text: str
    source: str
    namespace: dict[str, str]
    pinned: bool = False

    def __post_init__(self):
        if self.scope not in VALID_SCOPES:
            raise ValueError(f"scope invalido: {self.scope!r}; aceitos: {VALID_SCOPES}")
        if self.kind not in VALID_KINDS:
            raise ValueError(f"kind invalido: {self.kind!r}; aceitos: {VALID_KINDS}")
        if not self.text or not self.text.strip():
            raise ValueError("text vazio")
        if len(self.text) > MAX_TEXT_LEN:
            raise ValueError(f"text excede {MAX_TEXT_LEN} caracteres")
        if not self.source:
            raise ValueError("source obrigatorio")
        missing = [k for k in ("org",) if k not in self.namespace]
        if missing:
            raise ValueError(f"namespace sem chave obrigatoria: {missing}")
        # escopo precisa existir no namespace correspondente
        if self.scope in ("project", "cluster") and "project" not in self.namespace:
            raise ValueError("scope project/cluster exige namespace.project")
        if self.scope == "cluster" and "cluster" not in self.namespace:
            raise ValueError("scope cluster exige namespace.cluster")

    def to_document(self) -> dict:
        return {
            "scope": self.scope,
            "kind": self.kind,
            "text": self.text,
            "source": self.source,
            "namespace": dict(self.namespace),
            "pinned": self.pinned,
        }
