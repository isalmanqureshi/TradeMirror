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
- npm 10+ (or pnpm 9+)
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
npm ci
npm run dev
```

Backend:

```bash
cd services/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## CI

GitHub Actions workflow at `.github/workflows/ci.yml` runs:

- Frontend lint
- Backend tests

## CI and dependency-installation behavior

- CI installs dependencies before running checks (`pip install -r services/api/requirements.txt` before `cd services/api && pytest -q`, and Node package installation before `npm run lint`).
- Running `pytest` or `npm run lint` without first installing dependencies is expected to fail from a clean checkout.
- In restricted environments (including some Codex sandboxes), package registry access can fail with HTTP 403 during `pip install`/`npm install`/`npm ci`; treat this as an environment limitation rather than an application-code failure.

## Notes

- Trading analytics logic is intentionally not implemented yet.
- This setup is a clean foundation for iterative RAG and analytics development.


### 4) Run local checks from a clean checkout

Backend tests:

```bash
cd services/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

Frontend lint:

```bash
cd apps/web
npm ci
npm run lint
```
