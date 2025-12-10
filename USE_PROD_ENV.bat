@echo off
echo ============================================
echo Switching to PRODUCTION Environment
echo ============================================
echo.
echo ⚠️  WARNING: You are switching to PRODUCTION!
echo    All changes will affect the live system.
echo.
set /p confirm="Are you sure? (Y/N): "
if /i not "%confirm%"=="Y" (
    echo Cancelled.
    pause
    exit /b 0
)

if not exist "config\kanban_config.prod.json" (
    echo ERROR: config\kanban_config.prod.json not found!
    echo Please create this file first with PRODUCTION database settings.
    pause
    exit /b 1
)

copy /Y "config\kanban_config.prod.json" "config\kanban_config.json"

echo.
echo ✓ Done! Now using PRODUCTION database.
echo.
echo Database: itit_kanban_prod
echo.
pause





