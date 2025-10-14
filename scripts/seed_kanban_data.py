"""Seed script to populate Kanban database with initial test data."""

from __future__ import annotations

import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from random import choice, randint

# Add parent directory to path to import kanban module
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config_manager import get_kanban_config
from kanban.database import get_db_manager
from kanban.models import KanbanColumn, KanbanTask, KanbanUser


def seed_users(session) -> dict[int, KanbanUser]:
    """Create test users."""
    print("Creating test users...")

    users_data = [
        {
            "username": "kenyi.seen",
            "display_name": "Kenyi Seen",
            "email": "kenyi.seen@ingrasys.com",
            "role": "admin",
            "avatar_color": "#F59E0B",
            "department": "IT/OA",
        },
        {
            "username": "alex.ng",
            "display_name": "Alex Ng",
            "email": "alex.ng@ingrasys.com",
            "role": "member",
            "avatar_color": "#3B82F6",
            "department": "IT/OA",
        },
        {
            "username": "oscar.loo",
            "display_name": "Oscar Loo",
            "email": "oscar.loo@ingrasys.com",
            "role": "member",
            "avatar_color": "#10B981",
            "department": "IT/OA",
        },
        {
            "username": "lingyun.niu",
            "display_name": "Lingyun Niu",
            "email": "lingyun.niu@foxconn.com.sg",
            "role": "member",
            "avatar_color": "#8B5CF6",
            "department": "IT/OA",
        },
        {
            "username": "benni.tsao",
            "display_name": "Benni Tsao",
            "email": "benni.yh.tsao@ingrasys.com",
            "role": "member",
            "avatar_color": "#EC4899",
            "department": "IT/OA",
        },
        {
            "username": "test.user",
            "display_name": "Test User",
            "email": "test@example.com",
            "role": "viewer",
            "avatar_color": "#6B7280",
            "department": "IT/OA",
        },
    ]

    user_dict = {}
    for user_data in users_data:
        # Check if user already exists
        existing = session.query(KanbanUser).filter_by(username=user_data["username"]).first()
        if existing:
            print(f"  ✓ User '{user_data['username']}' already exists (ID: {existing.id})")
            user_dict[existing.id] = existing
            continue

        user = KanbanUser(**user_data)
        session.add(user)
        session.flush()
        user_dict[user.id] = user
        print(f"  ✓ Created user: {user.display_name} (ID: {user.id})")

    session.commit()
    return user_dict


def seed_columns(session) -> dict[str, KanbanColumn]:
    """Create default Kanban columns from config."""
    print("Creating Kanban columns...")

    config = get_kanban_config()
    columns_config = config.get("default_columns", [])

    column_dict = {}
    for col_data in columns_config:
        # Check if column already exists
        existing = session.query(KanbanColumn).filter_by(name=col_data["name"], is_active=True).first()
        if existing:
            print(f"  ✓ Column '{col_data['name']}' already exists (ID: {existing.id})")
            column_dict[existing.name] = existing
            continue

        column = KanbanColumn(
            name=col_data["name"],
            position=col_data["position"],
            color=col_data["color"],
            wip_limit=col_data.get("wip_limit"),
        )
        session.add(column)
        session.flush()
        column_dict[column.name] = column
        print(f"  ✓ Created column: {column.name} (ID: {column.id})")

    session.commit()
    return column_dict


def seed_tasks(session, users: dict[int, KanbanUser], columns: dict[str, KanbanColumn], count: int = 30) -> None:
    """Create sample tasks."""
    print(f"Creating {count} sample tasks...")

    # Task templates
    task_templates = {
        "sap": [
            "Create SAP account for new employee {name}",
            "Reset SAP password for user {name}",
            "Disable SAP access for terminated employee {name}",
            "Update SAP authorizations for {name}",
        ],
        "agile": [
            "Create Agile account for {name} (MFG & RD)",
            "Reset Agile password for {name}",
            "Grant Agile PLM access to {name}",
            "Migrate Agile projects for {name}",
        ],
        "telco": [
            "Process Singtel IGS32 form for {name}",
            "Submit M1 CNT35 form for {name}",
            "Update mobile plan for {name}",
            "Terminate mobile subscription for {name}",
        ],
        "user_ops": [
            "Onboard new user: {name}",
            "Setup workstation for {name}",
            "Configure email access for {name}",
            "Provision network drive access for {name}",
        ],
        "general": [
            "Update IT documentation",
            "Review security policies",
            "Quarterly system maintenance",
            "Backup verification task",
            "Update system inventory",
            "Process pending IT requests",
        ],
    }

    names = ["John Doe", "Jane Smith", "Bob Wilson", "Alice Lee", "Charlie Brown", "Diana Ross"]
    priorities = ["low", "low", "medium", "medium", "medium", "high", "high", "critical"]
    column_names = list(columns.keys())
    user_ids = list(users.keys())

    created_count = 0
    for i in range(count):
        # Select random category and template
        category = choice(list(task_templates.keys()))
        template = choice(task_templates[category])

        # Generate title
        if "{name}" in template:
            title = template.format(name=choice(names))
        else:
            title = template

        # Generate description
        description = f"This is a sample task for category '{category}'.\n\n**Details:**\n- Auto-generated for testing\n- Task #{i+1}\n- Category: {category.upper()}"

        # Random assignment
        column_name = choice(column_names)
        assigned_to = choice(user_ids) if randint(1, 10) > 3 else None  # 70% chance of assignment
        priority = choice(priorities)

        # Random deadline (20-80 days from now, or past for overdue testing)
        days_offset = randint(-10, 80)  # Some tasks in past for overdue testing
        deadline = date.today() + timedelta(days=days_offset)

        # Random estimated hours
        estimated_hours = float(choice([0.5, 1, 2, 4, 8, 16]))

        # Random tags
        all_tags = ["urgent", "maintenance", "new-user", "support", "training", "migration"]
        tags = [choice(all_tags) for _ in range(randint(0, 3))]

        # Create task
        task = KanbanTask(
            title=title,
            task_number=f"TASK-{i+1:04d}",
            description=description,
            column_id=columns[column_name].id,
            position=float(i),
            assigned_to=assigned_to,
            created_by=user_ids[0],  # First user (admin) creates all
            priority=priority,
            category=category,
            deadline=deadline,
            estimated_hours=estimated_hours,
            tags=tags,
            is_workflow_task=False,
        )

        session.add(task)
        created_count += 1

        if (i + 1) % 10 == 0:
            print(f"  ✓ Created {i+1}/{count} tasks...")

    session.commit()
    print(f"  ✓ Created {created_count} tasks successfully!")


def main():
    """Main seed function."""
    print("=" * 60)
    print("Kanban Database Seed Script")
    print("=" * 60)
    print()

    try:
        # Get database manager
        db = get_db_manager()

        # Test connection
        if not db.test_connection():
            print("❌ Failed to connect to database!")
            print("Please ensure PostgreSQL is running and config is correct.")
            sys.exit(1)

        print("✓ Database connection successful!")
        print()

        # Get session
        session = db.get_session()

        try:
            # Seed users
            users = seed_users(session)
            print()

            # Seed columns
            columns = seed_columns(session)
            print()

            # Seed tasks
            seed_tasks(session, users, columns, count=30)
            print()

            print("=" * 60)
            print("✅ Seed completed successfully!")
            print("=" * 60)
            print()
            print("Summary:")
            print(f"  - Users: {len(users)}")
            print(f"  - Columns: {len(columns)}")
            print(f"  - Tasks: 30")
            print()
            print("You can now test the Kanban system with this data.")

        finally:
            session.close()

    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


