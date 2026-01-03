#!/bin/bash
set -euo pipefail

# One-click deploy wrapper.
# Prefer `make deploy`, but this script keeps the defaults in one place.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

VPS_SSH="${VPS_SSH:-root@107.174.42.198}"
VPS_PATH="${VPS_PATH:-/opt/docker-projects/heavy-tasks/agent-recipes}"
PROD_SITE_URL="${PROD_SITE_URL:-https://agentrecipes.com}"
PROD_API_URL="${PROD_API_URL:-https://api.agentrecipes.com}"
NEXT_OUTPUT="${NEXT_OUTPUT:-export}"

make deploy \
  VPS_SSH="${VPS_SSH}" \
  VPS_PATH="${VPS_PATH}" \
  PROD_SITE_URL="${PROD_SITE_URL}" \
  PROD_API_URL="${PROD_API_URL}" \
  NEXT_OUTPUT="${NEXT_OUTPUT}"
