.PHONY: help setup run index export test test-cov clean deploy sync-up sync-frontend build-frontend

# Prefer Python 3.11+ (required by this repo). Override if needed:
#   make PYTHON=python3.11 setup
PYTHON ?= python3.11

help:
	@echo "Development:"
	@echo "  setup       Create venv + install deps"
	@echo "  run         Run Streamlit app"
	@echo "  run-api     Run FastAPI server locally"
	@echo "  index       Build data/agents.json (requires SOURCE_REPO=/path/to/repo)"
	@echo "  export      Export SEO static site to ./site"
	@echo "  test        Run unit tests"
	@echo "  test-cov    Run tests with coverage report"
	@echo "  clean       Remove build artifacts"
	@echo ""
	@echo "Deployment:"
	@echo "  build-frontend  Build Next.js frontend"
	@echo "  sync-up         Sync backend to VPS"
	@echo "  sync-frontend   Sync frontend dist to VPS"
	@echo "  deploy          Full deploy (build + sync + deploy on VPS)"

setup:
	$(PYTHON) -m venv .venv
	. .venv/bin/activate && pip install -r requirements.txt -r requirements-dev.txt

run:
	streamlit run src/app.py

run-api:
	uvicorn src.api:app --reload --port 8000

index:
	@test -n "$(SOURCE_REPO)" || (echo "Set SOURCE_REPO=/path/to/source-repo" && exit 1)
	$(PYTHON) src/indexer.py --repo "$(SOURCE_REPO)" --output data/agents.json

export:
	$(PYTHON) src/export_static.py --output site

test:
	.venv/bin/python -m pytest tests/ -q

test-cov:
	.venv/bin/python -m pytest tests/ --cov=src --cov-report=term-missing --cov-report=html

clean:
	rm -rf .pytest_cache .coverage htmlcov .pyc_cache __pycache__
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete 2>/dev/null || true

# ============ Deployment ============
VPS_SSH ?= root@107.174.42.198
VPS_PATH ?= /opt/docker-projects/heavy-tasks/agent-recipes
PROD_SITE_URL ?= https://agentrecipes.com
PROD_API_URL ?= https://api.agentrecipes.com
NEXT_OUTPUT ?= export

build-frontend:
	cd nextjs-app && \
		NEXT_PUBLIC_SITE_URL="$(PROD_SITE_URL)" \
		NEXT_PUBLIC_API_URL="$(PROD_API_URL)" \
		NEXT_OUTPUT="$(NEXT_OUTPUT)" \
		npm ci && npm run build

sync-up:
	rsync -avz \
		--exclude 'node_modules' \
		--exclude '.git' \
		--exclude '.venv' \
		--exclude '.next' \
		--exclude '__pycache__' \
		--exclude '.pytest_cache' \
		--exclude '.ruff_cache' \
		--exclude 'nextjs-app' \
		--exclude 'nextjs-frontend' \
		--exclude 'site' \
		--exclude 'logs' \
		--exclude '*.md' \
		--exclude '.env.local' \
		--exclude '.DS_Store' \
		. $(VPS_SSH):$(VPS_PATH)/

sync-frontend:
	rsync -avz nextjs-app/out/ $(VPS_SSH):$(VPS_PATH)/frontend-dist/

deploy: build-frontend sync-up sync-frontend
	ssh $(VPS_SSH) "cd $(VPS_PATH) && bash scripts/vps/release.sh"
	@echo "Deployed! Frontend: $(PROD_SITE_URL) | API: $(PROD_API_URL)"

logs:
	ssh $(VPS_SSH) "cd $(VPS_PATH) && (docker compose -f docker-compose.prod.yml logs -f || docker-compose -f docker-compose.prod.yml logs -f)"

validate:
	curl -s "$(PROD_API_URL)/v1/health" | $(PYTHON) -m json.tool
