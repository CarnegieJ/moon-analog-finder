@echo off
rem Serves the workspace at http://localhost:8765 and opens it in your browser.
cd /d "%~dp0..\workspace"
start "" http://localhost:8765
python -m http.server 8765
