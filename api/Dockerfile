# An example using multi-stage image builds to create a final image without uv.
# Taken from https://github.com/astral-sh/uv-docker-example/blob/main/multistage.Dockerfile

FROM ubuntu:22.04 AS builder

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Install Python 3.12 and other dependencies
RUN DEBIAN_FRONTEND=noninteractive TZ=UTC apt-get update && apt-get install -y \
    software-properties-common \
    && add-apt-repository -y ppa:deadsnakes/ppa \
    && apt-get update \
    && apt-get install -y \
    python3.12 \
    python3.12-venv \
    python3.12-dev \
    python3-pip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create symlinks for python and pip
RUN ln -s /usr/bin/python3.12 /usr/bin/python
RUN ln -s /usr/bin/pip3 /usr/bin/pip

COPY --from=ghcr.io/astral-sh/uv:0.6.8 /uv /bin/uv

WORKDIR /app

# uv keeps package info at the root of the workspace
# Make sure you build this at the root context
COPY uv.lock pyproject.toml .python-version /app/

COPY vendor vendor
COPY packages/ packages/


RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev --package infini-gram-api --no-install-workspace

COPY ./api ./api

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable --package infini-gram-api


# Then, use a final image without uv
FROM ubuntu:22.04 as runner

# It is important to use the image that matches the builder, as the path to the
# Python executable must be the same, e.g., using `python:3.11-slim-bookworm`
# will fail.

# Install Python 3.12 and other dependencies
RUN DEBIAN_FRONTEND=noninteractive TZ=UTC apt-get update && apt-get install -y \
    software-properties-common \
    && add-apt-repository -y ppa:deadsnakes/ppa \
    && apt-get update \
    && apt-get install -y \
    python3.12 \
    python3.12-venv \
    python3.12-dev \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Create symlinks for python and pip
RUN ln -s /usr/bin/python3.12 /usr/bin/python
RUN ln -s /usr/bin/pip3 /usr/bin/pip

# Copy the application from the builder
COPY --from=builder --chown=root:root /app /app

WORKDIR /app/api

COPY vendor/llama-2-7b-hf/ vendor/llama-2-7b-hf/
COPY vendor/olmo-7b-hf/ vendor/olmo-7b-hf/
COPY vendor/llama-2_bow_ids.txt vendor/llama-2_bow_ids.tx

ENV PATH "/app/.venv/bin:$PATH"
ENV TRANSFORMERS_NO_ADVISORY_WARNINGS 1

FROM runner as dev
ENV OTEL_SERVICE_NAME=infinigram-api-dev
ENV OTEL_TRACES_EXPORTER=otlp
ENV OTEL_METRICS_EXPORTER=otlp
ENV OTEL_EXPORTER_OTLP_ENDPOINT="http://otelcol:4318"
ENV ENV=development

CMD ["fastapi", "dev", "app.py", "--port", "7860", "--proxy-headers", "--host", "0.0.0.0"]

FROM runner as prod
ENV OTEL_SERVICE_NAME=infinigram-api
ENV ENV=production

CMD ["fastapi", "run", "app.py", "--port", "7860", "--proxy-headers"]
