# ADR 0001: Integração com IDP via Backstage

Status: aceito
Data: 2026-06-12

## Contexto

Backstage (backstage.io) é o padrão de mercado para Internal Developer Portal (IDP). A maioria dos usuários Enterprise já opera um portal próprio e não adota um portal novo apenas para o fluxo de MongoDB Atlas. O Maestro precisa entregar self-service dentro do portal que o usuário já tem.

## Decisão

1. O Maestro é a camada de domínio Atlas, plugável no IDP do usuário. Ele não compete com o IDP.
2. A camada de agentes (`agent/`, pacote `maestro_agent`) permanece headless: nenhuma lógica de negócio acoplada a UI. Quando o módulo de agente estiver funcional, será exposta uma API HTTP fina para consumo por plugins de portal.
3. A interface em `demo/maestro.html` passa a ser entendida como simulação do portal do usuário, não como produto final.
4. Roteiro de integração, em ordem de custo:
   a. Software Template (scaffolder): provisionamento de cluster como `template.yaml`, reutilizando `templates/*.tfvars` e o workflow do GitHub Actions existentes.
   b. Catalog: clusters provisionados registrados como `Resource`, mapeando a hierarquia `org > project > cluster` para o modelo de entidades do Backstage.
   c. Plugin do Ops Copilot: frontend e backend plugin consumindo a API HTTP da camada de agentes. Depende do item 2.

## Consequências

1. Restrição permanente de design: qualquer módulo novo da camada de agentes nasce sem dependência de UI.
2. O scaffolder template pode ser construído a qualquer momento, pois não depende da camada de agentes.
3. O plugin do Ops Copilot só entra no roadmap após o módulo de memória funcional e a definição da API HTTP.
4. README e ARCHITECTURE devem posicionar o Maestro como camada plugável em IDP na próxima revisão.
