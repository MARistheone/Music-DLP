"""
AI Prompts for Music DLP Title Processing - Active Version

This module re-exports the currently active prompt version.
Currently using V4 (cover_artist support).

Change history:
- V1: Initial prompts
- V2: Simplified artist extraction, objective confidence criteria
- V3: VTuber enhancements, better romanization, Vocaloid producer knowledge
- V4: Added cover_artist field (original artist vs performer distinction)
"""

from ai.prompts_v4 import (
    SYSTEM_PROMPT_V4 as SYSTEM_PROMPT,
    PROMPT_VERSION,
    build_user_prompt_v4 as build_user_prompt,
    build_regeneration_prompt_v4 as build_regeneration_prompt,
    format_metadata_display_v4 as format_metadata_display,
    validate_response_v4 as validate_response,
    normalize_response_v4 as normalize_response,
)
