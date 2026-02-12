"""
Metadata Embedder Module

Handles embedding metadata (title, artist, album, artwork) into MP3 and M4A audio files.

Key Features:
- Embed ID3 tags in MP3 files (mutagen.id3)
- Embed MP4 atoms in M4A files (mutagen.mp4)
- Embed album artwork (300x300 JPEG)
- Validate embedded metadata
- Database integration for approved metadata

Metadata Fields:
- Title (TIT2 for MP3, \xa9nam for M4A)
- Artist (TPE1 for MP3, \xa9ART for M4A)
- Album (TALB for MP3, \xa9alb for M4A)
- Album Art (APIC for MP3, covr for M4A)

Usage:
    from converters import MetadataEmbedder

    embedder = MetadataEmbedder()
    success, error = embedder.embed_mp3_metadata(
        file_path='downloads/final/Artist - Title.mp3',
        metadata={'title': 'Title', 'artist': 'Artist'},
        thumbnail_path='downloads/raw/[VIDEO_ID]_thumb.jpg'
    )
"""

import json
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import logging

from mutagen.mp3 import MP3
from mutagen.mp4 import MP4, MP4Cover
from mutagen.id3 import ID3, TIT2, TPE1, TALB, APIC, COMM
from mutagen import File as MutagenFile
from PIL import Image


class MetadataEmbedder:
    """
    Metadata embedding handler for MP3 and M4A files.

    Uses mutagen library to embed ID3 tags (MP3) and MP4 atoms (M4A).
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize metadata embedder.

        Args:
            logger: Logger instance (if None, creates new logger)
        """
        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger('metadata_embedder')
            if not self.logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter('[%(levelname)s] %(asctime)s - %(message)s', datefmt='%H:%M:%S')
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
                self.logger.setLevel(logging.INFO)

    def _validate_thumbnail(self, thumbnail_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Validate thumbnail image.

        Args:
            thumbnail_path: Path to thumbnail image

        Returns:
            Tuple of (is_valid: bool, error_message: Optional[str])
        """
        thumbnail_path = Path(thumbnail_path)

        if not thumbnail_path.exists():
            return False, f"Thumbnail not found: {thumbnail_path}"

        try:
            with Image.open(thumbnail_path) as img:
                # Check if it's a valid image
                img.verify()

                # Reopen to get size (verify() closes the image)
                with Image.open(thumbnail_path) as img_check:
                    width, height = img_check.size

                    # Warn if not 300x300
                    if width != 300 or height != 300:
                        self.logger.warning(
                            f"Thumbnail is {width}x{height}, expected 300x300. "
                            "Consider using thumbnail_processor to resize."
                        )

            return True, None

        except Exception as e:
            return False, f"Invalid thumbnail image: {str(e)}"

    def embed_mp3_metadata(
        self,
        file_path: Path,
        metadata: Dict[str, Any],
        thumbnail_path: Optional[Path] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Embed metadata into MP3 file using ID3 tags.

        Args:
            file_path: Path to MP3 file
            metadata: Dictionary with keys: title, artist, album (optional), tags (optional)
            thumbnail_path: Path to thumbnail image (300x300 JPEG recommended)

        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        file_path = Path(file_path)

        # Validate file exists
        if not file_path.exists():
            error_msg = f"MP3 file not found: {file_path}"
            self.logger.error(error_msg)
            return False, error_msg

        # Validate required metadata
        if 'title' not in metadata or 'artist' not in metadata:
            error_msg = "Metadata must contain 'title' and 'artist'"
            self.logger.error(error_msg)
            return False, error_msg

        self.logger.info(f"Embedding MP3 metadata: {file_path.name}")

        try:
            # Load MP3 file
            audio = MP3(file_path, ID3=ID3)

            # Add ID3v2 tag if not present
            if audio.tags is None:
                audio.add_tags()

            # Clear existing tags to avoid conflicts
            audio.tags.clear()

            # Embed title (TIT2)
            audio.tags.add(
                TIT2(encoding=3, text=metadata['title'])
            )
            self.logger.debug(f"  Title: {metadata['title']}")

            # Embed artist (TPE1)
            audio.tags.add(
                TPE1(encoding=3, text=metadata['artist'])
            )
            self.logger.debug(f"  Artist: {metadata['artist']}")

            # Embed album if provided (TALB)
            if 'album' in metadata and metadata['album']:
                audio.tags.add(
                    TALB(encoding=3, text=metadata['album'])
                )
                self.logger.debug(f"  Album: {metadata['album']}")

            # Embed tags as comment if provided (COMM)
            if 'tags' in metadata and metadata['tags']:
                tags_str = ', '.join(metadata['tags']) if isinstance(metadata['tags'], list) else metadata['tags']
                audio.tags.add(
                    COMM(encoding=3, lang='eng', desc='Tags', text=tags_str)
                )
                self.logger.debug(f"  Tags: {tags_str}")

            # Embed album artwork if provided (APIC)
            if thumbnail_path:
                thumbnail_path = Path(thumbnail_path)

                # Validate thumbnail
                is_valid, error_msg = self._validate_thumbnail(thumbnail_path)
                if not is_valid:
                    self.logger.warning(f"Thumbnail validation failed: {error_msg}")
                else:
                    with open(thumbnail_path, 'rb') as img:
                        audio.tags.add(
                            APIC(
                                encoding=3,
                                mime='image/jpeg',
                                type=3,  # Cover (front)
                                desc='Cover',
                                data=img.read()
                            )
                        )
                    self.logger.debug(f"  Album art: {thumbnail_path.name}")

            # Save changes
            audio.save(v2_version=3)  # Use ID3v2.3 for better compatibility

            self.logger.info(f"MP3 metadata embedded successfully: {file_path.name}")
            return True, None

        except Exception as e:
            error_msg = f"Error embedding MP3 metadata: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def embed_m4a_metadata(
        self,
        file_path: Path,
        metadata: Dict[str, Any],
        thumbnail_path: Optional[Path] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Embed metadata into M4A file using MP4 atoms.

        Args:
            file_path: Path to M4A file
            metadata: Dictionary with keys: title, artist, album (optional), tags (optional)
            thumbnail_path: Path to thumbnail image (300x300 JPEG recommended)

        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        file_path = Path(file_path)

        # Validate file exists
        if not file_path.exists():
            error_msg = f"M4A file not found: {file_path}"
            self.logger.error(error_msg)
            return False, error_msg

        # Validate required metadata
        if 'title' not in metadata or 'artist' not in metadata:
            error_msg = "Metadata must contain 'title' and 'artist'"
            self.logger.error(error_msg)
            return False, error_msg

        self.logger.info(f"Embedding M4A metadata: {file_path.name}")

        try:
            # Load M4A file
            audio = MP4(file_path)

            # Embed title (\xa9nam)
            audio['\xa9nam'] = metadata['title']
            self.logger.debug(f"  Title: {metadata['title']}")

            # Embed artist (\xa9ART)
            audio['\xa9ART'] = metadata['artist']
            self.logger.debug(f"  Artist: {metadata['artist']}")

            # Embed album if provided (\xa9alb)
            if 'album' in metadata and metadata['album']:
                audio['\xa9alb'] = metadata['album']
                self.logger.debug(f"  Album: {metadata['album']}")

            # Embed tags as comment if provided (\xa9cmt)
            if 'tags' in metadata and metadata['tags']:
                tags_str = ', '.join(metadata['tags']) if isinstance(metadata['tags'], list) else metadata['tags']
                audio['\xa9cmt'] = tags_str
                self.logger.debug(f"  Tags: {tags_str}")

            # Embed album artwork if provided (covr)
            if thumbnail_path:
                thumbnail_path = Path(thumbnail_path)

                # Validate thumbnail
                is_valid, error_msg = self._validate_thumbnail(thumbnail_path)
                if not is_valid:
                    self.logger.warning(f"Thumbnail validation failed: {error_msg}")
                else:
                    with open(thumbnail_path, 'rb') as img:
                        audio['covr'] = [
                            MP4Cover(img.read(), imageformat=MP4Cover.FORMAT_JPEG)
                        ]
                    self.logger.debug(f"  Album art: {thumbnail_path.name}")

            # Save changes
            audio.save()

            self.logger.info(f"M4A metadata embedded successfully: {file_path.name}")
            return True, None

        except Exception as e:
            error_msg = f"Error embedding M4A metadata: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def embed_both_formats(
        self,
        mp3_file: Path,
        m4a_file: Path,
        metadata: Dict[str, Any],
        thumbnail_path: Optional[Path] = None
    ) -> Tuple[bool, bool, Optional[str], Optional[str]]:
        """
        Embed metadata into both MP3 and M4A files.

        Args:
            mp3_file: Path to MP3 file
            m4a_file: Path to M4A file
            metadata: Dictionary with metadata
            thumbnail_path: Path to thumbnail image

        Returns:
            Tuple of (mp3_success, m4a_success, mp3_error, m4a_error)
        """
        self.logger.info("Embedding metadata in both formats")

        # Embed MP3 metadata
        mp3_success, mp3_error = self.embed_mp3_metadata(
            mp3_file,
            metadata,
            thumbnail_path
        )

        # Embed M4A metadata
        m4a_success, m4a_error = self.embed_m4a_metadata(
            m4a_file,
            metadata,
            thumbnail_path
        )

        if mp3_success and m4a_success:
            self.logger.info("Metadata embedded in both formats successfully")
        elif mp3_success:
            self.logger.warning(f"MP3 embedding succeeded, but M4A failed: {m4a_error}")
        elif m4a_success:
            self.logger.warning(f"M4A embedding succeeded, but MP3 failed: {mp3_error}")
        else:
            self.logger.error("Both metadata embeddings failed")

        return mp3_success, m4a_success, mp3_error, m4a_error

    def validate_mp3_metadata(
        self,
        file_path: Path,
        expected_metadata: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that MP3 file has expected metadata.

        Args:
            file_path: Path to MP3 file
            expected_metadata: Expected metadata dictionary

        Returns:
            Tuple of (is_valid: bool, error_message: Optional[str])
        """
        file_path = Path(file_path)

        if not file_path.exists():
            return False, f"File not found: {file_path}"

        try:
            audio = MP3(file_path, ID3=ID3)

            if audio.tags is None:
                return False, "No ID3 tags found"

            # Check title
            if 'TIT2' not in audio.tags:
                return False, "Title (TIT2) not found in tags"
            if str(audio.tags['TIT2']) != expected_metadata.get('title'):
                return False, f"Title mismatch: expected '{expected_metadata.get('title')}', got '{audio.tags['TIT2']}'"

            # Check artist
            if 'TPE1' not in audio.tags:
                return False, "Artist (TPE1) not found in tags"
            if str(audio.tags['TPE1']) != expected_metadata.get('artist'):
                return False, f"Artist mismatch: expected '{expected_metadata.get('artist')}', got '{audio.tags['TPE1']}'"

            # Check album if provided
            if 'album' in expected_metadata and expected_metadata['album']:
                if 'TALB' not in audio.tags:
                    return False, "Album (TALB) not found in tags"

            # Check album art if provided
            if 'APIC:Cover' in audio.tags:
                self.logger.debug("Album art found in MP3")

            self.logger.debug(f"MP3 metadata validation passed: {file_path.name}")
            return True, None

        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def validate_m4a_metadata(
        self,
        file_path: Path,
        expected_metadata: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that M4A file has expected metadata.

        Args:
            file_path: Path to M4A file
            expected_metadata: Expected metadata dictionary

        Returns:
            Tuple of (is_valid: bool, error_message: Optional[str])
        """
        file_path = Path(file_path)

        if not file_path.exists():
            return False, f"File not found: {file_path}"

        try:
            audio = MP4(file_path)

            # Check title
            if '\xa9nam' not in audio:
                return False, "Title (\xa9nam) not found in tags"
            actual_title = audio['\xa9nam'][0]
            expected_title = expected_metadata.get('title')
            if actual_title != expected_title:
                return False, f"Title mismatch: expected '{expected_title}', got '{actual_title}'"

            # Check artist
            if '\xa9ART' not in audio:
                return False, "Artist (\xa9ART) not found in tags"
            actual_artist = audio['\xa9ART'][0]
            expected_artist = expected_metadata.get('artist')
            if actual_artist != expected_artist:
                return False, f"Artist mismatch: expected '{expected_artist}', got '{actual_artist}'"

            # Check album if provided
            if 'album' in expected_metadata and expected_metadata['album']:
                if '\xa9alb' not in audio:
                    return False, "Album (\xa9alb) not found in tags"

            # Check album art if provided
            if 'covr' in audio:
                self.logger.debug("Album art found in M4A")

            self.logger.debug(f"M4A metadata validation passed: {file_path.name}")
            return True, None

        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def get_metadata(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Read metadata from audio file (MP3 or M4A).

        Args:
            file_path: Path to audio file

        Returns:
            Dictionary with metadata, or None if read fails
        """
        file_path = Path(file_path)

        if not file_path.exists():
            self.logger.error(f"File not found: {file_path}")
            return None

        try:
            audio = MutagenFile(file_path)

            if audio is None:
                self.logger.error(f"Could not read audio file: {file_path}")
                return None

            metadata = {}

            # Handle MP3 files
            if isinstance(audio, MP3):
                if audio.tags:
                    metadata['title'] = str(audio.tags.get('TIT2', ''))
                    metadata['artist'] = str(audio.tags.get('TPE1', ''))
                    metadata['album'] = str(audio.tags.get('TALB', ''))
                    metadata['has_artwork'] = 'APIC:Cover' in audio.tags

            # Handle M4A files
            elif isinstance(audio, MP4):
                metadata['title'] = audio.get('\xa9nam', [''])[0]
                metadata['artist'] = audio.get('\xa9ART', [''])[0]
                metadata['album'] = audio.get('\xa9alb', [''])[0]
                metadata['has_artwork'] = 'covr' in audio

            # Add file info
            metadata['duration'] = audio.info.length if hasattr(audio, 'info') else 0
            metadata['bitrate'] = audio.info.bitrate if hasattr(audio, 'info') else 0

            return metadata

        except Exception as e:
            self.logger.error(f"Error reading metadata: {str(e)}")
            return None
