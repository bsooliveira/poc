#!/bin/sh
set -eu
dns_resolver=$(awk '/^nameserver / { print $2; exit }' /etc/resolv.conf)
case "$dns_resolver" in
  ''|*[!0-9a-fA-F.:]*) echo 'DNS do container inválido' >&2; exit 1 ;;
esac
sed "s/__PODMAN_DNS__/$dns_resolver/g" /etc/nginx/nginx.conf > /tmp/simplfaq-nginx.conf
exec nginx -c /tmp/simplfaq-nginx.conf -g 'daemon off;'
