-- Grant permissions for kanban_dev user
-- Run this as postgres superuser

-- Connect to the database
\c itit_kanban_dev

-- Grant schema permissions
GRANT ALL ON SCHEMA public TO kanban_dev;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO kanban_dev;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO kanban_dev;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO kanban_dev;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO kanban_dev;

-- Make kanban_dev the owner of the database (optional but recommended)
-- ALTER DATABASE itit_kanban_dev OWNER TO kanban_dev;

\echo '========================================='
\echo 'Permissions granted successfully!'
\echo '========================================='
\echo 'Now you can run the setup script again.'
\echo '========================================='













