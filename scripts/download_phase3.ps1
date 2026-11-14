# Phase 3 data: Earth temperature + vegetation (NASA MODIS, needs Earthdata token), Moon temperature (LRO Diviner), one extra elevation tile.
# Run from the project folder:  powershell -ExecutionPolicy Bypass -File .\scripts\download_phase3.ps1
# Reads EARTHDATA_TOKEN from .env. The token is never printed. Safe to re-run: finished files are skipped.
$root = Split-Path $PSScriptRoot -Parent
$line = Get-Content (Join-Path $root ".env") | Where-Object { $_ -match "^EARTHDATA_TOKEN=" } | Select-Object -First 1
$token = ($line -replace "^EARTHDATA_TOKEN=", "").Trim().Trim('"')
if (-not $token) { Write-Host "EARTHDATA_TOKEN is empty in .env" -ForegroundColor Red; exit 1 }
$year = 2024

function Get-Modis($short, $destName) {
  $dest = Join-Path $root "data\modis\$destName"; New-Item -ItemType Directory -Force -Path $dest | Out-Null
  $q = "https://cmr.earthdata.nasa.gov/search/granules.json?short_name=$short&version=061&temporal=$year-01-01T00:00:00Z,$year-12-31T23:59:59Z&page_size=50"
  try { $r = Invoke-RestMethod -Uri $q } catch { Write-Host "CMR search failed for $short : $_" -ForegroundColor Red; return }
  $urls = @($r.feed.entry | ForEach-Object { $_.links } | Where-Object { $_.href -match "^https://.*\.hdf$" } | ForEach-Object { $_.href } | Select-Object -Unique)
  Write-Host "$short : found $($urls.Count) files for $year"
  foreach ($u in $urls) {
    $out = Join-Path $dest (Split-Path $u -Leaf)
    if ((Test-Path $out) -and ((Get-Item $out).Length -gt 1000000)) { continue }
    curl.exe -L --fail -s -H "Authorization: Bearer $token" -o $out $u
    if ($LASTEXITCODE -ne 0) { Write-Host "  FAILED: $(Split-Path $u -Leaf) (curl exit $LASTEXITCODE)" -ForegroundColor Red; Remove-Item $out -ErrorAction SilentlyContinue }
  }
  Write-Host ("  on disk: " + (Get-ChildItem $dest -Filter *.hdf).Count + " files")
}
Get-Modis "MOD11C3" "lst"     # monthly land surface temperature, 0.05 degree
Get-Modis "MOD13C2" "ndvi"    # monthly vegetation index, 0.05 degree

Write-Host "Extra elevation tile (Amazon control point) ..."
$t = "Copernicus_DSM_COG_30_S03_00_W060_00_DEM"
curl.exe -L --fail -s -o (Join-Path $root "data\earth\$t.tif") "https://copernicus-dem-90m.s3.amazonaws.com/$t/$t.tif"

Write-Host "Moon temperature (Diviner Polar Resource Products, about 605 MB) ..."
$dv = Join-Path $root "data\diviner"; New-Item -ItemType Directory -Force -Path $dv | Out-Null
$base = "https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/data_derived_prp"
curl.exe -L --fail -s -o (Join-Path $dv "dlre_prp_south.xml") "$base/dlre_prp_south.xml"
curl.exe -L --fail -C - -o (Join-Path $dv "dlre_prp_south.tab") "$base/dlre_prp_south.tab"
Write-Host "Done."
Get-ChildItem (Join-Path $root "data") -Recurse -File | Group-Object DirectoryName | ForEach-Object { "{0,-50} {1,3} files {2,8:N0} MB" -f (Split-Path $_.Name -Leaf), $_.Count, (($_.Group | Measure-Object Length -Sum).Sum/1MB) }
