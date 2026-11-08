PYTHON ?= .venv/bin/python

.PHONY: setup test test-stdlib analyze analyze-numerical audit plan live-pilot live-main validate-frames

setup:
	python3 -m venv .venv
	$(PYTHON) -m pip install -r requirements.txt

test:
	$(PYTHON) -m pytest -q

test-stdlib:
	python3 -m unittest discover -s tests -v

analyze:
	$(PYTHON) analysis/analyze.py data/pilot.jsonl data/results.jsonl

analyze-numerical:
	python3 analysis/analyze.py data/pilot.jsonl data/results.jsonl --skip-figures

audit:
	python3 tests/independent_audit.py data/pilot.jsonl data/results.jsonl --summary analysis/results_summary.json --output analysis/independent_audit.json

plan:
	python3 experiments/run_experiment.py --split validation --plan-only --output data/design_preview.jsonl

live-pilot:
	python3 experiments/run_experiment.py --split pilot --output data/rerun_pilot.jsonl --workers 8

live-main:
	python3 experiments/run_experiment.py --split main --output data/rerun_main.jsonl --workers 8

validate-frames:
	python3 experiments/validate_frames.py --output data/rerun_frame_validation.jsonl --workers 8
