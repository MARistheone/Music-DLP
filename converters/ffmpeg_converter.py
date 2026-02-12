"""
FFmpeg Converter Module

Handles audio file conversion from Opus to MP3 and M4A formats using FFmpeg.

Key Features:
- Convert Opus to MP3 (320kbps with libmp3lame)
- Convert Opus to M4A/AAC (320kbps)
- Audio normalization support
- Progress tracking for GUI integration
- Comprehensive error handling
- File validation

Usage:
    from converters import FFmpegConverter

    converter = FFmpegConverter()
    success, error = converter.convert_to_mp3(
        input_file='downloads/raw/[VIDEO_ID].opus',
        output_file='downloads/final/Artist - Title.mp3'
    )
"""

import subprocess
import shutil
import sys
import os
import json
import re
from pathlib import Path
from typing import Optional, Tuple, Callable
import logging
import time

import ffmpeg


class FFmpegConverter:
    """
    FFmpeg-based audio converter.

    Converts Opus audio files to MP3 and M4A formats with configurable bitrates.
    Includes progress tracking and error handling.
    """

    def __init__(
        self,
        mp3_bitrate: str = '320k',
        m4a_bitrate: str = '320k',
        normalize_audio: bool = True,
        loudnorm_target_i: float = -14.0,
        loudnorm_true_peak: float = -1.0,
        loudnorm_lra: float = 11.0,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize FFmpeg converter.

        Args:
            mp3_bitrate: Bitrate for MP3 encoding (default: 320k)
            m4a_bitrate: Bitrate for M4A/AAC encoding (default: 320k)
            normalize_audio: Whether to apply audio normalization (default: True)
            loudnorm_target_i: Target integrated loudness in LUFS (default: -14.0 for Spotify)
            loudnorm_true_peak: True peak ceiling in dBTP (default: -1.0 for Spotify)
            loudnorm_lra: Loudness range target (default: 11.0)
            logger: Logger instance (if None, creates new logger)
        """
        self.mp3_bitrate = mp3_bitrate
        self.m4a_bitrate = m4a_bitrate
        self.normalize_audio = normalize_audio
        self.loudnorm_target_i = loudnorm_target_i
        self.loudnorm_true_peak = loudnorm_true_peak
        self.loudnorm_lra = loudnorm_lra

        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger('ffmpeg_converter')
            if not self.logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter('[%(levelname)s] %(asctime)s - %(message)s', datefmt='%H:%M:%S')
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
                self.logger.setLevel(logging.INFO)

        # Check FFmpeg availability
        self._check_ffmpeg()

    def _check_ffmpeg(self) -> None:
        """
        Check if FFmpeg is available (app-adjacent dirs first, then PATH).

        Raises:
            RuntimeError: If FFmpeg is not found
        """
        # Check app-adjacent directories for portable FFmpeg
        if getattr(sys, 'frozen', False):
            base_dir = Path(sys.executable).parent
        else:
            base_dir = Path.cwd()

        for candidate in [base_dir / 'ffmpeg.exe', base_dir / 'ffmpeg' / 'ffmpeg.exe']:
            if candidate.exists():
                ffmpeg_dir = str(candidate.parent)
                if ffmpeg_dir not in os.environ.get('PATH', ''):
                    os.environ['PATH'] = ffmpeg_dir + os.pathsep + os.environ.get('PATH', '')
                self.logger.debug(f"FFmpeg found at: {candidate}")
                return

        if shutil.which('ffmpeg'):
            self.logger.debug("FFmpeg found in system PATH")
            return

        raise RuntimeError(
            "FFmpeg not found. Please either:\n"
            "1. Place ffmpeg.exe next to MusicDLP.exe\n"
            "2. Place it in a 'ffmpeg' subfolder\n"
            "3. Install FFmpeg and add to system PATH\n\n"
            "Download from: https://ffmpeg.org/download.html"
        )

    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to remove invalid characters.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename safe for filesystem
        """
        # Replace invalid characters with underscores
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')

        # Remove leading/trailing spaces and dots
        filename = filename.strip('. ')

        # Limit length (Windows MAX_PATH consideration)
        if len(filename) > 200:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:200] + (f'.{ext}' if ext else '')

        return filename

    def _measure_loudness(self, input_file: Path) -> Optional[dict]:
        """
        Pass 1 of two-pass loudnorm: measure the input file's loudness.

        Runs FFmpeg with the loudnorm filter to null output, capturing the
        JSON measurement stats from stderr. These stats are then fed into
        pass 2 for precise, linear normalization.

        Args:
            input_file: Path to input audio file

        Returns:
            Dictionary with measured loudness stats, or None on failure.
            Keys: input_i, input_tp, input_lra, input_thresh, target_offset
        """
        input_file = Path(input_file)
        self.logger.info(f"Measuring loudness (pass 1): {input_file.name}")

        loudnorm_filter = (
            f"loudnorm="
            f"I={self.loudnorm_target_i}:"
            f"TP={self.loudnorm_true_peak}:"
            f"LRA={self.loudnorm_lra}:"
            f"print_format=json"
        )

        cmd = [
            'ffmpeg', '-i', str(input_file),
            '-af', loudnorm_filter,
            '-f', 'null', '-'
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )

            stderr = result.stderr

            # The loudnorm JSON block is at the end of stderr output.
            # Find the last JSON object in the output.
            json_match = re.search(
                r'\{[^{}]*"input_i"[^{}]*\}',
                stderr,
                re.DOTALL
            )

            if not json_match:
                self.logger.error("Could not find loudnorm JSON in FFmpeg output")
                return None

            stats = json.loads(json_match.group())

            self.logger.info(
                f"Loudness measured: "
                f"I={stats.get('input_i')} LUFS, "
                f"TP={stats.get('input_tp')} dBTP, "
                f"LRA={stats.get('input_lra')}"
            )

            return stats

        except subprocess.TimeoutExpired:
            self.logger.error(f"Loudness measurement timed out for {input_file.name}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse loudnorm JSON: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Loudness measurement failed: {e}")
            return None

    def _apply_two_pass_loudnorm(self, stream, loudness_stats: dict):
        """
        Pass 2 of two-pass loudnorm: apply measured values for precise normalization.

        Uses linear mode to avoid dynamic compression artifacts.

        Args:
            stream: ffmpeg input stream
            loudness_stats: Dictionary from _measure_loudness()

        Returns:
            ffmpeg stream with loudnorm filter applied
        """
        return stream.filter(
            'loudnorm',
            I=self.loudnorm_target_i,
            TP=self.loudnorm_true_peak,
            LRA=self.loudnorm_lra,
            measured_I=loudness_stats['input_i'],
            measured_TP=loudness_stats['input_tp'],
            measured_LRA=loudness_stats['input_lra'],
            measured_thresh=loudness_stats['input_thresh'],
            offset=loudness_stats['target_offset'],
            linear='true'
        )

    def convert_to_mp3(
        self,
        input_file: Path,
        output_file: Path,
        progress_callback: Optional[Callable[[float], None]] = None,
        loudness_stats: Optional[dict] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Convert Opus audio to MP3 format.

        Args:
            input_file: Path to input .opus file
            output_file: Path to output .mp3 file
            progress_callback: Optional callback for progress updates (0.0-1.0)
            loudness_stats: Pre-measured loudness stats from _measure_loudness().
                            If None and normalize_audio is True, will measure automatically.

        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        input_file = Path(input_file)
        output_file = Path(output_file)

        # Validate input
        if not input_file.exists():
            error_msg = f"Input file not found: {input_file}"
            self.logger.error(error_msg)
            return False, error_msg

        # Create output directory
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Sanitize output filename
        sanitized_name = self._sanitize_filename(output_file.name)
        output_file = output_file.parent / sanitized_name

        self.logger.info(f"Converting to MP3: {input_file.name} -> {output_file.name}")

        try:
            start_time = time.time()

            # Build FFmpeg command
            stream = ffmpeg.input(str(input_file))

            # Apply two-pass audio normalization if enabled
            if self.normalize_audio:
                if loudness_stats is None:
                    loudness_stats = self._measure_loudness(input_file)

                if loudness_stats:
                    stream = self._apply_two_pass_loudnorm(stream, loudness_stats)
                else:
                    self.logger.warning(
                        "Loudness measurement failed, converting without normalization"
                    )

            # Output settings for MP3
            stream = ffmpeg.output(
                stream,
                str(output_file),
                acodec='libmp3lame',
                audio_bitrate=self.mp3_bitrate,
                ar='48000',  # Sample rate 48kHz
                map_metadata='0',  # Preserve metadata from source
                loglevel='warning'
            )

            # Run conversion (pass 2)
            ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)

            # Validate output
            if not output_file.exists() or output_file.stat().st_size == 0:
                error_msg = "Conversion produced empty or missing file"
                self.logger.error(error_msg)
                return False, error_msg

            elapsed = time.time() - start_time
            file_size_mb = output_file.stat().st_size / (1024 * 1024)
            self.logger.info(
                f"MP3 conversion complete: {output_file.name} "
                f"({file_size_mb:.2f} MB in {elapsed:.1f}s)"
            )

            if progress_callback:
                progress_callback(1.0)

            return True, None

        except ffmpeg.Error as e:
            error_msg = f"FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

        except Exception as e:
            error_msg = f"Unexpected error during MP3 conversion: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def convert_to_m4a(
        self,
        input_file: Path,
        output_file: Path,
        progress_callback: Optional[Callable[[float], None]] = None,
        loudness_stats: Optional[dict] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Convert Opus audio to M4A/AAC format.

        Args:
            input_file: Path to input .opus file
            output_file: Path to output .m4a file
            progress_callback: Optional callback for progress updates (0.0-1.0)
            loudness_stats: Pre-measured loudness stats from _measure_loudness().
                            If None and normalize_audio is True, will measure automatically.

        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        input_file = Path(input_file)
        output_file = Path(output_file)

        # Validate input
        if not input_file.exists():
            error_msg = f"Input file not found: {input_file}"
            self.logger.error(error_msg)
            return False, error_msg

        # Create output directory
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Sanitize output filename
        sanitized_name = self._sanitize_filename(output_file.name)
        output_file = output_file.parent / sanitized_name

        self.logger.info(f"Converting to M4A: {input_file.name} -> {output_file.name}")

        try:
            start_time = time.time()

            # Build FFmpeg command
            stream = ffmpeg.input(str(input_file))

            # Apply two-pass audio normalization if enabled
            if self.normalize_audio:
                if loudness_stats is None:
                    loudness_stats = self._measure_loudness(input_file)

                if loudness_stats:
                    stream = self._apply_two_pass_loudnorm(stream, loudness_stats)
                else:
                    self.logger.warning(
                        "Loudness measurement failed, converting without normalization"
                    )

            # Output settings for M4A/AAC
            stream = ffmpeg.output(
                stream,
                str(output_file),
                acodec='aac',
                audio_bitrate=self.m4a_bitrate,
                ar='48000',  # Sample rate 48kHz
                map_metadata='0',  # Preserve metadata from source
                loglevel='warning'
            )

            # Run conversion (pass 2)
            ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)

            # Validate output
            if not output_file.exists() or output_file.stat().st_size == 0:
                error_msg = "Conversion produced empty or missing file"
                self.logger.error(error_msg)
                return False, error_msg

            elapsed = time.time() - start_time
            file_size_mb = output_file.stat().st_size / (1024 * 1024)
            self.logger.info(
                f"M4A conversion complete: {output_file.name} "
                f"({file_size_mb:.2f} MB in {elapsed:.1f}s)"
            )

            if progress_callback:
                progress_callback(1.0)

            return True, None

        except ffmpeg.Error as e:
            error_msg = f"FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

        except Exception as e:
            error_msg = f"Unexpected error during M4A conversion: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def convert_both_formats(
        self,
        input_file: Path,
        output_mp3: Path,
        output_m4a: Path,
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> Tuple[bool, bool, Optional[str], Optional[str]]:
        """
        Convert Opus to both MP3 and M4A formats.

        Args:
            input_file: Path to input .opus file
            output_mp3: Path to output .mp3 file
            output_m4a: Path to output .m4a file
            progress_callback: Optional callback with (format, progress) args

        Returns:
            Tuple of (mp3_success, m4a_success, mp3_error, m4a_error)
        """
        self.logger.info(f"Converting to both formats: {Path(input_file).name}")

        # Measure loudness once for both conversions (avoids redundant pass 1)
        loudness_stats = None
        if self.normalize_audio:
            loudness_stats = self._measure_loudness(input_file)
            if not loudness_stats:
                self.logger.warning(
                    "Loudness measurement failed, both formats will convert without normalization"
                )

        # Convert to MP3
        mp3_callback = None
        if progress_callback:
            mp3_callback = lambda p: progress_callback('mp3', p)

        mp3_success, mp3_error = self.convert_to_mp3(
            input_file,
            output_mp3,
            mp3_callback,
            loudness_stats=loudness_stats
        )

        # Convert to M4A
        m4a_callback = None
        if progress_callback:
            m4a_callback = lambda p: progress_callback('m4a', p)

        m4a_success, m4a_error = self.convert_to_m4a(
            input_file,
            output_m4a,
            m4a_callback,
            loudness_stats=loudness_stats
        )

        if mp3_success and m4a_success:
            self.logger.info("Both conversions successful")
        elif mp3_success:
            self.logger.warning(f"MP3 conversion succeeded, but M4A failed: {m4a_error}")
        elif m4a_success:
            self.logger.warning(f"M4A conversion succeeded, but MP3 failed: {mp3_error}")
        else:
            self.logger.error("Both conversions failed")

        return mp3_success, m4a_success, mp3_error, m4a_error

    def get_audio_info(self, file_path: Path) -> Optional[dict]:
        """
        Get audio file information using ffprobe.

        Args:
            file_path: Path to audio file

        Returns:
            Dictionary with audio info, or None if probe fails
        """
        file_path = Path(file_path)

        if not file_path.exists():
            self.logger.error(f"File not found: {file_path}")
            return None

        try:
            probe = ffmpeg.probe(str(file_path))

            # Extract audio stream info
            audio_stream = next(
                (s for s in probe['streams'] if s['codec_type'] == 'audio'),
                None
            )

            if not audio_stream:
                self.logger.error(f"No audio stream found in {file_path}")
                return None

            info = {
                'codec': audio_stream.get('codec_name'),
                'bitrate': audio_stream.get('bit_rate'),
                'sample_rate': audio_stream.get('sample_rate'),
                'channels': audio_stream.get('channels'),
                'duration': float(probe['format'].get('duration', 0)),
                'size': int(probe['format'].get('size', 0))
            }

            return info

        except ffmpeg.Error as e:
            self.logger.error(f"FFprobe error: {e.stderr.decode() if e.stderr else str(e)}")
            return None

        except Exception as e:
            self.logger.error(f"Unexpected error getting audio info: {str(e)}")
            return None

    def validate_conversion(
        self,
        input_file: Path,
        output_file: Path,
        expected_codec: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that conversion was successful.

        Args:
            input_file: Original input file
            output_file: Converted output file
            expected_codec: Expected codec name (e.g., 'mp3', 'aac')

        Returns:
            Tuple of (is_valid: bool, error_message: Optional[str])
        """
        # Check output file exists
        output_file = Path(output_file)
        if not output_file.exists():
            return False, "Output file does not exist"

        # Check file size
        if output_file.stat().st_size == 0:
            return False, "Output file is empty"

        # Get audio info
        info = self.get_audio_info(output_file)
        if not info:
            return False, "Could not probe output file"

        # Validate codec
        if info['codec'] != expected_codec:
            return False, f"Expected codec {expected_codec}, got {info['codec']}"

        # Compare duration with input (within 1 second tolerance)
        input_info = self.get_audio_info(input_file)
        if input_info:
            duration_diff = abs(info['duration'] - input_info['duration'])
            if duration_diff > 1.0:
                return False, f"Duration mismatch: {duration_diff:.1f}s difference"

        self.logger.debug(f"Validation passed for {output_file.name}")
        return True, None
