@echo off
echo ============================================================
echo Kanban Feature Setup Script
echo ============================================================
echo.
echo This script will:
echo 1. Install Python dependencies
echo 2. Initialize database schema
echo 3. Seed test data
echo 4. Run backend tests
echo.
echo Prerequisites:
echo - PostgreSQL installed and running
echo - Database 'itit_kanban_dev' created
echo - User 'kanban_dev' created with password 'DevPassword123!'
echo.
pause

echo.
echo ============================================================
echo Step 1: Installing Python dependencies...
echo ============================================================
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install dependencies!
    pause
    exit /b 1
)
echo.
echo Dependencies installed successfully!

echo.
echo ============================================================
echo Step 2: Initializing database schema...
echo ============================================================
echo Note: You will be prompted for the database password.
echo Password: DevPassword123!
echo.
psql -h localhost -U kanban_dev -d itit_kanban_dev -f scripts/setup_kanban_db.sql
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to initialize database schema!
    echo.
    echo Troubleshooting:
    echo 1. Ensure PostgreSQL is running
    echo 2. Verify database 'itit_kanban_dev' exists
    echo 3. Verify user 'kanban_dev' exists with correct password
    echo 4. Check if psql is in your PATH
    pause
    exit /b 1
)
echo.
echo Database schema created successfully!

echo.
echo ============================================================
echo Step 3: Seeding test data...
echo ============================================================
python scripts/seed_kanban_data.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to seed test data!
    pause
    exit /b 1
)
echo.
echo Test data seeded successfully!

echo.
echo ============================================================
echo Step 4: Running backend tests...
echo ============================================================
python scripts/test_kanban_backend.py
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Some backend tests failed!
    echo You may still be able to use Kanban, but some features might not work.
)

echo.
echo ============================================================
echo Setup Complete!
echo ============================================================
echo.
echo The Kanban feature is now ready to use.
echo.
echo To launch the application, run:
echo     START_IT_TOOL.bat
echo.
echo Or:
echo     python app.py
echo.
echo The Kanban tab should appear in the application.
echo.
echo For troubleshooting, see:
echo - docs\KANBAN_SETUP.md
echo - KANBAN_QUICKSTART.md
echo.
pause


