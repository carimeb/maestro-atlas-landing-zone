# Observabilidade — Grafana + MongoDB Atlas

> 🟡 **Tarefa do cliente.** O datasource roda na instância de Grafana do cliente. Aqui vai a receita de integração.

O Atlas expõe métricas que o Grafana consome. Há dois caminhos comuns:

## Opção A — Grafana Cloud / OSS com o plugin MongoDB Atlas

1. Gere uma **Programmatic API Key** no Atlas (escopo: Project Read Only).
2. No Grafana, instale o datasource **MongoDB Atlas** (ou use o plugin de integração via Prometheus).
3. Configure com `public_key`, `private_key`, `Organization ID`, `Project (Group) ID`.
4. Importe um dashboard com os painéis: CPU/System, memória residente, conexões, opcounters, disk IOPS e replication lag (são os painéis simulados no Maestro).

## Opção B — Exportar métricas via Prometheus

1. No Atlas: **Project → Integrations → Prometheus** (Atlas envia métricas no formato Prometheus).
2. Adicione o endpoint como target no seu Prometheus.
3. No Grafana, use o Prometheus como datasource e monte os painéis.

## Métricas-chave a monitorar (alertas)

| Métrica | Alerta sugerido |
|---------|-----------------|
| Normalized System CPU | > 80% por 5 min |
| Connections | > 80% do limite do tier |
| Replication lag | > 10s |
| Disk IOPS | saturação sustentada |
| Opcounters (scan/queries) | picos anômalos |

## Alertas e on-call

- Os alertas do Atlas/Grafana podem disparar **webhooks** para Slack/PagerDuty/ServiceNow.
- Esse webhook é o gancho ideal para o **Ops Copilot / agente de IA** (Day 2): o alerta chega, o agente correlaciona métricas + slow query log e propõe a causa raiz + ação (com aprovação humana).

## Referências

- Atlas Prometheus integration: https://www.mongodb.com/docs/atlas/tutorial/prometheus-integration/
- Atlas metrics: https://www.mongodb.com/docs/atlas/reference/alert-conditions/
