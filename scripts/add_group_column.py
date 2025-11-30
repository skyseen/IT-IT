"""
Add assigned_group_id column to kanban_tasks table.
This is a database migration to support the group assignment feature.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from kanban.database import get_db_manager
from sqlalchemy import text

def add_group_column():
    """Add assigned_group_id column to kanban_tasks table."""
    print("[*] Adding assigned_group_id column to kanban_tasks...")
    
    try:
        # Get database manager
        db = get_db_manager()
        
        # SQL to add the column (if it doesn't exist)
        sql = """
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'kanban_tasks' 
                AND column_name = 'assigned_group_id'
            ) THEN
                ALTER TABLE kanban_tasks 
                ADD COLUMN assigned_group_id INTEGER REFERENCES kanban_groups(id);
                
                CREATE INDEX IF NOT EXISTS ix_kanban_tasks_assigned_group_id 
                ON kanban_tasks(assigned_group_id);
                
                RAISE NOTICE 'Column assigned_group_id added successfully';
            ELSE
                RAISE NOTICE 'Column assigned_group_id already exists';
            END IF;
        END $$;
        """
        
        # Execute the SQL
        session = db.get_session()
        try:
            session.execute(text(sql))
            session.commit()
            print("[SUCCESS] Column added successfully!")
            print("\nThe kanban_tasks table now has:")
            print("  - assigned_group_id column (nullable, references kanban_groups)")
            print("  - Index for better query performance")
            print("\n[DONE] Database migration complete!")
        except Exception as e:
            session.rollback()
            print(f"[ERROR] Failed to add column: {e}")
            sys.exit(1)
        finally:
            session.close()
        
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure PostgreSQL is running")
        print("2. Check that config/kanban_config.json has correct credentials")
        print("3. Verify you can connect: psql -U kanban_dev -d itit_kanban_dev")
        sys.exit(1)

if __name__ == "__main__":
    add_group_column()

