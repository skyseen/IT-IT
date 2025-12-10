# IT-IT Deployment Guide

## 📁 Files to Distribute to IT Users

After building, distribute the **entire `dist\IT-IT\` folder**. The folder contains:

```
dist\IT-IT\
├── IT-IT.exe              ← Main application (double-click to run)
├── _internal\             ← Required runtime files (DO NOT DELETE)
│   ├── python311.dll
│   ├── PySide6\
│   ├── config\            ← Bundled config templates
│   └── ... (many DLLs)
├── config\                ← User configuration
│   └── kanban_config.json ← Database config (EDIT THIS)
├── logs\                  ← Application logs
└── kanban_attachments\    ← Kanban file attachments
```

### Distribution Options

**Option 1: Copy Folder** (Simplest)
1. Copy the entire `dist\IT-IT\` folder to a shared network drive or USB
2. Users copy the folder to their PC (e.g., `C:\IT-IT\`)
3. Users run `IT-IT.exe`

**Option 2: ZIP Archive**
1. Compress `dist\IT-IT\` to `IT-IT-v1.0.0.zip`
2. Users extract and run `IT-IT.exe`

**Option 3: Installer** (Professional)
1. Run `build\build_installer.bat` (requires Inno Setup)
2. Distribute the generated `.exe` installer

---

## 🔧 Configuration Setup

Before distributing, edit `dist\IT-IT\config\kanban_config.json`:

```json
{
  "environment": "production",
  "database": {
    "host": "your-database-server.com",
    "port": 5432,
    "database": "itit_kanban_prod",
    "username": "kanban_app",
    "password": "YOUR_SECURE_PASSWORD",
    "pool_size": 5,
    "max_overflow": 3
  }
}
```

⚠️ **Important**: Never commit passwords to Git! Use the template file for reference.

---

## 🛠️ How to Build the Application

### Prerequisites (One-time setup)

1. **Install Python 3.11** from https://www.python.org/downloads/release/python-3119/
   - Install to `C:\Python311\` or default location
   - ✅ Check "Add Python to PATH"

2. **First build creates virtual environment automatically**

### Build Steps

1. **Open PowerShell/Command Prompt** in the project folder:
   ```
   C:\Users\Kenyi.Seen\Documents\GitHub\IT-IT\
   ```

2. **Run the build script**:
   ```batch
   .\build\build_exe_py311.bat
   ```

3. **Wait 2-5 minutes** for the build to complete

4. **Test the EXE**:
   ```
   dist\IT-IT\IT-IT.exe
   ```

5. **Configure and distribute** the `dist\IT-IT\` folder

### Build Output

- `dist\IT-IT\` - **Distributable folder** (give this to users)
- `build\IT-IT\` - Temporary build files (can be deleted)
- `build_venv\` - Build virtual environment (keep for future builds)

---

## 📌 Version Management

### Updating Version

Edit `version.py` before building:

```python
__version__ = "1.1.0"           # Increment for each release
__build_date__ = "2024-12-05"   # Update build date
```

### Version History (Add entries here)

| Version | Date       | Changes |
|---------|------------|---------|
| 1.0.0   | 2024-12-04 | Initial release |

### Viewing Version

- **At startup**: Version is logged to console (if visible)
- **In logs**: Check `dist\IT-IT\logs\` folder
- **In code**: Import from `version.py`

---

## 🔄 Release Checklist

Before each release:

- [ ] Update `__version__` in `version.py`
- [ ] Update `__build_date__` in `version.py`
- [ ] Update version in `build\IT-IT.spec` (APP_VERSION)
- [ ] Test locally: `python app.py`
- [ ] Build EXE: `.\build\build_exe_py311.bat`
- [ ] Test EXE: `dist\IT-IT\IT-IT.exe`
- [ ] Update `config\kanban_config.json` with production settings
- [ ] Create ZIP or installer for distribution
- [ ] Tag release in Git: `git tag v1.0.0`

---

## ❓ Troubleshooting

### "Failed to load Python DLL"
- **Cause**: Running wrong EXE (from `build\` instead of `dist\`)
- **Fix**: Run `dist\IT-IT\IT-IT.exe`, NOT `build\IT-IT\IT-IT.exe`

### "Config file not found"
- **Cause**: Missing `config\kanban_config.json`
- **Fix**: Create/copy config file to `dist\IT-IT\config\kanban_config.json`

### "No module named 'tkinter'"
- **Cause**: tkinter excluded in build
- **Fix**: Remove 'tkinter' from excludes in `build\IT-IT.spec`, rebuild

### Build fails
1. Delete `build\IT-IT\` and `dist\IT-IT\` folders
2. Run build again: `.\build\build_exe_py311.bat`

### App crashes on startup
1. Run from command line to see error:
   ```
   cd dist\IT-IT
   .\IT-IT.exe
   ```
2. Check `dist\IT-IT\logs\` for error logs

---

## 📞 Support

For issues, check:
1. This guide's Troubleshooting section
2. Log files in `dist\IT-IT\logs\`
3. Build warnings in `build\IT-IT\warn-IT-IT.txt`



