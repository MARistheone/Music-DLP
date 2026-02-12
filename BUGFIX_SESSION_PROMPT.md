# Bug Fixing & Polish Session - Music DLP Project

**Copy and paste this entire prompt to start the next bug-fixing session:**

---

## Session Context

I'm continuing work on the Music DLP project. We've completed Phase 5 (GUI Implementation) and fixed critical bugs to get the core functionality working. Now I need to continue identifying and fixing issues before moving to Phase 6 (Packaging).

**Project location**: `c:\Users\amiel\OneDrive\Documents\yt-dlp\Music-dlp\2026-2\`

---

## Current Status (As of 2026-02-09)

### ✅ What's Working

**Core Functionality:**
- ✅ GUI launches successfully
- ✅ Playlist extraction (Stage 1) - extracts videos and stores in database
- ✅ Video downloads (Stage 2) - downloads audio files and thumbnails
- ✅ AI processing setup (Stage 3) - processor initializes correctly

**Fixed Bugs (Previous Session):**
1. ✅ Directory creation - fixed property name mismatch in `main.py`
2. ✅ MetadataExtractor parameters - fixed in `download_worker.py`
3. ✅ Database method name - `link_video_to_playlist` in `metadata_extractor.py`
4. ✅ Extraction return value unpacking - fixed tuple handling
5. ✅ YTDLPManager initialization - fixed parameter passing
6. ✅ ThumbnailProcessor initialization - fixed parameter passing
7. ✅ Download method call - changed to `download_audio()` with correct params
8. ✅ Thumbnail method call - changed to `download_and_process()`
9. ✅ Video format mismatch - fixed `get_selected_videos()` to return dicts
10. ✅ TitleProcessor initialization - fixed parameters for AI processing
11. ✅ AI processing method - changed to `process_single_video()`
12. ✅ AI result handling - fixed to handle `List[ProcessingResult]`

### ⚠️ Known Issues

**Dependencies:**
- ⚠️ Ollama service must be running manually (not auto-started)
- ⚠️ Missing AI models (qwen3:14b, qwen2.5:7b) - only gemma3:12b installed
- ⚠️ JavaScript runtime warning from yt-dlp (non-critical, optional fix)
- ⚠️ Cookies file required for reliable YouTube downloads (user must configure)

**Untested Functionality:**
- ❓ Stage 3: AI Processing (needs Ollama running with all models)
- ❓ Stage 4: Review & Approve (batch review dialog)
- ❓ Stage 5: Convert & Export (FFmpeg conversion, metadata embedding)
- ❓ Error handling for edge cases
- ❓ GUI responsiveness during long operations
- ❓ Cancel functionality for background operations

### 📋 Architecture Overview

**Five-Stage Pipeline:**
```
Stage 1: Extract    → MetadataExtractor extracts playlist/video info
Stage 2: Download   → YTDLPManager downloads audio + ThumbnailProcessor gets images
Stage 3: AI Process → TitleProcessor runs 3 models in parallel
Stage 4: Review     → User reviews/approves AI-generated metadata (GUI dialog)
Stage 5: Convert    → AudioConverter creates MP3+M4A with metadata
```

**Key Files:**
- `main.py` - Application entry point
- `core/database.py` - SQLite database manager
- `core/config_manager.py` - Configuration handler
- `gui/main_window.py` - Main GUI window
- `gui/workers/` - Background threading workers
- `downloaders/` - yt-dlp integration
- `ai/` - Ollama AI processing
- `converters/` - FFmpeg audio conversion

---

## Instructions for This Session

### STEP 1: Review Issue Report

The user will provide issues they've encountered in this format:

```
Issue: [Brief description]
Stage: [Which pipeline stage: Extract/Download/AI/Review/Convert]
Error Log: [Paste relevant error messages]
Expected: [What should happen]
Actual: [What actually happened]
```

### STEP 2: Reproduce & Diagnose

For each issue:
1. **Read the relevant code files** to understand the current implementation
2. **Identify the root cause** - look for parameter mismatches, logic errors, missing methods
3. **Explain the issue** clearly to the user

### STEP 3: Fix & Verify

For each fix:
1. **Make the necessary code changes** using Edit tool
2. **Explain what you changed and why**
3. **Ask user to test** the specific functionality

### STEP 4: Track Progress

Use the **TodoWrite tool** to track bugs being fixed:

```
✅ Bug: [Description] - FIXED
⏳ Bug: [Description] - IN PROGRESS
📋 Bug: [Description] - PENDING
```

---

## Common Bug Patterns to Watch For

Based on previous session, watch for these patterns:

### 1. Parameter Mismatch Pattern
**Symptom**: `TypeError: __init__() got an unexpected keyword argument 'X'`

**Cause**: Worker passing wrong parameters to class constructors

**Fix**:
- Read the class `__init__()` to see what parameters it expects
- Update the worker to pass correct parameters from config

### 2. Return Value Mismatch Pattern
**Symptom**: `TypeError: 'X' object is not subscriptable` or `string indices must be integers`

**Cause**: Method returns different type than caller expects

**Fix**:
- Check method signature and return type
- Update caller to unpack/handle return value correctly

### 3. Missing Method Pattern
**Symptom**: `AttributeError: 'X' object has no attribute 'Y'`

**Cause**: Calling non-existent method or using old method name

**Fix**:
- Use `Grep` to find actual method name
- Update caller to use correct method

### 4. Database Type Mismatch Pattern
**Symptom**: `Error binding parameter 0 - probably unsupported type`

**Cause**: Passing wrong data type to database query

**Fix**:
- Check what type the database expects (str, int, dict, etc.)
- Convert/extract the correct type before passing

---

## Testing Checklist

As bugs are fixed, systematically test each stage:

### Stage 1: Playlist Extraction
```bash
# Test
1. Launch app: python main.py
2. Click "Add Playlist"
3. Enter URL: https://www.youtube.com/playlist?list=PLvXezMeJKDy_AgFj01TFrQUhhKkU6FEMq
4. Click "Extract"

# Expected
- Progress indicator appears
- Videos appear in song list
- Database populated with playlist + videos
- No errors in log
```

### Stage 2: Download
```bash
# Test
1. Select 1-3 videos from list (checkbox)
2. Click "Download Selected"

# Expected
- Download progress updates
- Files appear in downloads/raw/
- Thumbnails downloaded
- Database status updated to 'downloaded'
- No errors in log
```

### Stage 3: AI Processing
```bash
# Prerequisites
- Ollama must be running: ollama serve
- Models must be installed: ollama pull gemma3:12b, etc.

# Test
1. Select downloaded videos
2. Click "Process with AI"

# Expected
- AI processing progress updates
- All 3 models process each video
- AI attempts stored in database
- No errors in log
```

### Stage 4: Review & Approve
```bash
# Test
1. Select AI-processed videos
2. Click "Review & Approve"

# Expected
- Batch review dialog opens
- Shows all AI attempts for each video
- User can select preferred metadata
- Approved metadata saved to database
```

### Stage 5: Convert & Export
```bash
# Test
1. Select approved videos
2. Click "Convert & Export"

# Expected
- Conversion progress updates
- Both MP3 and M4A files created
- Metadata embedded (title, artist, album art)
- Files appear in downloads/final/
- Ready for Spotify import
```

---

## Debugging Tools & Commands

**Check Database:**
```bash
sqlite3 music_dlp.db
.tables
SELECT * FROM playlists;
SELECT * FROM videos LIMIT 5;
SELECT * FROM ai_title_attempts LIMIT 5;
.exit
```

**Check Logs:**
```bash
# View latest log
type logs\music_dlp_20260209.log | more

# Watch log in real-time (PowerShell)
Get-Content logs\music_dlp_20260209.log -Wait -Tail 20
```

**Check Dependencies:**
```bash
# FFmpeg
ffmpeg -version

# Ollama
ollama list
curl http://localhost:11434/api/tags

# Python packages
pip list | findstr "yt-dlp customtkinter"
```

**Check File System:**
```bash
# Downloaded files
dir downloads\raw
dir downloads\final

# Database
dir *.db

# Config
type config.ini
```

---

## Issue Report Template

**For the user to fill out:**

```markdown
## Issues Found

### Issue 1: [Short Description]
- **Stage**: [Extract/Download/AI/Review/Convert/Other]
- **Steps to Reproduce**:
  1. [Step 1]
  2. [Step 2]
  3. [Step 3]

- **Error Log**:
  ```
  [Paste relevant error messages here]
  ```

- **Expected Behavior**: [What should happen]
- **Actual Behavior**: [What actually happened]
- **Frequency**: [Always/Sometimes/Once]

---

### Issue 2: [Short Description]
[Same format as Issue 1]

---

### Enhancement Requests (Optional)
- [ ] [Enhancement idea 1]
- [ ] [Enhancement idea 2]
```

---

## After Bug Fixes are Complete

Once all critical bugs are fixed and all 5 stages work end-to-end:

1. **Run Full Integration Test**:
   - Add fresh playlist
   - Extract → Download → AI Process → Review → Convert
   - Verify final MP3/M4A files play correctly with metadata

2. **Update Documentation**:
   - Update HANDOFF.md with bug fixes
   - Create BUGFIX_SUMMARY.md listing all fixes
   - Note any remaining known issues

3. **Proceed to Phase 6**: Packaging & Distribution
   - See PHASE6_START_PROMPT.md for packaging instructions

---

## Important Files to Reference

**Core Implementation:**
- `core/database.py` - All database operations
- `core/config_manager.py` - Configuration management
- `gui/workers/download_worker.py` - Download/extraction worker
- `gui/workers/ai_worker.py` - AI processing worker
- `downloaders/metadata_extractor.py` - Playlist extraction
- `downloaders/yt_dlp_manager.py` - Audio downloads
- `ai/title_processor.py` - AI title processing

**Previous Documentation:**
- `HANDOFF.md` - Project overview and current status
- `PHASE5_README.md` - GUI implementation details
- `PHASE5_SUMMARY.md` - What was completed in Phase 5
- `MEMORY.md` - Project memory and lessons learned

**Test Files:**
- `test_phase5.py` - GUI component tests
- `test_phase3.py` - AI processing tests
- `test_phase2.py` - Download system tests

---

## Session Start

When the user is ready, they should say:

**"Here are the issues I found:"** and then list the issues using the template above.

Or if testing a specific stage:

**"I want to test [Stage Name]. Here's what I'm seeing:"** and describe the behavior.

---

**Ready to start fixing bugs!** 🐛🔨

**Document Version**: 1.0
**Created**: 2026-02-09
**For**: Bug Fixing & Polish Session
**Prerequisites**: Phase 5 complete, core functionality working
