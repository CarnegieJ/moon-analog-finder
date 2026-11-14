# Wider Earth search: downloads the Copernicus DEM GLO-90 tiles listed in data\tiles_search.txt (about 400 tiles, roughly 1 to 1.5 GB).
# Run from the project folder:  powershell -ExecutionPolicy Bypass -File .\scripts\download_search.ps1
# Safe to re-run: tiles already on disk are skipped. Runs 8 downloads at a time.
$root = Split-Path $PSScriptRoot -Parent
$dest = Join-Path $root "data\earth"
New-Item -ItemType Directory -Force -Path $dest | Out-Null
$names = Get-Content (Join-Path $root "data\tiles_search.txt") | Where-Object { $_.Trim() }
$cfg = Join-Path $env:TEMP "moon_analogs_curl.txt"
$lines = @(); $todo = 0
foreach ($n in $names) {
  $out = Join-Path $dest "$n.tif"
  if ((Test-Path $out) -and ((Get-Item $out).Length -gt 10000)) { continue }
  $lines += "url = `"https://copernicus-dem-90m.s3.amazonaws.com/$n/$n.tif`""
  $lines += "output = `"$($out -replace '\\','/')`""
  $todo++
}
Write-Host "$($names.Count) tiles listed, $todo to download ..."
if ($todo -gt 0) {
  [IO.File]::WriteAllLines($cfg, $lines)
  curl.exe --parallel --parallel-max 8 --fail -L -s -S --retry 2 -K $cfg
}
# remove empty or failed files
Get-ChildItem $dest -Filter *.tif | Where-Object { $_.Length -lt 10000 } | Remove-Item
$have = ($names | Where-Object { Test-Path (Join-Path $dest "$_.tif") }).Count
Write-Host "Done: $have of $($names.Count) tiles on disk. (A few missing tiles are normal: some map squares are open sea.)"
