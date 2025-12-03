"""Update WIP limit for In Progress column from 10 to 20."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from kanban.database import get_db_manager
from kanban.models import KanbanColumn


def update_wip_limit():
    """Update WIP limit for In Progress column."""
    print("\n" + "="*60)
    print("UPDATING WIP LIMIT")
    print("="*60)
    
    db = get_db_manager()
    session = db.get_session()
    
    try:
        # Find In Progress column
        in_progress = session.query(KanbanColumn).filter_by(name="In Progress").first()
        
        if not in_progress:
            print("\n❌ In Progress column not found!")
            return False
        
        print(f"\n📊 Current WIP Limit: {in_progress.wip_limit}")
        
        # Update WIP limit
        in_progress.wip_limit = 20
        session.commit()
        
        print(f"✅ Updated WIP Limit: {in_progress.wip_limit}")
        print(f"\n🎉 WIP limit successfully updated!")
        print(f"   Now shows: ⚠️ WIP Limit Exceeded: current/20")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating WIP limit: {e}")
        session.rollback()
        return False
    finally:
        session.close()


if __name__ == "__main__":
    success = update_wip_limit()
    sys.exit(0 if success else 1)


