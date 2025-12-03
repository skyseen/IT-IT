# IT!IT Kanban Deployment Guide

Complete guide for deploying the IT!IT Kanban system from localhost to company server with Test and Production environments.

---

## Table of Contents

1. [Overview](#overview)
2. [Environment Strategy](#environment-strategy)
3. [Database Setup on Company Server](#database-setup-on-company-server)
4. [Data Migration Strategy](#data-migration-strategy)
5. [Configuration Management](#configuration-management)
6. [IT Team Deployment Steps](#it-team-deployment-steps)
7. [Professional Deployment Workflow](#professional-deployment-workflow)
8. [Rollback Procedures](#rollback-procedures)
9. [Checklist](#checklist)

---

## Overview

### Current Setup
- **Database**: PostgreSQL on localhost
- **Config File**: `config/kanban_config.json`
- **Application**: Python desktop app using PySide6

### Target Setup
- **Test Environment (UAT)**: PostgreSQL on company server VM
- **Production Environment**: PostgreSQL on company server VM (separate database)
- **Application**: Deployed to IT team workstations via GitHub clone

---

## Environment Strategy

### Why Two Environments?

| Environment | Purpose | Who Uses It |
|-------------|---------|-------------|
| **TEST (UAT)** | Testing new features, bug fixes, training | IT Team (testers) |
| **PRODUCTION** | Live system with real data | All IT Team members |

### Recommended Approach

```
┌─────────────────────────────────────────────────────────────────┐
│                    COMPANY SERVER (VM)                          │
│                                                                 │
│  ┌─────────────────────┐     ┌─────────────────────┐           │
│  │   TEST DATABASE     │     │   PROD DATABASE     │           │
│  │  itit_kanban_test   │     │  itit_kanban_prod   │           │
│  │  Port: 5432         │     │  Port: 5432         │           │
│  │  User: kanban_test  │     │  User: kanban_prod  │           │
│  └─────────────────────┘     └─────────────────────┘           │
│                                                                 │
│  IP: xxx.xxx.xxx.xxx                                           │
└─────────────────────────────────────────────────────────────────┘
               │                          │
               ▼                          ▼
    ┌─────────────────────┐    ┌─────────────────────┐
    │  TEST Config File   │    │  PROD Config File   │
    │  kanban_config.json │    │  kanban_config.json │
    │  (on tester's PC)   │    │  (on all user PCs)  │
    └─────────────────────┘    └─────────────────────┘
```

---

## Database Setup on Company Server

### Prerequisites on Company Server

1. **PostgreSQL 15+** must be installed on the VM
2. **Network access** from user workstations to the VM (port 5432)
3. **Firewall rules** allowing PostgreSQL connections

### Step 1: Connect to Company Server

You need the following information from IT infrastructure team:

```
Server IP:       ___________________
PostgreSQL Port: 5432 (or custom)
Admin Username:  ___________________
Admin Password:  ___________________
```

### Step 2: Create Databases

Connect to the PostgreSQL server using pgAdmin or psql:

```bash
# From your workstation, connect to the server
psql -h <SERVER_IP> -U postgres -p 5432
```

Or use pgAdmin:
1. Open pgAdmin
2. Right-click "Servers" → "Register" → "Server..."
3. General tab: Name = "Company Server"
4. Connection tab:
   - Host: `<SERVER_IP>`
   - Port: `5432`
   - Username: `postgres` (or admin account)
   - Password: `<ADMIN_PASSWORD>`

### Step 3: Create TEST Environment Database

Run these SQL commands:

```sql
-- ============================================
-- TEST ENVIRONMENT DATABASE SETUP
-- ============================================

-- Create TEST database
CREATE DATABASE itit_kanban_test
    WITH OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TEMPLATE template0;

-- Create TEST user
CREATE USER kanban_test WITH PASSWORD 'TestPassword123!';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE itit_kanban_test TO kanban_test;

-- Connect to the test database and grant schema privileges
\c itit_kanban_test

GRANT ALL ON SCHEMA public TO kanban_test;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO kanban_test;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO kanban_test;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO kanban_test;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO kanban_test;
```

### Step 4: Create PRODUCTION Environment Database

```sql
-- ============================================
-- PRODUCTION ENVIRONMENT DATABASE SETUP
-- ============================================

-- Create PROD database
CREATE DATABASE itit_kanban_prod
    WITH OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TEMPLATE template0;

-- Create PROD user with stronger password
CREATE USER kanban_prod WITH PASSWORD 'ProdSecure456!@#';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE itit_kanban_prod TO kanban_prod;

-- Connect to the prod database and grant schema privileges
\c itit_kanban_prod

GRANT ALL ON SCHEMA public TO kanban_prod;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO kanban_prod;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO kanban_prod;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO kanban_prod;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO kanban_prod;
```

### Step 5: Initialize Database Schema

Run the schema setup script for each database:

```bash
# For TEST database
psql -h <SERVER_IP> -U kanban_test -d itit_kanban_test -f scripts/setup_kanban_db.sql

# For PRODUCTION database
psql -h <SERVER_IP> -U kanban_prod -d itit_kanban_prod -f scripts/setup_kanban_db.sql
```

### Step 5b: (If upgrading existing database) Run Migration

If you already ran `setup_kanban_db.sql` before and are getting errors about missing `kanban_groups` or `assigned_group_id`, run the migration script:

```bash
# For TEST database
psql -h <SERVER_IP> -U kanban_test -d itit_kanban_test -f scripts/migrate_add_groups.sql

# For PRODUCTION database  
psql -h <SERVER_IP> -U kanban_prod -d itit_kanban_prod -f scripts/migrate_add_groups.sql
```

This adds the group system tables without affecting existing data.

---

## Data Migration Strategy

### What Data Needs to Be Migrated?

| Data Type | Migrate to TEST? | Migrate to PROD? | Notes |
|-----------|------------------|------------------|-------|
| **Users (kanban_users)** | ✅ Yes | ✅ Yes | Real IT team members |
| **Columns (kanban_columns)** | ✅ Yes | ✅ Yes | Board structure |
| **Tasks (kanban_tasks)** | ⚠️ Sample only | ❌ No | Tasks created fresh in prod |
| **Activity Logs** | ❌ No | ❌ No | Start fresh |
| **Comments** | ❌ No | ❌ No | Start fresh |
| **Attachments** | ❌ No | ❌ No | Start fresh |

### Required User Data

You need to collect this information from your IT team:

| Field | Required? | Example |
|-------|-----------|---------|
| username | ✅ | `kenyi.seen` |
| display_name | ✅ | `Kenyi Seen` |
| email | ✅ | `kenyi.seen@ingrasys.com` |
| role | ✅ | `admin`, `member`, or `viewer` |
| department | Optional | `IT/OA` |
| avatar_color | Optional | `#F59E0B` |

### IT Team User List Template

Create a spreadsheet or collect this data:

```
╔══════════════════╦═══════════════════╦════════════════════════════════╦════════════╦═══════════╗
║ Username         ║ Display Name      ║ Email                          ║ Role       ║ Department║
╠══════════════════╬═══════════════════╬════════════════════════════════╬════════════╬═══════════╣
║ kenyi.seen       ║ Kenyi Seen        ║ kenyi.seen@ingrasys.com        ║ admin      ║ IT/OA     ║
║ alex.ng          ║ Alex Ng           ║ alex.ng@ingrasys.com           ║ member     ║ IT/OA     ║
║ oscar.loo        ║ Oscar Loo         ║ oscar.loo@ingrasys.com         ║ member     ║ IT/OA     ║
║ lingyun.niu      ║ Lingyun Niu       ║ lingyun.niu@foxconn.com.sg     ║ member     ║ IT/OA     ║
║ benni.tsao       ║ Benni Tsao        ║ benni.yh.tsao@ingrasys.com     ║ member     ║ IT/OA     ║
║ [add more...]    ║                   ║                                ║            ║           ║
╚══════════════════╩═══════════════════╩════════════════════════════════╩════════════╩═══════════╝
```

### Create Production Seed Script

Create a new file `scripts/seed_production_users.py`:

```python
"""Seed script for PRODUCTION - Only creates real users and columns (no sample tasks)."""

from __future__ import annotations

import sys
import io
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config_manager import get_kanban_config
from kanban.database import get_db_manager
from kanban.auth import ensure_password_initialized
from kanban.models import KanbanColumn, KanbanUser


def seed_production_users(session) -> dict[int, KanbanUser]:
    """Create REAL production users - UPDATE THIS LIST with your team!"""
    print("Creating production users...")
    
    # ============================================
    # UPDATE THIS LIST WITH YOUR REAL IT TEAM
    # ============================================
    users_data = [
        {
            "username": "kenyi.seen",
            "display_name": "Kenyi Seen",
            "email": "kenyi.seen@ingrasys.com",
            "role": "admin",
            "avatar_color": "#F59E0B",
            "department": "IT/OA",
        },
        {
            "username": "alex.ng",
            "display_name": "Alex Ng",
            "email": "alex.ng@ingrasys.com",
            "role": "member",
            "avatar_color": "#3B82F6",
            "department": "IT/OA",
        },
        {
            "username": "oscar.loo",
            "display_name": "Oscar Loo",
            "email": "oscar.loo@ingrasys.com",
            "role": "member",
            "avatar_color": "#10B981",
            "department": "IT/OA",
        },
        {
            "username": "lingyun.niu",
            "display_name": "Lingyun Niu",
            "email": "lingyun.niu@foxconn.com.sg",
            "role": "member",
            "avatar_color": "#8B5CF6",
            "department": "IT/OA",
        },
        {
            "username": "benni.tsao",
            "display_name": "Benni Tsao",
            "email": "benni.yh.tsao@ingrasys.com",
            "role": "member",
            "avatar_color": "#EC4899",
            "department": "IT/OA",
        },
        # ADD MORE TEAM MEMBERS HERE
        # {
        #     "username": "new.user",
        #     "display_name": "New User",
        #     "email": "new.user@company.com",
        #     "role": "member",
        #     "avatar_color": "#6366F1",
        #     "department": "IT/OA",
        # },
    ]
    
    user_dict = {}
    for user_data in users_data:
        existing = session.query(KanbanUser).filter_by(username=user_data["username"]).first()
        if existing:
            print(f"  ✓ User '{user_data['username']}' already exists (ID: {existing.id})")
            user_dict[existing.id] = existing
            continue
        
        user = KanbanUser(**user_data)
        session.add(user)
        session.flush()
        user_dict[user.id] = user
        print(f"  ✓ Created user: {user.display_name} (ID: {user.id})")
    
    session.commit()
    
    # Set initial passwords
    print("Setting initial passwords (ChangeMe123!)...")
    for user in user_dict.values():
        ensure_password_initialized(user, default_password="ChangeMe123!", db_manager=None)
    print("  ✓ Passwords initialized (users MUST change on first login)")
    
    return user_dict


def seed_columns(session) -> dict[str, KanbanColumn]:
    """Create Kanban columns."""
    print("Creating Kanban columns...")
    
    config = get_kanban_config()
    columns_config = config.get("default_columns", [])
    
    column_dict = {}
    for col_data in columns_config:
        existing = session.query(KanbanColumn).filter_by(name=col_data["name"], is_active=True).first()
        if existing:
            print(f"  ✓ Column '{col_data['name']}' already exists (ID: {existing.id})")
            column_dict[existing.name] = existing
            continue
        
        column = KanbanColumn(
            name=col_data["name"],
            position=col_data["position"],
            color=col_data["color"],
            wip_limit=col_data.get("wip_limit"),
        )
        session.add(column)
        session.flush()
        column_dict[column.name] = column
        print(f"  ✓ Created column: {column.name} (ID: {column.id})")
    
    session.commit()
    return column_dict


def main():
    """Main seed function for production."""
    print("=" * 60)
    print("PRODUCTION Kanban Database Seed Script")
    print("=" * 60)
    print()
    print("⚠️  This script creates REAL users only (NO sample tasks)")
    print()
    
    try:
        db = get_db_manager()
        
        if not db.test_connection():
            print("❌ Failed to connect to database!")
            print("Please check your config/kanban_config.json settings.")
            sys.exit(1)
        
        print("✓ Database connection successful!")
        print()
        
        session = db.get_session()
        
        try:
            users = seed_production_users(session)
            print()
            
            columns = seed_columns(session)
            print()
            
            print("=" * 60)
            print("✅ Production seed completed successfully!")
            print("=" * 60)
            print()
            print("Summary:")
            print(f"  - Users: {len(users)}")
            print(f"  - Columns: {len(columns)}")
            print(f"  - Tasks: 0 (created by team)")
            print()
            print("Next steps:")
            print("  1. Users login with initial password: ChangeMe123!")
            print("  2. Users must change password on first login")
            print("  3. Start creating real tasks!")
            
        finally:
            session.close()
            
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
```

---

## Configuration Management

### Configuration Files Structure

Create separate config files for each environment:

```
config/
├── kanban_config.json          # Current active config (gitignored)
├── kanban_config.dev.json      # Development (localhost)
├── kanban_config.test.json     # Test environment
└── kanban_config.prod.json     # Production environment
```

### Development Config (`config/kanban_config.dev.json`)

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

### Test Config (`config/kanban_config.test.json`)

```json
{
  "environment": "test",
  "database": {
    "host": "xxx.xxx.xxx.xxx",
    "port": 5432,
    "database": "itit_kanban_test",
    "username": "kanban_test",
    "password": "TestPassword123!",
    "pool_size": 5,
    "max_overflow": 3
  }
}
```

### Production Config (`config/kanban_config.prod.json`)

```json
{
  "environment": "production",
  "database": {
    "host": "xxx.xxx.xxx.xxx",
    "port": 5432,
    "database": "itit_kanban_prod",
    "username": "kanban_prod",
    "password": "ProdSecure456!@#",
    "pool_size": 10,
    "max_overflow": 5
  }
}
```

### Switching Between Environments

**Option A: Copy the right config file**

```batch
:: Switch to TEST environment
copy config\kanban_config.test.json config\kanban_config.json

:: Switch to PRODUCTION environment
copy config\kanban_config.prod.json config\kanban_config.json
```

**Option B: Create batch scripts**

Create `USE_TEST_ENV.bat`:
```batch
@echo off
echo Switching to TEST environment...
copy /Y config\kanban_config.test.json config\kanban_config.json
echo Done! Now using TEST database.
pause
```

Create `USE_PROD_ENV.bat`:
```batch
@echo off
echo Switching to PRODUCTION environment...
copy /Y config\kanban_config.prod.json config\kanban_config.json
echo Done! Now using PRODUCTION database.
pause
```

### Git Ignore Active Config

Add to `.gitignore`:

```gitignore
# Active config (contains passwords)
config/kanban_config.json

# Keep template configs in git
!config/kanban_config.*.json
```

---

## IT Team Deployment Steps

### For IT Team Members (End Users)

#### Prerequisites

Each team member's workstation needs:

| Software | Version | Download Link |
|----------|---------|---------------|
| Python | 3.8+ | https://www.python.org/downloads/ |
| Git | Any | https://git-scm.com/download/win |

#### Step-by-Step Setup

##### Step 1: Clone the Repository

Open Command Prompt or PowerShell:

```powershell
# Navigate to your preferred location
cd C:\Users\%USERNAME%\Documents

# Clone the repository
git clone https://github.com/YOUR_ORG/IT-IT.git

# Navigate into the project
cd IT-IT
```

##### Step 2: Install Python Dependencies

```powershell
# Install all required packages
pip install -r requirements.txt
```

This installs:
- `PySide6` - GUI framework
- `psycopg2-binary` - PostgreSQL driver
- `SQLAlchemy` - Database ORM
- `bcrypt` - Password hashing
- Other dependencies

##### Step 3: Configure Database Connection

**Get the config file from your admin (Kenyi):**

The admin should provide the correct `config/kanban_config.json` file with the production database settings. This file contains sensitive credentials and should NOT be in the Git repository.

**Or create it manually:**

```powershell
# Copy the template
copy config\kanban_config.prod.json config\kanban_config.json
```

Edit `config/kanban_config.json` with the correct server details:

```json
{
  "environment": "production",
  "database": {
    "host": "YOUR_SERVER_IP",
    "port": 5432,
    "database": "itit_kanban_prod",
    "username": "kanban_prod",
    "password": "YOUR_PASSWORD",
    "pool_size": 10,
    "max_overflow": 5
  }
}
```

##### Step 4: Test Connection

```powershell
python scripts/test_kanban_backend.py
```

Expected output:
```
✅ Connection successful!
```

##### Step 5: Launch Application

```powershell
# Start the IT!IT tool
python app.py
```

Or double-click `START_IT_TOOL.bat`

##### Step 6: First Login

1. Click the **📋 Kanban** tab
2. Login with your username
3. Initial password: `ChangeMe123!`
4. **You MUST change your password on first login**

---

### Quick Setup Script for IT Team

Create `QUICK_SETUP.bat` for easy deployment:

```batch
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
    pause
    exit /b 1
)

echo [1/4] Python found: 
python --version

echo.
echo [2/4] Installing dependencies...
pip install -r requirements.txt

echo.
echo [3/4] Checking config file...
if not exist "config\kanban_config.json" (
    echo WARNING: config\kanban_config.json not found!
    echo Please copy the config file from your admin.
    pause
    exit /b 1
)

echo.
echo [4/4] Testing database connection...
python scripts/test_kanban_backend.py

echo.
echo ============================================
echo Setup complete! 
echo Run START_IT_TOOL.bat to launch the application.
echo ============================================
pause
```

---

## Professional Deployment Workflow

### Git Branch Strategy

```
main (stable)
  │
  ├── develop (integration)
  │     │
  │     ├── feature/xxx
  │     ├── bugfix/xxx
  │     └── hotfix/xxx
  │
  └── release/v1.0 (UAT testing)
```

### Deployment Process

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        DEPLOYMENT WORKFLOW                              │
└─────────────────────────────────────────────────────────────────────────┘

  Developer                TEST ENV                    PROD ENV
     │                        │                           │
     │   1. Push to develop   │                           │
     │───────────────────────>│                           │
     │                        │                           │
     │   2. Deploy to TEST    │                           │
     │   (git pull on test    │                           │
     │    machines)           │                           │
     │                        │                           │
     │   3. UAT Testing       │                           │
     │<──────────────────────>│                           │
     │                        │                           │
     │   4. If pass:          │                           │
     │   Merge to main        │                           │
     │───────────────────────>│                           │
     │                        │                           │
     │                        │   5. Deploy to PROD       │
     │                        │   (git pull on prod       │
     │                        │    machines)              │
     │                        │──────────────────────────>│
     │                        │                           │
```

### Version Control Commands

```bash
# Developer: Push feature to develop
git checkout develop
git merge feature/my-feature
git push origin develop

# Test Environment: Pull latest
git pull origin develop

# After UAT approval: Merge to main
git checkout main
git merge develop
git push origin main

# Production: Pull stable version
git pull origin main
```

### Deployment Commands for Each Environment

**For TEST Environment:**

```powershell
# On test machine
cd C:\Path\To\IT-IT

# Pull latest from develop branch
git checkout develop
git pull origin develop

# Restart application
python app.py
```

**For PRODUCTION Environment:**

```powershell
# On production machine
cd C:\Path\To\IT-IT

# Pull latest from main branch (stable)
git checkout main
git pull origin main

# Restart application
python app.py
```

---

## Rollback Procedures

### If Something Goes Wrong

#### Application Rollback

```powershell
# Check recent commits
git log --oneline -10

# Rollback to specific version
git checkout <commit-hash>

# Or rollback to previous commit
git reset --hard HEAD~1
```

#### Database Rollback

If you need to reset the database:

```sql
-- Connect to the database
\c itit_kanban_prod

-- Drop all data and recreate
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO kanban_prod;
```

Then re-run setup script:
```powershell
psql -h <SERVER_IP> -U kanban_prod -d itit_kanban_prod -f scripts/setup_kanban_db.sql
python scripts/seed_production_users.py
```

---

## Checklist

### Pre-Deployment Checklist

- [ ] PostgreSQL installed on company server
- [ ] Network access verified (can ping server from workstations)
- [ ] Firewall allows port 5432
- [ ] TEST database created (`itit_kanban_test`)
- [ ] PROD database created (`itit_kanban_prod`)
- [ ] Database users created with correct permissions
- [ ] Schema initialized on both databases
- [ ] User list collected from IT team
- [ ] Config files created for each environment

### Per-Machine Setup Checklist

- [ ] Python 3.8+ installed
- [ ] Git installed
- [ ] Repository cloned
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Correct `kanban_config.json` in place
- [ ] Database connection tested
- [ ] Application launches successfully
- [ ] User can login

### Go-Live Checklist

- [ ] All team members have accounts
- [ ] All team members changed initial password
- [ ] Production seed script run (users + columns only)
- [ ] Backup procedure documented
- [ ] All test cases passed in UAT
- [ ] Rollback procedure tested

---

## Summary

### Key Points

1. **Two Databases**: Create separate TEST and PROD databases on the company server
2. **User Data Only**: For production, only seed users and columns - no sample tasks
3. **Config Files**: Keep separate config files for each environment; switch by copying
4. **Git Clone**: IT team clones from GitHub, installs dependencies, and configures
5. **Credentials**: The `kanban_config.json` with passwords should NOT be in Git

### Quick Reference

| Task | Command |
|------|---------|
| Clone repo | `git clone https://github.com/YOUR_ORG/IT-IT.git` |
| Install deps | `pip install -r requirements.txt` |
| Switch to TEST | `copy config\kanban_config.test.json config\kanban_config.json` |
| Switch to PROD | `copy config\kanban_config.prod.json config\kanban_config.json` |
| Test connection | `python scripts/test_kanban_backend.py` |
| Seed prod users | `python scripts/seed_production_users.py` |
| Start app | `python app.py` |
| Update app | `git pull origin main` |

---

## Need Help?

If you encounter issues:

1. Check database connection settings in `config/kanban_config.json`
2. Verify network connectivity to the server
3. Check PostgreSQL service is running on server
4. Review application logs in `logs/activity_log.jsonl`
5. Run `python scripts/test_kanban_backend.py` to diagnose

---

*Last Updated: November 2025*
*Version: 1.0*

