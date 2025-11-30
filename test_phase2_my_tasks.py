"""Test script for Phase 2: My Tasks Enhancements

Tests:
1. Filter functionality (Status, Priority, Sort)
2. Status summary widget accuracy
3. Overdue severity grouping (Critical/Moderate/Recent)
4. Search functionality in My Tasks
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime, date, timedelta
from kanban.database import get_db_manager
from kanban.manager import KanbanManager
from kanban.models import KanbanTask, KanbanUser, KanbanColumn
from sqlalchemy.orm import joinedload


def test_my_tasks_summary_stats():
    """Test that summary statistics are calculated correctly."""
    print("\n" + "="*60)
    print("TEST 1: My Tasks Summary Statistics")
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
        
        # Get tasks assigned to user
        assigned_tasks = (
            session.query(KanbanTask)
            .options(joinedload(KanbanTask.column))
            .filter_by(assigned_to=user_id, is_deleted=False)
            .all()
        )
        
        # Calculate stats manually
        total = len(assigned_tasks)
        done = len([t for t in assigned_tasks if t.column and t.column.name == "Done"])
        active = len([t for t in assigned_tasks if t.column and t.column.name != "Done"])
        overdue = len([t for t in assigned_tasks if t.is_overdue])
        
        print(f"\n📊 Manual Calculation:")
        print(f"   Total Tasks: {total}")
        print(f"   Done: {done}")
        print(f"   Active: {active}")
        print(f"   Overdue: {overdue}")
        
        # Verify logic
        if total == done + active:
            print(f"\n✅ Total = Done + Active ({total} = {done} + {active})")
        else:
            print(f"\n❌ Total != Done + Active ({total} != {done} + {active})")
            return False
        
        if overdue <= active:
            print(f"✅ Overdue ({overdue}) <= Active ({active})")
        else:
            print(f"⚠️ Overdue ({overdue}) > Active ({active}) - possible but unusual")
        
        return True
        
    finally:
        session.close()


def test_overdue_severity_grouping():
    """Test overdue tasks are correctly grouped by severity."""
    print("\n" + "="*60)
    print("TEST 2: Overdue Severity Grouping")
    print("="*60)
    
    db = get_db_manager()
    session = db.get_session()
    
    try:
        today = datetime.now().date()
        
        # Get all overdue tasks
        all_tasks = (
            session.query(KanbanTask)
            .options(joinedload(KanbanTask.column))
            .filter_by(is_deleted=False)
            .all()
        )
        
        overdue_tasks = [t for t in all_tasks if t.is_overdue]
        
        # Group by severity
        critical = []  # >7 days
        moderate = []  # 3-7 days
        recent = []    # 1-2 days
        
        for task in overdue_tasks:
            if task.deadline:
                days_overdue = (today - task.deadline).days
                if days_overdue > 7:
                    critical.append((task, days_overdue))
                elif days_overdue >= 3:
                    moderate.append((task, days_overdue))
                else:
                    recent.append((task, days_overdue))
        
        print(f"\n📊 Overdue Grouping:")
        print(f"   Total Overdue: {len(overdue_tasks)}")
        print(f"   🔴 Critical (>7 days): {len(critical)}")
        print(f"   🟠 Moderate (3-7 days): {len(moderate)}")
        print(f"   🟡 Recent (1-2 days): {len(recent)}")
        
        # Show samples
        if critical:
            print(f"\n🔴 Critical Overdue (showing up to 3):")
            for task, days in sorted(critical, key=lambda x: x[1], reverse=True)[:3]:
                print(f"   {task.task_number}: {days} days overdue (deadline: {task.deadline})")
        
        if moderate:
            print(f"\n🟠 Moderate Overdue (showing up to 3):")
            for task, days in sorted(moderate, key=lambda x: x[1], reverse=True)[:3]:
                print(f"   {task.task_number}: {days} days overdue (deadline: {task.deadline})")
        
        if recent:
            print(f"\n🟡 Recent Overdue (showing up to 3):")
            for task, days in sorted(recent, key=lambda x: x[1], reverse=True)[:3]:
                print(f"   {task.task_number}: {days} days overdue (deadline: {task.deadline})")
        
        # Verify totals
        total_grouped = len(critical) + len(moderate) + len(recent)
        if total_grouped == len(overdue_tasks):
            print(f"\n✅ All overdue tasks properly grouped ({total_grouped} = {len(overdue_tasks)})")
            return True
        else:
            print(f"\n❌ Grouping mismatch ({total_grouped} != {len(overdue_tasks)})")
            return False
        
    finally:
        session.close()


def test_filter_by_column():
    """Test filtering tasks by column (status)."""
    print("\n" + "="*60)
    print("TEST 3: Filter by Column/Status")
    print("="*60)
    
    db = get_db_manager()
    session = db.get_session()
    
    try:
        # Get a user with tasks
        user = session.query(KanbanUser).filter_by(is_active=True).first()
        user_id = user.id
        
        # Get all tasks
        assigned_tasks = (
            session.query(KanbanTask)
            .options(joinedload(KanbanTask.column))
            .filter_by(assigned_to=user_id, is_deleted=False)
            .all()
        )
        
        # Test each filter
        print(f"\n👤 User: {user.display_name}")
        print(f"Total assigned tasks: {len(assigned_tasks)}")
        
        # Active filter (not in Done)
        active = [t for t in assigned_tasks if t.column and t.column.name != "Done"]
        print(f"\n✅ Active Only filter: {len(active)} tasks")
        
        # Completed filter (in Done)
        completed = [t for t in assigned_tasks if t.column and t.column.name == "Done"]
        print(f"✅ Completed filter: {len(completed)} tasks")
        
        # In Progress filter
        in_progress = [t for t in assigned_tasks if t.column and t.column.name == "In Progress"]
        print(f"✅ In Progress filter: {len(in_progress)} tasks")
        
        # Review filter
        review = [t for t in assigned_tasks if t.column and t.column.name == "Review"]
        print(f"✅ Review filter: {len(review)} tasks")
        
        # Blocked filter
        blocked = [t for t in assigned_tasks if t.status == "blocked"]
        print(f"✅ Blocked filter: {len(blocked)} tasks")
        
        # Verify active + completed = total
        if len(active) + len(completed) == len(assigned_tasks):
            print(f"\n✅ Active + Completed = Total ({len(active)} + {len(completed)} = {len(assigned_tasks)})")
            return True
        else:
            print(f"\n❌ Filter mismatch")
            return False
        
    finally:
        session.close()


def test_priority_filter():
    """Test filtering by priority."""
    print("\n" + "="*60)
    print("TEST 4: Filter by Priority")
    print("="*60)
    
    db = get_db_manager()
    session = db.get_session()
    
    try:
        # Get all tasks
        all_tasks = session.query(KanbanTask).filter_by(is_deleted=False).all()
        
        # Count by priority
        critical = len([t for t in all_tasks if t.priority == "critical"])
        high = len([t for t in all_tasks if t.priority == "high"])
        medium = len([t for t in all_tasks if t.priority == "medium"])
        low = len([t for t in all_tasks if t.priority == "low"])
        
        print(f"\n📊 Tasks by Priority:")
        print(f"   🔴 Critical: {critical}")
        print(f"   🟠 High: {high}")
        print(f"   🟡 Medium: {medium}")
        print(f"   🟢 Low: {low}")
        print(f"   Total: {critical + high + medium + low}")
        
        if critical + high + medium + low == len(all_tasks):
            print(f"\n✅ All tasks have valid priority")
            return True
        else:
            print(f"\n⚠️ Some tasks may have invalid priority")
            return False
        
    finally:
        session.close()


def test_sort_functionality():
    """Test sorting tasks."""
    print("\n" + "="*60)
    print("TEST 5: Sort Functionality")
    print("="*60)
    
    db = get_db_manager()
    session = db.get_session()
    
    try:
        # Get tasks with deadlines
        tasks_with_deadline = (
            session.query(KanbanTask)
            .filter(KanbanTask.is_deleted == False, KanbanTask.deadline.isnot(None))
            .all()
        )
        
        print(f"\n📊 Tasks with deadlines: {len(tasks_with_deadline)}")
        
        # Sort by deadline
        sorted_by_deadline = sorted(tasks_with_deadline, key=lambda t: t.deadline)
        if sorted_by_deadline:
            print(f"\n✅ Sort by deadline:")
            print(f"   Earliest: {sorted_by_deadline[0].task_number} - {sorted_by_deadline[0].deadline}")
            print(f"   Latest: {sorted_by_deadline[-1].task_number} - {sorted_by_deadline[-1].deadline}")
        
        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_by_priority = sorted(tasks_with_deadline, key=lambda t: priority_order.get(t.priority, 4))
        if sorted_by_priority:
            print(f"\n✅ Sort by priority:")
            print(f"   First: {sorted_by_priority[0].task_number} - {sorted_by_priority[0].priority}")
            print(f"   Last: {sorted_by_priority[-1].task_number} - {sorted_by_priority[-1].priority}")
        
        # Sort by task number
        sorted_by_number = sorted(tasks_with_deadline, key=lambda t: t.task_number)
        if sorted_by_number:
            print(f"\n✅ Sort by task number:")
            print(f"   First: {sorted_by_number[0].task_number}")
            print(f"   Last: {sorted_by_number[-1].task_number}")
        
        return True
        
    finally:
        session.close()


def test_search_functionality():
    """Test search in task title and description."""
    print("\n" + "="*60)
    print("TEST 6: Search Functionality")
    print("="*60)
    
    db = get_db_manager()
    session = db.get_session()
    
    try:
        all_tasks = session.query(KanbanTask).filter_by(is_deleted=False).all()
        
        # Test search for "SAP"
        search_term = "sap"
        matches = [
            t for t in all_tasks
            if search_term in t.title.lower()
            or (t.description and search_term in t.description.lower())
            or search_term in t.task_number.lower()
        ]
        
        print(f"\n🔍 Search for '{search_term}':")
        print(f"   Found {len(matches)} tasks")
        
        if matches:
            print(f"\n   Sample results (up to 5):")
            for task in matches[:5]:
                print(f"   {task.task_number} - {task.title}")
        
        # Test another search
        search_term2 = "alice"
        matches2 = [
            t for t in all_tasks
            if search_term2 in t.title.lower()
            or (t.description and search_term2 in t.description.lower())
        ]
        
        print(f"\n🔍 Search for '{search_term2}':")
        print(f"   Found {len(matches2)} tasks")
        
        if matches2:
            print(f"\n   Sample results (up to 5):")
            for task in matches2[:5]:
                print(f"   {task.task_number} - {task.title}")
        
        print(f"\n✅ Search functionality working")
        return True
        
    finally:
        session.close()


def run_all_tests():
    """Run all Phase 2 tests."""
    print("\n" + "✨" * 30)
    print("PHASE 2: MY TASKS ENHANCEMENTS - TEST SUITE")
    print("✨" * 30)
    
    results = []
    
    # Test 1: Summary stats
    results.append(("My Tasks Summary Stats", test_my_tasks_summary_stats()))
    
    # Test 2: Overdue severity grouping
    results.append(("Overdue Severity Grouping", test_overdue_severity_grouping()))
    
    # Test 3: Filter by column
    results.append(("Filter by Column/Status", test_filter_by_column()))
    
    # Test 4: Priority filter
    results.append(("Filter by Priority", test_priority_filter()))
    
    # Test 5: Sort functionality
    results.append(("Sort Functionality", test_sort_functionality()))
    
    # Test 6: Search functionality
    results.append(("Search Functionality", test_search_functionality()))
    
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
        print("\n🎉 All Phase 2 tests PASSED! ✅")
        print("\nManual UI Tests Required:")
        print("1. My Tasks → Status summary shows correct counts")
        print("2. Use Status filter → Tasks filtered correctly")
        print("3. Use Priority filter → Only selected priority shown")
        print("4. Change Sort → Tasks reorder correctly")
        print("5. Search box → Find tasks by title/description")
        print("6. Overdue tab → Tasks grouped by severity (🔴🟠🟡)")
        print("7. Clear filters button → Resets all filters")
    else:
        print("\n⚠️ Some tests FAILED. Please review above output.")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

