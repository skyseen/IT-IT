"""CLI helper to reset Kanban user passwords."""

from __future__ import annotations

import argparse
import getpass
import sys

from kanban.auth import AuthorizationError, admin_reset_password
from kanban.database import get_db_manager
from kanban.models import KanbanUser


def _find_user(session, username: str) -> KanbanUser | None:
    return (
        session.query(KanbanUser)
        .filter(KanbanUser.username == username, KanbanUser.is_active == True)  # noqa: E712
        .first()
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reset a Kanban user's password.")
    parser.add_argument("admin", help="Username of the admin performing the reset")
    parser.add_argument("target", help="Username of the user whose password will be reset")
    parser.add_argument("--temporary", help="Optional temporary password to set")
    parser.add_argument("--no-force", action="store_true", help="Do not require the user to change password on next login")
    args = parser.parse_args(argv)

    db = get_db_manager()
    session = db.get_session()
    try:
        admin = _find_user(session, args.admin)
        if not admin:
            print(f"Admin user '{args.admin}' not found or inactive.")
            return 1

        target = _find_user(session, args.target)
        if not target:
            print(f"Target user '{args.target}' not found or inactive.")
            return 1

        if not args.temporary:
            prompt = f"Enter new password for {target.username} (leave blank to auto-generate): "
            entered = getpass.getpass(prompt)
            if entered:
                confirm = getpass.getpass("Confirm password: ")
                if entered != confirm:
                    print("Passwords do not match.")
                    return 1
                args.temporary = entered

        try:
            password = admin_reset_password(
                admin,
                target_user_id=target.id,
                new_password=args.temporary,
                force_reset=not args.no_force,
                db_manager=db,
            )
        except AuthorizationError as exc:
            print(f"Authorization error: {exc}")
            return 1
        except Exception as exc:  # noqa: BLE001
            print(f"Failed to reset password: {exc}")
            return 1

        # If generated automatically, show once.
        print("Password reset successful.")
        print(f"Username: {target.username}")
        print(f"Temporary Password: {password}")
        if args.no_force:
            print("User is not forced to change password on next login.")
        else:
            print("User must change password on next login.")
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())











