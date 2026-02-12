"""Quick database state check"""
from core.database import Database

db = Database()

# Check playlists
cursor = db.conn.cursor()
cursor.execute("SELECT playlist_id, title, video_count FROM playlists")
playlists = cursor.fetchall()

print("PLAYLISTS:")
print("=" * 60)
if playlists:
    for p in playlists:
        print(f"  {p['title']} ({p['playlist_id']})")
        print(f"    Video count: {p['video_count']}")
else:
    print("  No playlists found")

print()

# Check videos
cursor.execute("SELECT video_id, title FROM videos")
videos = cursor.fetchall()

print(f"VIDEOS: {len(videos)} total")
print("=" * 60)
for v in videos:
    print(f"  {v['video_id']}: {v['title'][:60]}")

print()

# Check orphaned videos
cursor.execute("""
    SELECT v.video_id, v.title
    FROM videos v
    LEFT JOIN playlist_videos pv ON v.video_id = pv.video_id
    WHERE pv.video_id IS NULL
""")
orphaned = cursor.fetchall()

print(f"ORPHANED VIDEOS (not in any playlist): {len(orphaned)}")
print("=" * 60)
if orphaned:
    for v in orphaned:
        print(f"  {v['video_id']}: {v['title'][:60]}")
else:
    print("  None")

db.close()
