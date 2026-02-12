# AI Improvements V2 - Artist Extraction & Confidence Calibration

**Date**: 2026-02-10
**Version**: 2.0
**Status**: Ready for Testing

---

## Problems Identified

### 1. Poor Artist Extraction
- **Issue**: Models confused by "Original Artist; Cover Artist" format
- **Symptoms**:
  - Inconsistent results (sometimes original, sometimes cover artist)
  - Models guessing when info unclear
  - Semicolon format awkward for music libraries

### 2. Confidence Overestimation
- **Issue**: Models always report 95-98% confidence
- **Symptoms**:
  - No differentiation between clear and ambiguous titles
  - User cannot trust confidence scores for prioritizing review
  - Vague criteria ("clear information", "some interpretation") are subjective

---

## Improvements in V2

### 🎯 Artist Extraction - Simplified Strategy

**OLD (V1):**
```
Artist: "Original Artist; Cover Artist"
```
- Required both artists for covers
- Confusing when cover artist not mentioned
- Inconsistent results

**NEW (V2):**
```
Artist: "Original Artist" (for covers)
Artist: "Primary Artist" (for originals)
```

**New Rules:**
1. **For covers**: Always extract the ORIGINAL artist (who wrote the song)
2. **Fallback hierarchy**:
   - If original artist in title → use it
   - If you know the song → use original artist from knowledge
   - If unknown → use channel/uploader name
   - Last resort → "Unknown Artist"
3. **One artist only** (no semicolons, no "Artist1 & Artist2")
4. **Conservative approach**: When in doubt, pick most prominent artist

**Why this works better:**
- Simpler decision tree for models
- Matches music library conventions (Spotify, Apple Music focus on original artist)
- Uses channel name strategically as fallback
- More consistent results

### 📊 Confidence Calibration - Objective Criteria

**OLD (V1):**
```
0.95-1.0: "Very confident, clear information available"
0.85-0.94: "Confident, some interpretation needed"
```
- Subjective descriptions
- No specific criteria
- Models defaulted high

**NEW (V2):**
```
0.90-1.0 (Very High):
✓ Song title clearly identifiable in English or well-known romanization
✓ Artist explicitly named OR you recognize the song
✓ No ambiguity about song vs. channel vs. description
✓ Cover vs. original is clear

0.75-0.89 (High):
✓ Song title identifiable but needs romanization
✓ Artist inferable from context or song knowledge
✓ Some minor ambiguity but reasonable interpretation exists

0.55-0.74 (Medium):
✓ Song title requires guesswork or heavy interpretation
✓ Artist unclear, using channel name as fallback
✓ Multiple possible interpretations exist

0.35-0.54 (Low):
✓ Title very messy with special characters
✓ Cannot determine original artist, using "Unknown Artist"
✓ High chance of misinterpretation

0.0-0.34 (Very Low):
✗ Title incomprehensible or completely ambiguous
✗ Cannot extract any meaningful information
```

**Why this works better:**
- Objective checklist-based evaluation
- Models explicitly instructed to be conservative
- Expected range is 0.60-0.85 (realistic for cover songs)
- High confidence (>0.90) should be RARE
- Includes negative examples showing when to score low

### 📝 Enhanced Examples

**V2 includes 10 diverse examples** (vs. 7 in V1):
- Example 1: Clear cover → 0.92 confidence
- Example 2: Japanese cover, known song → 0.88
- Example 3: Unclear artist (using knowledge) → 0.72
- Example 4: Unknown artist fallback → 0.58
- Example 5: Famous Vocaloid → 0.94
- Example 6: Complex Vocaloid cover → 0.78
- **Example 7: Messy otomad → 0.42** ⭐ (LOW confidence example)
- **Example 8: Ambiguous title → 0.38** ⭐ (LOW confidence example)
- Example 9: Nightcore → 0.81
- Example 10: Feature artist → 0.91

**Key addition**: Examples 7-8 show models when to use LOW confidence

---

## How to Test V2 Prompts

### Option 1: Quick Test (Single Video)

Create a test script `test_prompts_v2.py`:

```python
import sys
sys.path.insert(0, '.')

from ai.ollama_client import OllamaClient
from ai.prompts_v2 import SYSTEM_PROMPT_V2, build_user_prompt_v2
import json

# Test cases with expected confidence ranges
test_cases = [
    {
        "title": "Racing Into The Night (YOASOBI Cover)",
        "uploader": "RandomChannel",
        "expected_artist": "YOASOBI",
        "expected_confidence": "0.85-0.95",
        "notes": "Clear English title, artist stated"
    },
    {
        "title": "【カバー】夜に駆ける / YOASOBI を歌ってみた【Channel Name】",
        "uploader": "Channel Name",
        "expected_artist": "YOASOBI",
        "expected_confidence": "0.85-0.92",
        "notes": "Well-known song, artist clearly stated"
    },
    {
        "title": "Gurenge (鬼滅の刃OP) 歌ってみた cover",
        "uploader": "SomeCoverChannel",
        "expected_artist": "LiSA",
        "expected_confidence": "0.65-0.80",
        "notes": "Artist not stated, must use knowledge"
    },
    {
        "title": "【音MAD】おもしろ動画集【超絶】wwwww",
        "uploader": "MADChannel",
        "expected_artist": "Unknown Artist",
        "expected_confidence": "0.30-0.50",
        "notes": "Very messy, low information"
    }
]

client = OllamaClient()

print("=== Testing V2 Prompts ===\n")

for i, test in enumerate(test_cases, 1):
    print(f"Test {i}: {test['title'][:50]}...")
    print(f"Expected: {test['expected_artist']} | Confidence: {test['expected_confidence']}")

    user_prompt = build_user_prompt_v2(
        raw_title=test['title'],
        uploader=test['uploader']
    )

    # Test with your best model (try gemma3:12b first)
    result = client.generate_title(
        model='gemma3:12b',
        system_prompt=SYSTEM_PROMPT_V2,
        user_prompt=user_prompt,
        temperature=0.5  # Lower temperature for V2
    )

    if result:
        print(f"Got: {result['artist']} | Confidence: {result['confidence']:.2f}")
        print(f"Title: {result['title']}")
        print(f"Tags: {result['tags']}")

        # Check if confidence is in expected range
        min_conf, max_conf = map(float, test['expected_confidence'].split('-'))
        in_range = min_conf <= result['confidence'] <= max_conf
        print(f"Confidence in range: {'✓' if in_range else '✗'}")
    else:
        print("FAILED - No response")

    print()
```

Run:
```bash
python test_prompts_v2.py
```

### Option 2: Full Integration Test

Modify `ai/title_processor.py` to use V2 prompts temporarily:

```python
# In title_processor.py, change imports at top:
from .prompts_v2 import (
    SYSTEM_PROMPT_V2 as SYSTEM_PROMPT,
    PROMPT_VERSION as PROMPT_VERSION_V2,
    build_user_prompt_v2 as build_user_prompt,
    validate_response_v2 as validate_response,
    normalize_response_v2 as normalize_response
)

# Also update the PROMPT_VERSION assignment
PROMPT_VERSION = "2.0"
```

Then run a normal batch processing test through your GUI.

### Option 3: A/B Comparison

Keep both versions and compare results:

1. Process 10 videos with V1 (current)
2. Delete AI attempts: `DELETE FROM ai_title_attempts WHERE video_id IN (...)`
3. Process same 10 videos with V2
4. Compare results in database

```sql
-- Compare confidence distributions
SELECT
    CASE
        WHEN confidence >= 0.90 THEN '0.90-1.00'
        WHEN confidence >= 0.75 THEN '0.75-0.89'
        WHEN confidence >= 0.55 THEN '0.55-0.74'
        ELSE 'Below 0.55'
    END as confidence_range,
    COUNT(*) as count
FROM ai_title_attempts
WHERE prompt_version = '2.0'
GROUP BY confidence_range;
```

---

## Configuration Changes

### 1. Lower Temperature

In [title_processor.py:201](title_processor.py#L201), change:

```python
# OLD
temperature=0.7

# NEW
temperature=0.5
```

**Why**: Lower temperature (0.5) = more deterministic, less creative guessing. Better for metadata extraction where consistency matters.

### 2. Use V2 Prompts

In `ai/prompts.py`, either:

**Option A: Replace** (permanent switch):
- Replace entire file content with `prompts_v2.py`
- Update PROMPT_VERSION to "2.0"

**Option B: Add toggle** (A/B testing):
```python
# At bottom of prompts.py
USE_V2 = True  # Toggle this

if USE_V2:
    from .prompts_v2 import (
        SYSTEM_PROMPT_V2 as SYSTEM_PROMPT,
        build_user_prompt_v2 as build_user_prompt,
        # etc.
    )
```

---

## Expected Results

### Artist Extraction

**Before (V1):**
- Title: "Yoru ni Kakeru cover"
- Artist: "YOASOBI; Unknown" ❌ (semicolon format awkward)

**After (V2):**
- Title: "Yoru ni Kakeru"
- Artist: "YOASOBI" ✅ (clean, consistent)

**Before (V1):**
- Title: "Some unknown song 歌ってみた"
- Channel: "CoverChannel123"
- Artist: "Unknown; CoverChannel123" ❌ (weird format)

**After (V2):**
- Title: "Some Unknown Song"
- Artist: "CoverChannel123" ✅ (uses channel as fallback)

### Confidence Calibration

**Before (V1):**
- Clear title: 0.95-0.98
- Unclear title: 0.92-0.95
- Very messy: 0.88-0.92
- **Problem**: Everything 88%+ → no differentiation

**After (V2):**
- Clear title: 0.88-0.94 ✅
- Unclear title: 0.65-0.80 ✅
- Very messy: 0.35-0.55 ✅
- **Better**: Wide spread allows prioritizing review

---

## Rollback Plan

If V2 doesn't work well:

1. **Revert prompts.py**:
   - Keep V1 as backup: `cp prompts.py prompts_v1_backup.py`
   - If V2 fails: `cp prompts_v1_backup.py prompts.py`

2. **Database cleanup**:
   ```sql
   -- Remove V2 attempts if needed
   DELETE FROM ai_title_attempts WHERE prompt_version = '2.0';
   ```

3. **Restore temperature**:
   - Change back to 0.7 in title_processor.py

---

## Metrics to Track

After testing V2, check:

1. **Confidence Distribution**:
   ```sql
   SELECT
       AVG(confidence) as avg_conf,
       MIN(confidence) as min_conf,
       MAX(confidence) as max_conf,
       STDDEV(confidence) as std_dev
   FROM ai_title_attempts
   WHERE prompt_version = '2.0';
   ```
   - **Good**: avg=0.70-0.78, min=0.35, max=0.94, std_dev>0.15
   - **Bad**: avg>0.90, min>0.85, std_dev<0.05 (still overconfident)

2. **Artist Extraction Accuracy**:
   - Manually review 20 results
   - Count how many have correct original artist
   - Target: >85% correct (vs. current estimate ~60-70%)

3. **User Satisfaction**:
   - Do confidence scores correlate with actual quality?
   - Are low-confidence (0.40-0.60) results actually messy?
   - Are high-confidence (>0.85) results actually clean?

---

## Additional Recommendations

### 1. Consider Model-Specific Temperature

Different models may need different temperatures:

```python
# In title_processor.py
MODEL_TEMPERATURES = {
    'gemma3:12b': 0.5,    # More conservative
    'qwen3:14b': 0.6,     # Slightly more flexible
    'qwen2.5:7b': 0.4     # Most conservative (less capable)
}

temperature = MODEL_TEMPERATURES.get(model_name, 0.5)
```

### 2. Add Confidence Calibration Layer

Post-process confidence scores based on observed patterns:

```python
def calibrate_confidence(raw_confidence: float, indicators: dict) -> float:
    """
    Adjust confidence based on objective indicators.

    indicators = {
        'has_special_chars': bool,
        'artist_in_title': bool,
        'known_song': bool,
        'japanese_romanization_needed': bool
    }
    """
    adjusted = raw_confidence

    # Penalize special characters
    if indicators.get('has_special_chars', False):
        adjusted *= 0.85

    # Boost if artist explicitly stated
    if indicators.get('artist_in_title', False):
        adjusted = min(1.0, adjusted * 1.15)

    # Lower if romanization needed (more error-prone)
    if indicators.get('japanese_romanization_needed', False):
        adjusted *= 0.90

    return max(0.0, min(1.0, adjusted))
```

### 3. Ensemble Confidence

Use agreement between models as confidence indicator:

```python
def ensemble_confidence(attempts: List[dict]) -> float:
    """
    Calculate confidence based on model agreement.

    If all 3 models agree on artist → boost confidence
    If all disagree → lower confidence
    """
    artists = [a['artist'] for a in attempts]
    titles = [a['title'] for a in attempts]

    # Count unique values
    artist_agreement = len(set(artists)) == 1  # All same
    title_agreement = len(set(titles)) <= 2     # At most 2 variations

    avg_conf = sum(a['confidence'] for a in attempts) / len(attempts)

    if artist_agreement and title_agreement:
        return min(1.0, avg_conf * 1.2)  # Boost
    elif len(set(artists)) == 3:  # All different
        return avg_conf * 0.7  # Penalty
    else:
        return avg_conf
```

---

## Next Steps

1. **Test V2 prompts** with Quick Test script (10 minutes)
2. **Review results** - are confidence scores more realistic?
3. **A/B test** - process 20 songs with V1 vs V2, compare accuracy
4. **Adjust temperature** if needed (try 0.4, 0.5, 0.6)
5. **Consider ensemble confidence** if individual models still overconfident
6. **Deploy to production** if results better than V1

---

## Questions?

- Check [prompts_v2.py](prompts_v2.py) for full prompt text
- See examples in the V2 prompt (10 diverse cases)
- Test script in this document (Option 1)

**Remember**: The goal is USEFUL confidence scores that help you prioritize which songs to review manually!
