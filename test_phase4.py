"""
Phase 4 Test Script - Conversion System

Comprehensive test suite for FFmpeg conversion and metadata embedding.

Tests:
- FFmpeg availability
- MP3 conversion
- M4A conversion
- Metadata embedding (ID3 and MP4 atoms)
- File validation
- Integration tests

Usage:
    python test_phase4.py --test-ffmpeg        # Check FFmpeg availability
    python test_phase4.py --test-mp3           # Test MP3 conversion
    python test_phase4.py --test-m4a           # Test M4A conversion
    python test_phase4.py --test-metadata      # Test metadata embedding
    python test_phase4.py --test-all           # Run all tests
    python test_phase4.py --integration        # Integration test with database
"""

import argparse
import sys
from pathlib import Path
import shutil
import tempfile
import json

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.logger import setup_logger
from core.database import Database
from core.config_manager import ConfigManager
from converters import FFmpegConverter, MetadataEmbedder


class Phase4Tester:
    """Test suite for Phase 4 conversion system."""

    def __init__(self):
        """Initialize tester with logger and components."""
        self.logger = setup_logger('test_phase4', level='INFO')
        self.db = Database()
        self.config = ConfigManager(db=self.db)

        self.converter = FFmpegConverter(
            mp3_bitrate=self.config.mp3_bitrate,
            m4a_bitrate=self.config.m4a_bitrate,
            normalize_audio=True,
            logger=self.logger
        )

        self.embedder = MetadataEmbedder(logger=self.logger)

        # Test data directory
        self.test_dir = project_root / 'test_data'
        self.test_dir.mkdir(exist_ok=True)

    def test_ffmpeg_availability(self) -> bool:
        """
        Test 1: Check if FFmpeg is installed and accessible.

        Returns:
            True if FFmpeg is available
        """
        self.logger.info("=" * 60)
        self.logger.info("TEST 1: FFmpeg Availability")
        self.logger.info("=" * 60)

        try:
            # Check FFmpeg
            if not shutil.which('ffmpeg'):
                self.logger.error("FFmpeg not found in PATH")
                self.logger.error("Please install FFmpeg:")
                self.logger.error("  Windows: https://ffmpeg.org/download.html#build-windows")
                self.logger.error("  macOS: brew install ffmpeg")
                self.logger.error("  Linux: sudo apt install ffmpeg")
                return False

            self.logger.info("[OK] FFmpeg found in PATH")

            # Check FFprobe
            if not shutil.which('ffprobe'):
                self.logger.error("FFprobe not found in PATH")
                return False

            self.logger.info("[OK] FFprobe found in PATH")

            # Get version info
            import subprocess
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                self.logger.info(f"[OK] {version_line}")

                # Check for libmp3lame support
                if 'libmp3lame' in result.stdout:
                    self.logger.info("[OK] libmp3lame encoder available")
                else:
                    self.logger.warning("⚠ libmp3lame not found in FFmpeg build")

                # Check for AAC support
                if 'aac' in result.stdout.lower():
                    self.logger.info("[OK] AAC encoder available")

            self.logger.info("\n[PASS] FFmpeg availability test PASSED\n")
            return True

        except Exception as e:
            self.logger.error(f"FFmpeg availability test failed: {str(e)}")
            return False

    def test_mp3_conversion(self) -> bool:
        """
        Test 2: Test MP3 conversion with sample audio.

        Returns:
            True if MP3 conversion works
        """
        self.logger.info("=" * 60)
        self.logger.info("TEST 2: MP3 Conversion")
        self.logger.info("=" * 60)

        try:
            # Create test audio file (silence)
            test_input = self.test_dir / 'test_input.opus'
            test_output = self.test_dir / 'test_output.mp3'

            # Generate 3 seconds of silence as test file
            import subprocess
            result = subprocess.run(
                [
                    'ffmpeg', '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo',
                    '-t', '3', '-c:a', 'libopus', '-y', str(test_input)
                ],
                capture_output=True,
                timeout=10
            )

            if result.returncode != 0:
                self.logger.error("Failed to create test input file")
                return False

            self.logger.info(f"Created test input: {test_input.name} ({test_input.stat().st_size} bytes)")

            # Convert to MP3
            success, error = self.converter.convert_to_mp3(
                test_input,
                test_output
            )

            if not success:
                self.logger.error(f"MP3 conversion failed: {error}")
                return False

            self.logger.info(f"[OK] MP3 file created: {test_output.name} ({test_output.stat().st_size} bytes)")

            # Validate output
            is_valid, error = self.converter.validate_conversion(
                test_input,
                test_output,
                'mp3'
            )

            if not is_valid:
                self.logger.error(f"MP3 validation failed: {error}")
                return False

            self.logger.info("[OK] MP3 validation passed")

            # Get audio info
            info = self.converter.get_audio_info(test_output)
            if info:
                self.logger.info(f"  Codec: {info['codec']}")
                self.logger.info(f"  Bitrate: {int(info.get('bitrate', 0))} bps")
                self.logger.info(f"  Duration: {info['duration']:.2f}s")
                self.logger.info(f"  Channels: {info['channels']}")

            # Cleanup
            test_input.unlink()
            test_output.unlink()

            self.logger.info("\n[PASS] MP3 conversion test PASSED\n")
            return True

        except Exception as e:
            self.logger.error(f"MP3 conversion test failed: {str(e)}")
            return False

    def test_m4a_conversion(self) -> bool:
        """
        Test 3: Test M4A conversion with sample audio.

        Returns:
            True if M4A conversion works
        """
        self.logger.info("=" * 60)
        self.logger.info("TEST 3: M4A Conversion")
        self.logger.info("=" * 60)

        try:
            # Create test audio file (silence)
            test_input = self.test_dir / 'test_input.opus'
            test_output = self.test_dir / 'test_output.m4a'

            # Generate 3 seconds of silence as test file
            import subprocess
            result = subprocess.run(
                [
                    'ffmpeg', '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo',
                    '-t', '3', '-c:a', 'libopus', '-y', str(test_input)
                ],
                capture_output=True,
                timeout=10
            )

            if result.returncode != 0:
                self.logger.error("Failed to create test input file")
                return False

            self.logger.info(f"Created test input: {test_input.name} ({test_input.stat().st_size} bytes)")

            # Convert to M4A
            success, error = self.converter.convert_to_m4a(
                test_input,
                test_output
            )

            if not success:
                self.logger.error(f"M4A conversion failed: {error}")
                return False

            self.logger.info(f"[OK] M4A file created: {test_output.name} ({test_output.stat().st_size} bytes)")

            # Validate output
            is_valid, error = self.converter.validate_conversion(
                test_input,
                test_output,
                'aac'
            )

            if not is_valid:
                self.logger.error(f"M4A validation failed: {error}")
                return False

            self.logger.info("[OK] M4A validation passed")

            # Get audio info
            info = self.converter.get_audio_info(test_output)
            if info:
                self.logger.info(f"  Codec: {info['codec']}")
                self.logger.info(f"  Bitrate: {int(info.get('bitrate', 0))} bps")
                self.logger.info(f"  Duration: {info['duration']:.2f}s")
                self.logger.info(f"  Channels: {info['channels']}")

            # Cleanup
            test_input.unlink()
            test_output.unlink()

            self.logger.info("\n[PASS] M4A conversion test PASSED\n")
            return True

        except Exception as e:
            self.logger.error(f"M4A conversion test failed: {str(e)}")
            return False

    def test_metadata_embedding(self) -> bool:
        """
        Test 4: Test metadata embedding in both MP3 and M4A.

        Returns:
            True if metadata embedding works
        """
        self.logger.info("=" * 60)
        self.logger.info("TEST 4: Metadata Embedding")
        self.logger.info("=" * 60)

        try:
            # Create test audio files
            test_mp3 = self.test_dir / 'test_metadata.mp3'
            test_m4a = self.test_dir / 'test_metadata.m4a'
            test_thumbnail = self.test_dir / 'test_thumbnail.jpg'

            # Generate test audio (3 seconds of silence)
            import subprocess

            # Create MP3
            result = subprocess.run(
                [
                    'ffmpeg', '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo',
                    '-t', '3', '-c:a', 'libmp3lame', '-b:a', '320k', '-y', str(test_mp3)
                ],
                capture_output=True,
                timeout=10
            )

            if result.returncode != 0:
                self.logger.error("Failed to create test MP3 file")
                return False

            # Create M4A
            result = subprocess.run(
                [
                    'ffmpeg', '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo',
                    '-t', '3', '-c:a', 'aac', '-b:a', '320k', '-y', str(test_m4a)
                ],
                capture_output=True,
                timeout=10
            )

            if result.returncode != 0:
                self.logger.error("Failed to create test M4A file")
                return False

            # Create test thumbnail (300x300 blue square)
            from PIL import Image
            img = Image.new('RGB', (300, 300), color=(0, 100, 200))
            img.save(test_thumbnail, 'JPEG', quality=95)

            self.logger.info("Created test files:")
            self.logger.info(f"  MP3: {test_mp3.name}")
            self.logger.info(f"  M4A: {test_m4a.name}")
            self.logger.info(f"  Thumbnail: {test_thumbnail.name}")

            # Prepare metadata
            metadata = {
                'title': 'Test Song Title',
                'artist': 'Test Artist',
                'album': 'Test Album',
                'tags': ['test', 'cover', 'vocaloid']
            }

            # Embed MP3 metadata
            self.logger.info("\nEmbedding MP3 metadata...")
            success, error = self.embedder.embed_mp3_metadata(
                test_mp3,
                metadata,
                test_thumbnail
            )

            if not success:
                self.logger.error(f"MP3 metadata embedding failed: {error}")
                return False

            self.logger.info("[OK] MP3 metadata embedded")

            # Validate MP3 metadata
            is_valid, error = self.embedder.validate_mp3_metadata(
                test_mp3,
                metadata
            )

            if not is_valid:
                self.logger.error(f"MP3 metadata validation failed: {error}")
                return False

            self.logger.info("[OK] MP3 metadata validation passed")

            # Read MP3 metadata
            read_metadata = self.embedder.get_metadata(test_mp3)
            if read_metadata:
                self.logger.info("  Read metadata:")
                self.logger.info(f"    Title: {read_metadata['title']}")
                self.logger.info(f"    Artist: {read_metadata['artist']}")
                self.logger.info(f"    Album: {read_metadata['album']}")
                self.logger.info(f"    Has artwork: {read_metadata['has_artwork']}")

            # Embed M4A metadata
            self.logger.info("\nEmbedding M4A metadata...")
            success, error = self.embedder.embed_m4a_metadata(
                test_m4a,
                metadata,
                test_thumbnail
            )

            if not success:
                self.logger.error(f"M4A metadata embedding failed: {error}")
                return False

            self.logger.info("[OK] M4A metadata embedded")

            # Validate M4A metadata
            is_valid, error = self.embedder.validate_m4a_metadata(
                test_m4a,
                metadata
            )

            if not is_valid:
                self.logger.error(f"M4A metadata validation failed: {error}")
                return False

            self.logger.info("[OK] M4A metadata validation passed")

            # Read M4A metadata
            read_metadata = self.embedder.get_metadata(test_m4a)
            if read_metadata:
                self.logger.info("  Read metadata:")
                self.logger.info(f"    Title: {read_metadata['title']}")
                self.logger.info(f"    Artist: {read_metadata['artist']}")
                self.logger.info(f"    Album: {read_metadata['album']}")
                self.logger.info(f"    Has artwork: {read_metadata['has_artwork']}")

            # Cleanup
            test_mp3.unlink()
            test_m4a.unlink()
            test_thumbnail.unlink()

            self.logger.info("\n[PASS] Metadata embedding test PASSED\n")
            return True

        except Exception as e:
            self.logger.error(f"Metadata embedding test failed: {str(e)}")
            return False

    def test_integration(self) -> bool:
        """
        Test 5: Integration test with complete workflow.

        Tests the full conversion pipeline:
        1. Create test audio file
        2. Convert to both MP3 and M4A
        3. Embed metadata in both formats
        4. Validate both outputs

        Returns:
            True if integration test passes
        """
        self.logger.info("=" * 60)
        self.logger.info("TEST 5: Integration Test")
        self.logger.info("=" * 60)

        try:
            # Setup test files
            test_input = self.test_dir / 'integration_input.opus'
            test_mp3 = self.test_dir / 'Integration Test - Complete.mp3'
            test_m4a = self.test_dir / 'Integration Test - Complete.m4a'
            test_thumbnail = self.test_dir / 'integration_thumb.jpg'

            # Generate test audio (5 seconds)
            import subprocess
            self.logger.info("Creating test audio file...")
            result = subprocess.run(
                [
                    'ffmpeg', '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo',
                    '-t', '5', '-c:a', 'libopus', '-y', str(test_input)
                ],
                capture_output=True,
                timeout=10
            )

            if result.returncode != 0:
                self.logger.error("Failed to create test input file")
                return False

            # Create test thumbnail
            from PIL import Image
            img = Image.new('RGB', (300, 300), color=(50, 150, 50))
            img.save(test_thumbnail, 'JPEG', quality=95)

            self.logger.info(f"[OK] Test input created: {test_input.name}")

            # Convert to both formats
            self.logger.info("\nConverting to MP3 and M4A...")
            mp3_success, m4a_success, mp3_error, m4a_error = self.converter.convert_both_formats(
                test_input,
                test_mp3,
                test_m4a
            )

            if not mp3_success:
                self.logger.error(f"MP3 conversion failed: {mp3_error}")
                return False

            if not m4a_success:
                self.logger.error(f"M4A conversion failed: {m4a_error}")
                return False

            self.logger.info("[OK] Both conversions successful")

            # Prepare metadata
            metadata = {
                'title': 'Complete Integration Test',
                'artist': 'Music DLP Tester',
                'album': 'Phase 4 Tests',
                'tags': ['test', 'integration']
            }

            # Embed metadata in both
            self.logger.info("\nEmbedding metadata in both formats...")
            mp3_success, m4a_success, mp3_error, m4a_error = self.embedder.embed_both_formats(
                test_mp3,
                test_m4a,
                metadata,
                test_thumbnail
            )

            if not mp3_success:
                self.logger.error(f"MP3 metadata embedding failed: {mp3_error}")
                return False

            if not m4a_success:
                self.logger.error(f"M4A metadata embedding failed: {m4a_error}")
                return False

            self.logger.info("[OK] Metadata embedded in both formats")

            # Validate both files
            self.logger.info("\nValidating outputs...")

            mp3_valid, mp3_val_error = self.embedder.validate_mp3_metadata(test_mp3, metadata)
            if not mp3_valid:
                self.logger.error(f"MP3 validation failed: {mp3_val_error}")
                return False

            m4a_valid, m4a_val_error = self.embedder.validate_m4a_metadata(test_m4a, metadata)
            if not m4a_valid:
                self.logger.error(f"M4A validation failed: {m4a_val_error}")
                return False

            self.logger.info("[OK] Both files validated successfully")

            # Display final file info
            self.logger.info("\nFinal Output Files:")
            self.logger.info(f"  MP3: {test_mp3.name}")
            self.logger.info(f"    Size: {test_mp3.stat().st_size / 1024:.2f} KB")

            mp3_info = self.converter.get_audio_info(test_mp3)
            if mp3_info:
                self.logger.info(f"    Duration: {mp3_info['duration']:.2f}s")
                self.logger.info(f"    Bitrate: {int(mp3_info.get('bitrate', 0))} bps")

            self.logger.info(f"\n  M4A: {test_m4a.name}")
            self.logger.info(f"    Size: {test_m4a.stat().st_size / 1024:.2f} KB")

            m4a_info = self.converter.get_audio_info(test_m4a)
            if m4a_info:
                self.logger.info(f"    Duration: {m4a_info['duration']:.2f}s")
                self.logger.info(f"    Bitrate: {int(m4a_info.get('bitrate', 0))} bps")

            # Keep files for manual inspection
            self.logger.info(f"\nTest files saved in: {self.test_dir}")
            self.logger.info("  (You can manually play these files to verify quality)")

            self.logger.info("\n[PASS] Integration test PASSED\n")
            return True

        except Exception as e:
            self.logger.error(f"Integration test failed: {str(e)}")
            return False

    def run_all_tests(self) -> bool:
        """
        Run all Phase 4 tests.

        Returns:
            True if all tests pass
        """
        self.logger.info("Starting Phase 4 Comprehensive Test Suite\n")

        tests = [
            ("FFmpeg Availability", self.test_ffmpeg_availability),
            ("MP3 Conversion", self.test_mp3_conversion),
            ("M4A Conversion", self.test_m4a_conversion),
            ("Metadata Embedding", self.test_metadata_embedding),
            ("Integration Test", self.test_integration),
        ]

        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                self.logger.error(f"Test '{test_name}' crashed: {str(e)}")
                results.append((test_name, False))

        # Summary
        self.logger.info("=" * 60)
        self.logger.info("TEST SUMMARY")
        self.logger.info("=" * 60)

        for test_name, result in results:
            status = "PASS" if result else "FAIL"
            self.logger.info(f"{status}: {test_name}")

        passed = sum(1 for _, result in results if result)
        total = len(results)

        self.logger.info(f"\nResults: {passed}/{total} tests passed")

        if passed == total:
            self.logger.info("\nAll Phase 4 tests PASSED! Phase 4 is production-ready.")
            return True
        else:
            self.logger.error(f"\n{total - passed} test(s) failed. Please review errors above.")
            return False


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description='Phase 4 Test Suite - Conversion System')

    parser.add_argument('--test-ffmpeg', action='store_true', help='Test FFmpeg availability')
    parser.add_argument('--test-mp3', action='store_true', help='Test MP3 conversion')
    parser.add_argument('--test-m4a', action='store_true', help='Test M4A conversion')
    parser.add_argument('--test-metadata', action='store_true', help='Test metadata embedding')
    parser.add_argument('--integration', action='store_true', help='Run integration test')
    parser.add_argument('--test-all', action='store_true', help='Run all tests')

    args = parser.parse_args()

    # If no arguments, show help
    if not any(vars(args).values()):
        parser.print_help()
        sys.exit(0)

    # Initialize tester
    tester = Phase4Tester()

    # Run requested tests
    if args.test_all:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)

    if args.test_ffmpeg:
        success = tester.test_ffmpeg_availability()
        if not success:
            sys.exit(1)

    if args.test_mp3:
        success = tester.test_mp3_conversion()
        if not success:
            sys.exit(1)

    if args.test_m4a:
        success = tester.test_m4a_conversion()
        if not success:
            sys.exit(1)

    if args.test_metadata:
        success = tester.test_metadata_embedding()
        if not success:
            sys.exit(1)

    if args.integration:
        success = tester.test_integration()
        if not success:
            sys.exit(1)

    print("\n[PASS] All requested tests completed successfully!")


if __name__ == '__main__':
    main()
