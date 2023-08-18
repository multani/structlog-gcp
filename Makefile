DIRS = structlog_gcp

all: lint fmt

.PHONY: lint
lint:
	$(MAKE) ruff
	$(MAKE) mypy

.PHONY: ruff
ruff:
	hatch run ruff check $(DIRS)

.PHONY: mypy
mypy:
	hatch run mypy $(DIRS)

.PHONY: fmt
fmt:
	hatch run black $(DIRS)
	hatch run isort $(DIRS)

.PHONY: test
test:
	hatch run test
