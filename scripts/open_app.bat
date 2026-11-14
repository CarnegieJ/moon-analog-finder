@echo off
rem Serves the Moon Analog Finder at http://localhost:8766 and opens it in your browser.
cd /d "%~dp0..\app"
start "" http://localhost:8766
python -m http.server 8766
