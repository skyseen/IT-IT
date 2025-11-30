@echo off
echo ============================================================
echo Kanban Database - Fix Permissions
echo ============================================================
echo.
echo This script will grant the necessary permissions to kanban_dev user.
echo.
echo You will be prompted for the PostgreSQL superuser (postgres) password.
echo.
pause

echo.
echo Granting permissions...
psql -U postgres -d itit_kanban_dev -f scripts/grant_permissions.sql

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Failed to grant permissions!
    echo.
    echo Troubleshooting:
    echo 1. Make sure you entered the correct postgres password
    echo 2. Ensure PostgreSQL is running
    echo 3. Try running this command manually:
    echo    psql -U postgres -d itit_kanban_dev -f scripts/grant_permissions.sql
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Permissions granted successfully!
echo ============================================================
echo.
echo Now you can run SETUP_KANBAN.bat again.
echo.
pause













