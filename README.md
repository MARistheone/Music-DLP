# Music DLP

A Windows desktop app that downloads songs from YouTube playlists, cleans up their metadata with AI, and exports them as Spotify-compatible MP3 files with album art.

Built for people with YouTube playlists full of Japanese covers, VTuber songs, and other music that isn't on Spotify.

## Features

- **YouTube playlist downloading** via yt-dlp with bot detection avoidance
- **AI-powered metadata cleaning** - fixes messy YouTube titles into proper `Artist - Title` format using local Ollama models
- **Batch review workflow** - review AI suggestions side-by-side, edit manually, or regenerate
- **Dual output** - MP3 (320kbps, for Spotify) + M4A (320kbps AAC, for archival)
- **Album art** - embeds 300x300 thumbnails into every file
- **Modern GUI** - CustomTkinter with light/dark mode

## Quick Start (Pre-built exe)

1. Download the latest release from [Releases](../../releases)
2. Extract the zip
3. Read `INSTALL.txt` inside for setup (FFmpeg, Ollama, cookies)
4. Run `MusicDLP.exe`

## Quick Start (From source)

```bash
# Clone
git clone https://github.com/MARistheone/Music-DLP.git
cd Music-DLP

# Install Python dependencies
pip install -r requirements.txt

# Run
python main.py
```

You'll also need:
- **FFmpeg** installed and in PATH ([download](https://ffmpeg.org/download.html))
- **Ollama** running locally with at least one model ([download](https://ollama.com/download)):
  ```
  ollama pull gemma3:12b
  ```
- **YouTube cookies** exported from your browser (see `INSTALL.txt`)

## How It Works

```
1. Add Playlist    - Paste a YouTube playlist URL
2. Extract         - Pulls video metadata (no downloading yet)
3. Download        - Downloads audio as .opus with bot avoidance
4. AI Process      - Ollama models clean up titles/artists
5. Review          - You approve, edit, or regenerate AI suggestions
6. Convert         - FFmpeg converts to MP3 + M4A with embedded metadata
```

Output goes to `downloads/final/mp3/` and `downloads/final/m4a/`.

## Importing to Spotify

1. Open Spotify desktop app > Settings > Local Files
2. Enable "Show Local Files"
3. Add the `downloads/final/mp3/` folder as a source
4. Your songs appear under Local Files with album art

**Note:** Use MP3 files for Spotify. Spotify doesn't display album art on M4A local files.

## Building the exe

```bash
pip install pyinstaller
python build_exe.py --clean
```

Output: `dist/MusicDLP/`

## Tech Stack

| Component | Technology |
|-----------|-----------|
| GUI | CustomTkinter |
| Database | SQLite |
| Downloader | yt-dlp |
| Audio conversion | FFmpeg |
| AI models | Ollama (gemma3:12b recommended) |
| Metadata | mutagen |
| Thumbnails | Pillow |
| Packaging | PyInstaller |

## License

For personal use.
