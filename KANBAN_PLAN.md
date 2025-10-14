# Kanban Feature Implementation Plan (Local Dev + Production Migration)

## Project Scope

Add Kanban task management to the existing IT!IT OA Tool (PySide6 desktop app) with:

- PostgreSQL database backend (20 users, 10 concurrent max)
- Integrated as new tab in app.py
- Optional auto-task creation from workflows (configurable)
- Comprehensive audit logging using existing activity_log.py infrastructure
- **Development Strategy: Build locally, then migrate to IT server**

## Development Strategy (Two-Phase Approach)

### Phase A: Local Development (Week 0-9)

- Install PostgreSQL on YOUR local machine
- Develop and test all features locally
- No dependency on IT department
- Full control over database and testing

### Phase B: Production Migration (Week 10)

- Set up PostgreSQL on IT server
- Export schema and migrate data
- Update connection config for all 20 users
- Gradual rollout with monitoring

This approach is **much better** because:

- Faster development cycles
- Easy debugging and testing
- No network coordination during dev
- Production deployment only when ready
- Can demo to management before full rollout

## Phase A: Local Development Setup

### Prerequisites (Week 0 - Your Local Machine)

**1. Install PostgreSQL Locally (Windows)**

- Download PostgreSQL 15+ installer from postgresql.org
- Install on your Windows machine (localhost)
- Installation specs: Default settings are fine for local dev
- Port: 5432 (default)
- Set postgres user password (remember it!)

**2. Create Local Development Database**

```sql
-- Run in pgAdmin or psql on YOUR machine
CREATE DATABASE itit_kanban_dev;
CREATE USER kanban_dev WITH PASSWORD 'DevPassword123!';
GRANT ALL PRIVILEGES ON DATABASE itit_kanban_dev TO kanban_dev;
```

**3. Update Python Dependencies**

Add to `requirements.txt`:

```
pandas>=1.5
openpyxl>=3.1
pywin32>=306
PySide6>=6.6
psycopg2-binary>=2.9.9    # NEW: PostgreSQL adapter
SQLAlchemy>=2.0.23         # NEW: ORM
python-dateutil>=2.8.2     # NEW: Date utilities
```

Run: `pip install -r requirements.txt`

**4. Local Connection Configuration**

Create `config/kanban_config.json`:

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

## File Structure (New Files to Create)

```
IT-IT/
├── app.py                          # MODIFY: Add Kanban tab
├── ui.py                           # USE AS-IS: Reuse scroll components
├── activity_log.py                 # USE AS-IS: Kanban will log here
├── config_manager.py               # MODIFY: Add kanban config section
├── requirements.txt                # MODIFY: Add PostgreSQL deps
│
├── kanban/                         # NEW MODULE
│   ├── __init__.py
│   ├── models.py                   # SQLAlchemy ORM models
│   ├── database.py                 # Connection manager
│   ├── manager.py                  # Business logic (CRUD)
│   ├── ui_board.py                 # Main Kanban board view
│   ├── ui_components.py            # Task cards, dialogs
│   ├── ui_my_tasks.py              # Personal task view
│   ├── ui_reports.py               # Metrics dashboard
│   └── audit_logger.py             # Kanban-specific audit wrapper
│
├── config/
│   └── kanban_config.json          # NEW: DB connection (local for dev)
│
├── scripts/
│   ├── setup_kanban_db.sql         # NEW: Database schema
│   ├── seed_kanban_data.py         # NEW: Initial data setup
│   ├── backup_kanban.py            # NEW: Backup script
│   ├── export_for_migration.py     # NEW: Export data for migration
│   └── migrate_to_production.py   # NEW: Migration script
│
├── kanban_attachments/             # NEW: Local attachment storage
│
└── docs/
    └── KANBAN_USER_GUIDE.md        # NEW: User documentation
```

## Implementation Phases (Local Development)

### Phase 1: Database Foundation (Week 1-2)

**Week 1: Schema & Models**

1. **Create database schema**: `scripts/setup_kanban_db.sql`

   - Tables: kanban_users, kanban_columns, kanban_tasks, kanban_activity_log, kanban_comments, kanban_attachments, kanban_sessions, kanban_settings
   - Indexes for performance
   - Triggers for auto-logging
   - Views for common queries
   - Run this script on your local PostgreSQL

2. **Create SQLAlchemy models**: `kanban/models.py`

   - KanbanUser, KanbanColumn, KanbanTask, KanbanActivityLog, etc.
   - Define relationships between models
   - Add computed properties

3. **Create database connection manager**: `kanban/database.py`

   - Singleton pattern with connection pooling
   - Session management (scoped_session for thread safety)
   - Reads from config/kanban_config.json
   - Environment-aware (dev vs production)
   - Retry logic for connection failures

4. **Add Kanban config to `config_manager.py`**:

   ```python
   # Add to DEFAULT_CONFIG
   "kanban": {
       "enabled": True,
       "features": {
           "auto_create_tasks": True,
           "workflow_integration": {
               "sap_creation": True,
               "sap_disable": True,
               "agile_creation": True,
               "agile_reset": True,
               "telco_singtel": True,
               "telco_m1": True,
               "user_onboarding": False,
               "user_disable": False
           }
       },
       "default_columns": [
           {"name": "Backlog", "position": 0, "color": "#94A3B8"},
           {"name": "To Do", "position": 1, "color": "#60A5FA"},
           {"name": "In Progress", "position": 2, "color": "#FBBF24", "wip_limit": 10},
           {"name": "Review", "position": 3, "color": "#A78BFA"},
           {"name": "Done", "position": 4, "color": "#34D399"}
       ]
   }
   ```

**Week 2: Business Logic & Testing**

1. **Create KanbanManager**: `kanban/manager.py`

   - CRUD operations for tasks
   - Move tasks between columns with position management
   - Assign/unassign users
   - Add comments and attachments
   - All operations with full audit trail

2. **Create audit logger**: `kanban/audit_logger.py`

   - Wraps existing activity_log.py
   - Logs to PostgreSQL (detailed) AND JSONL (summary)
   - Event types: task_created, task_moved, task_assigned, etc.

3. **Create seed data script**: `scripts/seed_kanban_data.py`

   - Creates test users (you + 4-5 test users for local testing)
   - Creates default columns from config
   - Creates 20-30 sample tasks for testing
   - Run this to populate your local database

4. **Write test script**: `scripts/test_kanban_backend.py`

   - Test all CRUD operations
   - Test concurrent operations (simulate multiple users)
   - Verify audit logging works
   - Test error handling and rollback

**Deliverable**: Fully functional backend testable via Python scripts

**Verification**: Run test script successfully, inspect data in pgAdmin

### Phase 2: Core Kanban UI (Week 3-5)

**Week 3: Basic Board Layout**

1. **Add Kanban tab to `app.py`**:

   ```python
   # In MainWindow._build_tabs()
   from kanban.ui_board import build_kanban_section
   
   kanban_tab = QtWidgets.QWidget()
   build_kanban_section(kanban_tab)
   self.tabs.addTab(kanban_tab, "📋 Kanban")
   ```

2. **Create main board view**: `kanban/ui_board.py`

   - KanbanBoardWidget class
   - Column headers with task counts and WIP limits
   - Uses QScrollArea (like existing tabs)
   - Filter toolbar: search, assignee filter, category, priority, deadline
   - "New Task" button
   - Refresh button (manual refresh for now)

3. **Create task card component**: `kanban/ui_components.py`

   - TaskCardWidget class (QFrame-based)
   - Display: task number, title, assignee avatar, priority badge, deadline
   - Visual indicators: overdue (red), high priority (orange), has attachments (📎), has comments (💬)
   - Hover state with quick action buttons
   - Click to open detail dialog

4. **Load and display tasks**:

   - On board load, fetch tasks from KanbanManager
   - Render cards in appropriate columns
   - Apply current filters
   - Handle empty columns gracefully

**Week 4: Drag-Drop & Task Operations**

1. **Implement drag-and-drop**:

   - Make TaskCardWidget draggable (implement mousePressEvent, mouseMoveEvent, startDrag)
   - Make columns accept drops (implement dragEnterEvent, dragMoveEvent, dropEvent)
   - Visual feedback: highlight target column during drag
   - On drop: call KanbanManager.move_task() to update database
   - Refresh UI after successful move

2. **Create New Task dialog**: `kanban/ui_components.py > NewTaskDialog`

   - Modal dialog with form layout
   - Fields: title (required), description, assignee dropdown, priority dropdown, category dropdown, deadline date picker, estimated hours
   - Tags input (comma-separated)
   - Column selection (which column to create in)
   - Validation: title is required
   - On save: calls KanbanManager.create_task()

3. **Create Task Detail dialog**: `kanban/ui_components.py > TaskDetailDialog`

   - Larger modal dialog
   - Editable fields (same as New Task)
   - Workflow link section (shows only if is_workflow_task=True)
   - Comments section: thread view + add comment input
   - Attachments section: list + upload button + download/delete buttons
   - Activity history: timeline of all changes
   - Buttons: Delete Task, Cancel, Save Changes

4. **Implement auto-refresh**:

   - QTimer triggers every 30 seconds
   - Fetches tasks from database
   - Compares with current UI state
   - Updates only changed/new/deleted tasks (not full reload)

**Week 5: Comments, Attachments & Polish**

1. **Comments system**:

   - Add comment input box in TaskDetailDialog
   - Post button calls KanbanManager.add_comment()
   - Display thread with user name, timestamp
   - Edit/delete buttons for own comments
   - Logs comment activity

2. **Attachments system**:

   - Upload button opens file dialog
   - Stores file in `kanban_attachments/task_{id}/` folder
   - Saves metadata to database
   - Download button opens file
   - Delete button removes file and database entry
   - Shows file name, size, uploader, date

3. **UI polish**:

   - Loading spinner during database operations
   - Error dialogs with friendly messages
   - Confirmation for delete operations
   - Keyboard shortcuts (Ctrl+N new task, F5 refresh, Esc close dialogs)
   - Tooltips on all controls
   - Consistent styling with existing tool theme

**Deliverable**: Fully functional Kanban board in IT!IT tool

**Verification**: Test all operations locally, drag-drop works, data persists

### Phase 3: Additional Views & Reports (Week 6-7)

**Week 6: My Tasks View**

1. **Create personal dashboard**: `kanban/ui_my_tasks.py`

   - MyTasksWidget showing current user's tasks only
   - Sections: Overdue (red), High Priority (orange), In Progress, Completed Today
   - Each section shows filtered task cards
   - Click card to open TaskDetailDialog

2. **Add sub-tabs in Kanban tab**:

   ```python
   # In kanban/ui_board.py
   kanban_tabs = QTabWidget()
   kanban_tabs.addTab(board_view, "🏠 Board")
   kanban_tabs.addTab(my_tasks_view, "👤 My Tasks")
   kanban_tabs.addTab(reports_view, "📊 Reports")
   ```

**Week 7: Reports & Metrics**

1. **Create reports view**: `kanban/ui_reports.py`

   - ReportsWidget with metrics dashboard
   - Overview: total tasks, completed %, overdue count, in progress count
   - Team workload: horizontal bar chart showing tasks per user
   - Category breakdown: bar chart by category
   - Time metrics: average completion time, tasks completed this week
   - Bottleneck detection: columns exceeding WIP limits

2. **Data export**:

   - "Export to CSV" button
   - Exports currently filtered task list
   - Opens save file dialog
   - Uses pandas to generate CSV

3. **Audit log viewer**:

   - Searchable list of all activities
   - Filters: user dropdown, activity type dropdown, date range
   - Shows: timestamp, user, action, details
   - Click to see full details

**Deliverable**: Complete Kanban feature with analytics

**Verification**: Generate reports with test data, export works

### Phase 4: Workflow Integration (Week 8)

**Integration Points**

Modify existing workflow files to optionally create Kanban tasks:

1. **SAP workflows** (`sap_workflows.py`):

   ```python
   # After successful SAP account creation
   if get_config("kanban.features.workflow_integration.sap_creation"):
       from kanban.manager import KanbanManager
       kanban_mgr = KanbanManager(current_user_id=current_user.id)
       kanban_mgr.create_task(
           title=f"SAP Account - {employee_name}",
           description=f"Employee ID: {employee_id}\nDepartment: {department}",
           category="sap",
           priority="medium",
           column_id=get_column_by_name("To Do"),
           is_workflow_task=True,
           workflow_type="sap_creation",
           workflow_reference=employee_id
       )
   ```

2. **Agile workflows** (in workflow handlers):

   - Similar pattern for agile_creation and agile_reset

3. **Telco workflows** (`telco_workflows.py`):

   - Similar pattern for telco_singtel and telco_m1

**Settings UI**

1. **Add Kanban tab to SettingsDialog** (`ui.py`):

   - New tab "Kanban Settings"
   - Section: Workflow Integration
   - Checkboxes for each workflow type
   - Dropdown for default column
   - Dropdown for default priority
   - Save/Cancel buttons

2. **Update config_manager.py**:

   - Add get_kanban_config() and set_kanban_config() functions
   - Save settings to it_tool_config.json

**Deliverable**: Optional workflow integration with on/off switches

**Verification**: Enable SAP integration, run workflow, verify task created

### Phase 5: Local Testing & Refinement (Week 9)

**Comprehensive Testing**

1. **Feature testing**:

   - Test all CRUD operations
   - Test drag-drop thoroughly
   - Test filters and search
   - Test comments and attachments
   - Test all reports and exports
   - Test workflow integration

2. **Performance testing**:

   - Create 1000 test tasks via script
   - Measure board load time (target < 2s)
   - Test search speed (target < 0.5s)
   - Monitor memory usage

3. **Bug fixing**:

   - Fix any crashes or errors
   - Improve error handling
   - Polish UI/UX issues
   - Optimize slow operations

4. **Documentation**:

   - Create `docs/KANBAN_USER_GUIDE.md` with screenshots
   - Document all features
   - Add troubleshooting section
   - Create admin guide for migration

**Deliverable**: Production-ready code, fully tested locally

**Verification**: All features work flawlessly on your local machine

## Phase B: Production Migration (Week 10)

### Step 1: IT Server PostgreSQL Setup

**Coordinate with IT Department**:

1. Request PostgreSQL server (or VM) with:

   - PostgreSQL 15+
   - 2 CPU cores, 8GB RAM, 100GB storage
   - Network accessible to all 20 users
   - Static IP address (e.g., 192.168.1.100)

2. Have IT create database and user:

   ```sql
   CREATE DATABASE itit_kanban;
   CREATE USER kanban_app WITH PASSWORD 'SecureProductionPassword!';
   GRANT ALL PRIVILEGES ON DATABASE itit_kanban TO kanban_app;
   ```

3. Verify connectivity:

   - From your machine: `psql -h 192.168.1.100 -U kanban_app -d itit_kanban`
   - Test from 2-3 user machines

### Step 2: Schema Migration

**Export and Import Schema**:

1. Run migration script: `scripts/migrate_to_production.py`

   ```python
   # This script will:
   # 1. Export schema from local to SQL file
   # 2. Connect to production server
   # 3. Create all tables, indexes, triggers, views
   # 4. Create default columns
   # 5. Optionally import test data (for demo)
   ```

2. Verify tables created:

   - Connect to production database
   - Check all tables exist
   - Verify indexes and triggers

### Step 3: Create Production Users

**Seed User Data**:

1. Create list of 20 actual users (names, emails, departments)
2. Run seed script on production: `scripts/seed_production_users.py`
3. Verify all users created

### Step 4: Update Application Configuration

**Create Production Config**:

1. Create `config/kanban_config_production.json`:

   ```json
   {
     "environment": "production",
     "database": {
       "host": "192.168.1.100",
       "port": 5432,
       "database": "itit_kanban",
       "username": "kanban_app",
       "password": "ENCRYPTED_PASSWORD",
       "pool_size": 10,
       "max_overflow": 5
     }
   }
   ```

2. Update `kanban/database.py` to read correct config based on environment

3. Distribute updated IT!IT tool to all users:

   - Option A: Network share (update .py files)
   - Option B: Compile to .exe and distribute
   - Option C: Installer package

### Step 5: Gradual Rollout

**Week 10 - Phased Deployment**:

1. **Pilot Group (Day 1-2)**: 5 users test production

   - Monitor for connection issues
   - Verify multi-user operations work
   - Collect initial feedback

2. **Expand (Day 3-4)**: 10 users

   - Monitor performance
   - Check concurrent access
   - Fix any issues

3. **Full Rollout (Day 5)**: All 20 users

   - Announce via email
   - Provide user guide
   - Be available for support

### Step 6: Production Monitoring

**Setup Monitoring**:

1. **Database backups**:

   - Schedule `scripts/backup_kanban.py` via Windows Task Scheduler
   - Daily at 2:00 AM
   - Keep last 30 backups
   - Store on network drive

2. **Performance monitoring**:

   - Monitor PostgreSQL connection pool usage
   - Check slow query log
   - Monitor disk space

3. **User support**:

   - Create support channel (email/Teams)
   - Document common issues
   - Plan regular check-ins

### Step 7: Post-Launch Stabilization (Week 11-12)

**Monitor and Optimize**:

- Track user adoption rate
- Fix reported bugs
- Optimize slow queries
- Adjust connection pool if needed
- Gather user feedback for improvements

## Migration Checklist

**Before Migration**:

- [ ] Local development fully complete and tested
- [ ] All features working on local PostgreSQL
- [ ] User guide documentation complete
- [ ] PostgreSQL installed on IT server
- [ ] Database and user created on IT server
- [ ] Network connectivity verified from all user machines
- [ ] Backup script tested

**During Migration**:

- [ ] Export schema to production server
- [ ] Create default columns
- [ ] Seed user data (20 users)
- [ ] Update application config to production
- [ ] Test connection from your machine
- [ ] Deploy updated tool to pilot users (5)

**After Migration**:

- [ ] Pilot testing successful
- [ ] Expand to 10 users
- [ ] Full rollout to 20 users
- [ ] Backup automation scheduled
- [ ] User training completed
- [ ] Support process established

## Technical Specifications

### Local Development

- **Database**: PostgreSQL 15+ on localhost
- **Connection**: localhost:5432
- **Pool Size**: 5 (sufficient for local testing)
- **Data**: Test/sample data only

### Production Environment

- **Database**: PostgreSQL 15+ on IT server (192.168.1.x)
- **Connection**: server_ip:5432
- **Pool Size**: 10 (10 concurrent users)
- **Max Overflow**: 5 (handle bursts up to 15)
- **Users**: 20 actual users
- **Data**: Real production data

### Audit Logging

- **PostgreSQL**: Detailed activity log in kanban_activity_log table
- **JSONL**: Summary logs in logs/activity_log.jsonl (existing)
- **Retention**: 90 days in database, unlimited in JSONL

## Timeline Summary

**Phase A: Local Development**

- Week 0: Install PostgreSQL locally, setup dev environment
- Week 1-2: Database foundation (backend)
- Week 3-5: Core Kanban UI
- Week 6-7: Additional views & reports
- Week 8: Workflow integration
- Week 9: Local testing & refinement

**Phase B: Production Migration**

- Week 10: Coordinate with IT, migrate to production, gradual rollout
- Week 11-12: Stabilization and support

**Total**: 12 weeks (9 weeks dev + 1 week migration + 2 weeks stabilization)

## Advantages of This Approach

1. **Faster Development**: No network latency, no IT dependencies
2. **Full Control**: Complete control over database during development
3. **Easy Testing**: Can reset database anytime, test with sample data
4. **Lower Risk**: Thoroughly tested before production deployment
5. **Flexible Timeline**: No pressure from IT server availability
6. **Better Debugging**: Easier to troubleshoot on local machine
7. **Demo Ready**: Can show management working prototype anytime

## Open Questions for Production Migration

Answer these before Week 10:

1. What is the IT server IP address for PostgreSQL?
2. Who will manage PostgreSQL on the server (DBA)?
3. Where should production backups be stored? (network drive path?)
4. What is the preferred distribution method for the tool? (network share/exe/installer)
5. Should we use Windows Active Directory for user authentication?
6. Attachment storage in production: local folder or network share?
7. Maximum attachment file size limit?
8. Email notification preferences for task assignments?

## Implementation To-dos

### Phase A: Local Development (Week 0-9)

**Week 0 - Local Setup**

- [ ] Install PostgreSQL 15+ on your local Windows machine
- [ ] Create local database: itit_kanban_dev
- [ ] Create local user: kanban_dev with password
- [ ] Install Python dependencies (psycopg2-binary, SQLAlchemy, python-dateutil)
- [ ] Create config/kanban_config.json with localhost connection

**Week 1-2 - Backend Foundation**

- [ ] Create database schema SQL script (scripts/setup_kanban_db.sql)
- [ ] Run schema script on local PostgreSQL to create tables
- [ ] Build SQLAlchemy ORM models (kanban/models.py)
- [ ] Create database connection manager (kanban/database.py) pointing to localhost
- [ ] Add Kanban configuration section to config_manager.py
- [ ] Build KanbanManager business logic with CRUD operations (kanban/manager.py)
- [ ] Create audit logger wrapper (kanban/audit_logger.py)
- [ ] Create seed data script for local testing (scripts/seed_kanban_data.py)
- [ ] Write and run backend test script (scripts/test_kanban_backend.py)
- [ ] Verify all backend operations work locally

**Week 3-5 - Core Kanban UI**

- [ ] Add Kanban tab to app.py main window
- [ ] Create main board view layout (kanban/ui_board.py)
- [ ] Build task card widget component (kanban/ui_components.py)
- [ ] Implement drag-and-drop functionality for task cards
- [ ] Create New Task dialog with form validation
- [ ] Create Task Detail dialog with full editing capabilities
- [ ] Implement comments system (add, edit, delete)
- [ ] Implement attachments system (upload, download, delete)
- [ ] Add loading states and error handling
- [ ] Add keyboard shortcuts and tooltips
- [ ] Test all UI operations on local database

**Week 6-7 - Additional Views & Reports**

- [ ] Build My Tasks personal dashboard view (kanban/ui_my_tasks.py)
- [ ] Add sub-tabs (Board, My Tasks, Reports) to Kanban section
- [ ] Create reports and metrics view (kanban/ui_reports.py)
- [ ] Implement data export to CSV functionality
- [ ] Build audit log viewer with filters
- [ ] Test reports with varied data sets

**Week 8 - Workflow Integration**

- [ ] Integrate Kanban with SAP workflows (sap_workflows.py)
- [ ] Integrate Kanban with Agile workflows
- [ ] Integrate Kanban with Telco workflows (telco_workflows.py)
- [ ] Add Kanban settings tab to SettingsDialog in ui.py
- [ ] Update config_manager.py with Kanban config functions
- [ ] Test workflow auto-task creation end-to-end

**Week 9 - Testing & Documentation**

- [ ] Comprehensive feature testing (all CRUD, drag-drop, filters, search)
- [ ] Performance testing with 1000 test tasks
- [ ] Bug fixing and optimization
- [ ] Write user documentation (docs/KANBAN_USER_GUIDE.md)
- [ ] Write admin migration guide
- [ ] Create migration scripts (export_for_migration.py, migrate_to_production.py)
- [ ] Final local testing - ensure everything works perfectly

### Phase B: Production Migration (Week 10-12)

**Week 10 - Migration to IT Server**

- [ ] Coordinate with IT department for PostgreSQL server setup
- [ ] Get IT server IP address, database credentials, and network details
- [ ] Verify network connectivity from 2-3 user machines to IT server
- [ ] Run migration script to export schema to production server
- [ ] Verify all tables, indexes, triggers, and views created on production
- [ ] Seed production user data (20 actual users)
- [ ] Create production config file (config/kanban_config_production.json)
- [ ] Update kanban/database.py to support environment-based config
- [ ] Deploy updated tool to 5 pilot users
- [ ] Monitor pilot group for 2 days, collect feedback
- [ ] Expand to 10 users
- [ ] Monitor expanded group for 2 days
- [ ] Full rollout to all 20 users
- [ ] Setup automated backup script on IT server (Windows Task Scheduler)
- [ ] Verify backups are running correctly

**Week 11-12 - Stabilization & Support**

- [ ] Monitor production performance daily
- [ ] Track PostgreSQL connection pool usage
- [ ] Fix any reported bugs or issues
- [ ] Optimize slow queries if identified
- [ ] Gather user feedback and feature requests
- [ ] Document common issues and solutions
- [ ] Plan future enhancements based on feedback


