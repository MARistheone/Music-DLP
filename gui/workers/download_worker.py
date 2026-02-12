"""
Download Worker

Background threading worker for:
- Playlist metadata extraction
- Video downloads
- Progress callbacks to GUI

Author: Music DLP Project
Version: 1.0.0
"""

import threading
from typing import Callable, Optional, List, Dict
import time
import shutil
from pathlib import Path

from downloaders.yt_dlp_manager import YTDLPManager
from downloaders.metadata_extractor import MetadataExtractor
from downloaders.thumbnail_processor import ThumbnailProcessor


class DownloadWorker(threading.Thread):
    """
    Background worker for downloads and extraction.

    Runs in separate thread to prevent GUI blocking.
    """

    def __init__(self, db, config, logger,
                 mode: str = 'download',
                 url: Optional[str] = None,
                 videos: Optional[List[Dict]] = None,
                 on_complete: Optional[Callable] = None,
                 on_progress: Optional[Callable] = None):
        """
        Initialize download worker.

        Args:
            db: Database instance
            config: ConfigManager instance
            logger: Logger instance
            mode: Operation mode ('extract' or 'download')
            url: Playlist URL (for extract mode)
            videos: List of video dicts (for download mode)
            on_complete: Callback when complete (success: bool, result: dict)
            on_progress: Callback for progress updates (current: int, total: int, message: str)
        """
        super().__init__(daemon=True)

        self.db = db
        self.config = config
        self.logger = logger

        self.mode = mode
        self.url = url
        self.videos = videos or []

        self.on_complete = on_complete
        self.on_progress = on_progress

        self.cancelled = False

    def run(self):
        """Execute the download operation."""
        try:
            if self.mode == 'extract':
                self._extract_playlist()
            elif self.mode == 'download':
                self._download_videos()
            else:
                raise ValueError(f"Invalid mode: {self.mode}")

        except Exception as e:
            self.logger.error(f"Download worker error: {e}")
            if self.on_complete:
                self.on_complete(False, {'error': str(e)})

    def _extract_playlist(self):
        """Extract playlist metadata (Stage 1)."""
        if not self.url:
            raise ValueError("URL required for extract mode")

        self.logger.info(f"Extracting playlist: {self.url}")

        if self.on_progress:
            self.on_progress(0, 1, "Extracting playlist metadata...")

        try:
            # Initialize extractor
            extractor = MetadataExtractor(
                database=self.db,
                cookies_file=self.config.cookies_file,
                logger=self.logger
            )

            # Extract metadata
            success, error, playlist_data = extractor.extract_playlist(self.url)

            if not success:
                raise Exception(f"Failed to extract playlist: {error}")

            # Get playlist info
            playlist_id = playlist_data['playlist_id']
            playlist = self.db.get_playlist(playlist_id)
            video_count = playlist.get('video_count', 0)

            if self.on_progress:
                self.on_progress(1, 1, f"Extracted {video_count} videos")

            self.logger.info(f"Extraction complete: {playlist_id}")

            if self.on_complete:
                self.on_complete(True, {
                    'playlist_id': playlist_id,
                    'title': playlist.get('title', 'Unknown'),
                    'video_count': video_count
                })

        except Exception as e:
            self.logger.error(f"Extraction failed: {e}")
            if self.on_complete:
                self.on_complete(False, {'error': str(e)})

    def _download_videos(self):
        """Download videos (Stage 2) with resume support and disk space check."""
        if not self.videos:
            raise ValueError("Videos required for download mode")

        # --- Disk space pre-check ---
        try:
            output_dir = Path(str(self.config.raw_download_dir))
            output_dir.mkdir(parents=True, exist_ok=True)
            usage = shutil.disk_usage(str(output_dir))
            free_gb = usage.free / (1024**3)
            if free_gb < 5.0:
                self.logger.warning(
                    f"LOW DISK SPACE: {free_gb:.1f}GB free. "
                    f"Recommend 5GB+ for large playlists."
                )
        except Exception as e:
            self.logger.warning(f"Could not check disk space: {e}")

        # --- Resume: filter out already-downloaded videos ---
        remaining = []
        skipped = 0
        for v in self.videos:
            vid = v['video_id']
            if v.get('download_status') == 'downloaded':
                raw_path = v.get('file_path_raw')
                if raw_path and Path(raw_path).exists():
                    skipped += 1
                    continue
            remaining.append(v)

        if skipped > 0:
            self.logger.info(f"Resuming: skipping {skipped} already-downloaded video(s)")

        if not remaining:
            self.logger.info("All videos already downloaded - nothing to do")
            if self.on_complete:
                self.on_complete(True, {'count': 0, 'total': len(self.videos), 'errors': 0, 'skipped': skipped})
            return

        total = len(remaining)
        self.logger.info(f"Downloading {total} videos ({skipped} already done)...")

        try:
            # Initialize download manager
            manager = YTDLPManager(
                cookies_file=self.config.cookies_file,
                sleep_interval=self.config.get_int('Download', 'sleep_interval_min', 2),
                max_sleep_interval=self.config.get_int('Download', 'sleep_interval_max', 5),
                max_retries=self.config.get_int('Download', 'max_retries', 3),
                logger=self.logger
            )

            # Initialize thumbnail processor
            thumb_processor = ThumbnailProcessor(
                logger=self.logger
            )

            success_count = 0
            error_count = 0

            for idx, video in enumerate(remaining, 1):
                if self.cancelled:
                    self.logger.info("Download cancelled by user")
                    break

                video_id = video['video_id']
                title = video.get('title', 'Unknown')

                # Update progress
                if self.on_progress:
                    self.on_progress(idx, total, f"Downloading: {title[:50]}...")

                try:
                    # Mark as in-progress so interrupted downloads are detectable
                    self.db.update_download_status(video_id=video_id, status='downloading')

                    # Download audio
                    success, error_msg, info = manager.download_audio(
                        video_id=video_id,
                        output_dir=str(self.config.raw_download_dir)
                    )

                    if success:
                        success_count += 1
                        self.logger.info(f"Downloaded: {video_id}")

                        # Update database
                        self.db.update_download_status(
                            video_id=video_id,
                            status='downloaded',
                            file_path=info.get('filename') if info else None
                        )

                        # Download thumbnail
                        try:
                            thumb_url = video.get('thumbnail_url')
                            if thumb_url:
                                thumb_path = self.config.raw_download_dir / f"{video_id}_thumb.jpg"
                                thumb_success, thumb_error = thumb_processor.download_and_process(
                                    thumbnail_url=thumb_url,
                                    output_path=str(thumb_path)
                                )
                                if not thumb_success:
                                    self.logger.warning(f"Thumbnail download failed: {thumb_error}")
                        except Exception as te:
                            self.logger.warning(f"Thumbnail download failed: {te}")

                    else:
                        error_count += 1
                        self.logger.error(f"Download failed for {video_id}: {error_msg}")

                        # Update database with error
                        self.db.update_download_status(
                            video_id=video_id,
                            status='error',
                            error=error_msg
                        )

                except Exception as e:
                    error_count += 1
                    self.logger.error(f"Download error for {video_id}: {e}")

                # Cool-down pause every 50 successful downloads
                if success_count > 0 and success_count % 50 == 0:
                    self.logger.info("Cool-down: pausing 30s after 50 downloads to avoid rate limiting...")
                    time.sleep(30)

            # Final progress
            if self.on_progress:
                self.on_progress(
                    total,
                    total,
                    f"Complete: {success_count} succeeded, {error_count} failed, {skipped} skipped"
                )

            # Complete callback
            if self.on_complete:
                self.on_complete(True, {
                    'count': success_count,
                    'total': total,
                    'errors': error_count,
                    'skipped': skipped
                })

        except Exception as e:
            self.logger.error(f"Download batch failed: {e}")
            if self.on_complete:
                self.on_complete(False, {'error': str(e)})

    def cancel(self):
        """Cancel the download operation."""
        self.cancelled = True
        self.logger.info("Download worker cancellation requested")
