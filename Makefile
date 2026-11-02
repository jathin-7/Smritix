.PHONY: help up down restart logs backend frontend migrate seed setup clean

# Default target
help: ## Show this help
	@echo SMRITIX Development Commands
	@echo ===========================
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

# --- Infrastructure ---

up: ## Start all infrastructure services (PostgreSQL, Qdrant, Redis)
	docker compose -f infrastructure/docker/docker-compose.yml up -d

down: ## Stop all infrastructure services
	docker compose -f infrastructure/docker/docker-compose.yml down

restart: ## Restart all infrastructure services
	docker compose -f infrastructure/docker/docker-compose.yml restart

logs: ## Show infrastructure service logs
	docker compose -f infrastructure/docker/docker-compose.yml logs -f

# --- Backend ---

backend: ## Start the FastAPI backend dev server
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

migrate: ## Run Alembic database migrations
	cd backend && alembic upgrade head

migrate-new: ## Create a new migration (usage: make migrate-new msg="description")
	cd backend && alembic revision --autogenerate -m "$(msg)"

seed: ## Seed the database with development data
	cd backend && python -m scripts.seed

lint-backend: ## Lint backend code with ruff
	cd backend && ruff check . && ruff format --check .

type-check-backend: ## Type check backend with mypy
	cd backend && mypy app/

test-backend: ## Run backend tests
	cd backend && pytest tests/ -v

# --- Frontend ---

frontend: ## Start the Next.js frontend dev server
	cd frontend && npm run dev

lint-frontend: ## Lint frontend code
	cd frontend && npm run lint

type-check-frontend: ## Type check frontend
	cd frontend && npm run type-check

build-frontend: ## Build the frontend for production
	cd frontend && npm run build

# --- Full Stack ---

dev: up ## Start everything for development
	@echo "Infrastructure started. Run 'make backend' and 'make frontend' in separate terminals."

setup: ## First-time setup
	@echo "=== SMRITIX Setup ==="
	@echo "1. Starting infrastructure..."
	docker compose -f infrastructure/docker/docker-compose.yml up -d
	@echo "2. Installing backend dependencies..."
	cd backend && pip install -e ".[dev]"
	@echo "3. Installing frontend dependencies..."
	cd frontend && npm install
	@echo "4. Copying environment file..."
	@if not exist .env copy .env.example .env
	@echo ""
	@echo "=== Setup complete ==="
	@echo "Next steps:"
	@echo "  1. Edit .env and set JWT_SECRET_KEY"
	@echo "  2. Run: make migrate"
	@echo "  3. Run: make backend  (in one terminal)"
	@echo "  4. Run: make frontend (in another terminal)"

clean: ## Remove all generated files and volumes
	docker compose -f infrastructure/docker/docker-compose.yml down -v
	cd frontend && rm -rf node_modules .next
	cd backend && rm -rf __pycache__ .pytest_cache .mypy_cache
