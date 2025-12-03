@echo off
echo ============================================
echo IT!IT Kanban - Quick Setup Script
echo ============================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed!
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo [1/4] Python found:
python --version

echo.
echo [2/4] Installing dependencies...
echo This may take a few minutes...
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ERROR: Failed to install dependencies!
    echo Please check your internet connection and try again.
    pause
    exit /b 1
)

echo.
echo [3/4] Checking config file...
if not exist "config\kanban_config.json" (
    echo.
    echo ⚠️  WARNING: config\kanban_config.json not found!
    echo.
    echo Please do one of the following:
    echo   1. Get the config file from your admin ^(Kenyi^)
    echo   2. Copy the template: copy config\kanban_config.prod.json config\kanban_config.json
    echo   3. Create the file manually with correct database settings
    echo.
    pause
    exit /b 1
)

echo ✓ Config file found!

echo.
echo [4/4] Testing database connection...
python scripts/test_kanban_backend.py

if errorlevel 1 (
    echo.
    echo ⚠️  Database connection test had issues.
    echo Please verify your config/kanban_config.json settings.
    pause
    exit /b 1
)

echo.
echo ============================================
echo ✅ Setup complete!
echo ============================================
echo.
echo Next steps:
echo   1. Run START_IT_TOOL.bat to launch the application
echo   2. Login with your username
echo   3. Initial password: ChangeMe123!
echo   4. Change your password on first login
echo.
pause


