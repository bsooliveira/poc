#!/usr/bin/env bash
set -euo pipefail
# A Windows-launched foreground WSL process keeps the distro alive; systemd does not.
# stop.sh creates this marker so the session exits without terminating the distro.
stop_marker="/run/user/$(id -u)/simplfaq-wsl-stop"
trap 'exit 0' INT TERM
while [[ ! -e "$stop_marker" ]]; do
  sleep 5
done
