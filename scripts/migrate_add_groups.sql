-- ===========================================================================
-- Migration Script: Add Group System Tables
-- ===========================================================================
-- This script adds the group functionality that was added after initial setup.
-- Run this on your TEST/PROD database to fix the schema mismatch.
--
-- Run with:
--   psql -h <SERVER_IP> -U kanban_test -d itit_kanban_test -f scripts/migrate_add_groups.sql
-- ===========================================================================

-- ===========================================================================
-- STEP 1: Create kanban_groups table (if not exists)
-- ===========================================================================
CREATE TABLE IF NOT EXISTS kanban_groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    color VARCHAR(7) DEFAULT '#60A5FA',
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Audit fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES kanban_users(id),
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_by INTEGER REFERENCES kanban_users(id)
);

-- Create indexes for kanban_groups
CREATE INDEX IF NOT EXISTS idx_groups_name ON kanban_groups(name);
CREATE INDEX IF NOT EXISTS idx_groups_is_active ON kanban_groups(is_active);

DO $$ 
BEGIN
    RAISE NOTICE '✓ kanban_groups table ready';
END $$;

-- ===========================================================================
-- STEP 2: Create kanban_group_members junction table (if not exists)
-- ===========================================================================
CREATE TABLE IF NOT EXISTS kanban_group_members (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES kanban_groups(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES kanban_users(id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'member',
    
    -- Audit
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    added_by INTEGER REFERENCES kanban_users(id),
    
    -- Ensure unique membership
    CONSTRAINT uq_group_user UNIQUE(group_id, user_id)
);

-- Create indexes for kanban_group_members
CREATE INDEX IF NOT EXISTS idx_group_members_group_id ON kanban_group_members(group_id);
CREATE INDEX IF NOT EXISTS idx_group_members_user_id ON kanban_group_members(user_id);

DO $$ 
BEGIN
    RAISE NOTICE '✓ kanban_group_members table ready';
END $$;

-- ===========================================================================
-- STEP 3: Add assigned_group_id column to kanban_tasks (if not exists)
-- ===========================================================================
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'kanban_tasks' 
        AND column_name = 'assigned_group_id'
    ) THEN
        ALTER TABLE kanban_tasks 
        ADD COLUMN assigned_group_id INTEGER REFERENCES kanban_groups(id);
        
        CREATE INDEX ix_kanban_tasks_assigned_group_id 
        ON kanban_tasks(assigned_group_id);
        
        RAISE NOTICE '✓ assigned_group_id column added to kanban_tasks';
    ELSE
        RAISE NOTICE '✓ assigned_group_id column already exists in kanban_tasks';
    END IF;
END $$;

-- ===========================================================================
-- STEP 4: Create default groups (optional - for testing)
-- ===========================================================================
-- INSERT INTO kanban_groups (name, description, color)
-- VALUES 
--     ('IT', 'IT Department Group', '#3B82F6'),
--     ('OA', 'OA Team Group', '#10B981')
-- ON CONFLICT (name) DO NOTHING;

-- ===========================================================================
-- COMPLETION MESSAGE
-- ===========================================================================
DO $$ 
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE '✅ Migration Complete!';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Added:';
    RAISE NOTICE '  - kanban_groups table';
    RAISE NOTICE '  - kanban_group_members table';
    RAISE NOTICE '  - assigned_group_id column';
    RAISE NOTICE '========================================';
END $$;


