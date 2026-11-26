FROM node:26-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:26-alpine AS build
WORKDIR /app
# Public values are compiled into the browser code, so they are set at build time.
ARG NEXT_PUBLIC_VIGILO_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_VIGILO_API_URL=$NEXT_PUBLIC_VIGILO_API_URL \
    NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:26-alpine AS run
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0
RUN addgroup -S vigilo && adduser -S vigilo -G vigilo
COPY --from=build --chown=vigilo:vigilo /app/.next/standalone ./
COPY --from=build --chown=vigilo:vigilo /app/.next/static ./.next/static
USER vigilo
EXPOSE 3000
CMD ["node", "server.js"]
