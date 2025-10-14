-- ===========================================================================
-- Kanban Database Schema Setup Script
-- PostgreSQL 15+
-- ===========================================================================
-- This script creates all tables, indexes, triggers, and views for the
-- Kanban task management system.
--
-- Run this script on your local PostgreSQL:
--   psql -h localhost -U kanban_dev -d itit_kanban_dev -f setup_kanban_db.sql
-- ===========================================================================

-- Drop existing tables if they exist (for clean setup)
DROP TABLE IF EXISTS kanban_dependencies CASCADE;
DROP TABLE IF EXISTS kanban_attachments CASCADE;
DROP TABLE IF EXISTS kanban_comments CASCADE;
DROP TABLE IF EXISTS kanban_activity_log CASCADE;
DROP TABLE IF EXISTS kanban_tasks CASCADE;
DROP TABLE IF EXISTS kanban_columns CASCADE;
DROP TABLE IF EXISTS kanban_sessions CASCADE;
DROP TABLE IF EXISTS kanban_settings CASCADE;
DROP TABLE IF EXISTS kanban_users CASCADE;

-- ===========================================================================
-- TABLE: kanban_users
-- ===========================================================================
CREATE TABLE kanban_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    email VARCHAR(200),
    role VARCHAR(50) DEFAULT 'member',
    avatar_color VARCHAR(7) DEFAULT '#60A5FA',
    department VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Audit fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES kanban_users(id),
    last_login TIMESTAMP,
    
    -- Metadata
    preferences JSONB DEFAULT '{}'::JSONB
);

CREATE INDEX idx_users_username ON kanban_users(username);
CREATE INDEX idx_users_is_active ON kanban_users(is_active);

-- ===========================================================================
-- TABLE: kanban_columns
-- ===========================================================================
CREATE TABLE kanban_columns (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    position INTEGER NOT NULL,
    color VARCHAR(7) DEFAULT '#94A3B8',
    wip_limit INTEGER DEFAULT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    description TEXT,
    
    -- Audit fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES kanban_users(id),
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_by INTEGER REFERENCES kanban_users(id),
    
    CONSTRAINT uq_column_name_active UNIQUE(name, is_active)
);

CREATE INDEX idx_columns_position ON kanban_columns(position);
CREATE INDEX idx_columns_is_active ON kanban_columns(is_active);

-- ===========================================================================
-- TABLE: kanban_tasks
-- ===========================================================================
CREATE TABLE kanban_tasks (
    id SERIAL PRIMARY KEY,
    
    -- Basic Info
    title VARCHAR(500) NOT NULL,
    description TEXT,
    task_number VARCHAR(50) UNIQUE,
    
    -- Organization
    column_id INTEGER REFERENCES kanban_columns(id) NOT NULL,
    position REAL NOT NULL,
    
    -- Assignment & Ownership
    assigned_to INTEGER REFERENCES kanban_users(id),
    created_by INTEGER REFERENCES kanban_users(id) NOT NULL,
    
    -- Priority & Status
    priority VARCHAR(20) DEFAULT 'medium',
    status VARCHAR(50) DEFAULT 'active',
    
    -- Categorization
    category VARCHAR(50),
    tags TEXT[],
    color VARCHAR(7),
    
    -- Time Tracking
    deadline DATE,
    estimated_hours NUMERIC(6,2),
    actual_hours NUMERIC(6,2) DEFAULT 0,
    
    -- Optional Workflow Integration
    is_workflow_task BOOLEAN DEFAULT FALSE,
    workflow_type VARCHAR(50),
    workflow_reference VARCHAR(200),
    workflow_metadata JSONB,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Soft delete
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP,
    deleted_by INTEGER REFERENCES kanban_users(id)
);

-- Indexes for performance
CREATE INDEX idx_tasks_column ON kanban_tasks(column_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_tasks_assigned ON kanban_tasks(assigned_to) WHERE is_deleted = FALSE;
CREATE INDEX idx_tasks_deadline ON kanban_tasks(deadline) WHERE is_deleted = FALSE;
CREATE INDEX idx_tasks_category ON kanban_tasks(category) WHERE is_deleted = FALSE;
CREATE INDEX idx_tasks_status ON kanban_tasks(status) WHERE is_deleted = FALSE;
CREATE INDEX idx_tasks_priority ON kanban_tasks(priority) WHERE is_deleted = FALSE;
CREATE INDEX idx_tasks_created_at ON kanban_tasks(created_at);
CREATE INDEX idx_tasks_is_deleted ON kanban_tasks(is_deleted);

-- Full-text search index
CREATE INDEX idx_tasks_search ON kanban_tasks 
USING gin(to_tsvector('english', title || ' ' || COALESCE(description, '')));

-- ===========================================================================
-- TABLE: kanban_activity_log
-- ===========================================================================
CREATE TABLE kanban_activity_log (
    id BIGSERIAL PRIMARY KEY,
    
    -- What happened
    task_id INTEGER REFERENCES kanban_tasks(id) ON DELETE SET NULL,
    activity_type VARCHAR(50) NOT NULL,
    
    -- Who did it
    user_id INTEGER REFERENCES kanban_users(id) NOT NULL,
    
    -- Details
    field_name VARCHAR(100),
    old_value TEXT,
    new_value TEXT,
    comment TEXT,
    
    -- Context
    ip_address VARCHAR(45),
    user_agent TEXT,
    
    -- When
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Full snapshot
    task_snapshot JSONB
);

CREATE INDEX idx_activity_task ON kanban_activity_log(task_id);
CREATE INDEX idx_activity_user ON kanban_activity_log(user_id);
CREATE INDEX idx_activity_type ON kanban_activity_log(activity_type);
CREATE INDEX idx_activity_date ON kanban_activity_log(created_at);

-- ===========================================================================
-- TABLE: kanban_comments
-- ===========================================================================
CREATE TABLE kanban_comments (
    id BIGSERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES kanban_tasks(id) ON DELETE CASCADE NOT NULL,
    user_id INTEGER REFERENCES kanban_users(id) NOT NULL,
    comment TEXT NOT NULL,
    
    -- Threading
    parent_comment_id INTEGER REFERENCES kanban_comments(id),
    
    -- Metadata
    is_edited BOOLEAN DEFAULT FALSE,
    edited_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_comments_task ON kanban_comments(task_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_comments_user ON kanban_comments(user_id);

-- ===========================================================================
-- TABLE: kanban_attachments
-- ===========================================================================
CREATE TABLE kanban_attachments (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES kanban_tasks(id) ON DELETE CASCADE NOT NULL,
    
    -- File info
    file_name VARCHAR(500) NOT NULL,
    file_path TEXT NOT NULL,
    file_type VARCHAR(100),
    file_size BIGINT,
    mime_type VARCHAR(100),
    
    -- Workflow attachment
    from_workflow BOOLEAN DEFAULT FALSE,
    
    -- Audit
    uploaded_by INTEGER REFERENCES kanban_users(id) NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Soft delete
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP,
    deleted_by INTEGER REFERENCES kanban_users(id)
);

CREATE INDEX idx_attachments_task ON kanban_attachments(task_id) WHERE is_deleted = FALSE;

-- ===========================================================================
-- TABLE: kanban_dependencies
-- ===========================================================================
CREATE TABLE kanban_dependencies (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES kanban_tasks(id) ON DELETE CASCADE NOT NULL,
    depends_on_task_id INTEGER REFERENCES kanban_tasks(id) ON DELETE CASCADE NOT NULL,
    dependency_type VARCHAR(20) DEFAULT 'blocks',
    
    -- Audit
    created_by INTEGER REFERENCES kanban_users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uq_task_dependency UNIQUE(task_id, depends_on_task_id)
);

-- ===========================================================================
-- TABLE: kanban_sessions
-- ===========================================================================
CREATE TABLE kanban_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES kanban_users(id) ON DELETE CASCADE NOT NULL,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    
    login_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    logout_at TIMESTAMP,
    
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_sessions_user ON kanban_sessions(user_id);
CREATE INDEX idx_sessions_is_active ON kanban_sessions(is_active);
CREATE INDEX idx_sessions_token ON kanban_sessions(session_token);

-- ===========================================================================
-- TABLE: kanban_settings
-- ===========================================================================
CREATE TABLE kanban_settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value JSONB NOT NULL,
    description TEXT,
    
    -- Audit
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_by INTEGER REFERENCES kanban_users(id)
);

-- ===========================================================================
-- TRIGGERS
-- ===========================================================================

-- Auto-update modified timestamp
CREATE OR REPLACE FUNCTION update_modified_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_task_timestamp
BEFORE UPDATE ON kanban_tasks
FOR EACH ROW
EXECUTE FUNCTION update_modified_timestamp();

-- Auto-log task changes
CREATE OR REPLACE FUNCTION log_task_changes()
RETURNS TRIGGER AS $$
BEGIN
    -- Log column moves
    IF TG_OP = 'UPDATE' THEN
        IF OLD.column_id != NEW.column_id THEN
            INSERT INTO kanban_activity_log (task_id, activity_type, user_id, field_name, old_value, new_value)
            VALUES (NEW.id, 'moved', COALESCE(NEW.assigned_to, NEW.created_by), 'column_id', 
                    OLD.column_id::TEXT, NEW.column_id::TEXT);
        END IF;
        
        -- Log assignment changes
        IF OLD.assigned_to IS DISTINCT FROM NEW.assigned_to THEN
            INSERT INTO kanban_activity_log (task_id, activity_type, user_id, field_name, old_value, new_value)
            VALUES (NEW.id, 'assigned', COALESCE(NEW.assigned_to, OLD.assigned_to, NEW.created_by), 
                    'assigned_to', COALESCE(OLD.assigned_to::TEXT, 'unassigned'), 
                    COALESCE(NEW.assigned_to::TEXT, 'unassigned'));
        END IF;
        
        -- Log priority changes
        IF OLD.priority != NEW.priority THEN
            INSERT INTO kanban_activity_log (task_id, activity_type, user_id, field_name, old_value, new_value)
            VALUES (NEW.id, 'priority_changed', COALESCE(NEW.assigned_to, NEW.created_by), 
                    'priority', OLD.priority, NEW.priority);
        END IF;
        
        -- Log deadline changes
        IF OLD.deadline IS DISTINCT FROM NEW.deadline THEN
            INSERT INTO kanban_activity_log (task_id, activity_type, user_id, field_name, old_value, new_value)
            VALUES (NEW.id, 'deadline_changed', COALESCE(NEW.assigned_to, NEW.created_by), 
                    'deadline', COALESCE(OLD.deadline::TEXT, 'none'), 
                    COALESCE(NEW.deadline::TEXT, 'none'));
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_log_task_changes
AFTER UPDATE ON kanban_tasks
FOR EACH ROW
EXECUTE FUNCTION log_task_changes();

-- ===========================================================================
-- VIEWS
-- ===========================================================================

-- Active tasks with user info
CREATE OR REPLACE VIEW v_active_tasks AS
SELECT 
    t.id,
    t.task_number,
    t.title,
    t.description,
    t.priority,
    t.category,
    t.deadline,
    t.created_at,
    c.name AS column_name,
    c.color AS column_color,
    u.display_name AS assigned_to_name,
    u.avatar_color AS assignee_color,
    creator.display_name AS created_by_name,
    (SELECT COUNT(*) FROM kanban_comments WHERE task_id = t.id AND is_deleted = FALSE) AS comment_count,
    (SELECT COUNT(*) FROM kanban_attachments WHERE task_id = t.id AND is_deleted = FALSE) AS attachment_count
FROM kanban_tasks t
LEFT JOIN kanban_columns c ON t.column_id = c.id
LEFT JOIN kanban_users u ON t.assigned_to = u.id
LEFT JOIN kanban_users creator ON t.created_by = creator.id
WHERE t.is_deleted = FALSE AND c.is_active = TRUE
ORDER BY c.position, t.position;

-- Overdue tasks
CREATE OR REPLACE VIEW v_overdue_tasks AS
SELECT *
FROM v_active_tasks
WHERE deadline < CURRENT_DATE AND column_name != 'Done';

-- User workload
CREATE OR REPLACE VIEW v_user_workload AS
SELECT 
    u.id AS user_id,
    u.display_name,
    COUNT(t.id) AS active_tasks,
    SUM(CASE WHEN t.priority = 'critical' THEN 1 ELSE 0 END) AS critical_tasks,
    SUM(CASE WHEN t.deadline < CURRENT_DATE THEN 1 ELSE 0 END) AS overdue_tasks
FROM kanban_users u
LEFT JOIN kanban_tasks t ON u.id = t.assigned_to AND t.is_deleted = FALSE
WHERE u.is_active = TRUE
GROUP BY u.id, u.display_name
ORDER BY active_tasks DESC;

-- ===========================================================================
-- COMPLETION MESSAGE
-- ===========================================================================
DO $$ 
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Kanban Database Schema Setup Complete!';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Tables created: 9';
    RAISE NOTICE 'Indexes created: 20+';
    RAISE NOTICE 'Triggers created: 2';
    RAISE NOTICE 'Views created: 3';
    RAISE NOTICE '';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '1. Run seed_kanban_data.py to populate initial data';
    RAISE NOTICE '2. Test connection with test_kanban_backend.py';
    RAISE NOTICE '========================================';
END $$;


