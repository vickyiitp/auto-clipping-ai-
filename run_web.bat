@echo off
chcp 65001 >nul
title AutoClip Studio - Web Interface

echo ======================================================================
echo    🎬 AutoClip Studio - Web Interface
echo    Running locally at: http://localhost:5000
echo ======================================================================
echo.

cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found!
    echo Please make sure the venv folder exists.
    pause
    exit /b 1
)

echo Starting AutoClip Studio Web App...
start "" "http://localhost:5000"
venv\Scripts\python.exe app.py
pause
