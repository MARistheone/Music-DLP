"""
Music DLP - Phase 2 Test Script

Test the download system implementation:
1. Database initialization
2. Metadata extraction from playlist/video
3. Audio download with bot avoidance
4. Thumbnail processing

Usage:
    python test_phase2.py --test-extract <playlist_url>
    python test_phase2.py --test-download <video_id>
    python test_phase2.py --test-thumbnail <thumbnail_url>
    python test_phase2.py --test-all
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.database import Database
from core.config_manager import ConfigManager
from core.logger import setup_logger
from downloaders.yt_dlp_manager import YTDLPManager, validate_cookies_file
from downloaders.metadata_extractor import MetadataExtractor, validate_youtube_url
from downloaders.thumbnail_processor import ThumbnailProcessor


def test_database():
    """Test database initialization"""
    print("\n" + "=" * 60)
    print("TEST 1: Database Initialization")
    print("=" * 60)

    try:
        db = Database()
        print(f"✓ Database initialized: {db.db_path}")

        # Check tables exist
        tables = db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()

        table_names = [t[0] for t in tables]
        expected_tables = [
            'playlists', 'videos', 'playlist_videos',
            'ai_title_attempts', 'approved_metadata', 'app_config'
        ]

        print(f"✓ Tables found: {', '.join(table_names)}")

        for table in expected_tables:
            if table not in table_names:
                print(f"✗ Missing table: {table}")
                return False

        print("✓ All tables present")
        db.close()
        return True

    except Exception as e:
        print(f"✗ Database test failed: {str(e)}")
        return False


def test_config():
    """Test configuration manager"""
    print("\n" + "=" * 60)
    print("TEST 2: Configuration Manager")
    print("=" * 60)

    try:
        db = Database()
        config = ConfigManager(db=db)

        print(f"✓ Config loaded from: {config.config_file}")
        print(f"  - Theme mode: {config.theme_mode}")
        print(f"  - Download format: {config.download_format}")
        print(f"  - AI models: {config.ai_models}")
        print(f"  - Cookies file: {config.cookies_file}")

        # Validate cookies if configured
        if config.cookies_file:
            if validate_cookies_file(config.cookies_file):
                print(f"✓ Cookies file is valid")
            else:
                print(f"⚠ Cookies file not found or invalid: {config.cookies_file}")
                print("  Note: You need to export cookies from your browser")
                print("  Use 'Get cookies.txt LOCALLY' extension")

        db.close()
        return True

    except Exception as e:
        print(f"✗ Config test failed: {str(e)}")
        return False


def test_extract_playlist(playlist_url: str):
    """Test playlist metadata extraction"""
    print("\n" + "=" * 60)
    print("TEST 3: Playlist Metadata Extraction")
    print("=" * 60)

    # Validate URL
    is_valid, url_type = validate_youtube_url(playlist_url)
    if not is_valid:
        print(f"✗ Invalid YouTube URL: {playlist_url}")
        return False

    print(f"✓ Valid {url_type} URL: {playlist_url}")

    try:
        db = Database()
        config = ConfigManager(db=db)
        logger = setup_logger('test_extract')

        extractor = MetadataExtractor(
            database=db,
            cookies_file=config.cookies_file,
            logger=logger
        )

        print(f"Extracting metadata (this may take a moment)...")

        if url_type == 'playlist':
            success, error, data = extractor.extract_playlist(
                playlist_url,
                store_in_db=True
            )
        else:
            success, error, data = extractor.extract_single_video(
                playlist_url,
                store_in_db=True
            )

        if success:
            if url_type == 'playlist':
                print(f"✓ Playlist extracted successfully:")
                print(f"  - Title: {data['title']}")
                print(f"  - Uploader: {data['uploader']}")
                print(f"  - Videos: {data['video_count']}")
                print(f"\nFirst 3 videos:")
                for i, video in enumerate(data['videos'][:3], 1):
                    print(f"  {i}. {video['title']} ({video['duration']}s)")
            else:
                print(f"✓ Video extracted successfully:")
                print(f"  - Title: {data['title']}")
                print(f"  - Uploader: {data['uploader']}")
                print(f"  - Duration: {data['duration']}s")
                print(f"  - Video ID: {data['video_id']}")

            print(f"✓ Data stored in database")

            # Verify database storage
            if url_type == 'playlist':
                playlist = db.get_playlist(data['playlist_id'])
                if playlist:
                    print(f"✓ Verified: Playlist found in database")
                    videos = db.get_playlist_videos(data['playlist_id'])
                    print(f"✓ Verified: {len(videos)} videos linked to playlist")
            else:
                video = db.get_video(data['video_id'])
                if video:
                    print(f"✓ Verified: Video found in database")

            db.close()
            return True
        else:
            print(f"✗ Extraction failed: {error}")
            db.close()
            return False

    except Exception as e:
        print(f"✗ Extract test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_download_video(video_id: str):
    """Test video download"""
    print("\n" + "=" * 60)
    print("TEST 4: Video Download")
    print("=" * 60)
    print(f"Video ID: {video_id}")
    print("Note: This will actually download the video!")

    try:
        db = Database()
        config = ConfigManager(db=db)
        logger = setup_logger('test_download')

        manager = YTDLPManager(
            cookies_file=config.cookies_file,
            sleep_interval=2,
            max_sleep_interval=5,
            logger=logger
        )

        output_dir = Path(config.raw_download_dir)
        print(f"Output directory: {output_dir}")

        print(f"Starting download (this may take a minute)...")
        success, error, info = manager.download_audio(
            video_id=video_id,
            output_dir=str(output_dir)
        )

        if success:
            print(f"✓ Download successful!")
            print(f"  - File: {Path(info['filename']).name}")
            print(f"  - Size: {info['filesize'] / 1024 / 1024:.2f}MB")
            print(f"  - Duration: {info['duration']}s")
            print(f"  - Format: {info['ext']}")

            # Update database
            db.update_video_download_status(
                video_id=video_id,
                status='downloaded',
                file_path=info['filename']
            )
            print(f"✓ Database updated with download status")

            # Show stats
            stats = manager.get_stats()
            print(f"\nDownload stats:")
            print(f"  - Attempted: {stats['downloads_attempted']}")
            print(f"  - Successful: {stats['downloads_successful']}")
            print(f"  - Failed: {stats['downloads_failed']}")
            print(f"  - Bot detections: {stats['bot_detections']}")

            db.close()
            return True
        else:
            print(f"✗ Download failed: {error}")
            db.close()
            return False

    except Exception as e:
        print(f"✗ Download test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_thumbnail(thumbnail_url: str):
    """Test thumbnail processing"""
    print("\n" + "=" * 60)
    print("TEST 5: Thumbnail Processing")
    print("=" * 60)
    print(f"Thumbnail URL: {thumbnail_url}")

    try:
        logger = setup_logger('test_thumbnail')
        processor = ThumbnailProcessor(logger=logger)

        output_dir = Path("downloads/raw/")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "test_thumbnail.jpg"

        print(f"Output path: {output_path}")
        print(f"Processing thumbnail...")

        success, error = processor.download_and_process(
            thumbnail_url=thumbnail_url,
            output_path=str(output_path),
            size=(300, 300)
        )

        if success:
            print(f"✓ Thumbnail processed successfully!")
            print(f"  - Size: {output_path.stat().st_size / 1024:.1f}KB")
            print(f"  - Format: JPEG, 300x300px")
            print(f"  - Location: {output_path}")
            return True
        else:
            print(f"✗ Thumbnail processing failed: {error}")
            return False

    except Exception as e:
        print(f"✗ Thumbnail test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_all():
    """Run all basic tests"""
    print("\n" + "=" * 70)
    print(" MUSIC DLP - PHASE 2 TEST SUITE")
    print("=" * 70)

    results = []

    # Test 1: Database
    results.append(("Database", test_database()))

    # Test 2: Config
    results.append(("Config", test_config()))

    # Print summary
    print("\n" + "=" * 70)
    print(" TEST SUMMARY")
    print("=" * 70)

    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name:20} {status}")

    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ All tests passed! Phase 2 core components are working.")
        print("\nNext steps:")
        print("1. Export cookies from browser (Get cookies.txt LOCALLY extension)")
        print("2. Update config.ini with cookies file path")
        print("3. Test extraction: python test_phase2.py --test-extract <playlist_url>")
        print("4. Test download: python test_phase2.py --test-download <video_id>")
        return True
    else:
        print("\n✗ Some tests failed. Please check the errors above.")
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Test Music DLP Phase 2 implementation")
    parser.add_argument('--test-all', action='store_true', help='Run all basic tests')
    parser.add_argument('--test-extract', metavar='URL', help='Test metadata extraction from URL')
    parser.add_argument('--test-download', metavar='VIDEO_ID', help='Test video download')
    parser.add_argument('--test-thumbnail', metavar='URL', help='Test thumbnail processing')

    args = parser.parse_args()

    if args.test_all:
        success = test_all()
        sys.exit(0 if success else 1)

    elif args.test_extract:
        success = test_extract_playlist(args.test_extract)
        sys.exit(0 if success else 1)

    elif args.test_download:
        success = test_download_video(args.test_download)
        sys.exit(0 if success else 1)

    elif args.test_thumbnail:
        success = test_thumbnail(args.test_thumbnail)
        sys.exit(0 if success else 1)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
