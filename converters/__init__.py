"""
Converters Package

This package handles audio file conversion and metadata embedding for the Music DLP application.

Modules:
- ffmpeg_converter: Converts audio files from Opus to MP3 and M4A formats
- metadata_embedder: Embeds metadata (title, artist, album art) into audio files

Usage:
    from converters import FFmpegConverter, MetadataEmbedder

    # Convert audio
    converter = FFmpegConverter()
    converter.convert_to_mp3(input_file, output_file)

    # Embed metadata
    embedder = MetadataEmbedder()
    embedder.embed_mp3_metadata(file, metadata, thumbnail)
"""

from .ffmpeg_converter import FFmpegConverter
from .metadata_embedder import MetadataEmbedder

__all__ = ['FFmpegConverter', 'MetadataEmbedder']
