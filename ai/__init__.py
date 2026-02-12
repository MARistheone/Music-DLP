"""
AI processing package for Music DLP.

This package handles AI-powered title cleaning using Ollama models.

Modules:
    ollama_client: Ollama API client for model communication
    prompts: AI prompts for title generation
    title_processor: Parallel AI processing orchestrator
"""

from .ollama_client import OllamaClient
from .title_processor import TitleProcessor

__all__ = [
    'OllamaClient',
    'TitleProcessor',
]
