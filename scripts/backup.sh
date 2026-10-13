#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/lib.sh"
require_idle
backup_dir="${1:-$HOME/simplfaq-backups}"
mkdir -p "$backup_dir"
umask 077
backup_path="$backup_dir/simplfaq-$(date -u +%Y%m%dT%H%M%SZ).tar"
# Stop writer to include SQLite + WAL and all artifacts as one consistent snapshot.
# Do not execute during a running generation or training unless interruption is intended.
systemctl --user stop simplfaq-api.service
trap 'systemctl --user start simplfaq-api.service; systemctl --user restart simplfaq-web.service' EXIT
podman volume export simplfaq-data --output "$backup_path"
chmod 600 "$backup_path"
sha256sum "$backup_path" > "$backup_path.sha256"
printf 'Backup: %s\n' "$backup_path"
