"""Test bug fixes for logout state and overdue calculation."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime
from kanban.database import get_db_manager
from kanban.models import KanbanTask, KanbanColumn, KanbanUser
from kanban.manager import KanbanManager
from sqlalchemy.orm import joinedload


def test_overdue_excludes_done_column():
    """Test that overdue calculation correctly excludes Done column tasks."""
    print("\n" + "="*60)
    print("TEST: Overdue Calculation (My Tasks Logic)")
    print("="*60)
    
    db = get_db_manager()
    session = db.get_session()
    
    try:
        # Get Done column
        done_column = session.query(KanbanColumn).filter_by(name="Done", is_active=True).first()
        
        # Get all tasks with deadline < today
        today = datetime.now().date()
        tasks_with_passed_deadline = (
            session.query(KanbanTask)
            .options(joinedload(KanbanTask.column))
            .filter(
                KanbanTask.is_deleted == False,
                KanbanTask.deadline.isnot(None),
                KanbanTask.deadline < today
            )
            .all()
        )
        
        # Separate by Done vs Not Done
        done_tasks_with_passed_deadline = []
        overdue_tasks = []
        
        for task in tasks_with_passed_deadline:
            if task.column_id == done_column.id:
                done_tasks_with_passed_deadline.append(task)
            else:
                # Check using is_overdue property
                if task.is_overdue:
                    overdue_tasks.append(task)
        
        print(f"\n📊 Deadline Analysis:")
        print(f"   Total tasks with passed deadline: {len(tasks_with_passed_deadline)}")
        print(f"   Done column (completed late): {len(done_tasks_with_passed_deadline)}")
        print(f"   Actual overdue (using is_overdue): {len(overdue_tasks)}")
        
        print(f"\n📋 Done Column Tasks with Passed Deadline:")
        for task in done_tasks_with_passed_deadline:
            print(f"   {task.task_number} - {task.title}")
            print(f"      Deadline: {task.deadline} | Column: {task.column.name}")
            print(f"      is_overdue: {task.is_overdue} (should be False)")
        
        print(f"\n⚠️ Actually Overdue Tasks:")
        for task in overdue_tasks[:5]:  # Show first 5
            print(f"   {task.task_number} - {task.title}")
            print(f"      Deadline: {task.deadline} | Column: {task.column.name}")
            print(f"      is_overdue: {task.is_overdue} (should be True)")
        if len(overdue_tasks) > 5:
            print(f"   ... and {len(overdue_tasks) - 5} more")
        
        # Verify TASK-0005 specifically
        task_0005 = session.query(KanbanTask).filter_by(
            task_number="TASK-0005",
            is_deleted=False
        ).options(joinedload(KanbanTask.column)).first()
        
        if task_0005:
            print(f"\n🔍 TASK-0005 Verification:")
            print(f"   Column: {task_0005.column.name}")
            print(f"   Deadline: {task_0005.deadline}")
            print(f"   is_overdue: {task_0005.is_overdue}")
            
            if task_0005.column.name == "Done" and not task_0005.is_overdue:
                print(f"   ✅ TASK-0005 correctly NOT shown as overdue")
                return True
            else:
                print(f"   ❌ TASK-0005 incorrectly marked as overdue")
                return False
        else:
            print(f"\n⚠️ TASK-0005 not found for verification")
            return len(overdue_tasks) < len(tasks_with_passed_deadline)
        
    finally:
        session.close()


def test_my_tasks_overdue_logic():
    """Test the My Tasks overdue logic matches the fixed implementation."""
    print("\n" + "="*60)
    print("TEST: My Tasks Overdue Tab Logic")
    print("="*60)
    
    db = get_db_manager()
    session = db.get_session()
    
    try:
        # Get a user with tasks
        user = session.query(KanbanUser).filter_by(is_active=True).first()
        if not user:
            print("❌ No active user found")
            return False
        
        user_id = user.id
        print(f"\n👤 Testing with user: {user.display_name} (ID: {user_id})")
        
        # Get all tasks
        all_tasks = (
            session.query(KanbanTask)
            .options(joinedload(KanbanTask.column))
            .filter_by(is_deleted=False)
            .all()
        )
        
        # Apply My Tasks overdue logic (NEW FIXED VERSION)
        overdue_tasks = []
        for task in all_tasks:
            if (task.assigned_to == user_id and 
                task.is_overdue and  # Uses property which checks column
                not task.is_deleted):
                overdue_tasks.append(task)
        
        print(f"\n📋 Overdue Tasks for {user.display_name}:")
        print(f"   Count: {len(overdue_tasks)}")
        
        # Check none are in Done column
        done_column_count = 0
        for task in overdue_tasks:
            if task.column and task.column.name == "Done":
                done_column_count += 1
                print(f"   ❌ {task.task_number} is in Done but marked overdue!")
        
        if done_column_count == 0:
            print(f"   ✅ No Done column tasks in overdue list")
            return True
        else:
            print(f"   ❌ Found {done_column_count} Done tasks in overdue!")
            return False
        
    finally:
        session.close()


def run_all_tests():
    """Run all bug fix tests."""
    print("\n" + "🐛" * 30)
    print("BUG FIXES - TEST SUITE")
    print("🐛" * 30)
    
    results = []
    
    # Test 1: Overdue excludes Done
    results.append(("Overdue Excludes Done Column", test_overdue_excludes_done_column()))
    
    # Test 2: My Tasks overdue logic
    results.append(("My Tasks Overdue Logic", test_my_tasks_overdue_logic()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n{'='*60}")
    print(f"Results: {passed}/{total} tests passed")
    print(f"{'='*60}")
    
    if passed == total:
        print("\n🎉 All bug fix tests PASSED! ✅")
        print("\nManual UI Tests Required:")
        print("1. Logout → My Tasks and Reports should be empty")
        print("2. Try clicking tasks after logout → Should not crash")
        print("3. My Tasks → Overdue tab → TASK-0005 should NOT appear")
        print("4. Verify only tasks NOT in Done column appear as overdue")
    else:
        print("\n⚠️ Some tests FAILED. Please review above output.")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)





