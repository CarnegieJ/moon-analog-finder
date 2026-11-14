@echo off
rem One-step publish to GitHub. Usage:  scripts\push_github.bat https://github.com/USERNAME/REPO.git
rem Uses your own Git sign-in on this computer. The .env file and the data folder are never included.
if "%~1"=="" (echo Usage: scripts\push_github.bat https://github.com/USERNAME/REPO.git & exit /b 1)
cd /d "%~dp0.."
if not exist .git git init
git add .
echo.
echo ---- Files that will be published (check that .env and data/ are NOT here) ----
git status --short | findstr /v /c:"app/data" /c:"app/layers"
echo ---------------------------------------------------------------------------
git ls-files --error-unmatch .env >nul 2>&1 && (echo STOP: .env is tracked. Not pushing. & exit /b 1)
pause
git commit -m "Moon Analog Finder: pipeline, app and docs"
git branch -M main
git remote remove origin >nul 2>&1
git remote add origin %1
git push -u origin main
