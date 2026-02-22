# ADR-003 — Processamento Assíncrono e Geração de PDF

- Status: **Aceito**
- Data: 2026-02-22

## Contexto
Algumas operações podem ser custosas:
- Geração de PDF de orçamento
- Relatórios mais completos (exportações, agregações)

Executar essas tarefas no request HTTP pode degradar o tempo de resposta e a experiência do usuário.

## Decisão
- Adotar processamento assíncrono com **Celery + Redis** (broker) quando as features de PDF/relatórios entrarem.
- Manter inicialmente um endpoint síncrono simples (se necessário) apenas para MVP, e migrar para async quando o volume justificar.

## Consequências
### Positivas
- API permanece responsiva.
- Tarefas podem ser reprocessadas e monitoradas.
- Escalabilidade horizontal (workers).

### Negativas / Trade-offs
- Aumento de complexidade operacional (mais containers: redis + worker).
- Exige monitoramento (logs, retries, timeouts).

## Alternativas consideradas
- Gerar PDF síncrono no backend (mais simples, mas piora performance)
- Serviços externos de filas (aumenta dependências e custo)

## Próximos passos
- Adicionar `redis` e `worker` no docker-compose quando iniciar a feature de PDF.
- Definir modelo `QuoteDocument` para armazenar status e link do arquivo gerado.