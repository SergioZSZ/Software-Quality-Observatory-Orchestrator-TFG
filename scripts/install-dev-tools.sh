#!/usr/bin/env bash
# -e: para si un comando falla
# -u: para si usamos una variable no definida
# -o pipefail: detecta errores dentro de pipelines
set -euo pipefail

has_cmd() {
    # Comprueba si un comando está disponible en PATH.
    command -v "$1" >/dev/null 2>&1
}

need_sudo() {
    # Ejecuta el comando con sudo salvo que ya estemos como root.
    if [[ "${EUID}" -eq 0 ]]; then
        "$@"
    else
        sudo "$@"
    fi
}

install_apt_package() {
    local package_name="$1"
    # Instalación estándar de paquetes del sistema en distribuciones basadas en apt.
    need_sudo apt-get install -y "$package_name"
}

install_snap_package() {
    local package_name="$1"
    # Usamos --classic porque estas herramientas de CLI suelen necesitar acceso amplio al sistema.
    need_sudo snap install "$package_name" --classic
}

# Este script está orientado a Linux; en Windows usamos el .ps1.
if [[ "$(uname -s)" != "Linux" ]]; then
    echo "This script is intended for Linux. Use scripts/install-dev-tools.ps1 on Windows."
    exit 1
fi

# El flujo Linux de este script asume apt para paquetes base.
if ! has_cmd apt-get; then
    echo "apt-get is required for this script."
    echo "Install the tools manually on your distribution if it does not provide apt."
    exit 1
fi

# Y snap para las herramientas de despliegue que hemos decidido instalar así.
if ! has_cmd snap; then
    echo "snap is required for minikube, helm, kubectl and OpenTofu in this script."
    echo "Install snapd first or adapt the script for your distribution."
    exit 1
fi

# Actualizamos el índice de paquetes antes de instalar nada con apt.
need_sudo apt-get update

# Arrays para el resumen final.
already_present=()
installed_now=()

# Docker en Linux depende mucho de la distro y de la configuración del repositorio,
# así que aquí solo avisamos si falta en vez de intentar forzar una instalación genérica.
if has_cmd docker; then
    already_present+=("Docker")
else
    echo "Docker is not installed. Install it manually for your distribution before deploying DashVERSE."
fi

# make sí lo resolvemos con apt porque es una dependencia simple y estable.
if has_cmd make; then
    already_present+=("make")
else
    echo "Installing make with apt..."
    install_apt_package make
    installed_now+=("make")
fi

# Para el resto del stack comprobamos primero si ya está instalado
# y solo en caso contrario lanzamos la instalación.
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

# Resumen final para ver rápidamente el estado del entorno tras ejecutar el script.
echo
echo "Installation summary"
echo "--------------------"
echo "Already available: ${already_present[*]:-none}"
echo "Installed now: ${installed_now[*]:-none}"
echo
# Aunque Docker exista, el usuario aún puede necesitar autenticarse manualmente.
echo "Docker login remains manual. Run 'docker login' before deploying DashVERSE."
