# TradeMirror Monorepo

TradeMirror is a monorepo containing:

- `apps/web`: Next.js (TypeScript) frontend with Tailwind CSS and shadcn/ui-style components.
- `services/api`: FastAPI backend service.
- `packages/shared`: Shared schemas/types for cross-service contracts.
- `infra`: Local infrastructure definitions (Docker Compose).
- `docs`: Architecture and onboarding documentation.

## Prerequisites

- Node.js 20+
- npm 10+
- Python 3.11+
- Docker + Docker Compose

## Local Development

### 1) Install web dependencies

```bash
cd apps/web
npm install
```

### 2) Install API dependencies

```bash
cd services/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3) Start infrastructure and API with Docker Compose

From repository root:

```bash
docker compose -f infra/docker-compose.yml up --build
```

Services:

- API: `http://localhost:8000`
- API health: `http://localhost:8000/health`
- Postgres: `localhost:5432`
- Redis: `localhost:6379`

### 4) Run web app locally

In a new terminal:

```bash
cd apps/web
npm run dev
```

Open `http://localhost:3000`.

## Health Checks

- Web health route: `GET /api/health` (Next.js route handler)
- API health route: `GET /health` (FastAPI)

## Notes

- This scaffold intentionally contains no business logic yet.
- Shared contracts should be added under `packages/shared` and consumed by both frontend and backend.
