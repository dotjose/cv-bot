# Build from monorepo root:
#   docker build -f apps/backend/Dockerfile -t <account>.dkr.ecr.<region>.amazonaws.com/<repo>:<tag> .
#
# Runtime deps: pip install into the Lambda base image (no uv / no venv).

FROM public.ecr.aws/lambda/python:3.11

WORKDIR ${LAMBDA_TASK_ROOT}

COPY apps/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/backend .

COPY packages ./packages
COPY data ./data

ENV PYTHONPATH=${LAMBDA_TASK_ROOT}/packages \
    PROFILE_DATA_PATH=/var/task/data/dynamic-profile.json \
    DATA_DIR=/var/task/data

CMD ["app.main.handler"]
