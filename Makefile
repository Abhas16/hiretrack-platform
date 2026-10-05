# Application targets (Python). Requires uv: https://docs.astral.sh/uv/
# Infra/DevOps targets are added separately.

ALEMBIC := uv run alembic -c services/api/alembic.ini

.PHONY: help install lint format typecheck test test-unit test-integration migrate migration run-api
.PHONY: web-install web-dev web-check web-build

help: ## Show targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  %-18s %s\n", $$1, $$2}'

install: ## Install all workspace packages + dev tools into .venv
	uv sync --all-packages

lint: ## Ruff lint + format check
	uv run ruff check .
	uv run ruff format --check .

format: ## Auto-format and auto-fix lint
	uv run ruff format .
	uv run ruff check --fix .

typecheck: ## mypy (strict) on application code
	uv run mypy libs/hiretrack_common/src services/api/src

test-unit: ## Fast tests, no Docker needed
	uv run pytest -m "not integration"

test-integration: ## Tests against a throwaway Postgres (needs Docker running)
	uv run pytest -m integration

test: ## All tests
	uv run pytest

migrate: ## Apply DB migrations (reads DB_* from .env)
	$(ALEMBIC) upgrade head

migration: ## Create a migration from model changes: make migration m="add salary"
	$(ALEMBIC) revision --autogenerate -m "$(m)"

run-api: ## Run the API locally with auto-reload on http://localhost:8000 (docs at /docs)
	uv run uvicorn hiretrack_api.main:create_app --factory --reload --port 8000

# ---- Frontend (services/web) -------------------------------------------------------------
WEB := cd services/web &&

web-install: ## Install exact frontend dependencies from package-lock.json
	$(WEB) npm ci

web-dev: ## Run the React dev server on http://localhost:5173
	$(WEB) npm run dev

web-check: ## Typecheck, lint, format check and tests for the frontend
	$(WEB) npm run typecheck && npm run lint && npm run format:check && npm test

web-build: ## Production build -> services/web/dist
	$(WEB) npm run build
