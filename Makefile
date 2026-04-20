.PHONY: help install test lint format typecheck check clean build

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install: ## Install in editable mode with dev dependencies
	pip install -e ".[dev]"

test: ## Run tests
	pytest tests/ -v

lint: ## Run ruff linter
	ruff check --no-fix src tests

format: ## Run ruff formatter (fix in place)
	ruff format src tests
	ruff check --fix src tests

format-check: ## Check formatting without changes
	ruff format --check src tests
	ruff check --no-fix src tests

typecheck: ## Run mypy and pyright
	mypy src
	pyright src

check: lint format-check typecheck test ## Run all checks (lint, format, types, tests)

clean: ## Remove build artifacts
	rm -rf dist build src/*.egg-info .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +

build: clean ## Build source and wheel distributions
	python -m build
