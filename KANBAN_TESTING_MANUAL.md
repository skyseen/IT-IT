# Kanban Feature Testing Manual

## Current Implementation Status

### ✅ Completed Features (Ready to Test)

#### 1. Authentication & Session Management ✅
- **Login system** with username/password
- **Remember me** functionality with session tokens
- **Password change** (self-service)
- **Admin password reset** for other users
- **Session tracking** in database
- **Password validation** (min 8 chars, uppercase, lowercase, digit, special char)
- **Force password change** on first login

#### 2. Core Task Management ✅
- **Create tasks** with full form validation
- **View tasks** on Kanban board by column
- **Edit tasks** with comprehensive fields
- **Delete tasks** (soft delete with confirmation)
- **Move tasks** between columns
- **Task assignment** to users
- **Task priorities** (Low, Medium, High, Critical)
- **Task categories** (SAP, Agile, Telco, User Ops, General)
- **Task deadlines** with date picker
- **Task descriptions** with rich text

#### 3. Comments System ✅
- **Add comments** to tasks
- **View comments** with user info and timestamps
- **Delete comments** (soft delete)
- **Comment count** badge on task cards

#### 4. Search & Filter ✅
- **Search tasks** by title/description (real-time)
- **Filter by assignee** (dropdown)
- **Filter by priority** (dropdown)
- **Clear filters** button
- **Refresh board** button

#### 5. Audit Logging ✅
- **All actions logged** to PostgreSQL
- **Summary logs** to JSONL file
- **Change tracking** (old/new values)
- **User context** (who, when, where)
- **IP address tracking**

#### 6. Database Backend ✅
- **PostgreSQL integration**
- **9 tables** with relationships
- **20+ indexes** for performance
- **Automatic triggers** for audit
- **Connection pooling**
- **Thread-safe sessions**

### ⏳ Not Yet Implemented (To Do)

#### 1. Drag-and-Drop (Pending) ⏳
- Visual drag-and-drop between columns (backend ready)
- Drag preview and drop zones
- Real-time column updates during drag

#### 2. File Attachments UI (Pending) ⏳
- Upload files to tasks (backend complete)
- Download attachments
- View attachment list
- Delete attachments

#### 3. My Tasks View (Pending) ⏳
- Personal dashboard showing:
  - Tasks assigned to me
  - Tasks I created
  - Tasks I'm watching
  - Overdue tasks
- Quick filters and sorting

#### 4. Reports View (Pending) ⏳
- Task statistics dashboard
- Charts and graphs
- Export to CSV
- Date range filters
- Team performance metrics

#### 5. Workflow Integration (Pending) ⏳
- Auto-create tasks from SAP workflows
- Auto-create tasks from Agile workflows
- Auto-create tasks from Telco workflows
- Settings UI for workflow configuration

#### 6. Activity Log Viewer (Pending) ⏳
- View audit history for tasks
- Filter by user, date, action type
- Export audit logs

#### 7. Auto-Refresh Timer (Pending) ⏳
- Configurable auto-refresh interval
- Real-time updates for multi-user scenarios

---

## Comprehensive Testing Plan

### Pre-Test Setup

1. **Verify Database**
   ```bash
   # Check if tables exist and have data
   python -c "from kanban.database import get_db_manager; db = get_db_manager(); print('✓ Connected' if db.test_connection() else '✗ Failed')"
   ```

2. **Verify Test Users**
   - Default users created by seed script:
     - `kenyi.seen` / `ChangeMe123!` (admin)
     - `alex.ng` / `ChangeMe123!` (member)
     - `oscar.loo` / `ChangeMe123!` (member)
     - `lingyun.niu` / `ChangeMe123!` (member)
     - `benni.tsao` / `ChangeMe123!` (member)
     - `test.user` / `ChangeMe123!` (member)

### Test Suite 1: Authentication & User Management

#### Test 1.1: Initial Login
**Steps:**
1. Launch `python app.py`
2. Click on "📋 Kanban" tab
3. Login dialog should appear automatically
4. Enter username: `kenyi.seen`
5. Enter password: `ChangeMe123!`
6. Check "Remember me on this device" ✓
7. Click "Sign In"

**Expected Results:**
- ✓ Login dialog appears on first Kanban tab access
- ✓ Checkbox can be ticked/unticked
- ✓ Login succeeds
- ✓ Password change dialog appears (first login requires password change)
- ✓ Board loads with tasks after password change

#### Test 1.2: Password Change (First Login)
**Steps:**
1. After first login, password change dialog appears
2. Enter current password: `ChangeMe123!`
3. Enter new password: `MyNewPass123!`
4. Confirm new password: `MyNewPass123!`
5. Click "Change Password"

**Expected Results:**
- ✓ Password change succeeds
- ✓ Success message shown
- ✓ Board loads normally
- ✓ Can logout and login with new password

#### Test 1.3: Password Validation
**Steps:**
1. Try changing password to: `short` (too short)
2. Try changing password to: `nouppercase123!` (no uppercase)
3. Try changing password to: `NOLOWERCASE123!` (no lowercase)
4. Try changing password to: `NoDigitsHere!` (no digits)
5. Try changing password to: `NoSpecialChar123` (no special)
6. Try valid password: `ValidPass123!`

**Expected Results:**
- ✓ Each invalid password shows specific error message
- ✓ Valid password is accepted
- ✓ Password successfully changed

#### Test 1.4: Remember Me Functionality
**Steps:**
1. Login with "Remember me" checked
2. Close the application
3. Reopen `python app.py`
4. Click "📋 Kanban" tab

**Expected Results:**
- ✓ Should auto-login without showing login dialog
- ✓ Board loads immediately with remembered session
- ✓ Username shown in account button (top right)

#### Test 1.5: Sign Out
**Steps:**
1. Click account button (top right, shows username)
2. Click "Sign Out"

**Expected Results:**
- ✓ Session ends
- ✓ Board clears
- ✓ Message: "You have been signed out"
- ✓ Must login again to access board

#### Test 1.6: Switch User
**Steps:**
1. Login as `kenyi.seen`
2. Click account button → "Switch User"
3. Login as `alex.ng` / `MyNewPass123!` (or original password if not changed)

**Expected Results:**
- ✓ Login dialog appears
- ✓ Previous username pre-filled (optional)
- ✓ Can login as different user
- ✓ Board reloads with new user context
- ✓ Account button shows new username

#### Test 1.7: Self-Service Password Change
**Steps:**
1. Login as any user
2. Click account button → "Change Password"
3. Enter current password
4. Enter new password (meeting requirements)
5. Confirm new password
6. Click "Change Password"

**Expected Results:**
- ✓ Dialog appears with 3 fields
- ✓ Current password verified
- ✓ New password validated
- ✓ Confirmation must match
- ✓ Success message shown
- ✓ Can login with new password

#### Test 1.8: Admin Password Reset
**Steps:**
1. Login as `kenyi.seen` (admin role)
2. Click account button → "Reset Another User Password"
3. Select user: `alex.ng`
4. Click "Generate Temporary Password"
5. Click "Reset Password"
6. Copy the temporary password shown
7. Logout and login as `alex.ng` with temp password

**Expected Results:**
- ✓ Admin sees "Reset Another User Password" option
- ✓ User dropdown shows all users
- ✓ Temporary password generated (12+ chars, strong)
- ✓ Reset succeeds with confirmation
- ✓ Target user can login with temp password
- ✓ Target user forced to change password on next login

#### Test 1.9: Invalid Login Attempts
**Steps:**
1. Try login with wrong username: `fake.user` / `anything`
2. Try login with wrong password: `kenyi.seen` / `wrongpass`
3. Try login with empty fields

**Expected Results:**
- ✓ Error: "Authentication failed: Invalid credentials"
- ✓ Error: "Authentication failed: Invalid credentials"
- ✓ Error: "Username and password are required"
- ✓ Login dialog remains open
- ✓ No crash or freeze

---

### Test Suite 2: Task Creation & Management

#### Test 2.1: Create New Task (Basic)
**Steps:**
1. Login and access Kanban board
2. Click "+ New Task" button
3. Fill in:
   - Title: "Test Task 1"
   - Description: "This is a test task"
   - Column: "To Do"
   - Priority: "Medium"
   - Category: "General"
4. Click "Create"

**Expected Results:**
- ✓ Dialog opens with empty form
- ✓ All fields available
- ✓ Task created successfully
- ✓ Task appears in "To Do" column
- ✓ Task card shows title, priority badge, category
- ✓ Success message shown

#### Test 2.2: Create Task with All Fields
**Steps:**
1. Click "+ New Task"
2. Fill in:
   - Title: "Complete Task Example"
   - Description: "Full test with all fields"
   - Column: "In Progress"
   - Priority: "High"
   - Category: "SAP"
   - Assign to: Select a user (e.g., yourself)
   - Deadline: Select a date (e.g., tomorrow)
3. Click "Create"

**Expected Results:**
- ✓ All fields accepted
- ✓ Task created in "In Progress" column
- ✓ Priority shown as red "HIGH"
- ✓ Category badge shows "SAP"
- ✓ Assignee avatar/name shown
- ✓ Deadline date shown
- ✓ Task number auto-generated (e.g., KAN-0031)

#### Test 2.3: Create Task (Validation)
**Steps:**
1. Click "+ New Task"
2. Leave title empty, click "Create"
3. Enter title: "A", click "Create" (too short)
4. Enter valid title, leave column empty, click "Create"

**Expected Results:**
- ✓ Error: "Title is required"
- ✓ Error: "Title must be at least 3 characters"
- ✓ Error: "Column is required"
- ✓ Form doesn't submit until valid

#### Test 2.4: View Task Details
**Steps:**
1. Click on any task card
2. Review all fields in detail dialog

**Expected Results:**
- ✓ Dialog opens showing full task details
- ✓ All fields visible (title, description, status, priority, etc.)
- ✓ Comments section shown at bottom
- ✓ Can see task metadata (created by, created at, modified at)

#### Test 2.5: Edit Task
**Steps:**
1. Click on task card to open detail dialog
2. Click "Edit" button
3. Change title to: "Updated Task Title"
4. Change priority from "Medium" to "High"
5. Change column to different one
6. Click "Save"

**Expected Results:**
- ✓ Fields become editable
- ✓ Changes saved successfully
- ✓ Task card updates immediately
- ✓ Task moves to new column if changed
- ✓ Priority badge updates
- ✓ Detail dialog closes

#### Test 2.6: Assign/Unassign User
**Steps:**
1. Open task detail dialog
2. Click "Edit"
3. Select assignee from dropdown
4. Click "Save"
5. Open task again, click "Edit"
6. Clear assignee (select "Unassigned")
7. Click "Save"

**Expected Results:**
- ✓ User assigned successfully
- ✓ Task card shows assignee avatar
- ✓ Unassign works
- ✓ Task card removes assignee avatar

#### Test 2.7: Set/Clear Deadline
**Steps:**
1. Open task, click "Edit"
2. Click deadline date picker
3. Select a date 3 days from now
4. Save task
5. Open task again, click "Edit"
6. Clear deadline
7. Save task

**Expected Results:**
- ✓ Date picker opens
- ✓ Date saved correctly
- ✓ Task card shows deadline date
- ✓ Can clear deadline
- ✓ Deadline removed from card

#### Test 2.8: Move Task Between Columns
**Steps:**
1. Create task in "To Do"
2. Open task, click "Edit"
3. Change column to "In Progress"
4. Save task
5. Verify task moved

**Expected Results:**
- ✓ Task disappears from "To Do"
- ✓ Task appears in "In Progress"
- ✓ Board updates immediately
- ✓ Change logged in audit trail

#### Test 2.9: Delete Task
**Steps:**
1. Open task detail dialog
2. Click "Delete" button
3. Confirm deletion

**Expected Results:**
- ✓ Confirmation dialog appears
- ✓ Warning message shown
- ✓ Task removed from board
- ✓ Success message shown
- ✓ Task soft-deleted (not permanently removed from DB)

#### Test 2.10: Cancel Task Deletion
**Steps:**
1. Open task detail dialog
2. Click "Delete" button
3. Click "No" or "Cancel" on confirmation

**Expected Results:**
- ✓ Task not deleted
- ✓ Task still visible on board
- ✓ Dialog remains open

---

### Test Suite 3: Comments System

#### Test 3.1: Add Comment
**Steps:**
1. Open any task detail dialog
2. Scroll to comments section
3. Enter text in comment box: "This is a test comment"
4. Click "Post Comment"

**Expected Results:**
- ✓ Comment added successfully
- ✓ Comment appears in list with user name and timestamp
- ✓ Comment box clears
- ✓ Comment count badge on task card increments

#### Test 3.2: Add Multiple Comments
**Steps:**
1. Open task
2. Add comment: "First comment"
3. Add comment: "Second comment"
4. Add comment: "Third comment"

**Expected Results:**
- ✓ All comments appear in order (newest first or oldest first)
- ✓ Each has correct timestamp
- ✓ Each shows correct user
- ✓ Comment count shows "3"

#### Test 3.3: View Comments
**Steps:**
1. Open task with comments
2. Scroll through comments section

**Expected Results:**
- ✓ All comments visible
- ✓ User display names shown
- ✓ Timestamps formatted properly (e.g., "2 hours ago")
- ✓ Comment text preserved (no formatting loss)

#### Test 3.4: Empty Comment Validation
**Steps:**
1. Open task
2. Leave comment box empty
3. Click "Post Comment"

**Expected Results:**
- ✓ Error message: "Comment cannot be empty"
- ✓ Comment not posted
- ✓ No crash

#### Test 3.5: Long Comment
**Steps:**
1. Open task
2. Enter very long comment (500+ characters)
3. Click "Post Comment"

**Expected Results:**
- ✓ Comment accepted
- ✓ Full text saved
- ✓ Comment displayed properly (scrollable if needed)

---

### Test Suite 4: Search & Filter

#### Test 4.1: Search by Text
**Steps:**
1. View board with multiple tasks
2. Click search box (toolbar)
3. Type: "test" (partial search)

**Expected Results:**
- ✓ Board filters in real-time
- ✓ Only tasks with "test" in title/description shown
- ✓ Other tasks hidden
- ✓ Clear search clears filter

#### Test 4.2: Filter by Assignee
**Steps:**
1. View board
2. Click "Assigned To" dropdown
3. Select a specific user

**Expected Results:**
- ✓ Only tasks assigned to that user shown
- ✓ Unassigned tasks hidden
- ✓ Select "All" to clear filter

#### Test 4.3: Filter by Priority
**Steps:**
1. View board
2. Click "Priority" dropdown
3. Select "High"

**Expected Results:**
- ✓ Only high-priority tasks shown
- ✓ Other priorities hidden
- ✓ Select "All" to clear filter

#### Test 4.4: Combined Filters
**Steps:**
1. Set search text: "SAP"
2. Set priority: "High"
3. Set assignee: "kenyi.seen"

**Expected Results:**
- ✓ Only tasks matching ALL criteria shown
- ✓ Filters work together (AND logic)
- ✓ Clear individual filters independently

#### Test 4.5: No Results
**Steps:**
1. Search for text that doesn't exist: "xyzabc123"

**Expected Results:**
- ✓ Board shows empty state
- ✓ Message: "No tasks found" or similar
- ✓ No errors

#### Test 4.6: Clear All Filters
**Steps:**
1. Apply multiple filters (search, priority, assignee)
2. Click "Clear Filters" button

**Expected Results:**
- ✓ All filters cleared at once
- ✓ Board shows all tasks
- ✓ Search box empty
- ✓ Dropdowns reset to "All"

---

### Test Suite 5: Board Operations

#### Test 5.1: Refresh Board
**Steps:**
1. View board
2. Click "Refresh" button (toolbar)

**Expected Results:**
- ✓ Board reloads from database
- ✓ Any changes from other users appear
- ✓ Current user's view preserved (column positions, etc.)
- ✓ Filters cleared

#### Test 5.2: Multiple Columns Display
**Steps:**
1. View board with all default columns:
   - Backlog
   - To Do
   - In Progress
   - Review
   - Done

**Expected Results:**
- ✓ All columns visible
- ✓ Columns in correct order
- ✓ Each column shows task count
- ✓ Horizontal scrolling works if needed

#### Test 5.3: Column Task Counts
**Steps:**
1. Count tasks in each column manually
2. Compare with column header count

**Expected Results:**
- ✓ Header shows correct task count for each column
- ✓ Count updates when tasks move
- ✓ Count includes filtered tasks only

#### Test 5.4: Empty Column Display
**Steps:**
1. Move all tasks out of a column (e.g., "Backlog")
2. View empty column

**Expected Results:**
- ✓ Column still visible
- ✓ Shows empty state message
- ✓ Can still add tasks to it
- ✓ Count shows "0"

#### Test 5.5: Task Card Display
**Steps:**
1. View any task card on board

**Expected Results:**
- ✓ Task number visible (e.g., "KAN-0042")
- ✓ Title shown (truncated if long)
- ✓ Priority badge visible (color-coded)
- ✓ Category badge shown
- ✓ Assignee avatar/name (if assigned)
- ✓ Deadline date (if set)
- ✓ Comment count icon (if comments exist)
- ✓ Card clickable

---

### Test Suite 6: Multi-User Scenarios

#### Test 6.1: Concurrent Users (Different Machines/Sessions)
**Steps:**
1. User A: Login as `kenyi.seen` on one machine
2. User B: Login as `alex.ng` on another machine
3. User A: Create a new task
4. User B: Click "Refresh"

**Expected Results:**
- ✓ Both users can login simultaneously
- ✓ User B sees User A's new task after refresh
- ✓ No conflicts or crashes

#### Test 6.2: Task Assignment Notification
**Steps:**
1. User A: Create task and assign to User B
2. User B: Refresh board

**Expected Results:**
- ✓ User B sees task assigned to them
- ✓ Can filter "My Tasks" to see only their assignments

#### Test 6.3: Audit Trail Attribution
**Steps:**
1. User A: Create task
2. User B: Edit same task
3. View audit log in database

**Expected Results:**
- ✓ Create action logged with User A's name
- ✓ Edit action logged with User B's name
- ✓ Timestamps correct for each action

---

### Test Suite 7: Edge Cases & Error Handling

#### Test 7.1: Database Connection Loss
**Steps:**
1. Stop PostgreSQL service
2. Try to create a task

**Expected Results:**
- ✓ Error message: "Database connection failed"
- ✓ No crash
- ✓ Can retry after database restored

#### Test 7.2: Network Timeout
**Steps:**
1. Simulate slow/timeout scenario
2. Try to load board

**Expected Results:**
- ✓ Loading indicator shown
- ✓ Timeout error after reasonable wait
- ✓ Can retry

#### Test 7.3: Invalid User Session
**Steps:**
1. Login successfully
2. Manually delete session from database
3. Try to perform action (create task, etc.)

**Expected Results:**
- ✓ Error: "Session expired" or similar
- ✓ Prompted to login again
- ✓ No crash

#### Test 7.4: Long Strings
**Steps:**
1. Create task with very long title (200+ chars)
2. Create task with very long description (5000+ chars)

**Expected Results:**
- ✓ Title truncated on card but full in detail
- ✓ Description scrollable in detail dialog
- ✓ No display issues

#### Test 7.5: Special Characters
**Steps:**
1. Create task with title: "Test <script>alert('xss')</script>"
2. Create task with emojis: "Task with emojis 🚀 🎉 ✨"
3. Create task with quotes: 'Task with "quotes" and \'apostrophes\''

**Expected Results:**
- ✓ HTML/script tags escaped (no XSS)
- ✓ Emojis display correctly
- ✓ Quotes handled properly
- ✓ No SQL injection

---

### Test Suite 8: Performance & Stress Testing

#### Test 8.1: Large Task Count
**Steps:**
1. Use seed script or manually create 100+ tasks
2. Load board
3. Scroll through columns
4. Use search/filter

**Expected Results:**
- ✓ Board loads within 3 seconds
- ✓ Scrolling smooth
- ✓ Search responsive
- ✓ No lag or freeze

#### Test 8.2: Rapid Actions
**Steps:**
1. Quickly create 10 tasks in succession
2. Quickly move 10 tasks between columns
3. Quickly add 20 comments to one task

**Expected Results:**
- ✓ All actions processed
- ✓ No duplicates or lost actions
- ✓ UI remains responsive

#### Test 8.3: Long Session
**Steps:**
1. Login with "Remember me"
2. Keep application open for several hours
3. Perform actions periodically

**Expected Results:**
- ✓ Session remains valid
- ✓ No memory leaks
- ✓ Performance stable

---

## Test Results Template

Use this template to track your testing:

```
Test ID: [e.g., 1.1]
Test Name: [e.g., Initial Login]
Date: [YYYY-MM-DD]
Tester: [Your name]
Status: [ ] Pass / [ ] Fail / [ ] Blocked
Notes: [Any observations]
Issues Found: [List any bugs]
```

---

## Known Issues & Limitations

### Current Limitations
1. **No drag-and-drop** - Must edit task to move columns (backend ready)
2. **No file upload UI** - Backend ready, UI not implemented
3. **No auto-refresh** - Must manually click refresh for updates
4. **No My Tasks view** - Can filter but no dedicated dashboard
5. **No reports/charts** - Statistics available but no visual reports

### Workarounds
- **Moving tasks**: Click task → Edit → Change column → Save
- **Multi-user updates**: Click Refresh button periodically
- **Finding my tasks**: Use "Assigned To" filter

---

## Bug Report Template

If you find issues, please document using this format:

```
Bug ID: BUG-[number]
Severity: [ ] Critical / [ ] High / [ ] Medium / [ ] Low
Title: [Brief description]
Steps to Reproduce:
1. [Step 1]
2. [Step 2]
3. [Step 3]

Expected Result:
[What should happen]

Actual Result:
[What actually happened]

Screenshots/Logs:
[Attach if available]

Environment:
- OS: [Windows 10/11]
- Python Version: [3.11+]
- Database: [PostgreSQL version]
```

---

## Testing Completion Checklist

Mark each test suite as you complete it:

- [ ] Test Suite 1: Authentication & User Management (9 tests)
- [ ] Test Suite 2: Task Creation & Management (10 tests)
- [ ] Test Suite 3: Comments System (5 tests)
- [ ] Test Suite 4: Search & Filter (6 tests)
- [ ] Test Suite 5: Board Operations (5 tests)
- [ ] Test Suite 6: Multi-User Scenarios (3 tests)
- [ ] Test Suite 7: Edge Cases & Error Handling (5 tests)
- [ ] Test Suite 8: Performance & Stress Testing (3 tests)

**Total: 46 tests**

---

## Post-Testing Actions

After completing all tests:

1. **Document all bugs** found using the bug report template
2. **Prioritize bugs** by severity
3. **Report to developer** with clear reproduction steps
4. **Re-test after fixes** to verify resolution
5. **Sign off** when all critical/high bugs resolved

---

## Contact & Support

For questions or issues during testing:
- Check database logs: `logs/activity_log.jsonl`
- Check PostgreSQL logs
- Run backend tests: `python scripts/test_kanban_backend.py`
- Review documentation: `docs/KANBAN_SETUP.md`












