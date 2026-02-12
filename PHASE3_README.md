# Phase 3: AI Processing System - README

**Status**: ✅ **COMPLETE**
**Date**: 2026-02-08

---

## Overview

Phase 3 implements AI-powered title cleaning using Ollama with parallel processing across multiple models.

### What's Included

1. **`ai/ollama_client.py`** (~390 lines)
   - Ollama API client
   - Model availability checking
   - Chat request management
   - JSON response parsing
   - Error handling and retries

2. **`ai/prompts.py`** (~400 lines)
   - System prompts for title cleaning
   - Japanese music expertise
   - Response validation
   - Normalization functions
   - Example-driven prompts

3. **`ai/title_processor.py`** (~560 lines)
   - Parallel processing orchestrator
   - ThreadPoolExecutor for concurrency
   - Database integration
   - Progress tracking
   - Batch processing support

4. **`test_phase3.py`** (~430 lines)
   - Comprehensive test suite
   - Connection testing
   - Model availability checks
   - Title generation tests
   - Batch processing tests

**Total**: ~1,780 lines of robust AI processing code

---

## Prerequisites

### 1. Ollama Installation

**Download and install Ollama:**
- Visit [ollama.com](https://ollama.com)
- Download for your OS (Windows, macOS, Linux)
- Install and start the service

**Verify installation:**
```bash
ollama --version
```

### 2. Pull Required Models

The project uses 3 models by default:

```bash
# Primary model (most accurate)
ollama pull gemma3:12b

# Alternative model (good balance)
ollama pull qwen3:14b

# Fallback model (faster, less accurate)
ollama pull qwen2.5:7b
```

**Note**: Each model is 5-10GB. Make sure you have enough disk space (~30GB total).

### 3. Verify Ollama is Running

Check if Ollama is accessible:
```bash
curl http://localhost:11434/api/tags
```

Should return JSON with installed models.

---

## Quick Start

### Test Ollama Connection

```bash
python test_phase3.py --test-ollama
```

Expected output:
```
✓ Ollama is running and accessible
```

### Test Model Availability

```bash
python test_phase3.py --test-models
```

Expected output:
```
Found 3 installed models
✓ gemma3:12b
✓ qwen3:14b
✓ qwen2.5:7b
```

### Test Title Generation

```bash
python test_phase3.py --test-generation
```

This runs test cases to verify the AI can clean titles correctly.

### Process a Single Video

```bash
python test_phase3.py --test-single VIDEO_ID
```

Replace `VIDEO_ID` with an actual video ID from your database (one you've downloaded in Phase 2).

### Process a Batch of Videos

```bash
python test_phase3.py --test-batch 3
```

This processes 3 pending videos (ones that are downloaded but not yet processed by AI).

### View Statistics

```bash
python test_phase3.py --stats
```

Shows:
- Total videos in database
- How many have been processed
- AI attempts per model
- Recent AI attempts

---

## How It Works

### 1. Ollama Client

The `OllamaClient` class handles communication with the local Ollama instance:

```python
from ai.ollama_client import OllamaClient

client = OllamaClient(base_url="http://localhost:11434")

# Check availability
if client.is_available():
    print("Ollama is running")

# List models
models = client.list_models()

# Generate title
result = client.generate_title(
    model="gemma3:12b",
    system_prompt=SYSTEM_PROMPT,
    user_prompt="【カバー】夜に駆ける / YOASOBI"
)
# Returns: {'title': 'Yoru ni Kakeru', 'artist': 'YOASOBI', 'tags': ['cover'], 'confidence': 0.95}
```

### 2. Prompts

The `prompts.py` module contains carefully crafted prompts for Japanese music:

**System Prompt Features:**
- Hepburn romanization for Japanese
- Original artist extraction for covers
- Standardized tags (cover, vocaloid, otomad, etc.)
- Confidence scoring
- JSON output format

**Example transformations:**
- `【カバー】夜に駆ける / YOASOBI を歌ってみた【Channel】` → `Yoru ni Kakeru by YOASOBI`
- `Racing Into The Night (YOASOBI Cover)` → `Racing Into The Night by YOASOBI`
- `【初音ミク】千本桜【オリジナル】` → `Senbonzakura by Hatsune Miku`

### 3. Title Processor

The `TitleProcessor` orchestrates parallel processing:

```python
from ai.title_processor import TitleProcessor
from core.database import Database

db = Database()
processor = TitleProcessor(
    db=db,
    models=['gemma3:12b', 'qwen3:14b', 'qwen2.5:7b'],
    max_workers=3
)

# Process pending videos
def progress(current, total, video_id):
    print(f"Processing {current}/{total}: {video_id}")

results = processor.process_pending_videos(progress_callback=progress)
```

**Parallel Processing:**
- Uses `ThreadPoolExecutor` with 3 workers
- Each video is processed by all 3 models
- Results are stored in the database
- User can choose the best result in GUI (Phase 5)

---

## Configuration

Edit `config.ini` to customize AI processing:

```ini
[AI]
ollama_url = http://localhost:11434
ai_models = gemma3:12b,qwen3:14b,qwen2.5:7b
ai_parallel_workers = 3
ai_temperature = 0.7
```

**Settings explained:**
- `ollama_url`: Ollama API endpoint
- `ai_models`: Comma-separated list of models to use
- `ai_parallel_workers`: Number of concurrent workers (3 recommended)
- `ai_temperature`: Model creativity (0.0-1.0, higher = more creative)

---

## Database Integration

AI attempts are stored in the `ai_title_attempts` table:

```sql
CREATE TABLE ai_title_attempts (
    attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT NOT NULL,
    model_name TEXT NOT NULL,
    generated_title TEXT NOT NULL,
    artist TEXT,
    tags TEXT,  -- JSON array as string
    confidence REAL,
    prompt_version TEXT,
    generation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_time REAL,
    FOREIGN KEY (video_id) REFERENCES videos(video_id)
);
```

**Query AI attempts:**
```python
attempts = db.get_ai_attempts(video_id='dQw4w9WgXcQ')
for attempt in attempts:
    print(f"{attempt['model_name']}: {attempt['generated_title']} ({attempt['confidence']:.1%})")
```

---

## Testing Workflow

### Complete Test Flow

1. **Test Ollama is running:**
   ```bash
   python test_phase3.py --test-ollama
   ```

2. **Test models are available:**
   ```bash
   python test_phase3.py --test-models
   ```

3. **Test title generation:**
   ```bash
   python test_phase3.py --test-generation
   ```

4. **Process real videos:**
   ```bash
   # First, download some videos with Phase 2
   python test_phase2.py --test-download VIDEO_ID

   # Then process them with AI
   python test_phase3.py --test-batch 3
   ```

5. **Check results:**
   ```bash
   python test_phase3.py --stats
   ```

---

## Troubleshooting

### Ollama Not Available

**Error:** `✗ Ollama is not available`

**Solutions:**
1. Check if Ollama is installed: `ollama --version`
2. Start Ollama service (it should auto-start)
3. Check if port 11434 is open: `curl http://localhost:11434/api/tags`
4. On Windows, check if Ollama app is running in system tray

### Models Not Found

**Error:** `✗ gemma3:12b` (model not available)

**Solutions:**
1. Pull the model: `ollama pull gemma3:12b`
2. Wait for download to complete (5-10GB per model)
3. Verify with: `ollama list`

### Generation Timeout

**Error:** `Chat request timed out after 60s`

**Solutions:**
1. First generation is slow (model loading), try again
2. Increase timeout in `OllamaClient(timeout=120)`
3. Use a smaller model (qwen2.5:7b is faster)
4. Check system resources (Ollama needs RAM/GPU)

### Invalid JSON Response

**Error:** `Failed to parse model response as JSON`

**Solutions:**
1. Model may need better prompting (already optimized in prompts.py)
2. Try a different model (gemma3:12b is most reliable)
3. Check Ollama logs for errors
4. Response validation will catch this and skip the attempt

### No Pending Videos

**Error:** `No pending videos found`

**Solutions:**
1. Download videos first with Phase 2: `python test_phase2.py --test-download VIDEO_ID`
2. Check database: `python test_phase2.py --test-db`
3. Make sure videos have `download_status='downloaded'`

---

## Performance Notes

### Processing Speed

- **gemma3:12b**: ~8-15 seconds per video (most accurate)
- **qwen3:14b**: ~6-12 seconds per video (good balance)
- **qwen2.5:7b**: ~3-8 seconds per video (fastest)

Times depend on your hardware (CPU/GPU) and whether models are cached.

### Parallel Processing

With 3 models and 3 workers:
- Each video gets 3 AI attempts (one per model)
- Videos are processed concurrently
- Example: 10 videos = ~30 attempts total
- Expected time: ~2-5 minutes for 10 videos

### Resource Usage

- **RAM**: ~4-8GB per model (12-24GB total for 3 models)
- **Disk**: ~30GB for all 3 models
- **CPU/GPU**: High usage during processing

---

## What's Next: Phase 4

Phase 4 will implement the conversion system:

1. **`converters/ffmpeg_converter.py`**
   - Convert .opus → .mp3 (320kbps)
   - Convert .opus → .m4a (320kbps AAC)
   - Audio normalization

2. **`converters/metadata_embedder.py`**
   - Embed ID3 tags (MP3)
   - Embed MP4 atoms (M4A)
   - Embed 300x300 album art
   - Validate output files

Before starting Phase 4:
- ✅ Ollama installed and working
- ✅ Models downloaded and tested
- ✅ Videos downloaded with Phase 2
- ✅ AI processing working with Phase 3
- ⏳ Install FFmpeg (needed for Phase 4)

---

## Example Output

### Successful Processing

```
=== Testing Batch Processing (limit=3) ===
Processing 3 videos: ['dQw4w9WgXcQ', 'jNQXAC9IVRw', 'L_jWHffIx5E']

Progress: [1/3] Processing dQw4w9WgXcQ...
Progress: [2/3] Processing jNQXAC9IVRw...
Progress: [3/3] Processing L_jWHffIx5E...

=== Batch Processing Results ===
✓ dQw4w9WgXcQ: 3/3 models succeeded
✓ jNQXAC9IVRw: 3/3 models succeeded
✓ L_jWHffIx5E: 3/3 models succeeded

Overall: 9/9 attempts successful
```

### AI Attempts Display

```
✓ gemma3:12b:
  Title: Yoru ni Kakeru
  Artist: YOASOBI
  Tags: ["cover"]
  Confidence: 95.0%
  Time: 8.34s

✓ qwen3:14b:
  Title: Racing Into The Night
  Artist: YOASOBI
  Tags: ["cover"]
  Confidence: 88.0%
  Time: 6.12s

✓ qwen2.5:7b:
  Title: Yoru ni Kakeru
  Artist: YOASOBI
  Tags: ["cover"]
  Confidence: 72.0%
  Time: 4.56s
```

---

## Tips for Best Results

1. **Use all 3 models**: Different models have different strengths
2. **Higher confidence = better accuracy**: Trust >90% confidence scores
3. **gemma3:12b is most reliable**: Prefer its results when multiple differ
4. **Review manually**: AI isn't perfect, Phase 5 GUI will allow review
5. **Regenerate if needed**: `processor.regenerate_for_video(video_id)`

---

## API Reference

### OllamaClient

```python
client = OllamaClient(base_url="http://localhost:11434", timeout=60)

# Check if Ollama is running
client.is_available() -> bool

# List all installed models
client.list_models() -> List[str]

# Check specific model
client.model_exists("gemma3:12b") -> bool

# Generate title
client.generate_title(
    model="gemma3:12b",
    system_prompt=str,
    user_prompt=str,
    temperature=0.7
) -> Optional[Dict[str, Any]]
```

### TitleProcessor

```python
processor = TitleProcessor(
    db=Database(),
    ollama_url="http://localhost:11434",
    models=['gemma3:12b', 'qwen3:14b', 'qwen2.5:7b'],
    max_workers=3
)

# Check availability
processor.check_availability() -> Dict[str, bool]

# Process single video
processor.process_single_video(
    video_id=str,
    raw_title=str,
    uploader=str,
    description=str
) -> List[ProcessingResult]

# Process batch
processor.process_batch(
    video_ids=List[str],
    progress_callback=Callable[[int, int, str], None]
) -> Dict[str, List[ProcessingResult]]

# Process pending videos
processor.process_pending_videos(
    playlist_id=Optional[str],
    limit=Optional[int],
    progress_callback=Optional[Callable]
) -> Dict[str, List[ProcessingResult]]

# Get statistics
processor.get_processing_stats() -> Dict[str, Any]
```

---

## Summary

Phase 3 is complete with:
- ✅ Ollama client with robust error handling
- ✅ Carefully crafted prompts for Japanese music
- ✅ Parallel processing with 3 models
- ✅ Database integration for storing attempts
- ✅ Comprehensive test suite
- ✅ Progress tracking for GUI integration

**Lines of Code**: ~1,780 lines
**Test Coverage**: Connection, models, generation, batch processing
**Ready for**: Phase 4 (Conversion System)

---

**Next Steps**: Install FFmpeg and proceed to Phase 4!
