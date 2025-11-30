"""
Fix Duplicate Move Logging
===========================
This script modifies the database trigger to stop logging column moves automatically
since we now handle this in Python code with readable column names.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from kanban.database import get_db_manager
from sqlalchemy import text


def fix_duplicate_logging():
    """Remove column move logging from database trigger to avoid duplicates."""
    print("[*] Fixing duplicate move logging...")
    print()
    
    try:
        db = get_db_manager()
        session = db.get_session()
        
        sql = """
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
        """
        
        session.execute(text(sql))
        session.commit()
        
        print("[SUCCESS] Database trigger updated successfully!")
        print()
        print("Changes made:")
        print("  - Removed automatic column move logging from database trigger")
        print("  - Column moves are now ONLY logged by Python code")
        print("  - Activity log will show readable column names (e.g., 'To Do', 'Done')")
        print("  - No more duplicate move entries will be created")
        print()
        print("[DONE] You can now test drag-and-drop - it should create only ONE activity log entry!")
        
        session.close()
        
    except Exception as e:
        print(f"[ERROR] Failed to update trigger: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    fix_duplicate_logging()



