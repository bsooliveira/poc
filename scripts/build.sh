#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
podman build -t localhost/simplfaq-api:base -f backend/Containerfile backend
if [[ "${1:-}" == "--training" ]]; then
  podman build --target dependencies -t localhost/simplfaq-api:dependencies -f backend/Containerfile backend
  podman build -t localhost/simplfaq-api:poc -f backend/Containerfile.training backend
else
  podman tag localhost/simplfaq-api:base localhost/simplfaq-api:poc
fi
podman build -t localhost/simplfaq-web:poc -f frontend/Containerfile .
