# Makefile for Utils Bot v2 development

.PHONY: help install install-dev setup lint format clean run docker-build docker-run migrate

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install production dependencies
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	pip install -r requirements.txt -r requirements-dev.txt

setup: install-dev ## Set up development environment
	pre-commit install
	make migrate

lint: ## Run linting
	flake8 .
	mypy .

format: ## Format code
	black .
	isort .

format-check: ## Check if code is formatted
	black --check .
	isort --check-only .

clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.log" -delete
	rm -rf .mypy_cache

run: ## Run the bot
	python main.py

run-dev: ## Run the bot in development mode
	DEVELOPMENT_MODE=true python main.py

migrate: ## Run database migrations
	python migrations/init_db.py
	python migrations/populate_data.py

docker-build: ## Build Docker image
	docker build -t utils-bot-plus .

docker-run: ## Run with Docker Compose
	docker-compose up -d

docker-stop: ## Stop Docker Compose
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f bot

check: lint ## Run all checks

ci: format-check lint ## Run CI pipeline

dev: setup run-dev ## Set up and run in development mode
