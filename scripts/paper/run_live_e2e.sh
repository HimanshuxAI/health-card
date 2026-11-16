#!/usr/bin/env bash
# Start local services, run the 16-step smoke workflow, then stop cleanly.
set -euo pipefail
cd "$(dirname "$0")/../.."

export PYTHONPATH="$(pwd)"
LOG_DIR=/tmp/abha-paper-services
mkdir -p "$LOG_DIR"

if [ ! -f services/identity/identity.db ]; then
  echo "Seeding databases..."
  .venv/bin/python scripts/seed.py
fi

echo "Starting services..."
bash dev.sh > "$LOG_DIR/orchestrator.log" 2>&1 &
DEV_PID=$!
trap 'kill "$DEV_PID" 2>/dev/null || true; wait "$DEV_PID" 2>/dev/null || true' EXIT INT TERM

echo "Waiting for health checks..."
wait_url() {
  local port=$1
  for attempt in $(seq 1 60); do
    if curl -fsS "http://127.0.0.1:$port/health" >/dev/null 2>&1; then
      return 0
    fi
    sleep 0.25
  done
  echo "Service on port $port did not become ready"
  return 1
}

wait_url 8001
wait_url 8002
wait_url 8003
wait_url 8004
wait_url 8005

sleep 2
.venv/bin/python scripts/e2e.py | tee docs/paper/e2e.txt
