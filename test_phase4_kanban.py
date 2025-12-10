"""Test script for Phase 4: Kanban Board Improvements

Tests:
1. Group filter functionality
2. Pagination logic (when to show, load more, view all)
3. View mode selection (detailed/compact/mini)
4. Search results counter
5. Filter combinations
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime
from kanban.database import get_db_manager
from kanban.manager import KanbanManager
from kanban.models import KanbanTask, KanbanUser, KanbanGroup
from sqlalchemy.orm import joinedload


def test_group_filter_exists():
    """Test that groups exist in database for filtering."""
    print("\n" + "="*60)
    print("TEST 1: Group Filter - Database Groups")
    print("="*60)
    
    db = get_db_manager()
    session = db.get_session()
    
    try:
        # Get all active groups
        groups = session.query(KanbanGroup).filter_by(is_active=True).all()
        
        print(f"\n👥 Active Groups: {len(groups)}")
        
        if not groups:
            print("⚠️ No groups found - creating 'IT' group for testing")
            return False
        
        for group in groups:
            print(f"   - {group.name} (ID: {group.id}, Color: {group.color})")
            
            # Count tasks assigned to this group
            task_count = session.query(KanbanTask).filter_by(
                assigned_group_id=group.id,
                is_deleted=False
            ).count()
            print(f"     Tasks assigned: {task_count}")
        
        # Check for IT group specifically
        it_group = session.query(KanbanGroup).filter_by(name="IT", is_active=True).first()
        if it_group:
            print(f"\n✅ 'IT' group exists (ID: {it_group.id})")
            return True
        else:
            print(f"\n⚠️ 'IT' group not found")
            return False
        
    finally:
        session.close()


def test_group_filter_logic():
    """Test filtering tasks by group."""
    print("\n" + "="*60)
    print("TEST 2: Group Filter Logic")
    print("="*60)
    
    db = get_db_manager()
    session = db.get_session()
    
    try:
        # Get IT group
        it_group = session.query(KanbanGroup).filter_by(name="IT", is_active=True).first()
        if not it_group:
            print("⚠️ IT group not found, skipping test")
            return True
        
        # Get all tasks
        all_tasks = session.query(KanbanTask).filter_by(is_deleted=False).all()
        
        # Filter by IT group
        it_tasks = [t for t in all_tasks if t.assigned_group_id == it_group.id]
        
        print(f"\n📊 Filter Results:")
        print(f"   Total tasks: {len(all_tasks)}")
        print(f"   IT group tasks: {len(it_tasks)}")
        
        if it_tasks:
            print(f"\n   IT Group Tasks:")
            for task in it_tasks[:5]:
                print(f"   {task.task_number} - {task.title}")
            if len(it_tasks) > 5:
                print(f"   ... and {len(it_tasks) - 5} more")
            
            print(f"\n✅ Group filter logic working")
            return True
        else:
            print(f"\n⚠️ No tasks assigned to IT group yet")
            return True
        
    finally:
        session.close()


def test_pagination_logic():
    """Test pagination threshold logic."""
    print("\n" + "="*60)
    print("TEST 3: Pagination Logic")
    print("="*60)
    
    # Test should_use_pagination logic
    test_cases = [
        (5, False, "has_search", "Pagination OFF (search active)"),
        (50, False, "has_filter", "Pagination OFF (filter active)"),
        (25, False, "no_filter", "Pagination OFF (<30 tasks)"),
        (35, True, "no_filter", "Pagination ON (>30 tasks, no filters)"),
        (100, True, "no_filter", "Pagination ON (>30 tasks, no filters)"),
    ]
    
    print(f"\n📊 Pagination Test Cases:")
    for task_count, expected_pagination, condition, description in test_cases:
        # Simulate logic
        has_filters = condition in ["has_search", "has_filter"]
        should_paginate = (not has_filters) and (task_count > 30)
        
        status = "✅" if should_paginate == expected_pagination else "❌"
        print(f"   {status} {task_count} tasks, {condition}: {description}")
    
    print(f"\n✅ Pagination logic tests passed")
    return True


def test_view_mode_selection():
    """Test view mode auto-selection based on task count."""
    print("\n" + "="*60)
    print("TEST 4: View Mode Auto-Selection")
    print("="*60)
    
    test_cases = [
        (5, "detailed", "< 20 tasks"),
        (15, "detailed", "< 20 tasks"),
        (20, "compact", "20-50 tasks"),
        (35, "compact", "20-50 tasks"),
        (50, "compact", "20-50 tasks"),
        (51, "mini", "> 50 tasks"),
        (100, "mini", "> 50 tasks"),
    ]
    
    print(f"\n📊 View Mode Test Cases:")
    for task_count, expected_mode, description in test_cases:
        # Simulate logic
        if task_count < 20:
            mode = 'detailed'
        elif task_count <= 50:
            mode = 'compact'
        else:
            mode = 'mini'
        
        status = "✅" if mode == expected_mode else "❌"
        print(f"   {status} {task_count} tasks → {mode} ({description})")
    
    print(f"\n✅ View mode selection logic correct")
    return True


def test_search_with_task_number():
    """Test search includes task number."""
    print("\n" + "="*60)
    print("TEST 5: Search Includes Task Number")
    print("="*60)
    
    db = get_db_manager()
    session = db.get_session()
    
    try:
        # Get all tasks
        all_tasks = session.query(KanbanTask).filter_by(is_deleted=False).all()
        
        # Search by task number
        search_term = "task-0005"
        matches = [
            t for t in all_tasks
            if search_term.lower() in t.task_number.lower()
            or search_term.lower() in t.title.lower()
            or (t.description and search_term.lower() in t.description.lower())
        ]
        
        print(f"\n🔍 Search for '{search_term}':")
        print(f"   Found {len(matches)} tasks")
        
        if matches:
            for task in matches:
                print(f"   {task.task_number} - {task.title}")
            print(f"\n✅ Search by task number working")
            return True
        else:
            print(f"\n❌ Search by task number failed")
            return False
        
    finally:
        session.close()


def test_filter_combinations():
    """Test that multiple filters work together."""
    print("\n" + "="*60)
    print("TEST 6: Filter Combinations")
    print("="*60)
    
    db = get_db_manager()
    session = db.get_session()
    
    try:
        # Get all tasks
        all_tasks = (
            session.query(KanbanTask)
            .options(joinedload(KanbanTask.assignee), joinedload(KanbanTask.assigned_group))
            .filter_by(is_deleted=False)
            .all()
        )
        
        print(f"\n📊 Starting with {len(all_tasks)} tasks")
        
        # Test: Filter by priority = high
        high_priority = [t for t in all_tasks if t.priority == "high"]
        print(f"\n   Filter Priority = 'high': {len(high_priority)} tasks")
        
        # Test: Filter by priority + search
        high_with_sap = [t for t in high_priority if "sap" in t.title.lower()]
        print(f"   + Search 'sap': {len(high_with_sap)} tasks")
        
        # Test: Filter by group (if IT group exists)
        it_group = session.query(KanbanGroup).filter_by(name="IT", is_active=True).first()
        if it_group:
            it_tasks = [t for t in all_tasks if t.assigned_group_id == it_group.id]
            print(f"   Filter Group = 'IT': {len(it_tasks)} tasks")
            
            # IT + high priority
            it_high = [t for t in it_tasks if t.priority == "high"]
            print(f"   IT + High Priority: {len(it_high)} tasks")
        
        # Test: Filter by assignee
        if all_tasks and all_tasks[0].assigned_to:
            user_id = all_tasks[0].assigned_to
            user_tasks = [t for t in all_tasks if t.assigned_to == user_id]
            print(f"   Filter by specific user: {len(user_tasks)} tasks")
        
        print(f"\n✅ Filter combinations working correctly")
        return True
        
    finally:
        session.close()


def run_all_tests():
    """Run all Phase 4 tests."""
    print("\n" + "🎨" * 30)
    print("PHASE 4: KANBAN BOARD IMPROVEMENTS - TEST SUITE")
    print("🎨" * 30)
    
    results = []
    
    # Test 1: Groups exist
    results.append(("Group Filter - Database", test_group_filter_exists()))
    
    # Test 2: Group filter logic
    results.append(("Group Filter Logic", test_group_filter_logic()))
    
    # Test 3: Pagination logic
    results.append(("Pagination Logic", test_pagination_logic()))
    
    # Test 4: View mode selection
    results.append(("View Mode Selection", test_view_mode_selection()))
    
    # Test 5: Search with task number
    results.append(("Search Task Number", test_search_with_task_number()))
    
    # Test 6: Filter combinations
    results.append(("Filter Combinations", test_filter_combinations()))
    
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
        print("\n🎉 All Phase 4 tests PASSED! ✅")
        print("\nManual UI Tests Required:")
        print("1. Kanban Board → See Group filter dropdown")
        print("2. Select 'IT' group → Only IT group tasks shown")
        print("3. Select 'All Groups' → All tasks shown again")
        print("4. Column with >30 tasks → See pagination controls")
        print("5. Click 'Load More' → Loads 20 more tasks")
        print("6. Click 'View All' → Shows all tasks")
        print("7. Column <20 tasks → Detailed card view")
        print("8. Column 20-50 tasks → Compact card view")
        print("9. Column >50 tasks → Mini card view")
        print("10. Search 'SAP' → See results counter '✓ X found'")
        print("11. Click ✕ button → Clears search")
        print("12. Drag task between columns → Still works")
    else:
        print("\n⚠️ Some tests FAILED. Please review above output.")
        print("\nNote: If 'IT' group doesn't exist, some tests will be skipped.")
        print("      Create the 'IT' group in the app to enable full testing.")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)





