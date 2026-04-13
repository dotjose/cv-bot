# Build from monorepo root:
#   docker build -f apps/backend/Dockerfile -t <account>.dkr.ecr.<region>.amazonaws.com/<repo>:<tag> .
#
# Python 3.12 image = Amazon Linux 2023 (glibc new enough for numpy 2.4 manylinux_2_27 wheels).
# The 3.11 image is Amazon Linux 2; uv then falls back to numpy sdist and fails (no gcc in image).
FROM public.ecr.aws/lambda/python:3.12

COPY --from=ghcr.io/astral-sh/uv:0.6.14 /uv /usr/local/bin/uv

WORKDIR ${LAMBDA_TASK_ROOT}

COPY apps/backend/pyproject.toml apps/backend/uv.lock ./
COPY apps/backend/README.md ./README.md
COPY apps/backend/app ./app
COPY packages ./packages
COPY data ./data

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON=/var/lang/bin/python3.12 \
    PYTHONPATH=${LAMBDA_TASK_ROOT}/packages \
    PROFILE_DATA_PATH=/var/task/data/dynamic-profile.json \
    DATA_DIR=/var/task/data

RUN uv sync --frozen --no-dev --no-install-project

ENV PATH="${LAMBDA_TASK_ROOT}/.venv/bin:${PATH}"

CMD ["app.main.handler"]
