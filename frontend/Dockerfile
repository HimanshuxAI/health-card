FROM --platform=$BUILDPLATFORM node:22-alpine AS deps
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# The build stage runs on the native builder platform. Next.js output is
# JavaScript and does not depend on the target architecture, so only the
# runtime image has to be produced per platform.
FROM --platform=$BUILDPLATFORM node:22-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY frontend/ ./
ENV NEXT_TELEMETRY_DISABLED=1
# Next bakes rewrite destinations into the production build, so the gateway URL
# has to be present at build time.
ARG API_GATEWAY_URL=http://gateway:80
ENV API_GATEWAY_URL=$API_GATEWAY_URL
RUN npm run build

FROM --platform=$TARGETPLATFORM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=builder /app/package.json ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/next.config.ts ./
EXPOSE 3000
CMD ["npm", "run", "start"]
