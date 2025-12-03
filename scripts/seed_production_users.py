"""Seed script for PRODUCTION - Only creates real users and columns (no sample tasks)."""

from __future__ import annotations

import sys
import io
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config_manager import get_kanban_config
from kanban.database import get_db_manager
from kanban.auth import ensure_password_initialized
from kanban.models import KanbanColumn, KanbanUser


def seed_production_users(session) -> dict[int, KanbanUser]:
    """Create REAL production users - UPDATE THIS LIST with your team!"""
    print("Creating production users...")
    
    # ============================================
    # UPDATE THIS LIST WITH YOUR REAL IT TEAM
    # ============================================
    users_data = [
        {
            "username": "kenyi.seen",
            "display_name": "Kenyi Seen",
            "email": "kenyi.seen@ingrasys.com",
            "role": "admin",
            "avatar_color": "#F59E0B",
            "department": "IT",
        },
        {
            "username": "alex.ng",
            "display_name": "Alex Ng",
            "email": "alex.ng@ingrasys.com",
            "role": "member",
            "avatar_color": "#3B82F6",
            "department": "IT",
        },
        {
            "username": "oscar.loo",
            "display_name": "Oscar Loo",
            "email": "oscar.loo@ingrasys.com",
            "role": "member",
            "avatar_color": "#10B981",
            "department": "IT",
        },
        {
            "username": "lingyun.niu",
            "display_name": "Lingyun Niu",
            "email": "lingyun.niu@foxconn.com.sg",
            "role": "manager",
            "avatar_color": "#8B5CF6",
            "department": "IT",
        },
        {
            "username": "andrew.wong",
            "display_name": "Andrew Wong",
            "email": "andrew.wong@ingrasys.com",
            "role": "member",
            "avatar_color": "#EC4899",
            "department": "IT",
        },
        {
             "username": "flaming.liu",
             "display_name": "Flaming Liu",
             "email": "flaming.liu@foxconn.com.sg",
             "role": "manager",
             "avatar_color": "#6366F1",
             "department": "IT",
        },
        {
             "username": "bryan.leong",
             "display_name": "Bryan Leong",
             "email": "bryan.leong@ingrasys.com",
             "role": "member",
             "avatar_color": "#2596be",
             "department": "IT",
        },
        {
             "username": "lezhi.yi",
             "display_name": "LeZhi.Yin",
             "email": "LeZhi.Yin@ingrasys.com",
             "role": "manager",
             "avatar_color": "#f19856",
             "department": "IT",
        },
        {
             "username": "chinyong.lim",
             "display_name": "ChinYong Lim",
             "email": "chinyong.lim@ingrasys.com",
             "role": "member",
             "avatar_color": "#492f1c",
             "department": "IT",
        },
        {
             "username": "alfred.tang",
             "display_name": "Alfred Tang",
             "email": "alfred.tang@ingrasys.com",
             "role": "member",
             "avatar_color": "#25491c",
             "department": "IT",
        },
        {
             "username": "chinlun.wong",
             "display_name": "ChinLun Wong",
             "email": "chinlun.wong@ingrasys.com",
             "role": "member",
             "avatar_color": "#49301c",
             "department": "IT",
        }
    ]
    
    user_dict = {}
    for user_data in users_data:
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
    
    # Set initial passwords
    print("Setting initial passwords (ChangeMe123!)...")
    for user in user_dict.values():
        ensure_password_initialized(user, default_password="ChangeMe123!", db_manager=None)
    print("  ✓ Passwords initialized (users MUST change on first login)")
    
    return user_dict


def seed_columns(session) -> dict[str, KanbanColumn]:
    """Create Kanban columns."""
    print("Creating Kanban columns...")
    
    config = get_kanban_config()
    columns_config = config.get("default_columns", [])
    
    column_dict = {}
    for col_data in columns_config:
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


def main():
    """Main seed function for production."""
    print("=" * 60)
    print("PRODUCTION Kanban Database Seed Script")
    print("=" * 60)
    print()
    print("⚠️  This script creates REAL users only (NO sample tasks)")
    print()
    
    try:
        db = get_db_manager()
        
        if not db.test_connection():
            print("❌ Failed to connect to database!")
            print("Please check your config/kanban_config.json settings.")
            sys.exit(1)
        
        print("✓ Database connection successful!")
        print()
        
        session = db.get_session()
        
        try:
            users = seed_production_users(session)
            print()
            
            columns = seed_columns(session)
            print()
            
            print("=" * 60)
            print("✅ Production seed completed successfully!")
            print("=" * 60)
            print()
            print("Summary:")
            print(f"  - Users: {len(users)}")
            print(f"  - Columns: {len(columns)}")
            print(f"  - Tasks: 0 (created by team)")
            print()
            print("Next steps:")
            print("  1. Users login with initial password: ChangeMe123!")
            print("  2. Users must change password on first login")
            print("  3. Start creating real tasks!")
            
        finally:
            session.close()
            
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


