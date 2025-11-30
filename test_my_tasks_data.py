"""Test script to diagnose My Tasks data issue.

This script checks:
1. User authentication
2. Tasks assigned to user
3. Tasks created by user
4. Overdue tasks
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime
from kanban.database import get_db_manager
from kanban.models import KanbanTask, KanbanUser
from sqlalchemy.orm import joinedload


def test_my_tasks_data():
    """Test My Tasks data retrieval."""
    print("\n" + "="*60)
    print("MY TASKS DATA DIAGNOSTIC")
    print("="*60)
    
    db = get_db_manager()
    session = db.get_session()
    
    try:
        # Get the user (admin or specific user)
        print("\n1️⃣ Finding User...")
        user = session.query(KanbanUser).filter_by(username="kenyi.seen", is_active=True).first()
        
        if not user:
            print("   ❌ User 'kenyi.seen' not found!")
            print("   Available users:")
            all_users = session.query(KanbanUser).filter_by(is_active=True).all()
            for u in all_users:
                print(f"      - {u.username} (ID: {u.id}, Role: {u.role})")
            return False
        
        print(f"   ✅ User found: {user.display_name} (ID: {user.id}, Role: {user.role})")
        
        # Check assigned tasks
        print(f"\n2️⃣ Checking Tasks Assigned to User {user.id}...")
        assigned_tasks = (
            session.query(KanbanTask)
            .options(joinedload(KanbanTask.column), joinedload(KanbanTask.assignee))
            .filter_by(assigned_to=user.id, is_deleted=False)
            .all()
        )
        
        print(f"   Found {len(assigned_tasks)} assigned tasks")
        if assigned_tasks:
            for task in assigned_tasks[:5]:
                column_name = task.column.name if task.column else "No column"
                print(f"      - {task.task_number}: {task.title} [{column_name}]")
            if len(assigned_tasks) > 5:
                print(f"      ... and {len(assigned_tasks) - 5} more")
        else:
            print("   ⚠️ No tasks assigned to this user")
        
        # Check created tasks
        print(f"\n3️⃣ Checking Tasks Created by User {user.id}...")
        created_tasks = (
            session.query(KanbanTask)
            .options(joinedload(KanbanTask.column), joinedload(KanbanTask.creator))
            .filter_by(created_by=user.id, is_deleted=False)
            .all()
        )
        
        print(f"   Found {len(created_tasks)} created tasks")
        if created_tasks:
            for task in created_tasks[:5]:
                column_name = task.column.name if task.column else "No column"
                assignee_name = task.assignee.display_name if task.assignee else "Unassigned"
                print(f"      - {task.task_number}: {task.title} [{column_name}] → {assignee_name}")
            if len(created_tasks) > 5:
                print(f"      ... and {len(created_tasks) - 5} more")
        else:
            print("   ⚠️ No tasks created by this user")
        
        # Check overdue tasks
        print(f"\n4️⃣ Checking Overdue Tasks for User {user.id}...")
        all_tasks = (
            session.query(KanbanTask)
            .options(joinedload(KanbanTask.column))
            .filter_by(assigned_to=user.id, is_deleted=False)
            .all()
        )
        
        overdue_tasks = [t for t in all_tasks if t.is_overdue]
        
        print(f"   Found {len(overdue_tasks)} overdue tasks")
        if overdue_tasks:
            today = datetime.now().date()
            for task in overdue_tasks[:5]:
                if task.deadline:
                    days_overdue = (today - task.deadline).days
                    column_name = task.column.name if task.column else "No column"
                    print(f"      - {task.task_number}: {task.title}")
                    print(f"        Due: {task.deadline}, {days_overdue} days overdue [{column_name}]")
            if len(overdue_tasks) > 5:
                print(f"      ... and {len(overdue_tasks) - 5} more")
        else:
            print("   ✅ No overdue tasks (excellent!)")
        
        # Check all tasks in database
        print(f"\n5️⃣ Database Summary...")
        total_tasks = session.query(KanbanTask).filter_by(is_deleted=False).count()
        assigned_to_anyone = session.query(KanbanTask).filter(KanbanTask.assigned_to.isnot(None), KanbanTask.is_deleted == False).count()
        unassigned = session.query(KanbanTask).filter_by(assigned_to=None, is_deleted=False).count()
        
        print(f"   Total tasks: {total_tasks}")
        print(f"   Assigned to someone: {assigned_to_anyone}")
        print(f"   Unassigned: {unassigned}")
        
        # Summary
        print(f"\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        
        if assigned_tasks or created_tasks or overdue_tasks:
            print(f"✅ User has tasks:")
            print(f"   - Assigned: {len(assigned_tasks)}")
            print(f"   - Created: {len(created_tasks)}")
            print(f"   - Overdue: {len(overdue_tasks)}")
            print(f"\n   If My Tasks tab shows 'No records', the issue is likely:")
            print(f"   1. Session/auth not being passed correctly")
            print(f"   2. UI not refreshing on login")
            print(f"   3. Filters clearing the results")
        else:
            print(f"⚠️ User has NO tasks!")
            print(f"\n   To fix:")
            print(f"   1. Assign some existing tasks to {user.display_name}")
            print(f"   2. Or create new tasks and assign to this user")
            print(f"   3. Run: python create_test_tasks.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()


if __name__ == "__main__":
    success = test_my_tasks_data()
    sys.exit(0 if success else 1)

