# Build from monorepo root:
#   docker build -f apps/backend/Dockerfile -t <ecr>:<tag> .

FROM public.ecr.aws/lambda/python:3.12

COPY --from=ghcr.io/astral-sh/uv:0.6.14 /uv /usr/local/bin/uv

WORKDIR ${LAMBDA_TASK_ROOT}

ENV UV_PYTHON=/var/lang/bin/python3.12 \
    UV_LINK_MODE=copy \
    UV_PYTHON_PREFERENCE=only-system \
    UV_COMPILE_BYTECODE=1

COPY apps/backend/pyproject.toml apps/backend/uv.lock ./

RUN uv sync --frozen --no-dev --no-install-project --no-build

COPY apps/backend/app ./app
COPY apps/backend/README.md ./README.md
COPY packages ./packages
COPY data ./data

ENV PYTHONPATH=${LAMBDA_TASK_ROOT}/packages \
    PROFILE_DATA_PATH=/var/task/data/dynamic-profile.json \
    DATA_DIR=/var/task/data

ENV PATH="${LAMBDA_TASK_ROOT}/.venv/bin:${PATH}"

CMD ["app.main.handler"]
