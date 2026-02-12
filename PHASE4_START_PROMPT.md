# Phase 4 Start Prompt - Music DLP Project

**Copy and paste this entire prompt to start Phase 4 implementation:**

---

I'm continuing the Music DLP project. Please read my handoff documentation to understand where we left off.

**Project location**: `c:\Users\amiel\OneDrive\Documents\yt-dlp\Music-dlp\2026-2\`

## Current Status

✅ **Phase 1**: Core Infrastructure (database, config, logger) - COMPLETE
✅ **Phase 2**: Download System (yt-dlp, metadata, thumbnails) - COMPLETE
✅ **Phase 3**: AI Processing with Ollama - COMPLETE
⏳ **Phase 4**: Conversion System - READY TO START

**Overall Progress**: 50% complete (~4,380 lines of code)

## Required Reading

Please read these files in order:

1. **HANDOFF.md** - Current project status and architecture
2. **C:\Users\amiel\.claude\plans\idempotent-sauteeing-barto.md** - Full implementation plan
3. **PHASE3_SUMMARY.md** - Summary of Phase 3 completion

## Pre-Implementation Checks

**BEFORE starting Phase 4 implementation, please verify:**

### 1. Project Structure Check
```bash
# Verify all Phase 1-3 modules exist
ls core/database.py core/config_manager.py core/logger.py
ls downloaders/yt_dlp_manager.py downloaders/metadata_extractor.py downloaders/thumbnail_processor.py
ls ai/ollama_client.py ai/prompts.py ai/title_processor.py
ls test_phase2.py test_phase3.py
```

### 2. Database Schema Check
```python
# Verify database tables exist
python -c "from core.database import Database; db = Database(); cursor = db.conn.cursor(); cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table'\"); print([row[0] for row in cursor.fetchall()]); db.close()"
```
Expected output: `['playlists', 'videos', 'playlist_videos', 'ai_title_attempts', 'approved_metadata', 'app_config']`

### 3. FFmpeg Availability Check
```bash
# CRITICAL: FFmpeg must be installed for Phase 4
ffmpeg -version
ffprobe -version
```

If FFmpeg is not installed:
- **Windows**: Download from https://ffmpeg.org/download.html#build-windows
  - Extract to `C:\ffmpeg`
  - Add `C:\ffmpeg\bin` to PATH
  - Restart terminal
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt install ffmpeg`

### 4. Python Dependencies Check
```python
# Verify all required packages are installed
python -c "import ffmpeg, mutagen, PIL; print('✓ All Phase 4 dependencies available')"
```

If packages are missing:
```bash
pip install ffmpeg-python mutagen Pillow
```

### 5. Previous Phases Functionality Check

Run quick tests to ensure Phase 1-3 are working:

```bash
# Test Phase 2 (Download System)
python test_phase2.py --test-db

# Test Phase 3 (AI Processing) - only if Ollama is installed
python test_phase3.py --test-ollama
python test_phase3.py --stats
```

### 6. Review Implementation Plan Section

Read the implementation plan section on **Phase 3: Conversion** (lines 1018-1024):
- Understand FFmpeg conversion requirements
- Review metadata embedding strategy
- Check output format requirements (MP3 320kbps, M4A 320kbps)

## Phase 4 Implementation Task

**Once all checks pass**, implement the Conversion System:

### Files to Create:

1. **`converters/__init__.py`**
   - Package initialization
   - Export main classes

2. **`converters/ffmpeg_converter.py`** (~400 lines)
   - Convert .opus → .mp3 (320kbps with libmp3lame)
   - Convert .opus → .m4a (320kbps AAC)
   - Audio normalization (optional but recommended)
   - Progress tracking for GUI integration
   - Comprehensive error handling
   - File validation

3. **`converters/metadata_embedder.py`** (~350 lines)
   - Embed ID3 tags for MP3 (mutagen.id3)
     - Title (TIT2)
     - Artist (TPE1)
     - Album (TALB)
     - Album art (APIC) - 300x300 JPEG
   - Embed MP4 atoms for M4A (mutagen.mp4)
     - Title (\xa9nam)
     - Artist (\xa9ART)
     - Album (\xa9alb)
     - Cover art (covr) - 300x300 JPEG
   - Validate embedded metadata
   - Database integration

4. **`test_phase4.py`** (~400 lines)
   - FFmpeg availability tests
   - MP3 conversion tests
   - M4A conversion tests
   - Metadata embedding tests
   - File validation tests
   - Integration tests

### Critical Requirements:

1. **Both MP3 and M4A output**
   - MP3 for Spotify (Spotify shows album art on MP3 only)
   - M4A for archival (better quality)
   - Both at 320kbps bitrate

2. **Follow existing patterns**
   - Use Database class for data access (see Phase 1-3)
   - Use ConfigManager for settings
   - Use logger from core.logger
   - Follow error handling patterns from Phase 2-3

3. **File naming convention**
   - Input: `downloads/raw/[VIDEO_ID].opus`
   - Output: `downloads/final/Artist - Title.mp3` and `Artist - Title.m4a`
   - Sanitize filenames (remove invalid characters)

4. **Database updates**
   - Update `approved_metadata` table with output file paths
   - Set `conversion_status` to 'converting', then 'completed' or 'error'
   - Store any conversion errors

5. **Progress tracking**
   - Provide callbacks for GUI integration
   - Track conversion progress (0-100%)
   - Report current file being processed

### Implementation Order:

1. Start with `ffmpeg_converter.py` (core conversion logic)
2. Then `metadata_embedder.py` (metadata embedding)
3. Finally `test_phase4.py` (comprehensive tests)
4. Test thoroughly before marking complete

## Success Criteria

Phase 4 is complete when:

- ✅ Can convert .opus → .mp3 (320kbps)
- ✅ Can convert .opus → .m4a (320kbps AAC)
- ✅ Metadata embedded correctly in both formats
- ✅ Album art (300x300) embedded in both formats
- ✅ Files playable in media players
- ✅ Metadata visible in Spotify (MP3)
- ✅ Test suite passes all tests
- ✅ Database updated with conversion status
- ✅ Error handling works (missing files, FFmpeg errors)

## Important Notes from Project Memory

From MEMORY.md:

1. **Spotify M4A Issue**: Spotify doesn't show album art on M4A files. MP3 is the primary format for Spotify.
2. **Thumbnail Processing**: Already done in Phase 2 (300x300 center square crop)
3. **File Organization**: Use `downloads/raw/` for .opus, `downloads/final/` for MP3/M4A
4. **FFmpeg Format Selection**: Use libmp3lame for MP3, AAC for M4A, 320kbps for both

## Questions to Ask If Unclear

If anything is unclear before starting:

- Ask about FFmpeg command-line arguments
- Ask about mutagen usage for metadata embedding
- Ask about error handling strategies
- Ask about progress tracking implementation

## After Phase 4 Completion

When Phase 4 is done:

1. Update HANDOFF.md with Phase 4 completion
2. Create PHASE4_README.md with testing instructions
3. Create PHASE4_SUMMARY.md with session summary
4. Run full integration test:
   - Extract playlist
   - Download videos
   - Process with AI
   - Convert to MP3/M4A
   - Import to Spotify and verify

## Start Implementation

Once all pre-checks pass, begin implementing Phase 4 starting with the FFmpeg converter module.

Good luck! 🚀
