"""
Deteccao de segredos.

A politica de docs/agent-memory.md ("nunca segredos" na memoria do agente)
vira verificacao obrigatoria: todo texto candidato a fato passa por scan()
antes da escrita. Encontrou padrao de segredo, a escrita e negada e o evento
vai para a auditoria.

Cobertura por padrao, nao por exaustao: connection strings com credencial,
chaves de API dos provedores usados no projeto, credenciais AWS, blocos PEM
e atribuicoes explicitas de senha. Falsos negativos sao possiveis; a camada
existe para impedir o acidente comum, nao para substituir DLP corporativo.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("connection_string_com_credencial",
     re.compile(r"mongodb(\+srv)?://[^/\s:@]+:[^@\s]+@", re.I)),
    ("api_key_anthropic_openai",
     re.compile(r"\bsk-[A-Za-z0-9_\-]{16,}\b")),
    ("api_key_voyage",
     re.compile(r"\bpa-[A-Za-z0-9_\-]{16,}\b")),
    ("aws_access_key_id",
     re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("chave_privada_pem",
     re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("bearer_token",
     re.compile(r"\bBearer\s+[A-Za-z0-9_\-.~+/]{20,}", re.I)),
    ("atribuicao_de_senha",
     re.compile(r"\b(password|passwd|pwd|senha)\s*[:=]\s*\S+", re.I)),
]


@dataclass(frozen=True)
class Finding:
    rule: str          # qual padrao disparou
    excerpt: str       # trecho MASCARADO, seguro para log


class SecretDetected(ValueError):
    """Texto contem padrao de segredo; escrita na memoria negada."""

    def __init__(self, findings: list[Finding]):
        self.findings = findings
        rules = ", ".join(f.rule for f in findings)
        super().__init__(f"Padrao de segredo detectado ({rules}); escrita negada.")


def scan(text: str) -> list[Finding]:
    """Retorna os achados (lista vazia = texto limpo)."""
    findings = []
    for rule, pattern in _PATTERNS:
        m = pattern.search(text)
        if m:
            findings.append(Finding(rule=rule, excerpt=_mask(m.group(0))))
    return findings


def ensure_clean(text: str) -> None:
    """Lanca SecretDetected se o texto contiver padrao de segredo."""
    findings = scan(text)
    if findings:
        raise SecretDetected(findings)


def _mask(s: str) -> str:
    """Mantem so o inicio para diagnostico; o resto vira asteriscos."""
    keep = min(8, max(2, len(s) // 4))
    return s[:keep] + "***"
