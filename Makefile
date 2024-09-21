all: fmt mypy test

.PHONY: mypy
mypy:
	hatch run mypy

.PHONY: fmt
fmt:
	hatch run ruff format
	hatch run ruff check --fix

.PHONY: test
test:
	hatch run test
