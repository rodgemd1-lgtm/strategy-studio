#!/usr/bin/env bash
set -euo pipefail

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

APP_NAME="RIG GTM CRM"
RUNTIME_DIR="/Users/mikerodgers/strategy-studio/out/twenty-crm"
URL="${RIG_GTM_CRM_URL:-http://localhost:3020/objects/companies}"
HEALTH_URL="${RIG_GTM_CRM_HEALTH_URL:-http://localhost:3020/healthz}"
ARTIFACT_URL="${RIG_GTM_ARTIFACT_URL:-http://127.0.0.1:8096/teasers_2000/haskins-law-firm/index.html}"
ARTIFACT_LOG_FILE="${RUNTIME_DIR}/rig-gtm-artifacts.log"
LOG_FILE="${RUNTIME_DIR}/rig-gtm-crm-launch.log"

mkdir -p "${RUNTIME_DIR}"
touch "${LOG_FILE}"
chmod 600 "${LOG_FILE}" 2>/dev/null || true

log() {
  printf '[%s] %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$*" >>"${LOG_FILE}"
}

notify() {
  /usr/bin/osascript -e "display notification \"$1\" with title \"${APP_NAME}\"" >/dev/null 2>&1 || true
}

wait_for_health() {
  local attempts="${1:-120}"
  local delay="${2:-1}"

  for _ in $(seq 1 "${attempts}"); do
    if /usr/bin/curl -fsS "${HEALTH_URL}" >/dev/null 2>&1; then
      return 0
    fi
    sleep "${delay}"
  done

  return 1
}

start_artifact_server() {
  if /usr/bin/curl -fsS "${ARTIFACT_URL}" >/dev/null 2>&1; then
    log "artifact server already healthy"
    return 0
  fi

  log "starting local artifact server"
  nohup /Users/mikerodgers/strategy-studio/scripts/serve_strategy_artifacts.sh >>"${ARTIFACT_LOG_FILE}" 2>&1 &
}

open_crm_window() {
  if [[ "${RIG_GTM_CRM_NO_BROWSER:-}" == "1" ]]; then
    return 0
  fi

  if [[ -d "/Applications/Google Chrome.app" ]]; then
    /usr/bin/open -na "Google Chrome" --args --app="${URL}" >/dev/null 2>&1 || /usr/bin/open "${URL}"
  elif [[ -d "/Applications/Arc.app" ]]; then
    /usr/bin/open -a "Arc" "${URL}"
  else
    /usr/bin/open "${URL}"
  fi
}

main() {
  log "launch requested"

  if ! command -v docker >/dev/null 2>&1; then
    notify "Docker is not installed or not on PATH."
    log "docker not found"
    exit 1
  fi

  if ! docker info >/dev/null 2>&1; then
    if command -v colima >/dev/null 2>&1; then
      notify "Starting local Docker runtime..."
      log "starting colima"
      colima start --cpus 4 --memory 8 --disk 100 --runtime docker --save-config >>"${LOG_FILE}" 2>&1
    else
      notify "Docker is not running."
      log "docker not running and colima not found"
      exit 1
    fi
  fi

  cd "${RUNTIME_DIR}"
  start_artifact_server
  log "docker compose up"
  docker compose up -d >>"${LOG_FILE}" 2>&1

  if wait_for_health 120 1; then
    log "health ok"
    notify "RIG GTM CRM is ready."
    open_crm_window
  else
    notify "RIG GTM CRM did not become healthy. Check launch log."
    log "health failed"
    exit 1
  fi
}

main "$@"
