# Construye las imagenes Docker principales del proyecto en el orden requerido.
param(
    [switch]$NoCache,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Test-CommandExists {
    param(
        [Parameter(Mandatory = $true)]
        [string]$CommandName
    )

    return $null -ne (Get-Command $CommandName -ErrorAction SilentlyContinue)
}

function Invoke-DockerBuild {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Image,
        [Parameter(Mandatory = $true)]
        [string]$Context
    )

    $args = @("build", "-t", $Image)
    if ($NoCache) {
        $args += "--no-cache"
    }
    $args += $Context

    Write-Host ""
    Write-Host "Building $Image from $Context"

    if ($DryRun) {
        Write-Host "docker $($args -join ' ')"
        return
    }

    & docker @args
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot

if (-not $DryRun -and -not (Test-CommandExists "docker")) {
    throw "docker is not available in PATH. Start Docker Desktop or install Docker first."
}

$images = @(
    @{ Image = "soca-heavy:latest"; Context = "containers\soca_container" },
    @{ Image = "rsfc-heavy:latest"; Context = "containers\rsfc_container" },
    @{ Image = "resqui-heavy:latest"; Context = "containers\resqui_container" },
    @{ Image = "sw-metadata-bot:latest"; Context = "integrations\sw-metadata-bot-0.5.0" },
    @{ Image = "sw-metadata-bot-conf:latest"; Context = "containers\sw-metadata-bot_container" }
)

foreach ($item in $images) {
    Invoke-DockerBuild -Image $item["Image"] -Context $item["Context"]
}

Write-Host ""
Write-Host "Docker image build sequence completed."
