.PHONY: help install test test-unit test-integration test-e2e coverage clean

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install test dependencies
	pip install -r requirements.txt
	pip install pytest pytest-asyncio pytest-cov pytest-mock pytest-xdist

test: ## Run all tests
	pytest

test-unit: ## Run unit tests only
	pytest -m unit -v

test-integration: ## Run integration tests only
	pytest -m integration -v

test-e2e: ## Run E2E tests only
	pytest -m e2e -v

test-parallel: ## Run tests in parallel (faster)
	pytest -n auto

test-failed: ## Run only failed tests from last run
	pytest --lf

coverage: ## Generate coverage report
	pytest --cov=app --cov-report=html --cov-report=term --cov-report=xml

coverage-html: coverage ## Open HTML coverage report in browser
	@echo "Opening coverage report..."
	@if command -v xdg-open >/dev/null 2>&1; then \
		xdg-open htmlcov/index.html; \
	elif command -v open >/dev/null 2>&1; then \
		open htmlcov/index.html; \
	else \
		start htmlcov/index.html; \
	fi

clean: ## Clean test artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -exec rm -f {} + 2>/dev/null || true
	rm -rf htmlcov/ coverage.xml .pytest_cache/

lint: ## Run linting on tests
	pyflakes tests/
	pycodestyle tests/ --max-line-length=120

format: ## Format test code
	black tests/
	isort tests/

check: lint test ## Run all checks (lint + test)
