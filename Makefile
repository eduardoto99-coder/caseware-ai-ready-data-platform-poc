VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: install demo test serve clean

install:
	python3.11 -m venv $(VENV)
	$(PIP) install -e ".[dev]"

demo:
	$(PYTHON) scripts/run_demo.py

test:
	$(PYTHON) -m pytest

serve:
	$(PYTHON) scripts/serve_api.py

clean:
	rm -rf data sample_data .pytest_cache
