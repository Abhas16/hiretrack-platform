#!/bin/sh
# Writes the runtime config the React app reads at startup (GET /config.json).
# The same image runs everywhere; only these env vars differ per environment.
# Runs automatically: the nginx image executes /docker-entrypoint.d/*.sh before nginx starts.
set -eu

# Unset = local default; set but empty = same origin (the browser calls the host it loaded from).
API_BASE_URL="${API_BASE_URL-http://localhost:8000}"
ENVIRONMENT="${ENVIRONMENT:-local}"
VERSION="${VERSION:-dev}"

cat > /tmp/config.json <<EOF
{"apiBaseUrl": "${API_BASE_URL}", "environment": "${ENVIRONMENT}", "version": "${VERSION}"}
EOF

echo "40-runtime-config: apiBaseUrl=${API_BASE_URL} environment=${ENVIRONMENT} version=${VERSION}"
