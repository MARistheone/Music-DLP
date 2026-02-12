# Music DLP Project - Session Handoff Documentation

**Date**: 2026-02-10 (Updated)
**From**: AI Title Selection & Manual Editing Enhancement
**To**: Next Implementation Session (External AI Feature + Phase 6: Packaging)
**Status**: Phase 1-5 complete + all enhancements applied. External AI feature planned (not yet implemented).

---

## Pending Feature: External AI Export/Import

**Status**: Fully planned, not yet implemented
**Handoff Doc**: `EXTERNAL_AI_HANDOFF.md` (in project root)
**Plan File**: `C:\Users\amiel\.claude\plans\happy-dancing-book.md`

Allows users without local Ollama to export video metadata as JSON + prompt files, feed them to any external AI (ChatGPT, Claude, Gemini), and import the results back. Two files created per batch, user-configurable batch size, auto-detection of two import formats. Accessed via a "Tools" dropdown in the header bar.

**Files to create/modify:**
- NEW: `ai/external_processor.py` (~200 lines)
- MODIFY: `gui/main_window.py` (Tools button + export/import handlers)
- No changes to database.py or pipeline_panel.py

---

## Session Log: 2026-02-10 AI Title Selection & Manual Editing

### Problem Identified

Users reported that when AI titles were regenerated multiple times, the AI Review Dialog only allowed selecting the first attempt per model. Multiple attempts from the same model (e.g., "gemma3:12b" run twice) could not be distinguished or selected because radio buttons used `model_name` as the identifier, causing conflicts.

### Changes Made

**1. Fixed: Radio button value bug** (`gui/dialogs/ai_review_dialog.py`)
- **Root Cause**: Radio buttons used `model_name` (non-unique) instead of `attempt_id` (unique)
- **Impact**: Only first attempt per model was selectable; subsequent attempts from same model were invisible
- **Fix**: Changed radio button value from `model_name` to `attempt_id` throughout the dialog
- **Lines changed**: 48, 252, 277, 302, 390-394

**2. Enhanced: Attempt display to distinguish regenerations** (`gui/dialogs/ai_review_dialog.py`)
- Added generation timestamps to card headers (e.g., "Feb 10, 10:30 AM")
- Added attempt ID badges (e.g., "Attempt #123") for debugging
- Added processing time display (e.g., "Processing time: 2.34s")
- Updated radio button rowspan from 4 to 5 rows
- **Lines changed**: 305-334

**3. Added: Manual edit mode toggle** (`gui/dialogs/ai_review_dialog.py`)
- Added "Enable manual editing" checkbox to make editing intention clearer
- Edit fields now disabled by default; must be explicitly enabled
- Updated `_on_suggestion_selected()` to temporarily enable fields when populating from AI
- Added `_toggle_manual_edit()` method to control field states
- **Lines changed**: 142-159, 176-180, 343-360, 362-368

**4. Added: Delete attempt button** (`gui/dialogs/ai_review_dialog.py`)
- Red ✕ button on each suggestion card
- Confirmation dialog shows model, confidence, and title before deletion
- Automatically refreshes suggestions after deletion
- Added `_delete_attempt()` method
- **Lines changed**: 332-342, 370-394

**5. Added: Re-review capability via context menu** (`gui/components/song_panel.py`, `gui/main_window.py`)
- Right-click context menu on song items in song panel
- Menu options: "Review AI Titles..." and "Regenerate AI"
- Bound Button-3 event to each item frame
- Added `_show_context_menu()`, `_on_review_single_video()`, `_on_regenerate_single()` methods
- Wired up callbacks in main window: `_open_review_dialog_for_videos()` and `_regenerate_single_video()`
- Imported `AIReviewDialog` in main_window.py
- **Lines changed**: song_panel.py (~65 lines), main_window.py (~55 lines)

### Files Modified

1. **`gui/dialogs/ai_review_dialog.py`** - ~150 lines modified
   - Core bug fix (radio button values)
   - Display enhancements (timestamps, IDs, processing time)
   - Manual edit toggle checkbox
   - Delete attempt functionality

2. **`gui/components/song_panel.py`** - ~65 lines added
   - Context menu on right-click
   - Callback hooks for review and regenerate

3. **`gui/main_window.py`** - ~55 lines added
   - Import AIReviewDialog
   - Wire up song panel callbacks
   - Add handler methods for single-video operations

### New Capabilities

✅ **Select ANY AI attempt** - Even multiple from the same model
✅ **Distinguish attempts** - Timestamps, attempt IDs, and processing times
✅ **Delete unwanted attempts** - Clean up low-quality suggestions
✅ **Manual edit toggle** - Clearer UX for editing vs. using AI
✅ **Re-review approved songs** - Change selections after initial approval
✅ **Single-song regeneration** - Regenerate AI for individual songs

### Technical Details

- **Radio button fix**: Changed from `variable=selected_model_var, value=model_name` to `variable=selected_attempt_var, value=str(attempt_id)`
- **Timestamp parsing**: Uses `datetime.fromisoformat()` with fallback for malformed dates
- **Context menu**: Uses tkinter Menu with `tk_popup()` for right-click menus
- **Callback pattern**: Song panel exposes `on_review_callback` and `on_regenerate_callback` hooks that main window wires up

### Testing Completed

- ✅ Multiple attempts from same model are displayed and selectable
- ✅ Timestamps differentiate between regeneration runs
- ✅ Delete button removes attempts and refreshes display
- ✅ Manual edit checkbox controls field state correctly
- ✅ Right-click context menu appears on song items
- ✅ Re-review workflow opens AIReviewDialog for single songs
- ✅ Single-song regeneration triggers AI worker correctly

### Known Issues

None identified. All functionality working as expected.

---

## Session Log: 2026-02-10 Bug Fixes

### Changes Made

**1. Fixed: SQLite foreign keys disabled** (`core/database.py`)
- Added `PRAGMA foreign_keys = ON` after every database connection
- Without this, `ON DELETE CASCADE` never fired, leaving orphaned data when playlists were deleted
- Cleaned up 11 orphaned videos + 31 AI attempts + 11 approved_metadata rows from prior deletes

**2. Fixed: Thumbnails never embedded in output files** (`gui/workers/conversion_worker.py`)
- Root cause: `approved_metadata.thumbnail_path` was never populated during the approval workflow
- Added fallback: conversion worker now looks for `{video_id}_thumb.jpg` in `downloads/raw/`
- Album art will now appear in Windows Explorer, VLC, and Spotify

**3. Output split into format subdirectories** (`gui/workers/conversion_worker.py`, `core/config_manager.py`)
- MP3 files: `downloads/final/mp3/Artist - Title.mp3`
- M4A files: `downloads/final/m4a/Artist - Title.m4a`
- `ensure_directories()` now creates both subdirectories on startup

---

## 🎯 Project Overview

**Goal**: Build a modern, GUI-based application that downloads YouTube playlist songs, cleans their metadata with AI, and converts them to Spotify-compatible formats.

**Key Features**:
- Download from YouTube playlists using yt-dlp (with bot detection avoidance)
- AI-powered title cleaning (3 Ollama models: Gemma3:12B, Qwen3:14B, Qwen2.5:7B)
- Batch review workflow for approving AI-generated titles
- Convert to both MP3 (Spotify) and M4A (archival)
- Embed 300x300px thumbnails and metadata
- Modern CustomTkinter GUI with light/dark mode
- Package as standalone .exe

---

## 📋 What Has Been Completed

### ✅ Phase 1: Core Infrastructure (100% Complete)

1. **Project Structure** - All directories created:
   ```
   music-dlp/
   ├── core/                 # Core infrastructure
   ├── downloaders/          # yt-dlp integration
   ├── ai/                   # AI processing
   ├── converters/           # FFmpeg conversion
   ├── gui/                  # CustomTkinter GUI
   │   ├── components/
   │   ├── dialogs/
   │   └── workers/
   ├── utils/                # Utilities
   ├── downloads/
   │   ├── raw/             # Downloaded .opus files
   │   └── final/           # Converted MP3/M4A files
   └── logs/                # Application logs
   ```

2. **Database Module** (`core/database.py`) - **COMPLETE**:
   - SQLite database with schema v1.0
   - Tables: playlists, videos, playlist_videos, ai_title_attempts, approved_metadata, app_config
   - Full CRUD operations for all tables
   - Automatic schema initialization
   - JSON handling for tags/metadata
   - Context manager support

3. **Config Manager** (`core/config_manager.py`) - **COMPLETE**:
   - INI file configuration with sensible defaults
   - Database sync for key settings
   - Validation methods
   - Convenience properties for all settings
   - Directory management

4. **Logger Module** (`core/logger.py`) - **COMPLETE**:
   - Colored console output (with colorama)
   - File logging with rotation (10MB per file, 5 backups)
   - Custom GUI log handler for UI integration
   - Different formatters for console vs file

5. **Configuration Files**:
   - `requirements.txt` - All Python dependencies
   - `config.ini` - Default configuration template

### ✅ Phase 2: Download System (100% Complete)

1. **yt-dlp Manager** (`downloaders/yt_dlp_manager.py`) - **COMPLETE**:
   - Core yt-dlp wrapper with comprehensive bot avoidance
   - Cookie-based authentication support
   - Random sleep intervals (2-5s between downloads)
   - Progress hooks for GUI integration
   - Batch download functionality
   - Error handling with 403/bot detection recovery
   - Download statistics tracking
   - ~350 lines of robust download logic

2. **Metadata Extractor** (`downloaders/metadata_extractor.py`) - **COMPLETE**:
   - Extract playlist metadata without downloading
   - Extract individual video metadata
   - Parse video info (title, uploader, duration, thumbnail URLs)
   - Store extracted data in database
   - URL validation and type detection
   - Support for both playlists and single videos
   - ~380 lines of extraction logic

3. **Thumbnail Processor** (`downloaders/thumbnail_processor.py`) - **COMPLETE**:
   - Download thumbnails from YouTube URLs
   - Crop to center square (handles 16:9 aspect ratio)
   - Resize to 300x300px with LANCZOS quality
   - Save as JPEG with 95% quality
   - Batch processing support
   - Local image processing support
   - ~300 lines of image processing logic

4. **Testing Infrastructure**:
   - `test_phase2.py` - Comprehensive test script (400+ lines)
   - Tests for database, config, extraction, download, thumbnails
   - Integration testing support

### ✅ Phase 3: AI Processing System (100% Complete)

1. **Ollama Client** (`ai/ollama_client.py`) - **COMPLETE**:
   - Ollama API client for model communication
   - Connection and availability checking
   - Model listing and validation
   - Chat API request handling
   - JSON response parsing
   - Title generation with temperature control
   - Batch generation support
   - Comprehensive error handling
   - ~390 lines of robust API integration

2. **AI Prompts** (`ai/prompts.py`) - **COMPLETE**:
   - System prompts for Japanese music metadata
   - Hepburn romanization rules
   - Original artist extraction for covers
   - Standardized tag system (cover, vocaloid, otomad, etc.)
   - Confidence scoring guidelines
   - Response validation functions
   - Response normalization
   - Display formatting utilities
   - ~400 lines of prompt engineering

3. **Title Processor** (`ai/title_processor.py`) - **COMPLETE**:
   - Parallel processing orchestrator
   - ThreadPoolExecutor with 3 concurrent workers
   - Multi-model processing (gemma3:12b, qwen3:14b, qwen2.5:7b)
   - Database storage of AI attempts
   - Progress tracking for GUI integration
   - Batch processing support
   - Video regeneration capability
   - Processing statistics
   - ~560 lines of orchestration logic

4. **Testing Infrastructure**:
   - `test_phase3.py` - Comprehensive test script (430+ lines)
   - Ollama connection tests
   - Model availability tests
   - Title generation tests
   - Single video processing tests
   - Batch processing tests
   - Statistics display

### ✅ Phase 4: Conversion System (100% Complete)

1. **FFmpeg Converter** (`converters/ffmpeg_converter.py`) - **COMPLETE**:
   - FFmpeg-based audio conversion
   - Convert Opus → MP3 (320kbps with libmp3lame)
   - Convert Opus → M4A (320kbps AAC)
   - Audio normalization (EBU R128 loudnorm filter)
   - Progress tracking for GUI integration
   - File path sanitization
   - Audio info probing with ffprobe
   - Conversion validation
   - Comprehensive error handling
   - ~430 lines of conversion logic

2. **Metadata Embedder** (`converters/metadata_embedder.py`) - **COMPLETE**:
   - Metadata embedding using mutagen
   - ID3 tag embedding for MP3 (TIT2, TPE1, TALB, APIC, COMM)
   - MP4 atom embedding for M4A (\xa9nam, \xa9ART, \xa9alb, covr, \xa9cmt)
   - Album artwork embedding (300x300 JPEG)
   - Thumbnail validation
   - Metadata validation for both formats
   - Read metadata from files
   - Batch processing support
   - ~450 lines of metadata handling

3. **Testing Infrastructure**:
   - `test_phase4.py` - Comprehensive test script (660+ lines)
   - FFmpeg availability tests
   - MP3 conversion tests
   - M4A conversion tests
   - Metadata embedding tests
   - Integration tests
   - All tests passing (5/5)

### ✅ Phase 5: GUI Implementation (100% Complete)

1. **Application Entry Point** (`main.py`) - **COMPLETE**:
   - Dependency checks (FFmpeg, Ollama)
   - Database/config/logger initialization
   - Main window launcher
   - Error handling and graceful exit
   - ~200 lines

2. **Main Window** (`gui/main_window.py`) - **COMPLETE**:
   - Grid layout with all components
   - Theme switching (light/dark/system)
   - Menu bar with settings button
   - Pipeline stage coordination
   - ~450 lines

3. **UI Components** (4 files, ~840 lines) - **COMPLETE**:
   - `playlist_panel.py`: Playlist list with checkboxes (210 lines)
   - `song_panel.py`: Song table with status indicators (320 lines)
   - `pipeline_panel.py`: Pipeline buttons and progress (170 lines)
   - `log_panel.py`: Real-time log viewer (140 lines)

4. **Dialogs** (3 files, ~1,040 lines) - **COMPLETE**:
   - `add_playlist_dialog.py`: URL input and validation (190 lines)
   - `settings_dialog.py`: Tabbed settings interface (400 lines)
   - `ai_review_dialog.py`: Batch AI title review (450 lines)

5. **Threading Workers** (3 files, ~510 lines) - **COMPLETE**:
   - `download_worker.py`: Background extraction/downloads (180 lines)
   - `ai_worker.py`: Background AI processing (140 lines)
   - `conversion_worker.py`: Background conversions (190 lines)

6. **Testing Infrastructure**:
   - `test_phase5.py` - Comprehensive test script (400+ lines)
   - Import tests
   - Component creation tests
   - Dialog creation tests
   - Worker threading tests
   - Main window tests
   - All tests passing (5/5)

---

## 📍 Current Status

**Location**: `c:\Users\amiel\OneDrive\Documents\yt-dlp\Music-dlp\2026-2\`

**Files Created**:
```
2026-2/
├── config.ini                    ✅ Default configuration
├── requirements.txt              ✅ Python dependencies
├── test_phase2.py                ✅ Phase 2 test script (400+ lines)
├── test_phase3.py                ✅ Phase 3 test script (430+ lines)
├── test_phase4.py                ✅ Phase 4 test script (660+ lines)
├── PHASE2_README.md              ✅ Phase 2 documentation
├── PHASE3_README.md              ✅ Phase 3 documentation
├── PHASE4_README.md              ✅ Phase 4 documentation
├── PHASE3_SUMMARY.md             ✅ Phase 3 summary
├── PHASE4_SUMMARY.md             ✅ Phase 4 summary
├── SESSION_SUMMARY.md            ✅ Session progress tracking
├── core/                         ✅ Phase 1 COMPLETE
│   ├── __init__.py              ✅ Package init
│   ├── database.py              ✅ SQLite manager (650+ lines)
│   ├── config_manager.py        ✅ Config handler (280+ lines)
│   └── logger.py                ✅ Logging setup (180+ lines)
├── downloaders/                  ✅ Phase 2 COMPLETE
│   ├── __init__.py              ✅ Package init
│   ├── yt_dlp_manager.py        ✅ yt-dlp wrapper (350+ lines)
│   ├── metadata_extractor.py    ✅ Metadata extraction (380+ lines)
│   └── thumbnail_processor.py   ✅ Thumbnail processing (300+ lines)
├── ai/                           ✅ Phase 3 COMPLETE
│   ├── __init__.py              ✅ Package init
│   ├── ollama_client.py         ✅ Ollama API client (390+ lines)
│   ├── prompts.py               ✅ AI prompts (400+ lines)
│   └── title_processor.py       ✅ Parallel processor (560+ lines)
├── converters/                   ✅ Phase 4 COMPLETE
│   ├── __init__.py              ✅ Package init
│   ├── ffmpeg_converter.py      ✅ FFmpeg converter (430+ lines)
│   └── metadata_embedder.py     ✅ Metadata embedder (450+ lines)
├── main.py                       ✅ Application entry point (200 lines)
├── test_phase5.py                ✅ Phase 5 test script (400+ lines)
├── PHASE5_README.md              ✅ Phase 5 documentation
├── PHASE5_SUMMARY.md             ✅ Phase 5 summary
├── gui/                          ✅ Phase 5 COMPLETE
│   ├── __init__.py              ✅ Package init
│   ├── main_window.py           ✅ Main window (450 lines)
│   ├── components/              ✅ UI components
│   │   ├── __init__.py         ✅ Package init
│   │   ├── playlist_panel.py   ✅ Playlist list (210 lines)
│   │   ├── song_panel.py       ✅ Song table (320 lines)
│   │   ├── pipeline_panel.py   ✅ Pipeline controls (170 lines)
│   │   └── log_panel.py        ✅ Log viewer (140 lines)
│   ├── dialogs/                 ✅ Modal dialogs
│   │   ├── __init__.py         ✅ Package init
│   │   ├── add_playlist_dialog.py  ✅ URL input (190 lines)
│   │   ├── settings_dialog.py      ✅ Settings tabs (400 lines)
│   │   └── ai_review_dialog.py     ✅ AI review (450 lines)
│   └── workers/                 ✅ Threading workers
│       ├── __init__.py         ✅ Package init
│       ├── download_worker.py  ✅ Download thread (180 lines)
│       ├── ai_worker.py        ✅ AI thread (140 lines)
│       └── conversion_worker.py ✅ Conversion thread (190 lines)
├── utils/                        📁 Empty (Phase 6)
├── downloads/raw/                📁 Ready for downloads
├── downloads/final/              📁 Ready for outputs
└── logs/                         📁 Ready for logging
```

**What Works Right Now**:
- ✅ Database initialization and schema creation
- ✅ Configuration loading/saving
- ✅ Logging to console and file
- ✅ Directory management
- ✅ Playlist metadata extraction (without downloading)
- ✅ Video download with bot avoidance (cookies, sleep intervals)
- ✅ Thumbnail download and processing (300x300px)
- ✅ Database storage of playlists and videos
- ✅ Ollama API integration
- ✅ AI title cleaning with 3 models (gemma3:12b, qwen3:14b, qwen2.5:7b)
- ✅ Parallel processing with ThreadPoolExecutor
- ✅ AI attempt storage in database
- ✅ Audio conversion (Opus → MP3/M4A at 320kbps)
- ✅ Metadata embedding (ID3 tags for MP3, MP4 atoms for M4A)
- ✅ Album artwork embedding (300x300 JPEG)
- ✅ Audio normalization (EBU R128 loudnorm)
- ✅ File validation and audio info probing
- ✅ **Full GUI application with CustomTkinter**
- ✅ **Main window with all components (playlist, song, pipeline, log panels)**
- ✅ **Theme switching (light/dark/system)**
- ✅ **Add playlist dialog with URL validation**
- ✅ **Settings dialog with 5 tabs**
- ✅ **AI review dialog with batch workflow**
- ✅ **Background threading for all long operations (non-blocking GUI)**
- ✅ **Real-time progress bars and status updates**
- ✅ **Color-coded real-time log display**
- ✅ **Complete end-to-end workflow through GUI**

**Next Steps**: Phase 6 (Packaging & Distribution with PyInstaller)

---

## 🔄 Five-Stage Pipeline Architecture

The application follows this workflow:

```
STAGE 1: EXTRACT METADATA
↓ yt-dlp extracts playlist info without downloading
↓ Stores in SQLite database

STAGE 2: DOWNLOAD AUDIO
↓ Downloads .opus files with bot avoidance
↓ Stores in downloads/raw/

STAGE 3: AI TITLE PROCESSING
↓ 3 parallel workers process titles with Ollama models
↓ Stores multiple AI attempts per song

STAGE 4: BATCH REVIEW & APPROVAL
↓ GUI shows side-by-side comparison
↓ User approves/edits/regenerates titles

STAGE 5: CONVERT & EMBED METADATA
↓ FFmpeg converts to MP3 + M4A
↓ Embeds metadata and 300x300 thumbnails
↓ Final files in downloads/final/
```

---

## 📊 Technology Stack

| Component | Technology | Status |
|-----------|-----------|--------|
| Language | Python 3.10+ | ✅ |
| GUI | CustomTkinter 5.2+ | ⏳ Phase 5 |
| Database | SQLite 3 | ✅ |
| Downloader | yt-dlp | ✅ Phase 2 |
| Converter | FFmpeg | ⏳ Phase 4 |
| AI | Ollama (Gemma3:12B, Qwen3:14B, Qwen2.5:7B) | ✅ Phase 3 |
| Metadata | Mutagen | ⏳ Phase 4 |
| Images | Pillow | ✅ Phase 2 |
| Packaging | PyInstaller | ⏳ Phase 6 |

---

## 📖 Critical Implementation Details

### Database Schema Overview

**playlists**: Stores YouTube playlist metadata
- Key: `playlist_id` (YouTube PLxxx...)
- Tracks: title, uploader, video_count, dates

**videos**: Stores individual video metadata
- Key: `video_id` (YouTube 11-char ID)
- Tracks: title, uploader, duration, download status, file paths

**playlist_videos**: Many-to-many relationship
- Links videos to playlists with position tracking
- Same video can be in multiple playlists

**ai_title_attempts**: Stores AI-generated titles
- Multiple attempts per video (one per model)
- Stores: title, artist, tags, confidence, processing time

**approved_metadata**: Final user-approved metadata
- Links to selected AI attempt or manual edit
- Tracks conversion status and output file paths

**app_config**: Key-value configuration store
- Synced with config.ini
- Stores runtime settings

### Configuration System

**Config Sources**:
1. `config.ini` - User-editable settings file
2. SQLite `app_config` table - Runtime settings
3. Both are kept in sync

**Key Settings**:
- Theme: dark/light/system
- Download: format, cookies, retries, sleep intervals
- AI: Ollama URL, models list, parallel workers
- Output: MP3/M4A bitrates, output directories
- Logging: level, file rotation

**Validation**: `ConfigManager.validate()` checks all settings before use

### Logging System

**Console Logging**:
- Color-coded levels (green INFO, yellow WARNING, red ERROR)
- Human-readable timestamps (HH:MM:SS)
- Uses colorama for cross-platform colors

**File Logging**:
- Rotating files (10MB max, 5 backups)
- Daily log files: `music_dlp_YYYYMMDD.log`
- Full timestamps and module names

**GUI Integration**:
- Custom `GUILogHandler` for real-time log display
- Callback-based: GUI registers callback to receive logs

---

## 🚀 Next Phase: Conversion System (Phase 4)

**Files to Create**:

1. **`converters/__init__.py`** - Package init

2. **`converters/ffmpeg_converter.py`** - Audio conversion
   - Convert .opus → .mp3 (320kbps with libmp3lame)
   - Convert .opus → .m4a (320kbps AAC)
   - Audio normalization support
   - Progress tracking for GUI
   - Error handling and validation

3. **`converters/metadata_embedder.py`** - Metadata embedding
   - Embed ID3 tags for MP3 (title, artist, album, tags)
   - Embed MP4 atoms for M4A
   - Embed 300x300 album artwork
   - Use mutagen library
   - Validate embedded metadata

4. **`test_phase4.py`** - Test script for conversion
   - FFmpeg availability check
   - MP3 conversion tests
   - M4A conversion tests
   - Metadata embedding tests
   - File validation tests

**Key Implementation Notes**:

### yt-dlp Bot Avoidance Strategy

```python
# Required features:
- cookiefile: Use browser cookies (export from Chrome/Firefox)
- sleep_interval: 2-5 seconds between downloads
- sleep_interval_requests: 1 second between API requests
- retries: 3 attempts with exponential backoff
- format: '251/bestaudio[ext=opus]/bestaudio'

# On 403 or bot detection:
- Log warning
- Sleep for 60 seconds
- Return error, don't retry immediately
```

**Cookie Setup** (user must do):
1. Install "Get cookies.txt LOCALLY" browser extension
2. Log into YouTube
3. Export cookies to `cookies.txt`
4. Configure path in Settings

### Format Selection Priority

1. **Format 251**: Opus ~160kbps (best quality for standard videos)
2. **bestaudio[ext=opus]**: Any opus format
3. **bestaudio[ext=webm]**: WebM container
4. **bestaudio**: Best available

**Why Opus?**: Higher quality than AAC at same bitrate, and we'll convert to MP3/M4A later anyway.

### Thumbnail Processing

YouTube thumbnails are 16:9 (1280x720 typical).
We need square 300x300:
1. Download original
2. Crop to center square
3. Resize to 300x300 with LANCZOS
4. Save as JPEG quality=95

---

## 📝 Implementation Plan Reference

**Full plan location**: `C:\Users\amiel\.claude\plans\idempotent-sauteeing-barto.md`

**6-Week Development Phases**:
- ✅ **Week 1**: Core + Download (database, config, logging, yt-dlp)
- ✅ **Week 2**: AI Processing (Ollama client, prompts, parallelization)
- ⏳ **Week 3**: Conversion (FFmpeg, metadata embedding, thumbnail)
- ⏳ **Week 4**: GUI Foundation (main window, panels, settings)
- ⏳ **Week 5**: GUI Completion (AI review dialog, workers, threading)
- ⏳ **Week 6**: Polish & Package (error handling, testing, PyInstaller)

**Current Progress**: End of Week 2 (AI Processing Complete)

---

## 🎓 Key Decisions Made (Important!)

### Decision 1: Both MP3 and M4A Output
**Reason**: Spotify doesn't properly support M4A files (no album art). User wants both:
- **MP3**: For Spotify import (320kbps, best compatibility)
- **M4A**: For archival (320kbps AAC, better quality)

### Decision 2: SQLite over JSON
**Reason**:
- Better for querying and relationships
- Data integrity with foreign keys
- Concurrent access support
- User selected this in planning

### Decision 3: CustomTkinter over PyQt6
**Reason**:
- Lightweight and modern out-of-the-box
- Built-in light/dark mode
- Easier to package as .exe
- Smaller file size
- User selected this in planning

### Decision 4: 3 Ollama Models for AI
**User's models**:
1. **Gemma3:12B** (primary, most accurate)
2. **Qwen3:14B** (alternative, good quality)
3. **Qwen2.5:7B** (fallback, faster but less accurate)

**Strategy**: Run all 3 in parallel, show user side-by-side comparison

### Decision 5: Batch Review Workflow
**Reason**: User wants to review all AI suggestions at once, not one-by-one
- Process all songs first
- Then open review dialog
- Navigate through songs
- Approve/edit/regenerate as needed

---

## 🔧 Installation & Setup (For Testing)

```bash
# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 2. Install dependencies
pip install -r requirements.txt

# 3. Verify installations
python -c "import sqlite3, customtkinter, yt_dlp, ollama, PIL, mutagen; print('All imports successful!')"

# 4. Test database initialization
python -c "from core.database import Database; db = Database(); print('Database initialized:', db.db_path)"

# 5. Test config manager
python -c "from core.config_manager import ConfigManager; cfg = ConfigManager(); print('Config loaded:', cfg.theme_mode)"

# 6. Test logger
python -c "from core.logger import setup_logger; logger = setup_logger(); logger.info('Logger working!')"
```

**External Dependencies** (must be installed separately):
- **FFmpeg**: Download from ffmpeg.org, add to PATH
- **Ollama**: Download from ollama.com, install models:
  ```bash
  ollama pull gemma3:12b
  ollama pull qwen3:14b
  ollama pull qwen2.5:7b
  ```

---

## 🎯 How to Start Next Session

### Step 1: Review This Document
Read this entire `HANDOFF.md` to understand what's been done.

### Step 2: Load Plan File
The full implementation plan is at:
```
C:\Users\amiel\.claude\plans\idempotent-sauteeing-barto.md
```

Open and review the plan, especially:
- Phase 2: Download System section
- Critical Implementation Details for yt-dlp

### Step 3: Reference Existing Code
Look at the completed core modules to understand patterns:
- `core/database.py` - See how database operations are structured
- `core/config_manager.py` - See how config properties work
- `core/logger.py` - See how logging is set up

### Step 4: Start New Chat with Context

**Option A: Continue in Same Repository**

Create a new chat and say:

```
I'm continuing work on the Music DLP project in c:\Users\amiel\OneDrive\Documents\yt-dlp\Music-dlp\2026-2\

Please read these files first:
1. HANDOFF.md - Project status and handoff notes
2. C:\Users\amiel\.claude\plans\idempotent-sauteeing-barto.md - Full implementation plan

I need to implement Phase 2: Download System. This includes:
- downloaders/yt_dlp_manager.py (yt-dlp wrapper with bot avoidance)
- downloaders/metadata_extractor.py (playlist extraction)
- downloaders/thumbnail_processor.py (thumbnail processing)

Please review the handoff document and plan, then let's start with implementing the yt_dlp_manager module.
```

**Option B: Start Fresh Chat**

1. Copy this `HANDOFF.md` to your clipboard
2. Start new chat
3. Say: "I'm working on a Music DLP project. Here's the handoff documentation from my previous session: [paste HANDOFF.md]"
4. Then: "Please implement Phase 2: Download System as described in the handoff doc."

### Step 5: Verify Core Infrastructure

Before starting Phase 2, verify the core works:
```bash
cd c:\Users\amiel\OneDrive\Documents\yt-dlp\Music-dlp\2026-2
python -c "from core.database import Database; db = Database(); print(f'Tables: {db.conn.execute(\"SELECT name FROM sqlite_master WHERE type=\\'table\\'\").fetchall()}')"
```

Should print all 6 tables: playlists, videos, playlist_videos, ai_title_attempts, approved_metadata, app_config

---

## 📚 Important Links & References

**Planning Documents**:
- Implementation Plan: `C:\Users\amiel\.claude\plans\idempotent-sauteeing-barto.md`
- Original Requirements: `Music-dlp Plan.txt` (in parent directory)

**Previous Attempts** (for reference, what NOT to do):
- `2025-11/` - Most recent attempt, had working CLI but no complete GUI
- Issues: Bot detection, complex GUI, slow processing, disorganized code

**Web Resources** (from planning research):
- [yt-dlp Bot Avoidance](https://medium.com/@DataBeacon/how-to-tackle-yt-dlp-challenges-in-ai-scale-scraping-8b78242fedf0)
- [yt-dlp Format Codes](https://github.com/yt-dlp/yt-dlp/issues/9724)
- [CustomTkinter GitHub](https://github.com/TomSchimansky/CustomTkinter)
- [FFmpeg Audio Processing](https://www.ffmpeg.media/articles/audio-processing-aac-mp3-opus-loudness)
- [Spotify Local Files](https://support.spotify.com/us/article/local-files/)

---

## ⚠️ Critical Warnings & Gotchas

### 1. yt-dlp Bot Detection
- **DO NOT** download too fast (minimum 2s sleep between downloads)
- **DO** use browser cookies (without them, you'll get 403 errors quickly)
- **DO** keep yt-dlp updated (YouTube changes frequently)
- **DO** handle 403 errors gracefully (sleep 60s, then return error)

### 2. Spotify M4A Compatibility
- **IMPORTANT**: Spotify does NOT show album art on M4A files!
- MP3 is the primary format for Spotify
- M4A is for archival/backup only
- Always create both formats as user requested

### 3. Database Foreign Keys
- Deleting a playlist cascades to playlist_videos
- Deleting a video cascades to ai_title_attempts and approved_metadata
- Be careful with delete operations!

### 4. Threading in GUI
- All long-running operations (download, AI, conversion) MUST use separate threads
- Never block the GUI thread
- Use `gui/workers/` modules for threading

### 5. FFmpeg Dependency
- FFmpeg must be in PATH
- Check for it on app startup
- Provide clear error message if missing with download link

### 6. Ollama Availability
- Check if Ollama is running before AI processing
- Graceful degradation if models aren't available
- Clear error messages for users

---

## 🧪 Testing Strategy

**Unit Tests** (to be created later):
- Database CRUD operations
- Config validation
- AI prompt formatting
- Thumbnail resizing

**Integration Tests**:
1. Extract small playlist (3-5 videos)
2. Download 2-3 songs
3. Process with AI
4. Approve and convert
5. Verify outputs

**End-to-End Test**:
- Fresh database
- Add playlist → Extract → Download → AI Process → Review → Convert
- Import to Spotify and verify

---

## 📈 Progress Tracking

**Overall Progress**: ~84% (Phase 1, 2, 3, 4 & 5 complete, 1 phase remains)

**Phase Breakdown**:
- ✅ Phase 1: Core Infrastructure (100%)
- ✅ Phase 2: Download System (100%)
- ✅ Phase 3: AI Processing (100%)
- ✅ Phase 4: Conversion System (100%)
- ✅ Phase 5: GUI Implementation (100%)
- ⏳ Phase 6: Packaging & Distribution (0%)

**Lines of Code**: ~10,115+ lines
  - Phase 1 (Core): ~1,200 lines (database 650, config 280, logger 180, init 40)
  - Phase 2 (Download): ~1,400 lines (yt-dlp 350, metadata 380, thumbnail 300, test 400)
  - Phase 3 (AI): ~1,780 lines (client 390, prompts 400, processor 560, test 430)
  - Phase 4 (Conversion): ~1,565 lines (converter 430, embedder 450, test 660, docs 500+)
  - Phase 5 (GUI): ~4,170 lines (main 200, components 840, dialogs 1040, workers 510, test 400, docs 470, init 60)

**Time Estimate**: 1-2 days remaining (based on 6-week plan)

---

## 🎨 GUI Design Preview (For Reference)

When you get to Phase 5, the main window should look like this:

```
┌────────────────────────────────────────────────────────┐
│  Music DLP               [Light/Dark] [⚙️ Settings]    │
├────────────────────────────────────────────────────────┤
│  Playlist URL: [________________________] [Add]        │
│                                                        │
│  ┌─ Playlists ─────┬─ Songs ────────────────────────┐ │
│  │ ☑ Playlist 1    │ #  Title    Status  AI    ✓   │ │
│  │ ☐ Playlist 2    │ 1  Song 1   ⬇️ Done  🤖   ✓   │ │
│  │                 │ 2  Song 2   ⏸️ Pend  -    -   │ │
│  └─────────────────┴────────────────────────────────┘ │
│                                                        │
│  ┌─ Pipeline ──────────────────────────────────────┐  │
│  │ [Extract] [Download] [AI Process] [Review]     │  │
│  │ Progress: ████████░░░░░ 50%                     │  │
│  └──────────────────────────────────────────────────┘  │
│                                                        │
│  ┌─ Logs ──────────────────────────────────────────┐  │
│  │ [INFO] Playlist extracted: 24 videos            │  │
│  │ [SUCCESS] Downloaded: video.opus (4.2 MB)       │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
```

**But don't worry about this yet** - focus on Phase 2 (Download System) first!

---

## 🤝 Questions for Next Session Agent

If you're unsure about anything:

1. **"What settings should I use for yt-dlp?"**
   - See "Critical Implementation Details → yt-dlp Bot Avoidance Strategy" above
   - Reference the full plan: Section "1. yt-dlp Bot Detection Avoidance"

2. **"How do I store data in the database?"**
   - See `core/database.py` methods (add_video, add_playlist, etc.)
   - All methods are documented with docstrings

3. **"What's the AI prompt format?"**
   - See full plan: Section "2. AI Title Processing with Parallelization"
   - JSON format: {title, artist, tags, confidence}

4. **"Where do files go?"**
   - Raw downloads: `downloads/raw/`
   - Final outputs: `downloads/final/`
   - Configuration: `config.ini` (see [Paths] section)

5. **"How do I test my code?"**
   - See "Installation & Setup (For Testing)" above
   - Create simple test scripts that use Database and ConfigManager

---

## ✅ Checklist for Starting Next Session

Before writing code:
- [ ] Read this entire HANDOFF.md file
- [ ] Review implementation plan (idempotent-sauteeing-barto.md)
- [ ] Verify core infrastructure works (run test commands)
- [ ] Understand database schema (see core/database.py)
- [ ] Review yt-dlp bot avoidance strategy
- [ ] Check that Ollama is installed and models are pulled

When starting Phase 2:
- [ ] Create `downloaders/__init__.py`
- [ ] Implement `yt_dlp_manager.py` first (most critical)
- [ ] Then `metadata_extractor.py`
- [ ] Then `thumbnail_processor.py`
- [ ] Test each module as you build it
- [ ] Update this HANDOFF.md with progress

---

## 📞 Contact & Support

**User**: Amiel (you!)
**Project**: Music DLP (YouTube → Spotify music downloader)
**Location**: `c:\Users\amiel\OneDrive\Documents\yt-dlp\Music-dlp\2026-2\`

**Previous Attempts**:
- 2025-11, 2025-10, 2025-9, etc. (in parent directory)
- All had issues, starting fresh with better architecture

**AI Models Used**: Gemma3:12B, Qwen3:14B, Qwen2.5:7B (via Ollama)

---

## 🎉 Final Notes

You've built a solid foundation! The core infrastructure is clean, well-documented, and follows best practices:

✅ **Database**: Comprehensive schema with relationships and data integrity
✅ **Config**: Flexible INI + database sync system
✅ **Logging**: Professional colored console + rotating file logs
✅ **Structure**: Organized modules ready for next phases

**Next agent**: You're in great shape to start Phase 2. The hardest part (architecture planning) is done. Now it's just implementing the features one by one.

**Remember**: Go slow, test frequently, and follow the plan. Bot detection avoidance is critical - if you get it wrong, the whole app fails. Use cookies, sleep intervals, and graceful error handling.

Good luck! 🚀

---

**Document Version**: 1.0
**Last Updated**: 2026-02-08
**Next Review**: After Phase 2 completion
