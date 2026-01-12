.PHONY: help install dev dev-db dev-backend dev-frontend dev-all migrate makemigrations shell test lint format clean

# Colors
GREEN := \033[0;32m
NC := \033[0m

help: ## Show this help message
	@echo "ColdMail Development Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# ===================
# Installation
# ===================

install: ## Install all dependencies
	@echo "Installing backend dependencies..."
	cd backend && source venv/bin/activate && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && pnpm install
	@echo "Done!"

# ===================
# Development
# ===================

dev-db: ## Start development databases (PostgreSQL + Redis)
	docker-compose -f docker-compose.dev.yml up -d
	@echo "Waiting for databases to be ready..."
	@sleep 5
	@echo "Databases are ready!"
	@echo "PostgreSQL: localhost:5432"
	@echo "Redis: localhost:6379"

dev-db-stop: ## Stop development databases
	docker-compose -f docker-compose.dev.yml down

dev-db-clean: ## Stop and remove development database volumes
	docker-compose -f docker-compose.dev.yml down -v

dev-backend: ## Run Django development server
	cd backend && source venv/bin/activate && python manage.py runserver

dev-frontend: ## Run React development server
	cd frontend && pnpm dev

dev-celery: ## Run Celery worker
	cd backend && source venv/bin/activate && celery -A coldmail worker -l info

dev-celery-beat: ## Run Celery beat scheduler
	cd backend && source venv/bin/activate && celery -A coldmail beat -l info

# ===================
# Database
# ===================

migrate: ## Run database migrations
	cd backend && source venv/bin/activate && python manage.py migrate

makemigrations: ## Create new migrations
	cd backend && source venv/bin/activate && python manage.py makemigrations

shell: ## Open Django shell
	cd backend && source venv/bin/activate && python manage.py shell

createsuperuser: ## Create a superuser
	cd backend && source venv/bin/activate && python manage.py createsuperuser

# ===================
# Testing
# ===================

test: ## Run all tests
	cd backend && source venv/bin/activate && pytest

test-cov: ## Run tests with coverage
	cd backend && source venv/bin/activate && pytest --cov=apps --cov-report=html

# ===================
# Code Quality
# ===================

lint: ## Run linters
	cd backend && source venv/bin/activate && flake8 apps
	cd frontend && pnpm lint

format: ## Format code
	cd backend && source venv/bin/activate && black apps
	cd frontend && pnpm format

# ===================
# Production
# ===================

build: ## Build production containers
	docker-compose build

up: ## Start production stack
	docker-compose up -d

down: ## Stop production stack
	docker-compose down

logs: ## View logs
	docker-compose logs -f

# ===================
# Cleanup
# ===================

clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	rm -rf backend/htmlcov
	rm -rf backend/.coverage
	rm -rf frontend/dist
