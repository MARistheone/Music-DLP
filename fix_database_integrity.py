"""Fix database integrity issues - remove orphan links and videos"""
from core.database import Database

db = Database()
cursor = db.conn.cursor()

print("=" * 80)
print("DATABASE INTEGRITY FIX")
print("=" * 80)
print()

# Step 1: Find and delete orphan playlist_videos links
print("STEP 1: Cleaning up orphan playlist_videos links...")
cursor.execute("""
    SELECT pv.playlist_id, pv.video_id
    FROM playlist_videos pv
    LEFT JOIN playlists p ON pv.playlist_id = p.playlist_id
    WHERE p.playlist_id IS NULL
""")
orphan_links = cursor.fetchall()

if orphan_links:
    print(f"Found {len(orphan_links)} orphan links to delete:")
    for link in orphan_links:
        print(f"  - Playlist: {link['playlist_id']}, Video: {link['video_id']}")

    cursor.execute("""
        DELETE FROM playlist_videos
        WHERE playlist_id NOT IN (SELECT playlist_id FROM playlists)
    """)
    db.conn.commit()
    print(f"✅ Deleted {len(orphan_links)} orphan playlist_videos links")
else:
    print("✅ No orphan links found")

print()

# Step 2: Find orphaned videos (not in any playlist)
print("STEP 2: Finding orphaned videos...")
cursor.execute("""
    SELECT v.video_id, v.title
    FROM videos v
    LEFT JOIN playlist_videos pv ON v.video_id = pv.video_id
    WHERE pv.video_id IS NULL
""")
orphaned_videos = cursor.fetchall()

if orphaned_videos:
    print(f"Found {len(orphaned_videos)} orphaned videos:")
    for video in orphaned_videos:
        print(f"  - {video['video_id']}: {video['title'][:60]}")
    print()

    response = input(f"Delete these {len(orphaned_videos)} orphaned videos and their files? (yes/no): ").strip().lower()

    if response == 'yes':
        # Use the delete_orphaned_videos method
        summary = db.delete_orphaned_videos(delete_files=True)

        print()
        print("=" * 80)
        print("CLEANUP SUMMARY")
        print("=" * 80)
        print(f"✅ Videos deleted: {summary['videos_deleted']}")
        print(f"✅ Files deleted: {summary['files_deleted']}")

        if summary['errors']:
            print(f"\n⚠️  Errors: {len(summary['errors'])}")
            for error in summary['errors']:
                print(f"  - {error}")
    else:
        print("❌ Skipped video deletion")
else:
    print("✅ No orphaned videos found")

print()
print("=" * 80)
print("INTEGRITY FIX COMPLETE")
print("=" * 80)

db.close()
