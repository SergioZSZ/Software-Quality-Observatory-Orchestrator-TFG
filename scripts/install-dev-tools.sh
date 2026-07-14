#!/usr/bin/env bash
# Instala/verifica las herramientas de desarrollo usadas por SQOO y DashVERSE.
set -euo pipefail

has_cmd() {
    command -v "$1" >/dev/null 2>&1
}

need_sudo() {
    if [[ "${EUID}" -eq 0 ]]; then
        "$@"
    else
        sudo "$@"
    fi
}

install_apt_package() {
    local package_name="$1"
    need_sudo apt-get install -y "$package_name"
}

install_snap_package() {
    local package_name="$1"
    need_sudo snap install "$package_name" --classic
}

if [[ "$(uname -s)" != "Linux" ]]; then
    echo "This script is intended for Linux. Use scripts/install-dev-tools.ps1 on Windows."
    exit 1
fi

if ! has_cmd apt-get; then
    echo "apt-get is required for this script."
    echo "Install the tools manually on your distribution if it does not provide apt."
    exit 1
fi

if ! has_cmd snap; then
    echo "snap is required for minikube, helm, kubectl and OpenTofu in this script."
    echo "Install snapd first or adapt the script for your distribution."
    exit 1
fi

need_sudo apt-get update

already_present=()
installed_now=()

if has_cmd docker; then
    already_present+=("Docker")
elif has_cmd podman; then
    already_present+=("Podman")
else
    echo "Docker or Podman is not installed. Install one container runtime before deploying DashVERSE."
fi

apt_packages=(
    git
    curl
    jq
    unzip
    zip
    ansible
    netcat-openbsd
    make
    python3
    python3-venv
    coreutils
)

for package in "${apt_packages[@]}"; do
    echo "Installing/verifying $package with apt..."
    install_apt_package "$package"
done
installed_now+=("apt base packages")

if has_cmd just; then
    already_present+=("just")
else
    echo "Installing just with apt..."
    install_apt_package just
    installed_now+=("just")
fi

if has_cmd minikube; then
    already_present+=("minikube")
else
    echo "Installing minikube with snap..."
    install_snap_package minikube
    installed_now+=("minikube")
fi

if has_cmd helm; then
    already_present+=("helm")
else
    echo "Installing helm with snap..."
    install_snap_package helm
    installed_now+=("helm")
fi

if has_cmd kubectl; then
    already_present+=("kubectl")
else
    echo "Installing kubectl with snap..."
    install_snap_package kubectl
    installed_now+=("kubectl")
fi

if has_cmd tofu; then
    already_present+=("OpenTofu")
else
    echo "Installing OpenTofu with snap..."
    install_snap_package opentofu
    installed_now+=("OpenTofu")
fi

echo
echo "Installation summary"
echo "--------------------"
echo "Already available: ${already_present[*]:-none}"
echo "Installed now: ${installed_now[*]:-none}"
echo
echo "Docker login remains manual. Run 'docker login' before deploying DashVERSE."
echo "DashVERSE dependency check: cd integrations/DashVERSE && just check-deps"
