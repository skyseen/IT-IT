# IT Admin Automation Toolkit - User Manual

**Version 1.0**  
**Created by: INGRASYS IT Team**  
**Collaboration: CODEX & CLAUDE**

---

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Main Dashboard](#main-dashboard)
   - [Operations Center](#operations-center)
4. [User Management Module](#user-management-module)
   - [Create New User Email](#create-new-user-email)
   - [Disable User Email Access](#disable-user-email-access)
5. [SAP Integration Module](#sap-integration-module)
   - [Process SAP S4 Account Creation](#process-sap-s4-account-creation)
   - [SAP S4 Account Support](#sap-s4-account-support)
6. [Agile Integration Module](#agile-integration-module)
   - [Create Agile Account](#create-agile-account)
   - [Reset Agile Password](#reset-agile-password)
7. [Settings & Configuration](#settings--configuration)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

---

## Introduction

The **IT Admin Automation Toolkit** is a comprehensive desktop application designed to streamline IT administrative tasks for the INGRASYS IT team. This tool automates email creation, account management, and integration with SAP and Agile systems.

### Key Features

✅ **User Management** - Create and disable user email accounts  
✅ **SAP Integration** - Automate SAP account creation and support requests  
✅ **Agile Integration** - Manage MFG and RD Agile accounts and password resets  
✅ **Email Automation** - Automatic email generation with templates and attachments  
✅ **Batch Processing** - Handle multiple users simultaneously  
✅ **Configurable Settings** - Customize paths, recipients, and email signatures  

---

## Getting Started

### System Requirements

- **Operating System**: Windows 10 or later
- **Python**: Version 3.8 or higher
- **Microsoft Outlook**: Installed and configured
- **Dependencies**: tkinter, pandas, win32com

### Launching the Application

1. Navigate to the application directory
2. Run the command: `python app.py`
3. The main dashboard will appear centered on your screen

### First Time Setup

1. Click the **⚙ Settings** button in the header
2. Configure the following:
   - **Paths**: Set directories for Excel files, save folders, and screenshot directories
   - **Email Recipients**: Verify email addresses for SAP and Agile notifications
   - **Signature**: Customize your email signature

---

## Main Dashboard

The refreshed dashboard is organised into modern tabs that group related workflows while keeping the familiar automation
actions untouched. Use the tab strip near the top of the window to switch between the following workspaces:

* **User Ops** – Launch user onboarding and off-boarding email automations.
* **SAP** – Access SAP account creation previews, support ticket submissions, and disable workflows.
* **Agile** – Prepare Agile account creation or password reset requests with ticket evidence.
* **Telecom** – Run the Singtel and M1 billing processors with guided confirmations.
* **Operations Center** – Monitor live activity logs, audit events, and refresh them on demand.

The header retains the ASCII banner and proudly displays the current environment profile alongside a real-time timestamp. A
status bar at the bottom summarises the active profile and streams the most recent activity, giving operators immediate feedback
without interrupting the flow of work. Press **ESC** at any time to exit the application, and use the **⚙ Settings** button in the
header to configure environments or recipients.

### Navigation Tips

* **Mouse or keyboard tabs** – Use the tab strip or press `Ctrl+Tab`/`Ctrl+Shift+Tab` to cycle between modules.
* **Scroll within tabs** – Each tab supports vertical scrolling for long forms, with content automatically centred on resize.
* **Activity toast** – Watch the status bar for confirmation or error details immediately after a workflow runs.

### Operations Center

The **Operations Center** tab provides a live audit feed of all major workflows. Entries display timestamps, categories, and a
succinct description of each action (for example, “SAP disable email dispatched” or “M1 bill processed”). Use the **Refresh**
button to reload historical events (up to the most recent 120 entries), and keep the panel open while running automations to
observe progress in real time.

Key highlights:

* **Streaming events** – Actions logged from any tab append to the Operations Center automatically.
* **Colour-aligned log view** – The dark, high-contrast panel is designed to match the rest of the console.
* **At-a-glance troubleshooting** – Error level entries appear in the log and in the status bar, helping you respond quickly.

---

## User Management Module

### Create New User Email

**Purpose**: Generate email workbooks for new employee setup and automatically send notification emails to the IT team.

#### Step-by-Step Instructions

1. **Click** "✉ Create New User Email" on the main dashboard

2. **Fill in User Details**:
   - **User Name**: Employee's login username (e.g., john.doe)
   - **First Name**: Employee's first name
   - **Last Name**: Employee's last name
   - **Display Name**: Full name as it should appear
   - **Job Title**: Employee's position
   - **Department**: Department/team name
   - **Employee ID**: Company employee ID (e.g., SGP80937, S60382)

3. **Add User to Queue**:
   - After filling all fields, click **"➕ Add User"**
   - The user will appear in the queue list
   - Repeat for multiple users if needed

4. **Review Queue**:
   - Check the list of users to be processed
   - To remove a user: Select them and click **"➖ Remove Selected"**

5. **Submit**:
   - Click **"✅ Submit All"** when ready
   - Confirm the batch operation in the dialog

#### What Happens Next

✅ An Excel workbook is created for each user in the specified save folder  
✅ A summary email is sent to `kenyi.seen@ingrasys.com` (or configured recipient)  
✅ Email includes the list of new users and their details  
✅ Success message confirms completion  

#### Example Use Case

**Scenario**: Three new employees are joining the Sales department.

```
User 1:
- User Name: alice.chen
- First Name: Alice
- Last Name: Chen
- Display Name: Alice Chen
- Job Title: Sales Manager
- Department: Sales
- Employee ID: S60450

User 2:
- User Name: bob.wang
- First Name: Bob
- Last Name: Wang
- Display Name: Bob Wang
- Job Title: Sales Representative
- Department: Sales
- Employee ID: S60451

User 3:
- User Name: carol.liu
- First Name: Carol
- Last Name: Liu
- Display Name: Carol Liu
- Job Title: Sales Coordinator
- Department: Sales
- Employee ID: SGP80940
```

Add all three users to the queue, review, and submit in one batch operation.

---

### Disable User Email Access

**Purpose**: Process email access disable requests for departing employees or access revocations.

#### Step-by-Step Instructions

1. **Click** "🚫 Disable User Email Access" on the main dashboard

2. **Fill in User Details**:
   - **User Name**: Employee's username to be disabled
   - **Display Name**: Employee's full name
   - **Employee ID**: Company employee ID

3. **Add to Queue**:
   - Click **"➕ Add User"**
   - User appears in the disable queue
   - Add multiple users if needed

4. **Review and Submit**:
   - Verify the list of users to be disabled
   - Click **"✅ Submit All"**
   - Confirm the operation

#### What Happens Next

✅ Email sent to configured recipients requesting account disable  
✅ List includes all users scheduled for disabling  
✅ Confirmation message appears on success  

#### Important Notes

⚠️ **Warning**: This action initiates the disable process. Ensure all information is correct.  
📋 **Tip**: Always verify employee IDs before submission.

---

## SAP Integration Module

### Process SAP S4 Account Creation

**Purpose**: Automate SAP account creation requests for multiple users using consolidated Excel data.

#### Prerequisites

- Consolidated Excel file with existing SAP user data
- Individual user Excel files (generated from User Management module)
- Access to the save folder containing user workbooks

#### Step-by-Step Instructions

1. **Click** "🔄 Process SAP S4 Account Creation" on the main dashboard

2. **Select Consolidated Excel File**:
   - File browser opens automatically
   - Navigate to your SAP consolidated data file
   - Select the Excel file containing existing SAP accounts
   - Click "Open"

3. **Select User Excel Files**:
   - File browser allows multiple selections
   - Hold **Ctrl** to select multiple files
   - Select all new user workbooks to process
   - Click "Open"

4. **Review Preview**:
   - A preview window shows:
     - Number of users to be processed
     - User details for each account
     - Consolidated data summary
   - Scroll through the preview to verify information

5. **Send Email**:
   - Click **"Send Email"** in the preview window
   - Email is automatically generated and sent
   - Success message confirms delivery

#### Preview Window Details

```
┌─────────────────────────────────────────┐
│  SAP S4 Account Creation - Preview      │
├─────────────────────────────────────────┤
│                                         │
│  User 1: alice.chen (S60450)           │
│  User 2: bob.wang (S60451)             │
│  User 3: carol.liu (SGP80940)          │
│                                         │
│  Total Users: 3                        │
│  Consolidated Data: 150 records        │
│                                         │
│  [Send Email]    [Cancel]              │
└─────────────────────────────────────────┘
```

#### What Happens Next

✅ Email sent to `raymond.lin@fii-foxconn.com`  
✅ CC'd to specified recipients (Alex Ng, Wong Chin Lun, etc.)  
✅ Consolidated Excel file attached  
✅ Individual user workbooks attached  
✅ Formatted email body with user list  

#### Email Format

**Subject**: Please help to create SAP S4 Account for new user - S60450, S60451, SGP80940

**Body**:
```
Hi Raymond Lin,

Please help to create SAP S4 account for below new user.

1. alice.chen (S60450)
2. bob.wang (S60451)
3. carol.liu (SGP80940)

[Your Signature]
```

---

### SAP S4 Account Support

**Purpose**: Submit SAP account support requests, such as password resets and account reactivation.

#### Step-by-Step Instructions

1. **Click** "🛠 SAP S4 Account Support" on the main dashboard

2. **Select Support Type**:
   - **Reset Password**: Currently available
   - **Reactivate Account**: Coming soon (disabled)

3. **Fill in Required Information**:
   - **Employee ID**: User's company employee ID
   - **Ticket Number**: ServiceNow or support ticket reference
   - **Screenshot**: Click "📎 Select Screenshot" to attach ticket screenshot

4. **Select Screenshot**:
   - File browser opens to ticket image directory (if configured)
   - Select a PNG, JPG, or other image file
   - Filename appears after selection

5. **Submit Request**:
   - Review all information
   - Click **"Submit"**
   - Confirm submission

#### What Happens Next

✅ Email sent to `raymond.lin@fii-foxconn.com`  
✅ Subject includes employee ID and request type  
✅ Ticket screenshot embedded in email body  
✅ Ticket number included for reference  
✅ Confirmation message on success  

#### Email Format

**Subject**: Please help to reset password for SGP80871

**Body**:
```
Hi Raymond Lin,

Please help to reset password for user with Employee ID: SGP80871.

Ticket #: S0000YF30

[Embedded Screenshot]

[Your Signature]
```

#### Tips

💡 **Screenshot Quality**: Use clear, readable screenshots  
💡 **Ticket Number**: Always include the official ticket reference  
💡 **Response Time**: Check your email for Raymond's response  

---

## Agile Integration Module

### Create Agile Account

**Purpose**: Request new Agile account creation for MFG (Manufacturing) and/or RD (Research & Development) systems.

#### Step-by-Step Instructions

1. **Click** "➕ Create Agile Account" on the main dashboard

2. **Select System(s)**:
   - ☑️ **MFG Agile**: For manufacturing system access
   - ☐ **RD Agile**: For R&D system access
   - You can select both if the user needs access to both systems

3. **Enter Ticket Information**:
   - **Ticket Number**: ServiceNow ticket ID (e.g., S0000YEXP)

4. **Add Employee IDs**:
   - **Employee ID**: Enter one employee ID
   - Click **"+ Add"** to add to the list
   - Repeat for multiple users
   - Each user appears numbered in the queue: `[01] S60382`, `[02] S60807`, etc.

5. **Remove Users** (if needed):
   - Select a user from the list
   - Click **"− Remove Selected"**

6. **Upload Ticket Screenshot**:
   - Click **"📎 Select Screenshot"**
   - Choose the ticket screenshot image
   - Filename displays after selection

7. **Enter Ticket Content**:
   - Paste the ticket description/content in the text area
   - Include relevant details from the ticket

8. **Submit Request**:
   - Click **"Submit"**
   - Confirm all information is correct

#### What Happens Next

✅ Email sent to `zhong.yang@fii-foxconn.com`  
✅ CC'd to team (Lingyun Niu, Alex Ng, Wong Chin Lun, Oscar Loo, Lim Chin Yong)  
✅ Subject includes account type and all employee IDs  
✅ Ticket screenshot embedded in email  
✅ Ticket content included in email body  

#### Email Format

**Subject**: Please help to create MFG Agile Account for new user - S60382, S60807, SGP80937

**Body**:
```
Hi Yang Zhong,

Please help to create MFG Agile account for below user.

Ticket #: S0000YEXP

[Embedded Screenshot]

--- Ticket Content ---
[Pasted ticket description]

[Your Signature]
```

#### System Selection Guide

| System | When to Use |
|--------|-------------|
| **MFG Agile** | User works in manufacturing, production planning, or shop floor operations |
| **RD Agile** | User works in product development, engineering, or research |
| **Both** | User requires access to both manufacturing and R&D systems |

#### Example Workflow

**Scenario**: New engineer needs both MFG and RD access.

1. Check both ☑️ MFG Agile and ☑️ RD Agile
2. Enter ticket: `S0000YEXP`
3. Add employee: `SGP80937`
4. Upload ticket screenshot
5. Paste ticket content:
   ```
   Request Agile access for new engineer John Doe.
   Requires both MFG and RD systems for cross-functional role.
   Start date: 2025-10-01
   Manager: Jane Smith
   ```
6. Submit

---

### Reset Agile Password

**Purpose**: Request password resets for MFG or RD Agile accounts.

#### Step-by-Step Instructions

1. **Click** "🔑 Reset Agile Password" on the main dashboard

2. **Select System**:
   - ☑️ **MFG Agile**: Reset MFG system password
   - ☐ **RD Agile**: Reset RD system password
   - Select only one system per request

3. **Enter Request Details**:
   - **Ticket Number**: ServiceNow ticket reference
   - **Employee ID**: User whose password needs reset

4. **Upload Ticket Screenshot**:
   - Click **"📎 Select Screenshot"**
   - Select the ticket screenshot image

5. **Submit**:
   - Click **"Submit"**
   - Confirm the request

#### What Happens Next

✅ Email sent to `zhong.yang@fii-foxconn.com`  
✅ CC'd to IT team members  
✅ Subject specifies system and employee ID  
✅ Ticket screenshot embedded  
✅ Password reset processed by Agile admin  

#### Email Format

**Subject**: Please help to reset MFG Agile password for SGP80871

**Body**:
```
Hi Yang Zhong,

Please help to reset MFG Agile account for below user.

Ticket #: S0000YF30

[Embedded Screenshot]

[Your Signature]
```

#### Common Scenarios

| Scenario | Steps |
|----------|-------|
| User forgot password | 1. Get ticket from user<br>2. Select system<br>3. Enter details<br>4. Submit |
| Password expired | 1. Verify ticket<br>2. Confirm employee ID<br>3. Submit reset request |
| Account locked | 1. Check ticket for lock reason<br>2. Submit reset request<br>3. Follow up if unlock needed |

---

## Settings & Configuration

### Accessing Settings

1. Click the **⚙ Settings** button in the main dashboard header.
2. The Settings dialog opens with four tabs: **Profiles & Backups**, **Paths**, **Email Recipients**, and **Signature**.

### Profiles & Backups Tab

Manage environment-specific settings from this tab.

* **Active profile selector** – Choose the configuration profile to edit. The active profile is mirrored in the dashboard status bar.
* **Create profile** – Enter a new name (e.g., `UAT` or `Production-Asia`) and click **Create Profile** to clone the current setup.
* **Delete profile** – Remove non-default profiles when they are no longer required. The default profile cannot be deleted.
* **Recent backups** – Review the automatic snapshots generated whenever settings change. Files are stored under `config_backups/`.

Switching profiles instantly loads their saved paths, recipients, and signatures, helping teams separate production and testing
environments without manual file swaps.

### Paths Tab

Configure file and folder locations for the selected profile:

| Setting | Description | Example |
|---------|-------------|---------|
| **Consolidated Excel** | Path to SAP consolidated data file | `C:\IT\SAP\consolidated.xlsx` |
| **New User Save Folder** | Where to save generated user workbooks | `C:\IT\NewUsers\` |
| **SAP Ticket Image Dir** | Default folder for SAP ticket screenshots | `C:\IT\Screenshots\SAP\` |
| **Agile Ticket Image Dir** | Default folder for Agile ticket screenshots | `C:\IT\Screenshots\Agile\` |

Use the **Browse** buttons to update entries. Settings are stored per profile, allowing different environments to point to their
own network drives.

### Email Recipients Tab

Customise To/CC lists used by the automation emails (again per profile). Enter addresses separated by semicolons (`;`). The
defaults mirror the previous version of the toolkit and can be reinstated by copying from the table below.

| Workflow | Default To | Default CC |
|----------|------------|------------|
| New User | `benni.yh.tsao@ingrasys.com; rayliao@ingrasys.com` | `lingyun.niu@foxconn.com.sg; alex.ng@ingrasys.com; chinlun.wong@ingrasys.com; chinyong.lim@ingrasys.com; oscar.loo@ingrasys.com` |
| Disable User | `benni.yh.tsao@ingrasys.com; rayliao@ingrasys.com` | `lingyun.niu@foxconn.com.sg; alex.ng@ingrasys.com; chinlun.wong@ingrasys.com; chinyong.lim@ingrasys.com; oscar.loo@ingrasys.com` |
| SAP Creation/Support | `raymond.lin@fii-foxconn.com` | `kenyi.seen@ingrasys.com; chinlun.wong@ingrasys.com; chinyong.lim@ingrasys.com; oscar.loo@ingrasys.com` |
| Agile Creation/Reset | `zhong.yang@fii-foxconn.com` | `lingyun.niu@foxconn.com.sg; kenyi.seen@ingrasys.com; chinlun.wong@ingrasys.com; oscar.loo@ingrasys.com; chinyong.lim@ingrasys.com` |

### Signature Tab

Edit the shared email signature for the active profile.

1. Update the text area (supports plain text or HTML).
2. Include your name, job title, contact details, and any compliance statements.
3. Save to apply the signature across all automated emails for that profile.

**Default Signature**:

```
Best Regards,

[Your Name]
IT Administrator
INGRASYS Technology Inc.
Email: your.name@ingrasys.com
Tel: +65 XXXX XXXX
```

### Saving Settings & Versioning

* Changes are saved per profile when you click **Save**.
* Every save creates a timestamped backup under `config_backups/` with a changelog entry visible in the Profiles tab.
* The status message beneath the dialog confirms when updates succeed or warns if validation fails.

### Recovering or Resetting

* To restore a previous configuration, copy a backup JSON from `config_backups/` back to the main directory and rename it to
  `it_tool_config.json` (while the app is closed).
* To start from scratch, delete `it_tool_config.json` and the backups folder, then relaunch the application to regenerate defaults.

---

## Troubleshooting

### Common Issues and Solutions

#### Issue: "Path not found" error

**Solution**:
1. Open Settings (⚙)
2. Go to Paths tab
3. Verify all paths exist
4. Use "Browse..." to set correct paths
5. Save settings

---

#### Issue: Outlook email not sending

**Possible Causes**:
- Outlook not running
- Outlook not configured
- Network connection issue

**Solution**:
1. Ensure Microsoft Outlook is running
2. Check Outlook is configured with your email account
3. Test by sending a manual email in Outlook
4. Verify network connectivity
5. Restart the application

---

#### Issue: Excel file not found

**Solution**:
1. Verify the Excel file exists in the expected location
2. Check file permissions (read access required)
3. Ensure file is not open in another program
4. Update path in Settings if file moved

---

#### Issue: Screenshot not embedding in email

**Solution**:
1. Verify image file format (PNG, JPG, JPEG, BMP, GIF supported)
2. Check file is not corrupted (open in image viewer)
3. Ensure file size is reasonable (< 5MB recommended)
4. Try a different image format

---

#### Issue: Cannot add users to queue

**Solution**:
1. Ensure all required fields are filled
2. Check for special characters in fields
3. Verify employee ID format is correct
4. Try closing and reopening the form

---

#### Issue: Application won't start

**Solution**:
1. Check Python is installed: `python --version`
2. Verify dependencies: `pip install -r requirements.txt`
3. Check for error messages in terminal
4. Delete `__pycache__` folder and try again
5. Check `it_tool_config.json` for corruption

---

#### Issue: Window not centered or responsive

**Solution**:
1. Restart the application
2. Try resizing the window manually
3. Check display scaling settings in Windows
4. Update to latest version of the tool

---

### Error Messages Explained

| Error Message | Meaning | Solution |
|---------------|---------|----------|
| `NameError: name 'X' is not defined` | Code variable missing | Restart app, contact developer if persists |
| `FileNotFoundError` | File path incorrect | Check Settings > Paths |
| `PermissionError` | Cannot access file/folder | Check file permissions, close file if open |
| `QUEUE_EMPTY` | No users in queue | Add at least one user before submitting |
| `INPUT_ERROR` | Required field missing | Fill in all required fields |
| `SELECTION_ERROR` | No item selected | Select an item from the list first |

---

### Getting Help

If you encounter issues not covered here:

1. **Check Settings**: Verify all paths and email settings
2. **Review Logs**: Check terminal/console for error messages
3. **Restart Application**: Often resolves temporary issues
4. **Contact IT Team**:
   - Email: kenyi.seen@ingrasys.com
   - Subject: "IT Toolkit Support - [Brief Description]"
   - Include: Error message, steps to reproduce, screenshots

---

## Best Practices

### Daily Operations

✅ **Start of Day**:
- Launch the application
- Verify Outlook is running
- Check settings are configured

✅ **During Use**:
- Double-check employee IDs before submission
- Keep ticket screenshots organized in designated folders
- Review queues before submitting batches
- Save work frequently (batch operations)

✅ **End of Day**:
- Complete all pending requests
- Close the application properly (ESC or window close)
- Verify all emails were sent successfully

### Batch Processing Tips

💡 **Efficiency**:
- Group similar requests together
- Process new users in batches of 5-10
- Verify one sample before processing large batches

💡 **Accuracy**:
- Use copy-paste for employee IDs to avoid typos
- Keep a checklist of processed users
- Review preview windows carefully

💡 **Organization**:
- Maintain consistent folder structure
- Name screenshot files clearly (e.g., `Ticket_S0000YEXP.png`)
- Archive old workbooks monthly

### Email Management

📧 **Recipients**:
- Keep recipient lists updated in Settings
- Verify email addresses before first use
- Test with a sample email to yourself

📧 **Attachments**:
- Keep screenshots under 5MB
- Use PNG or JPG format for best compatibility
- Rename files descriptively before attaching

📧 **Content**:
- Keep ticket content concise but complete
- Include all relevant ticket information
- Proofread before sending

### File Management

📁 **Organization**:
```
IT_Admin_Files/
├── NewUsers/
│   ├── 2025-10/
│   │   ├── alice.chen_S60450.xlsx
│   │   ├── bob.wang_S60451.xlsx
│   │   └── carol.liu_SGP80940.xlsx
│   └── 2025-11/
├── Screenshots/
│   ├── SAP/
│   │   ├── Ticket_S0000YF30.png
│   │   └── Ticket_S0000YF31.png
│   └── Agile/
│       ├── Ticket_S0000YEXP.png
│       └── Ticket_S0000YEXQ.png
└── SAP/
    └── consolidated.xlsx
```

📁 **Maintenance**:
- Archive old files monthly
- Keep current month easily accessible
- Back up important data regularly

### Security

🔒 **Data Protection**:
- Do not share employee data outside authorized systems
- Close application when away from desk
- Lock your computer when leaving

🔒 **Email Safety**:
- Verify recipient addresses before sending
- Do not forward automated emails
- Report suspicious activity to IT security

### Quality Assurance

✔️ **Checklist Before Submission**:

**New User Email**:
- [ ] All user fields filled correctly
- [ ] Employee IDs verified
- [ ] Display names formatted properly
- [ ] Department names accurate

**SAP Account Creation**:
- [ ] Consolidated file is latest version
- [ ] User workbooks are correct
- [ ] Preview shows all expected users
- [ ] Email recipients verified

**Agile Requests**:
- [ ] Correct system selected (MFG/RD)
- [ ] Ticket number accurate
- [ ] Screenshot is clear and readable
- [ ] Employee IDs confirmed
- [ ] Ticket content complete

### Time-Saving Shortcuts

⚡ **Keyboard Shortcuts**:
- **ESC**: Exit application
- **Tab**: Move to next field
- **Enter**: Activate focused button (in some dialogs)
- **Ctrl+C / Ctrl+V**: Copy and paste employee IDs

⚡ **Mouse Shortcuts**:
- **Scroll wheel**: Navigate long forms
- **Click and drag**: Resize window
- **Double-click**: Open file browsers faster

---

## Appendix

### Employee ID Formats

INGRASYS uses multiple employee ID formats:

| Format | Example | Description |
|--------|---------|-------------|
| **S-format** | S60382 | Standard employee ID |
| **SGP-format** | SGP80937 | Singapore office employees |
| **CNX-format** | CNX12345 | China office employees |

### System Access Matrix

| Department | SAP Access | MFG Agile | RD Agile |
|------------|------------|-----------|----------|
| Manufacturing | Yes | Yes | No |
| R&D | Yes | No | Yes |
| Engineering | Yes | Yes | Yes |
| Sales | Yes | No | No |
| HR | Yes | No | No |
| IT | Yes | Yes | Yes |
| Finance | Yes | No | No |

### Ticket Number Formats

| System | Format | Example |
|--------|--------|---------|
| ServiceNow | S0000XXXX | S0000YF30 |
| Internal IT | IT-YYYY-NNNN | IT-2025-0123 |
| SAP | SAPXXXXXXXX | SAP000012345 |

### Contact Directory

| Role | Name | Email | Extension |
|------|------|-------|-----------|
| IT Admin | Alex Ng | kenyi.seen@ingrasys.com | 1234 |
| SAP Admin | Raymond Lin | raymond.lin@fii-foxconn.com | 5678 |
| Agile Admin | Yang Zhong | zhong.yang@fii-foxconn.com | 9012 |
| IT Manager | Wong Chin Lun | chinlun.wong@ingrasys.com | 3456 |

### Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-09-30 | Initial release with all modules |
| - | - | User Management, SAP, Agile integration |
| - | - | Modern UI with balanced dark theme |
| - | - | Responsive centered layout |

---

## Quick Reference Card

### Most Common Tasks

**Create New User**:
1. Click "✉ Create New User Email"
2. Fill all 7 fields
3. Click "➕ Add User"
4. Click "✅ Submit All"

**SAP Account Creation**:
1. Click "🔄 Process SAP S4 Account Creation"
2. Select consolidated Excel
3. Select user Excel files
4. Review preview
5. Click "Send Email"

**Agile Account Creation**:
1. Click "➕ Create Agile Account"
2. Check MFG/RD boxes
3. Enter ticket number
4. Add employee IDs
5. Upload screenshot
6. Paste ticket content
7. Click "Submit"

**Reset Agile Password**:
1. Click "🔑 Reset Agile Password"
2. Select system
3. Enter ticket and employee ID
4. Upload screenshot
5. Click "Submit"

---

## Glossary

- **Batch Processing**: Handling multiple users/requests in a single operation
- **Consolidated Excel**: Master SAP data file containing existing user accounts
- **Employee ID**: Unique identifier assigned to each company employee
- **Queue**: Temporary list of users pending processing
- **Screenshot**: Image capture of support ticket for reference
- **ServiceNow**: Company ticketing system for IT requests
- **Signature**: Personalized email footer with contact information
- **Workbook**: Excel file generated for each new user

---

**End of User Manual**

*For technical support, contact: kenyi.seen@ingrasys.com*  
*Last updated: September 30, 2025*  
*Document version: 1.0*
