#!/usr/bin/env bash
# Binds the gateway to the port the host asks for, then hands over to
# supervisord.
#
# Most hosts dictate the port and pass it in PORT (Render uses 10000, Fly
# uses 8080). Nothing in the image knows the value ahead of time, so the nginx
# configuration is written here.
set -euo pipefail

PORT="${PORT:-80}"

sed -i "s/__PORT__/${PORT}/" /etc/nginx/conf.d/health-card.conf

echo "gateway listening on port ${PORT}"

exec supervisord -c /etc/supervisor/supervisord.conf
