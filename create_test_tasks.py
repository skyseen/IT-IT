"""Create test tasks for pagination and view mode testing.

This script creates:
- 35 tasks in Backlog (to test pagination >30)
- 25 tasks in To Do (to test compact view 20-50)
- 55 tasks in In Progress (to test mini view >50)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime, timedelta, date
from kanban.database import get_db_manager
from kanban.manager import KanbanManager
from kanban.models import KanbanUser, KanbanColumn, KanbanGroup
import random


def create_test_tasks():
    """Create test tasks for pagination and view mode testing."""
    print("\n" + "="*60)
    print("CREATING TEST TASKS FOR PAGINATION & VIEW MODES")
    print("="*60)
    
    db = get_db_manager()
    session = db.get_session()
    
    try:
        # Get first active user
        user = session.query(KanbanUser).filter_by(is_active=True).first()
        if not user:
            print("❌ No active users found!")
            return False
        
        print(f"\n👤 Using user: {user.display_name}")
        
        manager = KanbanManager(db, user.id)
        
        # Get columns
        backlog = session.query(KanbanColumn).filter_by(name="Backlog").first()
        todo = session.query(KanbanColumn).filter_by(name="To Do").first()
        in_progress = session.query(KanbanColumn).filter_by(name="In Progress").first()
        
        if not all([backlog, todo, in_progress]):
            print("❌ Required columns not found!")
            return False
        
        # Get all users for random assignment
        all_users = session.query(KanbanUser).filter_by(is_active=True).all()
        
        # Get groups
        groups = session.query(KanbanGroup).filter_by(is_active=True).all()
        
        priorities = ["low", "medium", "high", "critical"]
        
        print(f"\n📊 Creating tasks...")
        
        # 1. Create 35 tasks in Backlog (for pagination test)
        print(f"\n1️⃣ Creating 35 tasks in Backlog (pagination test)...")
        for i in range(1, 36):
            title = f"Backlog Task {i} - Test Pagination Feature"
            description = f"This is test task #{i} created for pagination testing. " \
                         f"When there are more than 30 tasks in a column, pagination should activate."
            
            # Random assignment
            assigned_user = random.choice(all_users) if random.random() > 0.3 else None
            assigned_group = random.choice(groups) if groups and random.random() > 0.5 else None
            priority = random.choice(priorities)
            
            # Random deadline (some overdue, some not)
            if random.random() > 0.5:
                days_offset = random.randint(-10, 30)
                deadline = (datetime.now() + timedelta(days=days_offset)).date()
            else:
                deadline = None
            
            task = manager.create_task(
                title=title,
                description=description,
                column_id=backlog.id,
                assigned_to=assigned_user.id if assigned_user else None,
                assigned_group_id=assigned_group.id if assigned_group else None,
                priority=priority,
                deadline=deadline
            )
            
            if i % 10 == 0:
                print(f"   Created {i}/35 tasks...")
        
        print(f"   ✅ Created 35 tasks in Backlog")
        
        # 2. Create 25 tasks in To Do (for compact view test)
        print(f"\n2️⃣ Creating 25 tasks in To Do (compact view test)...")
        for i in range(1, 26):
            title = f"To Do Task {i} - Test Compact View"
            description = f"Test task #{i} for compact view (20-50 tasks)."
            
            assigned_user = random.choice(all_users) if random.random() > 0.3 else None
            assigned_group = random.choice(groups) if groups and random.random() > 0.5 else None
            priority = random.choice(priorities)
            
            if random.random() > 0.5:
                days_offset = random.randint(-10, 30)
                deadline = (datetime.now() + timedelta(days=days_offset)).date()
            else:
                deadline = None
            
            task = manager.create_task(
                title=title,
                description=description,
                column_id=todo.id,
                assigned_to=assigned_user.id if assigned_user else None,
                assigned_group_id=assigned_group.id if assigned_group else None,
                priority=priority,
                deadline=deadline
            )
            
            if i % 10 == 0:
                print(f"   Created {i}/25 tasks...")
        
        print(f"   ✅ Created 25 tasks in To Do")
        
        # 3. Create 55 tasks in In Progress (for mini view test)
        print(f"\n3️⃣ Creating 55 tasks in In Progress (mini view test)...")
        for i in range(1, 56):
            title = f"In Progress Task {i} - Test Mini View"
            description = f"Test task #{i} for mini view (>50 tasks)."
            
            assigned_user = random.choice(all_users) if random.random() > 0.3 else None
            assigned_group = random.choice(groups) if groups and random.random() > 0.5 else None
            priority = random.choice(priorities)
            
            if random.random() > 0.5:
                days_offset = random.randint(-10, 30)
                deadline = (datetime.now() + timedelta(days=days_offset)).date()
            else:
                deadline = None
            
            task = manager.create_task(
                title=title,
                description=description,
                column_id=in_progress.id,
                assigned_to=assigned_user.id if assigned_user else None,
                assigned_group_id=assigned_group.id if assigned_group else None,
                priority=priority,
                deadline=deadline
            )
            
            if i % 10 == 0:
                print(f"   Created {i}/55 tasks...")
        
        print(f"   ✅ Created 55 tasks in In Progress")
        
        # Summary
        print(f"\n" + "="*60)
        print("✅ TEST TASKS CREATED SUCCESSFULLY!")
        print("="*60)
        
        print(f"\n📊 Summary:")
        print(f"   Backlog: 35 tasks → Pagination should activate (>30)")
        print(f"   To Do: 25 tasks → Compact view (20-50)")
        print(f"   In Progress: 55 tasks → Mini view (>50)")
        
        print(f"\n🎯 What to test:")
        print(f"   1. Go to Kanban Board")
        print(f"   2. Backlog column:")
        print(f"      - Should show 'Showing 20 of 35'")
        print(f"      - Click 'Load More' → Shows 'Showing 40 of 35' or all")
        print(f"      - Click 'View All' → Shows all 35 tasks")
        print(f"   3. To Do column:")
        print(f"      - Should use Compact view (smaller cards)")
        print(f"   4. In Progress column:")
        print(f"      - Should use Mini view (single line cards)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating test tasks: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()


if __name__ == "__main__":
    success = create_test_tasks()
    
    if success:
        print(f"\n🎉 All done! Start the app with: python main.py")
    else:
        print(f"\n⚠️ Failed to create test tasks. Check errors above.")
    
    sys.exit(0 if success else 1)





