# Arquitetura — Portifólio 2026

Este diretório contém os artefatos de arquitetura e decisões do projeto.

## Índice
- C4 (Contexto): [c4-context.md](./c4-context.md)
- C4 (Containers): [c4-containers.md](./c4-containers.md)
- DER/ERD (Dados): [erd.md](./erd.md)
- ADRs (Decisões): [adrs/README.md](./adrs/README.md)

## Visão geral
O sistema é um monorepositório composto por:
- Backend: Django + Django REST Framework (API)
- Frontend: React (Vite)
- Banco de dados: PostgreSQL
- Infra: Docker (ambiente local) e CI (GitHub Actions)

Os diagramas C4 e o DER inicial suportam a implementação incremental por sprints.
As decisões importantes são registradas como ADRs para rastreabilidade.