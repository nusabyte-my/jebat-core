# JEBAT Test Suite — Makefile Targets
# Usage:
#   make test            — Run all tests
#   make test-unit       — Run unit tests only (no external deps)
#   make test-integration — Run integration tests only (mocked services)
#   make test-auth       — Run auth tests only
#   make test-ghost      — Run Ghost Database tests only
#   make test-catalyst   — Run Catalyst Observability tests only
#   make test-chat       — Run chat tests only
#   make test-logging    — Run logging tests only
#   make test-slow       — Run slow tests only
#   make coverage        — Run all tests with coverage report
#   make coverage-unit   — Run unit tests with coverage
#   make coverage-html   — Generate HTML coverage report
#   make lint            — Run linting checks
#   make check           — Run all checks (lint + tests + coverage)

PYTEST     ?= python -m pytest
PYTEST_OPTS ?= -v --tb=short --strict-markers
COV_OPTS   ?= --cov=. --cov-report=term-missing --cov-report=xml:coverage.xml

# ─── Test Targets ──────────────────────────────────────────────────

.PHONY: test test-unit test-integration test-auth test-ghost test-catalyst test-chat test-logging test-slow install

test:  ## Run all tests
	$(PYTEST) $(PYTEST_OPTS)

test-unit:  ## Run unit tests (no external dependencies)
	$(PYTEST) $(PYTEST_OPTS) -m "unit"

test-integration:  ## Run integration tests (mocked services)
	$(PYTEST) $(PYTEST_OPTS) -m "integration"

test-auth:  ## Run authentication and key management tests
	$(PYTEST) $(PYTEST_OPTS) -m "auth"

test-ghost:  ## Run Ghost Database feature tests
	$(PYTEST) $(PYTEST_OPTS) -m "ghost"

test-catalyst:  ## Run Catalyst Observability feature tests
	$(PYTEST) $(PYTEST_OPTS) -m "catalyst"

test-chat:  ## Run chat sync and streaming tests
	$(PYTEST) $(PYTEST_OPTS) -m "chat"

test-logging:  ## Run request logging and middleware tests
	$(PYTEST) $(PYTEST_OPTS) -m "logging"

test-slow:  ## Run slow tests
	$(PYTEST) $(PYTEST_OPTS) -m "slow"



install:  ## Install package in editable mode
	pip install --no-build-isolation -e ./jebat-core

# ─── Coverage Targets ─────────────────────────────────────────────

.PHONY: coverage coverage-unit coverage-html coverage-xml

coverage:  ## Run all tests with coverage report
	$(PYTEST) $(PYTEST_OPTS) $(COV_OPTS)

coverage-unit:  ## Run unit tests with coverage
	$(PYTEST) $(PYTEST_OPTS) -m "unit" $(COV_OPTS)

coverage-html:  ## Generate HTML coverage report in htmlcov/
	$(PYTEST) $(PYTEST_OPTS) $(COV_OPTS) --cov-report=html:htmlcov
	@echo "Open htmlcov/index.html in your browser to view the report."

coverage-xml:  ## Generate XML coverage report for CI
	$(PYTEST) $(PYTEST_OPTS) $(COV_OPTS) --cov-report=xml:coverage.xml

# ─── Quality Targets ──────────────────────────────────────────────

.PHONY: lint check

lint:  ## Run linting checks
	python -m py_compile test_*.py
	@echo "✓ Syntax checks passed"

check: lint coverage  ## Run all checks (lint + coverage — coverage already runs all tests)
	@echo "✓ All checks passed"

# ─── Help ─────────────────────────────────────────────────────────

.PHONY: help

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
