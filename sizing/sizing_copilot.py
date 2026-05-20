#!/usr/bin/env python3
"""
Maestro Sizing Copilot
======================
Recomenda o tier do MongoDB Atlas e estima o custo mensal a partir de uma
descrição de workload em linguagem natural.

Padrão importante: os NÚMEROS (tier e custo) são calculados de forma
determinística em Python — a IA NÃO inventa preços. Quando há
ANTHROPIC_API_KEY, o Claude apenas redige a recomendação em linguagem
natural usando os fatos já calculados (grounding).

Uso:
    export ANTHROPIC_API_KEY=sk-ant-...        # opcional
    python sizing_copilot.py "app de pedidos, 400GB, working set 50GB, 3000 ops/s, 5000 conexões, prod em São Paulo"
"""
import os
import re
import sys
import json

# --------------------------------------------------------------------------
# Tabela de tiers e preços (estimativas ~ on-demand AWS, USD/h, replica-set 3 nós)
# Mantida em sincronia com o protótipo Maestro (demo/maestro.html).
# --------------------------------------------------------------------------
TIERS = [
    {"name": "M10",  "ram": 2,   "vcpu": 2,  "storage": 10,   "hourly": 0.08,  "conns": 1500},
    {"name": "M20",  "ram": 4,   "vcpu": 2,  "storage": 20,   "hourly": 0.20,  "conns": 3000},
    {"name": "M30",  "ram": 8,   "vcpu": 2,  "storage": 40,   "hourly": 0.54,  "conns": 3000},
    {"name": "M40",  "ram": 16,  "vcpu": 4,  "storage": 80,   "hourly": 1.04,  "conns": 6000},
    {"name": "M50",  "ram": 32,  "vcpu": 8,  "storage": 160,  "hourly": 2.00,  "conns": 16000},
    {"name": "M60",  "ram": 64,  "vcpu": 16, "storage": 320,  "hourly": 3.95,  "conns": 32000},
    {"name": "M80",  "ram": 128, "vcpu": 32, "storage": 750,  "hourly": 7.42,  "conns": 96000},
    {"name": "M140", "ram": 192, "vcpu": 48, "storage": 1000, "hourly": 9.40,  "conns": 96000},
    {"name": "M200", "ram": 256, "vcpu": 64, "storage": 1500, "hourly": 14.59, "conns": 128000},
    {"name": "M300", "ram": 384, "vcpu": 96, "storage": 2000, "hourly": 24.50, "conns": 128000},
]
REGIONS = {
    "sa-east-1": {"label": "São Paulo (sa-east-1)", "mult": 1.46},
    "us-east-1": {"label": "N. Virginia (us-east-1)", "mult": 1.0},
    "eu-west-1": {"label": "Irlanda (eu-west-1)", "mult": 1.08},
    "eu-central-1": {"label": "Frankfurt (eu-central-1)", "mult": 1.12},
}
PRICING = {"storage_per_gb": 0.25, "backup_per_gb": 0.20, "network_pct": 0.10, "usd_brl": 5.05}


def parse_workload(text: str) -> dict:
    t = text.lower()

    def num(pattern):
        m = re.search(pattern, t)
        if not m:
            return 0.0
        val = float(m.group(1).replace(",", "."))
        if re.search(r"tb|tera", m.group(0)):
            val *= 1024
        return val

    data_gb = num(r"(\d+[.,]?\d*)\s*(tb|gb|tera)")
    working_set = num(r"working\s*set\s*(?:de)?\s*(\d+[.,]?\d*)\s*(gb|tb)")
    ops = num(r"(\d+[.,]?\d*)\s*(?:k)?\s*ops")
    conns = num(r"(\d+[.,]?\d*)\s*(?:k)?\s*(?:conex|connection)")

    env = "prod"
    if re.search(r"\bdev\b", t):
        env = "dev"
    elif re.search(r"stage|homolog", t):
        env = "stage"
    elif re.search(r"\btest\b", t):
        env = "test"

    region = "sa-east-1"
    if re.search(r"virginia|us-east", t):
        region = "us-east-1"
    elif re.search(r"irlanda|eu-west", t):
        region = "eu-west-1"
    elif re.search(r"frankfurt", t):
        region = "eu-central-1"

    genai = bool(re.search(r"vector|rag|genai|embedding|llm|ia gen", t))
    return {"data_gb": data_gb, "working_set": working_set, "ops": ops,
            "conns": conns, "env": env, "region": region, "genai": genai}


def recommend_tier(w: dict) -> dict:
    data_gb = w["data_gb"]
    working_set = w["working_set"] or max(1.0, data_gb * 0.10)
    for tier in TIERS:
        if (tier["ram"] >= working_set and tier["storage"] >= data_gb * 1.25
                and tier["conns"] >= w["conns"] and tier["vcpu"] * 8000 >= w["ops"]):
            return {"tier": tier, "working_set": working_set}
    return {"tier": TIERS[-1], "working_set": working_set}


def estimate_cost(tier_name: str, region: str, storage_gb: float) -> dict:
    tier = next(t for t in TIERS if t["name"] == tier_name)
    reg = REGIONS.get(region, REGIONS["us-east-1"])
    storage_gb = max(storage_gb, tier["storage"])
    compute = tier["hourly"] * 730 * reg["mult"]
    extra = max(0, storage_gb - tier["storage"])
    storage = extra * PRICING["storage_per_gb"]
    backup = storage_gb * PRICING["backup_per_gb"]
    sub = compute + storage + backup
    network = sub * PRICING["network_pct"]
    total = sub + network
    return {"compute": compute, "storage": storage, "backup": backup,
            "network": network, "total": total, "total_brl": total * PRICING["usd_brl"],
            "storage_gb": storage_gb}


def build_facts(text: str) -> dict:
    w = parse_workload(text)
    rec = recommend_tier(w)
    cost = estimate_cost(rec["tier"]["name"], w["region"], w["data_gb"] * 1.25)
    return {"workload": w, "recommended_tier": rec["tier"]["name"],
            "tier_specs": rec["tier"], "working_set_gb": round(rec["working_set"]),
            "vector_search": w["genai"], "region": REGIONS[w["region"]]["label"],
            "cost": cost}


def print_local(facts: dict):
    t = facts["tier_specs"]
    c = facts["cost"]
    print(f"\n  Tier recomendado: {facts['recommended_tier']}"
          + ("  (+ Vector Search / Search Nodes)" if facts["vector_search"] else ""))
    print(f"  Specs: {t['ram']}GB RAM · {t['vcpu']} vCPU · até {t['conns']:,} conexões")
    print(f"  Working set estimado: {facts['working_set_gb']} GB  |  Região: {facts['region']}\n")
    print("  Estimativa de custo mensal:")
    print(f"    Compute ............ ${c['compute']:,.2f}")
    print(f"    Storage ({c['storage_gb']:.0f}GB) ... ${c['storage']:,.2f}")
    print(f"    Backup ............. ${c['backup']:,.2f}")
    print(f"    Rede (+10%) ........ ${c['network']:,.2f}")
    print(f"    {'-'*34}")
    print(f"    TOTAL .............. ${c['total']:,.2f}/mês  ·  R$ {c['total_brl']:,.0f}/mês\n")


def with_claude(text: str, facts: dict):
    """Usa o Claude para redigir a recomendação a partir dos fatos calculados."""
    try:
        import anthropic
    except ImportError:
        print("(SDK 'anthropic' não instalado — rode: pip install -r requirements.txt)\n")
        return print_local(facts)

    client = anthropic.Anthropic()
    system = (
        "Você é o Maestro Copilot, especialista em sizing de MongoDB Atlas. "
        "Os números de tier e custo JÁ FORAM CALCULADOS e são autoritativos — "
        "NÃO recalcule nem invente preços. Apenas explique a recomendação de forma "
        "clara e objetiva para um arquiteto, em português, justificando o tier com "
        "base em working set, storage, conexões e throughput. Seja conciso."
    )
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=700,
        system=system,
        messages=[{"role": "user", "content":
                   f"Workload do cliente:\n{text}\n\n"
                   f"Fatos calculados (use exatamente estes números):\n"
                   f"{json.dumps(facts, ensure_ascii=False, indent=2)}"}],
    )
    print("\n" + msg.content[0].text + "\n")


# --------------------------------------------------------------------------
# Análise de documento JSON: estima volume/working set e detecta anti-patterns
# de modelagem MongoDB. Espelha o analisador do protótipo (Maestro Copilot).
# --------------------------------------------------------------------------
import base64
import binascii


def _looks_base64(s: str) -> bool:
    s = "".join(s.split())
    if len(s) < 300:
        return False
    try:
        base64.b64decode(s, validate=True)
        return True
    except (binascii.Error, ValueError):
        return False


def analyze_schema(obj) -> dict:
    issues = []
    state = {"depth": 0, "fields": 0, "max_array": 0}

    def walk(v, depth, path):
        state["depth"] = max(state["depth"], depth)
        if isinstance(v, list):
            state["max_array"] = max(state["max_array"], len(v))
            if len(v) > 100:
                issues.append(("high", "Array potencialmente unbounded",
                    f'O campo "{path}" tem {len(v)} elementos. Arrays sem limite incham o '
                    f'documento (limite 16MB) e degradam updates/índices. Use referências ou bucketing.'))
            for e in v[:40]:
                walk(e, depth + 1, path + "[]")
        elif isinstance(v, dict):
            keys = list(v.keys())
            state["fields"] += len(keys)
            if len(keys) > 60:
                issues.append(("medium", "Documento com muitos campos",
                    f'"{path or "root"}" tem {len(keys)} campos — aumenta working set e I/O.'))
            for k in keys:
                if k.startswith("$") or "." in k:
                    issues.append(("high", "Nome de campo inválido/arriscado",
                        f'Campo "{k}" usa "$" ou ".", o que quebra queries e drivers. Renomeie.'))
                walk(v[k], depth + 1, f"{path}.{k}" if path else k)
        elif isinstance(v, str):
            if _looks_base64(v):
                issues.append(("medium", "Blob/base64 dentro do documento",
                    f'"{path}" parece binário/base64 (~{len(v)//1024} KB). Use object storage e guarde só a referência.'))
            elif len(v) > 50000:
                issues.append(("low", "String muito longa",
                    f'"{path}" tem ~{len(v)//1024} KB; avalie mover para fora do documento.'))

    walk(obj, 1, "")
    size_bytes = len(json.dumps(obj).encode("utf-8"))
    if state["depth"] > 6:
        issues.append(("medium", "Aninhamento profundo",
            f'Profundidade de {state["depth"]} níveis dificulta indexar e atualizar campos internos.'))
    if size_bytes > 1_000_000:
        issues.append(("high", "Documento muito grande",
            f"~{size_bytes/1e6:.2f} MB — caminhando para o limite de 16MB; reveja embedding vs referência."))
    return {"size_bytes": size_bytes, "depth": state["depth"],
            "fields": state["fields"], "max_array": state["max_array"], "issues": issues}


def analyze_json_file(path: str, doc_count: int, region: str = "sa-east-1"):
    with open(path, encoding="utf-8") as f:
        obj = json.load(f)
    a = analyze_schema(obj)
    avg = a["size_bytes"] / len(obj) if isinstance(obj, list) and obj else a["size_bytes"]
    data_gb = avg * doc_count / 1e9
    working_set = max(0.5, data_gb * 0.10)
    rec = recommend_tier({"data_gb": data_gb, "working_set": working_set, "ops": 0, "conns": 0})
    cost = estimate_cost(rec["tier"]["name"], region, data_gb * 1.25)

    print(f"\n  Documento de amostra: {path}")
    print(f"  Tamanho médio: {avg/1024:.1f} KB  ·  profundidade: {a['depth']}  ·  maior array: {a['max_array']}")
    print(f"  Volume projetado ({doc_count:,} docs): {data_gb:.1f} GB")
    print(f"  Working set estimado: {working_set:.1f} GB  ->  Tier {rec['tier']['name']} ({rec['tier']['ram']}GB RAM)")
    print(f"  Custo estimado: ${cost['total']:,.2f}/mês  ·  R$ {cost['total_brl']:,.0f}/mês\n")
    print("  Anti-patterns de modelagem:")
    if not a["issues"]:
        print("    ✓ Nenhum anti-pattern crítico detectado.\n")
    else:
        for lvl, title, detail in a["issues"]:
            print(f"    [{lvl.upper()}] {title}\n        {detail}")
        print()
    return a


def main():
    args = sys.argv[1:]
    if not args:
        print('Uso:')
        print('  python sizing_copilot.py "descrição do workload"')
        print('  python sizing_copilot.py --json amostra.json [--docs 10000000] [--region sa-east-1]')
        sys.exit(1)

    if args[0] == "--json":
        if len(args) < 2:
            print("Informe o caminho do JSON: --json amostra.json")
            sys.exit(1)
        path = args[1]
        docs = 1_000_000
        region = "sa-east-1"
        if "--docs" in args:
            docs = int(args[args.index("--docs") + 1])
        if "--region" in args:
            region = args[args.index("--region") + 1]
        analyze_json_file(path, docs, region)
        return

    text = " ".join(args)
    facts = build_facts(text)
    if os.environ.get("ANTHROPIC_API_KEY"):
        with_claude(text, facts)
    else:
        print("\n[Modo local — defina ANTHROPIC_API_KEY para resposta redigida pelo Claude]")
        print_local(facts)


if __name__ == "__main__":
    main()
