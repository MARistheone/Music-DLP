"""
Song Panel Component

Right panel showing list of songs/videos with:
- Video title and status indicators
- Download status (pending, downloading, done, error)
- AI processing status
- Approval status
- Select all and action buttons

Author: Music DLP Project
Version: 1.0.0
"""

import customtkinter as ctk
from typing import List, Dict
import tkinter as tk


class SongPanel(ctk.CTkScrollableFrame):
    """
    Song list panel (right side of main window).

    Displays videos from selected playlist with status indicators.
    """

    def __init__(self, parent, db, config, logger):
        """
        Initialize song panel.

        Args:
            parent: Parent widget
            db: Database instance
            config: ConfigManager instance
            logger: Logger instance
        """
        super().__init__(parent, label_text="Songs", width=700)

        self.db = db
        self.config = config
        self.logger = logger

        self.current_playlist_id = None
        self.song_vars = {}  # {video_id: IntVar}
        self.song_widgets = {}  # {video_id: frame}

        self._create_widgets()

    def _create_widgets(self):
        """Create static widgets (header and buttons)."""
        # Header frame
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=5, pady=5)

        # Column headers
        ctk.CTkLabel(header_frame, text="#", width=30, anchor="w").grid(row=0, column=0, padx=2)
        ctk.CTkLabel(header_frame, text="Title", width=300, anchor="w").grid(row=0, column=1, padx=2)
        ctk.CTkLabel(header_frame, text="Status", width=80, anchor="w").grid(row=0, column=2, padx=2)
        ctk.CTkLabel(header_frame, text="AI", width=40, anchor="w").grid(row=0, column=3, padx=2)
        ctk.CTkLabel(header_frame, text="✓", width=30, anchor="w").grid(row=0, column=4, padx=2)

        # Hint label for discoverability
        hint_label = ctk.CTkLabel(
            self,
            text="Double-click a song to review AI titles  |  Right-click for more options",
            text_color="gray",
            font=("Arial", 11)
        )
        hint_label.pack(fill="x", padx=10, pady=(0, 5))

        # Button frame at bottom
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(side="bottom", fill="x", padx=5, pady=5)

        self.select_all_button = ctk.CTkButton(
            button_frame,
            text="Select All",
            width=100,
            command=self._select_all
        )
        self.select_all_button.pack(side="left", padx=2)

    def load_playlist_songs(self, playlist_id):
        """
        Load songs from a playlist.

        Args:
            playlist_id: Playlist ID to load
        """
        self.current_playlist_id = playlist_id
        self.refresh()

    def refresh(self):
        """Refresh song list from database."""
        # Clear existing widgets
        for widget in self.song_widgets.values():
            widget.destroy()

        self.song_widgets.clear()
        self.song_vars.clear()

        if not self.current_playlist_id:
            # Show empty state
            empty_label = ctk.CTkLabel(
                self,
                text="Select a playlist to view songs.",
                text_color="gray"
            )
            empty_label.pack(pady=20)
            self.song_widgets['empty'] = empty_label
            return

        # Get videos from database
        try:
            videos = self.db.get_playlist_videos(self.current_playlist_id)

            if not videos:
                empty_label = ctk.CTkLabel(
                    self,
                    text="No videos in this playlist.\nExtract playlist metadata first.",
                    text_color="gray"
                )
                empty_label.pack(pady=20)
                self.song_widgets['empty'] = empty_label
                return

            # Bulk-load AI and approval status (2 queries instead of 2*N)
            video_ids = [v['video_id'] for v in videos]
            self._ai_counts = self.db.get_ai_attempt_counts_bulk(video_ids)
            self._approved_ids = self.db.get_approved_video_ids_bulk(video_ids)

            # Create item for each video
            for idx, video in enumerate(videos, 1):
                self._create_song_item(idx, video)

        except Exception as e:
            self.logger.error(f"Failed to refresh song panel: {e}")

    def _create_song_item(self, index, video):
        """
        Create a song item widget.

        Args:
            index: Song number (1-indexed)
            video: Video dict from database
        """
        video_id = video['video_id']

        # Item frame
        item_frame = ctk.CTkFrame(self)
        item_frame.pack(fill="x", padx=5, pady=2)

        # Checkbox variable
        var = tk.IntVar(value=0)
        self.song_vars[video_id] = var

        # Checkbox
        checkbox = ctk.CTkCheckBox(
            item_frame,
            text="",
            variable=var,
            width=20
        )
        checkbox.grid(row=0, column=0, padx=2, pady=5)

        # Index number
        ctk.CTkLabel(item_frame, text=str(index), width=30, anchor="w").grid(row=0, column=1, padx=2)

        # Title (truncate if too long)
        title = video.get('title', 'Unknown')
        title_display = title[:60] + "..." if len(title) > 60 else title
        ctk.CTkLabel(item_frame, text=title_display, width=300, anchor="w").grid(row=0, column=2, padx=2)

        # Status indicators
        download_status = video.get('download_status', 'pending')
        status_emoji = self._get_status_emoji(download_status)
        ctk.CTkLabel(item_frame, text=status_emoji, width=80, anchor="w").grid(row=0, column=3, padx=2)

        # AI status (use bulk-loaded cache if available, fallback to per-item query)
        if hasattr(self, '_ai_counts'):
            has_ai = self._ai_counts.get(video_id, 0) > 0
        else:
            has_ai = len(self.db.get_ai_attempts(video_id)) > 0
        ai_emoji = "🤖" if has_ai else "-"
        ctk.CTkLabel(item_frame, text=ai_emoji, width=40, anchor="w").grid(row=0, column=4, padx=2)

        # Approval status (use bulk-loaded cache if available, fallback to per-item query)
        if hasattr(self, '_approved_ids'):
            is_approved = video_id in self._approved_ids
        else:
            is_approved = self.db.get_approved_metadata(video_id) is not None
        approval_emoji = "✓" if is_approved else "-"
        ctk.CTkLabel(item_frame, text=approval_emoji, width=30, anchor="w").grid(row=0, column=5, padx=2)

        # Bind right-click for context menu
        item_frame.bind("<Button-3>", lambda e, vid=video_id: self._show_context_menu(e, vid))

        # Bind double-click to open AI review dialog
        item_frame.bind("<Double-Button-1>", lambda e, vid=video_id: self._on_double_click(e, vid))
        # Also bind children so double-click works on labels too
        for child in item_frame.winfo_children():
            child.bind("<Double-Button-1>", lambda e, vid=video_id: self._on_double_click(e, vid))
            child.bind("<Button-3>", lambda e, vid=video_id: self._show_context_menu(e, vid))

        self.song_widgets[video_id] = item_frame

    def _get_status_emoji(self, status):
        """
        Get emoji for download status.

        Args:
            status: Download status string

        Returns:
            Emoji string
        """
        status_map = {
            'pending': '⏸️ Pending',
            'downloading': '⬇️ Downloading',
            'downloaded': '✅ Done',
            'error': '❌ Error'
        }
        return status_map.get(status, status)

    def _select_all(self):
        """Select or deselect all songs."""
        # Check if any are selected
        any_selected = any(var.get() == 1 for var in self.song_vars.values())

        # Toggle: if any selected, deselect all; otherwise select all
        new_value = 0 if any_selected else 1

        for var in self.song_vars.values():
            var.set(new_value)

        action = "Deselected" if new_value == 0 else "Selected"
        self.logger.info(f"{action} all songs")

    def get_selected_videos(self) -> List[Dict]:
        """
        Get list of selected video dictionaries (checked).

        Returns:
            List of video dictionaries with full metadata
        """
        selected = []
        for video_id, var in self.song_vars.items():
            if var.get() == 1:
                # Get full video record from database
                cursor = self.db.conn.cursor()
                cursor.execute("SELECT * FROM videos WHERE video_id = ?", (video_id,))
                row = cursor.fetchone()
                if row:
                    selected.append(dict(row))

        return selected

    def get_downloaded_videos(self) -> List[Dict]:
        """
        Get all videos that have been downloaded.

        Returns:
            List of video dicts
        """
        if not self.current_playlist_id:
            return []

        try:
            all_videos = self.db.get_playlist_videos(self.current_playlist_id)
            downloaded = [v for v in all_videos if v.get('download_status') == 'downloaded']
            return downloaded
        except Exception as e:
            self.logger.error(f"Failed to get downloaded videos: {e}")
            return []

    def get_ai_processed_videos(self) -> List[Dict]:
        """
        Get all videos that have AI attempts.

        Returns:
            List of video dicts
        """
        if not self.current_playlist_id:
            return []

        try:
            all_videos = self.db.get_playlist_videos(self.current_playlist_id)
            processed = []

            for video in all_videos:
                ai_attempts = self.db.get_ai_attempts(video['video_id'])
                if ai_attempts:
                    processed.append(video)

            return processed
        except Exception as e:
            self.logger.error(f"Failed to get AI processed videos: {e}")
            return []

    def get_approved_videos(self) -> List[Dict]:
        """
        Get all videos with approved metadata.

        Returns:
            List of video dicts
        """
        if not self.current_playlist_id:
            return []

        try:
            all_videos = self.db.get_playlist_videos(self.current_playlist_id)
            approved = []

            for video in all_videos:
                metadata = self.db.get_approved_metadata(video['video_id'])
                if metadata:
                    approved.append(video)

            return approved
        except Exception as e:
            self.logger.error(f"Failed to get approved videos: {e}")
            return []

    def get_selected_ai_processed_videos(self) -> List[Dict]:
        """
        Get selected videos that have AI attempts.

        Combines selection state (checkboxes) with AI processing status.
        This is used by the review dialog to only show selected videos.

        Returns:
            List of selected video dicts that have been AI-processed
        """
        selected = self.get_selected_videos()

        if not selected:
            return []

        processed = []
        for video in selected:
            ai_attempts = self.db.get_ai_attempts(video['video_id'])
            if ai_attempts:
                processed.append(video)

        return processed

    def _on_double_click(self, event, video_id: str):
        """
        Handle double-click on a song item to open review dialog.

        Args:
            event: Mouse event
            video_id: Video ID for the clicked row
        """
        # Check if video has AI attempts
        attempts = self.db.get_ai_attempts(video_id)
        if attempts:
            self._on_review_single_video(video_id)
        else:
            self.logger.info("No AI suggestions yet. Run AI Process first.")

    def _show_context_menu(self, event, video_id: str):
        """
        Show context menu on right-click.

        Args:
            event: Mouse event
            video_id: Video ID for the clicked row
        """
        # Get video data
        video = self.db.get_video(video_id)
        if not video:
            return

        # Check if video has AI attempts
        attempts = self.db.get_ai_attempts(video_id)
        has_ai = len(attempts) > 0

        # Create context menu
        menu = tk.Menu(self, tearoff=0)

        if has_ai:
            menu.add_command(
                label="Review AI Titles...",
                command=lambda: self._on_review_single_video(video_id)
            )

            # Delete AI Attempt submenu
            delete_menu = tk.Menu(menu, tearoff=0)
            for attempt in attempts:
                model = attempt.get('model_name', 'Unknown')
                title = attempt.get('generated_title', 'N/A')
                confidence = attempt.get('confidence', 0)
                attempt_id = attempt['attempt_id']
                # Truncate title for menu display
                title_short = title[:40] + "..." if len(title) > 40 else title
                label = f"#{attempt_id} {model} ({confidence:.0%}) - {title_short}"
                delete_menu.add_command(
                    label=label,
                    command=lambda aid=attempt_id, m=model, t=title: self._on_delete_attempt(aid, m, t)
                )
            menu.add_cascade(label="Delete AI Attempt", menu=delete_menu)

            menu.add_separator()

        menu.add_command(
            label="Regenerate AI",
            command=lambda: self._on_regenerate_single(video_id)
        )

        # Show menu
        menu.tk_popup(event.x_root, event.y_root)

    def _on_review_single_video(self, video_id: str):
        """
        Callback for reviewing a single video.

        Args:
            video_id: Video ID to review
        """
        # This will be connected to main window
        if hasattr(self, 'on_review_callback') and self.on_review_callback:
            video = self.db.get_video(video_id)
            if video:
                self.on_review_callback([video])

    def _on_regenerate_single(self, video_id: str):
        """
        Callback for regenerating AI for a single video.

        Args:
            video_id: Video ID to regenerate
        """
        # This will be connected to main window
        if hasattr(self, 'on_regenerate_callback') and self.on_regenerate_callback:
            self.on_regenerate_callback(video_id)

    def _on_delete_attempt(self, attempt_id: int, model_name: str, title: str):
        """
        Delete a specific AI attempt after confirmation.

        Args:
            attempt_id: AI attempt ID to delete
            model_name: Model name for display
            title: Generated title for display
        """
        from tkinter import messagebox

        confirm = messagebox.askyesno(
            "Delete AI Attempt",
            f"Delete this AI suggestion?\n\n"
            f"Model: {model_name}\n"
            f"Title: {title}"
        )

        if confirm:
            try:
                self.db.delete_ai_attempt(attempt_id)
                self.logger.info(f"Deleted AI attempt #{attempt_id} ({model_name})")
                self.refresh()
            except Exception as e:
                self.logger.error(f"Failed to delete attempt: {e}")
                messagebox.showerror("Error", f"Failed to delete:\n{e}")
