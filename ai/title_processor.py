"""
AI Title Processor for Music DLP.

This module orchestrates parallel AI processing of YouTube titles using multiple
Ollama models. It manages the processing workflow, stores results in the database,
and provides progress tracking for GUI integration.

The processor:
- Runs multiple models in parallel (gemma3:12b, qwen3:14b, qwen2.5:7b)
- Uses ThreadPoolExecutor for concurrent processing

- Stores all AI attempts in the database
- Handles errors gracefully with fallbacks
- Provides progress callbacks for UI updates
"""

import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass

from .ollama_client import OllamaClient
from .prompts import (
    SYSTEM_PROMPT,
    PROMPT_VERSION,
    build_user_prompt,
    validate_response,
    normalize_response
)
from core.database import Database


@dataclass
class ProcessingResult:
    """
    Result of processing a single video with one model.

    Attributes:
        video_id: The YouTube video ID
        model_name: The model used (e.g., 'gemma3:12b')
        success: Whether processing succeeded
        title: Generated title (None if failed)
        artist: Generated original artist (None if failed)
        cover_artist: Cover/performing artist (None if original or failed)
        tags: Generated tags as JSON string (None if failed)
        confidence: Confidence score (None if failed)
        processing_time: Time taken in seconds
        error: Error message if failed (None if succeeded)
    """
    video_id: str
    model_name: str
    success: bool
    title: Optional[str] = None
    artist: Optional[str] = None
    cover_artist: Optional[str] = None
    tags: Optional[str] = None  # JSON string
    confidence: Optional[float] = None
    processing_time: float = 0.0
    error: Optional[str] = None


class TitleProcessor:
    """
    AI title processor with parallel model execution.

    This class orchestrates the AI processing workflow:
    1. Fetch videos from database that need processing
    2. Run multiple AI models in parallel for each video
    3. Store all attempts in the database
    4. Provide progress updates via callbacks

    Attributes:
        db: Database instance
        client: OllamaClient instance
        models: List of model names to use
        max_workers: Maximum parallel workers
        logger: Logger instance
    """

    def __init__(
        self,
        db: Database,
        ollama_url: str = "http://localhost:11434",
        models: Optional[List[str]] = None,
        max_workers: int = 3,
        auto_unload: bool = True
    ):
        """
        Initialize the title processor.

        Args:
            db: Database instance for storing results
            ollama_url: Ollama API URL
            models: List of model names (defaults to gemma3:12b, qwen3:14b, qwen2.5:7b)
            max_workers: Maximum number of parallel workers
            auto_unload: If True, unload models from VRAM after each batch (default: True)
        """
        self.db = db
        self.client = OllamaClient(base_url=ollama_url, auto_unload=auto_unload)
        self.models = models or ['gemma3:12b', 'qwen3:14b', 'qwen2.5:7b']
        self.max_workers = max_workers
        self.auto_unload = auto_unload
        self.logger = logging.getLogger('music_dlp.ai.title_processor')

        self.logger.info(
            f"Initialized TitleProcessor with {len(self.models)} models, "
            f"{max_workers} workers, auto_unload={auto_unload}"
        )

    def check_availability(self) -> Dict[str, bool]:
        """
        Check if Ollama is running and models are available.

        Returns:
            Dict mapping model names to availability status
        """
        if not self.client.is_available():
            self.logger.error("Ollama is not available")
            return {model: False for model in self.models}

        availability = {}
        for model in self.models:
            availability[model] = self.client.model_exists(model)

        unavailable = [m for m, avail in availability.items() if not avail]
        if unavailable:
            self.logger.warning(f"Models not available: {unavailable}")

        return availability

    def process_single_video(
        self,
        video_id: str,
        raw_title: str,
        uploader: str = "",
        description: str = ""
    ) -> List[ProcessingResult]:
        """
        Process a single video with all available models.

        Args:
            video_id: The YouTube video ID
            raw_title: The raw YouTube title
            uploader: The channel/uploader name
            description: Video description (optional)

        Returns:
            List of ProcessingResult objects, one per model attempted
        """
        self.logger.info(f"Processing video {video_id} with {len(self.models)} models")

        results = []
        user_prompt = build_user_prompt(raw_title, uploader, description)

        for model_name in self.models:
            result = self._process_with_model(
                video_id=video_id,
                model_name=model_name,
                user_prompt=user_prompt
            )
            results.append(result)

        success_count = sum(1 for r in results if r.success)
        self.logger.info(
            f"Video {video_id} processed: {success_count}/{len(results)} models succeeded"
        )

        return results

    def _process_with_model(
        self,
        video_id: str,
        model_name: str,
        user_prompt: str,
        keep_alive: Optional[str] = None
    ) -> ProcessingResult:
        """
        Process a video with a single model.

        Args:
            video_id: The YouTube video ID
            model_name: The model to use
            user_prompt: The formatted user prompt
            keep_alive: How long to keep model in VRAM (None = use auto_unload setting)

        Returns:
            ProcessingResult with the outcome
        """
        start_time = time.time()

        try:
            # Check model availability
            if not self.client.model_exists(model_name):
                return ProcessingResult(
                    video_id=video_id,
                    model_name=model_name,
                    success=False,
                    processing_time=time.time() - start_time,
                    error=f"Model {model_name} not available"
                )

            # Generate title
            response = self.client.generate_title(
                model=model_name,
                system_prompt=SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.7,
                keep_alive=keep_alive
            )

            if not response:
                return ProcessingResult(
                    video_id=video_id,
                    model_name=model_name,
                    success=False,
                    processing_time=time.time() - start_time,
                    error="Failed to get response from model"
                )

            # Validate response
            if not validate_response(response):
                self.logger.warning(
                    f"Invalid response from {model_name} for {video_id}"
                )
                return ProcessingResult(
                    video_id=video_id,
                    model_name=model_name,
                    success=False,
                    processing_time=time.time() - start_time,
                    error="Response validation failed"
                )

            # Normalize response
            normalized = normalize_response(response)

            # Create success result
            return ProcessingResult(
                video_id=video_id,
                model_name=model_name,
                success=True,
                title=normalized['title'],
                artist=normalized['artist'],
                cover_artist=normalized.get('cover_artist'),
                tags=json.dumps(normalized['tags']),  # Store as JSON string
                confidence=normalized['confidence'],
                processing_time=time.time() - start_time
            )

        except Exception as e:
            self.logger.error(
                f"Unexpected error processing {video_id} with {model_name}: {e}"
            )
            return ProcessingResult(
                video_id=video_id,
                model_name=model_name,
                success=False,
                processing_time=time.time() - start_time,
                error=str(e)
            )

    def process_batch(
        self,
        video_ids: List[str],
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Dict[str, List[ProcessingResult]]:
        """
        Process multiple videos using one model at a time.

        NEW STRATEGY: Instead of running all models for each video,
        we run ONE model for ALL videos, then move to the next model.
        This keeps one model in VRAM and is much faster.

        Args:
            video_ids: List of video IDs to process
            progress_callback: Optional callback(current, total, message)
                               called after each batch completes

        Returns:
            Dict mapping video_id to list of ProcessingResults
        """
        total_videos = len(video_ids)
        total_tasks = total_videos * len(self.models)
        completed_tasks = 0

        self.logger.info(
            f"Starting batch processing of {total_videos} videos with {len(self.models)} models"
        )
        self.logger.info("Using ONE-MODEL-AT-A-TIME strategy for faster processing")

        all_results = {video_id: [] for video_id in video_ids}

        # Fetch all video metadata once
        video_metadata = {}
        for video_id in video_ids:
            video = self.db.get_video(video_id)
            if not video:
                self.logger.warning(f"Video {video_id} not found in database")
                continue
            video_metadata[video_id] = video

        # Process ONE MODEL AT A TIME with parallel instances
        for model_idx, model_name in enumerate(self.models, 1):
            self.logger.info(
                f"Processing with model {model_idx}/{len(self.models)}: {model_name}"
            )

            # Check model availability before processing
            if not self.client.model_exists(model_name):
                self.logger.warning(f"Model {model_name} not available, skipping")
                for video_id in video_ids:
                    all_results[video_id].append(ProcessingResult(
                        video_id=video_id,
                        model_name=model_name,
                        success=False,
                        error=f"Model {model_name} not available"
                    ))
                completed_tasks += total_videos
                if progress_callback:
                    progress_callback(
                        completed_tasks,
                        total_tasks,
                        f"Skipped {model_name} (not available)"
                    )
                continue

            # Process all videos with THIS model in parallel
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_video = {}
                num_videos = len([v for v in video_ids if v in video_metadata])

                for i, video_id in enumerate(video_ids, 1):
                    if video_id not in video_metadata:
                        continue

                    video = video_metadata[video_id]
                    user_prompt = build_user_prompt(
                        raw_title=video['title'],
                        uploader=video.get('uploader', ''),
                        description=video.get('description', '')
                    )

                    # Keep model loaded during batch, unload after last video
                    if i < num_videos:
                        keep_alive = "5m"  # Keep loaded for next video
                    else:
                        keep_alive = None  # Use auto_unload setting for last one

                    future = executor.submit(
                        self._process_with_model,
                        video_id=video_id,
                        model_name=model_name,
                        user_prompt=user_prompt,
                        keep_alive=keep_alive
                    )
                    future_to_video[future] = video_id

                # Collect results as they complete
                for future in as_completed(future_to_video):
                    video_id = future_to_video[future]
                    completed_tasks += 1

                    try:
                        result = future.result()
                        all_results[video_id].append(result)

                        # Store result in database immediately
                        self._store_results([result])

                        if progress_callback:
                            progress_callback(
                                completed_tasks,
                                total_tasks,
                                f"[{model_name}] Processed {video_id}"
                            )

                    except Exception as e:
                        self.logger.error(
                            f"Failed to process {video_id} with {model_name}: {e}"
                        )
                        all_results[video_id].append(ProcessingResult(
                            video_id=video_id,
                            model_name=model_name,
                            success=False,
                            error=str(e)
                        ))

            # Explicitly unload model after completing all videos with this model
            if self.auto_unload:
                self.logger.info(f"Unloading {model_name} from VRAM...")
                self.client.unload_model(model_name)

            self.logger.info(
                f"Completed model {model_idx}/{len(self.models)}: {model_name}"
            )

        success_count = sum(
            1 for results in all_results.values()
            if any(r.success for r in results)
        )
        self.logger.info(
            f"Batch processing complete: {success_count}/{total_videos} videos "
            f"processed successfully"
        )
        return all_results

    def _store_results(self, results: List[ProcessingResult]) -> None:
        """
        Store processing results in the database.

        Args:
            results: List of ProcessingResult objects to store
        """
        for result in results:
            if result.success:
                try:
                    self.db.add_ai_attempt(
                        video_id=result.video_id,
                        model_name=result.model_name,
                        generated_title=result.title,
                        artist=result.artist,
                        cover_artist=result.cover_artist,
                        tags=result.tags,  # Already JSON string
                        confidence=result.confidence,
                        prompt_version=PROMPT_VERSION,
                        processing_time=result.processing_time
                    )
                    self.logger.debug(
                        f"Stored AI attempt for {result.video_id} "
                        f"from {result.model_name}"
                    )
                except Exception as e:
                    self.logger.error(
                        f"Failed to store AI attempt for {result.video_id}: {e}"
                    )
            else:
                self.logger.debug(
                    f"Skipping failed result for {result.video_id} "
                    f"from {result.model_name}: {result.error}"
                )

    def process_pending_videos(
        self,
        playlist_id: Optional[str] = None,
        limit: Optional[int] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Dict[str, List[ProcessingResult]]:
        """
        Process all videos that haven't been processed yet.

        Finds videos with download_status='downloaded' but no AI attempts,
        then processes them.

        Args:
            playlist_id: Optional playlist ID to filter by
            limit: Optional limit on number of videos to process
            progress_callback: Optional progress callback

        Returns:
            Dict mapping video_id to list of ProcessingResults
        """
        # Find videos that need processing
        if playlist_id:
            videos = self.db.get_playlist_videos(playlist_id)
            video_ids = [v['video_id'] for v in videos]
        else:
            # Get all downloaded videos
            # Note: This is a simplified version; you may want to add
            # a proper query to Database class for this
            video_ids = self._get_pending_video_ids()

        if limit:
            video_ids = video_ids[:limit]

        self.logger.info(f"Found {len(video_ids)} videos pending AI processing")

        if not video_ids:
            self.logger.info("No videos to process")
            return {}

        return self.process_batch(video_ids, progress_callback)

    def _get_pending_video_ids(self) -> List[str]:
        """
        Get list of video IDs that need AI processing.

        Returns videos that are downloaded but have no AI attempts yet.

        Returns:
            List of video IDs
        """
        try:
            # Query for videos with download_status='downloaded' and no AI attempts
            query = """
                SELECT v.video_id
                FROM videos v
                WHERE v.download_status = 'downloaded'
                AND NOT EXISTS (
                    SELECT 1 FROM ai_title_attempts a
                    WHERE a.video_id = v.video_id
                )
                ORDER BY v.extraction_date DESC
            """

            cursor = self.db.conn.cursor()
            cursor.execute(query)
            results = cursor.fetchall()

            video_ids = [row[0] for row in results]
            return video_ids

        except Exception as e:
            self.logger.error(f"Failed to get pending video IDs: {e}")
            return []

    def regenerate_for_video(
        self,
        video_id: str,
        models: Optional[List[str]] = None
    ) -> List[ProcessingResult]:
        """
        Regenerate AI attempts for a specific video.

        This is useful when the user is not satisfied with existing attempts
        and wants to try again with different models.

        Args:
            video_id: The video ID to regenerate for
            models: Optional list of specific models to use (defaults to all)

        Returns:
            List of new ProcessingResult objects
        """
        video = self.db.get_video(video_id)
        if not video:
            self.logger.error(f"Video {video_id} not found")
            return []

        # Use specified models or default to all
        models_to_use = models or self.models
        self.logger.info(
            f"Regenerating AI attempts for {video_id} with {len(models_to_use)} models"
        )

        # Temporarily override models
        original_models = self.models
        self.models = models_to_use

        results = self.process_single_video(
            video_id=video_id,
            raw_title=video['title'],
            uploader=video.get('uploader', ''),
            description=video.get('description', '')
        )

        # Store new results
        self._store_results(results)

        # Restore original models
        self.models = original_models

        return results

    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Get statistics about AI processing.

        Returns:
            Dict with statistics:
            - total_videos: Total videos in database
            - downloaded_videos: Videos with download_status='downloaded'
            - processed_videos: Videos with at least one AI attempt
            - pending_videos: Downloaded but not processed
            - total_attempts: Total AI attempts across all videos
            - attempts_by_model: Dict of attempt counts per model
        """
        try:
            stats = {}

            # Total videos
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM videos")
            stats['total_videos'] = cursor.fetchone()[0]

            # Downloaded videos
            cursor.execute("SELECT COUNT(*) FROM videos WHERE download_status = 'downloaded'")
            stats['downloaded_videos'] = cursor.fetchone()[0]

            # Processed videos (with AI attempts)
            cursor.execute("""
                SELECT COUNT(DISTINCT video_id) FROM ai_title_attempts
            """)
            stats['processed_videos'] = cursor.fetchone()[0]

            # Pending videos
            stats['pending_videos'] = stats['downloaded_videos'] - stats['processed_videos']

            # Total attempts
            cursor.execute("SELECT COUNT(*) FROM ai_title_attempts")
            stats['total_attempts'] = cursor.fetchone()[0]

            # Attempts by model
            cursor.execute("""
                SELECT model_name, COUNT(*) as count
                FROM ai_title_attempts
                GROUP BY model_name
            """)
            stats['attempts_by_model'] = {
                row[0]: row[1] for row in cursor.fetchall()
            }

            return stats

        except Exception as e:
            self.logger.error(f"Failed to get processing stats: {e}")
            return {}


# Example usage and testing
if __name__ == "__main__":
    import sys
    from pathlib import Path

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Initialize database
    db = Database()

    # Initialize processor
    processor = TitleProcessor(db=db)

    # Check availability
    print("=== Checking Ollama Availability ===")
    availability = processor.check_availability()
    for model, available in availability.items():
        status = "✓" if available else "✗"
        print(f"{status} {model}")
    print()

    # Get stats
    print("=== Processing Statistics ===")
    stats = processor.get_processing_stats()
    print(f"Total videos: {stats.get('total_videos', 0)}")
    print(f"Downloaded: {stats.get('downloaded_videos', 0)}")
    print(f"Processed: {stats.get('processed_videos', 0)}")
    print(f"Pending: {stats.get('pending_videos', 0)}")
    print(f"Total AI attempts: {stats.get('total_attempts', 0)}")
    print()

    if stats.get('attempts_by_model'):
        print("Attempts by model:")
        for model, count in stats['attempts_by_model'].items():
            print(f"  - {model}: {count}")
    print()

    # Test with a single video if available
    pending_ids = processor._get_pending_video_ids()
    if pending_ids:
        print(f"=== Testing with video: {pending_ids[0]} ===")

        def progress(current, total, video_id):
            print(f"Progress: {current}/{total} - {video_id}")

        results = processor.process_batch([pending_ids[0]], progress_callback=progress)

        if pending_ids[0] in results:
            print("\nResults:")
            for result in results[pending_ids[0]]:
                if result.success:
                    print(f"  ✓ {result.model_name}: {result.title} by {result.artist}")
                    print(f"    Confidence: {result.confidence:.1%}, Time: {result.processing_time:.2f}s")
                else:
                    print(f"  ✗ {result.model_name}: {result.error}")
    else:
        print("No pending videos to test with.")
        print("Download some videos first using the Phase 2 downloader.")

    # Close database
    db.close()
