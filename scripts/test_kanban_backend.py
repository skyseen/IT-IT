"""Test script for Kanban backend functionality."""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kanban.auth import authenticate, AuthenticationError, change_password
from kanban.database import get_db_manager
from kanban.manager import KanbanManager


def test_connection():
    """Test database connection."""
    print("Test 1: Database Connection")
    print("-" * 40)

    try:
        db = get_db_manager()
        if db.test_connection():
            print("✅ Connection successful!")

            # Show pool status
            pool_status = db.get_pool_status()
            print(f"   Pool size: {pool_status.get('size', 'N/A')}")
            print(f"   Checked out: {pool_status.get('checked_out', 0)}")
            return True
        else:
            print("❌ Connection failed!")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_users(manager: KanbanManager):
    """Test user operations."""
    print("\nTest 2: User Operations")
    print("-" * 40)

    try:
        # Get all users
        users = manager.get_all_users()
        print(f"✅ Found {len(users)} users:")
        for user in users[:3]:  # Show first 3
            print(f"   - {user.display_name} ({user.username}) [ID: {user.id}]")

        if len(users) > 3:
            print(f"   ... and {len(users) - 3} more")

        # Get specific user
        if users:
            user = manager.get_user(users[0].id)
            print(f"✅ Get user by ID: {user.display_name}")

        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_columns(manager: KanbanManager):
    """Test column operations."""
    print("\nTest 3: Column Operations")
    print("-" * 40)

    try:
        # Get all columns
        columns = manager.get_all_columns()
        print(f"✅ Found {len(columns)} columns:")
        for col in columns:
            wip_str = f" (WIP limit: {col.wip_limit})" if col.wip_limit else ""
            print(f"   - {col.name} {col.color}{wip_str}")

        # Get column by name
        todo_col = manager.get_column_by_name("To Do")
        if todo_col:
            print(f"✅ Found 'To Do' column (ID: {todo_col.id})")

        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_task_crud(manager: KanbanManager):
    """Test task CRUD operations."""
    print("\nTest 4: Task CRUD Operations")
    print("-" * 40)

    try:
        # Get a column to create task in
        columns = manager.get_all_columns()
        if not columns:
            print("❌ No columns found!")
            return False

        backlog = manager.get_column_by_name("Backlog") or columns[0]

        # Create task
        task = manager.create_task(
            title="Test Task - Backend Verification",
            description="This task was created by the test script to verify backend functionality.",
            column_id=backlog.id,
            priority="high",
            category="testing",
            deadline=date.today() + timedelta(days=7),
            estimated_hours=2.5,
            tags=["test", "automation"],
        )
        print(f"✅ Created task: {task.task_number} - {task.title}")
        print(f"   ID: {task.id}, Column: {backlog.name}")

        # Read task
        retrieved = manager.get_task(task.id)
        if retrieved:
            print(f"✅ Retrieved task: {retrieved.task_number}")
            print(f"   Title: {retrieved.title}")
            print(f"   Priority: {retrieved.priority}")
            print(f"   Tags: {', '.join(retrieved.tags)}")

        # Update task
        updated = manager.update_task(
            task.id,
            priority="critical",
            description="Updated description - testing update functionality",
        )
        print(f"✅ Updated task priority to: {updated.priority}")

        # Get tasks in column
        tasks = manager.get_tasks_by_column(backlog.id)
        print(f"✅ Found {len(tasks)} tasks in '{backlog.name}' column")

        # Search tasks
        search_results = manager.search_tasks("Test Task")
        print(f"✅ Search found {len(search_results)} matching tasks")

        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_task_movement(manager: KanbanManager):
    """Test moving tasks between columns."""
    print("\nTest 5: Task Movement")
    print("-" * 40)

    try:
        # Get columns
        backlog = manager.get_column_by_name("Backlog")
        in_progress = manager.get_column_by_name("In Progress")

        if not (backlog and in_progress):
            print("❌ Required columns not found!")
            return False

        # Create a test task
        task = manager.create_task(
            title="Task Movement Test",
            description="Testing task movement between columns",
            column_id=backlog.id,
            priority="medium",
        )
        print(f"✅ Created task {task.task_number} in '{backlog.name}'")

        # Move to In Progress
        moved_task = manager.move_task(task.id, in_progress.id)
        print(f"✅ Moved task to '{in_progress.name}'")
        print(f"   Started at: {moved_task.started_at}")

        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_comments(manager: KanbanManager):
    """Test comment operations."""
    print("\nTest 6: Comment Operations")
    print("-" * 40)

    try:
        # Get any task
        columns = manager.get_all_columns()
        tasks = manager.get_tasks_by_column(columns[0].id)

        if not tasks:
            # Create a task if none exists
            task = manager.create_task(
                title="Comment Test Task",
                description="Task for testing comments",
                column_id=columns[0].id,
            )
        else:
            task = tasks[0]

        # Add comments
        comment1 = manager.add_comment(task.id, "This is a test comment from the backend test script.")
        print(f"✅ Added comment (ID: {comment1.id})")

        comment2 = manager.add_comment(
            task.id, "Another comment to verify threading and multiple comments support."
        )
        print(f"✅ Added second comment (ID: {comment2.id})")

        # Get all comments
        comments = manager.get_comments(task.id)
        print(f"✅ Task has {len(comments)} comments")

        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_statistics(manager: KanbanManager):
    """Test statistics retrieval."""
    print("\nTest 7: Statistics")
    print("-" * 40)

    try:
        stats = manager.get_task_statistics()
        print("✅ Retrieved task statistics:")
        print(f"   Total tasks: {stats['total_tasks']}")
        print(f"   Completed tasks: {stats['completed_tasks']}")
        print(f"   Completion rate: {stats['completion_rate']:.1f}%")
        print(f"   Overdue tasks: {stats['overdue_tasks']}")

        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Kanban Backend Test Suite")
    print("=" * 60)
    print()

    # Test 1: Connection
    if not test_connection():
        print("\n❌ Connection test failed! Aborting further tests.")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("Running functional tests...")
    print("=" * 60)

    # Get database and create manager
    db = get_db_manager()

    try:
        auth_result = authenticate("kenyi.seen", "ChangeMe123!", remember_me=False)
    except AuthenticationError as exc:
        print(f"❌ Failed to authenticate default user: {exc}")
        sys.exit(1)

    manager = KanbanManager(
        db,
        current_user_id=auth_result.user.id,
        session_token=auth_result.session.session_token,
    )

    # Run all tests
    tests = [
        ("Users", lambda: test_users(manager)),
        ("Columns", lambda: test_columns(manager)),
        ("Task CRUD", lambda: test_task_crud(manager)),
        ("Task Movement", lambda: test_task_movement(manager)),
        ("Comments", lambda: test_comments(manager)),
        ("Statistics", lambda: test_statistics(manager)),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")

    print()
    print(f"Total: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("\n🎉 All tests passed! Backend is working correctly.")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total_count - passed_count} test(s) failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()


