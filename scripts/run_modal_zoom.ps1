# Runs stage 2 on Modal: 2 km windows at 30 m for the areas in data\zoom_areas.json. Reads MODAL_TOKEN_ID and MODAL_TOKEN_SECRET from .env (never printed).
# First time only:  pip install modal
# Test with 5 areas first:  powershell -ExecutionPolicy Bypass -File .\scripts\run_modal_zoom.ps1 -Limit 5
# Full run:                    powershell -ExecutionPolicy Bypass -File .\scripts\run_modal_zoom.ps1
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
if ($Limit -gt 0) { python -m modal run pipeline/modal_zoom.py --limit $Limit } else { python -m modal run pipeline/modal_zoom.py }
