---
name: schema-anti-pattern-review
description: Audita a modelagem de dados de uma coleção MongoDB e aponta anti-patterns (arrays unbounded, documentos grandes próximos do limite de 16MB, aninhamento profundo, blobs/base64 embutidos, nomes de campo inválidos). Use quando o usuário pedir revisão de schema, design review, ou enviar um documento/coleção para análise.
---

# Schema Anti-pattern Review

Você revisa a modelagem de dados no MongoDB e recomenda melhorias.

## Quando usar
- O usuário envia um documento JSON ou aponta uma coleção para revisão.
- Há suspeita de problema de modelagem (documentos grandes, queries lentas).

## Procedimento
1. Obtenha um documento representativo:
   - Se o usuário forneceu um JSON, analise direto.
   - Se for uma coleção real, use o MCP `collection-schema` / `find` para amostrar documentos.
2. Rode a análise determinística:
   ```bash
   python sizing/sizing_copilot.py --json <amostra.json> --docs <quantidade>
   ```
3. Reporte cada anti-pattern encontrado com **severidade** (alto/médio/baixo) e uma **recomendação acionável**.

## Anti-patterns a detectar
- **Array unbounded** (cresce sem limite) → usar referências ou bucketing.
- **Documento grande** (perto de 16MB) → revisar embedding vs. referência.
- **Aninhamento profundo** → dificulta indexar/atualizar.
- **Blob/base64 embutido** → mover binário para object storage (ex: S3).
- **Nome de campo com `$` ou `.`** → renomear (quebra queries e drivers).
- **Documento bloated** (campos quentes + frios juntos) → separar para reduzir working set.

## Regras
- Seja específico: cite o caminho do campo e o impacto.
- Quando a coleção é de produção, opere em modo read-only; qualquer mudança de schema é recomendação para o time, não ação automática.
