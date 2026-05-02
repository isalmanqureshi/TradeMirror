# AGENTS.md

## Project
TradeMirror is a RAG chatbot for trading performance analytics.

## Rules
- Do not provide financial advice.
- Do not implement buy/sell recommendations.
- Prefer typed interfaces and tests.
- All analytics must expose sample size.
- All chatbot answers must be grounded in retrieved data or computed metrics.
- Use clear error handling for missing market data.
- Keep backend business logic in services/api/app/services.
- Keep analytics logic in services/api/app/analytics.
- Keep frontend API clients in apps/web/lib/api.
- Add or update tests for every feature.

## Local commands
- docker compose up
- cd services/api && pytest
- cd apps/web && npm run test
- cd apps/web && npm run lint

## Acceptance
A task is not complete unless tests pass and README/docs are updated when behavior changes.
