# Hace que PowerShell falle ante variables no definidas y otros errores comunes.
Set-StrictMode -Version Latest
# Corta la ejecución en cuanto un comando falle para no seguir en un estado inconsistente.
$ErrorActionPreference = "Stop"

function Test-CommandExists {
    param(
        [Parameter(Mandatory = $true)]
        [string]$CommandName
    )

    # Comprueba si el binario/comando está disponible en el PATH actual.
    return $null -ne (Get-Command $CommandName -ErrorAction SilentlyContinue)
}

function Install-WingetPackage {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PackageId,
        [Parameter(Mandatory = $true)]
        [string]$Label
    )

    # Instala el paquete con winget sin interacción extra de confirmación.
    Write-Host "Installing $Label with winget..."
    & winget install --exact --id $PackageId --accept-package-agreements --accept-source-agreements
}

# Este script está pensado solo para Windows; en Linux usamos el script .sh.
if (-not $IsWindows) {
    throw "This script is intended for Windows. Use scripts/install-dev-tools.sh on Linux."
}

# winget es la base del flujo de instalación en Windows, así que lo validamos antes.
if (-not (Test-CommandExists "winget")) {
    throw "winget is not available in PATH. Install App Installer from Microsoft Store or update Windows first."
}

# Lista de herramientas necesarias para desplegar DashVERSE.
# Cada entrada define:
# - Label: texto legible para mostrar al usuario
# - Command: ejecutable que esperamos encontrar en PATH
# - PackageId: identificador del paquete en winget
$tools = @(
    @{ Label = "Git"; Command = "git"; PackageId = "Git.Git" },
    @{ Label = "Docker Desktop"; Command = "docker"; PackageId = "Docker.DockerDesktop" },
    @{ Label = "Minikube"; Command = "minikube"; PackageId = "Kubernetes.minikube" },
    @{ Label = "Helm"; Command = "helm"; PackageId = "Helm.Helm" },
    @{ Label = "kubectl"; Command = "kubectl"; PackageId = "Kubernetes.kubectl" },
    @{ Label = "GNU Make"; Command = "make"; PackageId = "GnuWin32.Make" },
    @{ Label = "OpenTofu"; Command = "tofu"; PackageId = "OpenTofu.Tofu" },
    @{ Label = "Just"; Command = "just"; PackageId = "Casey.Just" },
    @{ Label = "jq"; Command = "jq"; PackageId = "jqlang.jq" }
)

# Estas listas acumulan el resultado final para mostrar un resumen claro.
$installedNow = New-Object System.Collections.Generic.List[string]
$alreadyPresent = New-Object System.Collections.Generic.List[string]
$pendingRestart = New-Object System.Collections.Generic.List[string]

foreach ($tool in $tools) {
    # Si el comando ya existe, no reinstalamos nada.
    if (Test-CommandExists $tool.Command) {
        Write-Host "$($tool.Label) is already available."
        $alreadyPresent.Add($tool.Label) | Out-Null
        continue
    }

    # Si falta, lo instalamos con winget usando su PackageId.
    Install-WingetPackage -PackageId $tool.PackageId -Label $tool.Label

    # Revalidamos tras instalar:
    # - si ya aparece en PATH, la herramienta está lista
    # - si no aparece todavía, normalmente basta con abrir una terminal nueva
    if (Test-CommandExists $tool.Command) {
        Write-Host "$($tool.Label) is ready to use."
        $installedNow.Add($tool.Label) | Out-Null
    }
    else {
        Write-Warning "$($tool.Label) was installed, but the command is not visible in this shell yet."
        $pendingRestart.Add($tool.Label) | Out-Null
    }
}

# Resumen final para saber qué había ya, qué se instaló y qué requiere reiniciar la terminal.
Write-Host ""
Write-Host "Installation summary"
Write-Host "--------------------"
Write-Host "Already available: $([string]::Join(', ', $alreadyPresent))"
Write-Host "Installed now: $([string]::Join(', ', $installedNow))"
Write-Host "Needs a new terminal session: $([string]::Join(', ', $pendingRestart))"
Write-Host ""
# Docker puede estar instalado pero seguir requiriendo autenticación del usuario.
Write-Host "Docker login remains manual. Run 'docker login' or sign in from Docker Desktop before deploying DashVERSE."
Write-Host "DashVERSE deploy should run from Linux/WSL. In that environment, verify: cd integrations/DashVERSE && just check-deps"
Write-Host "DashVERSE also needs ansible-playbook and nc/netcat in the Linux/WSL environment."
