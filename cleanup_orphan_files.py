"""
Cleanup Orphan Files

This script deletes files from disk that don't have corresponding database entries.
Use this when you've deleted playlists/videos but the files are still on disk.

Usage:
    python cleanup_orphan_files.py
"""

from core.database import Database
from core.logger import setup_logger
from pathlib import Path
import re


def get_video_id_from_filename(filename: str) -> str:
    """Extract video ID from various filename patterns"""
    # Pattern 1: [VIDEO_ID].webm or [VIDEO_ID].ext
    match = re.search(r'\[([a-zA-Z0-9_-]{11})\]', filename)
    if match:
        return match.group(1)

    # Pattern 2: VIDEO_ID_thumb.jpg (thumbnails without brackets)
    match = re.search(r'^([a-zA-Z0-9_-]{11})_thumb\.jpg$', filename)
    if match:
        return match.group(1)

    return None


def main():
    logger = setup_logger('cleanup_files', level='INFO')
    db = Database()

    print("=" * 80)
    print("ORPHAN FILE CLEANUP")
    print("=" * 80)
    print()

    # Get all video IDs and file paths from database
    cursor = db.conn.cursor()
    cursor.execute("SELECT video_id FROM videos")
    valid_video_ids = {row['video_id'] for row in cursor.fetchall()}

    # Get all final output file paths from approved_metadata
    cursor.execute("SELECT file_path_mp3, file_path_m4a FROM approved_metadata")
    valid_final_files = set()
    for row in cursor.fetchall():
        if row['file_path_mp3']:
            valid_final_files.add(Path(row['file_path_mp3']).name)
        if row['file_path_m4a']:
            valid_final_files.add(Path(row['file_path_m4a']).name)

    print(f"📊 Found {len(valid_video_ids)} videos in database")
    print(f"📊 Found {len(valid_final_files)} final output files in database")
    print()

    # Directories to scan
    scan_dirs = [
        (Path('downloads/raw'), 'Raw downloads'),
        (Path('downloads/final'), 'Final outputs'),
    ]

    orphan_files = []
    total_files_scanned = 0

    # Scan each directory
    for dir_path, dir_name in scan_dirs:
        print(f"📂 Scanning {dir_name}: {dir_path}")

        if not dir_path.exists():
            print(f"   ⚠️  Directory does not exist, skipping")
            print()
            continue

        files = list(dir_path.glob('*'))
        total_files_scanned += len(files)
        print(f"   Found {len(files)} files")

        for file_path in files:
            if file_path.is_file():
                # For final output directory, check against approved_metadata file paths
                if dir_path.name == 'final':
                    if file_path.name not in valid_final_files:
                        orphan_files.append((file_path, 'N/A', file_path.stat().st_size))
                        print(f"   🗑️  Orphan: {file_path.name} (not in database)")
                    else:
                        print(f"   ✅  Valid: {file_path.name}")
                else:
                    # For raw directory, extract video ID from filename
                    video_id = get_video_id_from_filename(file_path.name)

                    if video_id:
                        # Check if this video ID exists in database
                        if video_id not in valid_video_ids:
                            orphan_files.append((file_path, video_id, file_path.stat().st_size))
                            print(f"   🗑️  Orphan: {file_path.name} (Video ID: {video_id})")
                        else:
                            print(f"   ✅  Valid: {file_path.name} (Video ID: {video_id})")
                    else:
                        # File doesn't match expected pattern - might be user file
                        print(f"   ⚠️  Unknown format: {file_path.name} (skipping)")

        print()

    # Summary
    print("=" * 80)
    print("SCAN SUMMARY")
    print("=" * 80)
    print(f"Total files scanned: {total_files_scanned}")
    print(f"Orphan files found: {len(orphan_files)}")

    if orphan_files:
        total_size = sum(size for _, _, size in orphan_files)
        print(f"Total size to free: {total_size:,} bytes ({total_size / (1024*1024):.2f} MB)")
        print()

        # List all orphan files
        print("FILES TO BE DELETED:")
        print("-" * 80)
        for file_path, video_id, size in orphan_files:
            print(f"  {file_path.name}")
            print(f"    Video ID: {video_id}")
            print(f"    Size: {size:,} bytes ({size / 1024:.1f} KB)")
            print()

        # Confirm deletion
        print("=" * 80)
        print("⚠️  WARNING: This will permanently delete these files!")
        print("This action CANNOT be undone!")
        print("=" * 80)
        print()

        response = input("Do you want to proceed? (yes/no): ").strip().lower()

        if response != 'yes':
            print("\n❌ Cleanup cancelled.")
            db.close()
            return

        # Delete files
        print("\n🗑️  Deleting orphan files...")
        deleted_count = 0
        deleted_size = 0
        errors = []

        for file_path, video_id, size in orphan_files:
            try:
                file_path.unlink()
                deleted_count += 1
                deleted_size += size
                print(f"  ✅ Deleted: {file_path.name}")
            except Exception as e:
                error_msg = f"Failed to delete {file_path.name}: {e}"
                errors.append(error_msg)
                print(f"  ❌ {error_msg}")

        # Final summary
        print("\n" + "=" * 80)
        print("CLEANUP COMPLETE")
        print("=" * 80)
        print(f"✅ Files deleted: {deleted_count}/{len(orphan_files)}")
        print(f"✅ Disk space freed: {deleted_size:,} bytes ({deleted_size / (1024*1024):.2f} MB)")

        if errors:
            print(f"\n⚠️  Errors encountered: {len(errors)}")
            for error in errors:
                print(f"  - {error}")
        else:
            print("\n✨ All orphan files successfully deleted!")

    else:
        print("\n✅ No orphan files found! Your directories are clean.")

    db.close()


if __name__ == '__main__':
    main()
