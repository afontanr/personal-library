#!/bin/sh
# Construye la imagen para arm64 en esta máquina y la carga en la Raspberry Pi
# por ssh (LibreELEC no tiene git ni compose; ver docs/adr/0001).
# Nunca toca la base de datos de la Pi.
#
# Uso: scripts/deploy-pi.sh root@<ip-pi>
#      PI_HOST=root@<ip-pi> scripts/deploy-pi.sh
set -eu

PI_HOST=${1:-${PI_HOST:-}}
[ -n "$PI_HOST" ] || { echo "uso: $0 root@<ip-pi>" >&2; exit 1; }

cd "$(dirname "$0")/.."

echo "==> Construyendo personal-library:latest (linux/arm64)"
# --output type=docker,dest=- deja la imagen en un tar sin etiquetarla en
# local, así no pisa la imagen amd64 que usa docker compose.
docker buildx build \
    --platform linux/arm64 \
    --tag personal-library:latest \
    --output type=docker,dest=- \
    . | gzip | ssh "$PI_HOST" 'gunzip | docker load'

echo "==> Imagen cargada en $PI_HOST"
echo "Para (re)crear el contenedor, en la Pi:"
echo "  <kodi-raspberrypi-mediacenter>/scripts/update.sh library"
echo "  (la primera vez: scripts/start.sh library caddy)"
