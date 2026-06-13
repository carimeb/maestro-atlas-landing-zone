"""
Passo 3: o agente completo, juntando as duas memorias.

O roteiro demonstra o ciclo de aprendizado:

  1. A memoria longa e semeada com os fatos operacionais (passo 1).
  2. INCIDENTE 1 chega. O agente recupera fatos relevantes (recall),
     raciocina sobre eles (reason), para no gate de aprovacao (passo 2),
     e apos a aprovacao grava o resultado na memoria longa (learn).
  3. INCIDENTE 2, parecido, chega em OUTRA sessao. O recall agora encontra
     tambem o que o agente aprendeu no incidente 1. O agente melhorou.

Execucao offline:  python examples/step3_agent.py
                   (LLM stub local + embeddings locais; sem chave)
Execucao real:     exporte ANTHROPIC_API_KEY (raciocinio via Claude) e
                   VOYAGE_API_KEY (embeddings); para persistencia real,
                   MAESTRO_MEMORY_BACKEND=atlas + MONGODB_URI.
"""

from maestro_agent.agent import build_triage_agent
from maestro_agent.config import Settings
from maestro_agent.memory import MemoryFact

NAMESPACE = {"org": "contoso-atlas-prod", "project": "payments", "cluster": "fraud-ml-prod"}

SEED_FACTS = [
    MemoryFact("cluster", "decisão",
               "Índice { user_id: 1 } criado em 03/06 resolveu COLLSCAN na coleção transactions (p95 -65%).",
               "atlas-incident-triage", NAMESPACE, pinned=True),
    MemoryFact("cluster", "baseline",
               "Baseline de CPU em horário comercial: 55-65%. Picos acima de 85% por mais de 5min são anômalos.",
               "observação contínua", NAMESPACE),
    MemoryFact("project", "política",
               "Janela de manutenção aprovada pelo time de Payments: domingos 02:00-04:00 (BRT).",
               "dev (manual)", NAMESPACE, pinned=True),
]


def run_incident(agent, thread_id: str, incident: str):
    print(f"\n{'=' * 70}\nINCIDENTE ({thread_id}): {incident}\n{'=' * 70}")
    cfg = agent.config(thread_id)
    agent.graph.invoke({"incident": incident, "recalled": [], "analysis": "", "log": []}, cfg)

    state = agent.graph.get_state(cfg)
    for line in state.values["log"]:
        print(f"  {line}")
    print(f"\n  >> agente parado no gate de aprovação (próximo nó: {state.next})")
    print("  >> aprovação humana concedida; retomando...\n")

    final = agent.graph.invoke(None, cfg)
    for line in final["log"][len(state.values["log"]):]:
        print(f"  {line}")


def main():
    settings = Settings.from_env()
    print(f"# LLM: {settings.llm_provider_resolved()} | "
          f"embeddings: {settings.resolved_embedding_provider()} | "
          f"memória: {settings.memory_backend}")

    agent = build_triage_agent(settings, namespace=NAMESPACE)
    agent.store.ingest(SEED_FACTS)
    print(f"# memória longa semeada com {len(SEED_FACTS)} fatos")

    run_incident(agent, "triage-PAY-2001",
                 "CPU em 91% e queries lentas na coleção transactions do fraud-ml-prod")

    run_incident(agent, "triage-PAY-2002",
                 "latência alta de novo em queries da coleção transactions")

    print("\n# repare no recall do segundo incidente: a triagem do primeiro")
    print("# aparece como fato recuperado. O agente aprendeu entre sessões.")


if __name__ == "__main__":
    main()
