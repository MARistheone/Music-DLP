"""
Quick test script for V2 prompts.

Tests artist extraction and confidence calibration improvements.
Run this to see if V2 prompts perform better than V1.
"""

import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from ai.ollama_client import OllamaClient
from ai.prompts_v2 import SYSTEM_PROMPT_V2, build_user_prompt_v2

# Test cases covering different scenarios
TEST_CASES = [
    {
        "name": "Clear English Cover",
        "title": "Racing Into The Night (YOASOBI Cover)",
        "uploader": "RandomChannel",
        "expected_artist": "YOASOBI",
        "expected_confidence_range": (0.85, 0.95),
        "notes": "Clear English title, artist explicitly stated"
    },
    {
        "name": "Japanese Cover - Well Known",
        "title": "【カバー】夜に駆ける / YOASOBI を歌ってみた【Channel Name】",
        "uploader": "Channel Name",
        "expected_artist": "YOASOBI",
        "expected_confidence_range": (0.82, 0.92),
        "notes": "Well-known song, artist clearly stated, needs romanization"
    },
    {
        "name": "Unclear Artist - Must Use Knowledge",
        "title": "Gurenge (鬼滅の刃OP) 歌ってみた cover",
        "uploader": "SomeCoverChannel",
        "expected_artist": "LiSA",
        "expected_confidence_range": (0.65, 0.80),
        "notes": "Artist not in title, must infer from Demon Slayer OP knowledge"
    },
    {
        "name": "Unknown Song - Fallback to Channel",
        "title": "【歌ってみた】素敵な曲 - 誰か",
        "uploader": "RandomCoverChannel",
        "expected_artist": "Unknown Artist",
        "expected_confidence_range": (0.50, 0.70),
        "notes": "Unknown song, original artist unclear, should use fallback"
    },
    {
        "name": "Famous Vocaloid Original",
        "title": "【初音ミク】千本桜【オリジナル曲】",
        "uploader": "Official Channel",
        "expected_artist": "Hatsune Miku",
        "expected_confidence_range": (0.90, 0.98),
        "notes": "Famous Vocaloid song, very clear"
    },
    {
        "name": "Complex Vocaloid Cover",
        "title": "King - Kanaria feat. GUMI【歌ってみた】by SomeUtaite",
        "uploader": "SomeUtaite",
        "expected_artist": "Kanaria",
        "expected_confidence_range": (0.70, 0.85),
        "notes": "Original producer Kanaria, complex structure"
    },
    {
        "name": "Messy Otomad - Low Info",
        "title": "【音MAD】おもしろ動画集【超絶】wwwww",
        "uploader": "MADChannel",
        "expected_artist": "Unknown Artist",
        "expected_confidence_range": (0.30, 0.55),
        "notes": "Very messy, low information, should have LOW confidence"
    },
    {
        "name": "Ambiguous Title",
        "title": "新曲！！！【神曲】",
        "uploader": "MusicChannelXYZ",
        "expected_artist": "Unknown Artist",
        "expected_confidence_range": (0.25, 0.45),
        "notes": "Just means 'New Song', very vague, LOW confidence expected"
    },
    {
        "name": "Nightcore",
        "title": "Nightcore - Yoru ni Kakeru (YOASOBI) Sped Up",
        "uploader": "NightcoreChannel",
        "expected_artist": "YOASOBI",
        "expected_confidence_range": (0.75, 0.88),
        "notes": "Clear title and artist, modified version"
    },
    {
        "name": "Feature Artist in Title",
        "title": "【DECO*27】ヴァンパイア feat.初音ミク【MV】",
        "uploader": "Official DECO*27",
        "expected_artist": "DECO*27",
        "expected_confidence_range": (0.88, 0.96),
        "notes": "Producer clearly stated, well-known song"
    }
]


def colorize(text: str, color: str) -> str:
    """Add color to terminal output."""
    colors = {
        'green': '\033[92m',
        'red': '\033[91m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'reset': '\033[0m'
    }
    return f"{colors.get(color, '')}{text}{colors['reset']}"


def test_v2_prompts(model_name: str = 'gemma3:12b', temperature: float = 0.5):
    """
    Test V2 prompts with multiple test cases.

    Args:
        model_name: Ollama model to test with
        temperature: Temperature setting (0.5 recommended for V2)
    """
    print("=" * 80)
    print(colorize("AI PROMPTS V2 - TEST SUITE", 'blue'))
    print("=" * 80)
    print(f"\nModel: {model_name}")
    print(f"Temperature: {temperature}")
    print(f"Prompt Version: 2.0\n")

    # Initialize client with auto-unload enabled to prevent VRAM filling up
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
        'total': len(TEST_CASES),
        'passed': 0,
        'failed': 0,
        'confidence_in_range': 0,
        'artist_correct': 0,
        'total_confidence': 0.0
    }

    # Run tests
    print(colorize("Running tests...", 'blue'))
    print("-" * 80)

    for i, test in enumerate(TEST_CASES, 1):
        print(f"\n[Test {i}/{len(TEST_CASES)}] {colorize(test['name'], 'blue')}")
        print(f"Title: {test['title'][:70]}...")
        print(f"Channel: {test['uploader']}")
        print(f"Expected: {test['expected_artist']} | "
              f"Confidence: {test['expected_confidence_range'][0]:.2f}-{test['expected_confidence_range'][1]:.2f}")

        # Build prompt
        user_prompt = build_user_prompt_v2(
            raw_title=test['title'],
            uploader=test['uploader']
        )

        # Generate title
        try:
            result = client.generate_title(
                model=model_name,
                system_prompt=SYSTEM_PROMPT_V2,
                user_prompt=user_prompt,
                temperature=temperature
            )

            if not result:
                print(colorize("✗ FAILED - No response from model", 'red'))
                stats['failed'] += 1
                continue

            # Display result
            print(f"Got:      {result['artist']} | Confidence: {result['confidence']:.2f}")
            print(f"Title:    {result['title']}")
            print(f"Tags:     {', '.join(result['tags']) if result['tags'] else 'none'}")

            # Check artist match
            artist_correct = result['artist'].lower() == test['expected_artist'].lower()
            if artist_correct:
                print(colorize("✓ Artist correct", 'green'))
                stats['artist_correct'] += 1
            else:
                print(colorize(f"✗ Artist mismatch (expected: {test['expected_artist']})", 'yellow'))

            # Check confidence range
            min_conf, max_conf = test['expected_confidence_range']
            in_range = min_conf <= result['confidence'] <= max_conf

            if in_range:
                print(colorize("✓ Confidence in expected range", 'green'))
                stats['confidence_in_range'] += 1
            else:
                print(colorize(f"✗ Confidence out of range ({result['confidence']:.2f} not in {min_conf:.2f}-{max_conf:.2f})", 'yellow'))

            stats['passed'] += 1
            stats['total_confidence'] += result['confidence']

        except Exception as e:
            print(colorize(f"✗ ERROR: {e}", 'red'))
            stats['failed'] += 1

    # Print summary
    print("\n" + "=" * 80)
    print(colorize("TEST SUMMARY", 'blue'))
    print("=" * 80)
    print(f"\nTotal tests: {stats['total']}")
    print(f"Passed: {colorize(str(stats['passed']), 'green')}")
    print(f"Failed: {colorize(str(stats['failed']), 'red')}")
    print(f"\nArtist accuracy: {stats['artist_correct']}/{stats['passed']} "
          f"({100*stats['artist_correct']/stats['passed']:.1f}%)" if stats['passed'] > 0 else "N/A")
    print(f"Confidence accuracy: {stats['confidence_in_range']}/{stats['passed']} "
          f"({100*stats['confidence_in_range']/stats['passed']:.1f}%)" if stats['passed'] > 0 else "N/A")

    if stats['passed'] > 0:
        avg_conf = stats['total_confidence'] / stats['passed']
        print(f"Average confidence: {avg_conf:.2f}")

        if avg_conf > 0.85:
            print(colorize("\n⚠ WARNING: Average confidence is high (>0.85)!", 'yellow'))
            print("Models may still be overconfident. Consider:")
            print("  - Lowering temperature to 0.4")
            print("  - Adding more explicit low-confidence examples")
        elif avg_conf < 0.55:
            print(colorize("\n⚠ WARNING: Average confidence is low (<0.55)!", 'yellow'))
            print("Models may be too conservative. Consider:")
            print("  - Raising temperature to 0.6")
            print("  - Adjusting confidence criteria")
        else:
            print(colorize("\n✓ Average confidence in good range (0.55-0.85)", 'green'))

    print("\n" + "=" * 80)


def compare_with_v1(model_name: str = 'gemma3:12b'):
    """
    Compare V2 prompts with V1 (if available).

    This requires having the old prompts.py available as prompts_v1.py
    """
    try:
        from ai.prompts import SYSTEM_PROMPT as SYSTEM_PROMPT_V1
        from ai.prompts import build_user_prompt as build_user_prompt_v1

        print(colorize("\n=== V1 vs V2 COMPARISON ===", 'blue'))
        print("\nRunning same tests with V1 prompts for comparison...\n")

        # Run a few key tests with V1
        client = OllamaClient(auto_unload=True)
        test_case = TEST_CASES[2]  # "Unclear Artist" case

        print(f"Test case: {test_case['name']}")
        print(f"Title: {test_case['title']}\n")

        # V1 result
        user_prompt_v1 = build_user_prompt_v1(
            raw_title=test_case['title'],
            uploader=test_case['uploader']
        )
        result_v1 = client.generate_title(
            model=model_name,
            system_prompt=SYSTEM_PROMPT_V1,
            user_prompt=user_prompt_v1,
            temperature=0.7  # V1 used 0.7
        )

        # V2 result
        user_prompt_v2 = build_user_prompt_v2(
            raw_title=test_case['title'],
            uploader=test_case['uploader']
        )
        result_v2 = client.generate_title(
            model=model_name,
            system_prompt=SYSTEM_PROMPT_V2,
            user_prompt=user_prompt_v2,
            temperature=0.5  # V2 uses 0.5
        )

        print(f"V1: {result_v1['artist']} | Confidence: {result_v1['confidence']:.2f}")
        print(f"V2: {result_v2['artist']} | Confidence: {result_v2['confidence']:.2f}")
        print(f"Expected: {test_case['expected_artist']} | "
              f"Range: {test_case['expected_confidence_range'][0]:.2f}-{test_case['expected_confidence_range'][1]:.2f}")

    except ImportError:
        print(colorize("\n✗ Cannot compare with V1 (prompts.py not found)", 'yellow'))
        print("To enable comparison, save current prompts.py as prompts_v1.py")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Test V2 prompts for Music DLP')
    parser.add_argument('--model', default='gemma3:12b',
                        help='Ollama model to test with (default: gemma3:12b)')
    parser.add_argument('--temperature', type=float, default=0.5,
                        help='Temperature setting (default: 0.5)')
    parser.add_argument('--compare', action='store_true',
                        help='Compare with V1 prompts if available')

    args = parser.parse_args()

    # Run main tests
    test_v2_prompts(model_name=args.model, temperature=args.temperature)

    # Run comparison if requested
    if args.compare:
        compare_with_v1(model_name=args.model)

    print("\nTest complete!")
    print("\nNext steps:")
    print("1. Review the results above")
    print("2. If confidence scores look better, integrate V2 into title_processor.py")
    print("3. See AI_IMPROVEMENTS_V2.md for integration instructions")
