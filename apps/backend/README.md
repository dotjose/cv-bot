# CV Bot backend (`apps/backend`)

FastAPI API, **uv**-managed dependencies (`pyproject.toml` + `uv.lock`). Shared code: repo `packages/`.

## Setup

```bash
cd apps/backend
uv sync
```

## Run API

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8787
```

## Ingest

```bash
uv run python -m app.ingest_cli
```

## Docker (Lambda)

Build from **monorepo root**:

```bash
docker build -f apps/backend/Dockerfile -t <tag> .
```

Python **3.11**; installs dependencies with **`uv sync --frozen`** (Mangum handler `app.main.handler`).
