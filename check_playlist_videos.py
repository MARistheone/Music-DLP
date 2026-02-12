"""Check playlist_videos table for orphan links"""
from core.database import Database

db = Database()
cursor = db.conn.cursor()

print("=" * 80)
print("PLAYLIST_VIDEOS TABLE ANALYSIS")
print("=" * 80)
print()

# Check all playlist_videos entries
cursor.execute("SELECT * FROM playlist_videos")
pv_entries = cursor.fetchall()

print(f"Total playlist_videos entries: {len(pv_entries)}")
print()

if pv_entries:
    print("PLAYLIST_VIDEOS ENTRIES:")
    print("-" * 80)
    for pv in pv_entries:
        print(f"  Playlist: {pv['playlist_id']}")
        print(f"  Video: {pv['video_id']}")
        print(f"  Position: {pv['position']}")

        # Check if playlist exists
        cursor.execute("SELECT title FROM playlists WHERE playlist_id = ?", (pv['playlist_id'],))
        playlist = cursor.fetchone()
        if playlist:
            print(f"  ✅ Playlist exists: {playlist['title']}")
        else:
            print(f"  ❌ ORPHAN LINK - Playlist does NOT exist!")

        # Check if video exists
        cursor.execute("SELECT title FROM videos WHERE video_id = ?", (pv['video_id'],))
        video = cursor.fetchone()
        if video:
            print(f"  ✅ Video exists: {video['title'][:50]}")
        else:
            print(f"  ❌ Video does NOT exist!")

        print()

print("=" * 80)
print("DIAGNOSIS:")
print("=" * 80)

# Count orphan playlist links
cursor.execute("""
    SELECT COUNT(*) as count
    FROM playlist_videos pv
    LEFT JOIN playlists p ON pv.playlist_id = p.playlist_id
    WHERE p.playlist_id IS NULL
""")
orphan_playlist_links = cursor.fetchone()['count']

print(f"Orphan playlist links (playlist_videos pointing to deleted playlists): {orphan_playlist_links}")

if orphan_playlist_links > 0:
    print()
    print("⚠️  PROBLEM FOUND!")
    print("The playlist_videos table has orphan links pointing to deleted playlists.")
    print("This is why videos aren't showing as orphaned.")
    print()
    print("FIX: Delete these orphan links from playlist_videos table")

db.close()
