"""
Create new database tables for the Group System.
Run this script to add the group-related tables without affecting existing data.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from kanban.database import get_db_manager
from kanban.models import Base

def create_group_tables():
    """Create group-related tables in the database."""
    print("[*] Creating group system tables...")
    
    try:
        # Get database manager
        db = get_db_manager()
        
        # Create all tables (will only create missing ones)
        Base.metadata.create_all(db.engine)
        
        print("[SUCCESS] Group system tables created successfully!")
        print("\nNew tables added:")
        print("  - kanban_groups")
        print("  - kanban_group_members")
        print("\nNew column added to kanban_tasks:")
        print("  - assigned_group_id")
        print("\n[DONE] Database is ready! You can now use the group system.")
        
    except Exception as e:
        print(f"[ERROR] Error creating tables: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure PostgreSQL is running")
        print("2. Check that config/kanban_config.json has correct database credentials")
        print("3. Verify you can connect: psql -U kanban_dev -d itit_kanban_dev")
        sys.exit(1)

if __name__ == "__main__":
    create_group_tables()

