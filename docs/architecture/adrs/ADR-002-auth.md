# ADR-002 — Autenticação e Autorização

- Status: **Aceito**
- Data: 2026-02-22

## Contexto
O sistema terá pelo menos dois perfis de acesso:
- **Administrador:** gerencia cadastros (produtos/clientes/usuários) e acessa funcionalidades avançadas.
- **Usuário comum:** usa o sistema para gerar e consultar orçamentos, com restrições.

A solução deve ser simples para o MVP e compatível com SPA (frontend React).

## Decisão
- Utilizar **JWT** para autenticação (ex.: SimpleJWT no DRF).
- Utilizar **RBAC simples** via roles (`ADMIN` e `USER`) no modelo de usuário e permissions no DRF.

## Consequências
### Positivas
- JWT se integra bem com SPA e APIs REST.
- Facilita escalabilidade (tokens stateless).
- RBAC simples atende o MVP com baixo custo de implementação.

### Negativas / Trade-offs
- Necessidade de lidar com refresh/expiração de tokens.
- Revogação de tokens é mais complexa (pode exigir blacklist/rotacionamento).

## Alternativas consideradas
- Sessão/cookies (mais simples no backend, mas exige atenção extra com CSRF e SPA)
- OAuth2 completo (mais robusto, mas exagerado para o MVP)

## Regras de acesso (MVP)
- `ADMIN`: CRUD completo de usuários, clientes, produtos; leitura completa de orçamentos.
- `USER`: CRUD de orçamentos próprios; leitura de catálogo conforme permissões.

## Próximos passos
- Implementar endpoint `/api/auth/token/` e `/api/auth/refresh/`.
- Criar `permissions` no DRF para `IsAdmin`, `IsOwnerOrAdmin`.