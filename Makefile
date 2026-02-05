
PY?=python
PIP?=pip

.PHONY: setup lint test qa

setup:
	$(PIP) install -r requirements.txt

lint:
	black --check src scripts tests || true
	flake8 src scripts tests || true

test:
	pytest -q

qa: lint test
