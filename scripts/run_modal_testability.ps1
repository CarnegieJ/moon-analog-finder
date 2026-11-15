# Overnight job: scores every lunar spot against the whole Earth library (no downloads). Reads MODAL_TOKEN_ID and MODAL_TOKEN_SECRET from .env (never printed).
param([int]$Limit = 0)
$root = Split-Path $PSScriptRoot -Parent
foreach ($k in "MODAL_TOKEN_ID", "MODAL_TOKEN_SECRET") {
  $line = Get-Content (Join-Path $root ".env") | Where-Object { $_ -match "^$k=" } | Select-Object -First 1
  $v = ($line -replace "^$k=", "").Trim().Trim('"')
  if (-not $v) { Write-Host "$k is empty in .env" -ForegroundColor Red; exit 1 }
  Set-Item -Path "Env:$k" -Value $v
}
Set-Location $root
$env:PYTHONIOENCODING = "utf-8"
if ($Limit -gt 0) { python -m modal run pipeline/modal_testability.py } else { python -m modal run pipeline/modal_testability.py }
