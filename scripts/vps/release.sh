#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
ENV_FILE="${ENV_FILE:-.env.production}"

if [[ -f "${ENV_FILE}" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  set +a
fi

if docker compose version >/dev/null 2>&1; then
  DC=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  DC=(docker-compose)
else
  echo "Error: neither 'docker compose' nor 'docker-compose' is available." >&2
  exit 1
fi

echo "Deploying with ${DC[*]} -f ${COMPOSE_FILE} in ${ROOT_DIR}"

# Pull updated base images (no-op for local build services).
"${DC[@]}" -f "${COMPOSE_FILE}" pull || true

"${DC[@]}" -f "${COMPOSE_FILE}" up -d --build --remove-orphans

wait_for_service_health() {
  local service="$1"
  local id
  id="$("${DC[@]}" -f "${COMPOSE_FILE}" ps -q "${service}" || true)"
  if [[ -z "${id}" ]]; then
    echo "Error: service '${service}' has no container id (not running?)." >&2
    "${DC[@]}" -f "${COMPOSE_FILE}" ps >&2 || true
    return 1
  fi

  local status
  for _ in $(seq 1 60); do
    status="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "${id}" 2>/dev/null || true)"
    if [[ "${status}" == "healthy" || "${status}" == "none" ]]; then
      echo "OK: ${service} (${id}) health=${status}"
      return 0
    fi
    echo "Waiting: ${service} (${id}) health=${status}"
    sleep 2
  done

  echo "Error: ${service} did not become healthy in time (last=${status})." >&2
  "${DC[@]}" -f "${COMPOSE_FILE}" logs --tail=200 "${service}" >&2 || true
  return 1
}

wait_for_service_health "api"
wait_for_service_health "frontend"

frontend_host="${FRONTEND_VIRTUAL_HOST:-agentrecipes.com}"
frontend_host="${frontend_host%%,*}"
frontend_url="${NEXT_PUBLIC_SITE_URL:-https://${frontend_host}}"
api_host="${API_VIRTUAL_HOST:-api.agentrecipes.com}"

echo "Deployment OK."
echo "Frontend: ${frontend_url}"
echo "API:      https://${api_host}/v1/health"
