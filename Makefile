.PHONY: install
install: ## Install the uv environment.
	@echo "🚀 Creating virtual environment using uv"
	@uv sync

.PHONY: check
check: ## Run code quality tools.
	@echo "🚀 Linting code: Running pre-commit"
	@pre-commit run -a
	@echo "🚀 Checking for dependency issues: Running deptry"
	@uv run deptry python

.PHONY: test
test: test-unit test-functional

.PHONY: test-unit
test-unit: ## Run unit tests.
	@echo "🚀 Running unit tests"
	@uv run pytest tests/unit

.PHONY: test-functional
test-functional: ## Run functional tests.
	@echo "🚀 Running functional tests"
	@uv run pytest tests/functional

.PHONY: build
build: ## Build wheel and sdist files using maturin.
	@echo "🚀 Creating wheel and sdist files"
	@maturin build

.PHONY: docs-test
docs-test: ## Test if documentation can be built without warnings or errors.
	@uv run zensical build --strict

.PHONY: docs
docs: ## Build and serve the documentation.
	@uv run zensical serve

.PHONY: help
help: ## Show help for the commands.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
