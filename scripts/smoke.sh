#!/usr/bin/env bash
set -euo pipefail
endpoint="${1:-http://127.0.0.1:8080}"
check_endpoints() {
  curl --fail --silent "$endpoint/api/health/ready" >/dev/null || return 1
  curl --fail --silent "$endpoint/" >/dev/null || return 1
  if [[ "${SMOKE_HEALTH_ONLY:-0}" == "1" ]]; then
    printf '{"status":"ready"}'
  elif [[ -n "${SMOKE_AUTH_TOKEN:-}" ]]; then
    curl --fail --silent -H "Authorization: Bearer $SMOKE_AUTH_TOKEN" "$endpoint/api/system"
  else
    curl --fail --silent -H 'X-SimplFAQ: local-poc' "$endpoint/api/system"
  fi
}
for attempt in $(seq 1 30); do
  if result=$(check_endpoints); then
    printf '%s\n' "$result"
    exit 0
  fi
  sleep 1
done
echo 'Smoke test falhou' >&2
exit 1
