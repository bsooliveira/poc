#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/lib.sh
require_idle
podman exec simplfaq-api python -m app.normatives
