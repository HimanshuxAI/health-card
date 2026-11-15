#!/usr/bin/env bash
# Start all ABHA Health Card services locally (no Docker needed).
set -euo pipefail
cd "$(dirname "$0")"

LOG_DIR=/tmp/abha-services
mkdir -p "$LOG_DIR"
export PYTHONPATH="$(pwd)/services"

PIDS=()

start() {
  local name=$1 port=$2 dir=$3
  echo "Starting $name on :$port"
  (cd "services/$dir" && PYTHONPATH="$PYTHONPATH" uvicorn app.main:app --host 127.0.0.1 --port "$port" >>"$LOG_DIR/$name.log" 2>&1) &
  PIDS+=($!)
}

if [ ! -f services/identity/identity.db ]; then
  echo "Seeding databases..."
  python3 scripts/seed.py
fi

start identity 8001 identity
start records 8002 records
start abdm    8003 abdm
start nhcx    8004 nhcx
start sos     8005 sos

cleanup() {
  echo "Stopping services..."
  kill "${PIDS[@]}" 2>/dev/null || true
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "All services running. Logs in $LOG_DIR. Press Ctrl+C to stop."
wait
