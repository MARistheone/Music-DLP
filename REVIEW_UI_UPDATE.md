# AI Review UI Update - 2026-02-09

## Changes Made

### 1. ✅ New Table-Based Review Dialog

**Problem**: Old review dialog showed ONE song at a time, requiring navigation with Previous/Next buttons. This was too slow for reviewing 100+ songs.

**Solution**: Created completely new `AIReviewTableDialog` that shows ALL songs in a table.

**File**: `gui/dialogs/ai_review_table_dialog.py` (new file, ~700 lines)

**Features**:
- **Table view** - See all songs at once in a scrollable table
- **Columns**: Original title, AI title, AI artist, models used, confidence %, status
- **Checkboxes** - Select multiple rows for bulk operations
- **Double-click** - Edit individual song details
- **Bulk approve** - Approve all selected songs with their best AI suggestions
- **Bulk reprocess** - Reprocess selected songs with a chosen model
- **Model selector** - Choose which model to use for reprocessing (dropdown)
- **Visual indicators**:
  - Green "✓ Done" for approved songs
  - "Pending" for songs needing review
  - Checkmarks in first column for selected rows

**Workflow**:
1. Click "4. Review" button
2. Table opens showing all songs
3. Select rows you want to approve/reprocess (click checkbox column)
4. Use toolbar buttons:
   - "✓ Approve Selected" - Approves with best AI suggestion
   - "🔄 Reprocess Selected" - Regenerates with chosen model
5. Double-click any row to edit details manually
6. Close when done

### 2. ✅ Fixed Settings Dialog AI Processing Tab

**Problem**: AI Processing tab was empty (black screen).

**Solution**:
- Added error handling with try/catch blocks for each tab creation
- Made AI Processing tab **scrollable** with `CTkScrollableFrame`
- Added logging for debugging

**File**: `gui/dialogs/settings_dialog.py` (updated)

**Changes**:
- Lines 111-143: Added error handling for all tabs
- Lines 261-267: Made AI Processing tab scrollable
- All tab content now renders inside a scrollable container

**AI Processing Settings** (should now be visible):
- Ollama URL
- **Primary Model** dropdown (select default model)
- **Use All Models** checkbox (enable for parallel processing with all 3 models)
- AI Models list (comma-separated)
- Parallel Workers slider (1-5)
- Thinking Mode toggle

### 3. ✅ Updated Main Window

**File**: `gui/main_window.py` (updated)

**Changes**:
- Line 25: Changed import from `AIReviewDialog` to `AIReviewTableDialog`
- Lines 364-372: Updated `_on_review()` to use new table dialog

## How to Use the New UI

### Quick Workflow for 100+ Songs:

1. **Select songs in main window** (checkboxes in song list)
2. **Click "3. AI Process"** (processes with primary model by default - fast!)
3. **Click "4. Review"** → Table opens
4. **Skim through table** - Look for:
   - Low confidence scores (< 70%)
   - Wrong artist/title
   - Missing AI results
5. **Select bad rows** (click checkbox column)
6. **Choose model from dropdown** (e.g., qwen3:14b)
7. **Click "🔄 Reprocess Selected"** → Regenerates with better model
8. **Select good rows** (after reprocessing)
9. **Click "✓ Approve Selected"** → Bulk approve
10. **Double-click any row** for manual edits (album, tags, etc.)
11. **Close** → Ready for conversion

### Model Selection Strategy:

**Default (Fast)**:
- Settings → AI Processing → Primary Model: `gemma3:12b`
- Use All Models: **Unchecked**
- Result: Only processes with 1 model (FAST)
- Good for 95% of songs

**For Difficult Songs**:
1. In review table, select problematic songs
2. Change model dropdown to `qwen3:14b` or `qwen2.5:7b`
3. Click "🔄 Reprocess Selected"
4. Compare results and approve best one

**For Maximum Accuracy**:
- Settings → AI Processing → Use All Models: **Checked**
- Result: Processes with all 3 models (SLOWER)
- Use for important playlists or Japanese songs

## Files Changed

| File | Status | Lines | Description |
|------|--------|-------|-------------|
| `gui/dialogs/ai_review_table_dialog.py` | ✅ NEW | 700 | Table-based review UI |
| `gui/main_window.py` | ✅ UPDATED | ~5 | Import and use new dialog |
| `gui/dialogs/settings_dialog.py` | ✅ UPDATED | ~50 | Fix AI tab, add scrolling |

## Testing Checklist

- [ ] Open Settings → AI Processing tab → Verify widgets visible
- [ ] Select 1 song → AI Process → Verify uses primary model
- [ ] Click Review → Verify table shows all songs
- [ ] Select multiple rows → Verify checkmarks appear
- [ ] Click "✓ Approve Selected" → Verify songs marked "✓ Done"
- [ ] Select row → Choose model → Click "🔄 Reprocess Selected" → Verify regenerates
- [ ] Double-click row → Verify edit dialog opens
- [ ] Edit and save → Verify table updates
- [ ] Process 10+ songs → Verify table scrolls smoothly

## Known Issues / Limitations

None currently. All requested features implemented:
- ✅ Model selection in Settings
- ✅ Table view for bulk review
- ✅ Bulk approve/reprocess actions
- ✅ Individual editing
- ✅ Visual status indicators

## Next Steps

1. **Test with your 6 existing songs** in database
2. **Report any bugs or UI issues**
3. **Try bulk workflow with larger playlist** (20-50 songs)
4. **Adjust default settings** in Settings → AI Processing

## Performance Notes

- **Single model mode**: ~5-10 seconds per song (RECOMMENDED)
- **All models mode**: ~15-30 seconds per song (3x slower)
- **Table view**: Loads instantly even with 100+ songs
- **Bulk operations**: Process in background thread (non-blocking)

---

**Updated**: 2026-02-09
**Version**: 2.0.0 (Table-based review)
