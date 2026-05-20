# Identidade federada — Azure AD (Microsoft Entra ID)

> 🟡 **Tarefa do cliente.** Configurada no tenant do cliente. Aqui vai o passo a passo + os pontos de integração.

O Maestro usa SSO federado para que o acesso ao Atlas herde a identidade corporativa (ex: domínio `contoso.onmicrosoft.com`).

## 1. Federação no Atlas (SSO)

No Atlas: **Organization Settings → Federated Authentication Settings**.

1. Crie uma *Identity Provider* (SAML) apontando para o Azure AD (Enterprise Application).
2. No Azure AD, crie a Enterprise Application "MongoDB Atlas" (galeria) e configure SAML SSO.
3. Troque os metadados (Entity ID, SSO URL, certificado) entre os dois lados.
4. Verifique o domínio (`contoso.onmicrosoft.com`) e ative *domain mapping*.

## 2. Mapeamento de grupos → roles (RBAC)

Mapeie grupos do Azure AD para roles do Atlas, para que o RBAC siga o diretório corporativo:

| Grupo Azure AD | Role no Atlas |
|----------------|---------------|
| `platform-engineers` | Organization Owner |
| `app-developers` | Project Data Access Read/Write |
| `finops` | Organization Billing Viewer |
| `security` | Organization Read Only + Audit |

## 3. Autenticação de banco (workload)

Para a aplicação, prefira em produção:

- **AWS IAM database authentication**, ou
- **X.509** com certificados gerenciados.

Evite usuário/senha estático em prod (o módulo gera senha apenas para bootstrap/dev).

## Pontos de integração no repo

- O provider `mongodbatlas` autentica via **Programmatic API Key** (não via SSO) — o SSO é para acesso humano ao console.
- Os grupos AD podem ser referenciados em `mongodbatlas_database_user` (LDAP/OIDC) numa evolução futura.

## Referências

- Atlas Federated Authentication: https://www.mongodb.com/docs/atlas/security/federated-authentication/
- Azure AD SAML SSO: https://learn.microsoft.com/azure/active-directory/saas-apps/
