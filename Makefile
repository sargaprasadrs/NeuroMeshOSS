# Makefile for NeuroMeshOSS Monorepo

.PHONY: help init dev-infra test lint format clean build-all

help:
	@echo "NeuroMeshOSS Build & Development Orchestration"
	@echo "=============================================="
	@echo "init         - Initialize dependencies and pre-commit hooks"
	@echo "dev-infra    - Start local infrastructure (Postgres, Redis, Qdrant, MinIO)"
	@echo "stop-infra   - Stop local infrastructure"
	@echo "test         - Run backend and frontend test suites"
	@echo "lint         - Run linting checks (ruff, mypy, eslint)"
	@echo "format       - Format backend and frontend files"
	@echo "build-all    - Build docker images for production deployment"
	@echo "clean        - Clean build artifacts and temporary files"

init:
	@echo "Initializing workspace environments..."
	cd backend && poetry install
	cd cli && poetry install
	cd sdk/python && poetry install
	cd frontend && npm install
	@echo "Environment initialized. Run 'make dev-infra' to launch databases."

dev-infra:
	docker compose up -d

stop-infra:
	docker compose down

test:
	@echo "Running backend tests..."
	cd backend && poetry run pytest
	@echo "Running frontend tests..."
	cd frontend && npm test -- --passWithNoTests

lint:
	@echo "Linting backend..."
	cd backend && poetry run ruff check . && poetry run mypy src
	@echo "Linting CLI..."
	cd cli && poetry run ruff check . && poetry run mypy src
	@echo "Linting frontend..."
	cd frontend && npm run lint --if-present

format:
	cd backend && poetry run ruff format .
	cd cli && poetry run ruff format .

build-all:
	docker build -f docker/Dockerfile.backend -t neuromesh-backend:latest .
	docker build -f docker/Dockerfile.frontend -t neuromesh-frontend:latest .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".next" -exec rm -rf {} +
	find . -type d -name "node_modules" -exec rm -rf {} +
