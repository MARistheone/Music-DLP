"""
VTuber-specific test script for AI prompts - V3 ENHANCED VERSION

Tests how well the AI handles VTuber music titles with V3 prompts (VTuber-enhanced):
- VTuber character names (Gawr Gura, Mori Calliope, etc.)
- Agency branding (Hololive, Nijisanji)
- Mix of Japanese and English
- Original songs vs covers
- Collab songs (multiple VTubers)
- Fan uploads vs official channels

V3 improvements:
- Added VTuber-specific examples (12 new examples)
- Stronger emphasis on "ORIGINAL artist for covers"
- Better romanization guidance
- Added well-known Vocaloid producers
"""

import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from ai.ollama_client import OllamaClient
from ai.prompts_v3 import SYSTEM_PROMPT_V3, build_user_prompt_v3

# VTuber-specific test cases
VTUBER_TEST_CASES = [
    {
        "name": "VTuber Cover - Clear English",
        "title": "Fly Me To The Moon (Cover) - Gawr Gura",
        "uploader": "Gawr Gura Ch. hololive-EN",
        "expected_artist": "Bart Howard",  # Original composer (or Frank Sinatra if model knows it)
        "expected_confidence_range": (0.70, 0.85),
        "notes": "Clear cover, but original artist is classic song (tricky - accept various artists)"
    },
    {
        "name": "VTuber Original Song",
        "title": "【MV】Reflect / Gawr Gura (Official)",
        "uploader": "Gawr Gura Ch. hololive-EN",
        "expected_artist": "Gawr Gura",
        "expected_confidence_range": (0.88, 0.96),
        "notes": "Official original song by VTuber"
    },
    {
        "name": "VTuber Cover - Japanese Song",
        "title": "【歌ってみた】シャルル / バルーン covered by 森カリオペ",
        "uploader": "Mori Calliope Ch. hololive-EN",
        "expected_artist": "BALLOON",  # Original artist (バルーン)
        "expected_confidence_range": (0.80, 0.92),
        "notes": "Japanese song covered by EN VTuber, needs romanization"
    },
    {
        "name": "VTuber Cover - Messy Fan Upload",
        "title": "[Hololive] Gura Sings Ride on Time 【Gawr Gura】",
        "uploader": "Hololive Sings",
        "expected_artist": "Tatsuro Yamashita",  # Original artist
        "expected_confidence_range": (0.65, 0.82),
        "notes": "Fan upload, agency tag in title, classic city pop song"
    },
    {
        "name": "VTuber Collab Original",
        "title": "【星街すいせい×森カリオペ】Shinigami Note / Suisei × Calliope",
        "uploader": "Hololive Official",
        "expected_artist": "Hoshimachi Suisei",  # Primary artist (first listed)
        "expected_confidence_range": (0.82, 0.92),
        "notes": "Collab between two VTubers, pick primary artist"
    },
    {
        "name": "VTuber Cover - English Song",
        "title": "King - Kanaria (Cover) | Mori Calliope",
        "uploader": "Mori Calliope Ch. hololive-EN",
        "expected_artist": "Kanaria",
        "expected_confidence_range": (0.88, 0.96),
        "notes": "Clear format, well-known Vocaloid song covered by VTuber"
    },
    {
        "name": "VTuber Original - Full Japanese",
        "title": "【MV】可愛くてごめん (feat. かぴ) / HoneyWorks",
        "uploader": "Gawr Gura Ch. hololive-EN",
        "expected_artist": "HoneyWorks",
        "expected_confidence_range": (0.75, 0.88),
        "notes": "Feature artist, needs romanization: Kawaikute Gomen"
    },
    {
        "name": "VTuber Cover - Unclear Artist",
        "title": "【歌枠切り抜き】素敵な曲を歌う白上フブキ",
        "uploader": "Fubuki Clips",
        "expected_artist": "Unknown Artist",
        "expected_confidence_range": (0.30, 0.50),
        "notes": "Singing stream clip, vague title, low info - LOW confidence expected"
    },
    {
        "name": "VTuber Karaoke Stream",
        "title": "【KARAOKE】Unravel / 白上フブキ 【ホロライブ】",
        "uploader": "Shirakami Fubuki Ch.",
        "expected_artist": "TK from Ling tosite sigure",
        "expected_confidence_range": (0.75, 0.88),
        "notes": "Famous anime OP (Tokyo Ghoul), artist inferable from knowledge"
    },
    {
        "name": "VTuber Group Song",
        "title": "【hololive IDOL PROJECT】Shiny Smily Story【Original MV】",
        "uploader": "hololive ホロライブ - VTuber Group",
        "expected_artist": "Hololive",  # Group name acceptable
        "expected_confidence_range": (0.85, 0.94),
        "notes": "Group original song, agency as artist is acceptable"
    },
    {
        "name": "Nijisanji VTuber Cover",
        "title": "【にじさんじ】神っぽいな / 葛葉 【cover】",
        "uploader": "Kuzuha Channel",
        "expected_artist": "PinocchioP",  # Original producer
        "expected_confidence_range": (0.78, 0.90),
        "notes": "Nijisanji VTuber covering Vocaloid song"
    },
    {
        "name": "VTuber Cover - Multiple Interpretations",
        "title": "天ノ弱 歌ってみた",
        "uploader": "さくらみこ/Sakura Miko",
        "expected_artist": "164",  # Original Vocaloid producer
        "expected_confidence_range": (0.70, 0.85),
        "notes": "Well-known Vocaloid song, needs romanization: Amanojaku"
    },
    {
        "name": "VTuber Remix/Arrange",
        "title": "Suspect (Official Music Video) - Gawr Gura",
        "uploader": "Gawr Gura Ch. hololive-EN",
        "expected_artist": "Gawr Gura",
        "expected_confidence_range": (0.88, 0.96),
        "notes": "Official original song, very clear"
    },
    {
        "name": "VTuber Cover - Fan Animation",
        "title": "[Hololive/Eng Sub] Calli's Unravel is just too perfect",
        "uploader": "Some Fan Channel",
        "expected_artist": "TK from Ling tosite sigure",
        "expected_confidence_range": (0.65, 0.82),
        "notes": "Fan upload with commentary, original artist inferable"
    },
    {
        "name": "VTuber Orisong (Original Song)",
        "title": "【オリジナル曲】KING / 星街すいせい(official)【Music Video】",
        "uploader": "Suisei Channel",
        "expected_artist": "Hoshimachi Suisei",
        "expected_confidence_range": (0.88, 0.96),
        "notes": "Original song tag, very clear"
    }
]


def colorize(text: str, color: str) -> str:
    """Add color to terminal output."""
    colors = {
        'green': '\033[92m',
        'red': '\033[91m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'cyan': '\033[96m',
        'magenta': '\033[95m',
        'reset': '\033[0m'
    }
    return f"{colors.get(color, '')}{text}{colors['reset']}"


def test_vtuber_prompts(model_name: str = 'gemma3:12b', temperature: float = 0.5):
    """
    Test AI prompts with VTuber-specific test cases.

    Args:
        model_name: Ollama model to test with
        temperature: Temperature setting (0.5 recommended for V2)
    """
    print("=" * 80)
    print(colorize("VTUBER MUSIC - AI PROMPTS TEST SUITE", 'cyan'))
    print("=" * 80)
    print(f"\nModel: {model_name}")
    print(f"Temperature: {temperature}")
    print(f"Test Focus: VTuber songs and covers\n")
    print(colorize("VTuber music challenges:", 'cyan'))
    print("  • Character names vs original artists")
    print("  • Agency branding (Hololive, Nijisanji)")
    print("  • Mix of Japanese and English")
    print("  • Collab songs and group performances")
    print("  • Fan uploads vs official channels\n")

    # Initialize client with auto-unload
    client = OllamaClient(auto_unload=True)

    # Check if model is available
    if not client.is_available():
        print(colorize("✗ ERROR: Ollama is not running!", 'red'))
        print("\nPlease start Ollama and try again.")
        return

    if not client.model_exists(model_name):
        print(colorize(f"✗ ERROR: Model '{model_name}' not found!", 'red'))
        print("\nAvailable models:")
        for model in client.list_models():
            print(f"  - {model}")
        return

    # Track statistics
    stats = {
        'total': len(VTUBER_TEST_CASES),
        'passed': 0,
        'failed': 0,
        'confidence_in_range': 0,
        'artist_correct': 0,
        'artist_acceptable': 0,  # For cases with multiple valid answers
        'total_confidence': 0.0,
        'by_type': {
            'original': {'total': 0, 'correct': 0},
            'cover': {'total': 0, 'correct': 0},
            'collab': {'total': 0, 'correct': 0}
        }
    }

    # Run tests
    print(colorize("Running tests...", 'cyan'))
    print("-" * 80)

    for i, test in enumerate(VTUBER_TEST_CASES, 1):
        print(f"\n[Test {i}/{len(VTUBER_TEST_CASES)}] {colorize(test['name'], 'cyan')}")
        print(f"Title: {test['title'][:70]}{'...' if len(test['title']) > 70 else ''}")
        print(f"Channel: {test['uploader'][:50]}{'...' if len(test['uploader']) > 50 else ''}")
        print(f"Expected: {colorize(test['expected_artist'], 'blue')} | "
              f"Confidence: {test['expected_confidence_range'][0]:.2f}-{test['expected_confidence_range'][1]:.2f}")
        print(f"Note: {colorize(test['notes'], 'yellow')}")

        # Determine test type
        test_type = 'original' if 'Original' in test['name'] or 'Orisong' in test['name'] else \
                    'collab' if 'Collab' in test['name'] or 'Group' in test['name'] else 'cover'
        stats['by_type'][test_type]['total'] += 1

        # Build prompt
        user_prompt = build_user_prompt_v3(
            raw_title=test['title'],
            uploader=test['uploader']
        )

        # Generate title
        try:
            result = client.generate_title(
                model=model_name,
                system_prompt=SYSTEM_PROMPT_V3,
                user_prompt=user_prompt,
                temperature=temperature
            )

            if not result:
                print(colorize("✗ FAILED - No response from model", 'red'))
                stats['failed'] += 1
                continue

            # Display result
            print(f"Got:      {colorize(result['artist'], 'green')} | Confidence: {result['confidence']:.2f}")
            print(f"Title:    {result['title']}")
            print(f"Tags:     {', '.join(result['tags']) if result['tags'] else 'none'}")

            # Check artist match (with some flexibility for VTuber cases)
            artist_lower = result['artist'].lower()
            expected_lower = test['expected_artist'].lower()

            # Exact match
            artist_exact = artist_lower == expected_lower

            # Partial match (for cases like "Bart Howard" vs "Frank Sinatra" for Fly Me To The Moon)
            # or "Hololive" vs "Hoshimachi Suisei" for group songs
            artist_acceptable = False

            # Special cases for VTuber context
            if 'fly me to the moon' in test['title'].lower():
                # Accept Bart Howard, Frank Sinatra, or even Unknown Artist
                artist_acceptable = any(x in artist_lower for x in ['bart', 'frank', 'sinatra', 'howard', 'unknown'])
            elif 'group' in test['name'].lower():
                # For group songs, accept agency name or any member
                artist_acceptable = any(x in artist_lower for x in ['hololive', 'nijisanji', 'suisei', 'gura'])

            if artist_exact:
                print(colorize("✓ Artist correct (exact match)", 'green'))
                stats['artist_correct'] += 1
                stats['by_type'][test_type]['correct'] += 1
            elif artist_acceptable:
                print(colorize("≈ Artist acceptable (valid alternative)", 'yellow'))
                stats['artist_acceptable'] += 1
                stats['by_type'][test_type]['correct'] += 1
            else:
                print(colorize(f"✗ Artist mismatch (expected: {test['expected_artist']})", 'red'))

            # Check confidence range
            min_conf, max_conf = test['expected_confidence_range']
            in_range = min_conf <= result['confidence'] <= max_conf

            if in_range:
                print(colorize("✓ Confidence in expected range", 'green'))
                stats['confidence_in_range'] += 1
            else:
                if result['confidence'] > max_conf:
                    print(colorize(f"⚠ Confidence too HIGH ({result['confidence']:.2f} > {max_conf:.2f})", 'yellow'))
                else:
                    print(colorize(f"⚠ Confidence too LOW ({result['confidence']:.2f} < {min_conf:.2f})", 'yellow'))

            stats['passed'] += 1
            stats['total_confidence'] += result['confidence']

        except Exception as e:
            print(colorize(f"✗ ERROR: {e}", 'red'))
            stats['failed'] += 1

    # Print summary
    print("\n" + "=" * 80)
    print(colorize("TEST SUMMARY", 'cyan'))
    print("=" * 80)
    print(f"\nTotal tests: {stats['total']}")
    print(f"Passed: {colorize(str(stats['passed']), 'green')}")
    print(f"Failed: {colorize(str(stats['failed']), 'red')}")

    if stats['passed'] > 0:
        exact_accuracy = 100 * stats['artist_correct'] / stats['passed']
        total_accuracy = 100 * (stats['artist_correct'] + stats['artist_acceptable']) / stats['passed']

        print(f"\n{colorize('Artist Extraction:', 'cyan')}")
        print(f"  Exact matches: {stats['artist_correct']}/{stats['passed']} ({exact_accuracy:.1f}%)")
        print(f"  Acceptable: {stats['artist_acceptable']}/{stats['passed']}")
        print(f"  Total correct: {stats['artist_correct'] + stats['artist_acceptable']}/{stats['passed']} "
              f"({total_accuracy:.1f}%)")

        print(f"\n{colorize('By Song Type:', 'cyan')}")
        for song_type, type_stats in stats['by_type'].items():
            if type_stats['total'] > 0:
                type_accuracy = 100 * type_stats['correct'] / type_stats['total']
                print(f"  {song_type.capitalize()}: {type_stats['correct']}/{type_stats['total']} "
                      f"({type_accuracy:.1f}%)")

        print(f"\n{colorize('Confidence Calibration:', 'cyan')}")
        print(f"  In expected range: {stats['confidence_in_range']}/{stats['passed']} "
              f"({100*stats['confidence_in_range']/stats['passed']:.1f}%)")

        avg_conf = stats['total_confidence'] / stats['passed']
        print(f"  Average confidence: {avg_conf:.2f}")

        if avg_conf > 0.85:
            print(colorize("\n⚠ WARNING: Average confidence is high (>0.85)!", 'yellow'))
            print("Models may still be overconfident on VTuber content.")
            print("VTuber songs often have mixed languages and complex artist attribution.")
            print("Consider:")
            print("  - Lowering temperature to 0.4")
            print("  - Adding VTuber-specific examples to prompts")
        elif avg_conf < 0.55:
            print(colorize("\n⚠ WARNING: Average confidence is low (<0.55)!", 'yellow'))
            print("Models may be too conservative on VTuber content.")
        else:
            print(colorize("\n✓ Average confidence in good range (0.55-0.85)", 'green'))

        # VTuber-specific insights
        print(f"\n{colorize('VTuber-Specific Insights:', 'cyan')}")

        if total_accuracy < 60:
            print(colorize("  ⚠ Low artist accuracy (<60%) suggests:", 'yellow'))
            print("    • Model struggles with VTuber character names")
            print("    • Confusion between cover artist and original artist")
            print("    • Consider adding VTuber-specific training examples")
        elif total_accuracy > 80:
            print(colorize("  ✓ Good artist accuracy (>80%)!", 'green'))
            print("    • Model handles VTuber character names well")
            print("    • Successfully distinguishes cover from original artists")

        # Check if model is confusing VTuber names with original artists
        print("\n  Common VTuber pitfalls:")
        print("    • Covers: Extract ORIGINAL artist, not VTuber name")
        print("    • Collabs: Pick PRIMARY artist (usually first listed)")
        print("    • Agency tags: Hololive/Nijisanji are labels, not artists")
        print("    • Fan uploads: Look for original artist, not uploader")

    print("\n" + "=" * 80)
    print(colorize("\nVTuber Test Complete!", 'cyan'))
    print("\nNext steps:")
    print("1. Compare results with general test (test_prompts_v2.py)")
    print("2. If VTuber accuracy is lower, consider adding VTuber examples to prompts")
    print("3. If confidence scores vary significantly, VTuber content may need special handling")


if __name__ == "__main__":
    import argparse
    import sys
    import io

    # Fix Windows console encoding
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    parser = argparse.ArgumentParser(description='Test AI prompts with VTuber music')
    parser.add_argument('--model', default='gemma3:12b',
                        help='Ollama model to test with (default: gemma3:12b)')
    parser.add_argument('--temperature', type=float, default=0.5,
                        help='Temperature setting (default: 0.5)')

    args = parser.parse_args()

    # ASCII art for fun
    print(colorize("""
    ╔══════════════════════════════════════════╗
    ║    VTuber Music AI Test Suite          ║
    ║  Testing: Hololive, Nijisanji & more!   ║
    ╚══════════════════════════════════════════╝
    """, 'cyan'))

    test_vtuber_prompts(model_name=args.model, temperature=args.temperature)
