# HireTrack web: build the React app with Node, serve the static files with nginx (non-root).
# Build from the repo root:  docker build -t hiretrack-web:dev services/web

# ---------- Stage 1: build the static site ----------
FROM node:26.11.1-alpine@sha256:143494b1da2945f061539253adc65e4f1569ddf07da2d384c022c791a9d90a4a AS build

WORKDIR /app

# Layer A: dependencies (changes rarely -> cached).
# npm ci installs exactly what package-lock.json says (incl. devDependencies the build needs).
COPY package.json package-lock.json ./
RUN npm ci

# Layer B: source code (changes often). TypeScript errors fail the build here.
COPY . .
RUN npm run build

# ---------- Stage 2: serve with nginx as non-root ----------
# Node, node_modules and the source stay behind in stage 1; only dist/ (~5 MB) is copied.
FROM nginxinc/nginx-unprivileged:1.31.7-alpine@sha256:378d0c32f6562f7fd9629170797f57d2b953aa09be983b3daaf4809bb039ca00

LABEL org.opencontainers.image.source="https://github.com/Abhas16/hiretrack-platform" \
      org.opencontainers.image.description="HireTrack web (React SPA on nginx)"

# Our server rules replace nginx's default site (SPA fallback + caching).
COPY nginx.conf /etc/nginx/conf.d/default.conf

# The nginx image runs every executable script in /docker-entrypoint.d/ before starting nginx.
# This one writes /tmp/config.json from env vars, so one image works in every environment.
COPY --chmod=0755 docker/40-runtime-config.sh /docker-entrypoint.d/40-runtime-config.sh

COPY --from=build /app/dist /usr/share/nginx/html

# The image already runs as uid 101 (nginx). Non-root can't bind ports < 1024, hence 8080.
EXPOSE 8080

# busybox wget is included in alpine (no curl).
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ["wget", "-q", "-O", "/dev/null", "http://127.0.0.1:8080/"]
