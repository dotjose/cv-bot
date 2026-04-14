FROM public.ecr.aws/lambda/python:3.12

COPY --from=ghcr.io/astral-sh/uv:0.6.14 /uv /usr/local/bin/uv

WORKDIR ${LAMBDA_TASK_ROOT}

ENV UV_PYTHON=/var/lang/bin/python3.12 \
    UV_LINK_MODE=copy

COPY apps/backend/pyproject.toml apps/backend/uv.lock ./

RUN uv export --frozen --no-dev --no-annotate --no-hashes --no-emit-project -o /tmp/requirements.txt && \
    uv pip sync \
      --python /var/lang/bin/python3.12 \
      --system \
      --break-system-packages \
      --link-mode copy \
      --no-build \
      /tmp/requirements.txt && \
    rm -f /tmp/requirements.txt

COPY apps/backend/app ./app
COPY apps/backend/README.md ./README.md
COPY packages ./packages
COPY data ./data

ENV PYTHONPATH=${LAMBDA_TASK_ROOT}/packages \
    PROFILE_DATA_PATH=/var/task/data/dynamic-profile.json \
    DATA_DIR=/var/task/data

CMD ["app.main.handler"]
