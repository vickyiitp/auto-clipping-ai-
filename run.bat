@echo off
chcp 65001 >nul
title Auto Clipping - YouTube to Vertical Shorts

echo ======================================================================
echo    AUTO CLIPPING - YouTube to Vertical Shorts Pipeline
echo    100%% Local - Zero Paid APIs - Open Source
echo ======================================================================
echo.

cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found!
    echo Please make sure the venv folder exists.
    pause
    exit /b 1
)

if "%~1"=="" (
    set /p YOUTUBE_URL="🔗 Enter or paste YouTube URL: "
) else (
    set YOUTUBE_URL=%~1
)

if "%YOUTUBE_URL%"=="" (
    echo [ERROR] No URL entered. Exiting.
    pause
    exit /b 1
)

echo.
echo Running pipeline...
echo.
venv\Scripts\python.exe main.py "%YOUTUBE_URL%"

echo.
echo ======================================================================
echo Execution finished. Check the 'output' folder for generated Shorts.
echo ======================================================================
pause
