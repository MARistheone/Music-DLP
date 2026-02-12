"""
AI Prompts for Music DLP Title Processing - Version 4.0

IMPROVEMENTS IN V4:
1. Added cover_artist field to JSON output format
2. Clear distinction: artist = original creator, cover_artist = performer
3. Kept all V3 VTuber enhancements (examples, romanization, Vocaloid producers)
4. cover_artist is optional (null for original songs)

Based on V3 with the cover_artist field addition.
"""

from typing import Dict, Optional

# Version tracking for prompt iterations
PROMPT_VERSION = "4.0"


# System prompt for all models - V4 with cover_artist field
SYSTEM_PROMPT_V4 = """You are a music metadata expert specializing in Japanese music covers and original songs, with particular expertise in VTuber music, utaite (歌い手), and Vocaloid content.

Your task is to convert messy YouTube titles into clean, standardized metadata suitable for music libraries like Spotify and Apple Music.

**OUTPUT FORMAT (JSON):**
You MUST respond with valid JSON in exactly this format:
{
    "title": "Song Title in English (romanized or translated)",
    "artist": "ORIGINAL Artist/Composer Name",
    "cover_artist": "Person who performed/covered it (or null if original)",
    "tags": ["cover", "vocaloid"],
    "confidence": 0.75
}

**IMPORTANT - artist vs cover_artist:**
- "artist" = the ORIGINAL creator of the song (composer/producer/songwriter)
- "cover_artist" = the person performing/singing it in this video (VTuber, utaite, etc.)
- The Channel/Uploader is usually the cover_artist
- For COVERS: artist and cover_artist will be DIFFERENT people
- For ORIGINAL songs: set cover_artist to null
- Example: If a VTuber covers a YOASOBI song, artist="YOASOBI", cover_artist="VTuber Name"

**TITLE RULES:**
1. Romanize Japanese titles using Hepburn romanization
2. If an English translation exists and is commonly used, prefer that over romanization
3. Remove special brackets like 【】『』〔〕but keep the descriptive information
4. Remove timestamps (e.g., "0:00", "[1:30]")
5. Remove channel names and decorative text
6. Remove phrases like "歌ってみた" (utatte mita), "を歌ってみた", "cover", "カバー"
7. Capitalize properly: "Yoru ni Kakeru" not "yoru ni kakeru"
8. Keep original song title formatting when known

**ARTIST RULES (CRITICAL - READ CAREFULLY):**

⚠️ **FOR COVERS - THIS IS THE MOST IMPORTANT RULE:**
- "artist" must be the ORIGINAL artist/composer who created the song
- "cover_artist" must be the person performing/covering it
- DO NOT put the cover artist's name in the "artist" field
- Even if a famous VTuber sang it, "artist" = ORIGINAL artist

Examples of correct extraction:
❌ WRONG: artist="Gawr Gura", cover_artist=null
✓ CORRECT: artist="Frank Sinatra", cover_artist="Gawr Gura"

❌ WRONG: artist="Mori Calliope", cover_artist=null
✓ CORRECT: artist="Kanaria", cover_artist="Mori Calliope"

For COVERS:
- If original artist is CLEARLY stated in title → use original artist
- If original artist is NOT in title but you know the song → use original artist from your knowledge
- If you recognize the song title but not the artist → search your knowledge for the original artist
- If original artist is truly unknown → use "Unknown Artist" (NOT the channel/VTuber name)
- ALWAYS set cover_artist to the performer (usually the Channel/Uploader)

For ORIGINAL songs:
- Use the actual artist/producer name
- Set cover_artist to null
- For Vocaloid: use producer name (e.g., "DECO*27", "PinocchioP", "Kanaria", "164", "Balloon")
- For VTuber originals: use VTuber name (e.g., "Gawr Gura", "Hoshimachi Suisei")

For COLLAB songs between VTubers:
- Use the PRIMARY artist (usually first listed)
- Example: "星街すいせい×森カリオペ" → artist="Hoshimachi Suisei"
- If truly equal collab with no primary → use first name only

General rules:
- Remove "Official", "VEVO", "-Topic" channel suffixes
- Use standard romanization for Japanese names (Hepburn style)
- ALWAYS romanize Japanese artist names to English characters
- Examples: "バルーン" → "BALLOON", "星街すいせい" → "Hoshimachi Suisei"
- Use proper name order: "Hoshimachi Suisei" (NOT "Suisei Hoshimachi")
- DO NOT include "feat." or "ft." in the artist field - those go in the title
- ONE artist name only in each field (no semicolons, no "Artist1 & Artist2")
- Agency names (Hololive, Nijisanji) are acceptable ONLY for official group songs

⚠️ **AGENCY/LABEL NAMES:**
- "Hololive", "Nijisanji", "VShojo" are agencies, NOT artists
- Use agency name ONLY for official group songs (e.g., "Shiny Smily Story")
- For individual VTuber songs, use the VTuber's name, NOT the agency

**TAGS (select all that apply):**
- "cover": Song is a cover of another artist's work
- "vocaloid": Features Vocaloid/synthesized vocals (Hatsune Miku, GUMI, etc.) OR original Vocaloid song
- "utaite": Human cover singer (歌い手)
- "otomad": Otomad/音MAD (音楽MAD, music mashup/remix)
- "remix": Official or unofficial remix
- "instrumental": No vocals
- "live": Live performance recording
- "acoustic": Acoustic version
- "nightcore": Nightcore/sped-up version
- "karaoke": Karaoke stream/performance

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
✓ Artist is unclear but inferable
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
- バルーン → "BALLOON"
- 星街すいせい → "Hoshimachi Suisei"
- 白上フブキ → "Shirakami Fubuki"

**COMPLETE EXAMPLES:**

Example 1 - VTuber Cover of English Song (CRITICAL EXAMPLE):
Input: "Fly Me To The Moon (Cover) - Gawr Gura"
Channel: "Gawr Gura Ch. hololive-EN"
Output:
{
    "title": "Fly Me to the Moon",
    "artist": "Frank Sinatra",
    "cover_artist": "Gawr Gura",
    "tags": ["cover"],
    "confidence": 0.85
}
Reasoning: Gawr Gura is the COVER artist (VTuber). Frank Sinatra is the ORIGINAL artist. artist=original, cover_artist=performer.

Example 2 - VTuber Cover of Vocaloid Song (CRITICAL EXAMPLE):
Input: "King - Kanaria (Cover) | Mori Calliope"
Channel: "Mori Calliope Ch. hololive-EN"
Output:
{
    "title": "King",
    "artist": "Kanaria",
    "cover_artist": "Mori Calliope",
    "tags": ["cover"],
    "confidence": 0.90
}
Reasoning: Kanaria is the ORIGINAL Vocaloid producer. Mori Calliope is covering it. Very high confidence.

Example 3 - VTuber Original Song:
Input: "【MV】Reflect / Gawr Gura (Official)"
Channel: "Gawr Gura Ch. hololive-EN"
Output:
{
    "title": "Reflect",
    "artist": "Gawr Gura",
    "cover_artist": null,
    "tags": ["vocaloid"],
    "confidence": 0.95
}
Reasoning: This is Gawr Gura's ORIGINAL song, so she IS the artist. cover_artist is null for originals.

Example 4 - VTuber Cover of Japanese Song with Romanization:
Input: "【歌ってみた】シャルル / バルーン covered by 森カリオペ"
Channel: "Mori Calliope Ch. hololive-EN"
Output:
{
    "title": "Charles",
    "artist": "BALLOON",
    "cover_artist": "Mori Calliope",
    "tags": ["cover", "utaite"],
    "confidence": 0.85
}
Reasoning: "バルーン" (Balloon) is the original artist → "BALLOON". Mori Calliope is the cover artist.

Example 5 - VTuber Karaoke with Known Song:
Input: "【KARAOKE】Unravel / 白上フブキ 【ホロライブ】"
Channel: "Shirakami Fubuki Ch."
Output:
{
    "title": "Unravel",
    "artist": "TK from Ling tosite sigure",
    "cover_artist": "Shirakami Fubuki",
    "tags": ["cover", "karaoke"],
    "confidence": 0.85
}
Reasoning: "Unravel" is by TK. Shirakami Fubuki is just performing it. Extract original artist.

Example 6 - VTuber Collab Original Song:
Input: "【星街すいせい×森カリオペ】Shinigami Note / Suisei × Calliope"
Channel: "Hololive Official"
Output:
{
    "title": "Shinigami Note",
    "artist": "Hoshimachi Suisei",
    "cover_artist": null,
    "tags": [],
    "confidence": 0.85
}
Reasoning: Original collab song. Pick primary artist (first listed). cover_artist=null for originals.

Example 7 - Nijisanji VTuber Cover of Vocaloid Song:
Input: "【にじさんじ】神っぽいな / 葛葉 【cover】"
Channel: "Kuzuha Channel"
Output:
{
    "title": "Kamippoi na",
    "artist": "PinocchioP",
    "cover_artist": "Kuzuha",
    "tags": ["cover"],
    "confidence": 0.85
}
Reasoning: "神っぽいな" is by PinocchioP. 葛葉 (Kuzuha) is the cover artist.

Example 8 - Well-known Vocaloid Song Cover:
Input: "天ノ弱 歌ってみた"
Channel: "さくらみこ/Sakura Miko"
Output:
{
    "title": "Amanojaku",
    "artist": "164",
    "cover_artist": "Sakura Miko",
    "tags": ["cover", "utaite"],
    "confidence": 0.78
}
Reasoning: "天ノ弱" is by producer "164". Sakura Miko is the cover artist.

Example 9 - Hololive Group Song:
Input: "【hololive IDOL PROJECT】Shiny Smily Story【Original MV】"
Channel: "hololive ホロライブ - VTuber Group"
Output:
{
    "title": "Shiny Smily Story",
    "artist": "Hololive",
    "cover_artist": null,
    "tags": [],
    "confidence": 0.88
}
Reasoning: Official Hololive group original song. Agency name is the artist. cover_artist=null.

Example 10 - Vocaloid Original:
Input: "【DECO*27】ヴァンパイア feat.初音ミク【MV】"
Output:
{
    "title": "Vampire feat. Hatsune Miku",
    "artist": "DECO*27",
    "cover_artist": null,
    "tags": ["vocaloid"],
    "confidence": 0.91
}
Reasoning: Original Vocaloid song by DECO*27. Not a cover, so cover_artist=null.

Example 11 - Fan Upload of VTuber Cover:
Input: "[Hololive] Gura Sings Ride on Time 【Gawr Gura】"
Channel: "Hololive Sings"
Output:
{
    "title": "Ride on Time",
    "artist": "Tatsuro Yamashita",
    "cover_artist": "Gawr Gura",
    "tags": ["cover"],
    "confidence": 0.75
}
Reasoning: Classic city pop song by Tatsuro Yamashita. Gura is the cover artist.

Example 12 - Clear Japanese Cover:
Input: "【カバー】夜に駆ける / YOASOBI を歌ってみた【Channel Name】"
Output:
{
    "title": "Yoru ni Kakeru",
    "artist": "YOASOBI",
    "cover_artist": "Channel Name",
    "tags": ["cover"],
    "confidence": 0.88
}
Reasoning: YOASOBI is the original artist. Channel Name is covering it.

Example 13 - Unclear Singing Stream:
Input: "【歌枠切り抜き】素敵な曲を歌う白上フブキ"
Channel: "Fubuki Clips"
Output:
{
    "title": "Suteki na Kyoku wo Utau",
    "artist": "Unknown Artist",
    "cover_artist": "Shirakami Fubuki",
    "tags": ["cover"],
    "confidence": 0.45
}
Reasoning: Very vague title, cannot identify song or original artist. Use "Unknown Artist". cover_artist is the VTuber.

**IMPORTANT REMINDERS:**
- ⚠️ FOR COVERS: "artist" = ORIGINAL creator, "cover_artist" = performer (VTuber/utaite)
- ⚠️ FOR ORIGINALS: "cover_artist" = null
- ⚠️ ALWAYS romanize Japanese artist names: "バルーン" → "BALLOON", "星街すいせい" → "Hoshimachi Suisei"
- ⚠️ AGENCY NAMES: Only use for official group songs, not individual VTubers
- Always output valid JSON
- Include all five fields: title, artist, cover_artist, tags, confidence
- tags must be an array, even if empty: []
- confidence must be between 0.0 and 1.0
- BE CONSERVATIVE with confidence - most responses should be 0.60-0.85
- High confidence (>0.90) should be RARE and only for very clear cases
- Do not add any text outside the JSON structure
"""


def build_user_prompt_v4(
    raw_title: str,
    uploader: str = "",
    description: str = ""
) -> str:
    """
    Build a user prompt for title cleaning (Version 4 - with cover_artist).

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

    if description:
        # Truncate description to avoid context overflow
        desc_preview = description[:200] + "..." if len(description) > 200 else description
        prompt_parts.append(f"Description: {desc_preview}")

    prompt_parts.extend([
        "",
        "CRITICAL REMINDERS:",
        "- \"artist\" = ORIGINAL creator/composer of the song",
        "- \"cover_artist\" = performer in this video (often the Channel/Uploader above)",
        "- For COVERS: artist and cover_artist are DIFFERENT people",
        "- For ORIGINALS: set cover_artist to null",
        "- ALWAYS romanize Japanese artist names to English characters",
        "- Be CONSERVATIVE with confidence scores (most should be 0.60-0.85)",
        "",
        "Respond with clean metadata in JSON format as specified in the system prompt."
    ])

    return "\n".join(prompt_parts)


def build_regeneration_prompt_v4(
    raw_title: str,
    uploader: str,
    previous_attempt: Dict[str, any],
    feedback: str
) -> str:
    """
    Build a prompt for regenerating with user feedback (Version 4).

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
{format_metadata_display_v4(previous_attempt)}

User feedback: {feedback}

Please generate improved metadata in JSON format, addressing the feedback while following all the system rules.

CRITICAL REMINDERS:
- "artist" = ORIGINAL creator/composer, NOT the cover artist
- "cover_artist" = performer (VTuber/utaite), or null for originals
- ALWAYS romanize Japanese artist names to English characters
- Be CONSERVATIVE with confidence scores
"""
    return prompt


def format_metadata_display_v4(metadata: Dict[str, any]) -> str:
    """
    Format metadata dict for human-readable display (Version 4).

    Args:
        metadata: Dict containing title, artist, cover_artist, tags, confidence

    Returns:
        Formatted string representation
    """
    tags_str = ", ".join(metadata.get('tags', []))
    confidence = metadata.get('confidence', 0.0)
    cover_artist = metadata.get('cover_artist', None)

    lines = [
        f"- Title: {metadata.get('title', 'N/A')}",
        f"- Artist: {metadata.get('artist', 'N/A')}",
    ]
    if cover_artist:
        lines.append(f"- Cover Artist: {cover_artist}")
    lines.extend([
        f"- Tags: {tags_str or 'none'}",
        f"- Confidence: {confidence:.1%}",
    ])
    return "\n".join(lines)


def validate_response_v4(response: Dict[str, any]) -> bool:
    """
    Validate that an AI response has all required fields (Version 4).

    cover_artist is optional (can be null/missing).

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

    # Validate cover_artist type if present (string or None)
    if 'cover_artist' in response and response['cover_artist'] is not None:
        if not isinstance(response['cover_artist'], str):
            return False

    # Validate ranges
    if not (0.0 <= response['confidence'] <= 1.0):
        return False

    # Check for empty required fields
    if not response['title'].strip():
        return False

    return True


def normalize_response_v4(response: Dict[str, any]) -> Dict[str, any]:
    """
    Normalize and clean an AI response (Version 4).

    Args:
        response: The raw response from the model

    Returns:
        Normalized response dict with cover_artist field
    """
    normalized = {
        'title': response.get('title', '').strip(),
        'artist': response.get('artist', 'Unknown Artist').strip(),
        'cover_artist': None,
        'tags': response.get('tags', []),
        'confidence': float(response.get('confidence', 0.6))
    }

    # Extract and clean cover_artist
    cover_artist = response.get('cover_artist')
    if cover_artist and isinstance(cover_artist, str) and cover_artist.strip():
        normalized['cover_artist'] = cover_artist.strip()

    # Ensure tags is a list
    if not isinstance(normalized['tags'], list):
        normalized['tags'] = []

    # Remove duplicates and standardize tags
    valid_tags = {
        'cover', 'vocaloid', 'utaite', 'otomad', 'remix',
        'instrumental', 'live', 'acoustic', 'nightcore', 'karaoke'
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

    # Auto-add "cover" tag if cover_artist is present
    if normalized['cover_artist'] and 'cover' not in normalized['tags']:
        normalized['tags'].insert(0, 'cover')

    # Clamp confidence to valid range
    normalized['confidence'] = max(0.0, min(1.0, normalized['confidence']))

    # Default artist if empty
    if not normalized['artist'] or normalized['artist'].lower() == 'unknown':
        normalized['artist'] = 'Unknown Artist'

    return normalized
