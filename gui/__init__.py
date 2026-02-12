"""
GUI Package for Music DLP

CustomTkinter-based graphical user interface with:
- Main window with playlist/song panels
- AI review dialog for batch metadata approval
- Settings dialog for configuration
- Threading workers for long-running operations

Author: Music DLP Project
Version: 1.0.0
"""

from .main_window import MainWindow

__all__ = ['MainWindow']
