"""
Music DLP - Metadata Extractor

Extract playlist and video metadata from YouTube using yt-dlp without downloading.

This module handles:
- Playlist metadata extraction (title, uploader, video count)
- Individual video metadata (title, duration, thumbnail URL, etc.)
- Database storage of extracted metadata
- URL validation and type detection

Stage 1 of the pipeline: Extract metadata → Store in database → Ready for download
"""

from pathlib import Path
from typing import Optional, Tuple, List, Dict
from datetime import datetime
import yt_dlp
from core.logger import setup_logger
from core.database import Database


class MetadataExtractor:
    """Extracts playlist and video metadata from YouTube"""

    def __init__(self, database: Database, cookies_file: Optional[str] = None, logger=None):
        """
        Initialize metadata extractor.

        Args:
            database: Database instance for storing metadata
            cookies_file: Optional path to cookies.txt for authentication
            logger: Optional logger instance
        """
        self.db = database
        self.cookies_file = cookies_file
        self.logger = logger or setup_logger('metadata_extractor')

        self.logger.info("MetadataExtractor initialized")

    def _get_ydl_opts(self) -> dict:
        """
        Build yt-dlp options for metadata extraction only.

        Returns:
            Dict of yt-dlp options configured for extraction without download
        """
        opts = {
            # Don't download, only extract metadata
            'skip_download': True,
            'extract_flat': 'in_playlist',  # Get metadata without format resolution

            # Don't fail when formats can't be resolved (we don't need them)
            'ignore_no_formats_error': True,

            # EJS signature solving (required for YouTube as of 2026)
            'js_runtimes': {'node': {}},
            'remote_components': {'ejs:github': {}},

            # Performance
            'quiet': False,
            'no_warnings': False,

            # Authentication
            'sleep_interval_requests': 1,  # Be gentle with YouTube API

            # Logging
            'logger': self.logger,

            # Don't save anything to disk
            'writeinfojson': False,
            'writethumbnail': False,
            'writedescription': False,
        }

        # Add cookies if configured
        if self.cookies_file and Path(self.cookies_file).exists():
            opts['cookiefile'] = self.cookies_file
            self.logger.debug(f"Using cookies from: {self.cookies_file}")

        return opts

    def extract_playlist(
        self,
        playlist_url: str,
        store_in_db: bool = True
    ) -> Tuple[bool, Optional[str], Optional[dict]]:
        """
        Extract metadata from a YouTube playlist.

        Args:
            playlist_url: URL of the YouTube playlist
            store_in_db: If True, store results in database (default: True)

        Returns:
            Tuple of (success: bool, error_message: str|None, playlist_data: dict|None)

            playlist_data contains:
                - playlist_id: str
                - title: str
                - uploader: str
                - video_count: int
                - videos: List[dict] with video metadata
        """
        self.logger.info(f"Extracting playlist metadata from: {playlist_url}")

        opts = self._get_ydl_opts()

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                # Extract info
                info = ydl.extract_info(playlist_url, download=False)

                if not info:
                    error_msg = "No metadata returned from yt-dlp"
                    self.logger.error(error_msg)
                    return False, error_msg, None

                # Check if it's actually a playlist
                if info.get('_type') not in ('playlist', 'multi_video'):
                    # It's a single video, not a playlist
                    self.logger.warning(f"URL is a single video, not a playlist: {playlist_url}")

                    # Extract as single video instead
                    return self.extract_single_video(playlist_url, store_in_db)

                # Extract playlist metadata
                playlist_id = info.get('id', '')
                title = info.get('title', 'Unknown Playlist')
                uploader = info.get('uploader', info.get('channel', 'Unknown'))
                entries = info.get('entries', [])
                video_count = len(entries)

                self.logger.info(
                    f"Extracted playlist: '{title}' by {uploader} "
                    f"({video_count} videos)"
                )

                # Extract video metadata from entries
                videos = []
                for position, entry in enumerate(entries, start=1):
                    if entry is None:
                        self.logger.warning(f"Skipping null entry at position {position}")
                        continue

                    video_data = self._parse_video_entry(entry, position)
                    if video_data:
                        videos.append(video_data)

                playlist_data = {
                    'playlist_id': playlist_id,
                    'title': title,
                    'uploader': uploader,
                    'url': playlist_url,
                    'video_count': video_count,
                    'videos': videos
                }

                # Store in database if requested
                if store_in_db:
                    self._store_playlist_in_db(playlist_data)

                self.logger.info(f"Successfully extracted {len(videos)} videos from playlist")

                return True, None, playlist_data

        except yt_dlp.utils.DownloadError as e:
            error_msg = f"yt-dlp download error: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg, None

        except Exception as e:
            error_msg = f"Unexpected error extracting playlist: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, error_msg, None

    def extract_single_video(
        self,
        video_url: str,
        store_in_db: bool = True
    ) -> Tuple[bool, Optional[str], Optional[dict]]:
        """
        Extract metadata from a single YouTube video.

        Args:
            video_url: URL of the YouTube video
            store_in_db: If True, store result in database (default: True)

        Returns:
            Tuple of (success: bool, error_message: str|None, video_data: dict|None)
        """
        self.logger.info(f"Extracting video metadata from: {video_url}")

        opts = self._get_ydl_opts()
        # Single videos need full extraction for complete metadata
        opts['extract_flat'] = False

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                # Extract info
                info = ydl.extract_info(video_url, download=False)

                if not info:
                    error_msg = "No metadata returned from yt-dlp"
                    self.logger.error(error_msg)
                    return False, error_msg, None

                # Parse video data
                video_data = self._parse_video_entry(info, position=1)

                if not video_data:
                    error_msg = "Failed to parse video metadata"
                    self.logger.error(error_msg)
                    return False, error_msg, None

                self.logger.info(
                    f"Extracted video: '{video_data['title']}' by {video_data['uploader']} "
                    f"({video_data['duration']}s)"
                )

                # Store in database if requested
                if store_in_db:
                    self._store_video_in_db(video_data)

                return True, None, video_data

        except yt_dlp.utils.DownloadError as e:
            error_msg = f"yt-dlp download error: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg, None

        except Exception as e:
            error_msg = f"Unexpected error extracting video: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, error_msg, None

    def _parse_video_entry(self, entry: dict, position: int = 1) -> Optional[dict]:
        """
        Parse a video entry dict from yt-dlp into our format.

        Handles both flat extraction (playlist mode) and full extraction entries.

        Args:
            entry: Video info dict from yt-dlp
            position: Position in playlist (default: 1)

        Returns:
            Dict with standardized video metadata, or None if parsing fails
        """
        try:
            video_id = entry.get('id')
            if not video_id:
                self.logger.warning("Video entry missing ID, skipping")
                return None

            # Get thumbnail URL (prefer maxresdefault, fallback to default)
            thumbnails = entry.get('thumbnails', [])
            thumbnail_url = entry.get('thumbnail', '')

            if thumbnails:
                # Try to get highest quality thumbnail
                for thumb in reversed(thumbnails):
                    if thumb.get('url'):
                        thumbnail_url = thumb['url']
                        break

            # If no thumbnail from metadata, construct YouTube default URL
            if not thumbnail_url:
                thumbnail_url = f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"

            # Build URL — flat extraction uses 'url', full uses 'webpage_url'
            url = (
                entry.get('webpage_url')
                or entry.get('url')
                or f"https://www.youtube.com/watch?v={video_id}"
            )

            video_data = {
                'video_id': video_id,
                'title': entry.get('title', 'Unknown Title'),
                'uploader': entry.get('uploader', entry.get('channel', entry.get('uploader_id', 'Unknown'))),
                'duration': entry.get('duration') or 0,
                'url': url,
                'description': entry.get('description', ''),
                'thumbnail_url': thumbnail_url,
                'position': position
            }

            return video_data

        except Exception as e:
            self.logger.error(f"Error parsing video entry: {str(e)}", exc_info=True)
            return None

    def _store_playlist_in_db(self, playlist_data: dict):
        """
        Store playlist and its videos in the database.

        Args:
            playlist_data: Dict with playlist metadata and videos list
        """
        try:
            # Add playlist
            self.db.add_playlist(
                playlist_id=playlist_data['playlist_id'],
                title=playlist_data['title'],
                uploader=playlist_data['uploader'],
                url=playlist_data['url'],
                video_count=playlist_data['video_count']
            )

            self.logger.debug(f"Stored playlist: {playlist_data['playlist_id']}")

            # Add each video
            for video in playlist_data['videos']:
                # Add video to videos table
                self.db.add_video(
                    video_id=video['video_id'],
                    title=video['title'],
                    uploader=video['uploader'],
                    duration=video['duration'],
                    url=video['url'],
                    description=video.get('description', ''),
                    thumbnail_url=video.get('thumbnail_url', '')
                )

                # Link video to playlist
                self.db.link_video_to_playlist(
                    playlist_id=playlist_data['playlist_id'],
                    video_id=video['video_id'],
                    position=video['position']
                )

            self.logger.info(
                f"Stored {len(playlist_data['videos'])} videos in database "
                f"for playlist {playlist_data['playlist_id']}"
            )

        except Exception as e:
            self.logger.error(f"Error storing playlist in database: {str(e)}", exc_info=True)
            raise

    def _store_video_in_db(self, video_data: dict):
        """
        Store a single video in the database.

        Args:
            video_data: Dict with video metadata
        """
        try:
            self.db.add_video(
                video_id=video_data['video_id'],
                title=video_data['title'],
                uploader=video_data['uploader'],
                duration=video_data['duration'],
                url=video_data['url'],
                description=video_data.get('description', ''),
                thumbnail_url=video_data.get('thumbnail_url', '')
            )

            self.logger.debug(f"Stored video: {video_data['video_id']}")

        except Exception as e:
            self.logger.error(f"Error storing video in database: {str(e)}", exc_info=True)
            raise

    def get_playlist_videos_count(self, playlist_url: str) -> Tuple[bool, Optional[str], int]:
        """
        Quickly get just the video count from a playlist (fast extraction).

        Args:
            playlist_url: URL of the YouTube playlist

        Returns:
            Tuple of (success: bool, error_message: str|None, video_count: int)
        """
        self.logger.info(f"Getting video count for playlist: {playlist_url}")

        opts = self._get_ydl_opts()
        opts['extract_flat'] = True  # Fast extraction, only IDs

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(playlist_url, download=False)

                if not info:
                    return False, "No metadata returned", 0

                if info.get('_type') != 'playlist':
                    return False, "URL is not a playlist", 0

                entries = info.get('entries', [])
                count = len(entries)

                self.logger.info(f"Playlist contains {count} videos")
                return True, None, count

        except Exception as e:
            error_msg = f"Error getting video count: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg, 0


def validate_youtube_url(url: str) -> Tuple[bool, str]:
    """
    Validate and identify YouTube URL type.

    Args:
        url: YouTube URL to validate

    Returns:
        Tuple of (is_valid: bool, url_type: str)
        url_type can be: 'playlist', 'video', 'invalid'
    """
    url_lower = url.lower()

    # Check for playlist
    if 'playlist?list=' in url_lower or '/playlist?list=' in url_lower:
        return True, 'playlist'

    # Check for video
    if 'youtube.com/watch?' in url_lower or 'youtu.be/' in url_lower:
        return True, 'video'

    # Invalid
    return False, 'invalid'


def extract_playlist_id(url: str) -> Optional[str]:
    """
    Extract playlist ID from YouTube playlist URL.

    Args:
        url: YouTube playlist URL

    Returns:
        Playlist ID or None if not found
    """
    if 'list=' in url:
        parts = url.split('list=')
        if len(parts) > 1:
            # Get everything after list= until & or end of string
            playlist_id = parts[1].split('&')[0]
            return playlist_id
    return None


def extract_video_id(url: str) -> Optional[str]:
    """
    Extract video ID from YouTube video URL.

    Args:
        url: YouTube video URL

    Returns:
        Video ID (11 characters) or None if not found
    """
    url_lower = url.lower()

    # youtu.be short URLs
    if 'youtu.be/' in url_lower:
        parts = url.split('youtu.be/')
        if len(parts) > 1:
            video_id = parts[1].split('?')[0].split('&')[0]
            if len(video_id) == 11:
                return video_id

    # youtube.com/watch?v= URLs
    if 'v=' in url:
        parts = url.split('v=')
        if len(parts) > 1:
            video_id = parts[1].split('&')[0]
            if len(video_id) == 11:
                return video_id

    return None
