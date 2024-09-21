all: fmt mypy test

.PHONY: mypy
mypy:
	uv run mypy

.PHONY: fmt
fmt:
	uv run ruff format
	uv run ruff check --fix

.PHONY: test
test:
	uv run pytest

.PHONY: build
build:
	uv run python -m build --installer=uv
