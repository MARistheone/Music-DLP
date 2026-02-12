# Phase 5 Start Prompt - Music DLP Project

**Copy and paste this entire prompt to start Phase 5 implementation:**

---

I'm continuing the Music DLP project. Please read my handoff documentation to understand where we left off.

**Project location**: `c:\Users\amiel\OneDrive\Documents\yt-dlp\Music-dlp\2026-2\`

## Current Status

✅ **Phase 1**: Core Infrastructure (database, config, logger) - COMPLETE
✅ **Phase 2**: Download System (yt-dlp, metadata, thumbnails) - COMPLETE
✅ **Phase 3**: AI Processing with Ollama - COMPLETE
✅ **Phase 4**: Conversion System (FFmpeg, metadata embedding) - COMPLETE
⏳ **Phase 5**: GUI Implementation - READY TO START

**Overall Progress**: 67% complete (~5,945 lines of code)

## Required Reading

Please read these files in order:

1. **HANDOFF.md** - Current project status and architecture
2. **C:\Users\amiel\.claude\plans\idempotent-sauteeing-barto.md** - Full implementation plan
3. **PHASE4_SUMMARY.md** - Summary of Phase 4 completion

## Pre-Implementation Checks

**BEFORE starting Phase 5 implementation, please verify:**

### 1. Project Structure Check
```bash
# Verify all Phase 1-4 modules exist
ls core/database.py core/config_manager.py core/logger.py
ls downloaders/yt_dlp_manager.py downloaders/metadata_extractor.py downloaders/thumbnail_processor.py
ls ai/ollama_client.py ai/prompts.py ai/title_processor.py
ls converters/ffmpeg_converter.py converters/metadata_embedder.py
ls test_phase2.py test_phase3.py test_phase4.py
```

### 2. Database Schema Check
```python
# Verify database tables exist
python -c "from core.database import Database; db = Database(); cursor = db.conn.cursor(); cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table'\"); print([row[0] for row in cursor.fetchall()]); db.close()"
```
Expected output: `['playlists', 'videos', 'playlist_videos', 'ai_title_attempts', 'approved_metadata', 'app_config']`

### 3. CustomTkinter Installation Check
```python
# CRITICAL: CustomTkinter must be installed for Phase 5
python -c "import customtkinter; print(f'CustomTkinter version: {customtkinter.__version__}')"
```

If CustomTkinter is not installed:
```bash
pip install customtkinter
```

### 4. Python Dependencies Check
```python
# Verify all required packages are installed
python -c "import customtkinter, tkinter, PIL, threading, queue; print('All Phase 5 dependencies available')"
```

### 5. Previous Phases Functionality Check

Run quick tests to ensure Phase 1-4 are working:

```bash
# Test Phase 4 (Conversion System)
python test_phase4.py --test-ffmpeg
python test_phase4.py --test-mp3

# Verify all phases pass
python test_phase4.py --test-all
```

### 6. Review Implementation Plan Section

Read the implementation plan section on **Phase 4: GUI Foundation** and **Phase 5: GUI Completion** (lines 1025-1043):
- Understand CustomTkinter architecture
- Review main window layout
- Check component structure
- Understand threading requirements

## Phase 5 Implementation Task

**Once all checks pass**, implement the GUI System:

### Files to Create:

#### Phase 5A: Main Window & Components (~1,200 lines)

1. **`gui/__init__.py`**
   - Package initialization
   - Export main classes

2. **`gui/main_window.py`** (~400 lines)
   - Main application window
   - Layout management (grid system)
   - Theme switching (light/dark/system)
   - Menu bar setup
   - Component initialization
   - Event handling

3. **`gui/components/playlist_panel.py`** (~250 lines)
   - Left panel: Playlist list
   - Add/delete playlists
   - Playlist selection
   - Video count display
   - Checkbox for batch operations

4. **`gui/components/song_panel.py`** (~300 lines)
   - Right panel: Song table/list
   - Video display with status icons
   - Download status indicators
   - AI processing indicators
   - Approval status checkmarks
   - Context menu (right-click)

5. **`gui/components/pipeline_panel.py`** (~200 lines)
   - Pipeline stage buttons (Extract, Download, AI Process, Review, Convert)
   - Progress bar
   - Status text display
   - Current operation display

6. **`gui/components/log_panel.py`** (~150 lines)
   - Scrolling log viewer
   - Color-coded log levels
   - Auto-scroll to bottom
   - Clear logs button
   - Integration with core.logger

#### Phase 5B: Dialogs & Workers (~1,400 lines)

7. **`gui/dialogs/add_playlist_dialog.py`** (~150 lines)
   - Simple URL input dialog
   - URL validation
   - Add to database

8. **`gui/dialogs/settings_dialog.py`** (~400 lines)
   - Tabbed settings interface
   - Appearance tab (theme, font size)
   - Download tab (cookies, format, sleep intervals)
   - AI tab (Ollama URL, models, workers)
   - Output tab (bitrates, formats, directories)
   - Logging tab (level, file rotation)
   - Save/cancel buttons

9. **`gui/dialogs/ai_review_dialog.py`** (~450 lines)
   - **CRITICAL**: Batch AI review window
   - Side-by-side comparison of 3 AI models
   - Navigation (Previous/Next buttons)
   - Manual editing fields
   - Regenerate AI button
   - Approve & Next button
   - Progress indicator (Song X of Y)
   - Original title display

10. **`gui/workers/download_worker.py`** (~150 lines)
    - Background thread for downloads
    - Progress callbacks to GUI
    - Error handling
    - Cancel support

11. **`gui/workers/ai_worker.py`** (~150 lines)
    - Background thread for AI processing
    - Progress callbacks to GUI
    - Error handling
    - Cancel support

12. **`gui/workers/conversion_worker.py`** (~150 lines)
    - Background thread for conversions
    - Progress callbacks to GUI
    - Error handling
    - Cancel support

#### Phase 5C: Application Entry Point (~100 lines)

13. **`main.py`** (~100 lines)
    - Application entry point
    - Initialize database, config, logger
    - Create and run main window
    - Error handling

#### Phase 5D: Testing (~400 lines)

14. **`test_phase5.py`** (~400 lines)
    - GUI initialization tests
    - Component creation tests
    - Event handling tests
    - Threading tests
    - Integration tests

### Critical Requirements:

1. **Threading is MANDATORY**
   - All long-running operations (download, AI, conversion) MUST use separate threads
   - NEVER block the GUI thread
   - Use threading.Thread or Queue for communication
   - Use workers from `gui/workers/` modules

2. **Follow existing patterns**
   - Use Database class for data access
   - Use ConfigManager for settings
   - Use logger from core.logger
   - Follow error handling patterns from Phase 2-4

3. **CustomTkinter Best Practices**
   - Use CTk widgets (CTkButton, CTkLabel, etc.)
   - Use grid() layout manager consistently
   - Support light/dark/system themes
   - Use CTkScrollableFrame for scrolling content
   - Use CTkTabview for tabbed interfaces

4. **GUI Integration Hooks**
   - All backend modules already have progress callbacks
   - Connect these callbacks to GUI progress bars
   - Update status text in real-time
   - Show errors in log panel

5. **Database updates**
   - Refresh GUI when database changes
   - Update playlist/song lists
   - Show status indicators
   - Handle concurrent access

6. **Logging Integration**
   - Use GUILogHandler from core.logger
   - Display logs in log panel
   - Color-code by level (INFO=green, WARNING=yellow, ERROR=red)
   - Auto-scroll to latest

### Implementation Order:

1. Start with `main.py` (entry point)
2. Then `gui/main_window.py` (main window)
3. Then `gui/components/` (UI components one by one)
4. Then `gui/workers/` (threading workers)
5. Then `gui/dialogs/` (modal dialogs)
6. Finally `test_phase5.py` (comprehensive tests)
7. Test thoroughly before marking complete

## Success Criteria

Phase 5 is complete when:

- ✅ Main window launches and displays correctly
- ✅ Can add playlist URL
- ✅ Can extract playlist metadata (Stage 1)
- ✅ Can download videos (Stage 2) without blocking GUI
- ✅ Can process with AI (Stage 3) without blocking GUI
- ✅ Can review AI suggestions in batch dialog (Stage 4)
- ✅ Can convert to MP3/M4A (Stage 5) without blocking GUI
- ✅ All components display correctly
- ✅ Theme switching works (light/dark/system)
- ✅ Settings dialog saves configuration
- ✅ Logs display in real-time
- ✅ Progress bars update correctly
- ✅ No GUI freezing or blocking
- ✅ Test suite passes all tests
- ✅ Full workflow works end-to-end

## Important Notes from Project Memory

From MEMORY.md:

1. **Don't Block GUI Thread**: All downloads, AI processing, conversions must use separate threads
2. **Use gui/workers/ modules**: Download, AI, and conversion workers
3. **Update GUI via callbacks**: Use after() method for thread-safe GUI updates
4. **Threading Pattern**:
   ```python
   from gui.workers import DownloadWorker

   def on_download_click():
       worker = DownloadWorker(videos, callback=self.update_progress)
       worker.start()

   def update_progress(self, video_id, progress):
       # This runs in worker thread
       self.after(0, lambda: self._update_gui(video_id, progress))

   def _update_gui(self, video_id, progress):
       # This runs in GUI thread
       self.progress_bar.set(progress)
   ```

5. **AI Review Dialog**: Most complex component
   - Show original YouTube title
   - Show 3 AI suggestions side-by-side
   - Allow manual editing
   - Navigate between songs
   - Save approved metadata to database

## Questions to Ask If Unclear

If anything is unclear before starting:

- Ask about CustomTkinter widget usage
- Ask about threading patterns
- Ask about GUI update strategies
- Ask about layout management

## After Phase 5 Completion

When Phase 5 is done:

1. Update HANDOFF.md with Phase 5 completion
2. Create PHASE5_README.md with GUI usage instructions
3. Create PHASE5_SUMMARY.md with session summary
4. Test full end-to-end workflow:
   - Launch GUI
   - Add playlist
   - Extract → Download → AI Process → Review → Convert
   - Verify MP3/M4A files created
   - Import to Spotify and verify

## GUI Design Reference

From the implementation plan, the main window layout:

```
┌────────────────────────────────────────────────────────────────────┐
│  Music DLP                                    [Light/Dark] [⚙️ Settings]│
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  Playlist URL: [_________________________________] [Add]  │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                    │
│  ┌─ Playlists ──────────────┬─ Songs ─────────────────────────┐  │
│  │ ☑ Playlist Name 1 (24)  │ #  Title         Status  AI  ✓  │  │
│  │ ☐ Playlist Name 2 (18)  │ 1  Song Title 1  ⬇️ Done  🤖  ✓  │  │
│  │                          │ 2  Song Title 2  ⏸️ Pend  -   -  │  │
│  │ [Refresh] [Delete]       │ [Select All] [Download Selected] │  │
│  └──────────────────────────┴──────────────────────────────────┘  │
│                                                                    │
│  ┌─ Pipeline ──────────────────────────────────────────────────┐  │
│  │ [1. Extract]  [2. Download]  [3. AI Process]  [4. Review]   │  │
│  │  Progress: ████████████░░░░░░░░░░░░ 12/24 (50%)           │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌─ Logs ──────────────────────────────────────────────────────┐  │
│  │ [INFO] 14:23:45 - Playlist extracted: 24 videos             │  │
│  │ [SUCCESS] 14:24:12 - Downloaded: video.opus (4.2 MB)        │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

## Start Implementation

Once all pre-checks pass, begin implementing Phase 5 starting with the main.py entry point and main_window.py.

**Key Components**:
1. Main window with grid layout
2. Playlist panel (left)
3. Song panel (right)
4. Pipeline panel (middle)
5. Log panel (bottom)
6. AI review dialog (modal)
7. Settings dialog (modal)
8. Threading workers

**Estimated Complexity**: Medium-High
- CustomTkinter is straightforward
- Threading requires care
- AI review dialog is complex
- Lots of UI code but straightforward

Good luck! 🚀

---

**Note**: This is the most visible part of the application. Take time to make the UI clean, responsive, and user-friendly. The backend is solid, now we need a great frontend!
