#!/usr/bin/env bash
# Initialize one Ubuntu 22.04/24.04 group server once.
# Usage: sudo bash setup/bootstrap_ubuntu.sh
# Optional mirror: sudo DOCKER_MIRROR=https://<mirror> bash setup/bootstrap_ubuntu.sh
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "Run this script with sudo." >&2
  exit 1
fi

. /etc/os-release
if [ "$ID" != "ubuntu" ] || { [ "$VERSION_ID" != "22.04" ] && [ "$VERSION_ID" != "24.04" ]; }; then
  echo "Supported hosts: Ubuntu 22.04 or 24.04." >&2
  exit 1
fi

echo "System: $PRETTY_NAME  architecture: $(uname -m)"
apt-get update
apt-get install -y docker.io docker-compose-v2 docker-buildx git make python3 jq
systemctl enable --now docker

if [ -n "${DOCKER_MIRROR:-}" ] && [ ! -f /etc/docker/daemon.json ]; then
  printf '{\n  "registry-mirrors": ["%s"]\n}\n' "$DOCKER_MIRROR" > /etc/docker/daemon.json
  systemctl restart docker
  echo "Configured Docker registry mirror: $DOCKER_MIRROR"
elif [ -f /etc/docker/daemon.json ]; then
  echo "Existing /etc/docker/daemon.json found; leaving it unchanged."
fi

login_user="${SUDO_USER:-}"
if [ -n "$login_user" ] && [ "$login_user" != "root" ]; then
  usermod -aG docker "$login_user"
  echo "Added $login_user to the docker group; log in again for it to take effect."
fi

docker version --format 'Docker {{.Server.Version}}'
docker compose version
echo "Done. Keep the security group limited to SSH; do not expose Docker API ports 2375/2376."
