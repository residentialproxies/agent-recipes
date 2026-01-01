.PHONY: help setup run index export test test-cov clean

help:
	@echo "Targets:"
	@echo "  setup     Create venv + install deps"
	@echo "  run       Run Streamlit app"
	@echo "  index     Build data/agents.json (requires SOURCE_REPO=/path/to/repo)"
	@echo "  export    Export SEO static site to ./site"
	@echo "  test      Run unit tests"
	@echo "  test-cov  Run tests with coverage report"
	@echo "  clean     Remove build artifacts"

setup:
	python3 -m venv .venv
	. .venv/bin/activate && pip install -r requirements.txt -r requirements-dev.txt

run:
	streamlit run src/app.py

index:
	@test -n "$(SOURCE_REPO)" || (echo "Set SOURCE_REPO=/path/to/source-repo" && exit 1)
	python3 src/indexer.py --repo "$(SOURCE_REPO)" --output data/agents.json

export:
	python3 src/export_static.py --output site

test:
	.venv/bin/python -m pytest tests/ -q

test-cov:
	.venv/bin/python -m pytest tests/ --cov=src --cov-report=term-missing --cov-report=html

clean:
	rm -rf .pytest_cache .coverage htmlcov .pyc_cache __pycache__
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete 2>/dev/null || true
