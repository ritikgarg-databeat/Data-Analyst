.PHONY: help validate-content sync-content migrate seed setup test-api test-web test-e2e test dev-api dev-web build-python-sandbox test-python-kernel start stop restart lint format health backup restore

help:
	@echo "Ritik's Personal Data Analyst Lab"
	@echo ""
	@echo "  make start                  One-command start: docker compose up --build -d"
	@echo "  make stop                   Stop everything started by 'make start'"
	@echo "  make restart                Restart all Docker services"
	@echo "  make setup                  Install deps, migrate, seed (one-shot LOCAL, non-Docker setup)"
	@echo "  make dev-api                Run the API locally with hot-reload (non-Docker)"
	@echo "  make dev-web                Run the frontend dev server locally (non-Docker)"
	@echo "  make validate-content       Validate content/ files (schema + cross-references)"
	@echo "  make sync-content           Validate then sync content/ into the database"
	@echo "  make migrate                Apply pending Alembic migrations"
	@echo "  make seed                   Seed domains/skills/modules/datasets/tags + sync content"
	@echo "  make health                 Print a dependency-aware system health report"
	@echo "  make check-integrity        Print a referential-integrity audit (orphaned rows, etc.)"
	@echo "  make backup                 Write a timestamped backup to data/backups/"
	@echo "  make restore FILE=<path>    Preview-restore a backup (add YES=1 to actually apply it)"
	@echo "  make test                   Run the full backend + frontend test suites"
	@echo "  make test-api               Run backend pytest suite"
	@echo "  make test-web               Run frontend Vitest suite"
	@echo "  make test-e2e               Run Playwright e2e smoke tests"
	@echo "  make lint                   Lint backend (ruff) + frontend (eslint, tsc)"
	@echo "  make format                 Auto-format backend (ruff format) + frontend (eslint --fix)"
	@echo "  make build-python-sandbox   Build the Python Lab's execution image (requires Docker)"
	@echo "  make test-python-kernel     Run the sandbox kernel's own test suite (no Docker needed)"

validate-content:
	uv run --project apps/api python -m app.content.validate

sync-content:
	uv run --project apps/api python -m app.content.sync

migrate:
	uv run --project apps/api alembic -c alembic.ini upgrade head

seed:
	uv run --project apps/api python -m app.db.seed

setup:
	./scripts/setup.sh

test-api:
	uv run --project apps/api pytest -v

test-web:
	npm run test:web

test-e2e:
	npm run e2e

dev-api:
	uv run --project apps/api uvicorn app.main:app --reload --app-dir apps/api

dev-web:
	npm run dev:web

build-python-sandbox:
	docker compose build python-sandbox

test-python-kernel:
	cd apps/api && uv run pytest tests/test_python_kernel.py -v

start:
	docker compose up --build -d
	@echo ""
	@echo "Ritik's Personal Data Analyst Lab is starting. Open http://localhost:3000 once containers are healthy"
	@echo "('docker compose ps' to check, or 'make health' once the API responds)."

stop:
	docker compose down

restart:
	docker compose restart

health:
	uv run --project apps/api python -m app.db.health_cli

check-integrity:
	uv run --project apps/api python -m app.db.integrity_check_cli

backup:
	uv run --project apps/api python -m app.db.backup_cli

restore:
	@if [ -z "$(FILE)" ]; then echo "Usage: make restore FILE=<path-to-backup.json> [YES=1]"; exit 1; fi
	uv run --project apps/api python -m app.db.restore_cli "$(FILE)" $(if $(YES),--yes,)

lint:
	uv run --project apps/api ruff check .
	npm run lint:web
	npm run typecheck:web

format:
	uv run --project apps/api ruff format .
	npm run lint:web -- --fix

test: test-api test-web
