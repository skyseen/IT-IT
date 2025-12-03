@echo off
echo ============================================
echo Switching to TEST Environment
echo ============================================
echo.

if not exist "config\kanban_config.test.json" (
    echo ERROR: config\kanban_config.test.json not found!
    echo Please create this file first with TEST database settings.
    pause
    exit /b 1
)

copy /Y "config\kanban_config.test.json" "config\kanban_config.json"

echo.
echo ✓ Done! Now using TEST database.
echo.
echo Database: itit_kanban_test
echo.
pause


