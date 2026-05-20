# Sizing Copilot

Recomenda o tier do Atlas e estima o custo mensal a partir de uma descrição de workload em linguagem natural.

**Princípio:** os números (tier e custo) são calculados de forma determinística em Python — o Claude **não inventa preços**, apenas redige a recomendação usando os fatos calculados.

## Uso

```bash
pip install -r requirements.txt

# Modo local (sem IA) — sempre funciona:
python sizing_copilot.py "app de pedidos, 400GB, working set 50GB, 3000 ops/s, 5000 conexões, prod em São Paulo"

# Com Claude redigindo a recomendação:
export ANTHROPIC_API_KEY=sk-ant-...
python sizing_copilot.py "data lake analítico 2TB, working set 200GB, 1500 ops/s, stage"

# A partir de um documento JSON (estima volume + detecta anti-patterns):
python sizing_copilot.py --json sample-order.json --docs 10000000 --region sa-east-1
```

## Análise de documento JSON

O dev sobe um documento representativo e o copilot:

- estima o **tamanho médio** do documento e projeta o **volume de dados** pelo nº de documentos;
- recomenda o **tier** e estima o **custo**;
- detecta **anti-patterns de modelagem**: arrays unbounded, documento grande (limite 16MB), aninhamento profundo, blob/base64 embutido e nomes de campo inválidos (`$`, `.`).

O arquivo `sample-order.json` é um exemplo proposital com vários anti-patterns para testar.

## Heurísticas de sizing

- Working set (dado quente) deve caber em RAM.
- Storage = volume de dados × 1,25 (folga de crescimento).
- Conexões e throughput (ops/s) limitam o tier mínimo.
- Custo = compute + storage + backup + **10% de tráfego de rede**.

A mesma lógica roda no protótipo `demo/maestro.html` (Maestro Copilot).
