# External AI Export/Import Feature - Implementation Handoff

**Date**: 2026-02-10
**Status**: Planned, not yet implemented
**Plan File**: `C:\Users\amiel\.claude\plans\happy-dancing-book.md`

---

## What This Feature Does

Adds the ability to use **any external AI** (ChatGPT, Claude, Gemini, etc.) for Stage 3 (AI title processing) instead of requiring local Ollama. This is for users on devices that can't run local AI models.

**Workflow:**
1. User clicks **Tools > Export for External AI** in the header bar
2. App generates two files per batch:
   - `.json` — structured data with blank response slots
   - `.txt` — a ready-to-paste prompt for any AI chatbot
3. User pastes the `.txt` into their AI of choice, gets JSON back
4. User clicks **Tools > Import AI Results**, selects the response `.json`
5. Results appear in the Review dialog as normal AI attempts (model_name: "external")
6. User proceeds with Review > Convert as usual

---

## Why This Matters

Currently Stage 3 requires Ollama running locally with 12B+ parameter models. This blocks:
- Low-spec laptops/desktops without GPU
- Users who don't want to install Ollama
- Quick processing via cloud AI services

---

## Architecture Decision: Why It Works

The existing `db.add_ai_attempt()` method already accepts any `model_name` string. External results are stored with `model_name="external"` and `prompt_version="3.0-external"`. The Review dialog (`ai_review_dialog.py`) displays all attempts for a video regardless of model — so external results appear automatically alongside local Ollama results.

**No database schema changes needed. No changes to pipeline_panel.py or database.py.**

---

## Files to Create/Modify

### NEW: `ai/external_processor.py`

**~200 lines. Two main functions:**

#### `export_for_external_ai(db, output_dir, video_ids, batch_size=20)`

```python
# Pseudocode
def export_for_external_ai(db, output_dir, video_ids, batch_size=20):
    # 1. Get video metadata from DB for each video_id
    #    - db.get_video(video_id) → {video_id, title, uploader, ...}

    # 2. Filter: only videos with download_status='downloaded'
    #    and no existing AI attempts (db.get_ai_attempts(vid) == [])

    # 3. Split video list into batches of batch_size

    # 4. For each batch, generate two files:
    #    a) JSON export file with blank response slots
    #    b) TXT prompt file with SYSTEM_PROMPT_V3 + video list

    # 5. Return list of generated file paths
```

**JSON export format:**
```json
{
    "music_dlp_export": {
        "version": "1.0",
        "export_date": "2026-02-10T14:30:00",
        "batch": 1,
        "total_batches": 2,
        "total_videos": 10,
        "videos": [
            {
                "video_id": "dQw4w9WgXcQ",
                "raw_title": "【歌ってみた】夜に駆ける / YOASOBI【Cover】",
                "uploader": "VTuber Channel",
                "response": null
            }
        ]
    }
}
```

**TXT prompt format:**
```
[Full SYSTEM_PROMPT_V3 from ai/prompts_v3.py]

---

Process the following YouTube videos and return ONLY a JSON array.
For each video, provide: {"video_id": "...", "title": "...", "artist": "...", "tags": [...], "confidence": 0.0-1.0}

Video 1 (ID: dQw4w9WgXcQ):
  Title: "【歌ってみた】夜に駆ける / YOASOBI【Cover】"
  Uploader: "VTuber Channel"

Video 2 (ID: abc12345678):
  Title: "..."
  Uploader: "..."

Respond with ONLY a valid JSON array, no other text.
```

#### `import_external_ai_results(db, file_path)`

```python
# Pseudocode
def import_external_ai_results(db, file_path):
    # 1. Read JSON file

    # 2. Auto-detect format:
    #    Format A: {"music_dlp_export": {"videos": [{"video_id":..., "response":{...}}]}}
    #    Format B: [{"video_id":..., "title":..., "artist":..., ...}]

    # 3. Extract responses from either format

    # 4. For each response:
    #    a) Check video_id exists in DB → skip with warning if not
    #    b) validate_response_v3(response) → skip with warning if invalid
    #    c) normalize_response_v3(response)
    #    d) db.add_ai_attempt(
    #         video_id=response['video_id'],
    #         model_name="external",
    #         generated_title=response['title'],
    #         artist=response['artist'],
    #         tags=response['tags'],
    #         confidence=response['confidence'],
    #         prompt_version="3.0-external",
    #         processing_time=0.0
    #       )

    # 5. Return {"imported": N, "skipped": N, "errors": ["vid: reason", ...]}
```

**Imports needed from existing code:**
```python
from ai.prompts_v3 import SYSTEM_PROMPT_V3, validate_response_v3, normalize_response_v3
from core.database import Database
```

### MODIFY: `gui/main_window.py`

**Changes to `_create_menu()` method (around line 71-106):**

Add a "Tools" button to `right_frame` (next to theme toggle and settings button). The Tools button opens a tkinter context menu on click with two options:
- "Export for External AI..."
- "Import AI Results..."

**Pattern to follow** (same as song_panel.py context menu):
```python
# In _create_menu(), add after settings_button:
tools_button = ctk.CTkButton(
    right_frame,
    text="Tools",
    width=100,
    command=self._show_tools_menu
)
tools_button.grid(row=0, column=2, padx=5)

# New method:
def _show_tools_menu(self):
    menu = tk.Menu(self, tearoff=0)
    menu.add_command(label="Export for External AI...", command=self._on_export_ai)
    menu.add_command(label="Import AI Results...", command=self._on_import_ai)
    # Show at button position
    button = self.tools_button
    x = button.winfo_rootx()
    y = button.winfo_rooty() + button.winfo_height()
    menu.tk_popup(x, y)
```

**New method `_on_export_ai()`:**
1. Find downloaded videos needing AI processing:
   - Get all videos with `download_status='downloaded'`
   - Filter out those that already have AI attempts
2. If none found, show info messagebox and return
3. Show `CTkInputDialog` asking for batch size (default: "20")
4. Show `filedialog.askdirectory()` for save location
5. Call `export_for_external_ai(db, output_dir, video_ids, batch_size)`
6. Show success messagebox listing generated file paths
7. Log the export

**New method `_on_import_ai()`:**
1. Show `filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])`
2. If no file selected, return
3. Call `import_external_ai_results(db, file_path)`
4. Show summary messagebox: "Imported N results, skipped M (see log for details)"
5. If errors, log each one
6. Refresh song panel to update status indicators

---

## Key Code References

These existing functions/methods are reused directly (no changes needed):

| Function | File | Line | Purpose |
|----------|------|------|---------|
| `SYSTEM_PROMPT_V3` | `ai/prompts_v3.py` | 22 | The full V3 system prompt for export |
| `validate_response_v3()` | `ai/prompts_v3.py` | 437 (re-exported from prompts_v2) | Validates AI response has required fields |
| `normalize_response_v3()` | `ai/prompts_v3.py` | 438 (re-exported from prompts_v2) | Normalizes tags, confidence, artist |
| `db.add_ai_attempt()` | `core/database.py` | 651 | Stores attempt — accepts any model_name |
| `db.get_video()` | `core/database.py` | 402 | Gets video metadata by ID |
| `db.get_ai_attempts()` | `core/database.py` | 684 | Gets all AI attempts for a video |
| `db.get_videos_by_status()` | `core/database.py` | 465 | Gets videos by download_status |

### validate_response / normalize_response

These are re-exported from `ai/prompts_v2.py` in `ai/prompts_v3.py` (line 435-438):
```python
from .prompts_v2 import (
    validate_response_v2 as validate_response_v3,
    normalize_response_v2 as normalize_response_v3
)
```

**validate_response** checks: title exists (string), artist exists (string), tags is a list, confidence is a float 0-1. Returns bool.

**normalize_response** strips whitespace from title/artist, clamps confidence to 0.0-1.0, defaults artist to "Unknown Artist" if empty, filters tags to valid set.

### add_ai_attempt signature

```python
def add_ai_attempt(self, video_id: str, model_name: str,
                   generated_title: str, artist: Optional[str] = None,
                   tags: Optional[List[str]] = None, confidence: Optional[float] = None,
                   prompt_version: str = "v1.0", processing_time: Optional[float] = None
                   ) -> Optional[int]:
```

- `tags` accepts a Python list — it converts to JSON string internally
- Returns `attempt_id` (int) or None on error

---

## Batching Design

User chooses batch size at export time (default 20). Rationale:
- ChatGPT/Claude have context limits (~4K-128K tokens depending on model)
- 20 videos per prompt is a safe default for most AI chatbots
- Each batch produces its own independent file pair

File naming with batches:
- Single batch: `music_dlp_export_20260210_143000.json` + `.txt`
- Multiple batches: `music_dlp_export_20260210_143000_batch1.json` + `_batch1.txt`, etc.

---

## Import Format Auto-Detection

The import function should handle two formats because:

**Format A** (filled-in export JSON): For users who edit the `.json` file directly or use an AI that can process files. Has the `music_dlp_export` wrapper.

**Format B** (standalone JSON array): For users who paste the prompt into ChatGPT/Claude and copy the response. Most AI chatbots will return just the JSON array without the wrapper.

Detection logic:
```python
data = json.load(f)
if isinstance(data, list):
    # Format B: standalone array
    responses = data
elif isinstance(data, dict) and "music_dlp_export" in data:
    # Format A: filled-in export
    responses = [v["response"] for v in data["music_dlp_export"]["videos"] if v.get("response")]
    # Also carry forward video_id from the wrapper
```

For Format B, each item must contain `video_id` so the import knows which video to associate it with.

---

## GUI Layout Reference

Current header bar structure (`main_window.py:71-106`):
```
┌─────────────────────────────────────────────────────────┐
│ Music DLP          [Light/Dark] [Settings] [Tools NEW]  │
└─────────────────────────────────────────────────────────┘
```

The Tools button opens a dropdown menu (tk.Menu with tk_popup):
```
┌──────────────────────────┐
│ Export for External AI... │
│ Import AI Results...     │
└──────────────────────────┘
```

---

## Testing Checklist

- [ ] Export generates correct `.json` with video metadata and null responses
- [ ] Export generates correct `.txt` with full system prompt and video list
- [ ] Batch size splits correctly (25 videos / batch 10 = 3 batches of 10+10+5)
- [ ] Prompt text produces valid results when pasted into ChatGPT or Claude
- [ ] Import Format A (filled-in export JSON) works
- [ ] Import Format B (standalone JSON array) works
- [ ] Import stores results with model_name="external", prompt_version="3.0-external"
- [ ] Imported results appear in AI Review Dialog
- [ ] Invalid responses are skipped gracefully with warnings
- [ ] Unknown video_ids are skipped with warnings
- [ ] Summary messagebox shows correct counts
- [ ] Full pipeline works: Extract > Download > Export > (external AI) > Import > Review > Convert
- [ ] No changes needed to database.py or pipeline_panel.py

---

## How to Start Implementation

```
Read these files in order:
1. EXTERNAL_AI_HANDOFF.md (this file)
2. C:\Users\amiel\.claude\plans\happy-dancing-book.md (implementation plan)

Then implement in this order:
1. Create ai/external_processor.py (export + import functions)
2. Modify gui/main_window.py (Tools button + handler methods)
3. Test end-to-end
```
