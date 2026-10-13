#!/usr/bin/env bash
set -euo pipefail
systemctl --user --no-pager --full status simplfaq-ollama.service simplfaq-api.service simplfaq-web.service
podman ps --filter name=simplfaq
curl --fail --silent http://127.0.0.1:8080/api/health/ready
