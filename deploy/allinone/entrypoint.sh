#!/usr/bin/env bash
# Prepares the container, then hands over to supervisord.
#
# Two things happen here before anything listens.
#
# The port: most hosts dictate the port and pass it in PORT (Render uses
# 10000, Fly uses 8080). Nothing in the image knows the value ahead of time,
# so the nginx configuration is written here.
#
# The seed: on a host with no persistent volume the database is rebuilt on
# every boot. Seeding inside supervisord would leave a window where nginx is
# already answering while the tables are still empty, and a card scanned in
# that window would report an unknown token. Seeding first closes it. The seed
# is idempotent, so a boot with a volume already in place is a no-op.
set -euo pipefail

PORT="${PORT:-80}"

sed -i "s/__PORT__/${PORT}/" /etc/nginx/conf.d/health-card.conf
echo "gateway will listen on port ${PORT}"

export PYTHONPATH="${PYTHONPATH:-/srv/services:/srv}"
export IDENTITY_DB=/data/identity.db
export RECORDS_DB=/data/records.db
export ABDM_DB=/data/abdm.db
export NHCX_DB=/data/nhcx.db
export SOS_DB=/data/sos.db

echo "seeding"
cd /srv
python scripts/seed.py

echo "seed done, starting services"
exec supervisord -c /etc/supervisor/supervisord.conf
