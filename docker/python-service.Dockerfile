# ONE Dockerfile for the four Python workers (job-scout, match-scorer, reminder-worker,
# triage-bot). They share the same base, lib and build steps; only the package differs, so a
# build argument picks it. (The API keeps its own Dockerfile: it also ships migrations.)
#
#   docker build -f docker/python-service.Dockerfile --build-arg SERVICE=match-scorer \
#     -t hiretrack-match-scorer:dev .
#
# Build context = repo root (needs uv.lock, libs/ and config/).
ARG PYTHON_IMAGE=python:3.12.15-slim-trixie@sha256:05cda9777409a9c3ffddd94a4c476b79f0769a0b4857f0c7ed9226b6800b0d6f

# ---------- Stage 1: builder ----------
FROM ${PYTHON_IMAGE} AS builder

# The folder under services/ AND the package name in its pyproject.toml (they're the same).
ARG SERVICE
RUN test -n "$SERVICE" || (echo "pass --build-arg SERVICE=<job-scout|match-scorer|reminder-worker|triage-bot>" && exit 1)

COPY --from=ghcr.io/astral-sh/uv:0.12.15 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Layer A: third-party dependencies only (cached until uv.lock or a pyproject changes).
# uv needs every workspace member's pyproject.toml to read the lockfile, so copy them all.
COPY pyproject.toml uv.lock ./
COPY libs/hiretrack_common/pyproject.toml libs/hiretrack_common/
COPY services/api/pyproject.toml services/api/
COPY services/job-scout/pyproject.toml services/job-scout/
COPY services/match-scorer/pyproject.toml services/match-scorer/
COPY services/reminder-worker/pyproject.toml services/reminder-worker/
COPY services/triage-bot/pyproject.toml services/triage-bot/
RUN uv sync --frozen --no-dev --no-install-workspace --package "$SERVICE"

# Layer B: our code. Only this service's source is copied, so other services' changes
# don't invalidate this image's cache.
COPY libs/hiretrack_common/src libs/hiretrack_common/src
COPY services/${SERVICE}/src services/${SERVICE}/src
RUN uv sync --frozen --no-dev --no-editable --package "$SERVICE" \
    # A fixed name for the entry point, so CMD can be exec-form (no shell: the Python process
    # is PID 1 and receives SIGTERM directly, which graceful shutdown depends on).
    && ln -s "/app/.venv/bin/$SERVICE" /app/.venv/bin/service

# ---------- Stage 2: runtime ----------
FROM ${PYTHON_IMAGE}

ARG SERVICE
LABEL org.opencontainers.image.source="https://github.com/Abhas16/hiretrack-platform" \
      org.opencontainers.image.description="HireTrack ${SERVICE}"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

RUN groupadd --system --gid 10001 app \
    && useradd  --system --uid 10001 --gid app --no-create-home app

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
# Default sources.yaml / skills.yaml. In Kubernetes a ConfigMap is mounted over /app/config,
# so the lists change without rebuilding the image.
COPY config /app/config

USER 10001
CMD ["service"]
