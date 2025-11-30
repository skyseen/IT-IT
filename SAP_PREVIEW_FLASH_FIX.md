# SAP Preview Window Flashing/Disappearing Fix

## Problem

After fixing the blank window issue, a new problem appeared:
- Preview window would flash on screen for only **0.5 seconds**
- Window would then immediately disappear
- No error messages shown
- User couldn't interact with the window at all

## Root Cause

The issue was with the Tkinter event loop management:

### What Was Wrong

```python
# PREVIOUS ATTEMPT (Didn't work):
preview.wait_window(preview)
root.destroy()
```

**Problem:** `wait_window()` wasn't working correctly in the Qt+Tkinter mixed environment. The window would appear briefly but the event loop wouldn't properly start, causing it to disappear immediately.

### Why It Failed

1. **Mixed GUI frameworks**: Qt (PySide6) and Tkinter don't play well together
2. **Event loop conflict**: `wait_window()` expects to be in control of the event loop
3. **No proper blocking**: The function was returning immediately instead of blocking
4. **Window lifecycle**: The window was being created but not maintained

---

## Solution

Replace `wait_window()` with `root.mainloop()` and proper cleanup handlers:

### Key Changes

1. **Use `root.mainloop()` instead of `wait_window()`**
```python
# NEW (Works correctly):
root.mainloop()  # Properly blocks until root.quit() is called
```

2. **Add window close handler**
```python
def on_closing():
    preview.destroy()
    root.quit()  # Exit mainloop

preview.protocol("WM_DELETE_WINDOW", on_closing)
```

3. **Exit mainloop after successful completion**
```python
def confirm():
    # ... processing ...
    send_sap_creation_email(email_attach_paths)
    preview.destroy()
    root.quit()  # Exit mainloop after completion
```

4. **Ensure window is visible**
```python
preview.deiconify()  # Make sure window is shown
preview.lift()       # Bring to front
preview.focus_force()  # Give it focus
preview.grab_set()   # Make it modal
```

5. **Clean up after mainloop exits**
```python
root.mainloop()  # Blocks here

# After mainloop exits (user closed window or completed workflow):
try:
    root.destroy()
except:
    pass  # Window may already be destroyed
```

---

## Complete Flow

### 1. Window Creation
```python
root = tk.Tk()           # Create hidden root
root.withdraw()          # Hide it
preview = tk.Toplevel(root)  # Create visible preview
```

### 2. Setup UI Components
```python
# ... Create labels, buttons, table, etc. ...
```

### 3. Setup Close Handler
```python
def on_closing():
    preview.destroy()
    root.quit()

preview.protocol("WM_DELETE_WINDOW", on_closing)
```

### 4. Setup Confirm Handler
```python
def confirm():
    # ... Process data ...
    preview.destroy()
    root.quit()  # Exit mainloop
```

### 5. Display Window
```python
preview.deiconify()      # Show window
preview.lift()           # Bring to front
preview.focus_force()    # Give focus
preview.grab_set()       # Make modal
root.update()            # Process pending events
```

### 6. Start Event Loop (BLOCKS HERE)
```python
root.mainloop()  # ← Program execution STOPS here
                 # ← Window stays visible and interactive
                 # ← Waits for user action
```

### 7. User Interaction Paths

**Path A: User clicks X button**
```
Click X → on_closing() → preview.destroy() → root.quit() → mainloop exits
```

**Path B: User clicks Process Batch**
```
Click button → confirm() → processing → preview.destroy() → root.quit() → mainloop exits
```

### 8. Cleanup After Mainloop
```python
# Mainloop has exited
root.destroy()  # Clean up resources
# Function returns to Qt application
```

---

## Why This Works

### `mainloop()` vs `wait_window()`

| Aspect | `wait_window()` | `mainloop()` |
|--------|----------------|--------------|
| **Purpose** | Wait for a specific window | Run the entire Tk event loop |
| **Blocking** | Sometimes unreliable | Always blocks properly |
| **Control** | Limited | Full control |
| **Qt mixing** | Problematic | Works better |
| **Exit method** | Window destruction | `quit()` call |

### Event Loop Management

```
Qt Application (Main)
    ↓
    User clicks "Process SAP Creation"
    ↓
    launch_sap_flow() [Qt function]
    ↓
    build_preview_window() [Tkinter function]
    ↓
    root.mainloop() ← BLOCKS HERE
    ↓
    [User interacts with Tkinter window]
    ↓
    User action triggers root.quit()
    ↓
    mainloop() exits
    ↓
    root.destroy()
    ↓
    Function returns
    ↓
    Back to Qt Application (Main)
```

### Window Visibility

The key to keeping the window visible:

1. **`deiconify()`** - Ensures window is not iconified (minimized)
2. **`lift()`** - Brings window to front of window stack
3. **`focus_force()`** - Gives keyboard focus to window
4. **`grab_set()`** - Makes window modal (user must interact with it)
5. **`mainloop()`** - Keeps event loop running (window stays active)

---

## File Modified

**sap_workflows.py** - Lines 410-770

### Specific Changes:

1. **Line 739-740**: Added `root.quit()` after `preview.destroy()` in `confirm()`
2. **Line 742-745**: Added `on_closing()` handler function
3. **Line 747**: Added `preview.protocol("WM_DELETE_WINDOW", on_closing)`
4. **Line 755**: Added `preview.deiconify()` to ensure visibility
5. **Line 764**: Changed to `root.mainloop()` instead of `wait_window()`
6. **Line 767-770**: Added cleanup after mainloop exits

---

## Testing Instructions

### Test 1: Normal Workflow Completion
1. Click "Process SAP S4 Account Creation"
2. Select an Excel file
3. **Verify**: Preview window appears and STAYS VISIBLE ✅
4. **Verify**: You can see all content (header, table, buttons) ✅
5. **Verify**: Window remains open indefinitely ✅
6. Click "[EXECUTE] PROCESS_BATCH" button
7. Complete the workflow (select ticket, etc.)
8. **Verify**: Window closes after email is sent ✅
9. **Verify**: Control returns to main application ✅

### Test 2: Window Close (X Button)
1. Follow Test 1 steps 1-5
2. Click the X button (close button) on window title bar
3. **Verify**: Window closes immediately ✅
4. **Verify**: No error messages ✅
5. **Verify**: Control returns to main application ✅

### Test 3: Multiple Opens
1. Complete Test 1 or Test 2
2. Immediately repeat the process
3. **Verify**: Second window opens correctly ✅
4. **Verify**: No leftover windows or processes ✅

### Test 4: Window Interaction
1. Follow Test 1 steps 1-5
2. **Verify**: Can scroll through data table ✅
3. **Verify**: Can click on table rows ✅
4. **Verify**: Window stays on top ✅
5. **Verify**: Window responds to all interactions ✅

---

## Common Issues and Solutions

### Issue: Window still disappears quickly
**Possible causes:**
- Exception being thrown before mainloop
- `root.quit()` being called unexpectedly
- Resource conflict

**Debug steps:**
1. Add print statements before `root.mainloop()`
2. Check for exceptions in console/logs
3. Verify no other code is calling `root.quit()`

### Issue: Application hangs after closing window
**Possible cause:** mainloop not exiting properly

**Solution:** Ensure both close handlers call `root.quit()`:
- X button handler: `on_closing()`
- Process button handler: `confirm()`

### Issue: Can't interact with main application while window is open
**This is correct behavior!** The preview window is modal (`grab_set()`).

Users must complete or close the preview before returning to the main app.

---

## Summary

### Before This Fix
```
Window appears → 0.5 seconds → Window disappears ❌
User can't interact at all
```

### After This Fix
```
Window appears → Stays visible indefinitely → User interacts → User closes or completes → Window closes ✅
Fully interactive the entire time
```

---

## Key Takeaways

1. ✅ Use `root.mainloop()` for Qt+Tkinter mixing, not `wait_window()`
2. ✅ Always call `root.quit()` to exit mainloop properly
3. ✅ Handle both window close (X) and button completion
4. ✅ Use `deiconify()`, `lift()`, `focus_force()` for visibility
5. ✅ Clean up resources after mainloop exits
6. ✅ Modal windows require `grab_set()` for proper behavior

The preview window now works correctly and stays visible until the user explicitly closes it or completes the workflow!

