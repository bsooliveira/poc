#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/lib.sh
require_idle
release="$(date -u +%Y%m%dT%H%M%SZ)"
old_api="localhost/simplfaq-api:previous-$release"
old_web="localhost/simplfaq-web:previous-$release"
podman tag localhost/simplfaq-api:poc "$old_api"
podman tag localhost/simplfaq-web:poc "$old_web"
restore_on_failure() {
  local rc=$?
  trap - EXIT
  if [[ "$rc" != 0 ]]; then
    echo 'Atualização falhou; restaurando imagens anteriores.' >&2
    podman tag "$old_api" localhost/simplfaq-api:poc
    podman tag "$old_web" localhost/simplfaq-web:poc
    systemctl --user restart simplfaq-api.service simplfaq-web.service
  fi
  exit "$rc"
}
trap restore_on_failure EXIT
bash scripts/build.sh "${1:---training}"
require_idle
bash scripts/backup.sh
cp infra/quadlet/* "$HOME/.config/containers/systemd/"
systemctl --user daemon-reload
systemctl --user restart simplfaq-ollama.service simplfaq-api.service simplfaq-web.service
bash scripts/start.sh
printf '\nAtualização concluída. Rollback disponível com:\nbash scripts/rollback.sh %s %s\n' "$old_api" "$old_web"
