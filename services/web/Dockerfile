# HireTrack web: build the React app with Node, serve the static files with nginx (non-root).
# Build from the repo root:  docker build -t hiretrack-web:dev services/web

# ---------- Stage 1: build the static site ----------
FROM node:26.12.1-alpine@sha256:40cd011b55415bc894e45b02fdd5a5dfde056921b7d23a64c74f80497af48797 AS build

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
FROM nginxinc/nginx-unprivileged:1.31.7-alpine@sha256:b5047b9b76845eac124358373c6852377c52e4b05834a47647e955dd91cb8f1e

LABEL org.opencontainers.image.source="https://github.com/Abhas16/hiretrack-platform" \
      org.opencontainers.image.description="HireTrack web (React SPA on nginx)"

# Pick up Alpine security fixes released after the base image was built (Trivy flagged
# fixed-upstream CVEs in curl/expat/brotli). Trade-off: the build is a little less
# reproducible, so the pinned digest is still bumped by Dependabot as the main fix.
USER root
RUN apk upgrade --no-cache

# Our server rules replace nginx's default site (SPA fallback + caching).
COPY nginx.conf /etc/nginx/conf.d/default.conf

# The nginx image runs every executable script in /docker-entrypoint.d/ before starting nginx.
# This one writes /tmp/config.json from env vars, so one image works in every environment.
COPY --chmod=0755 docker/40-runtime-config.sh /docker-entrypoint.d/40-runtime-config.sh

COPY --from=build /app/dist /usr/share/nginx/html

# The base image already runs as uid 101 (nginx); saying it explicitly documents it and lets
# scanners (Trivy DS-0002) and admission policies verify it. Non-root can't bind ports < 1024,
# hence 8080.
USER 101
EXPOSE 8080

# busybox wget is included in alpine (no curl).
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ["wget", "-q", "-O", "/dev/null", "http://127.0.0.1:8080/"]
