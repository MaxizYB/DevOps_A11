#!/usr/bin/env bash
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "Run this once as root on the group Ubuntu server." >&2
  exit 1
fi

. /etc/os-release
if [ "$ID" != "ubuntu" ] || { [ "$VERSION_ID" != "22.04" ] && [ "$VERSION_ID" != "24.04" ]; }; then
  echo "Supported hosts: Ubuntu 22.04 or 24.04." >&2
  exit 1
fi

apt-get update
apt-get install -y ca-certificates curl gnupg git make python3

if ! command -v docker >/dev/null || ! docker compose version >/dev/null 2>&1 || ! docker buildx version >/dev/null 2>&1; then
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
  arch="$(dpkg --print-architecture)"
  printf 'deb [arch=%s signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu %s stable\n' "$arch" "$VERSION_CODENAME" > /etc/apt/sources.list.d/docker.list
  apt-get update
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi

docker version
docker compose version
docker buildx version
