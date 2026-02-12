"""
AI Worker

Background threading worker for:
- AI title processing with Ollama
- Parallel processing with multiple models
- Progress callbacks to GUI

Author: Music DLP Project
Version: 1.0.0
"""

import threading
import json
from typing import Callable, Optional, List, Dict

from ai.title_processor import TitleProcessor


class AIWorker(threading.Thread):
    """
    Background worker for AI processing.

    Runs in separate thread to prevent GUI blocking.
    """

    def __init__(self, db, config, logger,
                 videos: List[Dict],
                 on_complete: Optional[Callable] = None,
                 on_progress: Optional[Callable] = None):
        """
        Initialize AI worker.

        Args:
            db: Database instance
            config: ConfigManager instance
            logger: Logger instance
            videos: List of video dicts to process
            on_complete: Callback when complete (success: bool, result: dict)
            on_progress: Callback for progress updates (current: int, total: int, message: str)
        """
        super().__init__(daemon=True)

        self.db = db
        self.config = config
        self.logger = logger

        self.videos = videos
        self.on_complete = on_complete
        self.on_progress = on_progress

        self.cancelled = False

    def run(self):
        """Execute AI processing."""
        try:
            self._process_videos()

        except Exception as e:
            self.logger.error(f"AI worker error: {e}")
            if self.on_complete:
                self.on_complete(False, {'error': str(e)})

    def _process_videos(self):
        """Process videos with AI (Stage 3) with resume support."""
        # --- Resume: filter out videos that already have AI attempts ---
        remaining = []
        skipped = 0
        for video in self.videos:
            vid = video['video_id']
            existing_attempts = self.db.get_ai_attempts(vid)
            if existing_attempts:
                skipped += 1
            else:
                remaining.append(video)

        if skipped > 0:
            self.logger.info(f"Resuming: skipping {skipped} video(s) that already have AI attempts")

        if not remaining:
            self.logger.info("All videos already have AI attempts - nothing to do")
            if self.on_complete:
                self.on_complete(True, {'count': 0, 'total': len(self.videos), 'errors': 0, 'skipped': skipped})
            return

        total = len(remaining)
        self.logger.info(f"Processing {total} videos with AI ({skipped} already done)...")

        if self.on_progress:
            self.on_progress(0, total, "Initializing AI processor...")

        try:
            # Initialize title processor with active models
            # active_ai_models returns either [primary_model] or all models
            # based on the use_all_models setting
            active_models = self.config.active_ai_models
            self.logger.info(f"Using {len(active_models)} model(s): {', '.join(active_models)}")

            processor = TitleProcessor(
                db=self.db,
                ollama_url=self.config.ollama_url,
                models=active_models,  # Use active models based on settings
                max_workers=self.config.parallel_workers
            )

            # Check Ollama availability
            availability = processor.check_availability()
            if not any(availability.values()):
                raise Exception(
                    "Ollama is not available.\n\n"
                    "Make sure Ollama is running and accessible at:\n"
                    f"{self.config.ollama_url}"
                )

            # Extract video IDs for batch processing (only remaining)
            video_ids = [video['video_id'] for video in remaining]

            # Use optimized batch processing (one model at a time)
            # This keeps one model in VRAM and processes all videos in parallel
            def batch_progress(current, total_tasks, message):
                """Wrapper to convert batch progress to worker progress."""
                if self.cancelled:
                    return  # Stop if cancelled

                if self.on_progress:
                    self.on_progress(current, total_tasks, message)

            # Process all videos with batch method
            all_results = processor.process_batch(
                video_ids=video_ids,
                progress_callback=batch_progress
            )

            # Count successes and errors
            success_count = sum(
                1 for results in all_results.values()
                if any(r.success for r in results)
            )
            error_count = total - success_count

            # Log completion
            self.logger.info(
                f"AI batch processing complete: {success_count} succeeded, {error_count} failed"
            )

            # Final progress
            if self.on_progress:
                self.on_progress(
                    len(all_results),
                    total,
                    f"Complete: {success_count} succeeded, {error_count} failed"
                )

            # Complete callback
            if self.on_complete:
                self.on_complete(True, {
                    'count': success_count,
                    'total': total,
                    'errors': error_count
                })

        except Exception as e:
            self.logger.error(f"AI batch processing failed: {e}")
            if self.on_complete:
                self.on_complete(False, {'error': str(e)})

    def cancel(self):
        """Cancel the AI processing operation."""
        self.cancelled = True
        self.logger.info("AI worker cancellation requested")
