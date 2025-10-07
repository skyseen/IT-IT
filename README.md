# IT-IT Automation Toolkit

IT-IT is a desktop automation suite that streamlines day-to-day IT operations such as user onboarding, SAP administration, Agile account maintenance, and telecom billing updates. The application provides a Tkinter-based control panel that guides operators through each workflow while automatically preparing emails, Excel templates, and shared-folder artifacts required by downstream teams.

## Key Features
- **Centralized dashboard** – Launch user management, SAP, Agile, and telco workflows from a single window with contextual guidance for each task.
- **Configurable automation** – Store environment-specific paths, email recipient lists, and signature blocks in `it_tool_config.json`, editable through the in-app settings dialog.
- **Email generation** – Produce Outlook-ready messages (plain text or HTML with inline images) for new hires, account disables, SAP tickets, Agile access updates, and telco notifications.
- **Excel processing** – Convert user intake forms into standardized templates, reconcile SAP request spreadsheets, and update monthly telecom billing workbooks.
- **File orchestration** – Copy, rename, and archive supporting documents (PDF invoices, CSV extracts, request forms) into the correct shared folders for auditing.

## Repository Structure
- `app.py` – Application entry point that builds the main Tkinter window, themes, and keyboard shortcuts.
- `ui.py` – Composes dashboard sections, multi-user forms, telco dialogs, and settings management.
- `config_manager.py` / `config_utils.py` – Read, validate, and persist environment configuration used by all modules.
- `email_service.py` – Centralized Outlook automation for assembling workflow-specific emails.
- `user_workflow.py` – Generates onboarding/offboarding Excel templates from queued form entries.
- `sap_workflows.py` – Normalizes SAP request data, merges workbooks, and prepares approval previews.
- `telco_workflows.py` – Automates Singtel/M1 billing processing and reporting.
- `USER_MANUAL.md` – Detailed walkthrough of the UI, settings, and operating procedures.

## Getting Started
1. Ensure Python 3.10+ is installed on the workstation.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Review and update `it_tool_config.json` with local file paths, shared drive locations, and Outlook distribution lists.
4. Launch the application:
   ```bash
   python app.py
   ```
5. Use the **Settings** button within the app to adjust configuration values without editing JSON directly.

## Contributing
For internal teams, please:
1. Fork this repository and create a feature branch.
2. Make your changes with clear commit messages.
3. Submit a pull request summarizing the workflow improvements or fixes.
4. Attach screenshots or sample output when updating UI flows.

## Support
Consult `USER_MANUAL.md` for step-by-step guidance. For additional assistance, reach out to the IT automation team or open an issue describing the requested enhancement.
