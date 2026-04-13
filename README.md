# CV Bot — serverless AI CV chat

**Frontend:** Next.js static export → S3 + CloudFront. **Backend:** FastAPI on AWS Lambda (container). **AI:** OpenRouter only. **RAG:** Qdrant. **Memory:** S3.

## Layout

| Path | Role |
|------|------|
| `apps/frontend/` | Next.js (Node **only** for `next build` / dev — no Node API) |
| `apps/backend/` | FastAPI + **uv** (`pyproject.toml`, `uv.lock`, `Dockerfile`) |
| `packages/prompts/`, `packages/rag/`, `packages/memory/` | Shared Python libraries |
| `data/` | CV / LinkedIn / summary / website / profile JSON |
| `infra/terraform/` | `main.tf`, `variables.tf`, `outputs.tf`, `terraform.tfvars` (MVP AWS stack) |
| `.github/workflows/deploy.yml` | Push to `main` → build image (`:${GITHUB_SHA}`), Terraform apply, S3 + CloudFront |
| `.github/workflows/destroy.yml` | Manual destroy (type `DESTROY` to confirm) |

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

## Deploy (MVP — GitHub Actions only)

**Flow:** push to `main` uses GitHub Environment **`staging`**; push branch **`production`** uses **`prod`**. Each job resolves **only** that environment’s secrets → AWS auth → Terraform init → optional bootstrap → ECR build/tag/push `:$GITHUB_SHA` → `terraform apply` → Next static export → S3 sync → CloudFront invalidation.

**Secrets (per environment `staging` / `prod` — not repository-level for AWS):** `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`; optional `AWS_ROLE_ARN` (if set, OIDC is used instead of the access keys). Also: `TF_STATE_BUCKET`, `TF_LOCK_TABLE`, `OPENROUTER_API_KEY`, `QDRANT_URL`, `QDRANT_API_KEY` (optional), `NEXT_PUBLIC_API_URL`.

**First deploy:** After the first successful run, open the workflow **summary** and copy **`http_api_endpoint`**. Set `NEXT_PUBLIC_API_URL` to that value, then push again so the static UI points at the live API.

**GitHub OIDC role (IAM) must allow** (attach to the role assumed by Actions): Terraform state (S3 + DynamoDB lock), full Terraform CRUD on this stack, `ecr:GetAuthorizationToken` + ECR push, `s3:Sync` to the **frontend** bucket (or equivalent Put/List/Delete on that bucket prefix), `cloudfront:CreateInvalidation`, and read Terraform outputs. Lambda’s own role is created by Terraform (logs + **chat** S3 bucket `ListBucket` / `GetObject` / `PutObject` only).

**Destroy:** Actions → **Destroy** → choose **target environment** (`staging` or `prod`) → type **`DESTROY`** → `terraform init` / **`terraform destroy -auto-approve`** using that environment’s secrets.

Terraform layout: `infra/terraform/main.tf` (all resources), `variables.tf`, `outputs.tf`, `terraform.tfvars` (safe defaults; CI overrides `enable_api` and `lambda_image_uri`).
