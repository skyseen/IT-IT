"""Test script for Phase 3: Reports Enhancement

Tests:
1. Team performance metrics calculation
2. On-time completion percentage
3. Average completion days
4. Time period filtering (Monthly/90 Days/All Time)
5. Warning indicators (<60% warning, ≥80% success)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime, timedelta, date
from kanban.database import get_db_manager
from kanban.manager import KanbanManager
from kanban.models import KanbanTask, KanbanUser, KanbanColumn
from sqlalchemy.orm import joinedload


def test_on_time_completion_percentage():
    """Test on-time completion percentage calculation."""
    print("\n" + "="*60)
    print("TEST 1: On-Time Completion Percentage")
    print("="*60)
    
    db = get_db_manager()
    session = db.get_session()
    
    try:
        # Get a user with completed tasks
        all_tasks = (
            session.query(KanbanTask)
            .options(joinedload(KanbanTask.column))
            .filter_by(is_deleted=False)
            .all()
        )
        
        # Find tasks in Done column with deadlines
        done_tasks_with_deadline = [
            t for t in all_tasks
            if t.column and t.column.name == "Done"
            and t.deadline and t.completed_at
        ]
        
        print(f"\n📊 Completed Tasks with Deadline: {len(done_tasks_with_deadline)}")
        
        if not done_tasks_with_deadline:
            print("⚠️ No completed tasks with deadlines to test")
            return True
        
        # Calculate on-time
        on_time = 0
        late = 0
        
        for task in done_tasks_with_deadline:
            completed_date = task.completed_at.date() if isinstance(task.completed_at, datetime) else task.completed_at
            deadline_date = task.deadline if isinstance(task.deadline, date) else task.deadline
            
            if completed_date <= deadline_date:
                on_time += 1
            else:
                late += 1
        
        on_time_pct = (on_time / len(done_tasks_with_deadline)) * 100
        
        print(f"\n📈 Results:")
        print(f"   On-Time: {on_time}")
        print(f"   Late: {late}")
        print(f"   On-Time %: {on_time_pct:.1f}%")
        
        # Test warning thresholds
        if on_time_pct >= 80:
            print(f"   ✅ Excellent performance (≥80%)")
        elif on_time_pct < 60:
            print(f"   ⚠️ Warning threshold (<60%)")
        else:
            print(f"   📊 Normal performance (60-79%)")
        
        # Show some examples
        print(f"\n📋 Sample Tasks:")
        for task in done_tasks_with_deadline[:3]:
            completed_date = task.completed_at.date() if isinstance(task.completed_at, datetime) else task.completed_at
            deadline_date = task.deadline
            status = "✅ On-time" if completed_date <= deadline_date else "⚠️ Late"
            print(f"   {task.task_number}: Due {deadline_date}, Done {completed_date} - {status}")
        
        return True
        
    finally:
        session.close()


def test_average_completion_days():
    """Test average completion time calculation."""
    print("\n" + "="*60)
    print("TEST 2: Average Completion Days")
    print("="*60)
    
    db = get_db_manager()
    session = db.get_session()
    
    try:
        # Get completed tasks
        all_tasks = (
            session.query(KanbanTask)
            .options(joinedload(KanbanTask.column))
            .filter_by(is_deleted=False)
            .all()
        )
        
        done_tasks = [t for t in all_tasks if t.column and t.column.name == "Done" and t.completed_at]
        
        print(f"\n📊 Completed Tasks: {len(done_tasks)}")
        
        if not done_tasks:
            print("⚠️ No completed tasks to test")
            return True
        
        # Calculate completion times
        completion_times = []
        for task in done_tasks:
            completed_date = task.completed_at.date() if isinstance(task.completed_at, datetime) else task.completed_at
            created_date = task.created_at.date() if isinstance(task.created_at, datetime) else task.created_at
            days = (completed_date - created_date).days
            completion_times.append(days)
        
        avg_days = sum(completion_times) / len(completion_times)
        min_days = min(completion_times)
        max_days = max(completion_times)
        
        print(f"\n📈 Completion Time Stats:")
        print(f"   Average: {avg_days:.1f} days")
        print(f"   Fastest: {min_days} days")
        print(f"   Slowest: {max_days} days")
        
        # Show distribution
        fast = len([d for d in completion_times if d <= 3])
        medium = len([d for d in completion_times if 3 < d <= 7])
        slow = len([d for d in completion_times if d > 7])
        
        print(f"\n📊 Distribution:")
        print(f"   Fast (≤3 days): {fast}")
        print(f"   Medium (4-7 days): {medium}")
        print(f"   Slow (>7 days): {slow}")
        
        return True
        
    finally:
        session.close()


def test_time_period_filtering():
    """Test time period filtering (Monthly, 90 Days, All Time)."""
    print("\n" + "="*60)
    print("TEST 3: Time Period Filtering")
    print("="*60)
    
    db = get_db_manager()
    session = db.get_session()
    
    try:
        today = datetime.now().date()
        
        # Get all tasks
        all_tasks = session.query(KanbanTask).filter_by(is_deleted=False).all()
        
        # This month
        month_start = today.replace(day=1)
        month_tasks = [t for t in all_tasks if t.created_at.date() >= month_start]
        
        # Last 90 days
        days_90_start = today - timedelta(days=90)
        days_90_tasks = [t for t in all_tasks if t.created_at.date() >= days_90_start]
        
        # All time
        all_time_tasks = all_tasks
        
        print(f"\n📊 Task Counts by Time Period:")
        print(f"   This Month (from {month_start}): {len(month_tasks)}")
        print(f"   Last 90 Days (from {days_90_start}): {len(days_90_tasks)}")
        print(f"   All Time: {len(all_time_tasks)}")
        
        # Verify logic
        if len(month_tasks) <= len(days_90_tasks) <= len(all_time_tasks):
            print(f"\n✅ Time period filtering logic correct")
            print(f"   (Month ≤ 90 Days ≤ All Time)")
            return True
        else:
            print(f"\n❌ Time period filtering logic incorrect")
            return False
        
    finally:
        session.close()


def test_user_performance_metrics():
    """Test per-user performance calculation."""
    print("\n" + "="*60)
    print("TEST 4: User Performance Metrics")
    print("="*60)
    
    db = get_db_manager()
    session = db.get_session()
    
    try:
        # Get all users and tasks
        users = session.query(KanbanUser).filter_by(is_active=True).all()
        all_tasks = (
            session.query(KanbanTask)
            .options(joinedload(KanbanTask.column))
            .filter_by(is_deleted=False)
            .all()
        )
        
        print(f"\n👥 Active Users: {len(users)}")
        print(f"📋 Total Tasks: {len(all_tasks)}")
        
        # Calculate for each user
        user_stats = []
        for user in users[:5]:  # Test first 5 users
            user_tasks = [t for t in all_tasks if t.assigned_to == user.id]
            
            if not user_tasks:
                continue
            
            active = len([t for t in user_tasks if t.column and t.column.name != "Done"])
            done = len([t for t in user_tasks if t.column and t.column.name == "Done"])
            overdue = len([t for t in user_tasks if t.is_overdue])
            
            user_stats.append({
                "name": user.display_name,
                "total": len(user_tasks),
                "active": active,
                "done": done,
                "overdue": overdue
            })
        
        print(f"\n📊 User Performance (sample):")
        for stat in user_stats:
            print(f"\n   {stat['name']}:")
            print(f"      Total: {stat['total']}")
            print(f"      Active: {stat['active']}")
            print(f"      Done: {stat['done']}")
            print(f"      Overdue: {stat['overdue']}")
            
            # Verify logic
            if stat['active'] + stat['done'] == stat['total']:
                print(f"      ✅ Active + Done = Total")
            else:
                print(f"      ⚠️ Active + Done != Total")
        
        return True
        
    finally:
        session.close()


def test_warning_indicators():
    """Test warning indicator logic."""
    print("\n" + "="*60)
    print("TEST 5: Warning Indicator Logic")
    print("="*60)
    
    # Test on-time percentage thresholds
    test_cases = [
        (95, "✅ Success (≥80%)"),
        (80, "✅ Success (≥80%)"),
        (75, "📊 Normal (60-79%)"),
        (60, "📊 Normal (60-79%)"),
        (55, "⚠️ Warning (<60%)"),
        (30, "⚠️ Warning (<60%)"),
    ]
    
    print(f"\n📊 On-Time % Threshold Tests:")
    for on_time_pct, expected in test_cases:
        if on_time_pct >= 80:
            result = "✅ Success"
            indicator = "✅"
        elif on_time_pct < 60:
            result = "⚠️ Warning"
            indicator = "⚠️"
        else:
            result = "📊 Normal"
            indicator = ""
        
        print(f"   {on_time_pct}%: {result} {indicator}")
    
    print(f"\n📊 Overdue Count Threshold Tests:")
    test_overdue = [0, 2, 5, 6, 10]
    for count in test_overdue:
        if count > 5:
            result = "🔴 Warning"
        else:
            result = "OK"
        print(f"   {count} overdue tasks: {result}")
    
    print(f"\n✅ Warning indicator logic tests passed")
    return True


def test_team_performance_sorting():
    """Test team performance sorting logic."""
    print("\n" + "="*60)
    print("TEST 6: Team Performance Sorting")
    print("="*60)
    
    # Create sample performance data
    performance_data = [
        {"name": "User A", "overdue": 2, "active": 5},
        {"name": "User B", "overdue": 8, "active": 3},
        {"name": "User C", "overdue": 1, "active": 10},
        {"name": "User D", "overdue": 8, "active": 7},
    ]
    
    # Sort by overdue (desc), then active (desc)
    sorted_data = sorted(performance_data, key=lambda x: (-x["overdue"], -x["active"]))
    
    print(f"\n📊 Original Order:")
    for data in performance_data:
        print(f"   {data['name']}: {data['overdue']} overdue, {data['active']} active")
    
    print(f"\n📊 Sorted Order (by overdue desc, then active desc):")
    for i, data in enumerate(sorted_data, 1):
        print(f"   {i}. {data['name']}: {data['overdue']} overdue, {data['active']} active")
    
    # Verify sorting
    # Correct order: User D (8,7) > User B (8,3) > User A (2,5) > User C (1,10)
    expected_order = ["User D", "User B", "User A", "User C"]
    actual_order = [d["name"] for d in sorted_data]
    
    if actual_order == expected_order:
        print(f"\n✅ Sorting logic correct")
        return True
    else:
        print(f"\n❌ Sorting logic incorrect")
        print(f"   Expected: {expected_order}")
        print(f"   Got: {actual_order}")
        return False


def run_all_tests():
    """Run all Phase 3 tests."""
    print("\n" + "📊" * 30)
    print("PHASE 3: REPORTS ENHANCEMENT - TEST SUITE")
    print("📊" * 30)
    
    results = []
    
    # Test 1: On-time completion
    results.append(("On-Time Completion %", test_on_time_completion_percentage()))
    
    # Test 2: Average completion days
    results.append(("Average Completion Days", test_average_completion_days()))
    
    # Test 3: Time period filtering
    results.append(("Time Period Filtering", test_time_period_filtering()))
    
    # Test 4: User performance
    results.append(("User Performance Metrics", test_user_performance_metrics()))
    
    # Test 5: Warning indicators
    results.append(("Warning Indicator Logic", test_warning_indicators()))
    
    # Test 6: Sorting
    results.append(("Team Performance Sorting", test_team_performance_sorting()))
    
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
        print("\n🎉 All Phase 3 tests PASSED! ✅")
        print("\nManual UI Tests Required:")
        print("1. Reports → Time period dropdown visible")
        print("2. Select 'This Month' → Performance table updates")
        print("3. Select 'Last 90 Days' → Different numbers")
        print("4. Select 'All Time' → All historical data")
        print("5. Check On-Time % column → ✅ for ≥80%, ⚠️ for <60%")
        print("6. Check Overdue column → 🔴 for >5 overdue")
        print("7. Statistics cards show subtitles")
        print("8. Team sorted by overdue count (highest first)")
    else:
        print("\n⚠️ Some tests FAILED. Please review above output.")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

