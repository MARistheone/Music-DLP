# Phase 2: Download System - Complete! ✅

## What Was Built

Phase 2 implements the complete YouTube download system with bot detection avoidance:

### 1. **yt-dlp Manager** (`downloaders/yt_dlp_manager.py`)
- Smart bot detection avoidance with cookies and random sleep intervals
- Progress tracking for GUI integration
- Batch download support
- Comprehensive error handling
- Download statistics

### 2. **Metadata Extractor** (`downloaders/metadata_extractor.py`)
- Extract playlist metadata without downloading
- Extract individual video metadata
- Automatic database storage
- URL validation and type detection

### 3. **Thumbnail Processor** (`downloaders/thumbnail_processor.py`)
- Download and process YouTube thumbnails
- Crop to center square (handles 16:9 aspect ratio)
- Resize to 300x300px with high quality
- Batch processing support

### 4. **Test Suite** (`test_phase2.py`)
- Comprehensive testing for all Phase 2 components
- Integration tests for real YouTube downloads
- Database verification

---

## 🚀 Quick Start

### Prerequisites

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Export browser cookies (CRITICAL for avoiding bot detection):**
   - Install "Get cookies.txt LOCALLY" extension in Chrome/Firefox
   - Log into YouTube
   - Click extension and export to `cookies.txt`
   - Save the file somewhere safe

3. **Update config.ini:**
   ```ini
   [Download]
   cookies_file = C:\path\to\your\cookies.txt
   ```

---

## 🧪 Testing Phase 2

### Test 1: Basic Components (No YouTube access needed)
```bash
python test_phase2.py --test-all
```

This tests:
- Database initialization
- Configuration loading
- All modules import correctly

### Test 2: Extract Playlist Metadata
```bash
python test_phase2.py --test-extract "https://www.youtube.com/playlist?list=PLxxxxxx"
```

This will:
- Extract playlist metadata (title, uploader, video count)
- Extract all video metadata
- Store everything in the database
- **Does NOT download** any files

### Test 3: Download a Single Video
```bash
python test_phase2.py --test-download "VIDEO_ID_HERE"
```

Example:
```bash
python test_phase2.py --test-download "dQw4w9WgXcQ"
```

This will:
- Download the audio as .opus file
- Save to `downloads/raw/[VIDEO_ID].opus`
- Update database with download status
- Show download statistics

### Test 4: Process a Thumbnail
```bash
python test_phase2.py --test-thumbnail "https://i.ytimg.com/vi/VIDEO_ID/maxresdefault.jpg"
```

This will:
- Download the thumbnail
- Crop to center square
- Resize to 300x300px
- Save as `downloads/raw/test_thumbnail.jpg`

---

## 📝 Example Workflow

Here's a complete example using a small test playlist:

```bash
# 1. Test basic components
python test_phase2.py --test-all

# 2. Extract a small playlist (replace with your playlist URL)
python test_phase2.py --test-extract "https://www.youtube.com/playlist?list=YOUR_PLAYLIST_ID"

# 3. Download one video to verify it works
python test_phase2.py --test-download "VIDEO_ID_FROM_PLAYLIST"

# 4. Check the database to see stored metadata
python -c "from core.database import Database; db = Database(); playlists = db.get_all_playlists(); print('Playlists:', [(p['playlist_id'], p['title']) for p in playlists])"
```

---

## 🔍 Verifying Success

After running tests, check these locations:

### Database
```bash
# View all playlists
python -c "from core.database import Database; db = Database(); print([p['title'] for p in db.get_all_playlists()])"

# View all videos
python -c "from core.database import Database; db = Database(); print([v['title'] for v in db.get_all_videos()])"
```

### Downloaded Files
```
downloads/raw/
  └── [VIDEO_ID].opus    # Downloaded audio file
```

### Logs
```
logs/
  └── music_dlp_YYYYMMDD.log    # Detailed logs
```

---

## ⚠️ Important Notes

### Bot Detection Avoidance

**CRITICAL**: You MUST use browser cookies to avoid YouTube bot detection!

Without cookies:
- ❌ Downloads will fail with 403 errors
- ❌ YouTube will think you're a bot
- ❌ You'll get rate limited quickly

With cookies:
- ✅ Downloads work reliably
- ✅ YouTube treats you as a normal browser
- ✅ Rate limiting is much more lenient

### Sleep Intervals

The system automatically:
- Sleeps 2-5 seconds (random) between downloads
- Sleeps 1 second between API requests
- Waits 60 seconds if bot detection is triggered

**Don't disable these delays!** They're essential for avoiding bans.

### Format Selection

Downloads prefer this order:
1. Format 251 (opus 160kbps) - Best for most videos
2. Any opus format
3. Any webm format
4. Best available audio

The downloaded .opus files will be converted to MP3/M4A in Phase 4.

---

## 🐛 Troubleshooting

### "No cookies file found" warning
→ Export cookies from browser and update `config.ini`

### "403 Forbidden" or "Sign in to confirm you're not a bot"
→ Your cookies are expired or invalid. Re-export from browser

### "Download failed" repeatedly
→ Check if yt-dlp is up to date: `pip install --upgrade yt-dlp`

### Extraction is very slow
→ Normal for large playlists. Each video takes ~1 second due to API rate limiting

### Can't find video in database after extraction
→ Check logs folder for errors. Run with `--test-extract` to see detailed output

---

## 📊 What's Next: Phase 3

Once Phase 2 testing is complete, Phase 3 will add:

1. **Ollama Client** - Connect to local AI models
2. **AI Title Processor** - Clean messy YouTube titles with 3 models in parallel
3. **Prompt Engineering** - Specialized prompts for Japanese music metadata

**Requirements for Phase 3**:
- Ollama installed and running
- Models downloaded: `gemma3:12b`, `qwen3:14b`, `qwen2.5:7b`

---

## 💡 Tips

1. **Start small**: Test with a playlist of 3-5 videos first
2. **Check logs**: Detailed logs are in `logs/` folder
3. **Use cookies**: Absolutely essential for reliable downloads
4. **Be patient**: Sleep intervals are intentional, don't rush

---

## ✅ Phase 2 Checklist

Before moving to Phase 3, verify:

- [ ] Basic tests pass (`--test-all`)
- [ ] Can extract playlist metadata
- [ ] Can download at least one video successfully
- [ ] Thumbnail processing works
- [ ] Database is being populated correctly
- [ ] Cookies are configured and valid
- [ ] No 403 errors during downloads

---

**Phase 2 Status**: ✅ **COMPLETE** (~1,400 lines of code)

Ready to proceed to Phase 3: AI Processing! 🚀
