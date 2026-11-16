# syntax=docker/dockerfile:1
#
# One container that runs the whole stack: the five services, the frontend and
# the gateway, with the SQLite files on a single mounted volume.
#
# It exists because the hosts that are still free in 2026 give one service and
# one volume rather than a compose file. docker-compose.ghcr.yml remains the
# deployment for a host that runs Docker properly.
#
#   docker build -f deploy/allinone/Dockerfile -t health-card-allinone .
#   docker run -p 8080:80 -v health-card-data:/data health-card-allinone

# ---------------------------------------------------------------- frontend --
FROM --platform=$BUILDPLATFORM node:22-alpine AS frontend
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
ENV NEXT_TELEMETRY_DISABLED=1
# Next's standalone output carries only the files the server needs, which keeps
# node_modules out of the runtime image.
ENV NEXT_OUTPUT=standalone
# No API_GATEWAY_URL: the rewrites fall back to the loopback ports, and nginx
# in front routes /api/* before Next ever sees it.
RUN npm run build

# ----------------------------------------------------------------- runtime --
FROM python:3.13-slim AS runtime

# Node for the frontend server. The official build is needed rather than
# Debian's packaged one, which is too old for Next 15.
ARG TARGETARCH
ARG NODE_VERSION=22.11.0
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
      ca-certificates curl xz-utils nginx supervisor; \
    arch="${TARGETARCH:-amd64}"; \
    case "${arch}" in \
      amd64) node_arch=x64 ;; \
      arm64) node_arch=arm64 ;; \
      *) echo "unsupported architecture: ${arch}" >&2; exit 1 ;; \
    esac; \
    curl -fsSL "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-${node_arch}.tar.xz" \
      -o /tmp/node.tar.xz; \
    tar -xJf /tmp/node.tar.xz -C /usr/local --strip-components=1; \
    rm /tmp/node.tar.xz; \
    node --version; \
    rm -rf /var/lib/apt/lists/*

WORKDIR /srv
COPY requirements.txt /srv/requirements.txt
RUN pip install --no-cache-dir -r /srv/requirements.txt

COPY services/ /srv/services
COPY scripts/ /srv/scripts

# The standalone server, plus the static assets it expects beside it.
COPY --from=frontend /app/.next/standalone /srv/frontend
COPY --from=frontend /app/.next/static /srv/frontend/.next/static
COPY --from=frontend /app/public /srv/frontend/public

COPY deploy/allinone/supervisord.conf /etc/supervisor/conf.d/health-card.conf
# Debian's nginx reads /etc/nginx/conf.d/*.conf; the package's default site
# would otherwise claim the port first.
COPY deploy/allinone/nginx.conf /etc/nginx/conf.d/health-card.conf
RUN rm -f /etc/nginx/sites-enabled/default

COPY deploy/allinone/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# The SQLite files live here. Mount a volume over it to keep them; on hosts
# with an ephemeral filesystem they are rebuilt by the seed on every boot.
VOLUME /data

ENV PYTHONPATH=/srv/services:/srv
ENV PYTHONUNBUFFERED=1
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

EXPOSE 80

# HEALTHCHECK CMD already runs through a shell, so PORT expands.
HEALTHCHECK --interval=15s --timeout=5s --start-period=40s --retries=5 \
  CMD curl -fsS -o /dev/null "http://127.0.0.1:${PORT:-80}/api/identity/health" || exit 1

CMD ["/usr/local/bin/entrypoint.sh"]
