# AI Prompts V3 - Implementation Handoff

**Date**: 2026-02-10
**Status**: ✅ Tested and ready to deploy
**Time to implement**: 15-20 minutes

---

## What Was Done

✅ Created VTuber-enhanced AI prompts (V3)
✅ Tested with 15 VTuber/Japanese music cases
✅ Achieved **93.3% accuracy** (up from 60%)
✅ Compared 3 models (gemma3:12b wins)
✅ Optimized temperature (0.3 is best)

---

## What Needs to Be Done

### Required Changes

**1. Deploy V3 prompts** → 2 minutes
```bash
cd "c:\Users\amiel\OneDrive\Documents\yt-dlp\Music-dlp\2026-2"
cp ai/prompts_v3.py ai/prompts.py
```

**2. Update title_processor.py** → 5 minutes

Open `ai/title_processor.py` and make these changes:

```python
# Line ~10: Update imports
from ai.prompts import SYSTEM_PROMPT, build_user_prompt
# (Should work automatically if you copied prompts_v3.py to prompts.py)

# Line ~200-250: Change temperature in generate_title()
temperature=0.3  # Changed from 0.7
```

**3. Optional: Remove qwen models** → 1 minute

In `ai/title_processor.py` line ~15-20:
```python
# OLD
self.models = ['gemma3:12b', 'qwen3:14b', 'qwen2.5:7b']

# NEW (recommended - qwen models performed poorly)
self.models = ['gemma3:12b']
```

**4. Test with real songs** → 10 minutes
- Add small VTuber playlist (10-15 songs)
- Run through full pipeline
- Verify AI results look correct

---

## Key Files

**Code:**
- `ai/prompts_v3.py` - New prompts (ready to deploy)
- `ai/title_processor.py` - Needs temperature change (0.7 → 0.3)

**Documentation:**
- `V3_PROMPTS_RESULTS.md` - Full test results
- `DEPLOY_V3.md` - Detailed deployment guide
- `MODEL_COMPARISON_SUMMARY.md` - Model comparison data

**Tests:**
- `test_vtuber_prompts_v3.py` - V3 test script
- Run: `python test_vtuber_prompts_v3.py --model gemma3:12b --temperature 0.3`

---

## Expected Results After Deployment

### Before (V2)
- 60% accuracy on VTuber music
- Cover artists confused (extracted VTuber names)
- Vocaloid producers not recognized
- Japanese names not romanized

### After (V3)
- **93.3% accuracy** on VTuber music
- Cover artists correct (extracts originals)
- Vocaloid producers recognized (PinocchioP, 164, BALLOON)
- Japanese names romanized (バルーン → BALLOON)

### Specific Improvements
- ✅ Original songs: 100% (was 50%)
- ✅ Cover songs: 90% (was 50%)
- ✅ Collab songs: 100% (was 100%)

---

## Configuration Summary

| Setting | Value | Why |
|---------|-------|-----|
| **Model** | gemma3:12b | Best accuracy (93% vs 33-40% for qwen) |
| **Temperature** | 0.3 | Optimal balance (tested 0.3, 0.5, 0.7) |
| **Prompts** | V3 | VTuber-enhanced with 15 examples |
| **Expected Accuracy** | 93% | 14/15 correct on test suite |

---

## Testing Checklist

After deployment:

- [ ] Imports work: `python -c "from ai.prompts import SYSTEM_PROMPT; print('OK')"`
- [ ] Temperature changed: `grep "temperature=" ai/title_processor.py` shows 0.3
- [ ] Test suite passes: `python test_vtuber_prompts_v3.py` shows 93%
- [ ] Real songs work: Process 10-15 VTuber songs, verify >90% accuracy
- [ ] No regressions: Check English songs still work correctly

---

## Rollback (If Needed)

If V3 performs worse than expected:

```bash
# Restore V2 (if you backed it up)
cp ai/prompts_v2_backup.py ai/prompts.py

# Revert temperature in title_processor.py
temperature=0.7  # Back to original
```

---

## Important Notes

### ⚠️ Critical Changes
1. **Temperature 0.3** is required - V3 was optimized for this
2. **gemma3:12b only** - qwen models extract VTuber names incorrectly
3. **Test before production** - Verify with 10-15 real songs first

### ✅ What V3 Fixes
- Cover artist confusion (now extracts ORIGINAL artists)
- Vocaloid knowledge gaps (PinocchioP, 164, BALLOON recognized)
- Romanization consistency (Japanese → English)
- Collab songs (extracts primary artist)

### ❌ Known Edge Case
- "Suspect" by Gawr Gura → Gets "Unknown Artist"
- Simple English title confuses model
- Only 1/15 failure, acceptable

---

## Success Metrics

Monitor first 50-100 songs:

**Target:**
- >90% artist accuracy
- Average confidence 0.70-0.85
- <10% manual corrections

**Red flags:**
- <80% accuracy → Investigate
- Confidence all >0.90 → Too confident
- Extracting VTuber names for covers → Wrong prompts loaded

---

## Next Steps After Deployment

1. ✅ Deploy V3 (follow this guide)
2. ⏳ Test with real playlist (10-15 songs)
3. ⏳ Monitor first 50 songs processed
4. ⏳ Collect edge cases for future improvements
5. ⏳ Consider Phase 6: Packaging (.exe creation)

---

## Quick Reference

**Deploy:**
```bash
cp ai/prompts_v3.py ai/prompts.py
# Edit title_processor.py: temperature=0.3
```

**Test:**
```bash
python test_vtuber_prompts_v3.py
```

**Verify:**
```bash
python main.py
# Process 10-15 VTuber songs
# Check AI Review Dialog results
```

**Expected:** 90%+ accuracy, confidence 0.70-0.85

---

## Support Files

- Detailed guide: `DEPLOY_V3.md`
- Full results: `V3_PROMPTS_RESULTS.md`
- Session summary: `SESSION_SUMMARY_AI_V3.md`
- Updated memory: `C:\Users\amiel\.claude\projects\...\memory\MEMORY.md`

---

**Status**: ⏳ Ready to implement
**Risk**: Low (easy rollback)
**Impact**: High (+33% accuracy)
**Time**: 15-20 minutes
