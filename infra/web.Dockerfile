FROM node:24-slim AS build
RUN npm install -g pnpm@11.25.0
WORKDIR /app
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/web ./apps/web
ENV API_URL=http://api:8000 NEXT_TELEMETRY_DISABLED=1
RUN pnpm install --frozen-lockfile && pnpm --dir apps/web prepare-assets && pnpm build
EXPOSE 3000
CMD ["pnpm","--dir","apps/web","start"]
