# Build from monorepo root:
#   docker build -f apps/backend/Dockerfile -t <ecr>:<tag> .
#
# Uses AWS Lambda Python base (includes runtime + awslambdaric). Installs app deps on top
# via `uv pip install` (no `pip sync` / no full env replace — avoids breaking awslambdaric).

FROM public.ecr.aws/lambda/python:3.11

COPY --from=ghcr.io/astral-sh/uv:0.6.14 /uv /usr/local/bin/uv

WORKDIR ${LAMBDA_TASK_ROOT}

COPY apps/backend/requirements.txt .

# --system + --break-system-packages: install into Lambda’s /var/lang Python (PEP 668).
# --no-build: wheels only (no numpy/gcc). Falls back: pip install --only-binary=:all: -r requirements.txt
RUN uv pip install \
    --python /var/lang/bin/python3.11 \
    --system \
    --break-system-packages \
    --no-build \
    -r requirements.txt

COPY apps/backend/app ./app
COPY apps/backend/README.md ./README.md
COPY packages ./packages
COPY data ./data

ENV PYTHONPATH=${LAMBDA_TASK_ROOT}/packages \
    PROFILE_DATA_PATH=/var/task/data/dynamic-profile.json \
    DATA_DIR=/var/task/data

CMD ["app.main.handler"]
