"""
AI Review Dialog

Batch AI title review dialog for:
- Side-by-side comparison of AI model suggestions
- Navigation between songs
- Manual editing
- Regenerate AI
- Approve and next

Author: Music DLP Project
Version: 1.0.0
"""

import customtkinter as ctk
from tkinter import messagebox
import json
from typing import List, Dict


class AIReviewDialog(ctk.CTkToplevel):
    """
    Modal dialog for batch reviewing AI-generated titles.

    Shows 3 AI model suggestions side-by-side and allows user to
    select best one or manually edit metadata.
    """

    def __init__(self, parent, db, config, logger, videos: List[Dict]):
        """
        Initialize AI review dialog.

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

        self.current_index = 0  # Current video index
        self.selected_attempt_var = ctk.StringVar(value="")

        # Window configuration
        self.title(f"AI Title Review - {len(videos)} songs")
        self.geometry("900x700")
        self.resizable(True, True)
        self.minsize(800, 600)

        # Center on parent
        self.transient(parent)
        self._center_on_parent(parent)

        self._create_widgets()
        self._load_current_video()

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
        # Header frame
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(15, 10))

        # Progress label
        self.progress_label = ctk.CTkLabel(
            header_frame,
            text="Song 1 of X",
            font=("Arial", 14, "bold")
        )
        self.progress_label.pack(side="left")

        # Skip button
        skip_button = ctk.CTkButton(
            header_frame,
            text="Skip",
            width=80,
            fg_color="gray",
            hover_color="darkgray",
            command=self._skip_current
        )
        skip_button.pack(side="right", padx=5)

        # Original title frame
        original_frame = ctk.CTkFrame(self)
        original_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(original_frame, text="Original:", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=5)

        self.original_title_label = ctk.CTkLabel(
            original_frame,
            text="",
            wraplength=850,
            justify="left",
            anchor="w"
        )
        self.original_title_label.pack(fill="x", padx=20, pady=5)

        self.uploader_label = ctk.CTkLabel(
            original_frame,
            text="",
            text_color="gray"
        )
        self.uploader_label.pack(anchor="w", padx=20, pady=(0, 5))

        # AI suggestions frame (scrollable)
        suggestions_label = ctk.CTkLabel(
            self,
            text="AI Suggestions",
            font=("Arial", 14, "bold")
        )
        suggestions_label.pack(pady=(10, 5))

        self.suggestions_frame = ctk.CTkScrollableFrame(self, height=250)
        self.suggestions_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # Manual edit frame
        edit_frame = ctk.CTkFrame(self)
        edit_frame.pack(fill="x", padx=20, pady=10)

        # Header with label and checkbox
        edit_header_frame = ctk.CTkFrame(edit_frame, fg_color="transparent")
        edit_header_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            edit_header_frame,
            text="Manual Edit (Optional)",
            font=("Arial", 12, "bold")
        ).pack(side="left", padx=10)

        self.manual_edit_var = ctk.BooleanVar(value=False)
        manual_edit_checkbox = ctk.CTkCheckBox(
            edit_header_frame,
            text="Enable manual editing",
            variable=self.manual_edit_var,
            command=self._toggle_manual_edit
        )
        manual_edit_checkbox.pack(side="left", padx=20)

        # Title entry
        title_entry_frame = ctk.CTkFrame(edit_frame, fg_color="transparent")
        title_entry_frame.pack(fill="x", padx=10, pady=2)

        ctk.CTkLabel(title_entry_frame, text="Title:", width=60, anchor="w").pack(side="left", padx=(10, 5))
        self.title_entry = ctk.CTkEntry(title_entry_frame, width=600)
        self.title_entry.pack(side="left", fill="x", expand=True, padx=5)

        # Artist entry (original)
        artist_entry_frame = ctk.CTkFrame(edit_frame, fg_color="transparent")
        artist_entry_frame.pack(fill="x", padx=10, pady=2)

        ctk.CTkLabel(artist_entry_frame, text="Artist:", width=60, anchor="w").pack(side="left", padx=(10, 5))
        self.artist_entry = ctk.CTkEntry(artist_entry_frame, width=600)
        self.artist_entry.pack(side="left", fill="x", expand=True, padx=5)

        # Cover artist entry
        cover_artist_frame = ctk.CTkFrame(edit_frame, fg_color="transparent")
        cover_artist_frame.pack(fill="x", padx=10, pady=2)

        ctk.CTkLabel(cover_artist_frame, text="Cover:", width=60, anchor="w").pack(side="left", padx=(10, 5))
        self.cover_artist_entry = ctk.CTkEntry(cover_artist_frame, width=600, placeholder_text="Cover/performing artist (leave empty for originals)")
        self.cover_artist_entry.pack(side="left", fill="x", expand=True, padx=5)

        # Album entry
        album_entry_frame = ctk.CTkFrame(edit_frame, fg_color="transparent")
        album_entry_frame.pack(fill="x", padx=10, pady=2)

        ctk.CTkLabel(album_entry_frame, text="Album:", width=60, anchor="w").pack(side="left", padx=(10, 5))
        self.album_entry = ctk.CTkEntry(album_entry_frame, width=600)
        self.album_entry.pack(side="left", fill="x", expand=True, padx=5)

        # Tags entry
        tags_entry_frame = ctk.CTkFrame(edit_frame, fg_color="transparent")
        tags_entry_frame.pack(fill="x", padx=10, pady=(2, 10))

        ctk.CTkLabel(tags_entry_frame, text="Tags:", width=60, anchor="w").pack(side="left", padx=(10, 5))
        self.tags_entry = ctk.CTkEntry(tags_entry_frame, width=600)
        self.tags_entry.pack(side="left", fill="x", expand=True, padx=5)

        # Disable manual editing by default
        self.title_entry.configure(state="disabled")
        self.artist_entry.configure(state="disabled")
        self.cover_artist_entry.configure(state="disabled")
        self.album_entry.configure(state="disabled")
        self.tags_entry.configure(state="disabled")

        # Button frame
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=(0, 15))

        # Previous button
        self.prev_button = ctk.CTkButton(
            button_frame,
            text="◄ Previous",
            width=120,
            command=self._previous_song
        )
        self.prev_button.pack(side="left", padx=5)

        # Regenerate button (store as instance variable)
        self.regenerate_button = ctk.CTkButton(
            button_frame,
            text="Regenerate AI",
            width=130,
            fg_color="orange",
            hover_color="darkorange",
            command=self._regenerate_ai
        )
        self.regenerate_button.pack(side="left", padx=5)

        # Approve & Next button (store as instance variable)
        self.approve_button = ctk.CTkButton(
            button_frame,
            text="Approve & Next ►",
            width=150,
            fg_color="green",
            hover_color="darkgreen",
            command=self._approve_and_next
        )
        self.approve_button.pack(side="left", padx=5)

    def _load_current_video(self):
        """Load current video data and AI suggestions."""
        if self.current_index >= len(self.videos):
            # All done
            messagebox.showinfo("Review Complete", "All videos have been reviewed!")
            self.destroy()
            return

        video = self.videos[self.current_index]
        video_id = video['video_id']

        # Update progress label
        self.progress_label.configure(text=f"Song {self.current_index + 1} of {len(self.videos)}")

        # Update original title
        self.original_title_label.configure(text=video.get('title', 'Unknown'))
        self.uploader_label.configure(text=f"Uploader: {video.get('uploader', 'Unknown')}")

        # Enable/disable previous button
        self.prev_button.configure(state="normal" if self.current_index > 0 else "disabled")

        # Load AI suggestions
        self._load_ai_suggestions(video_id)

        # Clear manual edit fields
        self.title_entry.delete(0, 'end')
        self.artist_entry.delete(0, 'end')
        self.cover_artist_entry.delete(0, 'end')
        self.album_entry.delete(0, 'end')
        self.tags_entry.delete(0, 'end')

    def _load_ai_suggestions(self, video_id):
        """
        Load AI suggestions for video.

        Args:
            video_id: Video ID
        """
        # Clear existing suggestions
        for widget in self.suggestions_frame.winfo_children():
            widget.destroy()

        self.selected_attempt_var.set("")

        # Get AI attempts from database
        try:
            attempts = self.db.get_ai_attempts(video_id)

            if not attempts:
                # No AI attempts found
                no_attempts_label = ctk.CTkLabel(
                    self.suggestions_frame,
                    text="No AI suggestions found. Click 'Regenerate AI' to generate.",
                    text_color="orange"
                )
                no_attempts_label.pack(pady=20)
                return

            # Sort by confidence (highest first)
            attempts.sort(key=lambda a: a.get('confidence', 0), reverse=True)

            # Create suggestion cards
            for attempt in attempts:
                self._create_suggestion_card(attempt)

            # Auto-select highest confidence
            if attempts:
                self.selected_attempt_var.set(str(attempts[0]['attempt_id']))
                self._on_suggestion_selected(attempts[0])

        except Exception as e:
            self.logger.error(f"Failed to load AI suggestions: {e}")
            messagebox.showerror("Error", f"Failed to load suggestions:\n{e}")

    def _create_suggestion_card(self, attempt: Dict):
        """
        Create a suggestion card widget.

        Args:
            attempt: AI attempt dict
        """
        model_name = attempt['model_name']

        # Card frame
        card = ctk.CTkFrame(self.suggestions_frame)
        card.pack(fill="x", padx=5, pady=5)

        # Radio button for selection
        radio = ctk.CTkRadioButton(
            card,
            text="",
            variable=self.selected_attempt_var,
            value=str(attempt['attempt_id']),
            command=lambda: self._on_suggestion_selected(attempt)
        )
        radio.grid(row=0, column=0, rowspan=5, padx=10, pady=10, sticky="n")

        # Model name and confidence with timestamp
        generation_date = attempt.get('generation_date', '')
        if generation_date:
            # Parse and format timestamp
            from datetime import datetime
            try:
                dt = datetime.fromisoformat(generation_date.replace('Z', '+00:00'))
                timestamp_str = dt.strftime("%b %d, %I:%M %p")
            except:
                timestamp_str = generation_date[:16]  # Fallback
            header_text = f"{model_name} (Confidence: {attempt.get('confidence', 0):.0%}) - {timestamp_str}"
        else:
            header_text = f"{model_name} (Confidence: {attempt.get('confidence', 0):.0%})"

        ctk.CTkLabel(card, text=header_text, font=("Arial", 11, "bold")).grid(row=0, column=1, sticky="w", padx=5, pady=2)

        # Attempt ID badge
        attempt_id_label = ctk.CTkLabel(
            card,
            text=f"Attempt #{attempt['attempt_id']}",
            font=("Arial", 9),
            text_color="gray"
        )
        attempt_id_label.grid(row=0, column=2, sticky="e", padx=5)

        # Delete button
        delete_button = ctk.CTkButton(
            card,
            text="✕",
            width=30,
            height=30,
            fg_color="red",
            hover_color="darkred",
            command=lambda a=attempt: self._delete_attempt(a)
        )
        delete_button.grid(row=0, column=3, padx=5, pady=5, sticky="ne")

        # Title
        title_text = f"Title: {attempt.get('generated_title', 'N/A')}"
        ctk.CTkLabel(card, text=title_text, wraplength=700, anchor="w").grid(row=1, column=1, sticky="w", padx=5, pady=2)

        # Artist
        artist_text = f"Artist: {attempt.get('artist', 'N/A')}"
        cover_artist = attempt.get('cover_artist')
        if cover_artist:
            artist_text += f"  |  Cover: {cover_artist}"
        ctk.CTkLabel(card, text=artist_text).grid(row=2, column=1, sticky="w", padx=5, pady=2)

        # Tags
        tags = attempt.get('tags', [])
        if isinstance(tags, str):
            try:
                tags = json.loads(tags)
            except:
                tags = []
        tags_text = f"Tags: {', '.join(tags) if tags else 'None'}"
        ctk.CTkLabel(card, text=tags_text, text_color="gray").grid(row=3, column=1, sticky="w", padx=5, pady=2)

        # Processing time
        processing_time = attempt.get('processing_time', 0)
        time_text = f"Processing time: {processing_time:.2f}s"
        ctk.CTkLabel(card, text=time_text, text_color="gray", font=("Arial", 9)).grid(
            row=4, column=1, sticky="w", padx=5, pady=2
        )

    def _on_suggestion_selected(self, attempt: Dict):
        """
        Handle suggestion selection.

        Args:
            attempt: Selected AI attempt dict
        """
        # Temporarily enable fields to populate them
        if not self.manual_edit_var.get():
            self.title_entry.configure(state="normal")
            self.artist_entry.configure(state="normal")
            self.cover_artist_entry.configure(state="normal")
            self.album_entry.configure(state="normal")
            self.tags_entry.configure(state="normal")

        # Populate manual edit fields with selected suggestion
        self.title_entry.delete(0, 'end')
        self.title_entry.insert(0, attempt.get('generated_title', ''))

        self.artist_entry.delete(0, 'end')
        self.artist_entry.insert(0, attempt.get('artist', ''))

        self.cover_artist_entry.delete(0, 'end')
        cover_artist = attempt.get('cover_artist', '')
        if cover_artist:
            self.cover_artist_entry.insert(0, cover_artist)

        self.album_entry.delete(0, 'end')
        # Album is not in AI suggestions, leave empty

        self.tags_entry.delete(0, 'end')
        tags = attempt.get('tags', [])
        if isinstance(tags, str):
            try:
                tags = json.loads(tags)
            except:
                tags = []
        self.tags_entry.insert(0, ', '.join(tags) if tags else '')

        # Disable again if manual edit mode is off
        if not self.manual_edit_var.get():
            self.title_entry.configure(state="disabled")
            self.artist_entry.configure(state="disabled")
            self.cover_artist_entry.configure(state="disabled")
            self.album_entry.configure(state="disabled")
            self.tags_entry.configure(state="disabled")

    def _toggle_manual_edit(self):
        """Enable or disable manual editing fields."""
        state = "normal" if self.manual_edit_var.get() else "disabled"
        self.title_entry.configure(state=state)
        self.artist_entry.configure(state=state)
        self.cover_artist_entry.configure(state=state)
        self.album_entry.configure(state=state)
        self.tags_entry.configure(state=state)

    def _delete_attempt(self, attempt: Dict):
        """Delete an AI attempt after user confirmation."""
        model_name = attempt['model_name']
        confidence = attempt.get('confidence', 0)

        confirm = messagebox.askyesno(
            "Delete Attempt",
            f"Delete this AI suggestion?\n\n"
            f"Model: {model_name}\n"
            f"Confidence: {confidence:.0%}\n"
            f"Title: {attempt.get('generated_title', 'N/A')}"
        )

        if confirm:
            try:
                self.db.delete_ai_attempt(attempt['attempt_id'])
                self.logger.info(f"Deleted AI attempt {attempt['attempt_id']}")

                # Refresh suggestions
                video = self.videos[self.current_index]
                self._load_ai_suggestions(video['video_id'])

            except Exception as e:
                self.logger.error(f"Failed to delete attempt: {e}")
                messagebox.showerror("Error", f"Failed to delete:\n{e}")

    def _previous_song(self):
        """Go to previous song."""
        if self.current_index > 0:
            self.current_index -= 1
            self._load_current_video()

    def _skip_current(self):
        """Skip current song without approving."""
        self.logger.info(f"Skipped song {self.current_index + 1}")
        self.current_index += 1
        self._load_current_video()

    def _approve_and_next(self):
        """Approve current song and move to next."""
        video = self.videos[self.current_index]
        video_id = video['video_id']

        # Get metadata from manual edit fields
        title = self.title_entry.get().strip()
        artist = self.artist_entry.get().strip()
        cover_artist = self.cover_artist_entry.get().strip()
        album = self.album_entry.get().strip()
        tags_str = self.tags_entry.get().strip()

        # Validate required fields
        if not title:
            messagebox.showwarning("Missing Title", "Title is required.")
            return

        if not artist:
            messagebox.showwarning("Missing Artist", "Artist is required.")
            return

        # Parse tags
        tags = [t.strip() for t in tags_str.split(',') if t.strip()]

        # Get selected attempt ID (if any)
        selected_attempt_id = None
        selected_attempt_str = self.selected_attempt_var.get()
        if selected_attempt_str:
            selected_attempt_id = int(selected_attempt_str)

        # Save approved metadata to database
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

            # Move to next song
            self.current_index += 1
            self._load_current_video()

        except Exception as e:
            self.logger.error(f"Failed to save approved metadata: {e}")
            messagebox.showerror("Error", f"Failed to save metadata:\n{e}")

    def _regenerate_ai(self):
        """Regenerate AI suggestions for current video."""
        video = self.videos[self.current_index]
        video_id = video['video_id']

        self.logger.info(f"Regenerating AI for video: {video_id}")

        # Disable buttons during regeneration
        self.regenerate_button.configure(state="disabled", text="Processing...")
        self.approve_button.configure(state="disabled")
        self.prev_button.configure(state="disabled")

        # Import here to avoid circular dependency
        from ai.title_processor import TitleProcessor
        import threading

        def regenerate_thread():
            """Run regeneration in background thread."""
            try:
                # Initialize processor with active models
                active_models = self.config.active_ai_models
                self.logger.info(f"Regenerating with {len(active_models)} model(s): {', '.join(active_models)}")

                processor = TitleProcessor(
                    db=self.db,
                    ollama_url=self.config.ollama_url,
                    models=active_models,  # Use active models based on settings
                    max_workers=1  # Single video, sequential is fine
                )

                # Regenerate with all models
                results = processor.regenerate_for_video(video_id)

                # Update UI on main thread
                self.after(0, self._on_regenerate_complete, results)

            except Exception as e:
                self.logger.error(f"Regeneration failed: {e}")
                self.after(0, self._on_regenerate_error, str(e))

        # Start background thread
        thread = threading.Thread(target=regenerate_thread, daemon=True)
        thread.start()

    def _on_regenerate_complete(self, results):
        """Handle regeneration completion."""
        # Re-enable buttons
        self.regenerate_button.configure(state="normal", text="Regenerate AI")
        self.approve_button.configure(state="normal")

        # Enable/disable previous button based on index
        self.prev_button.configure(state="normal" if self.current_index > 0 else "disabled")

        # Refresh suggestions to show new attempts
        video = self.videos[self.current_index]
        self._load_ai_suggestions(video['video_id'])

        # Show success message
        success_count = sum(1 for r in results if r.success)
        messagebox.showinfo(
            "Regeneration Complete",
            f"Generated {success_count}/{len(results)} new suggestions."
        )

    def _on_regenerate_error(self, error_msg):
        """Handle regeneration error."""
        # Re-enable buttons
        self.regenerate_button.configure(state="normal", text="Regenerate AI")
        self.approve_button.configure(state="normal")
        self.prev_button.configure(state="normal" if self.current_index > 0 else "disabled")

        # Show error message
        messagebox.showerror("Regeneration Failed", f"Error: {error_msg}")
