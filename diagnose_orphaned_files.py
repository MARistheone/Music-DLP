"""
Diagnose Orphaned Files

This script helps diagnose why orphaned files might not be getting deleted.
It shows detailed information about orphaned videos and their file paths.

Usage:
    python diagnose_orphaned_files.py
"""

from core.database import Database
from core.logger import setup_logger
from pathlib import Path
import os


def main():
    logger = setup_logger('diagnose', level='INFO')
    db = Database()

    print("=" * 80)
    print("ORPHANED VIDEO DIAGNOSTICS")
    print("=" * 80)
    print()

    # Get orphaned videos
    orphaned = db.get_orphaned_videos()

    if not orphaned:
        print("✅ No orphaned videos found in database!")
        db.close()
        return

    print(f"Found {len(orphaned)} orphaned video(s) in database:\n")

    # Analyze each orphaned video
    total_files_found = 0
    total_files_missing = 0

    for idx, video in enumerate(orphaned, 1):
        video_id = video['video_id']
        print(f"\n{'='*80}")
        print(f"ORPHANED VIDEO #{idx}")
        print(f"{'='*80}")
        print(f"Title: {video['title']}")
        print(f"Video ID: {video_id}")
        print(f"Download Status: {video['download_status']}")
        print(f"Extraction Date: {video['extraction_date']}")
        print()

        files_found = []
        files_missing = []

        # Check raw file
        if video.get('file_path_raw'):
            raw_path = Path(video['file_path_raw'])
            print(f"📁 Raw File Path (from DB): {raw_path}")

            # Try absolute path
            if raw_path.exists():
                files_found.append(('Raw file', raw_path, raw_path.stat().st_size))
                print(f"   ✅ EXISTS - Size: {raw_path.stat().st_size:,} bytes")
            else:
                files_missing.append(('Raw file', raw_path))
                print(f"   ❌ NOT FOUND at this path")

                # Try relative to current directory
                rel_path = Path.cwd() / raw_path
                if rel_path.exists():
                    print(f"   ✅ But found at: {rel_path}")
                    files_found.append(('Raw file (relative)', rel_path, rel_path.stat().st_size))
        else:
            print("📁 Raw File Path: (not set in database)")

        # Check approved metadata and converted files
        metadata = db.get_approved_metadata(video_id)
        if metadata:
            print(f"\n📋 Approved Metadata Found:")
            print(f"   Title: {metadata.get('final_title', 'N/A')}")
            print(f"   Artist: {metadata.get('final_artist', 'N/A')}")
            print(f"   Conversion Status: {metadata.get('conversion_status', 'N/A')}")

            # Check MP3
            if metadata.get('file_path_mp3'):
                mp3_path = Path(metadata['file_path_mp3'])
                print(f"\n📁 MP3 File Path (from DB): {mp3_path}")
                if mp3_path.exists():
                    files_found.append(('MP3 file', mp3_path, mp3_path.stat().st_size))
                    print(f"   ✅ EXISTS - Size: {mp3_path.stat().st_size:,} bytes")
                else:
                    files_missing.append(('MP3 file', mp3_path))
                    print(f"   ❌ NOT FOUND at this path")
                    rel_path = Path.cwd() / mp3_path
                    if rel_path.exists():
                        print(f"   ✅ But found at: {rel_path}")
                        files_found.append(('MP3 file (relative)', rel_path, rel_path.stat().st_size))

            # Check M4A
            if metadata.get('file_path_m4a'):
                m4a_path = Path(metadata['file_path_m4a'])
                print(f"\n📁 M4A File Path (from DB): {m4a_path}")
                if m4a_path.exists():
                    files_found.append(('M4A file', m4a_path, m4a_path.stat().st_size))
                    print(f"   ✅ EXISTS - Size: {m4a_path.stat().st_size:,} bytes")
                else:
                    files_missing.append(('M4A file', m4a_path))
                    print(f"   ❌ NOT FOUND at this path")
                    rel_path = Path.cwd() / m4a_path
                    if rel_path.exists():
                        print(f"   ✅ But found at: {rel_path}")
                        files_found.append(('M4A file (relative)', rel_path, rel_path.stat().st_size))

            # Check thumbnail
            if metadata.get('thumbnail_path'):
                thumb_path = Path(metadata['thumbnail_path'])
                print(f"\n📁 Thumbnail Path (from DB): {thumb_path}")
                if thumb_path.exists():
                    files_found.append(('Thumbnail', thumb_path, thumb_path.stat().st_size))
                    print(f"   ✅ EXISTS - Size: {thumb_path.stat().st_size:,} bytes")
                else:
                    files_missing.append(('Thumbnail', thumb_path))
                    print(f"   ❌ NOT FOUND at this path")
                    rel_path = Path.cwd() / thumb_path
                    if rel_path.exists():
                        print(f"   ✅ But found at: {rel_path}")
                        files_found.append(('Thumbnail (relative)', rel_path, rel_path.stat().st_size))
        else:
            print(f"\n📋 No Approved Metadata")

        # Summary for this video
        print(f"\n📊 File Summary for {video_id}:")
        print(f"   Files found: {len(files_found)}")
        print(f"   Files missing: {len(files_missing)}")

        total_files_found += len(files_found)
        total_files_missing += len(files_missing)

        if files_found:
            total_size = sum(size for _, _, size in files_found)
            print(f"   Total size: {total_size:,} bytes ({total_size / (1024*1024):.2f} MB)")

    # Overall summary
    print(f"\n{'='*80}")
    print("OVERALL SUMMARY")
    print(f"{'='*80}")
    print(f"Orphaned videos in database: {len(orphaned)}")
    print(f"Total files found on disk: {total_files_found}")
    print(f"Total files missing: {total_files_missing}")
    print()

    # Check common directories
    print("📂 Checking common directories:")
    dirs_to_check = [
        Path('downloads/raw'),
        Path('downloads/final'),
        Path.cwd() / 'downloads' / 'raw',
        Path.cwd() / 'downloads' / 'final',
    ]

    for dir_path in dirs_to_check:
        if dir_path.exists():
            files = list(dir_path.glob('*'))
            print(f"   ✅ {dir_path}: {len(files)} files")
        else:
            print(f"   ❌ {dir_path}: does not exist")

    db.close()

    print(f"\n{'='*80}")
    print("💡 RECOMMENDATION:")
    print(f"{'='*80}")
    if total_files_found > 0:
        print("Files were found! The paths in the database might be relative.")
        print("You may need to manually delete files from:")
        print("  - downloads/raw/")
        print("  - downloads/final/")
        print("\nOr run the cleanup script from the project root directory.")
    else:
        print("No files were found. They may have already been deleted,")
        print("or the database paths don't match the actual file locations.")


if __name__ == '__main__':
    main()
