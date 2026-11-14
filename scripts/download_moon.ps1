# Downloads the lunar south pole reference files (about 700 MB total) into data\moon.
# Run from the project folder in PowerShell:  .\scripts\download_moon.ps1
# Safe to re-run: finished files are skipped, partial files resume.
$ErrorActionPreference = "Stop"
$dest = Join-Path $PSScriptRoot "..\data\moon"
New-Item -ItemType Directory -Force -Path $dest | Out-Null
$files = @(
  "https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LDEM_80S_80MPP_ADJ.TIF",
  "https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LDSM_80S_80MPP_ADJ.TIF",
  "https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LPSR_80S_20MPP_ADJ.TIF",
  "https://pgda.gsfc.nasa.gov/data/MoonIllumination/AVGVISIB_75S_120M_201608.TIF"
)
foreach ($u in $files) {
  $name = Split-Path $u -Leaf
  $out = Join-Path $dest $name
  Write-Host "Downloading $name ..."
  curl.exe -L --fail -C - -o $out $u
  if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne 33) { Write-Host "FAILED: $name (curl exit $LASTEXITCODE)" -ForegroundColor Red }
}
Write-Host "Done. Files in $dest :"
Get-ChildItem $dest | Format-Table Name, @{n="MB";e={[math]::Round($_.Length/1MB,1)}}
