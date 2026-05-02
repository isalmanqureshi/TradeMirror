# TradeMirror Monorepo

TradeMirror is a RAG chatbot platform for analyzing a user's trading history, backtests, journals, and market context.

## Monorepo Structure

- `apps/web` – Next.js frontend (TypeScript, Tailwind CSS, shadcn/ui-ready)
- `services/api` – FastAPI backend (SQLAlchemy, Alembic, Pydantic)
- `infra` – Local infrastructure and orchestration (`docker-compose.yml`)
- `docs` – Product and architecture documentation

## Prerequisites

- Docker + Docker Compose
- Node.js 20+
- pnpm 9+ (or npm)
- Python 3.11+

## Quick Start

### 1) Configure environment variables

Copy env examples:

```bash
cp .env.example .env
cp apps/web/.env.example apps/web/.env.local
cp services/api/.env.example services/api/.env
```

### 2) Run with Docker Compose

```bash
docker compose -f infra/docker-compose.yml up --build
```

Services:

- Web: `http://localhost:3000`
- API: `http://localhost:8000`
- API health: `http://localhost:8000/health`

### 3) Run components locally (optional)

Frontend:

```bash
cd apps/web
pnpm install
pnpm dev
```

Backend:

```bash
cd services/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 8000
```

## CI

GitHub Actions workflow at `.github/workflows/ci.yml` runs:

- Frontend lint
- Backend tests

## Notes

- Trading analytics logic is intentionally not implemented yet.
- This setup is a clean foundation for iterative RAG and analytics development.
