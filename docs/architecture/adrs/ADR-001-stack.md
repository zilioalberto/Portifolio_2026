# ADR-001 — Stack e Monorepositório

- Status: **Aceito**
- Data: 2026-02-22

## Contexto
O projeto precisa ser desenvolvido em sprints curtas, com rastreabilidade e evidências de engenharia (arquitetura, qualidade e segurança). Deve permitir evolução incremental, testes automatizados e pipeline de integração contínua.

## Decisão
Adotar:
- **Monorepositório** com `backend/`, `frontend/`, `docs/`, `infra/`
- **Backend:** Django + Django REST Framework (API REST)
- **Frontend:** React + Vite
- **Banco:** PostgreSQL
- **Ambiente local:** Docker (compose)
- **CI:** GitHub Actions

## Consequências
### Positivas
- Padronização e rastreabilidade em um único repositório.
- Facilidade de executar o ambiente completo via Docker.
- DRF acelera criação de endpoints REST e autenticação.
- CI reforça qualidade com checks automáticos.

### Negativas / Trade-offs
- Monorepo exige disciplina de CI (pipelines separados por pasta).
- Django/DRF adiciona boilerplate inicial (migrações, settings).

## Alternativas consideradas
- Backend em FastAPI (mais leve, porém exigiria mais decisões de arquitetura/estrutura)
- Repositórios separados (frontend e backend separados, porém dificulta rastreio/entrega no portfólio)

## Links
- Diagramas C4: `docs/architecture/`
- DER inicial: `docs/architecture/erd.md`