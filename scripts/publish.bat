@echo off
rem Commit all changes and push to GitHub.
rem Usage:  scripts\publish.bat "short description of the change"
cd /d "%~dp0.."
git add .
git ls-files --error-unmatch .env >nul 2>&1 && (echo STOP: .env is tracked. Not pushing. & exit /b 1)
git commit -m "%~1"
git push
