"""
Passo 1 (vector search puro) sobre as fundacoes.

Mesma demonstracao da pasta step1_vector_search, agora consumindo o pacote:
config central, provedor resolvido por registro, redaction e auditoria
ativas em todo o caminho. Inclui uma tentativa proposital de gravar um
segredo, para mostrar a politica em acao.

Execucao offline:        python examples/step1_vector_search.py
Execucao real (Atlas):   exporte VOYAGE_API_KEY (ou OPENAI_API_KEY),
                         MAESTRO_MEMORY_BACKEND=atlas e MONGODB_URI.
"""

from maestro_agent.config import Settings
from maestro_agent.memory import MemoryFact, build_memory_store
from maestro_agent.security.redaction import SecretDetected

NAMESPACE = {"org": "contoso-atlas-prod", "project": "payments", "cluster": "fraud-ml-prod"}

FACTS = [
    MemoryFact("cluster", "decisão",
               "Índice { user_id: 1 } criado em 03/06 resolveu COLLSCAN na coleção transactions (p95 -65%).",
               "atlas-incident-triage", NAMESPACE, pinned=True),
    MemoryFact("cluster", "baseline",
               "Baseline de CPU em horário comercial: 55-65%. Picos acima de 85% por mais de 5min são anômalos.",
               "observação contínua", NAMESPACE),
    MemoryFact("project", "política",
               "Janela de manutenção aprovada pelo time de Payments: domingos 02:00-04:00 (BRT).",
               "dev (manual)", NAMESPACE, pinned=True),
    MemoryFact("cluster", "pendência",
               "A coleção message_history cresce sem limite (~1.240 itens/doc) — refatoração de schema pendente (ticket JIRA PAY-812).",
               "schema-anti-pattern-review", NAMESPACE),
    MemoryFact("org", "política",
               "Política de FinOps: clusters com CPU média menor que 15% por 30 dias são candidatos a downgrade automático (com aprovação).",
               "dev (manual)", NAMESPACE),
    MemoryFact("cluster", "fato",
               "Restore de PITR testado com sucesso em 15/05 — RTO medido: 18 min.",
               "atlas-ops", NAMESPACE),
]

QUESTIONS = [
    "como costuma estar o uso de CPU desse cluster em horário normal?",
    "tem algum problema de schema pendente pra resolver?",
    "quando posso fazer manutenção sem incomodar o time?",
    "esse índice em user_id já ajudou em alguma situação parecida antes?",
]


def main():
    settings = Settings.from_env()
    print(f"# settings: {settings}\n")

    store = build_memory_store(settings)
    n = store.ingest(FACTS)
    print(f"\n# {n} fatos ingeridos\n")

    for q in QUESTIONS:
        print(f"PERGUNTA: {q}")
        for i, h in enumerate(store.search(q, k=2), 1):
            print(f"  {i}. [{h['score']}] ({h['kind']}) {h['text']}")
        print()

    # Politica "nunca segredos" em acao: escrita negada + evento de auditoria.
    print("# tentativa de gravar segredo (deve ser negada):")
    try:
        store.ingest([MemoryFact(
            "cluster", "fato",
            "Anotar acesso: mongodb+srv://<user>:<passkey>@cluster0.mongodb.net",
            "dev (manual)", NAMESPACE,
        )])
    except SecretDetected as exc:
        print(f"  negado como esperado -> {exc}")


if __name__ == "__main__":
    main()
