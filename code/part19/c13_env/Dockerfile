# Research image. Installs exactly what uv.lock says. Build from this directory:
#   docker build -t registry.research.example.com/research/notebook:2026.11.0 .
# Pin the tag to a digest after pushing (the checklist wants image@sha256:...).
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /usr/local/bin/uv
WORKDIR /opt/env
COPY pyproject.toml uv.lock ./
# --frozen: use uv.lock as is and fail if it is missing. --no-install-project: dependencies only.
RUN uv sync --frozen --no-install-project
ENV PATH="/opt/env/.venv/bin:$PATH"
