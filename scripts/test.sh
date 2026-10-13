#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
podman run --rm -v "$PWD/backend:/app:ro" localhost/simplfaq-api:poc ruff check app tests --no-cache
podman run --rm -v "$PWD/backend:/app:ro" localhost/simplfaq-api:poc python -m pytest -q -p no:cacheprovider
podman run --rm --network none -v "$PWD/frontend:/app:ro" -w /app docker.io/library/node:22-alpine node --experimental-strip-types --test tests/api.test.mjs
podman build -t localhost/simplfaq-web:test -f frontend/Containerfile .
