# Kanban Feature - Quick Start Guide

## ⚡ 5-Minute Setup

### Step 1: Install PostgreSQL

Download and install PostgreSQL 15+ from [postgresql.org](https://www.postgresql.org/download/windows/)

**Important**: Remember the password you set for the `postgres` user!

### Step 2: Create Database

Open **pgAdmin** (or **psql**) and run:

```sql
CREATE DATABASE itit_kanban_dev;
CREATE USER kanban_dev WITH PASSWORD 'DevPassword123!';
GRANT ALL PRIVILEGES ON DATABASE itit_kanban_dev TO kanban_dev;
```

Or use psql command line:
```cmd
psql -U postgres
```
Then paste the SQL above.

### Step 3: Install Python Dependencies

```cmd
cd C:\Users\Kenyi.Seen\Documents\GitHub\IT-IT
pip install -r requirements.txt
```

### Step 4: Initialize Database Schema

```cmd
psql -h localhost -U kanban_dev -d itit_kanban_dev -f scripts/setup_kanban_db.sql
```

Password: `DevPassword123!`

### Step 5: Seed Test Data

```cmd
python scripts/seed_kanban_data.py
```

You should see:
```
✅ Seed completed successfully!
```

### Step 6: Test Backend (Optional)

```cmd
python scripts/test_kanban_backend.py
```

Expected: `🎉 All tests passed! Backend is working correctly.`

### Step 7: Launch Application

```cmd
python app.py
```

**Done!** Click the **📋 Kanban** tab in the application.

## 🎯 Using Kanban

### Create a Task
1. Click **➕ New Task** button
2. Fill in title (required)
3. Select column, assignee, priority
4. Click **Create Task**

### View/Edit a Task
1. Click on any task card
2. Edit fields in the Details tab
3. Add comments in the Comments tab
4. Click **Save Changes**

### Filter Tasks
- Use the **🔍 Search** box to find tasks by title/description
- Select **👤 All Users** dropdown to filter by assignee
- Select **🎯 All Priorities** to filter by priority

### Refresh Board
Click **🔄 Refresh** to reload all tasks from database

## 🔧 Troubleshooting

### "psql is not recognized"

Add PostgreSQL to PATH:
```
C:\Program Files\PostgreSQL\15\bin
```

### "connection refused"

1. Check PostgreSQL service is running (services.msc)
2. Verify `config/kanban_config.json` settings

### "password authentication failed"

Update password in `config/kanban_config.json`

### Kanban tab not showing

1. Check for errors in terminal when launching app
2. Verify PostgreSQL is running and database exists
3. Run `python scripts/test_kanban_backend.py` to diagnose

## 📚 More Information

- **Detailed Setup**: See `docs/KANBAN_SETUP.md`
- **Implementation Status**: See `KANBAN_IMPLEMENTATION_STATUS.md`
- **Full Plan**: See `kanban-feature-implementation.plan.md`

## ✅ What Works Now

- ✅ Create, edit, delete tasks
- ✅ Assign tasks to users
- ✅ Set priority, deadline, category
- ✅ Add comments
- ✅ Search and filter
- ✅ View task statistics
- ✅ Complete audit logging

## 🚀 Coming Soon (Optional)

- Drag-and-drop between columns
- File attachments upload/download
- My Tasks personal view
- Reports and metrics dashboard
- Workflow auto-task creation
- Auto-refresh

---

**Need Help?** Check `docs/KANBAN_SETUP.md` for detailed troubleshooting.













