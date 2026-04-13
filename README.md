# CV Bot — serverless AI CV chat

**Frontend:** Next.js static export → S3 + CloudFront. **Backend:** FastAPI on AWS Lambda (container). **AI:** OpenRouter only. **RAG:** Qdrant. **Memory:** S3.

## Layout

| Path | Role |
|------|------|
| `apps/frontend/` | Next.js (Node **only** for `next build` / dev — no Node API) |
| `apps/backend/` | FastAPI + **uv** (`pyproject.toml`, `uv.lock`, `Dockerfile`) |
| `packages/prompts/`, `packages/rag/`, `packages/memory/` | Shared Python libraries |
| `data/` | CV / LinkedIn / summary / website / profile JSON |
| `infra/terraform/` | Single root module: S3, ECR, Lambda, HTTP API, CloudFront (no child modules; reproducible from empty AWS + state bucket) |
| `.github/workflows/deploy.yml` | Push `main` / `production` → **GitHub Environment** `staging` / `production` → env secrets → `terraform init` (S3 only) → **apply (full stack)** → ECR push → **apply (Lambda image)** → `outputs.json` → Next → S3 → CF |
| `.github/workflows/destroy.yml` | Manual destroy: confirm + **staging** / **production** (loads secrets from that environment) |

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python 3.11 toolchain + deps)
- Node 20+ **only** when working on `apps/frontend`

## Backend (uv)

```bash
cd apps/backend
uv sync
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8787
```

(`app` registers the monorepo `packages/` path automatically; you do not need `PYTHONPATH` for `uv run`.)

Set `OPENROUTER_API_KEY`, `QDRANT_URL`, etc. (see `.env.example`).

**Ingest (Qdrant index):**

```bash
cd apps/backend
uv run python -m app.ingest_cli
```

**Lockfile updates** (after editing `pyproject.toml`):

```bash
cd apps/backend
uv lock --python 3.11
```

## Frontend

```bash
cd apps/frontend
npm install
npm run dev
# production static export (next.config uses output: "export")
npm run build
npm run export
```

## Lambda image (local only)

From **repo root**: `docker build -f apps/backend/Dockerfile -t <ecr-url>:<tag> .` — uses **`uv sync --frozen`**. Production images are built only in **GitHub Actions** with tag **`${{ github.sha }}`** (not `:latest`-only).

## Deploy (GitHub Actions + Terraform — MVP)

**One-time (AWS console):** create an empty S3 bucket for **Terraform state only** (same logical name can be referenced by per-environment `TF_STATE_BUCKET` secrets if you use one bucket with different prefixes, or two buckets—your choice). No other manual AWS steps for app infra.

**GitHub Environments (required):** create **`staging`** and **`production`** under **Settings → Environments**. Do **not** rely on repository-level secrets for deploy; put the same secret names on **each** environment:

| Secret (required per env) | Purpose |
|----------------------------|---------|
| `AWS_ACCESS_KEY_ID` | CI IAM user |
| `AWS_SECRET_ACCESS_KEY` | CI IAM user |
| `AWS_REGION` | Region for Terraform backend, provider, and `configure-aws-credentials` (**use secrets, not `vars`**) |
| `TF_STATE_BUCKET` | Remote state bucket name |

Optional per environment: `OPENROUTER_API_KEY`, `QDRANT_URL`, `QDRANT_API_KEY`.

**S3 app buckets (Terraform):**

| Bucket | Pattern | Purpose |
|--------|---------|---------|
| Frontend | `cv-bot-{staging\|production}-frontend` | Next `out/` · private · CloudFront OAC only |
| Memory | `cv-bot-{staging\|production}-memory` | Chat JSON at `chat/{sessionId}.json` · private · Lambda IAM only (`ListBucket`, `GetObject`, `PutObject`) |

`{staging\|production}` is `deployment_env` (`main` → **staging**, `production` branch → **production**). ECR repo is `cv-bot-{env}-api`. Lambda **`image_uri` is only the image built and pushed in CI** (never a public `public.ecr.aws/lambda/...` URI in Terraform).

**Remote state keys**

| Branch | GitHub `environment` | `deployment_env` | State object key |
|--------|----------------------|------------------|------------------|
| `main` | `staging` | `staging` | `cv-bot/staging.tfstate` |
| `production` | `production` | `production` | `cv-bot/production.tfstate` |

**CI pipeline:** `terraform init` (S3 backend, **no DynamoDB**) → **`terraform apply -var='lambda_image_uri='`** (S3, ECR, CloudFront, Lambda IAM — **no** Lambda/API until an ECR image exists) → ECR login + **`aws ecr describe-repositories`** (`cv-bot-{env}-api`) → **Docker build + push** (`:${GITHUB_SHA}`) → **`terraform apply -var=lambda_image_uri=<ECR>:<sha>`** (Lambda + HTTP API) → **`terraform output -json` once** → Next build (`NEXT_PUBLIC_API_URL` from `http_api_endpoint`) → `s3 sync` + CloudFront invalidation.

**Required secrets** (copy onto **both** environments): `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `TF_STATE_BUCKET`.

**No DynamoDB / `TF_LOCK_TABLE`:** not supported in this MVP pipeline. Optional app secrets: `OPENROUTER_API_KEY`, `QDRANT_URL`, `QDRANT_API_KEY`.

**Lambda:** image URI uses commit SHA; function is **published**; HTTP API targets the **`live`** alias.

**IAM for CI user:** state bucket read/write, CRUD for this stack, `ecr:DescribeRepositories` + ECR push, S3 sync to **frontend** bucket, CloudFront invalidation.

**Terraform version:** CI uses **1.9.8** (`required_version = ">= 1.9.0"`).

**Local frontend:** `apps/frontend/.env.local.example` → `.env.local`.

**Destroy:** Actions → **Destroy** → pick **staging** or **production** → type **`DESTROY`** → `terraform destroy -auto-approve` (uses matching state key and that environment’s secrets).

**Note:** Bucket names are **deterministic** (no random suffix). Changing `deployment_env` or migrating from older random bucket names can force bucket replacement — prefer fresh accounts or coordinated state/bucket cleanup.

**Terraform outputs (root):** `frontend_bucket`, `memory_bucket`, `ecr_repository_url`, `http_api_endpoint`, `cloudfront_distribution_id`.

**State migration:** If you still have state from the old `module.bootstrap` / `module.app` layout, or older `prod` / `cv-bot/prod.tfstate` naming, use a **new** state key (`cv-bot/staging.tfstate` / `cv-bot/production.tfstate`) or run manual `terraform state` surgery; `deployment_env` is now **`production`**, not `prod`, so resource names changed.
