"""
External AI Export/Import for Music DLP.

Allows users to export video metadata as structured files for processing
by any external AI (ChatGPT, Claude, Gemini, etc.), then import the
results back into the database as AI attempts.

Two files generated per batch:
  - .json: Structured data with blank response slots
  - .txt: Ready-to-paste prompt for any AI chatbot

Two import formats auto-detected:
  - Format A: Filled-in export JSON (music_dlp_export wrapper)
  - Format B: Standalone JSON array (raw AI chatbot output)
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from ai.prompts_v4 import SYSTEM_PROMPT_V4, validate_response_v4, normalize_response_v4

logger = logging.getLogger(__name__)


def export_for_external_ai(
    db,
    output_dir: str,
    video_ids: List[str],
    batch_size: int = 20
) -> List[str]:
    """Export video metadata as JSON + prompt files for external AI processing.

    Args:
        db: Database instance
        output_dir: Directory to write export files
        video_ids: List of video IDs to export
        batch_size: Max videos per batch file pair

    Returns:
        List of generated file paths
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Gather video metadata
    videos = []
    for vid in video_ids:
        video = db.get_video(vid)
        if video and video.get('download_status') == 'downloaded':
            videos.append(video)

    if not videos:
        logger.warning("No eligible videos to export")
        return []

    # Split into batches
    batches = [videos[i:i + batch_size] for i in range(0, len(videos), batch_size)]
    total_batches = len(batches)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    generated_files = []

    for batch_idx, batch in enumerate(batches, 1):
        # Build file suffix
        if total_batches == 1:
            suffix = ""
        else:
            suffix = f"_batch{batch_idx}"

        json_filename = f"music_dlp_export_{timestamp}{suffix}.json"
        txt_filename = f"music_dlp_prompt_{timestamp}{suffix}.txt"

        json_path = output_path / json_filename
        txt_path = output_path / txt_filename

        # Build JSON export
        export_data = {
            "music_dlp_export": {
                "version": "1.0",
                "export_date": datetime.now().isoformat(),
                "batch": batch_idx,
                "total_batches": total_batches,
                "total_videos": len(batch),
                "videos": []
            }
        }

        for video in batch:
            export_data["music_dlp_export"]["videos"].append({
                "video_id": video["video_id"],
                "raw_title": video["title"],
                "uploader": video.get("uploader", ""),
                "response": None
            })

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        # Build TXT prompt
        prompt_lines = [
            SYSTEM_PROMPT_V4.strip(),
            "",
            "---",
            "",
            "Process the following YouTube videos and return ONLY a JSON array.",
            "For each video, provide a JSON object with these fields:",
            "",
            '{',
            '  "video_id": "the YouTube video ID (provided below)",',
            '  "title": "Clean song title (romanized if Japanese)",',
            '  "artist": "ORIGINAL artist/composer who created the song",',
            '  "cover_artist": "Person who performed/covered it (often the Uploader)",',
            '  "tags": ["cover", "vocaloid", ...],',
            '  "confidence": 0.0-1.0',
            '}',
            "",
            "IMPORTANT - artist vs cover_artist:",
            '- "artist" = the ORIGINAL creator of the song (composer/producer)',
            '- "cover_artist" = the person performing/singing it in this video',
            "- The Uploader shown below is usually the cover artist",
            '- For covers: artist and cover_artist will be DIFFERENT people',
            '- For original songs: set cover_artist to null',
            '- Example: If a VTuber covers a YOASOBI song, artist="YOASOBI", cover_artist="VTuber Name"',
            ""
        ]

        for i, video in enumerate(batch, 1):
            prompt_lines.append(f"Video {i} (ID: {video['video_id']}):")
            prompt_lines.append(f'  Title: "{video["title"]}"')
            uploader = video.get("uploader", "")
            if uploader:
                prompt_lines.append(f'  Uploader: "{uploader}"')
            prompt_lines.append("")

        prompt_lines.append("Respond with ONLY a valid JSON array, no other text.")

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(prompt_lines))

        generated_files.extend([str(json_path), str(txt_path)])
        logger.info(f"Exported batch {batch_idx}/{total_batches}: {json_filename}, {txt_filename}")

    logger.info(f"Export complete: {len(videos)} videos in {total_batches} batch(es)")
    return generated_files


def import_external_ai_results(
    db,
    file_path: str
) -> Dict[str, Any]:
    """Import AI results from an external AI JSON file.

    Auto-detects two formats:
      Format A: {"music_dlp_export": {"videos": [{"video_id":..., "response":{...}}]}}
      Format B: [{"video_id":..., "title":..., "artist":..., ...}]

    Args:
        db: Database instance
        file_path: Path to the JSON file to import

    Returns:
        Summary dict: {"imported": N, "skipped": N, "errors": [...]}
    """
    summary = {"imported": 0, "skipped": 0, "errors": []}

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        summary["errors"].append(f"Invalid JSON: {e}")
        return summary
    except OSError as e:
        summary["errors"].append(f"File read error: {e}")
        return summary

    return _process_import_data(db, data, summary)


def import_external_ai_from_text(
    db,
    text: str
) -> Dict[str, Any]:
    """Import AI results from pasted text (JSON string).

    Same format detection as import_external_ai_results but accepts
    raw text instead of a file path.

    Args:
        db: Database instance
        text: JSON string (pasted from AI chatbot)

    Returns:
        Summary dict: {"imported": N, "skipped": N, "errors": [...]}
    """
    summary = {"imported": 0, "skipped": 0, "errors": []}

    # Strip markdown code fences that AI chatbots often wrap around JSON
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # Remove first line (```json or ```) and last line (```)
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        summary["errors"].append(f"Invalid JSON: {e}")
        return summary

    return _process_import_data(db, data, summary)


def _process_import_data(
    db,
    data: Any,
    summary: Dict[str, Any]
) -> Dict[str, Any]:
    """Shared logic for importing parsed JSON data into the database.

    Args:
        db: Database instance
        data: Parsed JSON (dict or list)
        summary: Summary dict to populate

    Returns:
        Updated summary dict
    """
    responses = _extract_responses(data, summary)

    if not responses:
        if not summary["errors"]:
            summary["errors"].append("No valid responses found")
        return summary

    for resp in responses:
        video_id = resp.get("video_id")
        if not video_id:
            summary["errors"].append("Response missing video_id, skipped")
            summary["skipped"] += 1
            continue

        video = db.get_video(video_id)
        if not video:
            summary["errors"].append(f"{video_id}: not found in database, skipped")
            summary["skipped"] += 1
            continue

        if not validate_response_v4(resp):
            summary["errors"].append(f"{video_id}: invalid response format, skipped")
            summary["skipped"] += 1
            continue

        normalized = normalize_response_v4(resp)

        attempt_id = db.add_ai_attempt(
            video_id=video_id,
            model_name="external",
            generated_title=normalized["title"],
            artist=normalized["artist"],
            cover_artist=normalized.get("cover_artist"),
            tags=normalized["tags"],
            confidence=normalized["confidence"],
            prompt_version="4.0-external",
            processing_time=0.0
        )

        if attempt_id:
            summary["imported"] += 1
            logger.info(f"Imported: {video_id} -> {normalized['title']} by {normalized['artist']}")
        else:
            summary["errors"].append(f"{video_id}: database insert failed")
            summary["skipped"] += 1

    logger.info(
        f"Import complete: {summary['imported']} imported, "
        f"{summary['skipped']} skipped, {len(summary['errors'])} errors"
    )
    return summary


def _extract_responses(data: Any, summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract response dicts from either import format.

    Args:
        data: Parsed JSON data (dict or list)
        summary: Summary dict to append errors to

    Returns:
        List of response dicts, each containing video_id + metadata fields
    """
    # Format B: standalone JSON array
    if isinstance(data, list):
        return data

    # Format A: filled-in export JSON
    if isinstance(data, dict) and "music_dlp_export" in data:
        export = data["music_dlp_export"]
        videos = export.get("videos", [])
        responses = []
        for entry in videos:
            resp = entry.get("response")
            if resp and isinstance(resp, dict):
                # Carry forward video_id from the wrapper
                if "video_id" not in resp:
                    resp["video_id"] = entry.get("video_id")
                responses.append(resp)
        return responses

    summary["errors"].append("Unrecognized file format (expected JSON array or music_dlp_export object)")
    return []
