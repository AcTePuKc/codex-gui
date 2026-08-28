param(
    [Parameter(Mandatory = $true)]
    [string]$CodexExe,

    [Parameter(Mandatory = $true)]
    [string]$WorkingDirectory,

    [Parameter(Mandatory = $false)]
    [string]$RustLog = "codex_core::context_usage_experiment=info,codex_core=info"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $CodexExe)) {
    throw "Codex executable not found: $CodexExe"
}
if (-not (Test-Path $WorkingDirectory)) {
    throw "Working directory not found: $WorkingDirectory"
}

$previousRustLog = $env:RUST_LOG
try {
    $env:RUST_LOG = $RustLog
    Push-Location $WorkingDirectory
    try {
        & $CodexExe
    }
    finally {
        Pop-Location
    }
}
finally {
    $env:RUST_LOG = $previousRustLog
}
