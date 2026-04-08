VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: install test docker-up docker-down register-connectors clean

install:
	python3.11 -m venv $(VENV)
	$(PIP) install -e ".[dev]"

test:
	$(PYTHON) -m pytest

docker-up:
	docker compose -f docker/compose.yaml up -d

docker-down:
	docker compose -f docker/compose.yaml down -v

register-connectors:
	docker compose -f docker/compose.yaml exec kafka_connect bash /connectors/register-connectors.sh

clean:
	rm -rf .pytest_cache
