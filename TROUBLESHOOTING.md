# Music DLP - Quick Troubleshooting Guide

**Created**: 2026-02-09
**For**: Phase 5 GUI Testing

---

## GUI Won't Launch

### Issue: Running `python main.py` shows an error

**Fixed Issue**: There was a bug in line 113 of main.py that has been corrected.

**Try this**:
```bash
cd c:\Users\amiel\OneDrive\Documents\yt-dlp\Music-dlp\2026-2
python main.py
```

### Issue: "ModuleNotFoundError: No module named 'customtkinter'"

**Solution**:
```bash
pip install customtkinter
```

### Issue: Window doesn't appear but no error

**Possible causes**:
1. Window opened behind other windows - **Check your taskbar**
2. Window opened on another monitor
3. Window minimized on startup

**Try**:
- Alt+Tab to switch windows
- Check all monitors
- Look for "Music DLP" in taskbar

### Issue: "FFmpeg not found" error dialog

**Solution**: Install FFmpeg and add to PATH
1. Download from: https://ffmpeg.org/download.html
2. Extract to a folder (e.g., `C:\ffmpeg`)
3. Add to PATH:
   - Windows: Settings → System → About → Advanced System Settings → Environment Variables
   - Add `C:\ffmpeg\bin` to Path variable
4. Restart terminal and try again

---

## Testing the GUI

### Quick Functionality Test

Once the GUI opens, test these features:

**1. Window Appears**
- [ ] Can you see the main window?
- [ ] All panels visible (Playlists, Songs, Pipeline, Logs)?
- [ ] Menu bar at top with theme button and settings?

**2. Theme Toggle**
- [ ] Click the theme button (☀️ Light or 🌙 Dark)
- [ ] Does the theme change?
- [ ] Try cycling through themes

**3. Settings Dialog**
- [ ] Click "⚙️ Settings" button
- [ ] Does dialog open with 5 tabs?
- [ ] Can you navigate between tabs?
- [ ] Click Save or Cancel to close

**4. Log Panel**
- [ ] Do you see logs at the bottom?
- [ ] Should show "GUI logging initialized" and "Main window initialized"
- [ ] Are logs color-coded?

**5. Add Playlist (Without Actually Adding)**
- [ ] Type in the URL field
- [ ] Does typing work?
- [ ] Click Add (dialog should open asking for URL)

---

## Running Tests

### Run All Phase 5 Tests

```bash
cd c:\Users\amiel\OneDrive\Documents\yt-dlp\Music-dlp\2026-2
python test_phase5.py --test-all
```

**Expected Output**:
```
TEST SUMMARY
============================================================
[PASS] Imports
[PASS] Component Creation
[PASS] Dialog Creation
[PASS] Worker Threading
[PASS] Main Window Creation

Total: 5/5 tests passed

[SUCCESS] All tests passed!
```

### If Tests Fail

**Check Python version**:
```bash
python --version
# Should be Python 3.10 or higher
```

**Check all dependencies**:
```bash
python -c "import customtkinter, tkinter, PIL, threading, queue; print('All dependencies OK')"
```

**Check database**:
```bash
python -c "from core.database import Database; db = Database(); print('Database OK'); db.close()"
```

---

## Common Errors and Solutions

### Error: "not enough values to unpack"

**Cause**: Bug in main.py (already fixed)
**Solution**: Make sure you have the latest version of main.py

### Error: "Database is locked"

**Cause**: Another instance is running
**Solution**:
- Close all Python processes
- Delete `music_dlp.db.lock` if it exists
- Restart

### Error: "Config validation failed"

**Cause**: Invalid config.ini
**Solution**:
- Delete `config.ini`
- Restart app (will create default config)

### Error: "Ollama not responding"

**This is OK!** Ollama is optional. You'll see a warning but the app will still work. You just won't be able to use AI processing until you install Ollama.

**To install Ollama** (optional):
1. Download from: https://ollama.com/download
2. Install and run
3. Install models:
   ```bash
   ollama pull gemma3:12b
   ollama pull qwen3:14b
   ollama pull qwen2.5:7b
   ```

---

## Logs and Debugging

### Where to Find Logs

Log file location: `logs/music_dlp_20260209.log`

**View logs**:
```bash
# View last 50 lines
tail -50 logs/music_dlp_20260209.log

# Or open in text editor
notepad logs/music_dlp_20260209.log
```

### Understanding Log Levels

- `[INFO]` - Normal operation (green)
- `[WARNING]` - Something unexpected but not critical (yellow)
- `[ERROR]` - Something failed (red)
- `[DEBUG]` - Detailed diagnostic info

### Enable Debug Logging

Edit `config.ini`:
```ini
[Logging]
log_level = DEBUG
```

Restart the app and check logs for more details.

---

## What to Report

If you're still having issues, please provide:

1. **Error message** (exact text)
2. **What you were doing** when error occurred
3. **Operating System** version
4. **Python version**: `python --version`
5. **Last 20 lines of log file**:
   ```bash
   tail -20 logs/music_dlp_20260209.log
   ```
6. **Test results**:
   ```bash
   python test_phase5.py --test-all
   ```

---

## Quick Command Reference

```bash
# Launch GUI
python main.py

# Run all tests
python test_phase5.py --test-all

# Test specific components
python test_phase5.py --test-components

# Check Python version
python --version

# Check dependencies
python -c "import customtkinter; print('CustomTkinter:', customtkinter.__version__)"

# View logs
tail -20 logs/music_dlp_20260209.log

# Check FFmpeg
ffmpeg -version
```

---

## Still Not Working?

If none of the above helps, try:

1. **Clean start**:
   ```bash
   # Backup your database if you have data
   copy music_dlp.db music_dlp_backup.db

   # Delete database and config
   del music_dlp.db
   del config.ini

   # Restart
   python main.py
   ```

2. **Reinstall dependencies**:
   ```bash
   pip install --upgrade --force-reinstall customtkinter
   ```

3. **Check for conflicting processes**:
   - Close all Python processes
   - Close all terminal windows
   - Restart fresh

4. **Try test mode**:
   ```bash
   python test_phase5.py --test-gui
   ```

---

## Success Indicators

✅ **GUI is working if**:
- Window opens and displays all panels
- Theme toggle changes colors
- Settings dialog opens and closes
- Logs appear in bottom panel
- No error messages in terminal

✅ **Ready for Phase 6 if**:
- All Phase 5 tests pass (5/5)
- GUI launches consistently
- No critical errors in logs
- Basic features work (theme, settings, dialogs)

---

**Need Help?**: Check the log file first, then run tests, then report the specific error message.

**Next Step**: Once everything works, you're ready for Phase 6 (Packaging & Distribution)!
