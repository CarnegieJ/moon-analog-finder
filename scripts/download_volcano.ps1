# NOAA NCEI Global Volcano Locations Database (US government; locations originate from the Smithsonian Global Volcanism Program).
# Saves every page of the public API as JSON in data\geo\volcano\.
$dir = Join-Path $PSScriptRoot "..\data\geo\volcano"
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$base = "https://www.ngdc.noaa.gov/hazel/hazard-service/api/v1/volcanolocs"
$page = 1
do {
  $out = Join-Path $dir ("volcanolocs_{0}.json" -f $page)
  curl.exe -s -L --retry 3 -o $out "$base`?page=$page&itemsPerPage=200"
  $j = Get-Content $out -Raw | ConvertFrom-Json
  Write-Host ("page {0} of {1}: {2} volcanoes" -f $page, $j.totalPages, $j.items.Count)
  $page++
} while ($page -le $j.totalPages)
Get-ChildItem $dir | Format-Table Name, Length
