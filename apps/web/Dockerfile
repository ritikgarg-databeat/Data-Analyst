# Data Lab — web frontend
#
# This app lives in an npm-workspaces monorepo and depends on the
# @data-analyst-lab/shared workspace package, so the build context MUST be
# the repo root, not apps/web:
#
#   docker build -f apps/web/Dockerfile -t dal-web .
#
# docker-compose (owned by another engineer) should set:
#   build: { context: ., dockerfile: apps/web/Dockerfile }

FROM node:20-alpine AS base

# ---------------------------------------------------------------------------
# deps: install workspace dependencies with full layer caching
# ---------------------------------------------------------------------------
FROM base AS deps
WORKDIR /repo
COPY package.json package-lock.json ./
COPY apps/web/package.json apps/web/package.json
COPY packages/shared/package.json packages/shared/package.json
RUN npm ci

# ---------------------------------------------------------------------------
# builder: build the Next.js app (standalone output)
# ---------------------------------------------------------------------------
FROM base AS builder
WORKDIR /repo
COPY --from=deps /repo/node_modules ./node_modules
COPY package.json package-lock.json ./
COPY apps/web ./apps/web
COPY packages/shared ./packages/shared

ENV NEXT_TELEMETRY_DISABLED=1

RUN npm run build --workspace=apps/web

# ---------------------------------------------------------------------------
# runner: minimal production image
# ---------------------------------------------------------------------------
FROM base AS runner
WORKDIR /repo

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs \
  && adduser --system --uid 1001 nextjs

COPY --from=builder /repo/apps/web/public ./apps/web/public
COPY --from=builder --chown=nextjs:nodejs /repo/apps/web/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /repo/apps/web/.next/static ./apps/web/.next/static

USER nextjs

EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

CMD ["node", "apps/web/server.js"]
