"""
Phase 3 Test Script - AI Processing System

This script tests the AI processing components:
- Ollama client connectivity
- Model availability checking
- Title generation with prompts
- Parallel processing with multiple models
- Database storage of AI attempts

Usage:
    python test_phase3.py --test-all              # Run all tests
    python test_phase3.py --test-ollama           # Test Ollama connection
    python test_phase3.py --test-models           # Test model availability
    python test_phase3.py --test-generation       # Test title generation
    python test_phase3.py --test-single VIDEO_ID  # Process one video
    python test_phase3.py --test-batch LIMIT      # Process batch of pending videos
    python test_phase3.py --stats                 # Show processing statistics
"""

import sys
import json
import logging
from pathlib import Path
from typing import List, Optional
import argparse

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from core.database import Database
from core.config_manager import ConfigManager
from core.logger import setup_logger
from ai.ollama_client import OllamaClient
from ai.prompts import (
    SYSTEM_PROMPT,
    build_user_prompt,
    validate_response,
    normalize_response,
    format_metadata_display
)
from ai.title_processor import TitleProcessor


# Test data
TEST_TITLES = [
    {
        'title': '【カバー】夜に駆ける / YOASOBI を歌ってみた【Channel Name】',
        'uploader': 'Cover Channel',
        'expected_title': 'Yoru ni Kakeru',
        'expected_artist': 'YOASOBI',
        'expected_tags': ['cover']
    },
    {
        'title': 'Racing Into The Night (YOASOBI Cover)',
        'uploader': 'English Cover Channel',
        'expected_title': 'Racing Into The Night',
        'expected_artist': 'YOASOBI',
        'expected_tags': ['cover']
    },
    {
        'title': '【初音ミク】千本桜【オリジナル曲】',
        'uploader': 'Vocaloid Producer',
        'expected_title': 'Senbonzakura',
        'expected_artist': 'Hatsune Miku',
        'expected_tags': ['vocaloid']
    },
    {
        'title': 'King - Kanaria feat. GUMI【歌ってみた】',
        'uploader': 'Utaite Channel',
        'expected_title': 'King',
        'expected_artist': 'Kanaria',
        'expected_tags': ['cover', 'vocaloid']
    },
]


def test_ollama_connection(client: OllamaClient) -> bool:
    """Test if Ollama is running and accessible."""
    print("=== Testing Ollama Connection ===")

    if client.is_available():
        print("✓ Ollama is running and accessible")
        return True
    else:
        print("✗ Ollama is not available")
        print("\nPlease ensure:")
        print("  1. Ollama is installed (download from ollama.com)")
        print("  2. Ollama service is running")
        print("  3. Default URL is http://localhost:11434")
        return False


def test_model_availability(client: OllamaClient, models: List[str]) -> bool:
    """Test if required models are available."""
    print("\n=== Testing Model Availability ===")

    all_models = client.list_models()
    print(f"Found {len(all_models)} installed models")

    all_available = True
    for model in models:
        exists = client.model_exists(model)
        status = "✓" if exists else "✗"
        print(f"{status} {model}")

        if not exists:
            all_available = False

    if not all_available:
        print("\nMissing models. Install with:")
        for model in models:
            if not client.model_exists(model):
                print(f"  ollama pull {model}")

    return all_available


def test_title_generation(client: OllamaClient, model: str) -> bool:
    """Test title generation with a single model."""
    print(f"\n=== Testing Title Generation with {model} ===")

    if not client.model_exists(model):
        print(f"✗ Model {model} not available")
        return False

    success_count = 0
    for i, test_case in enumerate(TEST_TITLES, 1):
        print(f"\nTest {i}/{len(TEST_TITLES)}:")
        print(f"  Input: {test_case['title']}")

        user_prompt = build_user_prompt(
            raw_title=test_case['title'],
            uploader=test_case['uploader']
        )

        result = client.generate_title(
            model=model,
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt
        )

        if result:
            # Validate and normalize
            if validate_response(result):
                normalized = normalize_response(result)
                print(f"  ✓ Title: {normalized['title']}")
                print(f"    Artist: {normalized['artist']}")
                print(f"    Tags: {', '.join(normalized['tags'])}")
                print(f"    Confidence: {normalized['confidence']:.1%}")
                success_count += 1
            else:
                print(f"  ✗ Invalid response format")
                print(f"    Got: {result}")
        else:
            print(f"  ✗ Generation failed")

    print(f"\nResults: {success_count}/{len(TEST_TITLES)} successful")
    return success_count == len(TEST_TITLES)


def test_single_video_processing(
    processor: TitleProcessor,
    video_id: str
) -> bool:
    """Test processing a single video with all models."""
    print(f"\n=== Testing Single Video Processing: {video_id} ===")

    # Get video from database
    video = processor.db.get_video(video_id)
    if not video:
        print(f"✗ Video {video_id} not found in database")
        print("\nTip: Download some videos first using test_phase2.py")
        return False

    print(f"Video: {video['title']}")
    print(f"Uploader: {video.get('uploader', 'Unknown')}")
    print()

    # Process with all models
    results = processor.process_single_video(
        video_id=video_id,
        raw_title=video['title'],
        uploader=video.get('uploader', ''),
        description=video.get('description', '')
    )

    # Display results
    print(f"Processed with {len(results)} models:")
    success_count = 0

    for result in results:
        if result.success:
            print(f"\n✓ {result.model_name}:")
            print(f"  Title: {result.title}")
            print(f"  Artist: {result.artist}")
            print(f"  Tags: {result.tags}")
            print(f"  Confidence: {result.confidence:.1%}")
            print(f"  Time: {result.processing_time:.2f}s")
            success_count += 1
        else:
            print(f"\n✗ {result.model_name}:")
            print(f"  Error: {result.error}")

    print(f"\nResults: {success_count}/{len(results)} successful")

    # Store results in database
    processor._store_results(results)
    print(f"✓ Results stored in database")

    return success_count > 0


def test_batch_processing(
    processor: TitleProcessor,
    limit: int = 3
) -> bool:
    """Test batch processing of multiple videos."""
    print(f"\n=== Testing Batch Processing (limit={limit}) ===")

    # Get pending videos
    pending_ids = processor._get_pending_video_ids()

    if not pending_ids:
        print("No pending videos found")
        print("\nTip: Download some videos first using test_phase2.py")
        return False

    # Limit to requested number
    video_ids = pending_ids[:limit]
    print(f"Processing {len(video_ids)} videos: {video_ids}")
    print()

    # Progress callback
    def progress(current, total, video_id):
        print(f"Progress: [{current}/{total}] Processing {video_id}...")

    # Process batch
    results = processor.process_batch(video_ids, progress_callback=progress)

    # Summary
    print(f"\n=== Batch Processing Results ===")
    total_attempts = 0
    successful_attempts = 0

    for video_id, video_results in results.items():
        success = sum(1 for r in video_results if r.success)
        total = len(video_results)
        total_attempts += total
        successful_attempts += success

        status = "✓" if success > 0 else "✗"
        print(f"{status} {video_id}: {success}/{total} models succeeded")

    print(f"\nOverall: {successful_attempts}/{total_attempts} attempts successful")
    return successful_attempts > 0


def show_statistics(processor: TitleProcessor) -> None:
    """Display processing statistics."""
    print("\n=== AI Processing Statistics ===")

    stats = processor.get_processing_stats()

    print(f"Total videos: {stats.get('total_videos', 0)}")
    print(f"Downloaded: {stats.get('downloaded_videos', 0)}")
    print(f"Processed: {stats.get('processed_videos', 0)}")
    print(f"Pending: {stats.get('pending_videos', 0)}")
    print(f"\nTotal AI attempts: {stats.get('total_attempts', 0)}")

    if stats.get('attempts_by_model'):
        print("\nAttempts by model:")
        for model, count in stats['attempts_by_model'].items():
            print(f"  - {model}: {count}")

    # Show some recent attempts
    print("\n=== Recent AI Attempts (last 5) ===")
    try:
        cursor = processor.db.conn.cursor()
        cursor.execute("""
            SELECT
                a.video_id,
                v.title as original_title,
                a.model_name,
                a.generated_title,
                a.artist,
                a.confidence,
                a.processing_time
            FROM ai_title_attempts a
            JOIN videos v ON a.video_id = v.video_id
            ORDER BY a.generation_date DESC
            LIMIT 5
        """)

        for row in cursor.fetchall():
            video_id, orig_title, model, gen_title, artist, conf, proc_time = row
            print(f"\nVideo: {video_id}")
            print(f"  Original: {orig_title[:60]}...")
            print(f"  {model}: {gen_title} by {artist}")
            print(f"  Confidence: {conf:.1%}, Time: {proc_time:.2f}s")

    except Exception as e:
        print(f"Error fetching recent attempts: {e}")


def main():
    """Main test script."""
    parser = argparse.ArgumentParser(
        description="Test Phase 3: AI Processing System"
    )
    parser.add_argument(
        '--test-all',
        action='store_true',
        help='Run all tests'
    )
    parser.add_argument(
        '--test-ollama',
        action='store_true',
        help='Test Ollama connection'
    )
    parser.add_argument(
        '--test-models',
        action='store_true',
        help='Test model availability'
    )
    parser.add_argument(
        '--test-generation',
        action='store_true',
        help='Test title generation'
    )
    parser.add_argument(
        '--test-single',
        type=str,
        metavar='VIDEO_ID',
        help='Process a single video'
    )
    parser.add_argument(
        '--test-batch',
        type=int,
        metavar='LIMIT',
        help='Process batch of pending videos (specify limit)'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show processing statistics'
    )

    args = parser.parse_args()

    # Set up logging
    logger = setup_logger('music_dlp', level='INFO')

    # Initialize components
    print("Initializing Music DLP components...")
    db = Database()
    config = ConfigManager(db=db)

    # Get models from config
    models = config.ai_models
    print(f"Configured models: {models}")

    # Initialize Ollama client
    client = OllamaClient(base_url=config.ollama_url)

    # Initialize processor
    processor = TitleProcessor(
        db=db,
        ollama_url=config.ollama_url,
        models=models,
        max_workers=config.ai_parallel_workers
    )

    # Run tests based on arguments
    if args.test_all:
        print("Running all tests...\n")
        test_ollama_connection(client)
        test_model_availability(client, models)
        if client.is_available() and models:
            test_title_generation(client, models[0])

    elif args.test_ollama:
        test_ollama_connection(client)

    elif args.test_models:
        test_model_availability(client, models)

    elif args.test_generation:
        if not client.is_available():
            print("✗ Ollama not available")
            return
        available_models = [m for m in models if client.model_exists(m)]
        if available_models:
            test_title_generation(client, available_models[0])
        else:
            print("✗ No models available")

    elif args.test_single:
        test_single_video_processing(processor, args.test_single)

    elif args.test_batch is not None:
        test_batch_processing(processor, args.test_batch)

    elif args.stats:
        show_statistics(processor)

    else:
        parser.print_help()

    # Cleanup
    db.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
