default:
    @just --list

# Install the uv environment.
install:
    @echo "🚀 Creating virtual environment using uv"
    uv sync

# Run code quality tools.
check:
    @echo "🚀 Linting code: Running pre-commit"
    pre-commit run -a
    @echo "🚀 Checking for dependency issues: Running deptry"
    uv run deptry python

# Run all tests.
test: test-unit test-functional

# Run unit tests.
test-unit:
    @echo "🚀 Running unit tests"
    uv run pytest tests/unit

# Run functional tests.
test-functional:
    @echo "🚀 Running functional tests"
    uv run pytest tests/functional

# Update inline snapshots for functional tests.
update-snapshots:
    @echo "🚀 Updating inline snapshots"
    uv run pytest tests/functional --inline-snapshot=update

# Build wheel and sdist files using maturin.
build:
    @echo "🚀 Creating wheel and sdist files"
    maturin build

# Test if documentation can be built without warnings or errors.
docs-test:
    uv run zensical build --strict

# Build and serve the documentation.
docs:
    uv run zensical serve
