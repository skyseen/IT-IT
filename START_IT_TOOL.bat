@echo off
title IT-IT Automation Tool
cd /d "%~dp0"
echo Starting IT-IT Automation Tool...
python app.py
if errorlevel 1 (
    echo.
    echo ERROR: Failed to start the application.
    echo Please make sure Python and all dependencies are installed.
    echo.
    pause
)


