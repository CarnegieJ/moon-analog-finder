# Publishes the app to a public Modal URL. Reads the Modal tokens from .env (never printed).
# Run from the project folder:  powershell -ExecutionPolicy Bypass -File .\scripts\deploy_modal.ps1
$root = Split-Path $PSScriptRoot -Parent
foreach ($k in "MODAL_TOKEN_ID", "MODAL_TOKEN_SECRET") {
  $line = Get-Content (Join-Path $root ".env") | Where-Object { $_ -match "^$k=" } | Select-Object -First 1
  $v = ($line -replace "^$k=", "").Trim().Trim('"')
  if (-not $v) { Write-Host "$k is empty in .env" -ForegroundColor Red; exit 1 }
  Set-Item -Path "Env:$k" -Value $v
}
Set-Location $root
$env:PYTHONIOENCODING = "utf-8"
python -m modal deploy pipeline/modal_host.py
