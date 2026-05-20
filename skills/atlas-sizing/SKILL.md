---
name: atlas-sizing
description: Recomenda o tier do MongoDB Atlas e estima o custo mensal a partir de uma descrição de workload (volume de dados, working set, ops/s, conexões) ou de um documento JSON de amostra. Use quando o usuário pedir dimensionamento, escolha de tier, ou estimativa de custo de cluster Atlas.
---

# Atlas Sizing

Você ajuda a dimensionar clusters do MongoDB Atlas e a estimar o custo mensal.

## Quando usar
- O usuário descreve um workload e pergunta qual tier usar.
- O usuário quer uma estimativa de custo mensal.
- O usuário fornece um documento JSON de amostra para projetar volume.

## Procedimento
1. Reúna: volume de dados (GB/TB), working set (dado quente), throughput (ops/s) e pico de conexões. Se faltar, pergunte de forma objetiva. Para working set, use ~10% do volume se o usuário não souber.
2. Rode o script determinístico (os números são autoritativos — **não invente preços**):
   ```bash
   python sizing/sizing_copilot.py "<descrição do workload>"
   # ou, a partir de um documento:
   python sizing/sizing_copilot.py --json <amostra.json> --docs <quantidade> --region <região>
   ```
3. Explique a recomendação ao usuário: justifique o tier por working set (cabe em RAM), storage (dados × 1,25), conexões e throughput. Apresente o custo (compute + storage + backup + 10% rede).
4. Se houver um cluster existente, prefira **medir o uso real** via MCP (`atlas-get-metrics`) antes de recomendar.

## Regras
- Heurísticas: working set deve caber em RAM; storage = dados × 1,25; conexões e ops/s limitam o tier mínimo.
- Em produção, recomende sempre PITR e rede privada.
- Estimativa de custo é aproximada; deixe isso claro.
