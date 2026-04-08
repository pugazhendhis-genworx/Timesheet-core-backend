.PHONY: help install lint format test clean pre-commit-install pre-commit-run dev

help:
	@echo "Available commands:"
	@echo "  make install              - Install project dependencies"
	@echo "  make lint                 - Run ruff linter"
	@echo "  make format               - Format code with ruff"
	@echo "  make format-check         - Check code formatting (without making changes)"
	@echo "  make test                 - Run pytest tests"
	@echo "  make test-cov             - Run tests with coverage report"
	@echo "  make clean                - Clean up cache directories"
	@echo "  make pre-commit-install   - Install pre-commit hooks"
	@echo "  make pre-commit-run       - Run pre-commit hooks on all files"
	@echo "  make dev                  - Full dev setup (install + pre-commit-install)"

install:
	pip install -e .

lint:
	ruff check .

format:
	ruff format .

format-check:
	ruff format . --check

test:
	pytest

test-cov:
	pytest --cov=src --cov-report=term-missing --cov-report=html

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name .coverage -delete 2>/dev/null || true
	@echo "Cache directories cleaned"

pre-commit-install:
	pre-commit install

pre-commit-run:
	pre-commit run --all-files

dev: install pre-commit-install
	@echo "Development environment setup complete!"
	@echo "Run 'make pre-commit-run' to validate all files with pre-commit hooks"
