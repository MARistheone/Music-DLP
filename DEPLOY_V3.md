# Deploying AI Prompts V3 - Step-by-Step Guide

**Date**: 2026-02-10
**Status**: ✅ Ready for deployment
**Expected Impact**: +33% accuracy improvement (60% → 93%)

---

## Pre-Deployment Checklist

- [x] V3 prompts tested with 15 VTuber test cases
- [x] 93.3% accuracy achieved (14/15 correct)
- [x] Model comparison completed (gemma3:12b is best)
- [x] Temperature optimized (0.3 is optimal)
- [ ] Test with real playlist (10-15 songs)
- [ ] Backup current production prompts
- [ ] Deploy V3 prompts
- [ ] Update configuration
- [ ] Verify in production

---

## Step 1: Backup Current Prompts

```bash
cd "c:\Users\amiel\OneDrive\Documents\yt-dlp\Music-dlp\2026-2"

# Backup current prompts (if ai/prompts.py exists and is V2)
cp ai/prompts.py ai/prompts_v2_backup.py

# Or if using prompts_v2.py
cp ai/prompts_v2.py ai/prompts_v2_backup.py
```

---

## Step 2: Deploy V3 Prompts

**Option A: Direct deployment (recommended)**

```bash
# Copy V3 to production filename
cp ai/prompts_v3.py ai/prompts.py
```

**Option B: Keep V3 filename and update imports**

If you prefer to keep `prompts_v3.py` as the filename, update these files:
- `ai/title_processor.py`
- Any other files importing from `ai/prompts.py`

```python
# Change from:
from ai.prompts import SYSTEM_PROMPT, build_user_prompt

# To:
from ai.prompts_v3 import SYSTEM_PROMPT_V3 as SYSTEM_PROMPT, build_user_prompt_v3 as build_user_prompt
```

---

## Step 3: Update title_processor.py Configuration

Open `ai/title_processor.py` and make these changes:

### Change 1: Update Temperature

Find the `generate_title()` method (around line 200-250):

```python
# OLD (V2 default)
temperature=0.7

# NEW (V3 optimal)
temperature=0.3
```

### Change 2: Update Imports (if needed)

If you deployed V3 as `ai/prompts.py`:

```python
# Should already be:
from ai.prompts import SYSTEM_PROMPT, build_user_prompt
# No change needed if you used Option A above
```

If you kept V3 as `ai/prompts_v3.py`:

```python
# Change to:
from ai.prompts_v3 import SYSTEM_PROMPT_V3 as SYSTEM_PROMPT
from ai.prompts_v3 import build_user_prompt_v3 as build_user_prompt
```

### Change 3: Verify Model Configuration

Ensure `title_processor.py` is using gemma3:12b as the primary model:

```python
# Should be (around line 15-20):
self.models = ['gemma3:12b', 'qwen3:14b', 'qwen2.5:7b']
```

**IMPORTANT**: Based on test results, consider removing qwen models:

```python
# Recommended (gemma3 only):
self.models = ['gemma3:12b']

# OR keep for comparison but know they perform worse:
self.models = ['gemma3:12b', 'qwen3:14b', 'qwen2.5:7b']
```

---

## Step 4: Test with Real Playlist (CRITICAL)

Before deploying to production, test with 10-15 real VTuber/Japanese songs:

### 4.1 Add Test Playlist

```bash
# Run the app
python main.py

# In GUI:
1. Add a small VTuber playlist (10-15 songs)
   Example: "Hololive Music" playlist
2. Extract metadata (Stage 1)
3. Download songs (Stage 2)
4. Run AI processing (Stage 3)
```

### 4.2 Review AI Results

In the AI Review Dialog:
- Check artist extraction accuracy
- Verify confidence scores (should average 0.70-0.85)
- Look for:
  - ✅ Original artists for covers (not VTuber names)
  - ✅ Romanized Japanese names (BALLOON, not バルーン)
  - ✅ Well-known Vocaloid producers recognized
  - ✅ Collab songs using primary artist

### 4.3 Success Criteria

- **Target**: >90% artist accuracy (at least 9/10 correct)
- **Confidence**: Average 0.70-0.85
- **No regressions**: V3 should not perform worse than V2 on any song type

If results are worse than expected, see "Rollback" section below.

---

## Step 5: Monitor First Production Use

After deploying, monitor the first 50-100 songs processed:

### Metrics to Track

1. **Artist Accuracy**: How many require manual correction?
   - Target: <10% (9/10 correct)
   - If >15% need correction, investigate

2. **Confidence Distribution**:
   - Most should be 0.60-0.85
   - Very high (>0.90): Rare
   - Very low (<0.50): Rare
   - If too many >0.90, model is overconfident

3. **Common Failures**:
   - Are there patterns? (specific artist, song type, etc.)
   - Add failing cases to test suite
   - Consider V3.1 improvements

### Log Review

Check `logs/music_dlp_YYYYMMDD.log` for:
- AI processing errors
- Confidence score warnings
- JSON parsing issues

---

## Rollback Plan (If Needed)

If V3 performs worse than expected:

### Quick Rollback (5 minutes)

```bash
# Restore V2 prompts
cp ai/prompts_v2_backup.py ai/prompts.py

# Revert temperature in title_processor.py
# Change temperature=0.3 back to temperature=0.7
```

### Investigate Issues

1. Compare V2 vs V3 results on same songs
2. Check which test cases are failing
3. Review confidence scores
4. Consider adjusting temperature (try 0.4, 0.5)

---

## Advanced Configuration

### Temperature Tuning

If you want to experiment with different temperatures:

| Temperature | Effect | When to Use |
|-------------|--------|-------------|
| 0.2-0.3 | Very conservative | High accuracy priority |
| 0.3-0.5 | Balanced (recommended) | Production default |
| 0.5-0.7 | More creative | Diverse outputs |

Edit in `ai/title_processor.py`:

```python
# Around line 200-250, in generate_title():
temperature=0.3  # Adjust as needed
```

### Model Selection

Based on testing, gemma3:12b is best. But you can configure:

```python
# ai/title_processor.py (around line 15-20)

# Option 1: Gemma only (fastest, most accurate)
self.models = ['gemma3:12b']

# Option 2: All three (slower, more choices)
self.models = ['gemma3:12b', 'qwen3:14b', 'qwen2.5:7b']

# Option 3: Gemma + Qwen2.5 (middle ground)
self.models = ['gemma3:12b', 'qwen2.5:7b']
```

**Recommendation**: Use gemma3:12b only. Other models add processing time without accuracy benefit.

---

## Verification Steps

After deployment, verify everything works:

### 1. Check Imports

```bash
# Test that V3 imports work
python -c "from ai.prompts_v3 import SYSTEM_PROMPT_V3; print('V3 prompts loaded successfully')"
```

### 2. Run Quick Test

```bash
# Run VTuber test suite with V3
python test_vtuber_prompts_v3.py --model gemma3:12b --temperature 0.3

# Should show:
# Total correct: 14/15 (93.3%)
```

### 3. Check GUI

```bash
# Launch app
python main.py

# Verify:
# - AI processing completes without errors
# - AI Review Dialog shows results
# - Confidence scores display correctly
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'ai.prompts_v3'"

**Solution:**
```bash
# Verify file exists
ls ai/prompts_v3.py

# If missing:
# V3 prompts file was not created. Re-create from session or use V2.
```

### Issue: "AttributeError: module 'ai.prompts_v3' has no attribute 'SYSTEM_PROMPT'"

**Solution:**
```python
# You imported the wrong constant name
# V3 uses SYSTEM_PROMPT_V3, not SYSTEM_PROMPT

# Fix in title_processor.py:
from ai.prompts_v3 import SYSTEM_PROMPT_V3 as SYSTEM_PROMPT
```

### Issue: Accuracy worse than 93%

**Possible causes:**
1. Different songs than test suite (normal variation)
2. Temperature too high (check title_processor.py)
3. Wrong model (should be gemma3:12b)
4. Import issue (using V2 instead of V3)

**Debug steps:**
```bash
# 1. Verify V3 is loaded
python -c "from ai.prompts import SYSTEM_PROMPT; print(SYSTEM_PROMPT[:100])"
# Should start with "You are a music metadata expert specializing in Japanese music"

# 2. Check temperature
grep "temperature=" ai/title_processor.py
# Should show temperature=0.3

# 3. Test specific song
python test_vtuber_prompts_v3.py --model gemma3:12b --temperature 0.3
```

### Issue: Confidence scores all >0.90

**Cause:** Temperature too low or wrong prompt version

**Solution:**
```python
# In title_processor.py, try:
temperature=0.4  # Up from 0.3

# Or verify you're using V3 prompts (they have better confidence calibration)
```

---

## Success Indicators

After 1-2 weeks of production use, you should see:

✅ **<10% manual corrections** on VTuber/Japanese music
✅ **Confidence scores useful** for prioritizing review
✅ **No major regressions** on English/general music
✅ **Correct romanization** of Japanese artist names
✅ **Original artists extracted** from covers (not VTuber names)

---

## Next Steps After Deployment

1. **Collect edge cases** - When manual corrections are needed, note why
2. **Build test cases** - Add problematic songs to test suite
3. **Monitor performance** - Track accuracy over time
4. **Consider V3.1** - If patterns emerge, improve prompts further
5. **Test general music** - Run V3 on non-VTuber content to ensure no regression

---

## Reference Files

- **V3 Prompts**: `ai/prompts_v3.py`
- **Test Script**: `test_vtuber_prompts_v3.py`
- **Full Results**: `V3_PROMPTS_RESULTS.md`
- **Model Comparison**: `MODEL_COMPARISON_SUMMARY.md`
- **Memory**: `C:\Users\amiel\.claude\projects\...\memory\MEMORY.md`

---

## Support

If you encounter issues:
1. Check `logs/music_dlp_YYYYMMDD.log`
2. Review `V3_PROMPTS_RESULTS.md` for expected behavior
3. Compare against test suite results
4. Roll back to V2 if needed (see Rollback section)

---

**Deployment Status**: ⏳ Ready to deploy
**Expected Impact**: +33% accuracy (60% → 93%)
**Risk Level**: Low (easy rollback, thorough testing)
**Recommendation**: ✅ Deploy V3 prompts
