"""
Music DLP - Downloaders Package

This package handles YouTube audio downloads and metadata extraction using yt-dlp.

Modules:
    yt_dlp_manager: Core yt-dlp wrapper with bot detection avoidance
    metadata_extractor: Extract playlist/video metadata without downloading
    thumbnail_processor: Download and process thumbnails to 300x300px
"""

from .yt_dlp_manager import YTDLPManager
from .metadata_extractor import MetadataExtractor
from .thumbnail_processor import ThumbnailProcessor

__all__ = [
    'YTDLPManager',
    'MetadataExtractor',
    'ThumbnailProcessor'
]
