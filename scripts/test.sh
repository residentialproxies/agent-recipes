#!/bin/bash
# Test runner script for agent-recipes

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "Running pytest with coverage..."
.venv/bin/python -m pytest tests/ --cov=src --cov-report=term-missing --cov-report=html "$@"

echo ""
echo "Coverage report generated in htmlcov/index.html"
