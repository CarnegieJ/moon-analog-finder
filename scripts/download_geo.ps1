# Global Permafrost Zonation Index (Gruber 2012, The Cryosphere 6, 221-233). 30 arc-second grid, 60 S to 90 N. About 3.1 GB.
# Safe to re-run: an interrupted download resumes where it stopped.
$dir = Join-Path $PSScriptRoot "..\data\geo"
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$base = "https://microsite.geo.uzh.ch/cryodata/pf_global"
foreach ($f in "PZI.hdr", "README.txt", "PZI.flt") {
  Write-Host "Downloading $f"
  curl.exe -L -C - --retry 5 -o (Join-Path $dir $f) "$base/$f"
}
Get-ChildItem $dir | Format-Table Name, Length
Write-Host "Done. PZI.flt should be 3110400000 bytes."
