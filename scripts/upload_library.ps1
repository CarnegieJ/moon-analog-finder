# Uploads the overlapping-square library (data\cache\lib3, about 650 MB) to the Modal Volume the scoring service reads.
# Run once, and again whenever the library is rebuilt:  powershell -ExecutionPolicy Bypass -File .\scripts\upload_library.ps1
$root = Split-Path $PSScriptRoot -Parent
foreach ($k in "MODAL_TOKEN_ID", "MODAL_TOKEN_SECRET") {
  $line = Get-Content (Join-Path $root ".env") | Where-Object { $_ -match "^$k=" } | Select-Object -First 1
  $v = ($line -replace "^$k=", "").Trim().Trim('"')
  if (-not $v) { Write-Host "$k is empty in .env" -ForegroundColor Red; exit 1 }
  Set-Item -Path "Env:$k" -Value $v
}
Set-Location $root
$env:PYTHONIOENCODING = "utf-8"
python -m modal volume create moon-analogs-lib3 2>$null
foreach ($f in "s.npy", "hist.npy", "pzi.npy", "cols.txt", "country.npy", "country_names.json", "alt.npy") {
  Write-Host "Uploading $f"
  python -m modal volume put --force moon-analogs-lib3 (Join-Path $root "data\cache\lib3\$f") "/$f"
}
python -m modal volume ls moon-analogs-lib3
