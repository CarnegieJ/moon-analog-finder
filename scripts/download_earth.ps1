# Downloads Copernicus DEM GLO-90 tiles (ESA, open data on AWS) for the starter Earth sites into data\earth.
# Run from the project folder:  powershell -ExecutionPolicy Bypass -File .\scripts\download_earth.ps1
$dest = Join-Path $PSScriptRoot "..\data\earth"
New-Item -ItemType Directory -Force -Path $dest | Out-Null
$files = @(
  "https://copernicus-dem-90m.s3.amazonaws.com/Copernicus_DSM_COG_30_N19_00_E018_00_DEM/Copernicus_DSM_COG_30_N19_00_E018_00_DEM.tif",
  "https://copernicus-dem-90m.s3.amazonaws.com/Copernicus_DSM_COG_30_N19_00_W156_00_DEM/Copernicus_DSM_COG_30_N19_00_W156_00_DEM.tif",
  "https://copernicus-dem-90m.s3.amazonaws.com/Copernicus_DSM_COG_30_N28_00_W017_00_DEM/Copernicus_DSM_COG_30_N28_00_W017_00_DEM.tif",
  "https://copernicus-dem-90m.s3.amazonaws.com/Copernicus_DSM_COG_30_N34_00_W111_00_DEM/Copernicus_DSM_COG_30_N34_00_W111_00_DEM.tif",
  "https://copernicus-dem-90m.s3.amazonaws.com/Copernicus_DSM_COG_30_N34_00_W112_00_DEM/Copernicus_DSM_COG_30_N34_00_W112_00_DEM.tif",
  "https://copernicus-dem-90m.s3.amazonaws.com/Copernicus_DSM_COG_30_N35_00_W111_00_DEM/Copernicus_DSM_COG_30_N35_00_W111_00_DEM.tif",
  "https://copernicus-dem-90m.s3.amazonaws.com/Copernicus_DSM_COG_30_N35_00_W112_00_DEM/Copernicus_DSM_COG_30_N35_00_W112_00_DEM.tif",
  "https://copernicus-dem-90m.s3.amazonaws.com/Copernicus_DSM_COG_30_N38_00_W080_00_DEM/Copernicus_DSM_COG_30_N38_00_W080_00_DEM.tif",
  "https://copernicus-dem-90m.s3.amazonaws.com/Copernicus_DSM_COG_30_N38_00_W081_00_DEM/Copernicus_DSM_COG_30_N38_00_W081_00_DEM.tif",
  "https://copernicus-dem-90m.s3.amazonaws.com/Copernicus_DSM_COG_30_N41_00_W094_00_DEM/Copernicus_DSM_COG_30_N41_00_W094_00_DEM.tif",
  "https://copernicus-dem-90m.s3.amazonaws.com/Copernicus_DSM_COG_30_N42_00_W094_00_DEM/Copernicus_DSM_COG_30_N42_00_W094_00_DEM.tif",
  "https://copernicus-dem-90m.s3.amazonaws.com/Copernicus_DSM_COG_30_N43_00_W114_00_DEM/Copernicus_DSM_COG_30_N43_00_W114_00_DEM.tif",
  "https://copernicus-dem-90m.s3.amazonaws.com/Copernicus_DSM_COG_30_N64_00_W017_00_DEM/Copernicus_DSM_COG_30_N64_00_W017_00_DEM.tif",
  "https://copernicus-dem-90m.s3.amazonaws.com/Copernicus_DSM_COG_30_N65_00_W017_00_DEM/Copernicus_DSM_COG_30_N65_00_W017_00_DEM.tif",
  "https://copernicus-dem-90m.s3.amazonaws.com/Copernicus_DSM_COG_30_N75_00_W090_00_DEM/Copernicus_DSM_COG_30_N75_00_W090_00_DEM.tif",
  "https://copernicus-dem-90m.s3.amazonaws.com/Copernicus_DSM_COG_30_N79_00_E012_00_DEM/Copernicus_DSM_COG_30_N79_00_E012_00_DEM.tif",
  "https://copernicus-dem-90m.s3.amazonaws.com/Copernicus_DSM_COG_30_N79_00_E013_00_DEM/Copernicus_DSM_COG_30_N79_00_E013_00_DEM.tif",
  "https://copernicus-dem-90m.s3.amazonaws.com/Copernicus_DSM_COG_30_N82_00_W031_00_DEM/Copernicus_DSM_COG_30_N82_00_W031_00_DEM.tif",
  "https://copernicus-dem-90m.s3.amazonaws.com/Copernicus_DSM_COG_30_N82_00_W032_00_DEM/Copernicus_DSM_COG_30_N82_00_W032_00_DEM.tif",
  "https://copernicus-dem-90m.s3.amazonaws.com/Copernicus_DSM_COG_30_S03_00_W061_00_DEM/Copernicus_DSM_COG_30_S03_00_W061_00_DEM.tif",
  "https://copernicus-dem-90m.s3.amazonaws.com/Copernicus_DSM_COG_30_S04_00_W061_00_DEM/Copernicus_DSM_COG_30_S04_00_W061_00_DEM.tif",
  "https://copernicus-dem-90m.s3.amazonaws.com/Copernicus_DSM_COG_30_S24_00_W070_00_DEM/Copernicus_DSM_COG_30_S24_00_W070_00_DEM.tif",
  "https://copernicus-dem-90m.s3.amazonaws.com/Copernicus_DSM_COG_30_S24_00_W071_00_DEM/Copernicus_DSM_COG_30_S24_00_W071_00_DEM.tif",
  "https://copernicus-dem-90m.s3.amazonaws.com/Copernicus_DSM_COG_30_S25_00_W070_00_DEM/Copernicus_DSM_COG_30_S25_00_W070_00_DEM.tif",
  "https://copernicus-dem-90m.s3.amazonaws.com/Copernicus_DSM_COG_30_S25_00_W071_00_DEM/Copernicus_DSM_COG_30_S25_00_W071_00_DEM.tif",
  "https://copernicus-dem-90m.s3.amazonaws.com/Copernicus_DSM_COG_30_S78_00_E162_00_DEM/Copernicus_DSM_COG_30_S78_00_E162_00_DEM.tif",
  "https://copernicus-dem-90m.s3.amazonaws.com/Copernicus_DSM_COG_30_S78_00_E163_00_DEM/Copernicus_DSM_COG_30_S78_00_E163_00_DEM.tif"
)
$fail = @()
foreach ($u in $files) {
  $name = Split-Path $u -Leaf
  $out = Join-Path $dest $name
  if ((Test-Path $out) -and ((Get-Item $out).Length -gt 10000)) { continue }
  curl.exe -L --fail -s -o $out $u
  if ($LASTEXITCODE -ne 0) { $fail += $name; Remove-Item $out -ErrorAction SilentlyContinue }
}
Write-Host ("Downloaded: " + (Get-ChildItem $dest -Filter *.tif).Count + " of " + $files.Count + " tiles")
if ($fail.Count) { Write-Host "FAILED:" -ForegroundColor Red; $fail | ForEach-Object { Write-Host "  $_" } }
