# Testing Guide - AI Prompt Evaluation

**Date**: 2026-02-10
**Purpose**: Compare AI performance across different music types

---

## Test Scripts Overview

### 1. [test_prompts_v2.py](test_prompts_v2.py) - General Music Test
**Focus**: Broad coverage of music types
- Japanese covers (utaite)
- Vocaloid songs
- English covers
- Nightcore
- Otomad (音MAD)
- Messy/ambiguous titles

**Test cases**: 10 scenarios ranging from very clear (0.90+ expected) to very messy (0.30-0.50 expected)

### 2. [test_vtuber_prompts.py](test_vtuber_prompts.py) - VTuber-Specific Test
**Focus**: VTuber music challenges
- Hololive/Nijisanji songs
- VTuber character names (Gawr Gura, Mori Calliope, etc.)
- Agency branding
- Collab songs
- Original VTuber songs vs covers
- Fan uploads vs official channels

**Test cases**: 15 VTuber-specific scenarios with unique challenges

---

## Running Tests

### Quick Start

```bash
cd "c:\Users\amiel\OneDrive\Documents\yt-dlp\Music-dlp\2026-2"

# General music test (10 test cases)
python test_prompts_v2.py

# VTuber music test (15 test cases)
python test_vtuber_prompts.py
```

### Test Different Models

```bash
# Test with gemma3:12b (default - most accurate)
python test_prompts_v2.py --model gemma3:12b

# Test with qwen3:14b (alternative)
python test_vtuber_prompts.py --model qwen3:14b

# Test with qwen2.5:7b (fastest, less accurate)
python test_prompts_v2.py --model qwen2.5:7b
```

### Test Different Temperatures

```bash
# More conservative (0.3) - less creative, more consistent
python test_prompts_v2.py --temperature 0.3

# Recommended (0.5) - balanced
python test_prompts_v2.py --temperature 0.5

# More creative (0.7) - higher variance
python test_prompts_v2.py --temperature 0.7
```

---

## Interpreting Results

### Artist Extraction Accuracy

**General Test Output:**
```
Artist accuracy: 18/20 (90.0%)
```

**Ratings:**
- **≥85%**: Excellent - Ready for production
- **70-84%**: Good - Minor issues, usable
- **<70%**: Poor - Needs improvement

**VTuber Test Output:**
```
Artist Extraction:
  Exact matches: 12/15 (80.0%)
  Acceptable: 2/15 (13.3%)
  Total correct: 14/15 (93.3%)
```

VTuber tests include "acceptable" for edge cases (e.g., "Frank Sinatra" vs "Bart Howard" for classic songs)

### Confidence Calibration

**Good Results:**
```
Average confidence: 0.72
Confidence accuracy: 16/20 (80.0%)
✓ Average confidence in good range (0.55-0.85)
```

**Targets:**
- **Average**: 0.60-0.80 (NOT 0.90+)
- **Accuracy**: >75% within expected ranges
- **Spread**: Low-confidence (0.30-0.50) for messy, high (0.85-0.95) for clear

**Bad Results (Overconfident):**
```
Average confidence: 0.93
⚠ WARNING: Average confidence is high (>0.85)!
```
→ Lower temperature or adjust prompts

**Bad Results (Underconfident):**
```
Average confidence: 0.48
⚠ WARNING: Average confidence is low (<0.55)!
```
→ Raise temperature or adjust criteria

---

## Comparing Results

### Run Both Tests

```bash
# Save outputs
python test_prompts_v2.py > results_general.txt
python test_vtuber_prompts.py > results_vtuber.txt

# Compare
notepad results_general.txt
notepad results_vtuber.txt
```

### What to Look For

**Scenario 1: VTuber accuracy much lower**
```
General: 90% accuracy
VTuber: 65% accuracy
```
→ Model struggles with VTuber names
→ Add VTuber examples to prompts

**Scenario 2: VTuber confidence higher**
```
General: 0.72 avg
VTuber: 0.88 avg
```
→ Model overconfident on VTuber content
→ Add low-confidence VTuber examples

**Scenario 3: Similar performance** ✓
```
General: 85% accuracy, 0.70 avg
VTuber: 82% accuracy, 0.73 avg
```
→ Prompts generalize well!

---

## Common Issues & Solutions

### Issue 1: All Confidence High (>0.90)

**Symptom:**
```
Test 1: 0.95, Test 2: 0.96, Test 3: 0.94...
Average: 0.94
```

**Solutions:**
1. Lower temperature to 0.3-0.4
2. Verify using V2 prompts (not V1)
3. Check if models are actually reading low-confidence examples

### Issue 2: Wrong Artist Direction

**Symptom:**
```
Title: "Yoru ni Kakeru (Cover)"
Expected: YOASOBI
Got: Unknown Artist ❌
```

**Cause**: Model doesn't know the song

**Solution**: Provide uploader/channel as fallback:
```python
user_prompt = build_user_prompt_v2(
    raw_title=title,
    uploader=uploader  # ← Make sure this is set!
)
```

### Issue 3: VTuber Name in Artist Field

**Symptom:**
```
Title: "King (Cover) - Gawr Gura"
Expected: Kanaria (original)
Got: Gawr Gura ❌ (cover artist)
```

**Solution**: Add VTuber examples to prompts emphasizing "ORIGINAL artist, not cover artist"

### Issue 4: VRAM Filling Up

**Already fixed!** Both test scripts use `auto_unload=True`

If still happening:
- Update Ollama
- Manually unload: `ollama unload gemma3:12b`

---

## Model Comparison

### Test All Models

```bash
echo "Testing gemma3:12b..."
python test_prompts_v2.py --model gemma3:12b > results_gemma3.txt

echo "Testing qwen3:14b..."
python test_prompts_v2.py --model qwen3:14b > results_qwen3.txt

echo "Testing qwen2.5:7b..."
python test_prompts_v2.py --model qwen2.5:7b > results_qwen25.txt
```

### Expected Performance

| Model | Accuracy | Avg Conf | Speed | Best For |
|-------|----------|----------|-------|----------|
| gemma3:12b | Highest (85-90%) | 0.70-0.75 | Medium | Accuracy priority |
| qwen3:14b | High (80-85%) | 0.68-0.72 | Medium | Balance |
| qwen2.5:7b | Medium (70-80%) | 0.72-0.78 | Fast | Speed priority |

---

## Success Criteria

### Before Production Deployment

Run both tests and check:

- [ ] General test: >80% artist accuracy
- [ ] VTuber test: >75% accuracy (if applicable)
- [ ] Average confidence: 0.60-0.80
- [ ] Confidence spread: Low (0.30-0.50) for messy, high (0.85-0.95) for clear
- [ ] VRAM: Models unload cleanly after tests

### Integration Steps

If tests pass:

1. Backup V1: `cp ai/prompts.py ai/prompts_v1_backup.py`
2. Deploy V2: `cp ai/prompts_v2.py ai/prompts.py`
3. Update temperature: Change to 0.5 in `title_processor.py`
4. Test with 10 real songs
5. Monitor AI review dialog - does confidence help?

---

## Quick Reference

### Test Commands
```bash
# General test
python test_prompts_v2.py

# VTuber test
python test_vtuber_prompts.py

# Different model
python test_prompts_v2.py --model qwen3:14b

# Different temperature
python test_prompts_v2.py --temperature 0.4
```

### Good Results Look Like
```
Artist accuracy: 18/20 (90.0%)
Confidence accuracy: 16/20 (80.0%)
Average confidence: 0.72
✓ Average confidence in good range (0.55-0.85)
```

### Next Steps
1. Run both tests
2. Check if results meet success criteria
3. Compare VTuber vs general performance
4. Adjust temperature if needed
5. Deploy to production if satisfied

**Goal**: Confidence scores that help prioritize review, not just noise!
