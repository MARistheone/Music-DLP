"""
Cleanup Orphaned Videos

This script helps clean up videos that are not linked to any playlist.
Run this after deleting playlists to free up disk space.

Usage:
    python cleanup_orphaned_videos.py
"""

from core.database import Database
from core.logger import setup_logger


def main():
    # Setup
    logger = setup_logger('cleanup', level='INFO')
    db = Database()

    print("=" * 60)
    print("ORPHANED VIDEO CLEANUP")
    print("=" * 60)
    print()

    # Get orphaned videos
    orphaned = db.get_orphaned_videos()

    if not orphaned:
        print("✅ No orphaned videos found!")
        print("Your database is clean.")
        db.close()
        return

    print(f"Found {len(orphaned)} orphaned video(s):")
    print()

    # Display orphaned videos
    for idx, video in enumerate(orphaned, 1):
        print(f"{idx}. {video['title'][:60]}")
        print(f"   Video ID: {video['video_id']}")
        print(f"   Download Status: {video['download_status']}")
        if video.get('file_path_raw'):
            print(f"   Raw File: {video['file_path_raw']}")
        print()

    # Confirm deletion
    print("=" * 60)
    print("⚠️  WARNING: This will:")
    print("  - Delete all orphaned videos from the database")
    print("  - Delete all associated files (.opus, .mp3, .m4a)")
    print("  - Delete all AI attempts and approved metadata")
    print("  - This action CANNOT be undone!")
    print("=" * 60)
    print()

    response = input("Do you want to proceed? (yes/no): ").strip().lower()

    if response != 'yes':
        print("\n❌ Cleanup cancelled.")
        db.close()
        return

    # Perform cleanup
    print("\n🗑️  Deleting orphaned videos and files...")
    summary = db.delete_orphaned_videos(delete_files=True)

    print("\n" + "=" * 60)
    print("CLEANUP SUMMARY")
    print("=" * 60)
    print(f"✅ Videos deleted from database: {summary['videos_deleted']}")
    print(f"✅ Files deleted from disk: {summary['files_deleted']}")

    if summary['errors']:
        print(f"\n⚠️  Errors encountered: {len(summary['errors'])}")
        for error in summary['errors']:
            print(f"  - {error}")
    else:
        print("\n✨ Cleanup completed successfully!")

    db.close()


if __name__ == '__main__':
    main()
