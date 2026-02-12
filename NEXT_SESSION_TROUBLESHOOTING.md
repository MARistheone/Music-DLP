# Next Session: Systematic AttributeError Troubleshooting

## Current Problem

The application has **AttributeError exceptions throughout** - missing methods being called that don't exist in the classes.

### Known Errors:

1. **SettingsDialog**: `'SettingsDialog' object has no attribute 'format_entry'`
   - Location: When saving settings
   - Missing: `format_entry` attribute

2. **Database**: `'Database' object has no attribute 'delete_playlist'`
   - Location: When deleting playlists
   - Missing: `delete_playlist()` method

### Impact:

User reports: "There are attribute errors absolutely everywhere. Each time I try a new feature basically."

This indicates **widespread missing implementations** across multiple classes.

---

## Session Goals

### 1. Comprehensive Audit

Run a **full codebase scan** to find all method calls that reference non-existent attributes/methods:

```bash
# Scan for all AttributeError risk patterns
grep -r "self\." gui/ core/ downloaders/ ai/ converters/
```

### 2. Identify Missing Methods

Create a **missing methods inventory**:

**Classes to Audit**:
- [ ] `core/database.py` - Database class
- [ ] `core/config_manager.py` - ConfigManager class
- [ ] `gui/dialogs/settings_dialog.py` - SettingsDialog class
- [ ] `gui/dialogs/ai_review_table_dialog.py` - AIReviewTableDialog class
- [ ] `gui/components/playlist_panel.py` - PlaylistPanel class
- [ ] `gui/components/song_panel.py` - SongPanel class
- [ ] `gui/main_window.py` - MainWindow class

**For Each Class**:
1. List all method calls (`self.method_name()` or `object.method_name()`)
2. Check if method exists in class definition
3. Document missing methods

### 3. Systematic Fixes

**Priority Order**:

1. **Critical Database Methods** (data integrity)
   - [ ] `delete_playlist()`
   - [ ] `delete_video()`
   - [ ] Any CRUD operations
   - [ ] Relationship methods

2. **Settings Dialog Methods** (user configuration)
   - [ ] `format_entry` attribute
   - [ ] Save/load for each setting
   - [ ] Validation methods

3. **GUI Component Methods** (user interactions)
   - [ ] Event handlers
   - [ ] Refresh/update methods
   - [ ] Selection methods

4. **Worker Thread Methods** (background operations)
   - [ ] Progress callbacks
   - [ ] Error handlers

---

## Recommended Approach

### Step 1: Static Analysis

```python
# Create a script to find all method calls
import ast
import os

def find_method_calls(file_path):
    """Parse Python file and extract all method calls."""
    with open(file_path, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read())

    # Find all attribute access (self.method or obj.method)
    method_calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            method_calls.append(node.attr)

    return set(method_calls)

def find_method_definitions(file_path):
    """Parse Python file and extract all method definitions."""
    with open(file_path, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read())

    methods = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            methods.append(node.name)

    return set(methods)

# Compare calls vs definitions
calls = find_method_calls('core/database.py')
definitions = find_method_definitions('core/database.py')
missing = calls - definitions
print(f"Missing methods: {missing}")
```

### Step 2: Create Implementation Stubs

For each missing method, create a stub:

```python
def missing_method(self, *args, **kwargs):
    """TODO: Implement this method."""
    raise NotImplementedError(f"missing_method not yet implemented")
```

This makes errors explicit rather than AttributeError.

### Step 3: Implement by Priority

Focus on **most-used methods first**:

1. Database CRUD (add, get, update, delete)
2. Settings save/load
3. GUI refresh/update
4. Event handlers

### Step 4: Test Each Fix

After implementing each method:
- [ ] Test the specific feature
- [ ] Check logs for new AttributeErrors
- [ ] Document what was fixed

---

## Specific Known Issues to Fix

### Issue 1: SettingsDialog.format_entry

**Error**: `'SettingsDialog' object has no attribute 'format_entry'`

**Investigation**:
1. Search for `self.format_entry` in `gui/dialogs/settings_dialog.py`
2. Check if it's supposed to be:
   - An attribute (e.g., `self.format_entry = ctk.CTkEntry(...)`)
   - A method (e.g., `def format_entry(self): ...`)
   - Something else (e.g., `self.download_format_entry`)

**Likely Fix**: Rename `self.format_entry` to `self.format_entry` (the actual widget name) in save method.

### Issue 2: Database.delete_playlist()

**Error**: `'Database' object has no attribute 'delete_playlist'`

**Investigation**:
1. Check if method exists in `core/database.py`
2. Check if it's called from `gui/components/playlist_panel.py`

**Implementation Needed**:
```python
def delete_playlist(self, playlist_id: str) -> bool:
    """
    Delete a playlist and its relationships.

    Args:
        playlist_id: Playlist ID to delete

    Returns:
        True if deleted, False otherwise
    """
    try:
        cursor = self.conn.cursor()

        # Delete playlist (CASCADE will delete playlist_videos)
        cursor.execute("DELETE FROM playlists WHERE playlist_id = ?", (playlist_id,))

        self.conn.commit()
        return True

    except Exception as e:
        self.conn.rollback()
        raise Exception(f"Failed to delete playlist: {e}")
```

### Issue 3: Other Missing Methods

**To Be Discovered**:
- Run the app and trigger each feature
- Document every AttributeError
- Create a comprehensive list

---

## Testing Checklist

After fixes, test **every major feature**:

### Main Window
- [ ] Open application
- [ ] Switch themes
- [ ] Open settings
- [ ] Check logs display

### Playlist Management
- [ ] Add playlist
- [ ] Select playlist
- [ ] **Delete playlist** ⚠️ (known issue)
- [ ] Refresh playlist

### Song Management
- [ ] View songs
- [ ] Select songs
- [ ] Extract metadata
- [ ] Download songs

### AI Processing
- [ ] Process single song
- [ ] Process multiple songs
- [ ] View AI results
- [ ] Regenerate AI

### Review Workflow
- [ ] Open review table
- [ ] Select rows
- [ ] Bulk approve
- [ ] Bulk reprocess
- [ ] Edit individual song

### Settings
- [ ] Open settings dialog
- [ ] Change appearance
- [ ] **Save settings** ⚠️ (known issue)
- [ ] Change AI settings
- [ ] Save and close

### Conversion
- [ ] Convert approved songs
- [ ] Check output files
- [ ] Verify metadata

---

## Session Execution Plan

```
Phase 1: Discovery (30 min)
├─ Run static analysis script
├─ Document all missing methods
└─ Prioritize by frequency/impact

Phase 2: Database Fixes (45 min)
├─ Implement CRUD methods
├─ Test with actual operations
└─ Verify data integrity

Phase 3: Settings Dialog Fixes (30 min)
├─ Fix attribute references
├─ Test save/load
└─ Verify all tabs work

Phase 4: GUI Component Fixes (45 min)
├─ Fix event handlers
├─ Fix refresh methods
└─ Test all interactions

Phase 5: Integration Testing (30 min)
├─ Run through full workflow
├─ Document any new errors
└─ Create fix list for next session
```

---

## Expected Outcomes

After this session:
- ✅ **Zero AttributeError exceptions** for basic operations
- ✅ **All critical methods implemented** (Database, Settings, GUI)
- ✅ **Documentation of remaining TODOs** (if any)
- ✅ **Clean test run** through main workflow

---

## Files to Focus On

### High Priority (Most Likely to Have Missing Methods):

1. **`core/database.py`**
   - Missing: CRUD operations
   - Expected methods: delete_playlist, delete_video, update_*, bulk_*

2. **`gui/dialogs/settings_dialog.py`**
   - Missing: Widget references, save logic
   - Expected: All widget attributes, save_* methods

3. **`gui/components/playlist_panel.py`**
   - Missing: Event handlers
   - Expected: delete, refresh, select handlers

4. **`gui/components/song_panel.py`**
   - Missing: Selection/filter methods
   - Expected: get_*, filter_*, refresh methods

### Medium Priority:

5. **`gui/main_window.py`**
6. **`gui/dialogs/ai_review_table_dialog.py`**
7. **`gui/workers/*.py`**

---

## Success Criteria

✅ **Session is successful when**:
1. Can add and **delete** a playlist without errors
2. Can open settings, change values, and **save** without errors
3. Can process songs through entire pipeline (extract → download → AI → review → convert)
4. Can open review table, select songs, and approve/reprocess
5. No AttributeError exceptions in any common workflow

---

## Commands to Run

### 1. Find All Method Calls vs Definitions

```python
# Save as find_missing_methods.py
import ast
import os
from pathlib import Path

def analyze_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            tree = ast.parse(f.read(), filename=str(file_path))
        except:
            return None, None

    # Find calls
    calls = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            calls.add(node.attr)

    # Find definitions
    definitions = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            definitions.append(node.name)

    return calls, set(definitions)

# Analyze all Python files
for py_file in Path('.').rglob('*.py'):
    if 'venv' in str(py_file) or '__pycache__' in str(py_file):
        continue

    calls, defs = analyze_file(py_file)
    if calls and defs:
        missing = calls - defs
        if missing:
            print(f"\n{py_file}:")
            print(f"  Missing: {missing}")
```

### 2. Grep for Common Patterns

```bash
# Find all self.method_name patterns
grep -rn "self\.\w\+(" --include="*.py" gui/ core/ | grep -v "def "

# Find all db.method_name patterns
grep -rn "db\.\w\+(" --include="*.py" gui/

# Find all config.method_name patterns
grep -rn "config\.\w\+(" --include="*.py" gui/
```

---

## Additional Context

- **Project**: Music DLP - YouTube playlist downloader with AI metadata cleaning
- **Tech Stack**: Python, CustomTkinter, SQLite, yt-dlp, Ollama AI
- **Phase**: GUI Implementation (Phase 5) - mostly complete but buggy
- **Previous Work**:
  - Core infrastructure complete
  - Download system working
  - AI processing working
  - Conversion working
  - NEW: Table-based review dialog created
  - Settings dialog updated

---

**Start Next Session With**:
"I need to systematically fix all AttributeError exceptions in the Music DLP application. Please read NEXT_SESSION_TROUBLESHOOTING.md and follow the execution plan to audit and fix all missing methods."
