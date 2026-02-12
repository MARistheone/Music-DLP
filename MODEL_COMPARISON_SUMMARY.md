# VTuber Music Test - Model Comparison Summary

**Date**: 2026-02-10
**Test**: VTuber-specific prompts (15 test cases)
**Temperature**: 0.5
**Prompt Version**: V2

---

## Overall Results

| Model | Exact Matches | Acceptable | Total Correct | **Accuracy** | Avg Confidence | Status |
|-------|--------------|-----------|---------------|----------|----------------|--------|
| **gemma3:12b** | 7/15 (46.7%) | 1/15 (6.7%) | 8/15 | **53.3%** ✓ | 0.86 | **BEST** |
| qwen2.5:7b | 5/15 (33.3%) | 1/15 (6.7%) | 6/15 | **40.0%** | 0.77 | Poor |
| qwen3:14b | 3/15 (20.0%) | 2/15 (13.3%) | 5/15 | **33.3%** ✗ | 0.81 | **WORST** |

---

## Key Findings

### 1. gemma3:12b is the Clear Winner
- **Highest accuracy**: 53.3% on VTuber content
- **Best at avoiding VTuber name extraction**: Correctly identifies original artists more often
- **Confidence**: Slightly high (0.86) but acceptable
- **Recommendation**: Use this for production

### 2. qwen3:14b Performed Worst
- **Lowest accuracy**: Only 33.3%
- **Major flaw**: Frequently extracts VTuber/cover artist name instead of original artist
  - Test 2: "Official Hige Dandandan" instead of "Gawr Gura"
  - Test 8: "Shiraishi Fubuki" instead of "Unknown Artist"
  - Test 9: "Shirakami Fubuki" instead of "TK from Ling tosite sigure"
  - Test 14: "Calli" instead of "TK from Ling tosite sigure"
- **Not recommended** for VTuber/Japanese music

### 3. qwen2.5:7b is Middle Ground
- **Moderate accuracy**: 40.0%
- **Better than qwen3:14b** but still not good enough
- **Lower confidence** (0.77) - more conservative

---

## Detailed Breakdown

### By Song Type

| Song Type | gemma3:12b | qwen2.5:7b | qwen3:14b |
|-----------|-----------|-----------|-----------|
| **Original Songs** | 2/4 (50%) | 2/4 (50%) | 1/4 (25%) |
| **Cover Songs** | 5/10 (50%) | 4/10 (40%) | 3/10 (30%) |
| **Collab Songs** | 1/1 (100%) | 0/1 (0%) | 1/1 (100%) |

### Confidence Calibration

| Model | In Expected Range | Avg Confidence | Assessment |
|-------|------------------|----------------|------------|
| gemma3:12b | 8/15 (53.3%) | 0.86 | Too high |
| qwen2.5:7b | 8/15 (53.3%) | 0.77 | Good ✓ |
| qwen3:14b | 5/15 (33.3%) | 0.81 | Good ✓ |

---

## Common Failures Across All Models

### 1. Cover Artist Confusion
**Problem**: Extracting VTuber name instead of original artist

- **Test 4**: "Ride on Time" - All models fail to identify Tatsuro Yamashita
  - gemma3:12b → "LiSA"
  - qwen3:14b → "Exile"
  - qwen2.5:7b → "Unknown Artist"

- **Test 9**: "Unravel" karaoke - Original artist: TK from Ling tosite sigure
  - gemma3:12b → ✓ Correct
  - qwen3:14b → "Shirakami Fubuki" (VTuber name)
  - qwen2.5:7b → "白上フブキ" (VTuber name in Japanese)

### 2. Vocaloid Song Knowledge Gaps
**Problem**: Not recognizing well-known Vocaloid producers

- **Test 11**: "神っぽいな" by PinocchioP
  - gemma3:12b → "Sou"
  - qwen3:14b → "Unknown Artist"
  - qwen2.5:7b → "葛葉" (VTuber name)

- **Test 12**: "天ノ弱" by 164
  - gemma3:12b → "Yunomi"
  - qwen3:14b → "B'z"
  - qwen2.5:7b → "Unknown Artist"

### 3. Romanization Inconsistency
**Problem**: Japanese artist names not properly romanized

- **Test 3**: "バルーン" (BALLOON)
  - gemma3:12b → "バルーン" (not romanized)
  - qwen3:14b → "Unknown Artist"
  - qwen2.5:7b → "Charles / バルーン" (mixed)

- **Test 15**: "星街すいせい" (Hoshimachi Suisei)
  - gemma3:12b → "Hoshizaki Suisei" (wrong romanization)
  - qwen3:14b → "Suisei Hoshimachi" (name order reversed)
  - qwen2.5:7b → "Star Street Suisei" (translated instead of romanized)

### 4. Collab Song Handling
**Problem**: Difficulty identifying primary artist in collaborations

- **Test 5**: Suisei × Calliope collab
  - gemma3:12b → "Unknown Artist"
  - qwen3:14b → "Suisei × Calliope" (both names, not primary)
  - qwen2.5:7b → "Suisei × Calliope" (both names, not primary)

---

## Performance by Test Case

| # | Test Name | gemma3:12b | qwen2.5:7b | qwen3:14b | Difficulty |
|---|-----------|-----------|-----------|-----------|-----------|
| 1 | Fly Me To The Moon | ✓ (acceptable) | ✓ (acceptable) | ✓ (acceptable) | Easy |
| 2 | Reflect (Gura original) | ✓ | ✓ | ✗ | Easy |
| 3 | Charles / BALLOON cover | ✗ | ✗ | ✗ | Hard |
| 4 | Ride on Time cover | ✗ | ✗ | ✗ | Hard |
| 5 | Suisei × Calliope collab | ✗ | ✗ | ✗ | Hard |
| 6 | King - Kanaria cover | ✓ | ✓ | ✓ | Easy |
| 7 | Kawaikute Gomen | ✓ | ✓ | ✓ | Medium |
| 8 | Unclear singing stream | ✗ | ✓ | ✗ | Hard |
| 9 | Unravel karaoke | ✓ | ✗ | ✗ | Medium |
| 10 | Shiny Smily Story (group) | ✓ | ✗ | ✓ (acceptable) | Medium |
| 11 | 神っぽいな Vocaloid | ✗ | ✗ | ✗ | Hard |
| 12 | 天ノ弱 Vocaloid | ✗ | ✗ | ✗ | Hard |
| 13 | Suspect (Gura original) | ✓ | ✓ | ✓ | Easy |
| 14 | Unravel fan upload | ✓ | ✗ | ✗ | Medium |
| 15 | KING (Suisei original) | ✗ | ✗ | ✗ | Medium |

---

## Recommendations

### For Production Use

**Primary Model**: **gemma3:12b**
- Best accuracy on VTuber content (53.3%)
- Most consistent at avoiding VTuber name extraction
- Confidence slightly high but manageable

**Settings**:
- Temperature: 0.4 (lower to reduce overconfidence)
- Consider post-processing to fix romanization issues

### What Still Needs Fixing

1. **Add VTuber-specific examples to prompts**
   - Emphasize: "For covers, extract ORIGINAL artist, not the VTuber"
   - Include examples of Test 4, 9, 11, 12

2. **Improve Vocaloid producer knowledge**
   - Add examples of PinocchioP, 164, DECO*27, etc.

3. **Standardize romanization**
   - Always romanize Japanese names (バルーン → BALLOON)
   - Use consistent name order (Hoshimachi Suisei, not Suisei Hoshimachi)

4. **Lower temperature to 0.3-0.4**
   - Reduce overconfidence (gemma3 avg 0.86 → target 0.70-0.80)

### Testing Next Steps

1. **Test gemma3:12b with temperature 0.3** to reduce confidence
2. **Test with improved prompts** (add VTuber examples)
3. **Compare general music test** to see if models perform better on non-VTuber content

---

## Conclusion

**gemma3:12b is the best model for VTuber/Japanese music**, but:
- 53.3% accuracy is still **too low for production** (target: >80%)
- All models struggle with:
  - Cover artist confusion (VTuber vs original)
  - Vocaloid song knowledge gaps
  - Romanization consistency
  - Collab song handling

**Next actions**:
1. Improve prompts with VTuber-specific examples
2. Lower temperature to 0.4
3. Re-test with improved prompts
4. Target: >75% accuracy before production deployment
