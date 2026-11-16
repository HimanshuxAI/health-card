#!/usr/bin/env bash
# Installs the macOS launchd agents that keep the deployment up.
#
# macOS does not let a launchd job read anything inside ~/Documents, so the
# files the watchdog needs are copied into ~/.local/share/health-card:
#
#   docker-compose.ghcr.yml   the compose file it starts
#   gateway/nginx.conf        the gateway configuration it mounts
#   keepalive.sh              the watchdog
#   tunnel.sh                 the tunnel launcher
#   .tools/cloudflared        the tunnel binary, if it is present
#
# Two agents are written into ~/Library/LaunchAgents:
#
#   com.abha.healthcard.keepalive  runs keepalive.sh, which keeps the Docker
#                                   stack and the tunnel running
#   com.abha.healthcard.caffeinate stops the Mac from sleeping while it serves
#
# Both start at login and are restarted by launchd if they exit.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
INSTALL_DIR="${ABHA_INSTALL_DIR:-$HOME/.local/share/health-card}"
AGENTS="$HOME/Library/LaunchAgents"
STATE_DIR="${ABHA_STATE_DIR:-$HOME/.local/state/health-card}"

mkdir -p "$INSTALL_DIR/gateway" "$INSTALL_DIR/.tools" "$AGENTS" "$STATE_DIR"

cp "$REPO/docker-compose.ghcr.yml" "$INSTALL_DIR/docker-compose.ghcr.yml"
cp "$REPO/gateway/nginx.conf" "$INSTALL_DIR/gateway/nginx.conf"
cp "$REPO/scripts/keepalive.sh" "$INSTALL_DIR/keepalive.sh"
cp "$REPO/scripts/tunnel.sh" "$INSTALL_DIR/tunnel.sh"
chmod +x "$INSTALL_DIR/keepalive.sh" "$INSTALL_DIR/tunnel.sh"

if [ -x "$REPO/.tools/cloudflared" ]; then
  cp "$REPO/.tools/cloudflared" "$INSTALL_DIR/.tools/cloudflared"
  chmod +x "$INSTALL_DIR/.tools/cloudflared"
fi

cat > "$AGENTS/com.abha.healthcard.keepalive.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.abha.healthcard.keepalive</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>$INSTALL_DIR/keepalive.sh</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
  </dict>
  <key>StandardOutPath</key>
  <string>$STATE_DIR/keepalive.out</string>
  <key>StandardErrorPath</key>
  <string>$STATE_DIR/keepalive.err</string>
</dict>
</plist>
PLIST

cat > "$AGENTS/com.abha.healthcard.caffeinate.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.abha.healthcard.caffeinate</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/caffeinate</string>
    <string>-ims</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
</dict>
</plist>
PLIST

# Docker Desktop should also start at login, otherwise the stack has no engine.
defaults write com.docker.docker LoginItem -bool true 2>/dev/null || true

# bootstrap is the current way to register an agent; the legacy "load" only
# registers it and leaves it pending.
launchctl bootout "gui/$(id -u)/com.abha.healthcard.keepalive" 2>/dev/null || true
launchctl bootout "gui/$(id -u)/com.abha.healthcard.caffeinate" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$AGENTS/com.abha.healthcard.keepalive.plist"
launchctl bootstrap "gui/$(id -u)" "$AGENTS/com.abha.healthcard.caffeinate.plist"
launchctl enable "gui/$(id -u)/com.abha.healthcard.keepalive" 2>/dev/null || true
launchctl enable "gui/$(id -u)/com.abha.healthcard.caffeinate" 2>/dev/null || true

echo "Installed:"
echo "  $AGENTS/com.abha.healthcard.keepalive.plist"
echo "  $AGENTS/com.abha.healthcard.caffeinate.plist"
echo "  files in $INSTALL_DIR"
echo
echo "Check the state with: launchctl list | grep com.abha.healthcard"
echo "The current public address is written to $STATE_DIR/public-url.txt"
