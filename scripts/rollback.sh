#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/lib.sh"
require_idle
api_version="${1:?Informe a tag da imagem de API a restaurar}"
web_version="${2:?Informe a tag da imagem web a restaurar}"
podman image exists "$api_version"
podman image exists "$web_version"
podman tag "$api_version" localhost/simplfaq-api:poc
podman tag "$web_version" localhost/simplfaq-web:poc
systemctl --user restart simplfaq-api.service simplfaq-web.service
bash "$(dirname "$0")/start.sh"
