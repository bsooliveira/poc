#!/usr/bin/env bash
set -euo pipefail
systemctl --user stop simplfaq-web.service simplfaq-api.service simplfaq-ollama.service
if [[ "$(uname -r)" == *[Mm]icrosoft* ]]; then
  touch "/run/user/$(id -u)/simplfaq-wsl-stop"
fi
