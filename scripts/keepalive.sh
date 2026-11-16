#!/usr/bin/env bash
# Keeps the published stack and the public tunnel running on this machine.
#
# The watchdog wakes up every 30 seconds and does three things:
#
#   1. starts the Docker stack if any of the services is not running
#   2. restarts the tunnel if the process has died
#   3. writes the current public address to the state directory
#
# It is meant to run under launchd. scripts/install-mac-service.sh copies the
# files it needs into ~/.local/share/health-card, because macOS does not let a
# launchd job read anything inside ~/Documents.
set -uo pipefail

# launchd starts jobs with a minimal PATH, and the Docker CLI lives in
# /usr/local/bin.
export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

ROOT="$(cd "$(dirname "$0")" && pwd)"
PROJECT="${ABHA_PROJECT:-health-card-live}"
COMPOSE="$ROOT/docker-compose.ghcr.yml"
STATE_DIR="${ABHA_STATE_DIR:-$HOME/.local/state/health-card}"
TUNNEL_LOG="$STATE_DIR/tunnel.log"
URL_FILE="$STATE_DIR/public-url.txt"

mkdir -p "$STATE_DIR"
cd "$ROOT"

log() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') $*"
}

while true; do
  # 1. the stack
  if ! docker compose -p "$PROJECT" -f "$COMPOSE" ps --status running --services 2>/dev/null | grep -q gateway; then
    log "stack is not running, starting it"
    docker compose -p "$PROJECT" -f "$COMPOSE" up -d >>"$STATE_DIR/keepalive.log" 2>&1 || true
  fi

  # 2. the tunnel
  if ! pgrep -f "cloudflared .*tunnel" >/dev/null 2>&1; then
    log "tunnel is not running, starting it"
    nohup "$ROOT/tunnel.sh" >>"$TUNNEL_LOG" 2>&1 &
    sleep 15
  fi

  # 3. the current public address
  URL="$(grep -ohE 'https://[a-z0-9.-]+\.trycloudflare\.com' "$TUNNEL_LOG" 2>/dev/null | tail -1 || true)"
  if [ -n "$URL" ]; then
    if [ "$(cat "$URL_FILE" 2>/dev/null || true)" != "$URL" ]; then
      echo "$URL" > "$URL_FILE"
      log "public address: $URL"
    fi
  fi

  sleep 30
done
