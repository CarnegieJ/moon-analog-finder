# Stage 2 lunar data: LOLA south pole elevation at 20 m per pixel (about 2.6 GB), NASA PGDA product 90.
# Run from the project folder:  powershell -ExecutionPolicy Bypass -File .\scripts\download_moon20.ps1
# Safe to re-run: a partial file resumes.
$dest = Join-Path $PSScriptRoot "..\data\moon"
New-Item -ItemType Directory -Force -Path $dest | Out-Null
$u = "https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LDEM_80S_20MPP_ADJ.TIF"
$out = Join-Path $dest "LDEM_80S_20MPP_ADJ.TIF"
curl.exe -L --fail -C - -o $out $u
if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne 33) { Write-Host "FAILED (curl exit $LASTEXITCODE). If this is a 404, the file name differs; open https://pgda.gsfc.nasa.gov/products/90 and tell Claude the name of the 20 m 80S elevation file." -ForegroundColor Red }
Get-Item $out | Format-Table Name, @{n="GB";e={[math]::Round($_.Length/1GB,2)}}
