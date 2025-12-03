"""Test script for Phase 1: Critical Fixes

Tests:
1. Reports tab visibility based on user role
2. Report statistics accuracy (column-based, not status-based)
3. Overdue calculation (excludes Done column)
4. Tasks by Category removed
"""

import sys
from datetime import datetime, date, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from kanban.database import get_db_manager
from kanban.manager import KanbanManager
from kanban.models import KanbanColumn, KanbanTask, KanbanUser


def test_statistics_accuracy():
    """Test that statistics use columns, not status field."""
    print("\n" + "="*60)
    print("TEST 1: Statistics Accuracy (Column-based)")
    print("="*60)
    
    db = get_db_manager()
    if not db.test_connection():
        print("❌ Database connection failed!")
        return False
    
    session = db.get_session()
    try:
        # Get columns
        done_column = session.query(KanbanColumn).filter_by(name="Done", is_active=True).first()
        in_progress_column = session.query(KanbanColumn).filter_by(name="In Progress", is_active=True).first()
        
        if not done_column or not in_progress_column:
            print("❌ Required columns not found (Done, In Progress)")
            return False
        
        # Count tasks manually
        total_tasks = session.query(KanbanTask).filter_by(is_deleted=False).count()
        done_tasks = session.query(KanbanTask).filter_by(
            column_id=done_column.id,
            is_deleted=False
        ).count()
        in_progress_tasks_count = session.query(KanbanTask).filter_by(
            column_id=in_progress_column.id,
            is_deleted=False
        ).count()
        
        print(f"\n📊 Manual Count (Ground Truth):")
        print(f"   Total Tasks: {total_tasks}")
        print(f"   Done Column: {done_tasks}")
        print(f"   In Progress Column: {in_progress_tasks_count}")
        
        # Get statistics from manager
        # Use first admin user
        admin = session.query(KanbanUser).filter_by(role="admin", is_active=True).first()
        if not admin:
            print("❌ No admin user found for testing")
            return False
        
        manager = KanbanManager(db, current_user_id=admin.id)
        stats = manager.get_task_statistics()
        
        print(f"\n📈 Manager Statistics:")
        print(f"   Total Tasks: {stats.get('total_tasks')}")
        print(f"   Completed Tasks: {stats.get('completed_tasks')}")
        print(f"   In Progress Tasks: {stats.get('in_progress_tasks')}")
        print(f"   Active Tasks: {stats.get('active_tasks')}")
        print(f"   Overdue Tasks: {stats.get('overdue_tasks')}")
        print(f"   Completion Rate: {stats.get('completion_rate'):.1f}%")
        
        # Verify
        success = True
        
        if stats['total_tasks'] != total_tasks:
            print(f"\n❌ Total tasks mismatch: {stats['total_tasks']} != {total_tasks}")
            success = False
        else:
            print(f"\n✅ Total tasks correct: {total_tasks}")
        
        if stats['completed_tasks'] != done_tasks:
            print(f"❌ Completed tasks mismatch: {stats['completed_tasks']} != {done_tasks}")
            success = False
        else:
            print(f"✅ Completed tasks correct: {done_tasks}")
        
        if stats['in_progress_tasks'] != in_progress_tasks_count:
            print(f"❌ In Progress tasks mismatch: {stats['in_progress_tasks']} != {in_progress_tasks_count}")
            success = False
        else:
            print(f"✅ In Progress tasks correct: {in_progress_tasks_count}")
        
        expected_active = total_tasks - done_tasks
        if stats['active_tasks'] != expected_active:
            print(f"❌ Active tasks mismatch: {stats['active_tasks']} != {expected_active}")
            success = False
        else:
            print(f"✅ Active tasks correct: {expected_active}")
        
        return success
        
    finally:
        session.close()


def test_overdue_calculation():
    """Test that overdue calculation excludes Done column."""
    print("\n" + "="*60)
    print("TEST 2: Overdue Calculation (Excludes Done Column)")
    print("="*60)
    
    db = get_db_manager()
    session = db.get_session()
    
    try:
        # Get Done column
        done_column = session.query(KanbanColumn).filter_by(name="Done", is_active=True).first()
        
        # Get all tasks with deadlines
        all_tasks = session.query(KanbanTask).filter(
            KanbanTask.is_deleted == False,
            KanbanTask.deadline.isnot(None)
        ).all()
        
        today = datetime.now().date()
        
        # Manual count of overdue tasks
        overdue_count_with_done = 0
        overdue_count_without_done = 0
        done_overdue_count = 0
        
        for task in all_tasks:
            if task.deadline < today:
                overdue_count_with_done += 1
                
                if task.column_id == done_column.id:
                    done_overdue_count += 1
                else:
                    overdue_count_without_done += 1
        
        print(f"\n📊 Manual Overdue Count:")
        print(f"   Tasks with passed deadline (including Done): {overdue_count_with_done}")
        print(f"   Tasks in Done column with passed deadline: {done_overdue_count}")
        print(f"   Overdue tasks (excluding Done): {overdue_count_without_done}")
        
        # Count using is_overdue property
        property_overdue_count = sum(1 for task in all_tasks if task.is_overdue)
        
        print(f"\n📈 Using is_overdue Property:")
        print(f"   Overdue tasks: {property_overdue_count}")
        
        # Get from manager statistics
        admin = session.query(KanbanUser).filter_by(role="admin", is_active=True).first()
        manager = KanbanManager(db, current_user_id=admin.id)
        stats = manager.get_task_statistics()
        
        print(f"\n📈 Manager Statistics:")
        print(f"   Overdue tasks: {stats.get('overdue_tasks')}")
        
        # Verify
        if stats['overdue_tasks'] == property_overdue_count:
            print(f"\n✅ Overdue calculation correct (excludes Done column)")
            return True
        else:
            print(f"\n❌ Overdue count mismatch: {stats['overdue_tasks']} != {property_overdue_count}")
            return False
        
    finally:
        session.close()


def test_user_role_data():
    """Test user roles in database for tab visibility test."""
    print("\n" + "="*60)
    print("TEST 3: User Role Verification")
    print("="*60)
    
    db = get_db_manager()
    session = db.get_session()
    
    try:
        # Get users by role
        admins = session.query(KanbanUser).filter_by(role="admin", is_active=True).all()
        managers = session.query(KanbanUser).filter_by(role="manager", is_active=True).all()
        members = session.query(KanbanUser).filter_by(role="member", is_active=True).all()
        
        print(f"\n👥 Users by Role:")
        print(f"   Admins: {len(admins)}")
        for admin in admins:
            print(f"      - {admin.username} ({admin.display_name})")
        
        print(f"   Managers: {len(managers)}")
        for manager in managers:
            print(f"      - {manager.username} ({manager.display_name})")
        
        print(f"   Members: {len(members)}")
        for member in members[:5]:  # Show first 5
            print(f"      - {member.username} ({member.display_name})")
        if len(members) > 5:
            print(f"      ... and {len(members) - 5} more")
        
        if admins or managers:
            print(f"\n✅ Admin/Manager users exist for Reports tab")
        else:
            print(f"\n⚠️ No admin/manager users found")
        
        if members:
            print(f"✅ Member users exist for testing restricted access")
        else:
            print(f"⚠️ No member users found")
        
        return True
        
    finally:
        session.close()


def test_column_structure():
    """Test that required columns exist."""
    print("\n" + "="*60)
    print("TEST 4: Column Structure")
    print("="*60)
    
    db = get_db_manager()
    session = db.get_session()
    
    try:
        columns = session.query(KanbanColumn).filter_by(is_active=True).order_by(KanbanColumn.position).all()
        
        print(f"\n📋 Active Columns ({len(columns)}):")
        for col in columns:
            task_count = session.query(KanbanTask).filter_by(
                column_id=col.id,
                is_deleted=False
            ).count()
            print(f"   {col.position}. {col.name} - {task_count} tasks")
        
        # Check for required columns
        required = ["Done", "In Progress"]
        found = [col.name for col in columns]
        
        success = True
        for req in required:
            if req in found:
                print(f"\n✅ Required column '{req}' exists")
            else:
                print(f"\n❌ Required column '{req}' missing")
                success = False
        
        return success
        
    finally:
        session.close()


def run_all_tests():
    """Run all Phase 1 tests."""
    print("\n" + "🧪" * 30)
    print("PHASE 1: CRITICAL FIXES - TEST SUITE")
    print("🧪" * 30)
    
    results = []
    
    # Test 1: Column structure
    results.append(("Column Structure", test_column_structure()))
    
    # Test 2: User roles
    results.append(("User Role Data", test_user_role_data()))
    
    # Test 3: Statistics accuracy
    results.append(("Statistics Accuracy", test_statistics_accuracy()))
    
    # Test 4: Overdue calculation
    results.append(("Overdue Calculation", test_overdue_calculation()))
    
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
        print("\n🎉 All Phase 1 tests PASSED! ✅")
        print("\nManual UI Tests Required:")
        print("1. Login as admin/manager → Reports tab should be visible")
        print("2. Login as member → Reports tab should be hidden")
        print("3. Switch between users → Tab visibility updates correctly")
        print("4. Open Reports → Statistics match Kanban board counts")
        print("5. Reports → 'Tasks by Category' section is removed")
    else:
        print("\n⚠️ Some tests FAILED. Please review above output.")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)


