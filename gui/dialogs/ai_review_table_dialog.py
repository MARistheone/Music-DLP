"""
AI Review Table Dialog

Table-based batch review for AI-generated titles.
Shows all songs in a scrollable table for quick review and bulk operations.
Uses CustomTkinter widgets for full theme integration.

Author: Music DLP Project
Version: 3.0.0
"""

import customtkinter as ctk
from tkinter import messagebox
import tkinter as tk
import json
from typing import List, Dict, Optional
import threading


class AIReviewTableDialog(ctk.CTkToplevel):
    """
    Table-based AI review dialog using native CustomTkinter widgets.

    Shows all songs in a table with:
    - Original title
    - Best AI suggestion (highest confidence)
    - All available models
    - Quick approve/edit/reprocess actions
    """

    # Column definitions for consistent header/row alignment
    COLUMNS = [
        {"name": "cb",     "header": "",               "minsize": 40,  "weight": 0},
        {"name": "orig",   "header": "Original Title", "minsize": 250, "weight": 3},
        {"name": "ai_t",   "header": "AI Title (Best)","minsize": 250, "weight": 3},
        {"name": "ai_a",   "header": "AI Artist",      "minsize": 130, "weight": 1},
        {"name": "models", "header": "Models",         "minsize": 100, "weight": 1},
        {"name": "conf",   "header": "Conf%",          "minsize": 55,  "weight": 0},
        {"name": "status", "header": "Status",         "minsize": 70,  "weight": 0},
    ]

    # Theme-aware color tuples (light_mode, dark_mode)
    COLOR_ROW_EVEN = ("gray92", "gray17")
    COLOR_ROW_ODD = ("gray95", "gray14")
    COLOR_ROW_HOVER = ("gray85", "gray25")
    COLOR_ROW_SELECTED = ("gray80", "gray30")
    COLOR_MUTED_TEXT = ("gray40", "gray60")

    def __init__(self, parent, db, config, logger, videos: List[Dict]):
        """
        Initialize AI review table dialog.

        Args:
            parent: Parent window
            db: Database instance
            config: ConfigManager instance
            logger: Logger instance
            videos: List of video dicts to review
        """
        super().__init__(parent)

        self.db = db
        self.config = config
        self.logger = logger
        self.videos = videos

        # Track selected rows
        self.selected_rows = set()

        # Store AI attempts for each video
        self.video_attempts = {}  # {video_id: [attempts]}
        self.video_best_attempt = {}  # {video_id: best_attempt}

        # Row tracking
        self.row_widgets = {}  # {video_id: row_frame}
        self.row_vars = {}  # {video_id: IntVar for checkbox}
        self.row_colors = {}  # {video_id: base_color_tuple}

        # Window configuration
        self.title(f"AI Title Review - {len(videos)} songs")
        self.geometry("1400x800")
        self.resizable(True, True)
        self.minsize(1200, 600)

        # Center on parent
        self.transient(parent)
        self._center_on_parent(parent)

        self._load_ai_data()
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

    def _configure_row_columns(self, frame):
        """Apply consistent column configuration to a row frame."""
        for i, col in enumerate(self.COLUMNS):
            frame.grid_columnconfigure(i, minsize=col["minsize"], weight=col["weight"])

    def _load_ai_data(self):
        """Load AI attempts for all videos."""
        for video in self.videos:
            video_id = video['video_id']
            attempts = self.db.get_ai_attempts(video_id)

            if attempts:
                # Sort by confidence
                attempts.sort(key=lambda a: a.get('confidence', 0), reverse=True)
                self.video_attempts[video_id] = attempts
                self.video_best_attempt[video_id] = attempts[0]  # Highest confidence
            else:
                self.video_attempts[video_id] = []
                self.video_best_attempt[video_id] = None

    def _create_widgets(self):
        """Create dialog widgets."""
        # Header frame
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(15, 10))

        title_label = ctk.CTkLabel(
            header_frame,
            text=f"Review {len(self.videos)} Songs",
            font=("Arial", 18, "bold")
        )
        title_label.pack(side="left")

        # Stats label
        self.stats_label = ctk.CTkLabel(
            header_frame,
            text="",
            text_color="gray"
        )
        self.stats_label.pack(side="left", padx=20)
        self._update_stats()

        # Toolbar frame
        toolbar_frame = ctk.CTkFrame(self, fg_color="transparent")
        toolbar_frame.pack(fill="x", padx=20, pady=(0, 10))

        # Selection buttons
        select_all_btn = ctk.CTkButton(
            toolbar_frame,
            text="Select All",
            width=100,
            command=self._select_all
        )
        select_all_btn.pack(side="left", padx=5)

        deselect_all_btn = ctk.CTkButton(
            toolbar_frame,
            text="Deselect All",
            width=100,
            fg_color="gray",
            hover_color="darkgray",
            command=self._deselect_all
        )
        deselect_all_btn.pack(side="left", padx=5)

        # Bulk action buttons
        approve_selected_btn = ctk.CTkButton(
            toolbar_frame,
            text="Approve Selected",
            width=150,
            fg_color="green",
            hover_color="darkgreen",
            command=self._approve_selected
        )
        approve_selected_btn.pack(side="left", padx=5)

        reprocess_selected_btn = ctk.CTkButton(
            toolbar_frame,
            text="Reprocess Selected",
            width=150,
            fg_color="orange",
            hover_color="darkorange",
            command=self._reprocess_selected
        )
        reprocess_selected_btn.pack(side="left", padx=5)

        # Model selector for reprocessing
        ctk.CTkLabel(toolbar_frame, text="Model:", text_color="gray").pack(side="left", padx=(20, 5))

        available_models = self.config.ai_models
        self.reprocess_model_var = ctk.StringVar(value=self.config.primary_ai_model)
        self.model_dropdown = ctk.CTkComboBox(
            toolbar_frame,
            values=available_models,
            variable=self.reprocess_model_var,
            width=150
        )
        self.model_dropdown.pack(side="left", padx=5)

        # Close button (right side)
        close_btn = ctk.CTkButton(
            toolbar_frame,
            text="Close",
            width=100,
            fg_color="gray",
            hover_color="darkgray",
            command=self.destroy
        )
        close_btn.pack(side="right", padx=5)

        # Table container
        table_container = ctk.CTkFrame(self)
        table_container.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # Fixed header row
        header_row = ctk.CTkFrame(table_container, height=36)
        header_row.pack(fill="x", padx=2, pady=(2, 0))
        header_row.pack_propagate(False)
        self._configure_row_columns(header_row)

        for i, col in enumerate(self.COLUMNS):
            if col["name"] == "cb":
                # Empty header for checkbox column
                ctk.CTkLabel(header_row, text="", width=40).grid(
                    row=0, column=i, padx=2, pady=5, sticky="w"
                )
            else:
                ctk.CTkLabel(
                    header_row, text=col["header"],
                    font=("Arial", 10, "bold"), anchor="w"
                ).grid(row=0, column=i, padx=5, pady=5, sticky="w")

        # Scrollable table body
        self.table_body = ctk.CTkScrollableFrame(
            table_container,
            fg_color="transparent"
        )
        self.table_body.pack(fill="both", expand=True, padx=2, pady=(0, 2))

        # Populate table
        self._populate_table()

        # Bottom status bar
        status_frame = ctk.CTkFrame(self, fg_color="transparent")
        status_frame.pack(fill="x", padx=20, pady=(0, 15))

        self.status_label = ctk.CTkLabel(
            status_frame,
            text="Tip: Double-click a row to edit details, or select multiple and use bulk actions",
            text_color="gray"
        )
        self.status_label.pack(side="left")

    def _populate_table(self):
        """Populate table with video data rows."""
        # Clear existing rows
        for widget in self.table_body.winfo_children():
            widget.destroy()

        self.row_widgets.clear()
        self.row_vars.clear()
        self.row_colors.clear()

        if not self.videos:
            empty_label = ctk.CTkLabel(
                self.table_body,
                text="No songs to review.",
                text_color="gray"
            )
            empty_label.pack(pady=20)
            return

        for idx, video in enumerate(self.videos):
            self._create_data_row(idx, video)

    def _create_data_row(self, index, video):
        """Create a single data row in the table."""
        video_id = video['video_id']
        best_attempt = self.video_best_attempt.get(video_id)
        attempts = self.video_attempts.get(video_id, [])
        approved = self.db.get_approved_metadata(video_id)

        # Alternating row color
        base_color = self.COLOR_ROW_EVEN if index % 2 == 0 else self.COLOR_ROW_ODD

        row_frame = ctk.CTkFrame(self.table_body, fg_color=base_color, height=36)
        row_frame.pack(fill="x", padx=0, pady=1)
        row_frame.pack_propagate(False)
        self._configure_row_columns(row_frame)

        # Column 0: Checkbox
        var = tk.IntVar(value=1 if video_id in self.selected_rows else 0)
        self.row_vars[video_id] = var
        cb = ctk.CTkCheckBox(
            row_frame, text="", variable=var, width=20,
            command=lambda vid=video_id: self._on_checkbox_toggle(vid)
        )
        cb.grid(row=0, column=0, padx=(8, 2), pady=6, sticky="w")

        # Column 1: Original Title
        original_title = video.get('title', 'Unknown')
        orig_display = original_title[:70] + "..." if len(original_title) > 70 else original_title
        orig_label = ctk.CTkLabel(row_frame, text=orig_display, anchor="w")
        orig_label.grid(row=0, column=1, padx=5, pady=6, sticky="w")

        # Column 2: AI Title (Best)
        if best_attempt:
            ai_title = best_attempt.get('generated_title', '')
        else:
            ai_title = "No AI results"
        ai_display = ai_title[:70] + "..." if len(ai_title) > 70 else ai_title
        ai_label = ctk.CTkLabel(row_frame, text=ai_display, anchor="w")
        ai_label.grid(row=0, column=2, padx=5, pady=6, sticky="w")

        # Column 3: AI Artist
        ai_artist = best_attempt.get('artist', '-') if best_attempt else "-"
        artist_label = ctk.CTkLabel(row_frame, text=ai_artist, anchor="w")
        artist_label.grid(row=0, column=3, padx=5, pady=6, sticky="w")

        # Column 4: Models
        models_str = ", ".join([a['model_name'].split(':')[0] for a in attempts[:3]])
        if len(attempts) > 3:
            models_str += "..."
        models_label = ctk.CTkLabel(
            row_frame, text=models_str, anchor="w",
            text_color=self.COLOR_MUTED_TEXT
        )
        models_label.grid(row=0, column=4, padx=5, pady=6, sticky="w")

        # Column 5: Confidence
        if best_attempt:
            conf_text = f"{best_attempt.get('confidence', 0):.0%}"
        else:
            conf_text = "-"
        conf_label = ctk.CTkLabel(row_frame, text=conf_text, anchor="w")
        conf_label.grid(row=0, column=5, padx=5, pady=6, sticky="w")

        # Column 6: Status
        if approved:
            status_text = "Approved"
            status_color = "green"
        else:
            status_text = "Pending"
            status_color = self.COLOR_MUTED_TEXT
        status_label = ctk.CTkLabel(
            row_frame, text=status_text, anchor="w",
            text_color=status_color
        )
        status_label.grid(row=0, column=6, padx=5, pady=6, sticky="w")

        # Store references
        self.row_widgets[video_id] = row_frame
        self.row_colors[video_id] = base_color

        # Apply selected color if already selected
        if video_id in self.selected_rows:
            row_frame.configure(fg_color=self.COLOR_ROW_SELECTED)

        # Bind hover and double-click events
        self._bind_row_events(row_frame, video_id, base_color)

    def _bind_row_events(self, frame, video_id, base_color):
        """Bind hover and double-click events to row and all children."""
        def on_enter(event):
            frame.configure(fg_color=self.COLOR_ROW_HOVER)

        def on_leave(event):
            # Check if mouse truly left the row (not just moved to a child widget)
            x, y = frame.winfo_pointerxy()
            try:
                widget_under = frame.winfo_containing(x, y)
                if widget_under is not None and str(widget_under).startswith(str(frame)):
                    return  # Still inside the row
            except Exception:
                pass

            # Revert to selected color or base color
            if video_id in self.selected_rows:
                frame.configure(fg_color=self.COLOR_ROW_SELECTED)
            else:
                frame.configure(fg_color=base_color)

        def on_double_click(event):
            for v in self.videos:
                if v['video_id'] == video_id:
                    self._open_edit_dialog(v)
                    break

        # Bind to frame
        frame.bind("<Enter>", on_enter)
        frame.bind("<Leave>", on_leave)
        frame.bind("<Double-Button-1>", on_double_click)

        # Bind double-click to all child labels so clicks on text work
        for child in frame.winfo_children():
            child.bind("<Double-Button-1>", on_double_click)

    def _on_checkbox_toggle(self, video_id):
        """Handle checkbox toggle for a row."""
        var = self.row_vars.get(video_id)
        if not var:
            return

        if var.get() == 1:
            self.selected_rows.add(video_id)
            if video_id in self.row_widgets:
                self.row_widgets[video_id].configure(fg_color=self.COLOR_ROW_SELECTED)
        else:
            self.selected_rows.discard(video_id)
            base = self.row_colors.get(video_id, self.COLOR_ROW_ODD)
            if video_id in self.row_widgets:
                self.row_widgets[video_id].configure(fg_color=base)

        self._update_stats()

    def _open_edit_dialog(self, video):
        """Open edit dialog for a single video."""
        video_id = video['video_id']
        attempts = self.video_attempts.get(video_id, [])
        best_attempt = self.video_best_attempt.get(video_id)

        # Create edit popup
        edit_window = ctk.CTkToplevel(self)
        edit_window.title(f"Edit: {video.get('title', '')[:50]}...")
        edit_window.geometry("800x600")
        edit_window.transient(self)
        edit_window.grab_set()

        # Original title section
        original_frame = ctk.CTkFrame(edit_window)
        original_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            original_frame, text="Original Title:",
            font=("Arial", 12, "bold")
        ).pack(anchor="w", padx=10, pady=(10, 0))
        ctk.CTkLabel(
            original_frame, text=video.get('title', ''),
            wraplength=700, anchor="w"
        ).pack(anchor="w", padx=10, pady=(5, 10))

        # AI suggestions section
        if attempts:
            suggestions_frame = ctk.CTkFrame(edit_window)
            suggestions_frame.pack(fill="both", expand=True, padx=20, pady=10)

            ctk.CTkLabel(
                suggestions_frame,
                text="AI Suggestions (click to select):",
                font=("Arial", 12, "bold")
            ).pack(anchor="w", padx=10, pady=(10, 5))

            selected_attempt_var = tk.StringVar(value=best_attempt['model_name'] if best_attempt else "")

            suggestions_scroll = ctk.CTkScrollableFrame(suggestions_frame, height=200)
            suggestions_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

            for attempt in attempts:
                card = ctk.CTkFrame(suggestions_scroll)
                card.pack(fill="x", pady=3)

                radio = ctk.CTkRadioButton(
                    card,
                    text="",
                    variable=selected_attempt_var,
                    value=attempt['model_name']
                )
                radio.pack(side="left", padx=10, pady=8)

                info_frame = ctk.CTkFrame(card, fg_color="transparent")
                info_frame.pack(side="left", fill="x", expand=True, pady=5)

                ctk.CTkLabel(
                    info_frame,
                    text=f"{attempt['model_name']} ({attempt.get('confidence', 0):.0%})",
                    font=("Arial", 10, "bold")
                ).pack(anchor="w")
                ctk.CTkLabel(
                    info_frame,
                    text=f"Title: {attempt.get('generated_title', '')}",
                    anchor="w"
                ).pack(anchor="w")
                artist_text = f"Artist: {attempt.get('artist', '')}"
                cover_artist = attempt.get('cover_artist')
                if cover_artist:
                    artist_text += f"  |  Cover: {cover_artist}"
                ctk.CTkLabel(
                    info_frame,
                    text=artist_text,
                    anchor="w"
                ).pack(anchor="w")
        else:
            ctk.CTkLabel(
                edit_window,
                text="No AI suggestions available. Click 'Reprocess' to generate.",
                text_color="orange"
            ).pack(pady=20)
            selected_attempt_var = tk.StringVar(value="")

        # Manual edit fields section
        edit_frame = ctk.CTkFrame(edit_window)
        edit_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            edit_frame, text="Edit Metadata:",
            font=("Arial", 12, "bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))

        # Title
        ctk.CTkLabel(edit_frame, text="Title:", anchor="w").pack(anchor="w", padx=10)
        title_entry = ctk.CTkEntry(edit_frame)
        title_entry.pack(fill="x", padx=10, pady=5)
        if best_attempt:
            title_entry.insert(0, best_attempt.get('generated_title', ''))

        # Artist (original)
        ctk.CTkLabel(edit_frame, text="Artist:", anchor="w").pack(anchor="w", padx=10)
        artist_entry = ctk.CTkEntry(edit_frame)
        artist_entry.pack(fill="x", padx=10, pady=5)
        if best_attempt:
            artist_entry.insert(0, best_attempt.get('artist', ''))

        # Cover Artist
        ctk.CTkLabel(edit_frame, text="Cover Artist:", anchor="w").pack(anchor="w", padx=10)
        cover_artist_entry = ctk.CTkEntry(edit_frame, placeholder_text="Cover/performing artist (leave empty for originals)")
        cover_artist_entry.pack(fill="x", padx=10, pady=5)
        if best_attempt and best_attempt.get('cover_artist'):
            cover_artist_entry.insert(0, best_attempt.get('cover_artist', ''))

        # Album
        ctk.CTkLabel(edit_frame, text="Album:", anchor="w").pack(anchor="w", padx=10)
        album_entry = ctk.CTkEntry(edit_frame)
        album_entry.pack(fill="x", padx=10, pady=5)

        # Tags
        ctk.CTkLabel(edit_frame, text="Tags (comma-separated):", anchor="w").pack(anchor="w", padx=10)
        tags_entry = ctk.CTkEntry(edit_frame)
        tags_entry.pack(fill="x", padx=10, pady=(5, 10))
        if best_attempt:
            tags = best_attempt.get('tags', [])
            if isinstance(tags, str):
                try:
                    tags = json.loads(tags)
                except Exception:
                    tags = []
            tags_entry.insert(0, ', '.join(tags) if tags else '')

        # Buttons
        button_frame = ctk.CTkFrame(edit_window, fg_color="transparent")
        button_frame.pack(pady=15)

        def save_and_close():
            title = title_entry.get().strip()
            artist = artist_entry.get().strip()
            cover_artist = cover_artist_entry.get().strip()
            album = album_entry.get().strip()
            tags_str = tags_entry.get().strip()

            if not title or not artist:
                messagebox.showwarning("Missing Fields", "Title and Artist are required.")
                return

            tags = [t.strip() for t in tags_str.split(',') if t.strip()]

            # Get selected attempt ID
            selected_model = selected_attempt_var.get()
            selected_attempt_id = None
            if selected_model:
                for attempt in attempts:
                    if attempt['model_name'] == selected_model:
                        selected_attempt_id = attempt['attempt_id']
                        break

            # Save to database
            try:
                self.db.add_approved_metadata(
                    video_id=video_id,
                    selected_attempt_id=selected_attempt_id,
                    final_title=title,
                    final_artist=artist,
                    cover_artist=cover_artist or None,
                    album=album or None,
                    tags=tags
                )
                self.logger.info(f"Approved metadata for video: {video_id}")
                edit_window.destroy()
                self._populate_table()  # Refresh table
                self._update_stats()
            except Exception as e:
                self.logger.error(f"Failed to save metadata: {e}")
                messagebox.showerror("Error", f"Failed to save: {e}")

        ctk.CTkButton(
            button_frame, text="Save", width=120,
            fg_color="green", hover_color="darkgreen",
            command=save_and_close
        ).pack(side="left", padx=5)
        ctk.CTkButton(
            button_frame, text="Cancel", width=120,
            fg_color="gray", hover_color="darkgray",
            command=edit_window.destroy
        ).pack(side="left", padx=5)

    def _select_all(self):
        """Select all rows."""
        self.selected_rows.clear()
        for video_id, var in self.row_vars.items():
            var.set(1)
            self.selected_rows.add(video_id)
            if video_id in self.row_widgets:
                self.row_widgets[video_id].configure(fg_color=self.COLOR_ROW_SELECTED)
        self._update_stats()

    def _deselect_all(self):
        """Deselect all rows."""
        for video_id, var in self.row_vars.items():
            var.set(0)
            base = self.row_colors.get(video_id, self.COLOR_ROW_ODD)
            if video_id in self.row_widgets:
                self.row_widgets[video_id].configure(fg_color=base)
        self.selected_rows.clear()
        self._update_stats()

    def _update_stats(self):
        """Update statistics label."""
        total = len(self.videos)
        selected = len(self.selected_rows)
        approved_count = sum(1 for v in self.videos if self.db.get_approved_metadata(v['video_id']))

        self.stats_label.configure(text=f"Total: {total} | Selected: {selected} | Approved: {approved_count}")

    def _approve_selected(self):
        """Approve all selected rows with best AI suggestions."""
        if not self.selected_rows:
            messagebox.showwarning("No Selection", "Please select rows to approve.")
            return

        # Confirm
        if not messagebox.askyesno("Confirm Approval", f"Approve {len(self.selected_rows)} selected song(s) with their best AI suggestions?"):
            return

        success_count = 0
        fail_count = 0

        for video_id in self.selected_rows:
            try:
                best_attempt = self.video_best_attempt.get(video_id)
                if not best_attempt:
                    self.logger.warning(f"No AI attempt for video: {video_id}")
                    fail_count += 1
                    continue

                # Extract tags
                tags = best_attempt.get('tags', [])
                if isinstance(tags, str):
                    try:
                        tags = json.loads(tags)
                    except Exception:
                        tags = []

                # Save to database
                self.db.add_approved_metadata(
                    video_id=video_id,
                    selected_attempt_id=best_attempt['attempt_id'],
                    final_title=best_attempt.get('generated_title', ''),
                    final_artist=best_attempt.get('artist', ''),
                    cover_artist=best_attempt.get('cover_artist') or None,
                    album=None,
                    tags=tags
                )
                success_count += 1

            except Exception as e:
                self.logger.error(f"Failed to approve video {video_id}: {e}")
                fail_count += 1

        # Refresh table
        self._populate_table()
        self._update_stats()

        # Clear selection
        self._deselect_all()

        messagebox.showinfo("Approval Complete", f"Approved: {success_count}\nFailed: {fail_count}")

    def _reprocess_selected(self):
        """Reprocess selected rows with chosen model."""
        if not self.selected_rows:
            messagebox.showwarning("No Selection", "Please select rows to reprocess.")
            return

        selected_model = self.reprocess_model_var.get()
        if not selected_model:
            messagebox.showwarning("No Model", "Please select a model for reprocessing.")
            return

        # Confirm
        if not messagebox.askyesno("Confirm Reprocess", f"Reprocess {len(self.selected_rows)} selected song(s) with {selected_model}?"):
            return

        # Show progress
        self.status_label.configure(text=f"Reprocessing {len(self.selected_rows)} songs with {selected_model}...")
        self.update()

        # Get videos to reprocess
        videos_to_process = []
        for video_id in self.selected_rows:
            for video in self.videos:
                if video['video_id'] == video_id:
                    videos_to_process.append(video)
                    break

        # Run in background thread
        def reprocess_thread():
            try:
                from ai.title_processor import TitleProcessor

                processor = TitleProcessor(
                    db=self.db,
                    ollama_url=self.config.ollama_url,
                    models=[selected_model],  # Single model
                    max_workers=1
                )

                success_count = 0
                fail_count = 0

                for video in videos_to_process:
                    try:
                        processor.regenerate_for_video(video['video_id'])
                        success_count += 1
                    except Exception as e:
                        self.logger.error(f"Failed to reprocess {video['video_id']}: {e}")
                        fail_count += 1

                # Update UI on main thread
                self.after(0, self._on_reprocess_complete, success_count, fail_count)

            except Exception as e:
                self.logger.error(f"Reprocessing failed: {e}")
                self.after(0, self._on_reprocess_error, str(e))

        thread = threading.Thread(target=reprocess_thread, daemon=True)
        thread.start()

    def _on_reprocess_complete(self, success_count, fail_count):
        """Handle reprocessing completion."""
        # Reload AI data
        self._load_ai_data()

        # Refresh table
        self._populate_table()
        self._update_stats()

        # Clear selection
        self._deselect_all()

        self.status_label.configure(text="Tip: Double-click a row to edit details, or select multiple and use bulk actions")

        messagebox.showinfo("Reprocessing Complete", f"Success: {success_count}\nFailed: {fail_count}")

    def _on_reprocess_error(self, error_msg):
        """Handle reprocessing error."""
        self.status_label.configure(text="Tip: Double-click a row to edit details, or select multiple and use bulk actions")
        messagebox.showerror("Reprocessing Failed", f"Error: {error_msg}")
