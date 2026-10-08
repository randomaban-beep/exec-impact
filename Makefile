PYTHON ?= python

.PHONY: data fit simulate report test

test:
	$(PYTHON) -m ruff check src tests scripts
	$(PYTHON) -m pytest

data:
	$(PYTHON) scripts/download_data.py

fit:
	$(PYTHON) scripts/fit_impact.py

simulate:
	$(PYTHON) scripts/run_simulate.py

report:
	$(PYTHON) scripts/make_report.py
