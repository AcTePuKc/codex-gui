param(
    [Parameter(Mandatory = $false)]
    [string]$CodexHome = "$HOME\.codex",

    [Parameter(Mandatory = $false)]
    [string]$Output = ".\context-usage-experiment.log"
)

$ErrorActionPreference = "Stop"

$logDir = Join-Path $CodexHome "log"
if (-not (Test-Path $logDir)) {
    throw "Codex log directory not found: $logDir"
}

$target = "codex_core::context_usage_experiment"
$files = Get-ChildItem -Path $logDir -File -Recurse | Sort-Object LastWriteTime
$matches = foreach ($file in $files) {
    Select-String -Path $file.FullName -Pattern $target -SimpleMatch -ErrorAction SilentlyContinue |
        ForEach-Object { $_.Line }
}

$matches | Set-Content -Path $Output -Encoding utf8
Write-Host "Saved $($matches.Count) instrumentation lines to $Output"
