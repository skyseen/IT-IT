# Kanban Feature Setup Guide

This guide will walk you through setting up the Kanban feature for the IT!IT OA Tool.

## Prerequisites

1. **PostgreSQL 15+** installed on your local machine
2. **Python 3.8+** with all dependencies installed
3. **pgAdmin** or **psql** for database management (optional but recommended)

## Step 1: Install PostgreSQL

### Windows Installation

1. Download PostgreSQL installer from [postgresql.org](https://www.postgresql.org/download/windows/)
2. Run the installer and follow the wizard:
   - Use default port: `5432`
   - Set a password for the `postgres` superuser (remember this!)
   - Install pgAdmin 4 (recommended)
3. Verify installation by opening Command Prompt:
   ```cmd
   psql --version
   ```

## Step 2: Create Development Database

Open **pgAdmin** or **psql** and run:

```sql
-- Create database
CREATE DATABASE itit_kanban_dev;

-- Create user
CREATE USER kanban_dev WITH PASSWORD 'DevPassword123!';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE itit_kanban_dev TO kanban_dev;
```

Or using psql command line:

```cmd
psql -U postgres
```

Then paste the SQL commands above.

## Step 3: Install Python Dependencies

Open Command Prompt in the project root and run:

```cmd
pip install -r requirements.txt
```

This will install:
- `psycopg2-binary` - PostgreSQL adapter
- `SQLAlchemy` - ORM
- `python-dateutil` - Date utilities

## Step 4: Verify Database Configuration

Check that `config/kanban_config.json` has the correct settings:

```json
{
  "environment": "development",
  "database": {
    "host": "localhost",
    "port": 5432,
    "database": "itit_kanban_dev",
    "username": "kanban_dev",
    "password": "DevPassword123!",
    "pool_size": 5,
    "max_overflow": 3
  }
}
```

**⚠️ Important:** If you changed the database password, update it in this file.

## Step 5: Initialize Database Schema

Run the schema setup script:

```cmd
psql -h localhost -U kanban_dev -d itit_kanban_dev -f scripts/setup_kanban_db.sql
```

You'll be prompted for the password: `DevPassword123!`

You should see:
```
CREATE TABLE
CREATE INDEX
...
Kanban Database Schema Setup Complete!
```

## Step 6: Seed Initial Data

Run the seed script to populate test users, columns, and sample tasks:

```cmd
python scripts/seed_kanban_data.py
```

Expected output:
```
============================================================
Kanban Database Seed Script
============================================================

✓ Database connection successful!

Creating test users...
  ✓ Created user: Kenyi Seen (ID: 1)
  ✓ Created user: Alex Ng (ID: 2)
  ...

Creating Kanban columns...
  ✓ Created column: Backlog (ID: 1)
  ✓ Created column: To Do (ID: 2)
  ...

Creating 30 sample tasks...
  ✓ Created 30 tasks successfully!

============================================================
✅ Seed completed successfully!
============================================================
```

## Step 7: Test Backend

Verify everything is working:

```cmd
python scripts/test_kanban_backend.py
```

Expected output:
```
============================================================
Kanban Backend Test Suite
============================================================

Test 1: Database Connection
----------------------------------------
✅ Connection successful!
   Pool size: 5
   Checked out: 0

...

============================================================
Test Summary
============================================================
✅ PASS - Users
✅ PASS - Columns
✅ PASS - Task CRUD
✅ PASS - Task Movement
✅ PASS - Comments
✅ PASS - Statistics

Total: 6/6 tests passed

🎉 All tests passed! Backend is working correctly.
```

## Step 8: Launch Application

Start the IT!IT tool:

```cmd
python app.py
```

You should now see the **📋 Kanban** tab in the application!

## Troubleshooting

### Problem: "psql is not recognized"

**Solution:** Add PostgreSQL bin directory to your PATH:
1. Find PostgreSQL installation directory (usually `C:\Program Files\PostgreSQL\15\bin`)
2. Add it to your system PATH environment variable
3. Restart Command Prompt

### Problem: "connection refused"

**Solution:**
1. Check if PostgreSQL service is running:
   - Open Services (services.msc)
   - Find "postgresql-x64-15" (or similar)
   - Start the service if stopped
2. Verify connection settings in `config/kanban_config.json`

### Problem: "FATAL: password authentication failed"

**Solution:**
1. Verify password in `config/kanban_config.json` matches what you set
2. Try resetting the user password:
   ```sql
   ALTER USER kanban_dev WITH PASSWORD 'DevPassword123!';
   ```

### Problem: "No module named 'psycopg2'"

**Solution:**
```cmd
pip install psycopg2-binary
```

### Problem: Kanban tab not showing in app

**Solution:**
1. Check for errors in Command Prompt when launching app
2. Verify all Kanban files are in `kanban/` directory
3. Check that database connection is successful

## Next Steps

### Using the Kanban Board

1. **Create Tasks:** Click "➕ New Task" button
2. **View Tasks:** Click on any task card to view/edit details
3. **Filter Tasks:** Use the search bar and filter dropdowns
4. **Assign Tasks:** Edit task and select assignee
5. **Add Comments:** Open task details and use Comments tab

### Backup (Optional)

Set up automated backups:

```cmd
python scripts/backup_kanban.py
```

To schedule daily backups, use Windows Task Scheduler:
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger to Daily at 2:00 AM
4. Set action to run: `python C:\path\to\IT-IT\scripts\backup_kanban.py`

## Production Migration (Future)

When you're ready to deploy to production:

1. Coordinate with IT department for PostgreSQL server
2. Create production database
3. Run migration script (see `KANBAN_PLAN.md` Week 10)
4. Update connection config
5. Deploy to all users

## Getting Help

If you encounter issues:

1. Check the logs in `logs/activity_log.jsonl`
2. Verify PostgreSQL logs (in PostgreSQL data directory)
3. Run test script to identify specific failures
4. Review error messages in Command Prompt

## Configuration Reference

### Database Settings (`config/kanban_config.json`)

- `host`: PostgreSQL server address (localhost for development)
- `port`: PostgreSQL port (default 5432)
- `database`: Database name
- `username`: Database user
- `password`: Database password
- `pool_size`: Number of connections in pool (5 for dev, 10 for prod)
- `max_overflow`: Additional connections during bursts

### Kanban Settings (`it_tool_config.json`)

Kanban settings are stored in your existing IT!IT config under the `kanban` section:

```json
{
  "kanban": {
    "enabled": true,
    "features": {
      "auto_create_tasks": true,
      "workflow_integration": {
        "sap_creation": true,
        "agile_creation": true,
        ...
      }
    },
    "default_columns": [...]
  }
}
```

These can be modified through the Settings dialog (future feature).

## FAQ

**Q: Can I use a different database password?**  
A: Yes, just update it in both PostgreSQL and `config/kanban_config.json`

**Q: Do I need to run seed script every time?**  
A: No, only once initially. It will skip existing data on re-runs.

**Q: Can multiple people use the same local database?**  
A: Not recommended for development. Each developer should have their own local database.

**Q: How do I reset the database?**  
A: Drop and recreate the database, then re-run setup and seed scripts.

**Q: Where are attachments stored?**  
A: In `kanban_attachments/` folder (automatically created)

**Q: How do I update the schema later?**  
A: Run any new migration SQL scripts provided, or manually add columns/tables.

---

**Congratulations!** Your Kanban feature is now set up and ready to use! 🎉


