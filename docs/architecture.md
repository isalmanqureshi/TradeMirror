# TradeMirror Architecture (Initial)

## Monorepo Layout

- `apps/web`: Next.js frontend
- `services/api`: FastAPI backend
- `packages/shared`: shared contracts/types
- `infra`: local docker-compose stack

## High-level Design

1. Web app calls API over HTTP.
2. API uses Postgres for persistence and Redis for caching/queues.
3. Shared types package keeps request/response contracts aligned.

## Current Scope

- Basic scaffolding only
- Health endpoints
- No business logic yet

## Next Steps

- Add linting/formatting standards
- Add CI workflows
- Add database migration tooling
- Add API versioning and auth foundations
