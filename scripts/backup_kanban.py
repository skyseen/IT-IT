"""Automated backup script for Kanban PostgreSQL database."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def load_config():
    """Load database configuration."""
    config_path = Path(__file__).parent.parent / "config" / "kanban_config.json"

    # Try production config first
    prod_config_path = Path(__file__).parent.parent / "config" / "kanban_config_production.json"
    if prod_config_path.exists():
        config_path = prod_config_path

    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


def create_backup():
    """Create database backup using pg_dump."""
    print("=" * 60)
    print("Kanban Database Backup Script")
    print("=" * 60)
    print()

    # Load config
    config = load_config()
    db_config = config["database"]

    # Create backups directory
    backups_dir = Path(__file__).parent.parent / "backups"
    backups_dir.mkdir(exist_ok=True)

    # Generate backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backups_dir / f"kanban_backup_{timestamp}.sql"

    print(f"Backup location: {backup_file}")
    print(f"Database: {db_config['database']} @ {db_config['host']}:{db_config['port']}")
    print()

    # Build pg_dump command
    cmd = [
        "pg_dump",
        "-h",
        db_config["host"],
        "-p",
        str(db_config["port"]),
        "-U",
        db_config["username"],
        "-d",
        db_config["database"],
        "-f",
        str(backup_file),
        "--clean",
        "--if-exists",
        "--verbose",
    ]

    # Set password environment variable
    import os

    env = os.environ.copy()
    env["PGPASSWORD"] = db_config["password"]

    try:
        print("Running pg_dump...")
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=False)

        if result.returncode == 0:
            print()
            print("✅ Backup completed successfully!")
            print(f"   File: {backup_file}")
            print(f"   Size: {backup_file.stat().st_size / 1024:.2f} KB")

            # Clean up old backups (keep last 30)
            cleanup_old_backups(backups_dir, keep=30)

            return True
        else:
            print()
            print("❌ Backup failed!")
            print(f"Error: {result.stderr}")
            return False

    except FileNotFoundError:
        print()
        print("❌ pg_dump not found!")
        print("Please ensure PostgreSQL client tools are installed and in PATH.")
        return False
    except Exception as e:
        print()
        print(f"❌ Backup error: {e}")
        return False


def cleanup_old_backups(backups_dir: Path, keep: int = 30):
    """Remove old backups, keeping only the most recent ones."""
    backup_files = sorted(backups_dir.glob("kanban_backup_*.sql"), key=lambda p: p.stat().st_mtime, reverse=True)

    if len(backup_files) > keep:
        print()
        print(f"Cleaning up old backups (keeping {keep} most recent)...")
        for old_backup in backup_files[keep:]:
            try:
                old_backup.unlink()
                print(f"  🗑️  Removed: {old_backup.name}")
            except Exception as e:
                print(f"  ⚠️  Failed to remove {old_backup.name}: {e}")


def main():
    """Run backup."""
    success = create_backup()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()













