# Database Setup Instructions

## Before Running Any Scripts

You **MUST** set up the PostgreSQL database first. This is a one-time setup.

## Option 1: Using pgAdmin (Recommended - Visual)

1. **Open pgAdmin 4**
   - Start Menu → PostgreSQL 15 → pgAdmin 4

2. **Connect to PostgreSQL**
   - Expand Servers
   - Right-click "PostgreSQL 15"
   - Enter the password you set during installation

3. **Create Database**
   - Right-click "Databases"
   - Select "Create" → "Database..."
   - Database name: `itit_kanban_dev`
   - Owner: `postgres`
   - Click "Save"

4. **Create User**
   - Expand "PostgreSQL 15"
   - Right-click "Login/Group Roles"
   - Select "Create" → "Login/Group Role..."
   - **General tab**:
     - Name: `kanban_dev`
   - **Definition tab**:
     - Password: `DevPassword123!`
     - Check "Password expires" and set to "infinity" (never)
   - **Privileges tab**:
     - Check "Can login?"
   - Click "Save"

5. **Grant Privileges**
   - Right-click "itit_kanban_dev" database
   - Select "Query Tool"
   - Paste this SQL:
     ```sql
     GRANT ALL PRIVILEGES ON DATABASE itit_kanban_dev TO kanban_dev;
     ```
   - Press F5 or click Execute button

## Option 2: Using psql (Command Line)

1. **Open Command Prompt**

2. **Connect to PostgreSQL**
   ```cmd
   psql -U postgres
   ```
   Enter the postgres password when prompted.

3. **Run Setup SQL**
   ```sql
   CREATE DATABASE itit_kanban_dev;
   CREATE USER kanban_dev WITH PASSWORD 'DevPassword123!';
   GRANT ALL PRIVILEGES ON DATABASE itit_kanban_dev TO kanban_dev;
   \q
   ```

## Verify Setup

Test the connection:

```cmd
psql -h localhost -U kanban_dev -d itit_kanban_dev
```

Password: `DevPassword123!`

If you see:
```
itit_kanban_dev=>
```

**Success!** You're connected. Type `\q` to exit.

## If You Get Errors

### "psql is not recognized"

Add PostgreSQL to your PATH:
1. Open System Environment Variables
2. Edit PATH variable
3. Add: `C:\Program Files\PostgreSQL\15\bin`
4. Restart Command Prompt

### "connection refused"

1. Open Services (Press Win+R, type `services.msc`)
2. Find "postgresql-x64-15" (or similar)
3. Right-click → Start

### "password authentication failed"

Re-create the user with correct password:
```sql
psql -U postgres
DROP USER IF EXISTS kanban_dev;
CREATE USER kanban_dev WITH PASSWORD 'DevPassword123!';
\q
```

## Custom Password

If you want a different password:

1. Change it when creating the user:
   ```sql
   CREATE USER kanban_dev WITH PASSWORD 'YourPasswordHere';
   ```

2. Update `config/kanban_config.json`:
   ```json
   {
     "database": {
       "password": "YourPasswordHere"
     }
   }
   ```

## Next Steps

After database setup is complete, run:

```cmd
SETUP_KANBAN.bat
```

Or follow manual steps in `KANBAN_QUICKSTART.md`

## Need Help?

See `docs/KANBAN_SETUP.md` for detailed troubleshooting.













