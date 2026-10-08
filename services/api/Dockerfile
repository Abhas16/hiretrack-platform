# One pinned base image for both stages (same OS = compiled wheels built in stage 1 run in stage 2).
# Tag for humans, digest for machines: the digest makes the build reproducible even if the tag moves.
# It's a multi-arch index digest, so it works for both amd64 (laptop) and arm64 (Graviton) builds.
ARG PYTHON_IMAGE=python:3.12.15-slim-trixie@sha256:05cda9777409a9c3ffddd94a4c476b79f0769a0b4857f0c7ed9226b6800b0d6f

# STAGE 1: BUILDER
FROM ${PYTHON_IMAGE} AS builder

COPY --from=ghcr.io/astral-sh/uv:0.12.15 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY libs/hiretrack_common/pyproject.toml ./libs/hiretrack_common/
COPY services/api/pyproject.toml ./services/api/

RUN uv sync --frozen --no-dev --no-install-workspace --package hiretrack-api

# Layer B: our own code. Changes often, so it comes AFTER the dependency layer above.
# --no-editable installs real copies into .venv (an editable install would only point
# back at /app/libs/..., which doesn't exist in the runtime stage).
COPY libs/hiretrack_common/src ./libs/hiretrack_common/src
COPY services/api/src ./services/api/src
RUN uv sync --frozen --no-dev --no-editable --package hiretrack-api

# ---------- Stage 2: runtime ----------
FROM ${PYTHON_IMAGE}

LABEL org.opencontainers.image.source="https://github.com/Abhas16/hiretrack-platform" \
      org.opencontainers.image.description="HireTrack API (FastAPI)"

# PYTHONDONTWRITEBYTECODE: in Kubernetes the filesystem is read-only, so Python must not try to
# write .pyc files at runtime (they were already compiled at build time by UV_COMPILE_BYTECODE).
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

RUN groupadd --system --gid 10001 app \
    && useradd  --system --uid 10001 --gid app --no-create-home app

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY services/api/alembic.ini services/api/alembic.ini
COPY services/api/migrations  services/api/migrations

USER 10001
EXPOSE 8000

# Slim images have no curl, so use Python's standard library. /healthz never touches the DB,
# so a database outage won't mark the container unhealthy. (Kubernetes ignores HEALTHCHECK and
# uses its own probes; this one is for `docker run` and docker-compose.)
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2)"]

CMD ["python", "-m", "hiretrack_api"]
