"""
Add Playlist Dialog

Simple modal dialog for adding a YouTube playlist URL.

Features:
- URL input field
- URL validation
- Add to database
- Error handling

Author: Music DLP Project
Version: 1.0.0
"""

import customtkinter as ctk
from tkinter import messagebox
import re


class AddPlaylistDialog(ctk.CTkToplevel):
    """
    Modal dialog for adding a playlist URL.
    """

    def __init__(self, parent, db, config, logger):
        """
        Initialize add playlist dialog.

        Args:
            parent: Parent window
            db: Database instance
            config: ConfigManager instance
            logger: Logger instance
        """
        super().__init__(parent)

        self.db = db
        self.config = config
        self.logger = logger

        self.result = None  # Will store playlist_id if added

        # Window configuration
        self.title("Add Playlist")
        self.geometry("600x250")
        self.resizable(False, False)

        # Center on parent
        self.transient(parent)
        self._center_on_parent(parent)

        self._create_widgets()

    def _center_on_parent(self, parent):
        """Center dialog on parent window."""
        self.update_idletasks()

        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()

        dialog_w = self.winfo_width()
        dialog_h = self.winfo_height()

        x = parent_x + (parent_w - dialog_w) // 2
        y = parent_y + (parent_h - dialog_h) // 2

        self.geometry(f"+{x}+{y}")

    def _create_widgets(self):
        """Create dialog widgets."""
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="Add YouTube Playlist",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(20, 10))

        # Instructions
        instructions = ctk.CTkLabel(
            self,
            text="Enter a YouTube playlist URL:",
            text_color="gray"
        )
        instructions.pack(pady=(0, 10))

        # URL entry
        self.url_entry = ctk.CTkEntry(
            self,
            width=500,
            placeholder_text="https://www.youtube.com/playlist?list=PLxxx..."
        )
        self.url_entry.pack(pady=10)
        self.url_entry.focus()

        # Button frame
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=20)

        # Cancel button
        cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancel",
            width=120,
            fg_color="gray",
            hover_color="darkgray",
            command=self._on_cancel
        )
        cancel_button.pack(side="left", padx=10)

        # Add button
        add_button = ctk.CTkButton(
            button_frame,
            text="Add Playlist",
            width=120,
            command=self._on_add
        )
        add_button.pack(side="left", padx=10)

        # Bind Enter key to add
        self.url_entry.bind("<Return>", lambda e: self._on_add())

    def _validate_url(self, url: str) -> tuple:
        """
        Validate YouTube playlist URL.

        Args:
            url: URL string to validate

        Returns:
            tuple: (is_valid: bool, playlist_id: str or None, error_message: str or None)
        """
        if not url:
            return False, None, "URL cannot be empty"

        # Check for playlist URL pattern
        # Supports both formats:
        # - https://www.youtube.com/playlist?list=PLxxx
        # - https://www.youtube.com/watch?v=xxx&list=PLxxx
        playlist_pattern = r'[?&]list=([a-zA-Z0-9_-]+)'
        match = re.search(playlist_pattern, url)

        if not match:
            return False, None, "Invalid YouTube playlist URL.\nURL must contain 'list=' parameter."

        playlist_id = match.group(1)

        # Basic validation: playlist IDs typically start with PL or UU
        if not (playlist_id.startswith('PL') or playlist_id.startswith('UU') or
                playlist_id.startswith('FL') or playlist_id.startswith('LL')):
            return False, None, f"Invalid playlist ID format: {playlist_id}"

        return True, playlist_id, None

    def _on_add(self):
        """Handle Add button click."""
        url = self.url_entry.get().strip()

        # Validate URL
        is_valid, playlist_id, error_message = self._validate_url(url)

        if not is_valid:
            messagebox.showerror("Invalid URL", error_message)
            return

        # Check if playlist already exists
        existing = self.db.get_playlist(playlist_id)
        if existing:
            messagebox.showwarning(
                "Duplicate Playlist",
                f"Playlist '{existing['title']}' is already added."
            )
            return

        # Add placeholder to database (will be updated during extraction)
        try:
            self.db.add_playlist(
                playlist_id=playlist_id,
                title="Pending Extraction...",
                url=url
            )

            self.result = playlist_id
            self.logger.info(f"Added playlist: {playlist_id}")

            messagebox.showinfo(
                "Playlist Added",
                "Playlist added successfully!\n\nClick 'Extract' to fetch video metadata."
            )

            self.destroy()

        except Exception as e:
            self.logger.error(f"Failed to add playlist: {e}")
            messagebox.showerror("Error", f"Failed to add playlist:\n{e}")

    def _on_cancel(self):
        """Handle Cancel button click."""
        self.destroy()

    def get_result(self):
        """
        Get result after dialog closes.

        Returns:
            str or None: Playlist ID if added, None if cancelled
        """
        return self.result
