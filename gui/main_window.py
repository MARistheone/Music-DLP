"""
Main Window for Music DLP Application

CustomTkinter-based main window with:
- Playlist panel (left)
- Song panel (right)
- Pipeline panel (middle)
- Log panel (bottom)
- Menu bar with settings and theme switching

Author: Music DLP Project
Version: 1.0.0
"""

import customtkinter as ctk
from pathlib import Path
import threading
import tkinter as tk
from tkinter import messagebox, filedialog

from gui.components.playlist_panel import PlaylistPanel
from gui.components.song_panel import SongPanel
from gui.components.pipeline_panel import PipelinePanel
from gui.components.log_panel import LogPanel
from gui.dialogs.add_playlist_dialog import AddPlaylistDialog
from gui.dialogs.settings_dialog import SettingsDialog
from gui.dialogs.ai_review_table_dialog import AIReviewTableDialog
from gui.dialogs.ai_review_dialog import AIReviewDialog


class MainWindow(ctk.CTk):
    """
    Main application window.

    Manages layout, theme, and coordinates all UI components.
    """

    def __init__(self, db, config, logger):
        """
        Initialize main window.

        Args:
            db: Database instance
            config: ConfigManager instance
            logger: Logger instance
        """
        super().__init__()

        self.db = db
        self.config = config
        self.logger = logger

        # Window configuration
        self.title("Music DLP - YouTube Playlist Downloader")
        self.geometry("1200x800")
        self.minsize(1000, 600)

        # Set theme from config
        theme_mode = config.theme_mode  # 'light', 'dark', or 'system'
        ctk.set_appearance_mode(theme_mode)
        ctk.set_default_color_theme("blue")

        # Create UI
        self._create_menu()
        self._create_layout()
        self._setup_logging()

        # Bind close event
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        self.logger.info("Main window initialized")

    def _create_menu(self):
        """Create menu bar at top of window."""
        # Menu frame
        menu_frame = ctk.CTkFrame(self, height=50)
        menu_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        menu_frame.grid_columnconfigure(1, weight=1)  # Center spacer

        # Left side: Title
        title_label = ctk.CTkLabel(
            menu_frame,
            text="Music DLP",
            font=("Arial", 20, "bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=10, sticky="w")

        # Right side: Theme toggle and Settings button
        right_frame = ctk.CTkFrame(menu_frame, fg_color="transparent")
        right_frame.grid(row=0, column=2, padx=10, pady=10, sticky="e")

        # Theme toggle button
        self.theme_button = ctk.CTkButton(
            right_frame,
            text="☀️ Light" if self.config.theme_mode == "dark" else "🌙 Dark",
            width=100,
            command=self._toggle_theme
        )
        self.theme_button.grid(row=0, column=0, padx=5)

        # Settings button
        settings_button = ctk.CTkButton(
            right_frame,
            text="⚙️ Settings",
            width=100,
            command=self._open_settings
        )
        settings_button.grid(row=0, column=1, padx=5)

        # Tools button
        self.tools_button = ctk.CTkButton(
            right_frame,
            text="Tools",
            width=100,
            command=self._show_tools_menu
        )
        self.tools_button.grid(row=0, column=2, padx=5)

    def _create_layout(self):
        """Create main window layout with all panels."""
        # Configure grid weights for responsive layout
        self.grid_rowconfigure(1, weight=2)  # Playlist/Song panels
        self.grid_rowconfigure(2, weight=0)  # Pipeline panel (fixed height)
        self.grid_rowconfigure(3, weight=1)  # Log panel
        self.grid_columnconfigure(0, weight=1)  # Playlist panel
        self.grid_columnconfigure(1, weight=3)  # Song panel

        # URL input bar
        url_frame = ctk.CTkFrame(self)
        url_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=(0, 5))
        url_frame.grid_columnconfigure(1, weight=1)

        url_label = ctk.CTkLabel(url_frame, text="Playlist URL:")
        url_label.grid(row=0, column=0, padx=(10, 5), pady=10)

        self.url_entry = ctk.CTkEntry(url_frame, placeholder_text="https://www.youtube.com/playlist?list=...")
        self.url_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=10)

        add_button = ctk.CTkButton(url_frame, text="Add", width=100, command=self._add_playlist)
        add_button.grid(row=0, column=2, padx=(5, 10), pady=10)

        # Playlist panel (left)
        self.playlist_panel = PlaylistPanel(
            self,
            db=self.db,
            config=self.config,
            logger=self.logger,
            on_playlist_select=self._on_playlist_selected
        )
        self.playlist_panel.grid(row=2, column=0, sticky="nsew", padx=(5, 2), pady=5)

        # Song panel (right)
        self.song_panel = SongPanel(
            self,
            db=self.db,
            config=self.config,
            logger=self.logger
        )
        self.song_panel.grid(row=2, column=1, sticky="nsew", padx=(2, 5), pady=5)

        # Wire up song panel callbacks for context menu
        self.song_panel.on_review_callback = self._open_review_dialog_for_videos
        self.song_panel.on_regenerate_callback = self._regenerate_single_video

        # Pipeline panel (full width below)
        self.pipeline_panel = PipelinePanel(
            self,
            db=self.db,
            config=self.config,
            logger=self.logger,
            on_extract=self._on_extract,
            on_download=self._on_download,
            on_ai_process=self._on_ai_process,
            on_review=self._on_review,
            on_convert=self._on_convert
        )
        self.pipeline_panel.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        # Log panel (full width at bottom)
        self.log_panel = LogPanel(
            self,
            db=self.db,
            config=self.config,
            logger=self.logger
        )
        self.log_panel.grid(row=4, column=0, columnspan=2, sticky="nsew", padx=5, pady=(0, 5))

    def _setup_logging(self):
        """Setup GUI log handler to display logs in log panel."""
        from core.logger import GUILogHandler

        gui_handler = GUILogHandler(callback=self.log_panel.add_log_message)
        self.logger.addHandler(gui_handler)

        self.logger.info("GUI logging initialized")

    def _toggle_theme(self):
        """Toggle between light and dark themes."""
        current = self.config.theme_mode

        # Cycle: dark → light → system → dark
        if current == "dark":
            new_theme = "light"
            button_text = "🌙 Dark"
        elif current == "light":
            new_theme = "system"
            button_text = "💻 System"
        else:  # system
            new_theme = "dark"
            button_text = "☀️ Light"

        self.config.theme_mode = new_theme
        ctk.set_appearance_mode(new_theme)
        self.theme_button.configure(text=button_text)

        self.logger.info(f"Theme changed to: {new_theme}")

    def _open_settings(self):
        """Open settings dialog."""
        dialog = SettingsDialog(self, db=self.db, config=self.config, logger=self.logger)
        dialog.grab_set()  # Modal
        self.wait_window(dialog)

        # Refresh UI after settings change
        self.playlist_panel.refresh()
        self.song_panel.refresh()

    def _show_tools_menu(self):
        """Show dropdown menu from the Tools button."""
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Export for External AI...", command=self._on_export_ai)
        menu.add_command(label="Import AI Results...", command=self._on_import_ai)
        menu.add_command(label="Paste AI Results...", command=self._on_paste_ai)

        x = self.tools_button.winfo_rootx()
        y = self.tools_button.winfo_rooty() + self.tools_button.winfo_height()
        menu.tk_popup(x, y)

    def _on_export_ai(self):
        """Export downloaded videos as JSON + prompt files for external AI."""
        from ai.external_processor import export_for_external_ai

        # Find all downloaded videos
        downloaded = self.db.get_videos_by_status('downloaded')
        eligible = [v['video_id'] for v in downloaded]

        if not eligible:
            messagebox.showinfo(
                "Export for External AI",
                "No eligible videos found.\n\n"
                "Videos must be downloaded before exporting."
            )
            return

        # Ask for batch size
        batch_dialog = ctk.CTkInputDialog(
            text=f"Found {len(eligible)} video(s) to export.\n\nBatch size (videos per file):",
            title="Export Batch Size"
        )
        batch_input = batch_dialog.get_input()

        if not batch_input:
            return  # Cancelled

        try:
            batch_size = int(batch_input)
            if batch_size < 1:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input", "Batch size must be a positive integer.")
            return

        # Ask for output directory
        output_dir = filedialog.askdirectory(title="Select Export Folder")
        if not output_dir:
            return  # Cancelled

        # Run export
        try:
            files = export_for_external_ai(self.db, output_dir, eligible, batch_size)

            if files:
                file_list = "\n".join(Path(f).name for f in files)
                messagebox.showinfo(
                    "Export Complete",
                    f"Exported {len(eligible)} video(s) to {len(files) // 2} batch(es).\n\n"
                    f"Files created:\n{file_list}\n\n"
                    f"Paste the .txt file into any AI chatbot, then import the response."
                )
                self.logger.info(f"External AI export: {len(eligible)} videos, {len(files)} files")
            else:
                messagebox.showwarning("Export", "No files were generated.")
        except Exception as e:
            self.logger.error(f"Export failed: {e}")
            messagebox.showerror("Export Error", f"Export failed:\n{e}")

    def _on_import_ai(self):
        """Import AI results from an external AI JSON file."""
        from ai.external_processor import import_external_ai_results

        file_path = filedialog.askopenfilename(
            title="Select AI Results File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not file_path:
            return  # Cancelled

        try:
            result = import_external_ai_results(self.db, file_path)

            # Build summary message
            msg_parts = [f"Imported: {result['imported']}"]
            if result['skipped']:
                msg_parts.append(f"Skipped: {result['skipped']}")

            msg = "\n".join(msg_parts)

            if result['errors']:
                msg += f"\n\nIssues ({len(result['errors'])}):\n"
                # Show first 10 errors max
                for err in result['errors'][:10]:
                    msg += f"  - {err}\n"
                if len(result['errors']) > 10:
                    msg += f"  ... and {len(result['errors']) - 10} more (see log)"

                for err in result['errors']:
                    self.logger.warning(f"Import issue: {err}")

            if result['imported'] > 0:
                messagebox.showinfo("Import Complete", msg)
            else:
                messagebox.showwarning("Import", msg)

            # Refresh song panel to show new AI indicators
            self.song_panel.refresh()

        except Exception as e:
            self.logger.error(f"Import failed: {e}")
            messagebox.showerror("Import Error", f"Import failed:\n{e}")

    def _on_paste_ai(self):
        """Paste AI results directly from clipboard via a text dialog."""
        from ai.external_processor import import_external_ai_from_text

        # Create paste dialog
        paste_win = ctk.CTkToplevel(self)
        paste_win.title("Paste AI Results")
        paste_win.geometry("600x450")
        paste_win.transient(self)
        paste_win.grab_set()

        ctk.CTkLabel(
            paste_win,
            text="Paste the JSON response from your AI chatbot below:",
            anchor="w"
        ).pack(fill="x", padx=15, pady=(15, 5))

        text_box = ctk.CTkTextbox(paste_win, wrap="word")
        text_box.pack(fill="both", expand=True, padx=15, pady=5)

        # Try to pre-fill from clipboard
        try:
            clipboard = self.clipboard_get()
            if clipboard and clipboard.strip().startswith(("[", "{", "```")):
                text_box.insert("1.0", clipboard)
        except Exception:
            pass

        button_frame = ctk.CTkFrame(paste_win, fg_color="transparent")
        button_frame.pack(fill="x", padx=15, pady=(5, 15))

        def on_import():
            raw_text = text_box.get("1.0", "end").strip()
            if not raw_text:
                messagebox.showwarning("Empty", "No text to import.", parent=paste_win)
                return

            try:
                result = import_external_ai_from_text(self.db, raw_text)

                msg_parts = [f"Imported: {result['imported']}"]
                if result['skipped']:
                    msg_parts.append(f"Skipped: {result['skipped']}")
                msg = "\n".join(msg_parts)

                if result['errors']:
                    msg += f"\n\nIssues ({len(result['errors'])}):\n"
                    for err in result['errors'][:10]:
                        msg += f"  - {err}\n"
                    if len(result['errors']) > 10:
                        msg += f"  ... and {len(result['errors']) - 10} more (see log)"
                    for err in result['errors']:
                        self.logger.warning(f"Paste import issue: {err}")

                paste_win.destroy()

                if result['imported'] > 0:
                    messagebox.showinfo("Import Complete", msg)
                else:
                    messagebox.showwarning("Import", msg)

                self.song_panel.refresh()

            except Exception as e:
                self.logger.error(f"Paste import failed: {e}")
                messagebox.showerror("Import Error", f"Import failed:\n{e}", parent=paste_win)

        ctk.CTkButton(button_frame, text="Import", width=120, command=on_import).pack(side="right", padx=5)
        ctk.CTkButton(button_frame, text="Cancel", width=120, command=paste_win.destroy).pack(side="right", padx=5)

    def _add_playlist(self):
        """Add playlist from URL input or show dialog."""
        url = self.url_entry.get().strip()

        if url:
            # URL provided directly in entry
            self._extract_playlist(url)
            self.url_entry.delete(0, 'end')
        else:
            # Show dialog
            dialog = AddPlaylistDialog(self, db=self.db, config=self.config, logger=self.logger)
            dialog.grab_set()  # Modal
            self.wait_window(dialog)

            # Refresh playlist panel
            self.playlist_panel.refresh()

    def _extract_playlist(self, url):
        """
        Extract playlist metadata (Stage 1).

        Args:
            url: YouTube playlist URL
        """
        if self.pipeline_panel.is_busy:
            self.logger.warning(f"Cannot start Extract - '{self.pipeline_panel.active_stage}' is still running")
            return

        self.logger.info(f"Extracting playlist: {url}")
        self.pipeline_panel.set_busy("Extract")

        # Start extraction in background
        from gui.workers.download_worker import DownloadWorker

        def on_complete(success, result):
            self.pipeline_panel.set_idle()
            if success:
                self.logger.info(f"Playlist extracted: {result.get('title', 'Unknown')}")
                self.playlist_panel.refresh()
            else:
                self.logger.error(f"Extraction failed: {result}")

        worker = DownloadWorker(
            db=self.db,
            config=self.config,
            logger=self.logger,
            mode='extract',
            url=url,
            on_complete=on_complete,
            on_progress=self.pipeline_panel.update_progress
        )
        worker.start()

    def _on_playlist_selected(self, playlist_id):
        """
        Handle playlist selection.

        Args:
            playlist_id: Selected playlist ID
        """
        self.logger.info(f"Playlist selected: {playlist_id}")
        self.song_panel.load_playlist_songs(playlist_id)

    # Pipeline stage callbacks

    def _on_extract(self):
        """Stage 1: Extract metadata from selected playlists."""
        selected = self.playlist_panel.get_selected_playlists()

        if not selected:
            self.logger.warning("No playlists selected for extraction")
            return

        self.logger.info(f"Extracting {len(selected)} playlists...")
        # Extraction logic handled in playlist panel
        self.playlist_panel.extract_selected()

    def _on_download(self):
        """Stage 2: Download audio files."""
        if self.pipeline_panel.is_busy:
            self.logger.warning(f"Cannot start Download - '{self.pipeline_panel.active_stage}' is still running")
            return

        videos = self.song_panel.get_selected_videos()

        if not videos:
            self.logger.warning("No videos selected for download")
            return

        self.logger.info(f"Downloading {len(videos)} videos (resume logic in worker)...")
        self.pipeline_panel.set_busy("Download")

        from gui.workers.download_worker import DownloadWorker

        def on_complete(success, result):
            self.pipeline_panel.set_idle()
            if success:
                self.logger.info(f"Downloaded {result.get('count', 0)} videos")
                self.song_panel.refresh()
            else:
                self.logger.error(f"Download failed: {result}")

        worker = DownloadWorker(
            db=self.db,
            config=self.config,
            logger=self.logger,
            mode='download',
            videos=videos,
            on_complete=on_complete,
            on_progress=self.pipeline_panel.update_progress
        )
        worker.start()

    def _on_ai_process(self):
        """Stage 3: Process titles with AI."""
        if self.pipeline_panel.is_busy:
            self.logger.warning(f"Cannot start AI Process - '{self.pipeline_panel.active_stage}' is still running")
            return

        # Get selected videos that have been downloaded
        selected = self.song_panel.get_selected_videos()

        if not selected:
            self.logger.warning("No videos selected for AI processing")
            return

        # Filter for only downloaded videos
        videos = [v for v in selected if v.get('download_status') == 'downloaded']

        if not videos:
            self.logger.warning("Selected videos have not been downloaded yet")
            return

        self.logger.info(f"Processing {len(videos)} videos with AI...")
        self.pipeline_panel.set_busy("AI Process")

        from gui.workers.ai_worker import AIWorker

        def on_complete(success, result):
            self.pipeline_panel.set_idle()
            if success:
                self.logger.info(f"AI processed {result.get('count', 0)} videos")
                self.song_panel.refresh()
            else:
                self.logger.error(f"AI processing failed: {result}")

        worker = AIWorker(
            db=self.db,
            config=self.config,
            logger=self.logger,
            videos=videos,
            on_complete=on_complete,
            on_progress=self.pipeline_panel.update_progress
        )
        worker.start()

    def _on_review(self):
        """Stage 4: Batch review AI suggestions."""
        # Get selected videos that have been AI-processed
        videos = self.song_panel.get_selected_ai_processed_videos()

        if not videos:
            # Check if user selected any videos
            selected = self.song_panel.get_selected_videos()
            if not selected:
                self.logger.warning("No videos selected for review")
            else:
                self.logger.warning("Selected videos have not been AI-processed yet")
            return

        self.logger.info(f"Opening AI review table for {len(videos)} selected videos...")

        dialog = AIReviewTableDialog(
            self,
            db=self.db,
            config=self.config,
            logger=self.logger,
            videos=videos
        )
        dialog.grab_set()  # Modal
        self.wait_window(dialog)

        # Refresh after review
        self.song_panel.refresh()

    def _open_review_dialog_for_videos(self, videos):
        """
        Open AI review dialog for specific videos (called from context menu).

        Args:
            videos: List of video dicts to review
        """
        if not videos:
            return

        self.logger.info(f"Opening AI review dialog for {len(videos)} video(s)...")

        dialog = AIReviewDialog(
            parent=self,
            db=self.db,
            config=self.config,
            logger=self.logger,
            videos=videos
        )
        dialog.wait_window()  # Wait for dialog to close

        # Refresh song panel after review
        self.song_panel.refresh()

    def _regenerate_single_video(self, video_id: str):
        """
        Regenerate AI for a single video (called from context menu).

        Args:
            video_id: Video ID to regenerate
        """
        video = self.db.get_video(video_id)
        if not video:
            self.logger.error(f"Video {video_id} not found")
            return

        self.logger.info(f"Regenerating AI for video: {video.get('title', video_id)}")

        from gui.workers.ai_worker import AIWorker

        def on_complete(success, result):
            if success:
                self.logger.info(f"Regenerated AI for 1 video")
                self.song_panel.refresh()
            else:
                self.logger.error(f"AI regeneration failed: {result}")

        worker = AIWorker(
            db=self.db,
            config=self.config,
            logger=self.logger,
            videos=[video],
            on_complete=on_complete,
            on_progress=lambda p, s: None  # No progress bar for single video
        )
        worker.start()

    def _on_convert(self):
        """Stage 5: Convert to MP3/M4A with metadata."""
        if self.pipeline_panel.is_busy:
            self.logger.warning(f"Cannot start Convert - '{self.pipeline_panel.active_stage}' is still running")
            return

        videos = self.song_panel.get_approved_videos()

        if not videos:
            self.logger.warning("No approved videos to convert")
            return

        # Filter to only videos that have been downloaded
        ready = [v for v in videos if v.get('file_path_raw') and v.get('download_status') == 'downloaded']
        skipped = len(videos) - len(ready)

        if skipped > 0:
            self.logger.warning(f"{skipped} approved video(s) skipped - not yet downloaded")

        if not ready:
            self.logger.warning("No downloaded videos to convert. Run Download first.")
            return

        self.logger.info(f"Converting {len(ready)} videos...")
        self.pipeline_panel.set_busy("Convert")

        from gui.workers.conversion_worker import ConversionWorker

        def on_complete(success, result):
            self.pipeline_panel.set_idle()
            if success:
                self.logger.info(f"Converted {result.get('count', 0)} videos")
                self.song_panel.refresh()
            else:
                self.logger.error(f"Conversion failed: {result}")

        worker = ConversionWorker(
            db=self.db,
            config=self.config,
            logger=self.logger,
            videos=ready,
            on_complete=on_complete,
            on_progress=self.pipeline_panel.update_progress
        )
        worker.start()

    def _on_closing(self):
        """Handle window close event."""
        self.logger.info("Closing application...")

        # Cancel any running workers
        # (workers should check a cancellation flag)

        # Close database
        self.db.close()

        # Destroy window
        self.destroy()
