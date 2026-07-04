# Image du front Next.js (sortie « standalone » = serveur autonome minimal).
FROM node:22-slim AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:22-slim AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# NEXT_PUBLIC_* est figé au build (injecté dans le bundle navigateur) :
# c'est l'URL de l'API vue depuis le NAVIGATEUR (port publié sur l'hôte).
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:22-slim AS runner
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0
# Serveur autonome + assets statiques + fichiers publics
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
EXPOSE 3000
# API_URL_INTERNAL (URL de l'API dans le réseau Docker) est lue au runtime par le serveur Next.
CMD ["node", "server.js"]
