# Workflow Integration Guide for Kanban

## Overview

This guide explains how to integrate the Kanban system with existing IT!IT workflows (SAP, Agile, Telco) to automatically create tasks from workflow actions.

## Current Status

**Status**: Not Implemented (Optional Enhancement)

The Kanban system is fully functional without workflow integration. This feature is optional and can be added later when needed.

## Integration Points

### 1. SAP Workflows
**Location**: `sap_workflows.py` or similar

**When to create tasks**:
- New SAP user account creation
- SAP password reset requests
- SAP role modifications
- SAP system issues

**Implementation**:
```python
# Example: After creating SAP account
from kanban.database import get_db_manager
from kanban.manager import KanbanManager

def create_sap_user(user_data):
    # ... existing SAP creation logic ...
    
    # Auto-create Kanban task if enabled
    if get_kanban_config().get("auto_create_tasks", {}).get("sap", False):
        db = get_db_manager()
        manager = KanbanManager(db, current_user_id=get_current_user_id())
        
        manager.create_task(
            title=f"SAP Account Created: {user_data['name']}",
            description=f"SAP account created for {user_data['name']} ({user_data['id']})",
            category="SAP",
            priority="Low",
            status="Done",  # Already completed
            created_by=get_current_user_id()
        )
```

### 2. Agile Workflows
**Location**: Agile ticketing system integration

**When to create tasks**:
- New Agile ticket created
- Agile ticket assigned to IT
- Agile system maintenance
- Bulk Agile operations

**Implementation**:
```python
# Example: New Agile ticket
def handle_agile_ticket(ticket_data):
    # ... existing Agile logic ...
    
    if get_kanban_config().get("auto_create_tasks", {}).get("agile", False):
        db = get_db_manager()
        manager = KanbanManager(db, current_user_id=get_current_user_id())
        
        manager.create_task(
            title=f"Agile Ticket: {ticket_data['title']}",
            description=ticket_data['description'],
            category="Agile",
            priority=map_agile_priority(ticket_data['priority']),
            status="To Do",
            assigned_to=find_assignee(ticket_data),
            created_by=get_current_user_id()
        )
```

### 3. Telco Workflows
**Location**: `telco_workflows.py` or similar

**When to create tasks**:
- New telecom line requests
- Telecom bill processing
- Line deactivation requests
- Telecom issues

**Implementation**:
```python
# Example: Process telecom bill
def process_telco_bill(bill_data):
    # ... existing Telco logic ...
    
    if get_kanban_config().get("auto_create_tasks", {}).get("telco", False):
        db = get_db_manager()
        manager = KanbanManager(db, current_user_id=get_current_user_id())
        
        manager.create_task(
            title=f"Telecom Bill: {bill_data['provider']} - {bill_data['month']}",
            description=f"Process and verify telecom bill for {bill_data['provider']}",
            category="Telco",
            priority="Medium",
            status="To Do",
            deadline=bill_data['due_date'],
            created_by=get_current_user_id()
        )
```

## Configuration

### Add to `config_manager.py`

The Kanban configuration already supports workflow settings:

```python
# In get_kanban_config()
{
    "enabled": True,
    "auto_create_tasks": {
        "sap": False,  # Enable/disable SAP auto-tasks
        "agile": False,  # Enable/disable Agile auto-tasks
        "telco": False   # Enable/disable Telco auto-tasks
    },
    "default_assignee": {
        "sap": None,  # User ID or None for no default
        "agile": None,
        "telco": None
    },
    "default_column": {
        "sap": "Done",  # Column name for auto-created tasks
        "agile": "To Do",
        "telco": "To Do"
    }
}
```

### Settings UI

Add a settings dialog to configure workflow integration:

**Location**: Add to `ui.py` settings dialog or create `kanban/ui_settings.py`

```python
class KanbanSettingsDialog(QtWidgets.QDialog):
    """Dialog for configuring Kanban workflow integration."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kanban Settings")
        self.setMinimumWidth(500)
        
        layout = QtWidgets.QVBoxLayout(self)
        
        # Auto-create tasks section
        group = QtWidgets.QGroupBox("Automatic Task Creation")
        group_layout = QtWidgets.QVBoxLayout(group)
        
        self.sap_checkbox = QtWidgets.QCheckBox("Auto-create tasks for SAP actions")
        self.agile_checkbox = QtWidgets.QCheckBox("Auto-create tasks for Agile tickets")
        self.telco_checkbox = QtWidgets.QCheckBox("Auto-create tasks for Telecom workflows")
        
        group_layout.addWidget(self.sap_checkbox)
        group_layout.addWidget(self.agile_checkbox)
        group_layout.addWidget(self.telco_checkbox)
        
        layout.addWidget(group)
        
        # Buttons
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self._load_settings()
    
    def _load_settings(self):
        config = get_kanban_config()
        auto_create = config.get("auto_create_tasks", {})
        
        self.sap_checkbox.setChecked(auto_create.get("sap", False))
        self.agile_checkbox.setChecked(auto_create.get("agile", False))
        self.telco_checkbox.setChecked(auto_create.get("telco", False))
    
    def _save_settings(self):
        config = get_kanban_config()
        config["auto_create_tasks"] = {
            "sap": self.sap_checkbox.isChecked(),
            "agile": self.agile_checkbox.isChecked(),
            "telco": self.telco_checkbox.isChecked()
        }
        set_kanban_config(config)
```

## Implementation Steps

### Step 1: Identify Integration Points
1. Review existing workflow code (SAP, Agile, Telco)
2. Identify key actions that should create Kanban tasks
3. Determine what information to include in auto-created tasks

### Step 2: Add Kanban Imports
In each workflow file, add:
```python
from kanban.database import get_db_manager
from kanban.manager import KanbanManager
from config_manager import get_kanban_config
```

### Step 3: Create Helper Function
Add a reusable helper:
```python
def create_workflow_task(
    workflow_type: str,
    title: str,
    description: str,
    priority: str = "Low",
    status: str = "To Do",
    deadline=None,
    assigned_to=None
):
    """Create a Kanban task from a workflow action."""
    config = get_kanban_config()
    
    # Check if auto-create is enabled
    if not config.get("auto_create_tasks", {}).get(workflow_type.lower(), False):
        return
    
    try:
        db = get_db_manager()
        # Get current user ID from session or config
        current_user_id = 1  # TODO: Get actual current user
        
        manager = KanbanManager(db, current_user_id=current_user_id)
        
        # Get default column if not specified
        if status == "To Do":
            status = config.get("default_column", {}).get(workflow_type.lower(), "To Do")
        
        # Get default assignee if not specified
        if not assigned_to:
            assigned_to = config.get("default_assignee", {}).get(workflow_type.lower())
        
        task = manager.create_task(
            title=title,
            description=description,
            category=workflow_type.upper(),
            priority=priority,
            status=status,
            deadline=deadline,
            assigned_to=assigned_to,
            created_by=current_user_id
        )
        
        print(f"Auto-created Kanban task: {task.task_number} - {title}")
        return task
        
    except Exception as e:
        print(f"Failed to create auto-task: {e}")
        # Don't fail the workflow if Kanban task creation fails
        return None
```

### Step 4: Call from Workflows
Insert calls to `create_workflow_task()` at appropriate points in your workflow code.

### Step 5: Add Settings UI
Add the settings dialog to your main settings/preferences UI.

### Step 6: Test Integration
1. Enable auto-create for one workflow type
2. Perform workflow actions
3. Verify tasks appear in Kanban
4. Check task details are correct
5. Test with disabled auto-create

## Benefits

- **Automatic tracking**: All workflow actions logged in Kanban
- **Visibility**: Team can see all ongoing work in one place
- **Accountability**: Tasks auto-assigned to responsible person
- **History**: Complete audit trail of all workflow activities
- **Reporting**: Workflow statistics and metrics in Reports view

## Considerations

### Performance
- Keep task creation async/non-blocking
- Don't fail workflows if Kanban unavailable
- Batch create tasks if processing many items

### Privacy
- Avoid including sensitive data in task descriptions
- Consider access controls for auto-created tasks
- Log workflow actions appropriately

### Maintenance
- Document which actions create tasks
- Provide way to disable per workflow type
- Allow bulk deletion of auto-created tasks if needed

## Alternative: Manual Task Creation

If automatic integration is not needed, users can manually create tasks:

1. Complete workflow action (SAP, Agile, Telco)
2. Go to Kanban tab
3. Click "+ New Task"
4. Fill in details
5. Select appropriate category (SAP/Agile/Telco)

This gives more control but requires manual effort.

## Future Enhancements

- **Webhook support**: Trigger tasks from external systems
- **Email integration**: Create tasks from emails
- **Template tasks**: Pre-filled forms for common workflows
- **Task checklists**: Subtasks for complex workflows
- **Workflow automation**: Auto-move tasks based on rules

## Conclusion

Workflow integration is optional but valuable for teams that want automatic task tracking. Start with one workflow type, test thoroughly, then expand to others as needed.

The current Kanban system is fully functional without this feature and can be used effectively with manual task creation.












