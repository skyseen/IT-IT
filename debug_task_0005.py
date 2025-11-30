"""Debug TASK-0005 overdue issue."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime
from kanban.database import get_db_manager
from kanban.models import KanbanTask, KanbanColumn
from sqlalchemy.orm import joinedload

db = get_db_manager()
session = db.get_session()

try:
    # Find TASK-0005
    task = (
        session.query(KanbanTask)
        .options(joinedload(KanbanTask.column))
        .filter_by(task_number="TASK-0005", is_deleted=False)
        .first()
    )
    
    if not task:
        print("❌ TASK-0005 not found")
    else:
        print("="*60)
        print(f"TASK-0005 Debug Information")
        print("="*60)
        print(f"Title: {task.title}")
        print(f"Deadline: {task.deadline}")
        print(f"Column ID: {task.column_id}")
        print(f"Column Name: {task.column.name if task.column else 'NOT LOADED'}")
        print(f"Status: {task.status}")
        print(f"Completed At: {task.completed_at}")
        print(f"Is Deleted: {task.is_deleted}")
        print()
        print(f"Today: {datetime.now().date()}")
        print(f"Deadline < Today: {task.deadline < datetime.now().date() if task.deadline else 'N/A'}")
        print()
        print("="*60)
        print(f"is_overdue Property Result: {task.is_overdue}")
        print("="*60)
        print()
        
        # Check the logic step by step
        print("Step-by-step evaluation:")
        print(f"1. Has deadline? {task.deadline is not None}")
        if task.deadline:
            print(f"2. Status == 'archived'? {task.status == 'archived'}")
            print(f"3. Column loaded? {task.column is not None}")
            if task.column:
                print(f"4. Column name: '{task.column.name}'")
                print(f"5. Column name == 'Done'? {task.column.name == 'Done'}")
            print(f"6. Deadline ({task.deadline}) > Today ({datetime.now().date()})? {datetime.now().date() > task.deadline}")

finally:
    session.close()

