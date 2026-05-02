# TradeMirror Agent Rules

## General
- Keep code production-oriented, typed, and modular.
- Prefer explicit configuration over magic defaults.
- Keep business logic separated by domain boundaries.

## Scope & Boundaries
- Do not implement trading analytics/business alpha logic until explicitly requested.
- Prioritize secure defaults for API and infrastructure changes.

## Backend (`services/api`)
- Use FastAPI + Pydantic models for API contracts.
- Use SQLAlchemy for DB models/session management.
- Keep routers under `app/api` and app wiring in `app/main.py`.
- Write tests for added endpoints.

## Frontend (`apps/web`)
- Use TypeScript strict mode.
- Keep UI components small and composable.
- Use Tailwind utility classes with readable grouping.

## Infra/CI
- Keep Docker images lean and reproducible.
- CI should remain fast and deterministic.
