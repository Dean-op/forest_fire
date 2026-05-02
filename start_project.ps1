[CmdletBinding()]
param(
    [switch]$BackendOnly,
    [switch]$FrontendOnly,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

if ($BackendOnly -and $FrontendOnly) {
    throw "Cannot use -BackendOnly and -FrontendOnly together."
}

$projectRoot = $PSScriptRoot
$backendDir = Join-Path $projectRoot "forest_fire_backend"
$frontendDir = Join-Path $projectRoot "forest_fire_frontend"

function New-LaunchCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$WorkingDirectory,
        [Parameter(Mandatory = $true)]
        [string]$CommandBody,
        [Parameter(Mandatory = $true)]
        [string]$WindowTitle
    )

    return @"
`$Host.UI.RawUI.WindowTitle = '$WindowTitle'
Set-Location -LiteralPath '$WorkingDirectory'
$CommandBody
"@
}

function Start-ProjectProcess {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [string]$LaunchCommand
    )

    if ($DryRun) {
        Write-Host ""
        Write-Host "[$Name]"
        Write-Host $LaunchCommand
        return
    }

    Start-Process -FilePath "powershell.exe" -ArgumentList @(
        "-ExecutionPolicy", "Bypass",
        "-NoExit",
        "-Command", $LaunchCommand
    ) | Out-Null
}

$backendCommand = New-LaunchCommand `
    -WorkingDirectory $backendDir `
    -WindowTitle "Forest Fire Backend" `
    -CommandBody @'
if (Get-Command uv -ErrorAction SilentlyContinue) {
    uv run uvicorn app.main:app --host 127.0.0.1 --port 8010
} elseif (Test-Path ".venv\Scripts\python.exe") {
    & ".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8010
} else {
    Write-Host "Backend runtime not found. Install uv or create forest_fire_backend\\.venv first." -ForegroundColor Red
}
'@

$frontendCommand = New-LaunchCommand `
    -WorkingDirectory $frontendDir `
    -WindowTitle "Forest Fire Frontend" `
    -CommandBody @'
if (Get-Command npm -ErrorAction SilentlyContinue) {
    npm run dev
} else {
    Write-Host "npm was not found. Install Node.js and make sure npm is available." -ForegroundColor Red
}
'@

if (-not $FrontendOnly) {
    Start-ProjectProcess -Name "Backend" -LaunchCommand $backendCommand
}

if (-not $BackendOnly) {
    Start-ProjectProcess -Name "Frontend" -LaunchCommand $frontendCommand
}

if ($DryRun) {
    return
}

Write-Host "Launch commands sent."
if (-not $FrontendOnly) {
    Write-Host "- 后端: http://127.0.0.1:8010"
}
if (-not $BackendOnly) {
    Write-Host "- 前端: http://127.0.0.1:5173"
}
