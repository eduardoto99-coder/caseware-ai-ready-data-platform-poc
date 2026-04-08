VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: install demo test serve docker-up docker-down register-connectors clean

install:
	python3.11 -m venv $(VENV)
	$(PIP) install -e ".[dev]"

demo:
	$(PYTHON) scripts/run_demo.py

test:
	$(PYTHON) -m pytest

serve:
	$(PYTHON) scripts/serve_api.py

docker-up:
	docker compose -f docker/compose.yaml up -d

docker-down:
	docker compose -f docker/compose.yaml down -v

register-connectors:
	docker compose -f docker/compose.yaml exec kafka_connect bash /connectors/register-connectors.sh

clean:
	rm -rf data sample_data .pytest_cache
