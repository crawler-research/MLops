#!/usr/bin/env bash
set -euo pipefail

LOG_FILE="install.log"
exec > >(tee -a "$LOG_FILE") 2>&1

note() { echo -e "\n[INFO] $*"; }
has() { command -v "$1" >/dev/null 2>&1; }

# --- Docker ---
if has docker; then
  note "Docker already installed: $(docker --version)"
else
  note "Installing Docker Desktop via Homebrew"
  brew install --cask docker
  note "⚠️ Please start Docker Desktop manually once"
fi

if docker compose version >/dev/null 2>&1; then
  note "docker compose present: $(docker compose version | head -n1)"
else
  note "Installing docker-compose via brew"
  brew install docker-compose
fi

PY_OK=0
if has python3; then
  if python3 -c 'import sys; exit(0 if sys.version_info >= (3,9) else 1)'; then
    PY_OK=1
  fi
fi

if [ $PY_OK -eq 1 ]; then
  note "Python present: $(python3 --version)"
else
  note "Installing Python 3.11 via Homebrew"
  brew install python@3.11
fi

if has pip3; then
  note "pip present: $(pip3 --version)"
else
  note "Installing pip"
  curl -sS https://bootstrap.pypa.io/get-pip.py | python3
fi

REQS=(torch torchvision pillow Django)
for pkg in "${REQS[@]}"; do
  if python3 -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('$pkg') else 1)"; then
    note "Python pkg exists: $pkg"
  else
    note "Installing Python pkg: $pkg"
    if [ "$pkg" = torch ] || [ "$pkg" = torchvision ]; then
      pip3 install --upgrade "$pkg" --index-url https://download.pytorch.org/whl/cpu
    else
      pip3 install --upgrade "$pkg"
    fi
  fi
done
