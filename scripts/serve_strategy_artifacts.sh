#!/usr/bin/env bash
set -euo pipefail

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

ROOT="/Users/mikerodgers/strategy-studio"
OUT_DIR="${ROOT}/out"
PORT="${RIG_GTM_ARTIFACT_PORT:-8096}"
HOST="${RIG_GTM_ARTIFACT_HOST:-127.0.0.1}"

cd "${OUT_DIR}"
exec /usr/bin/python3 -m http.server "${PORT}" --bind "${HOST}"
