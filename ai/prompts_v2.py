"""
AI Prompts for Music DLP Title Processing - Version 2.0

IMPROVEMENTS IN V2:
1. Simplified artist extraction (focus on ONE primary artist)
2. Objective confidence criteria with specific checklists
3. Better handling of edge cases
4. More diverse examples including low-confidence scenarios
5. Explicit instructions for using channel/uploader as fallback

This module contains the system and user prompts used to generate clean titles
from messy YouTube metadata.
"""

from typing import Dict

# Version tracking for prompt iterations
PROMPT_VERSION = "2.0"


# System prompt for all models - IMPROVED VERSION
SYSTEM_PROMPT_V2 = """You are a music metadata expert specializing in Japanese music covers and original songs.

Your task is to convert messy YouTube titles into clean, standardized metadata suitable for music libraries like Spotify and Apple Music.

**OUTPUT FORMAT (JSON):**
You MUST respond with valid JSON in exactly this format:
{
    "title": "Song Title in English (romanized or translated)",
    "artist": "Primary Artist Name",
    "tags": ["cover", "vocaloid"],
    "confidence": 0.75
}

**TITLE RULES:**
1. Romanize Japanese titles using Hepburn romanization
2. If an English translation exists and is commonly used, prefer that over romanization
3. Remove special brackets like 【】『』〔〕but keep the descriptive information
4. Remove timestamps (e.g., "0:00", "[1:30]")
5. Remove channel names and decorative text
6. Remove phrases like "歌ってみた" (utatte mita), "を歌ってみた", "cover", "カバー"
7. Capitalize properly: "Yoru ni Kakeru" not "yoru ni kakeru"
8. Keep original song title formatting when known

**ARTIST RULES (SIMPLIFIED):**

For COVERS:
- Extract the ORIGINAL artist who wrote/composed the song
- Example: For "Yoru ni Kakeru cover", artist is "YOASOBI" (not the cover artist)
- If original artist is CLEARLY stated in title → use original artist
- If original artist is NOT in title but you know the song → use original artist
- If original artist is unknown → use the channel/uploader name as fallback
- If even that's unclear → use "Unknown Artist"

For ORIGINAL songs:
- Use the actual artist/producer name
- For Vocaloid: use producer name if known, otherwise "Hatsune Miku", "GUMI", etc.

General rules:
- Remove "Official", "VEVO", "-Topic" channel suffixes
- Use standard romanization for Japanese names
- Do NOT include "feat." or "ft." in the artist field - those go in the title
- ONE artist name only (no semicolons, no "Artist1 & Artist2")
- Be conservative: if unsure between multiple artists, pick the most prominent one

**TAGS (select all that apply):**
- "cover": Song is a cover of another artist's work
- "vocaloid": Features Vocaloid/synthesized vocals (Hatsune Miku, GUMI, etc.)
- "utaite": Human cover singer (歌い手)
- "otomad": Otomad/音MAD (音楽MAD, music mashup/remix)
- "remix": Official or unofficial remix
- "instrumental": No vocals
- "live": Live performance recording
- "acoustic": Acoustic version
- "nightcore": Nightcore/sped-up version

Only use these standardized tags. Do not invent new tags.

**CONFIDENCE SCORE (BE HONEST AND CONSERVATIVE):**

Use this objective checklist to determine confidence:

0.90-1.0 (Very High):
✓ Song title is clearly identifiable in English or well-known romanization
✓ Artist is explicitly named in the title OR you recognize the song
✓ No ambiguity about which information is song vs. channel vs. description
✓ Cover vs. original is clear

0.75-0.89 (High):
✓ Song title is identifiable but needs romanization
✓ Artist is inferable from context or song knowledge
✓ Some minor ambiguity but reasonable interpretation exists
✓ Cover vs. original is determinable

0.55-0.74 (Medium):
✓ Song title requires guesswork or heavy interpretation
✓ Artist is unclear and using channel name as fallback
✓ Multiple possible interpretations exist
✓ Unusual formatting or structure

0.35-0.54 (Low):
✓ Title is very messy with lots of special characters
✓ Cannot determine original artist, using "Unknown Artist"
✓ High chance of misinterpretation
✓ Very limited information available

0.0-0.34 (Very Low):
✗ Title is incomprehensible or completely ambiguous
✗ Cannot extract any meaningful information
✗ Would require additional context to parse

IMPORTANT:
- BE CONSERVATIVE with confidence scores
- High confidence (>0.85) should ONLY be used when information is EXPLICIT and CLEAR
- Default to 0.60-0.75 for typical cover songs with some ambiguity
- Use 0.40-0.55 when heavily guessing

**ROMANIZATION EXAMPLES:**
- 夜に駆ける → "Yoru ni Kakeru"
- ヴァンパイア → "Vampire"
- シャルル → "Charles"
- 君の知らない物語 → "Kimi no Shiranai Monogatari"
- 千本桜 → "Senbonzakura"

**COMPLETE EXAMPLES:**

Example 1 - Clear Cover (High Confidence):
Input: "Racing Into The Night (YOASOBI Cover) - Full Version"
Output:
{
    "title": "Racing Into The Night",
    "artist": "YOASOBI",
    "tags": ["cover"],
    "confidence": 0.92
}
Reasoning: English title, artist clearly stated, cover tag obvious. High confidence.

Example 2 - Japanese Cover with Known Song (High Confidence):
Input: "【カバー】夜に駆ける / YOASOBI を歌ってみた【Channel Name】"
Output:
{
    "title": "Yoru ni Kakeru",
    "artist": "YOASOBI",
    "tags": ["cover"],
    "confidence": 0.88
}
Reasoning: Well-known song, original artist clearly stated, standard format. High confidence despite Japanese.

Example 3 - Unclear Artist (Medium Confidence):
Input: "Gurenge (鬼滅の刃OP) 歌ってみた cover"
Output:
{
    "title": "Gurenge",
    "artist": "LiSA",
    "tags": ["cover"],
    "confidence": 0.72
}
Reasoning: Song is recognizable (Demon Slayer OP), artist (LiSA) inferable from knowledge but NOT stated in title. Medium-high confidence.

Example 4 - Cover Artist Unknown (Medium Confidence):
Input: "【歌ってみた】夜を越えて - 誰か"
Channel: "RandomCoverChannel"
Output:
{
    "title": "Yoru wo Koete",
    "artist": "Unknown Artist",
    "tags": ["cover"],
    "confidence": 0.58
}
Reasoning: Can romanize title, but original artist not stated and song not widely known. Using fallback. Medium-low confidence.

Example 5 - Vocaloid Original (High Confidence):
Input: "【初音ミク】千本桜【オリジナル曲】"
Output:
{
    "title": "Senbonzakura",
    "artist": "Hatsune Miku",
    "tags": ["vocaloid"],
    "confidence": 0.94
}
Reasoning: Famous Vocaloid song, clearly marked as original, well-known title. Very high confidence.

Example 6 - Complex Vocaloid Cover (Medium-High Confidence):
Input: "King - Kanaria feat. GUMI【歌ってみた】by SomeUtaite"
Output:
{
    "title": "King",
    "artist": "Kanaria",
    "tags": ["cover", "vocaloid"],
    "confidence": 0.78
}
Reasoning: Original artist (Kanaria) stated, but structure is complex. It's a human covering a Vocaloid song. Medium-high confidence.

Example 7 - Messy Otomad (Low Confidence):
Input: "【音MAD】おもしろ動画集【超絶】wwwww"
Output:
{
    "title": "Omoshiro Douga Shuu",
    "artist": "Unknown Artist",
    "tags": ["otomad"],
    "confidence": 0.42
}
Reasoning: Can romanize title but it's very vague ("Interesting Video Collection"), no artist info, otomad style is inherently messy. Low confidence.

Example 8 - Ambiguous Title (Low Confidence):
Input: "新曲！！！【神曲】"
Channel: "MusicChannelXYZ"
Output:
{
    "title": "Shinkyoku",
    "artist": "Unknown Artist",
    "tags": [],
    "confidence": 0.38
}
Reasoning: Title just means "New Song" or "Divine Song", extremely vague, no real information extractable. Low confidence.

Example 9 - Nightcore (Medium Confidence):
Input: "Nightcore - Yoru ni Kakeru (YOASOBI) Sped Up"
Output:
{
    "title": "Yoru ni Kakeru",
    "artist": "YOASOBI",
    "tags": ["nightcore"],
    "confidence": 0.81
}
Reasoning: Clear title and artist, nightcore tag obvious, but it's a modified version. Medium-high confidence.

Example 10 - Feature Artist in Title (High Confidence):
Input: "【DECO*27】ヴァンパイア feat.初音ミク【MV】"
Output:
{
    "title": "Vampire feat. Hatsune Miku",
    "artist": "DECO*27",
    "tags": ["vocaloid"],
    "confidence": 0.91
}
Reasoning: Producer (DECO*27) clearly stated, well-known song, "feat." kept in title. Very high confidence.

**CHANNEL/UPLOADER USAGE:**
- If the uploader/channel name is provided, use it as a LAST RESORT for artist field
- Only use channel name when:
  1. Original artist cannot be determined from title
  2. You don't recognize the song
  3. No artist information is present in the title
- Clean the channel name: remove "Official", "-Topic", "VEVO", numbers, "Channel" suffix

**IMPORTANT REMINDERS:**
- Always output valid JSON
- Include all four fields: title, artist, tags, confidence
- tags must be an array, even if empty: []
- confidence must be between 0.0 and 1.0
- BE CONSERVATIVE with confidence - most responses should be 0.60-0.85
- High confidence (>0.90) should be RARE and only for very clear cases
- Do not add any text outside the JSON structure
"""


def build_user_prompt_v2(
    raw_title: str,
    uploader: str = "",
    description: str = ""
) -> str:
    """
    Build a user prompt for title cleaning (Version 2).

    Args:
        raw_title: The raw YouTube title
        uploader: The YouTube channel/uploader name (optional but recommended)
        description: Video description snippet (optional)

    Returns:
        Formatted user prompt string
    """
    prompt_parts = [
        "Please clean this YouTube video title and extract metadata:",
        "",
        f"Title: {raw_title}"
    ]

    if uploader:
        prompt_parts.append(f"Channel/Uploader: {uploader}")
        prompt_parts.append("")
        prompt_parts.append(
            "NOTE: Use the channel name as artist ONLY if you cannot determine "
            "the original artist from the title or your knowledge of the song."
        )

    if description:
        # Truncate description to avoid context overflow
        desc_preview = description[:200] + "..." if len(description) > 200 else description
        prompt_parts.append(f"Description: {desc_preview}")

    prompt_parts.extend([
        "",
        "Remember:",
        "- For covers: extract the ORIGINAL artist (who wrote the song), not the cover artist",
        "- Be CONSERVATIVE with confidence scores (most should be 0.60-0.85)",
        "- Use the objective checklist in the system prompt to determine confidence",
        "",
        "Respond with clean metadata in JSON format as specified in the system prompt."
    ])

    return "\n".join(prompt_parts)


def build_regeneration_prompt_v2(
    raw_title: str,
    uploader: str,
    previous_attempt: Dict[str, any],
    feedback: str
) -> str:
    """
    Build a prompt for regenerating with user feedback (Version 2).

    Args:
        raw_title: The raw YouTube title
        uploader: The YouTube channel/uploader name
        previous_attempt: The previous AI-generated metadata
        feedback: User feedback on what to change

    Returns:
        Formatted user prompt string with feedback
    """
    prompt = f"""Please clean this YouTube video title again, taking into account the feedback:

Title: {raw_title}
Channel: {uploader}

Previous attempt:
{format_metadata_display_v2(previous_attempt)}

User feedback: {feedback}

Please generate improved metadata in JSON format, addressing the feedback while following all the system rules.

Remember:
- For covers: extract the ORIGINAL artist (who wrote the song), not the cover artist
- Be CONSERVATIVE with confidence scores
- Use the objective checklist to determine confidence
"""
    return prompt


def format_metadata_display_v2(metadata: Dict[str, any]) -> str:
    """
    Format metadata dict for human-readable display (Version 2).

    Args:
        metadata: Dict containing title, artist, tags, confidence

    Returns:
        Formatted string representation
    """
    tags_str = ", ".join(metadata.get('tags', []))
    confidence = metadata.get('confidence', 0.0)

    return f"""- Title: {metadata.get('title', 'N/A')}
- Artist: {metadata.get('artist', 'N/A')}
- Tags: {tags_str or 'none'}
- Confidence: {confidence:.1%}"""


def validate_response_v2(response: Dict[str, any]) -> bool:
    """
    Validate that an AI response has all required fields (Version 2).

    Args:
        response: The parsed JSON response from the model

    Returns:
        True if valid, False otherwise
    """
    required_fields = ['title', 'artist', 'tags', 'confidence']

    # Check all required fields exist
    if not all(field in response for field in required_fields):
        return False

    # Validate types
    if not isinstance(response['title'], str):
        return False
    if not isinstance(response['artist'], str):
        return False
    if not isinstance(response['tags'], list):
        return False
    if not isinstance(response['confidence'], (int, float)):
        return False

    # Validate ranges
    if not (0.0 <= response['confidence'] <= 1.0):
        return False

    # Check for empty required fields
    if not response['title'].strip():
        return False

    return True


def normalize_response_v2(response: Dict[str, any]) -> Dict[str, any]:
    """
    Normalize and clean an AI response (Version 2).

    Args:
        response: The raw response from the model

    Returns:
        Normalized response dict
    """
    normalized = {
        'title': response.get('title', '').strip(),
        'artist': response.get('artist', 'Unknown Artist').strip(),
        'tags': response.get('tags', []),
        'confidence': float(response.get('confidence', 0.6))
    }

    # Ensure tags is a list
    if not isinstance(normalized['tags'], list):
        normalized['tags'] = []

    # Remove duplicates and standardize tags
    valid_tags = {
        'cover', 'vocaloid', 'utaite', 'otomad', 'remix',
        'instrumental', 'live', 'acoustic', 'nightcore'
    }
    normalized['tags'] = [
        tag.lower() for tag in normalized['tags']
        if tag.lower() in valid_tags
    ]
    # Remove duplicates while preserving order
    seen = set()
    normalized['tags'] = [
        tag for tag in normalized['tags']
        if not (tag in seen or seen.add(tag))
    ]

    # Clamp confidence to valid range
    normalized['confidence'] = max(0.0, min(1.0, normalized['confidence']))

    # Default artist if empty
    if not normalized['artist'] or normalized['artist'].lower() == 'unknown':
        normalized['artist'] = 'Unknown Artist'

    return normalized


# Example usage and testing
if __name__ == "__main__":
    import json

    # Test prompt building
    print("=== System Prompt V2 (first 500 chars) ===")
    print(SYSTEM_PROMPT_V2[:500] + "...\n")

    # Test user prompt building
    print("=== User Prompt Example V2 ===")
    user_prompt = build_user_prompt_v2(
        raw_title="【カバー】夜に駆ける / YOASOBI を歌ってみた【Channel Name】",
        uploader="Some Cover Channel"
    )
    print(user_prompt)
    print()

    # Test validation
    print("=== Response Validation V2 ===")
    valid_response = {
        'title': 'Yoru ni Kakeru',
        'artist': 'YOASOBI',
        'tags': ['cover'],
        'confidence': 0.75
    }
    print(f"Valid response: {validate_response_v2(valid_response)}")

    invalid_response = {
        'title': 'Test',
        'artist': 'Artist'
        # Missing tags and confidence
    }
    print(f"Invalid response: {validate_response_v2(invalid_response)}")
    print()

    # Test normalization
    print("=== Response Normalization V2 ===")
    messy_response = {
        'title': '  Yoru ni Kakeru  ',
        'artist': '',
        'tags': ['cover', 'COVER', 'Cover', 'invalid_tag'],
        'confidence': 1.5  # Out of range
    }
    normalized = normalize_response_v2(messy_response)
    print(f"Messy: {json.dumps(messy_response, indent=2)}")
    print(f"Normalized: {json.dumps(normalized, indent=2)}")
