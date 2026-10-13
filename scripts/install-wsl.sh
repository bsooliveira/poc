#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v podman >/dev/null
mkdir -p "$HOME/.config/containers/systemd" "$HOME/.config/simplfaq"
if [[ ! -f "$HOME/.config/simplfaq/app.env" ]]; then
  install -m 600 .env.example "$HOME/.config/simplfaq/app.env"
fi
cp infra/quadlet/* "$HOME/.config/containers/systemd/"
systemctl --user daemon-reload
systemctl --user start simplfaq-ollama.service
podman exec simplfaq-ollama ollama pull qwen2.5:1.5b
systemctl --user restart simplfaq-api.service simplfaq-web.service
bash scripts/start.sh
printf 'SimplFAQ disponível em http://localhost:8080\n'
