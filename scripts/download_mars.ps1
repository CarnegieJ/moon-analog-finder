# Mars global elevation: MGS MOLA DEM, 463 m per pixel, about 2 GB, public domain (USGS Astrogeology).
# Run from the project folder:  powershell -ExecutionPolicy Bypass -File .\scripts\download_mars.ps1
# Safe to re-run: a partial file resumes.
$dest = Join-Path $PSScriptRoot "..\data\mars"
New-Item -ItemType Directory -Force -Path $dest | Out-Null
$out = Join-Path $dest "Mars_MGS_MOLA_DEM_mosaic_global_463m.tif"
curl.exe -L --fail -C - -o $out "https://planetarymaps.usgs.gov/mosaic/Mars_MGS_MOLA_DEM_mosaic_global_463m.tif"
Get-Item $out | Format-Table Name, @{n="GB";e={[math]::Round($_.Length/1GB,2)}}
