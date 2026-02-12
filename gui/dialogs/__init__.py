"""
GUI Dialogs Package

Modal dialog windows:
- AddPlaylistDialog: Simple URL input
- SettingsDialog: Configuration settings
- AIReviewDialog: Batch AI title review

Author: Music DLP Project
Version: 1.0.0
"""

from .add_playlist_dialog import AddPlaylistDialog
from .settings_dialog import SettingsDialog
from .ai_review_dialog import AIReviewDialog

__all__ = ['AddPlaylistDialog', 'SettingsDialog', 'AIReviewDialog']
