# C4 — Contexto (Nível 1)

```mermaid
flowchart LR
  %% Pessoas
  U[Usuário do Sistema<br/>(Administrador/Operador)]:::person

  %% Sistema
  S[Portifólio 2026<br/>Sistema de Orçamentos e Portfólio]:::system

  %% Sistemas externos
  EXTMAIL[Serviço de E-mail<br/>(SMTP/Provider)]:::external
  EXTPDF[Gerador de PDF<br/>(Worker assíncrono)]:::external

  %% Relações
  U -->|Cria e consulta orçamentos<br/>e dados de catálogo| S
  S -->|Envia notificações e e-mails| EXTMAIL
  S -->|Solicita geração de PDF| EXTPDF

  classDef person fill:#fff,stroke:#333,stroke-width:1px;
  classDef system fill:#e8f0fe,stroke:#1a73e8,stroke-width:1px;
  classDef external fill:#fce8e6,stroke:#d93025,stroke-width:1px;