#!/usr/bin/env bash
# Start all ABHA Health Card services locally (no Docker needed).
set -euo pipefail
cd "$(dirname "$0")"

LOG_DIR=${ABHA_LOG_DIR:-/tmp/abha-services}
mkdir -p "$LOG_DIR"
REPO_ROOT="$(pwd)"
export PYTHONPATH="$REPO_ROOT:$REPO_ROOT/services"
PYTHON="$REPO_ROOT/.venv/bin/python"
UVICORN="$REPO_ROOT/.venv/bin/uvicorn"

PIDS=()

start() {
  local name=$1 port=$2 dir=$3 module=$4
  echo "Starting $name on :$port"
  (cd "services/$dir" && PYTHONPATH="$PYTHONPATH" "$UVICORN" "$module:app" --host 127.0.0.1 --port "$port" >>"$LOG_DIR/$name.log" 2>&1) &
  PIDS+=($!)
}

if [ ! -f services/identity/identity.db ]; then
  echo "Seeding databases..."
  "$PYTHON" scripts/seed.py
fi

start identity 8001 identity identity_app.main
start records 8002 records records_app.main
start abdm    8003 abdm    abdm_app.main
start nhcx    8004 nhcx    nhcx_app.main
start sos     8005 sos     sos_app.main

cleanup() {
  echo "Stopping services..."
  kill "${PIDS[@]}" 2>/dev/null || true
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "All services running. Logs in $LOG_DIR. Press Ctrl+C to stop."
wait
