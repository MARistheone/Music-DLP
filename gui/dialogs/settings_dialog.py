"""
Settings Dialog

Tabbed settings dialog for configuring:
- Appearance (theme, font size)
- Download (cookies, format, sleep intervals)
- AI (Ollama URL, models, workers)
- Output (bitrates, formats, directories)
- Logging (level, file rotation)

Author: Music DLP Project
Version: 1.0.0
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path


class SettingsDialog(ctk.CTkToplevel):
    """
    Modal settings dialog with tabbed interface.
    """

    def __init__(self, parent, db, config, logger):
        """
        Initialize settings dialog.

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

        # Window configuration
        self.title("Settings")
        self.geometry("700x600")
        self.resizable(True, True)
        self.minsize(600, 500)

        # Center on parent
        self.transient(parent)
        self._center_on_parent(parent)

        # Store original values for cancel
        self._original_values = self._get_current_values()

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

    def _get_current_values(self):
        """Get current configuration values."""
        return {
            'theme_mode': self.config.theme_mode,
            'cookies_file': self.config.cookies_file,
            'download_format': self.config.download_format,
            'ollama_url': self.config.ollama_url,
            'ai_models': self.config.ai_models,
            'primary_ai_model': self.config.primary_ai_model,
            'use_all_models': self.config.use_all_models,
            'parallel_workers': self.config.parallel_workers,
            'thinking_mode': self.config.thinking_mode,
            'mp3_bitrate': self.config.mp3_bitrate,
            'm4a_bitrate': self.config.m4a_bitrate,
            'log_level': self.config.log_level,
        }

    def _create_widgets(self):
        """Create settings widgets."""
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="Settings",
            font=("Arial", 18, "bold")
        )
        title_label.pack(pady=(15, 10))

        # Tabview
        self.tabview = ctk.CTkTabview(self, width=650, height=450)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # Create tabs
        self.tabview.add("Appearance")
        self.tabview.add("Download")
        self.tabview.add("AI Processing")
        self.tabview.add("Output")
        self.tabview.add("Logging")

        # Populate tabs with error handling
        try:
            self._create_appearance_tab()
            self.logger.info("Created Appearance tab")
        except Exception as e:
            self.logger.error(f"Failed to create Appearance tab: {e}")

        try:
            self._create_download_tab()
            self.logger.info("Created Download tab")
        except Exception as e:
            self.logger.error(f"Failed to create Download tab: {e}")

        try:
            self._create_ai_tab()
            self.logger.info("Created AI Processing tab")
        except Exception as e:
            self.logger.error(f"Failed to create AI Processing tab: {e}")
            # Show error in tab
            error_label = ctk.CTkLabel(
                self.tabview.tab("AI Processing"),
                text=f"Error loading AI Processing settings:\n{str(e)}",
                text_color="red"
            )
            error_label.pack(pady=20)

        try:
            self._create_output_tab()
            self.logger.info("Created Output tab")
        except Exception as e:
            self.logger.error(f"Failed to create Output tab: {e}")

        try:
            self._create_logging_tab()
            self.logger.info("Created Logging tab")
        except Exception as e:
            self.logger.error(f"Failed to create Logging tab: {e}")

        # Button frame
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=(0, 15))

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

        # Save button
        save_button = ctk.CTkButton(
            button_frame,
            text="Save",
            width=120,
            command=self._on_save
        )
        save_button.pack(side="left", padx=10)

    def _create_appearance_tab(self):
        """Create Appearance tab."""
        tab = self.tabview.tab("Appearance")

        # Theme selection
        theme_frame = ctk.CTkFrame(tab)
        theme_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(theme_frame, text="Theme:", font=("Arial", 12, "bold")).pack(anchor="w", pady=5)

        self.theme_var = ctk.StringVar(value=self.config.theme_mode)

        theme_radio_frame = ctk.CTkFrame(theme_frame, fg_color="transparent")
        theme_radio_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkRadioButton(
            theme_radio_frame,
            text="Dark",
            variable=self.theme_var,
            value="dark"
        ).pack(side="left", padx=10)

        ctk.CTkRadioButton(
            theme_radio_frame,
            text="Light",
            variable=self.theme_var,
            value="light"
        ).pack(side="left", padx=10)

        ctk.CTkRadioButton(
            theme_radio_frame,
            text="System",
            variable=self.theme_var,
            value="system"
        ).pack(side="left", padx=10)

    def _create_download_tab(self):
        """Create Download tab."""
        tab = self.tabview.tab("Download")

        # Cookies file
        cookies_frame = ctk.CTkFrame(tab)
        cookies_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(cookies_frame, text="Cookies File:", font=("Arial", 12, "bold")).pack(anchor="w", pady=5)
        ctk.CTkLabel(
            cookies_frame,
            text="Browser cookies for bot avoidance (Export with 'Get cookies.txt LOCALLY' extension)",
            text_color="gray",
            wraplength=600
        ).pack(anchor="w", padx=10)

        cookies_entry_frame = ctk.CTkFrame(cookies_frame, fg_color="transparent")
        cookies_entry_frame.pack(fill="x", pady=5)

        self.cookies_entry = ctk.CTkEntry(cookies_entry_frame, width=450)
        self.cookies_entry.pack(side="left", padx=(10, 5))
        self.cookies_entry.insert(0, self.config.cookies_file or "")

        browse_button = ctk.CTkButton(
            cookies_entry_frame,
            text="Browse",
            width=80,
            command=self._browse_cookies
        )
        browse_button.pack(side="left", padx=5)

        # Download format
        format_frame = ctk.CTkFrame(tab)
        format_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(format_frame, text="Download Format:", font=("Arial", 12, "bold")).pack(anchor="w", pady=5)

        self.format_entry = ctk.CTkEntry(format_frame, width=500)
        self.format_entry.pack(fill="x", padx=10, pady=5)
        self.format_entry.insert(0, self.config.download_format)

        ctk.CTkLabel(
            format_frame,
            text="Default: 251/bestaudio[ext=opus]/bestaudio",
            text_color="gray"
        ).pack(anchor="w", padx=10)

    def _create_ai_tab(self):
        """Create AI Processing tab."""
        tab = self.tabview.tab("AI Processing")

        # Make the tab scrollable for many settings
        scroll_frame = ctk.CTkScrollableFrame(tab)
        scroll_frame.pack(fill="both", expand=True, padx=0, pady=0)

        # Use scroll_frame as container instead of tab
        container = scroll_frame

        # Ollama URL
        url_frame = ctk.CTkFrame(container)
        url_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(url_frame, text="Ollama URL:", font=("Arial", 12, "bold")).pack(anchor="w", pady=5)

        self.ollama_url_entry = ctk.CTkEntry(url_frame, width=500)
        self.ollama_url_entry.pack(fill="x", padx=10, pady=5)
        self.ollama_url_entry.insert(0, self.config.ollama_url)

        # Primary Model Selection
        primary_model_frame = ctk.CTkFrame(container)
        primary_model_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(primary_model_frame, text="Primary Model:", font=("Arial", 12, "bold")).pack(anchor="w", pady=5)
        ctk.CTkLabel(
            primary_model_frame,
            text="Select the AI model to use for processing (used when 'Use All Models' is disabled)",
            text_color="gray"
        ).pack(anchor="w", padx=10)

        # Get available models from config
        available_models = self.config.ai_models

        self.primary_model_dropdown = ctk.CTkComboBox(
            primary_model_frame,
            values=available_models,
            width=500
        )
        self.primary_model_dropdown.pack(fill="x", padx=10, pady=5)
        self.primary_model_dropdown.set(self.config.primary_ai_model)

        # Use All Models Toggle
        use_all_frame = ctk.CTkFrame(container)
        use_all_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            use_all_frame,
            text="Use All Models:",
            font=("Arial", 12, "bold")
        ).pack(anchor="w", pady=5)

        ctk.CTkLabel(
            use_all_frame,
            text="Enable to process with all models in parallel (slower but gives more options). Disable to use only the primary model (faster, recommended for 95% of songs).",
            text_color="gray",
            wraplength=600
        ).pack(anchor="w", padx=10)

        self.use_all_models_var = ctk.BooleanVar(value=self.config.use_all_models)
        ctk.CTkCheckBox(
            use_all_frame,
            text="Run All Models (3 models in parallel)",
            variable=self.use_all_models_var
        ).pack(anchor="w", padx=10, pady=5)

        # All Models List
        models_frame = ctk.CTkFrame(container)
        models_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(models_frame, text="AI Models:", font=("Arial", 12, "bold")).pack(anchor="w", pady=5)
        ctk.CTkLabel(
            models_frame,
            text="Models to use for title processing (comma-separated)",
            text_color="gray"
        ).pack(anchor="w", padx=10)

        self.models_entry = ctk.CTkEntry(models_frame, width=500)
        self.models_entry.pack(fill="x", padx=10, pady=5)
        self.models_entry.insert(0, ', '.join(self.config.ai_models))

        # Parallel workers
        workers_frame = ctk.CTkFrame(container)
        workers_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(workers_frame, text="Parallel Workers:", font=("Arial", 12, "bold")).pack(anchor="w", pady=5)

        self.workers_slider = ctk.CTkSlider(
            workers_frame,
            from_=1,
            to=5,
            number_of_steps=4,
            width=400
        )
        self.workers_slider.pack(padx=10, pady=5)
        self.workers_slider.set(self.config.parallel_workers)

        self.workers_label = ctk.CTkLabel(workers_frame, text=f"{self.config.parallel_workers} workers")
        self.workers_label.pack(padx=10)

        self.workers_slider.configure(command=lambda v: self.workers_label.configure(text=f"{int(v)} workers"))

        # Thinking mode toggle
        thinking_frame = ctk.CTkFrame(container)
        thinking_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            thinking_frame,
            text="AI Thinking Mode:",
            font=("Arial", 12, "bold")
        ).pack(anchor="w", pady=5)

        ctk.CTkLabel(
            thinking_frame,
            text="Enable extended processing for more accurate results (may be slower)",
            text_color="gray",
            wraplength=600
        ).pack(anchor="w", padx=10)

        self.thinking_var = ctk.BooleanVar(value=self.config.thinking_mode)
        ctk.CTkCheckBox(
            thinking_frame,
            text="Enable Thinking Mode",
            variable=self.thinking_var
        ).pack(anchor="w", padx=10, pady=5)

    def _create_output_tab(self):
        """Create Output tab."""
        tab = self.tabview.tab("Output")

        # MP3 bitrate
        mp3_frame = ctk.CTkFrame(tab)
        mp3_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(mp3_frame, text="MP3 Bitrate:", font=("Arial", 12, "bold")).pack(anchor="w", pady=5)

        self.mp3_bitrate_var = ctk.StringVar(value=self.config.mp3_bitrate)

        bitrate_frame = ctk.CTkFrame(mp3_frame, fg_color="transparent")
        bitrate_frame.pack(fill="x", padx=10, pady=5)

        for bitrate in ['192', '256', '320']:
            ctk.CTkRadioButton(
                bitrate_frame,
                text=f"{bitrate} kbps",
                variable=self.mp3_bitrate_var,
                value=bitrate
            ).pack(side="left", padx=10)

        # M4A bitrate
        m4a_frame = ctk.CTkFrame(tab)
        m4a_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(m4a_frame, text="M4A Bitrate:", font=("Arial", 12, "bold")).pack(anchor="w", pady=5)

        self.m4a_bitrate_var = ctk.StringVar(value=self.config.m4a_bitrate)

        bitrate_frame2 = ctk.CTkFrame(m4a_frame, fg_color="transparent")
        bitrate_frame2.pack(fill="x", padx=10, pady=5)

        for bitrate in ['192', '256', '320']:
            ctk.CTkRadioButton(
                bitrate_frame2,
                text=f"{bitrate} kbps",
                variable=self.m4a_bitrate_var,
                value=bitrate
            ).pack(side="left", padx=10)

    def _create_logging_tab(self):
        """Create Logging tab."""
        tab = self.tabview.tab("Logging")

        # Log level
        level_frame = ctk.CTkFrame(tab)
        level_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(level_frame, text="Log Level:", font=("Arial", 12, "bold")).pack(anchor="w", pady=5)

        self.log_level_var = ctk.StringVar(value=self.config.log_level)

        level_radio_frame = ctk.CTkFrame(level_frame, fg_color="transparent")
        level_radio_frame.pack(fill="x", padx=10, pady=5)

        for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:
            ctk.CTkRadioButton(
                level_radio_frame,
                text=level,
                variable=self.log_level_var,
                value=level
            ).pack(side="left", padx=10)

    def _browse_cookies(self):
        """Browse for cookies file."""
        filename = filedialog.askopenfilename(
            title="Select Cookies File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialdir=str(Path.home())
        )

        if filename:
            self.cookies_entry.delete(0, 'end')
            self.cookies_entry.insert(0, filename)

    def _on_save(self):
        """Save settings and close dialog."""
        try:
            # Save all settings
            self.config.theme_mode = self.theme_var.get()
            self.config.cookies_file = self.cookies_entry.get().strip() or ''
            self.config.download_format = self.format_entry.get().strip()
            self.config.ollama_url = self.ollama_url_entry.get().strip()

            # Parse models list
            models_str = self.models_entry.get().strip()
            self.config.ai_models = [m.strip() for m in models_str.split(',') if m.strip()]

            # Save primary model and use_all_models setting
            self.config.primary_ai_model = self.primary_model_dropdown.get()
            self.config.use_all_models = self.use_all_models_var.get()

            self.config.parallel_workers = int(self.workers_slider.get())
            self.config.thinking_mode = self.thinking_var.get()
            self.config.mp3_bitrate = self.mp3_bitrate_var.get()
            self.config.m4a_bitrate = self.m4a_bitrate_var.get()
            self.config.log_level = self.log_level_var.get()

            self.logger.info("Settings saved")

            messagebox.showinfo("Settings Saved", "Settings have been saved successfully.")
            self.destroy()

        except Exception as e:
            self.logger.error(f"Failed to save settings: {e}")
            messagebox.showerror("Error", f"Failed to save settings:\n{e}")

    def _on_cancel(self):
        """Cancel and restore original values."""
        # Restore original values
        for key, value in self._original_values.items():
            setattr(self.config, key, value)

        self.destroy()
