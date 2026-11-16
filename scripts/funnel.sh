#!/usr/bin/env bash
# Publishes the local gateway on a stable public address with Tailscale Funnel.
#
# The address is
#
#     https://<machine>.<tailnet>.ts.net
#
# and it is free on Tailscale's Personal plan. Unlike the cloudflared quick
# tunnel, the name does not change when the machine restarts, so a QR code
# printed on a card keeps pointing at the right place.
#
# Setup is once, in the browser:
#
#   1. install Tailscale for macOS (App Store or Standalone variant — the
#      sandboxed variants can forward a port, which is all this needs)
#   2. sign in, which creates a free Personal tailnet
#   3. run this script; Tailscale shows a page to approve Funnel, and enables
#      MagicDNS and HTTPS certificates for the tailnet as part of it
#
# With --bg, Funnel resumes on its own after a reboot, so there is nothing to
# keep alive afterwards.
set -euo pipefail

TARGET="${FUNNEL_TARGET:-localhost:${TUNNEL_LOCAL_PORT:-80}}"
PUBLIC_PORT="${FUNNEL_HTTPS_PORT:-443}"
STATE_DIR="${ABHA_STATE_DIR:-$HOME/.local/state/health-card}"
URL_FILE="$STATE_DIR/public-url.txt"

if ! command -v tailscale >/dev/null 2>&1; then
  cat >&2 <<'MSG'
tailscale is not installed.

Install Tailscale for macOS (the App Store build, or the Standalone variant),
sign in to create a free Personal tailnet, then run this script again:

  https://tailscale.com/download/mac
MSG
  exit 1
fi

if ! tailscale status >/dev/null 2>&1; then
  echo "tailscale is installed but not signed in. Run: tailscale up" >&2
  exit 1
fi

echo "Publishing $TARGET on https://<machine>.<tailnet>.ts.net (port $PUBLIC_PORT)"
tailscale funnel --bg --https="$PUBLIC_PORT" "$TARGET"

mkdir -p "$STATE_DIR"
URL="$(tailscale funnel status 2>/dev/null | grep -ohE 'https://[A-Za-z0-9.-]+\.ts\.net' | head -1 || true)"
if [ -n "$URL" ]; then
  echo "$URL" > "$URL_FILE"
  # Tells scripts/keepalive.sh that Funnel is the intended public address, so
  # it restarts Funnel rather than falling back to a quick tunnel.
  echo "enabled" > "$STATE_DIR/funnel-enabled"
  echo "Public address: $URL"
  echo "Written to $URL_FILE"
else
  echo "Funnel is configured, but the public address could not be read yet." >&2
  echo "Check it with: tailscale funnel status" >&2
fi
