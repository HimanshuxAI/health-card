#!/usr/bin/env bash
# Starts the public tunnel in front of the local gateway.
#
# Two modes:
#
#   Named tunnel   Set CLOUDFLARE_CONFIG (or create ~/.cloudflared/config.yml)
#                  and the address stays the same across restarts. This is the
#                  one to use for a permanent public link.
#
#   Quick tunnel   No configuration needed. Cloudflare hands out a random
#                  address that changes every time the tunnel restarts.
set -euo pipefail

CONFIG="${CLOUDFLARE_CONFIG:-$HOME/.cloudflared/config.yml}"
LOCAL_PORT="${TUNNEL_LOCAL_PORT:-80}"
HERE="$(cd "$(dirname "$0")" && pwd)"

if command -v cloudflared >/dev/null 2>&1; then
  BIN=cloudflared
elif [ -x "$HERE/.tools/cloudflared" ]; then
  BIN="$HERE/.tools/cloudflared"
elif [ -x "$HERE/../.tools/cloudflared" ]; then
  BIN="$HERE/../.tools/cloudflared"
else
  echo "cloudflared is not installed. See README, section 'Permanent public address'." >&2
  exit 1
fi

if [ -f "$CONFIG" ]; then
  echo "Starting the named tunnel with $CONFIG"
  exec "$BIN" --config "$CONFIG" tunnel run
fi

echo "Starting a quick tunnel on http://localhost:$LOCAL_PORT"
exec "$BIN" tunnel --url "http://localhost:$LOCAL_PORT" --no-autoupdate
