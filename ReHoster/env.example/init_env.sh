#!/usr/bin/env bash
# Creates ReHoster/env/ and ReHoster/docker-compose.yaml from the templates and generates
# random secrets and self-signed TLS material.
# Usage (from the ReHoster folder):  ./env.example/init_env.sh <host name> [turn host name]
# Example:                           ./env.example/init_env.sh rehost.example.net
set -euo pipefail
HOST="${1:?usage: init_env.sh <host name> [turn host name]}"
TURN_HOST="${2:-$HOST}"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REHOSTER="$(dirname "$SRC")"
DST="$REHOSTER/env"

if [ -e "$DST/.env" ]; then echo "$DST/.env already exists - not overwriting"; exit 1; fi
mkdir -p "$DST"
cp -R "$SRC/." "$DST/"
rm -f "$DST/init_env.sh" "$DST/README.md"
find "$DST" -name .gitkeep -delete
# every *.env.example becomes .env
find "$DST" -name .env.example | while read -r f; do mv "$f" "$(dirname "$f")/.env"; done

# host-specific folders and names
rmdir "$DST/envoy/example.org" "$DST/nginx/ssl/live/example.org" 2>/dev/null || true
mkdir -p "$DST/envoy/$HOST" "$DST/nginx/ssl/live/$HOST" "$DST/adb_streamer" "$DST/pihole" "$DST/nginx/public"
subst() { sed -i.bak "$1" "$2" && rm -f "$2.bak"; }
subst "s/example\.org/$HOST/g" "$DST/nginx/app.conf"
for f in "$DST/.env" "$DST/coturn/turnserver.conf"; do subst "s/turn\.example\.org/$TURN_HOST/g" "$f"; done

# random secrets (same Pi-hole password in env/.env and env/pihole/.env)
rnd() { openssl rand -hex 16; }
PIHOLE_PW="$(rnd)"; TURN_PW="$(rnd)"
for f in "$DST/.env" "$DST/pihole/.env"; do subst "s/CHANGE_THIS_SECRET/$PIHOLE_PW/g" "$f"; done
for f in "$DST/.env" "$DST/coturn/turnserver.conf"; do subst "s/CHANGE_THIS_TURN_PASSWORD/$TURN_PW/g" "$f"; done

# self-signed certificates (replace with real ones, e.g. Let's Encrypt, if the host is public)
cert() {  # <cert out> <key out>
  openssl req -x509 -newkey rsa:2048 -nodes -days 365 -subj "/CN=$HOST" \
    -addext "subjectAltName=DNS:$HOST" -keyout "$2" -out "$1" 2>/dev/null
}
cert "$DST/envoy/$HOST/certificate.pem"        "$DST/envoy/$HOST/privkey.pem"
cert "$DST/nginx/ssl/live/$HOST/fullchain.pem" "$DST/nginx/ssl/live/$HOST/privkey.pem"
cert "$DST/adb_streamer/fmd.cert"              "$DST/adb_streamer/fmd.key"
chmod 600 "$DST"/.env "$DST"/*/.env "$DST"/envoy/*/privkey.pem "$DST"/nginx/ssl/live/*/privkey.pem "$DST"/adb_streamer/fmd.key
chmod +x "$DST/envoy/init_envoy.sh"

# docker-compose.yaml and data folders next to it
if [ ! -e "$REHOSTER/docker-compose.yaml" ]; then
  sed "s/example\.org/$HOST/g" "$REHOSTER/docker-compose.example.yaml" > "$REHOSTER/docker-compose.yaml"
  echo "Created $REHOSTER/docker-compose.yaml"
fi
mkdir -p "$REHOSTER/pihole-data" "$REHOSTER/mitmproxy-data" "$REHOSTER/public/.well-known"

echo "Created $DST"
echo "  Pi-hole password : $PIHOLE_PW"
echo "  TURN user/pass   : turnuser / $TURN_PW"
echo "Next: generate env/envoy/envoy.yaml with create_docker_startup_scripts.py, then 'docker compose up -d'."
