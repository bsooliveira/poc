#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ "$(uname -r)" == *[Mm]icrosoft* ]]; then
  rm -f -- "/run/user/$(id -u)/simplfaq-wsl-stop"
  powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass \
    -File "$(wslpath -w "$PWD/scripts/Keep-SimpliFAQWSL.ps1")" \
    -LinuxScriptPath "$PWD/scripts/keep-wsl-alive.sh"
fi
systemctl --user start simplfaq-ollama.service simplfaq-api.service simplfaq-web.service
bash scripts/smoke.sh
