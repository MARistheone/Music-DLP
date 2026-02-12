# Music DLP - YouTube Playlist Downloader with AI Metadata Cleaning

Modern GUI application for downloading YouTube playlist songs, cleaning their metadata with AI, and converting to Spotify-compatible formats.

## Features

- ✅ Download from YouTube playlists using yt-dlp (with bot detection avoidance)
- ✅ AI-powered title cleaning using 3 Ollama models (Gemma3:12B, Qwen3:14B, Qwen2.5:7B)
- ✅ Batch review workflow for approving AI-generated titles
- ✅ Convert to both MP3 (Spotify) and M4A (archival) formats
- ✅ Embed 300x300px thumbnails and metadata
- ✅ Modern CustomTkinter GUI with light/dark mode
- ✅ Comprehensive logging for debugging
- ✅ Package as standalone .exe (planned)

## Project Status

**Current Phase**: Phase 1 Complete (Core Infrastructure)
**Next Phase**: Phase 2 (Download System)

### Completed ✅
- SQLite database with comprehensive schema
- Configuration management (INI + database sync)
- Logging system (colored console + file rotation)
- Directory structure
- Requirements and dependencies

### In Progress ⏳
- yt-dlp integration with bot avoidance
- Playlist metadata extraction
- Thumbnail processing

### Planned 📅
- AI title processing with Ollama
- FFmpeg audio conversion
- CustomTkinter GUI
- PyInstaller packaging

## Installation

### Prerequisites
- Python 3.10+
- FFmpeg (must be in PATH)
- Ollama (with models: gemma3:12b, qwen3:14b, qwen2.5:7b)

### Setup

```bash
# 1. Clone/navigate to project
cd c:\Users\amiel\OneDrive\Documents\yt-dlp\Music-dlp\2026-2

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install FFmpeg
# Download from: https://ffmpeg.org/download.html
# Add to PATH

# 5. Install Ollama and models
# Download from: https://ollama.com
ollama pull gemma3:12b
ollama pull qwen3:14b
ollama pull qwen2.5:7b

# 6. Verify installation
python -c "from core.database import Database; db = Database(); print('Database initialized!')"
```

## Configuration

Edit `config.ini` to customize settings:

```ini
[Appearance]
theme_mode = dark  # or light, system

[Download]
format = 251/bestaudio[ext=opus]/bestaudio
cookies_file =  # Path to cookies.txt (required for downloads)

[AI]
models = gemma3:12b,qwen3:14b,qwen2.5:7b
parallel_workers = 3

[Output]
mp3_enabled = true
m4a_enabled = true
mp3_bitrate = 320
m4a_bitrate = 320
```

### Cookie Setup (Important!)

To avoid YouTube bot detection:

1. Install "Get cookies.txt LOCALLY" browser extension
2. Log into YouTube
3. Export cookies to `cookies.txt`
4. Set path in `config.ini` under `[Download]` → `cookies_file`

## Usage

**Note**: GUI not yet implemented. Current usage is via Python modules.

```python
from core.database import Database
from core.config_manager import ConfigManager
from core.logger import setup_logger

# Initialize
logger = setup_logger('music_dlp')
db = Database()
config = ConfigManager(db=db)

# Add playlist (example)
db.add_playlist(
    playlist_id='PLxxxxxx',
    title='My Playlist',
    url='https://youtube.com/playlist?list=PLxxxxxx'
)

# Get playlists
playlists = db.get_playlists()
for playlist in playlists:
    print(f"{playlist['title']} - {playlist['video_count']} videos")
```

## Architecture

### Five-Stage Pipeline

```
1. EXTRACT → Extract metadata without downloading
2. DOWNLOAD → Download .opus files with bot avoidance
3. AI PROCESS → Generate clean titles with 3 models in parallel
4. REVIEW → User approves/edits titles in GUI
5. CONVERT → Convert to MP3/M4A with metadata and thumbnails
```

### Technology Stack

- **Language**: Python 3.10+
- **GUI**: CustomTkinter
- **Database**: SQLite 3
- **Downloader**: yt-dlp
- **Converter**: FFmpeg
- **AI**: Ollama (Gemma3:12B, Qwen3:14B, Qwen2.5:7B)
- **Metadata**: Mutagen
- **Images**: Pillow
- **Packaging**: PyInstaller

## Project Structure

```
music-dlp/
├── core/                    # Core infrastructure
│   ├── database.py         # SQLite manager
│   ├── config_manager.py   # Configuration
│   └── logger.py           # Logging
├── downloaders/             # yt-dlp integration (Phase 2)
├── ai/                      # AI processing (Phase 3)
├── converters/              # FFmpeg conversion (Phase 4)
├── gui/                     # CustomTkinter GUI (Phase 5)
├── utils/                   # Utilities (Phase 6)
├── downloads/
│   ├── raw/                # Downloaded .opus files
│   └── final/              # Converted MP3/M4A
├── logs/                    # Application logs
├── config.ini              # Configuration file
├── requirements.txt        # Python dependencies
├── HANDOFF.md             # Development handoff notes
└── README.md              # This file
```

## Development

### Current Session Status

See `HANDOFF.md` for detailed development handoff notes.

**Last Updated**: 2026-02-08
**Phase**: 1 of 6 complete
**Lines of Code**: ~1200

### Next Steps

1. Implement `downloaders/yt_dlp_manager.py`
2. Implement `downloaders/metadata_extractor.py`
3. Implement `downloaders/thumbnail_processor.py`

### Testing

```bash
# Test database
python -c "from core.database import Database; db = Database(); print('OK')"

# Test config
python -c "from core.config_manager import ConfigManager; cfg = ConfigManager(); print(cfg.theme_mode)"

# Test logger
python -c "from core.logger import setup_logger; logger = setup_logger(); logger.info('Test')"
```

## References

- **Implementation Plan**: `C:\Users\amiel\.claude\plans\idempotent-sauteeing-barto.md`
- **Previous Attempts**: `../2025-11/`, `../2025-10/` (for reference)
- **Original Requirements**: `../Music-dlp Plan.txt`

## License

Personal project for managing music downloads and metadata.

## Credits

- yt-dlp for YouTube downloading
- Ollama for local AI models
- FFmpeg for audio conversion
- CustomTkinter for modern GUI framework
