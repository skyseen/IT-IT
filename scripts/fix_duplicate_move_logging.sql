-- ===========================================================================
-- Fix Duplicate Move Logging
-- ===========================================================================
-- This script modifies the trigger to stop logging column moves automatically
-- since we now handle this in Python code with readable column names.
-- ===========================================================================

-- Drop the existing trigger
DROP TRIGGER IF EXISTS trigger_log_task_changes ON kanban_tasks;

-- Recreate the function WITHOUT column move logging
CREATE OR REPLACE FUNCTION log_task_changes()
RETURNS TRIGGER AS $$
BEGIN
    -- NOTE: Column moves are now logged by Python code with readable column names
    -- So we removed that section from this trigger to avoid duplicates
    
    IF TG_OP = 'UPDATE' THEN
        -- Log assignment changes
        IF OLD.assigned_to IS DISTINCT FROM NEW.assigned_to THEN
            INSERT INTO kanban_activity_log (task_id, activity_type, user_id, field_name, old_value, new_value)
            VALUES (NEW.id, 'assigned', COALESCE(NEW.assigned_to, NEW.created_by), 
                    'assigned_to', COALESCE(OLD.assigned_to::TEXT, 'unassigned'), 
                    COALESCE(NEW.assigned_to::TEXT, 'unassigned'));
        END IF;
        
        -- Log priority changes
        IF OLD.priority IS DISTINCT FROM NEW.priority THEN
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

-- Recreate the trigger
CREATE TRIGGER trigger_log_task_changes
AFTER UPDATE ON kanban_tasks
FOR EACH ROW
EXECUTE FUNCTION log_task_changes();

-- Confirmation message
DO $$
BEGIN
    RAISE NOTICE 'Trigger updated successfully!';
    RAISE NOTICE 'Column moves will now only be logged by Python code with readable column names.';
    RAISE NOTICE 'No more duplicate move entries will be created.';
END $$;



