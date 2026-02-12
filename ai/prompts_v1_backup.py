"""
AI Prompts for Music DLP Title Processing.

This module contains the system and user prompts used to generate clean titles
from messy YouTube metadata.

The prompts are designed to:
- Handle Japanese song titles (romanization and translation)
- Extract artist information from covers
- Standardize tags (cover, vocaloid, otomad, etc.)
- Generate confidence scores
- Output structured JSON responses
"""

from typing import Dict


# Version tracking for prompt iterations
PROMPT_VERSION = "1.0"


# System prompt for all models
SYSTEM_PROMPT = """You are a music metadata expert specializing in Japanese music covers and original songs.

Your task is to convert messy YouTube titles into clean, standardized metadata suitable for music libraries like Spotify and Apple Music.

**OUTPUT FORMAT (JSON):**
You MUST respond with valid JSON in exactly this format:
{
    "title": "Song Title in English (romanized or translated)",
    "artist": "Artist Name",
    "tags": ["cover", "vocaloid", "otomad"],
    "confidence": 0.95
}

**TITLE RULES:**
1. Romanize Japanese titles using Hepburn romanization
2. If an English translation exists and is commonly used, prefer that over romanization
3. Remove special brackets like 【】『』〔〕but keep the descriptive information
4. Remove timestamps (e.g., "0:00", "[1:30]")
5. Remove channel names and decorative text
6. Remove phrases like "歌ってみた" (utatte mita), "を歌ってみた", "cover", "カバー"
7. Capitalize properly: "Yoru Ni Kakeru" not "yoru ni kakeru"
8. Keep original song title formatting when known

**ARTIST RULES:**
1. For covers: List BOTH original artist AND cover artist, separated by semicolon
   - Format: "Original Artist; Cover Artist"
   - Example: "YOASOBI; Nightcore Paradise"
   - The original artist comes first, then the cover artist/channel
2. For original songs: Use the actual artist/producer name only
3. Remove "Official", "VEVO", channel suffixes (unless it's part of the actual artist name)
4. Use standard romanization for Japanese names
5. If artist is truly unknown, use "Unknown"
6. Do not include "feat." or "ft." in the artist field - those should be in the title

**TAGS (select all that apply):**
- "cover": Song is a cover of another artist's work
- "vocaloid": Features Vocaloid/synthesized vocals (Hatsune Miku, etc.)
- "utaite": Human cover singer (歌い手)
- "otomad": Otomad/音MAD (音楽MAD, music mashup/remix)
- "remix": Official or unofficial remix
- "instrumental": No vocals
- "live": Live performance recording
- "acoustic": Acoustic version
- "nightcore": Nightcore/sped-up version

Only use these standardized tags. Do not invent new tags.

**CONFIDENCE SCORE:**
- 0.95-1.0: Very confident, clear information available
- 0.85-0.94: Confident, some interpretation needed
- 0.70-0.84: Moderate confidence, significant guessing
- 0.50-0.69: Low confidence, very unclear title
- Below 0.50: Should not be this low; if unclear, default to 0.70

**ROMANIZATION EXAMPLES:**
- 夜に駆ける → "Yoru ni Kakeru"
- ヴァンパイア → "Vampire"
- シャルル → "Charles"
- 君の知らない物語 → "Kimi no Shiranai Monogatari"
- 千本桜 → "Senbonzakura"

**COMPLETE EXAMPLES:**

Input: "【カバー】夜に駆ける / YOASOBI を歌ってみた【Channel Name】"
Output:
{
    "title": "Yoru ni Kakeru",
    "artist": "YOASOBI; Channel Name",
    "tags": ["cover"],
    "confidence": 0.95
}

Input: "Racing Into The Night (YOASOBI Cover) - Full Version"
Output:
{
    "title": "Racing Into The Night",
    "artist": "YOASOBI; Unknown",
    "tags": ["cover"],
    "confidence": 0.98
}

Input: "【初音ミク】千本桜【オリジナル曲】"
Output:
{
    "title": "Senbonzakura",
    "artist": "Hatsune Miku",
    "tags": ["vocaloid"],
    "confidence": 0.97
}

Input: "【音MAD】おもしろ動画集【Remix】"
Output:
{
    "title": "Omoshiro Douga Shuu",
    "artist": "Unknown",
    "tags": ["otomad", "remix"],
    "confidence": 0.65
}

Input: "Gurenge (鬼滅の刃OP) 歌ってみた cover"
Output:
{
    "title": "Gurenge",
    "artist": "LiSA; Unknown",
    "tags": ["cover"],
    "confidence": 0.92
}

Input: "King - Kanaria feat. GUMI【歌ってみた】by SomeUtaite"
Output:
{
    "title": "King",
    "artist": "Kanaria; SomeUtaite",
    "tags": ["cover", "vocaloid"],
    "confidence": 0.94
}

Input: "ヴァンパイア / DECO*27 feat.初音ミク"
Output:
{
    "title": "Vampire",
    "artist": "DECO*27",
    "tags": ["vocaloid"],
    "confidence": 0.96
}

**IMPORTANT:**
- Always output valid JSON
- Include all four fields: title, artist, tags, confidence
- tags must be an array, even if empty: []
- confidence must be a number between 0.0 and 1.0
- Do not add any text outside the JSON structure
"""


def build_user_prompt(
    raw_title: str,
    uploader: str = "",
    description: str = ""
) -> str:
    """
    Build a user prompt for title cleaning.

    Args:
        raw_title: The raw YouTube title
        uploader: The YouTube channel/uploader name (optional)
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
        prompt_parts.append(f"Channel: {uploader}")

    if description:
        # Truncate description to avoid context overflow
        desc_preview = description[:200] + "..." if len(description) > 200 else description
        prompt_parts.append(f"Description: {desc_preview}")

    prompt_parts.extend([
        "",
        "Respond with clean metadata in JSON format as specified in the system prompt."
    ])

    return "\n".join(prompt_parts)


def build_regeneration_prompt(
    raw_title: str,
    previous_attempt: Dict[str, any],
    feedback: str
) -> str:
    """
    Build a prompt for regenerating with user feedback.

    This is used when the user is not satisfied with the AI's initial attempt
    and wants to regenerate with specific guidance.

    Args:
        raw_title: The raw YouTube title
        previous_attempt: The previous AI-generated metadata
        feedback: User feedback on what to change

    Returns:
        Formatted user prompt string with feedback
    """
    prompt = f"""Please clean this YouTube video title again, taking into account the feedback:

Title: {raw_title}

Previous attempt:
{format_metadata_display(previous_attempt)}

User feedback: {feedback}

Please generate improved metadata in JSON format, addressing the feedback while following all the system rules.
"""
    return prompt


def format_metadata_display(metadata: Dict[str, any]) -> str:
    """
    Format metadata dict for human-readable display.

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


def validate_response(response: Dict[str, any]) -> bool:
    """
    Validate that an AI response has all required fields.

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


def normalize_response(response: Dict[str, any]) -> Dict[str, any]:
    """
    Normalize and clean an AI response.

    This ensures consistent formatting and fixes common issues.

    Args:
        response: The raw response from the model

    Returns:
        Normalized response dict
    """
    normalized = {
        'title': response.get('title', '').strip(),
        'artist': response.get('artist', 'Unknown').strip(),
        'tags': response.get('tags', []),
        'confidence': float(response.get('confidence', 0.7))
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
    if not normalized['artist']:
        normalized['artist'] = 'Unknown'

    return normalized


# Pre-defined prompts for common scenarios
COMMON_SCENARIOS = {
    'vocaloid_original': {
        'example_title': '【初音ミク】楽曲名【オリジナル】',
        'expected': {
            'tags': ['vocaloid'],
            'note': 'Original Vocaloid song'
        }
    },
    'human_cover': {
        'example_title': '【歌ってみた】楽曲名 / アーティスト名',
        'expected': {
            'tags': ['cover'],
            'note': 'Human cover of existing song'
        }
    },
    'vocaloid_cover': {
        'example_title': '【初音ミク】楽曲名 / アーティスト名【カバー】',
        'expected': {
            'tags': ['cover', 'vocaloid'],
            'note': 'Vocaloid cover of existing song'
        }
    },
    'otomad': {
        'example_title': '【音MAD】タイトル',
        'expected': {
            'tags': ['otomad'],
            'note': 'Music MAD/mashup'
        }
    }
}


# Example usage and testing
if __name__ == "__main__":
    import json

    # Test prompt building
    print("=== System Prompt ===")
    print(SYSTEM_PROMPT[:500] + "...\n")

    # Test user prompt building
    print("=== User Prompt Example ===")
    user_prompt = build_user_prompt(
        raw_title="【カバー】夜に駆ける / YOASOBI を歌ってみた【Channel Name】",
        uploader="Some Cover Channel"
    )
    print(user_prompt)
    print()

    # Test validation
    print("=== Response Validation ===")
    valid_response = {
        'title': 'Yoru ni Kakeru',
        'artist': 'YOASOBI',
        'tags': ['cover'],
        'confidence': 0.95
    }
    print(f"Valid response: {validate_response(valid_response)}")

    invalid_response = {
        'title': 'Test',
        'artist': 'Artist'
        # Missing tags and confidence
    }
    print(f"Invalid response: {validate_response(invalid_response)}")
    print()

    # Test normalization
    print("=== Response Normalization ===")
    messy_response = {
        'title': '  Yoru ni Kakeru  ',
        'artist': '',
        'tags': ['cover', 'COVER', 'Cover', 'invalid_tag'],
        'confidence': 1.5  # Out of range
    }
    normalized = normalize_response(messy_response)
    print(f"Messy: {json.dumps(messy_response, indent=2)}")
    print(f"Normalized: {json.dumps(normalized, indent=2)}")
    print()

    # Test display formatting
    print("=== Display Formatting ===")
    print(format_metadata_display(valid_response))
