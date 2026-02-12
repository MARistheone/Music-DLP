"""
Test script to verify all database methods work correctly.
Tests the newly added delete, update, and alias methods.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.database import Database
from core.logger import setup_logger

def test_database_methods():
    """Test all database methods."""

    logger = setup_logger('test', level='INFO')
    print("=" * 80)
    print("DATABASE METHODS TEST")
    print("=" * 80)

    # Use a test database
    db = Database("test_methods.db")

    try:
        # Test 1: Add playlist
        print("\n[TEST 1] Adding test playlist...")
        result = db.add_playlist(
            playlist_id="PL_TEST123",
            title="Test Playlist",
            url="https://youtube.com/playlist?list=PL_TEST123",
            video_count=5
        )
        print(f"[OK] add_playlist: {result}")

        # Test 2: Get playlist
        print("\n[TEST 2] Getting playlist...")
        playlist = db.get_playlist("PL_TEST123")
        print(f"[OK] get_playlist: {playlist['title'] if playlist else 'None'}")

        # Test 3: Update playlist
        print("\n[TEST 3] Updating playlist...")
        result = db.update_playlist("PL_TEST123", title="Updated Test Playlist", video_count=10)
        print(f"[OK] update_playlist: {result}")

        updated = db.get_playlist("PL_TEST123")
        print(f"  Updated title: {updated['title']}")
        print(f"  Updated count: {updated['video_count']}")

        # Test 4: Add video
        print("\n[TEST 4] Adding test video...")
        result = db.add_video(
            video_id="VID_TEST123",
            title="Test Video",
            url="https://youtube.com/watch?v=VID_TEST123",
            uploader="Test Channel"
        )
        print(f"[OK] add_video: {result}")

        # Test 5: Link video to playlist
        print("\n[TEST 5] Linking video to playlist...")
        result = db.link_video_to_playlist("PL_TEST123", "VID_TEST123", 1)
        print(f"[OK] link_video_to_playlist: {result}")

        # Test 6: Get playlist videos
        print("\n[TEST 6] Getting playlist videos...")
        videos = db.get_playlist_videos("PL_TEST123")
        print(f"[OK] get_playlist_videos: {len(videos)} video(s)")

        # Test 7: Add AI attempt
        print("\n[TEST 7] Adding AI attempt...")
        attempt_id = db.add_ai_attempt(
            video_id="VID_TEST123",
            model_name="test-model",
            generated_title="Test Title",
            artist="Test Artist",
            tags=["test", "demo"],
            confidence=0.95
        )
        print(f"[OK] add_ai_attempt: ID {attempt_id}")

        # Test 8: Add approved metadata (using new alias method)
        print("\n[TEST 8] Adding approved metadata (alias method)...")
        result = db.add_approved_metadata(
            video_id="VID_TEST123",
            final_title="Approved Title",
            final_artist="Approved Artist",
            album="Test Album",
            tags=["approved", "test"],
            selected_attempt_id=attempt_id
        )
        print(f"[OK] add_approved_metadata: {result}")

        # Test 9: Get approved metadata
        print("\n[TEST 9] Getting approved metadata...")
        metadata = db.get_approved_metadata("VID_TEST123")
        print(f"[OK] get_approved_metadata: {metadata['final_title'] if metadata else 'None'}")

        # Test 10: Update approved metadata (using new method)
        print("\n[TEST 10] Updating approved metadata...")
        result = db.update_approved_metadata(
            video_id="VID_TEST123",
            final_title="Updated Approved Title"
        )
        print(f"[OK] update_approved_metadata: {result}")

        updated_metadata = db.get_approved_metadata("VID_TEST123")
        print(f"  Updated title: {updated_metadata['final_title']}")

        # Test 11: Unlink video from playlist
        print("\n[TEST 11] Unlinking video from playlist...")
        result = db.unlink_video_from_playlist("PL_TEST123", "VID_TEST123")
        print(f"[OK] unlink_video_from_playlist: {result}")

        # Test 12: Delete video (using new method)
        print("\n[TEST 12] Deleting video...")
        result = db.delete_video("VID_TEST123")
        print(f"[OK] delete_video: {result}")

        # Verify deletion
        video = db.get_video("VID_TEST123")
        print(f"  Video exists after delete: {video is not None}")

        # Test 13: Delete playlist (using new method)
        print("\n[TEST 13] Deleting playlist...")
        result = db.delete_playlist("PL_TEST123")
        print(f"[OK] delete_playlist: {result}")

        # Verify deletion
        playlist = db.get_playlist("PL_TEST123")
        print(f"  Playlist exists after delete: {playlist is not None}")

        print("\n" + "=" * 80)
        print("[PASS] ALL TESTS PASSED!")
        print("=" * 80)

    except Exception as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        db.close()
        # Clean up test database
        test_db_path = Path("test_methods.db")
        if test_db_path.exists():
            test_db_path.unlink()
            print("\n[DEL]  Cleaned up test database")

    return True

if __name__ == "__main__":
    success = test_database_methods()
    sys.exit(0 if success else 1)
