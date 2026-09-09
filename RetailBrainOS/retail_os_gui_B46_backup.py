"""
Retail Brain OS
Main Desktop GUI

Phase B-4.1
GUI <-> RetailVisionRuntime integration
with fixed application layout and live dashboard.
"""

from __future__ import annotations

import csv
import json
import os
import threading
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from pathlib import Path

import cv2
from PIL import Image, ImageTk

from app.gui.live_overlay import (
    render_live_frame,
)

from app.gui.zone_setup_gui import (
    ZoneSetupWindow,
)

from app.gui.live_dashboard import (
    LiveDashboard,
)

from app.gui.zone_management_panel import (
    ZoneManagementPanel,
)

from app.intelligence.retail_vision_runtime import (
    RetailVisionRuntime,
)


class RetailBrainOSApp:
    """
    Main Retail Brain OS desktop application.

    GUI owns:
        - Presentation
        - User controls
        - Dashboard

    RetailVisionRuntime owns:
        - Camera
        - Detector
        - Tracker
        - Zone Engine
        - Intelligence Engine
    """

    def __init__(self) -> None:

        self.root = tk.Tk()

        self.root.title(
            "Retail Brain OS"
        )

        self.root.geometry(
            "1200x750"
        )

        self.root.minsize(
            1000,
            650,
        )

        self.root.configure(
            bg="#eef1f4"
        )

        # -------------------------------------------------
        # Runtime
        # -------------------------------------------------

        self.runtime: RetailVisionRuntime | None = None

        self.runtime_starting = False
        self.runtime_stopping = False

        self.camera_photo = None

        # -------------------------------------------------
        # Surveillance Recording
        # -------------------------------------------------

        self.recording_writer = None
        self.recording_path: Path | None = None
        self.recording_active = False

        self.recordings_dir = (
            Path(__file__).resolve().parents[2]
            / "recordings"
        )

        self.face_captures_dir = (
            Path(__file__).resolve().parents[2]
            / "face_captures"
        )

        self.data_exports_dir = (
            Path(__file__).resolve().parents[2]
            / "data_exports"
        )

        self.person_data_dir = (
            Path(__file__).resolve().parents[2]
            / "person_data"
        )

        self.session_people: dict[int, dict[str, object]] = {}

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.close_application,
        )

        self.build_ui()

    # =====================================================
    # UI
    # =====================================================

    def build_ui(self) -> None:

        # -------------------------------------------------
        # Root geometry
        # -------------------------------------------------

        self.root.grid_rowconfigure(
            0,
            weight=0,
        )

        self.root.grid_rowconfigure(
            1,
            weight=1,
        )

        self.root.grid_rowconfigure(
            2,
            weight=0,
        )

        self.root.grid_rowconfigure(
            3,
            weight=0,
        )

        self.root.grid_columnconfigure(
            0,
            weight=1,
        )

        # =================================================
        # HEADER
        # =================================================

        header = tk.Frame(
            self.root,
            bg="#18202a",
            height=80,
        )

        header.grid(
            row=0,
            column=0,
            sticky="ew",
        )

        header.grid_propagate(False)

        tk.Label(
            header,
            text="RETAIL BRAIN OS",
            font=(
                "Segoe UI",
                22,
                "bold",
            ),
            fg="white",
            bg="#18202a",
        ).pack(
            anchor="w",
            padx=30,
            pady=(14, 0),
        )

        tk.Label(
            header,
            text=(
                "Retail Intelligence & "
                "Surveillance System"
            ),
            font=(
                "Segoe UI",
                10,
            ),
            fg="#b8c2cc",
            bg="#18202a",
        ).pack(
            anchor="w",
            padx=32,
            pady=(0, 8),
        )

        # =================================================
        # MAIN BODY
        # =================================================

        body = tk.Frame(
            self.root,
            bg="#eef1f4",
        )

        body.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=16,
            pady=12,
        )

        body.grid_rowconfigure(
            0,
            weight=1,
        )

        # Left zone management panel
        body.grid_columnconfigure(
            0,
            weight=0,
            minsize=270,
        )

        # Main live camera
        body.grid_columnconfigure(
            1,
            weight=1,
        )

        # Right live status
        body.grid_columnconfigure(
            2,
            weight=0,
            minsize=300,
        )

        # =================================================
        # LEFT ZONE MANAGEMENT PANEL
        # =================================================

        zone_panel = tk.Frame(
            body,
            width=270,
            bg="#ffffff",
            bd=1,
            relief="solid",
        )

        zone_panel.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 10),
        )

        zone_panel.grid_propagate(False)

        self.zone_management = ZoneManagementPanel(
            zone_panel,
            on_zones_changed=self.zone_configuration_changed,
            can_edit=self.zone_edit_allowed,
        )

        # =================================================
        # CAMERA PANEL
        # =================================================

        camera_panel = tk.Frame(
            body,
            bg="#111111",
            bd=1,
            relief="solid",
        )

        camera_panel.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(0, 10),
        )

        camera_panel.grid_rowconfigure(
            1,
            weight=1,
        )

        # Compact camera information strip below the live frame.
        # This mirrors the product reference: resolution and
        # current camera time are shown immediately below the
        # video area and above the control bar.
        camera_panel.grid_rowconfigure(
            2,
            weight=0,
        )

        camera_panel.grid_columnconfigure(
            0,
            weight=1,
        )

        tk.Label(
            camera_panel,
            text="LIVE CAMERA",
            font=(
                "Segoe UI",
                11,
                "bold",
            ),
            fg="#00d9c6",
            bg="#111111",
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=12,
            pady=(8, 4),
        )

        self.camera_label = tk.Label(
            camera_panel,
            text="Camera stopped",
            font=(
                "Segoe UI",
                14,
            ),
            fg="#aaaaaa",
            bg="#000000",
        )

        self.camera_label.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=8,
            pady=(0, 4),
        )

        # -------------------------------------------------
        # Camera Information Strip
        #
        # Compact readings shown directly below the camera,
        # matching the product reference:
        #
        # Resolution: 640x480  |  Time: 11 Aug 2026 16:15:42
        #
        # The values are updated from the live runtime frame.
        # -------------------------------------------------

        self.camera_info_bar = tk.Frame(
            camera_panel,
            bg="#03070d",
            height=28,
        )

        self.camera_info_bar.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=8,
            pady=(0, 8),
        )

        self.camera_info_bar.grid_propagate(False)

        self.camera_resolution_label = tk.Label(
            self.camera_info_bar,
            text="Resolution: --",
            font=("Segoe UI", 8),
            bg="#03070d",
            fg="#aeb9c8",
            anchor="w",
        )

        self.camera_resolution_label.pack(
            side="left",
            padx=(8, 0),
        )

        self.camera_info_separator = tk.Label(
            self.camera_info_bar,
            text="|",
            font=("Segoe UI", 8),
            bg="#03070d",
            fg="#526176",
        )

        self.camera_info_separator.pack(
            side="left",
            padx=10,
        )

        self.camera_time_label = tk.Label(
            self.camera_info_bar,
            text="Time: --",
            font=("Segoe UI", 8),
            bg="#03070d",
            fg="#aeb9c8",
            anchor="w",
        )

        self.camera_time_label.pack(
            side="left",
        )

        # =================================================
        # RIGHT DASHBOARD PANEL
        # =================================================

        status_panel = tk.Frame(
            body,
            width=300,
            bg="#ffffff",
            bd=1,
            relief="solid",
        )

        status_panel.grid(
            row=0,
            column=2,
            sticky="nsew",
        )

        status_panel.grid_propagate(False)

        status_panel.grid_columnconfigure(
            0,
            weight=1,
        )

        status_panel.grid_rowconfigure(
            1,
            weight=1,
        )

        # -------------------------------------------------
        # Dashboard title
        # -------------------------------------------------

        tk.Label(
            status_panel,
            text="LIVE STATUS",
            font=(
                "Segoe UI",
                12,
                "bold",
            ),
            fg="#00bfae",
            bg="#ffffff",
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=12,
            pady=(8, 4),
        )

        # =================================================
        # SCROLLABLE DASHBOARD CONTENT
        # =================================================

        status_canvas = tk.Canvas(
            status_panel,
            bg="#ffffff",
            highlightthickness=0,
            bd=0,
        )

        status_scrollbar = tk.Scrollbar(
            status_panel,
            orient="vertical",
            command=status_canvas.yview,
        )

        status_content = tk.Frame(
            status_canvas,
            bg="#ffffff",
        )

        status_content.bind(
            "<Configure>",
            lambda event: status_canvas.configure(
                scrollregion=status_canvas.bbox("all")
            ),
        )

        status_window = status_canvas.create_window(
            (0, 0),
            window=status_content,
            anchor="nw",
        )

        def resize_status_content(
            event,
        ) -> None:

            status_canvas.itemconfigure(
                status_window,
                width=event.width,
            )

        status_canvas.bind(
            "<Configure>",
            resize_status_content,
        )

        status_canvas.configure(
            yscrollcommand=status_scrollbar.set,
        )

        status_canvas.grid(
            row=1,
            column=0,
            sticky="nsew",
        )

        status_scrollbar.grid(
            row=1,
            column=1,
            sticky="ns",
        )

        # =================================================
        # TECHNICAL STATUS
        # =================================================

        tk.Label(
            status_content,
            text="TECHNICAL STATUS",
            font=(
                "Segoe UI",
                9,
                "bold",
            ),
            fg="#00bfae",
            bg="#ffffff",
        ).pack(
            anchor="w",
            padx=8,
            pady=(4, 4),
        )

        technical_frame = tk.Frame(
            status_content,
            bg="#ffffff",
        )

        technical_frame.pack(
            fill="x",
            padx=5,
        )

        technical_frame.grid_columnconfigure(
            0,
            weight=1,
        )

        technical_frame.grid_columnconfigure(
            1,
            weight=1,
        )

        self.runtime_status_label = (
            self.create_compact_status_card(
                technical_frame,
                "STATUS",
                "STOPPED",
                0,
                0,
            )
        )

        self.fps_label = (
            self.create_compact_status_card(
                technical_frame,
                "FPS",
                "0.0",
                0,
                1,
            )
        )

        self.processing_label = (
            self.create_compact_status_card(
                technical_frame,
                "PROCESSING",
                "0.0 ms",
                1,
                0,
            )
        )

        self.frame_label = (
            self.create_compact_status_card(
                technical_frame,
                "FRAME",
                "0",
                1,
                1,
            )
        )

        self.zone_label = (
            self.create_compact_status_card(
                technical_frame,
                "ZONES",
                "0",
                2,
                0,
            )
        )

        self.error_label = (
            self.create_compact_status_card(
                technical_frame,
                "ERROR",
                "None",
                2,
                1,
            )
        )

        # =================================================
        # LIVE INTELLIGENCE DASHBOARD
        # =================================================

        self.live_dashboard = LiveDashboard(
            status_content
        )

        # =================================================
        # CONTROL BAR
        # =================================================

        controls = tk.Frame(
            self.root,
            bg="#18202a",
            height=78,
        )

        controls.grid(
            row=2,
            column=0,
            sticky="ew",
        )

        controls.grid_propagate(False)

        # Responsive control layout:
        # - At the normal/minimized window size, buttons
        #   remain compact.
        # - When the window is maximized, the buttons
        #   expand horizontally and use the available bar.
        # - The whole control row stays visually balanced
        #   instead of leaving a large empty area on the right.

        for column in range(8):
            controls.grid_columnconfigure(
                column,
                weight=1,
                uniform="control",
            )

        controls.grid_columnconfigure(
            8,
            weight=1,
            uniform="control",
        )

        # -------------------------------------------------
        # Setup Zones
        # -------------------------------------------------

        self.setup_button = tk.Button(
            controls,
            text="SETUP ZONES",
            command=self.open_zone_setup,
            font=(
                "Segoe UI",
                9,
                "bold",
            ),
            height=2,
            relief="flat",
        )

        self.setup_button.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(16, 4),
            pady=12,
        )

        # -------------------------------------------------
        # Start Retail OS
        # -------------------------------------------------

        self.start_button = tk.Button(
            controls,
            text="START RETAIL OS",
            command=self.start_retail_os,
            font=(
                "Segoe UI",
                9,
                "bold",
            ),
            height=2,
            relief="flat",
        )

        self.start_button.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=4,
            pady=12,
        )

        # -------------------------------------------------
        # Stop Retail OS
        # -------------------------------------------------

        self.stop_button = tk.Button(
            controls,
            text="STOP RETAIL OS",
            command=self.stop_retail_os,
            font=(
                "Segoe UI",
                9,
                "bold",
            ),
            height=2,
            relief="flat",
            state="disabled",
        )

        self.stop_button.grid(
            row=0,
            column=2,
            sticky="ew",
            padx=4,
            pady=12,
        )

        # -------------------------------------------------
        # Record Surveillance
        # -------------------------------------------------

        self.record_button = tk.Button(
            controls,
            text="RECORD SURVEILLANCE",
            command=self.start_recording,
            font=(
                "Segoe UI",
                8,
                "bold",
            ),
            height=2,
            relief="flat",
            state="disabled",
        )

        self.record_button.grid(
            row=0,
            column=3,
            sticky="ew",
            padx=4,
            pady=12,
        )

        # -------------------------------------------------
        # Stop Recording
        # -------------------------------------------------

        self.stop_record_button = tk.Button(
            controls,
            text="STOP RECORDING",
            command=self.stop_recording,
            font=(
                "Segoe UI",
                8,
                "bold",
            ),
            height=2,
            relief="flat",
            state="disabled",
        )

        self.stop_record_button.grid(
            row=0,
            column=4,
            sticky="ew",
            padx=4,
            pady=12,
        )

        # -------------------------------------------------
        # Capture Face
        # -------------------------------------------------

        self.capture_face_button = tk.Button(
            controls,
            text="CAPTURE FACE",
            command=self.capture_selected_face,
            font=(
                "Segoe UI",
                8,
                "bold",
            ),
            height=2,
            relief="flat",
            state="disabled",
        )

        self.capture_face_button.grid(
            row=0,
            column=5,
            sticky="ew",
            padx=4,
            pady=12,
        )

        # -------------------------------------------------
        # Save Data
        # -------------------------------------------------

        self.save_data_button = tk.Button(
            controls,
            text="SAVE DATA",
            command=self.save_session_data,
            font=(
                "Segoe UI",
                8,
                "bold",
            ),
            height=2,
            relief="flat",
            state="disabled",
        )

        self.save_data_button.grid(
            row=0,
            column=6,
            sticky="ew",
            padx=4,
            pady=12,
        )

        # -------------------------------------------------
        # Open Saved Files
        # -------------------------------------------------

        self.open_recordings_button = tk.Button(
            controls,
            text="OPEN SAVED FILES",
            command=self.open_recordings,
            font=(
                "Segoe UI",
                8,
                "bold",
            ),
            height=2,
            relief="flat",
        )

        self.open_recordings_button.grid(
            row=0,
            column=7,
            sticky="ew",
            padx=4,
            pady=12,
        )

        # -------------------------------------------------
        # Close
        # -------------------------------------------------

        self.close_button = tk.Button(
            controls,
            text="CLOSE",
            command=self.close_application,
            font=(
                "Segoe UI",
                9,
                "bold",
            ),
            height=2,
            relief="flat",
        )

        self.close_button.grid(
            row=0,
            column=8,
            sticky="ew",
            padx=(4, 16),
            pady=12,
        )

        # =================================================
        # PRODUCT STATUS FOOTER
        # =================================================
        #
        # This mirrors the compact status strip from the
        # product reference:
        #
        # System Status | Camera | Tracker | Zones | Version
        #
        # The existing status_label is retained as the
        # center status message used by the runtime.
        # =================================================

        footer = tk.Frame(
            self.root,
            bg="#111c2c",
            height=34,
        )

        footer.grid(
            row=3,
            column=0,
            sticky="ew",
        )

        footer.grid_propagate(False)

        footer.grid_columnconfigure(
            0,
            weight=1,
        )

        footer.grid_columnconfigure(
            1,
            weight=1,
        )

        footer.grid_columnconfigure(
            2,
            weight=1,
        )

        footer.grid_columnconfigure(
            3,
            weight=1,
        )

        footer.grid_columnconfigure(
            4,
            weight=1,
        )

        # -------------------------------------------------
        # System Status
        # -------------------------------------------------

        self.footer_system_status = tk.Label(
            footer,
            text="●  System Status: Ready",
            font=("Segoe UI", 8),
            bg="#111c2c",
            fg="#91a0b5",
            anchor="w",
        )

        self.footer_system_status.grid(
            row=0,
            column=0,
            sticky="w",
            padx=(14, 4),
        )

        # -------------------------------------------------
        # Camera
        # -------------------------------------------------

        self.footer_camera_status = tk.Label(
            footer,
            text="Camera: Disconnected",
            font=("Segoe UI", 8),
            bg="#111c2c",
            fg="#91a0b5",
            anchor="center",
        )

        self.footer_camera_status.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=4,
        )

        # -------------------------------------------------
        # Tracker
        # -------------------------------------------------

        self.footer_tracker_status = tk.Label(
            footer,
            text="Tracker: Inactive",
            font=("Segoe UI", 8),
            bg="#111c2c",
            fg="#91a0b5",
            anchor="center",
        )

        self.footer_tracker_status.grid(
            row=0,
            column=2,
            sticky="ew",
            padx=4,
        )

        # -------------------------------------------------
        # Zones
        # -------------------------------------------------

        self.footer_zones_status = tk.Label(
            footer,
            text="Zones: Loaded (0)",
            font=("Segoe UI", 8),
            bg="#111c2c",
            fg="#91a0b5",
            anchor="center",
        )

        self.footer_zones_status.grid(
            row=0,
            column=3,
            sticky="ew",
            padx=4,
        )

        # -------------------------------------------------
        # Version
        # -------------------------------------------------

        self.footer_version = tk.Label(
            footer,
            text="Retail Brain OS v1.0.0",
            font=("Segoe UI", 8),
            bg="#111c2c",
            fg="#64748b",
            anchor="e",
        )

        self.footer_version.grid(
            row=0,
            column=4,
            sticky="e",
            padx=(4, 14),
        )

        # Existing runtime message label. Keep this object
        # because the rest of the GUI updates it directly.
        self.status_label = tk.Label(
            self.root,
            text="System ready",
            font=(
                "Segoe UI",
                1,
            ),
            bg="#111c2c",
            fg="#111c2c",
            height=1,
        )

        self.status_label.grid(
            row=4,
            column=0,
            sticky="ew",
        )

        # Apply the visual theme only after every widget has
        # been constructed. This keeps the existing runtime,
        # dashboard, recording, face capture, and save-data
        # behavior untouched.
        self._apply_visual_theme()

    # =====================================================
    # Visual Theme
    # =====================================================

    def _apply_visual_theme(self) -> None:
        """Apply the Retail Brain OS product visual theme."""

        self.COLORS = {
            "bg": "#070d17",
            "surface": "#0d1624",
            "surface_2": "#111c2c",
            "card": "#142033",
            "card_2": "#18263a",
            "border": "#263449",
            "text": "#e8eef7",
            "muted": "#91a0b5",
            "cyan": "#00d9c6",
            "teal": "#14b8a6",
            "green": "#22c55e",
            "red": "#ef4444",
            "blue": "#3b82f6",
            "purple": "#a855f7",
            "orange": "#f59e0b",
            "yellow": "#facc15",
        }

        colors = self.COLORS

        self.root.configure(
            bg=colors["bg"]
        )

        # Keep the main structural surfaces dark.
        for widget in (
            self.root,
        ):
            widget.configure(
                bg=colors["bg"]
            )

        # -------------------------------------------------
        # Recursive neutral-surface conversion
        #
        # Only known neutral backgrounds are converted.
        # Existing zone colors, camera black, and colored
        # status accents are left untouched.
        # -------------------------------------------------

        neutral_backgrounds = {
            "#ffffff": colors["surface"],
            "#eef1f4": colors["bg"],
            "#f4f6f8": colors["card"],
        }

        neutral_foregrounds = {
            "#18202a": colors["text"],
            "#555555": colors["muted"],
            "#666666": colors["muted"],
            "#777777": colors["muted"],
            "#888888": colors["muted"],
        }

        def style_tree(widget: tk.Widget) -> None:

            try:
                current_bg = str(
                    widget.cget("bg")
                )

                if current_bg in neutral_backgrounds:
                    widget.configure(
                        bg=neutral_backgrounds[current_bg]
                    )

                current_fg = str(
                    widget.cget("fg")
                )

                if current_fg in neutral_foregrounds:
                    widget.configure(
                        fg=neutral_foregrounds[current_fg]
                    )

            except (
                tk.TclError,
                TypeError,
            ):
                pass

            for child in widget.winfo_children():
                style_tree(child)

        style_tree(self.root)

        # -------------------------------------------------
        # Header
        # -------------------------------------------------

        for widget in (
            self.root.winfo_children()
        ):

            # Header is row 0.
            try:
                if widget.grid_info().get("row") == "0":
                    widget.configure(
                        bg=colors["surface_2"]
                    )
            except (
                tk.TclError,
                KeyError,
            ):
                pass

        # Explicitly keep camera area visually separate.
        self.camera_label.configure(
            bg="#03070d",
            fg="#9aa7b8",
        )

        # -------------------------------------------------
        # Colored product buttons
        # -------------------------------------------------

        button_styles = {
            self.setup_button: (
                colors["teal"],
                "#0f766e",
                "#ffffff",
            ),
            self.start_button: (
                colors["green"],
                "#15803d",
                "#ffffff",
            ),
            self.stop_button: (
                colors["red"],
                "#b91c1c",
                "#ffffff",
            ),
            self.record_button: (
                colors["blue"],
                "#1d4ed8",
                "#ffffff",
            ),
            self.stop_record_button: (
                "#475569",
                "#334155",
                "#ffffff",
            ),
            self.capture_face_button: (
                colors["purple"],
                "#7e22ce",
                "#ffffff",
            ),
            self.save_data_button: (
                colors["orange"],
                "#c2410c",
                "#ffffff",
            ),
            self.open_recordings_button: (
                colors["cyan"],
                "#0f766e",
                "#061018",
            ),
            self.close_button: (
                "#7f1d1d",
                "#991b1b",
                "#ffffff",
            ),
        }

        for button, (
            bg,
            active_bg,
            fg,
        ) in button_styles.items():

            button.configure(
                bg=bg,
                fg=fg,
                activebackground=active_bg,
                activeforeground="#ffffff",
                relief="flat",
                bd=0,
                highlightthickness=0,
                cursor="hand2",
            )

        # -------------------------------------------------
        # Add lightweight visual symbols to the controls.
        # -------------------------------------------------

        self.setup_button.configure(
            text="⚙  SETUP ZONES"
        )

        self.start_button.configure(
            text="▶  START RETAIL OS"
        )

        self.stop_button.configure(
            text="■  STOP RETAIL OS"
        )

        self.record_button.configure(
            text="●  RECORD SURVEILLANCE"
        )

        self.stop_record_button.configure(
            text="■  STOP RECORDING"
        )

        self.capture_face_button.configure(
            text="◉  CAPTURE FACE"
        )

        self.save_data_button.configure(
            text="▣  SAVE DATA"
        )

        self.open_recordings_button.configure(
            text="▤  OPEN SAVED FILES"
        )

        self.close_button.configure(
            text="↩  CLOSE"
        )

        # -------------------------------------------------
        # Footer
        # -------------------------------------------------

        self.status_label.configure(
            bg=colors["surface_2"],
            fg=colors["surface_2"],
        )

        self.footer_system_status.configure(
            bg=colors["surface_2"],
        )

        self.footer_camera_status.configure(
            bg=colors["surface_2"],
        )

        self.footer_tracker_status.configure(
            bg=colors["surface_2"],
        )

        self.footer_zones_status.configure(
            bg=colors["surface_2"],
        )

        self.footer_version.configure(
            bg=colors["surface_2"],
        )

    # =====================================================
    # Compact Technical Status Card
    # =====================================================

    def create_compact_status_card(
        self,
        parent: tk.Widget,
        title: str,
        value: str,
        row: int,
        column: int,
    ) -> tk.Label:

        frame = tk.Frame(
            parent,
            bg="#142033",
            bd=1,
            relief="solid",
        )

        frame.grid(
            row=row,
            column=column,
            sticky="nsew",
            padx=3,
            pady=3,
        )

        tk.Label(
            frame,
            text=title,
            font=(
                "Segoe UI",
                7,
                "bold",
            ),
            fg="#91a0b5",
            bg="#142033",
        ).pack(
            anchor="w",
            padx=6,
            pady=(4, 0),
        )

        label = tk.Label(
            frame,
            text=value,
            font=(
                "Segoe UI",
                10,
                "bold",
            ),
            fg="#e8eef7",
            bg="#142033",
        )

        label.pack(
            anchor="w",
            padx=6,
            pady=(0, 4),
        )

        return label

    # =====================================================
    # Legacy Status Card
    # =====================================================

    def create_status_card(
        self,
        parent: tk.Widget,
        title: str,
        value: str,
    ) -> tk.Label:

        frame = tk.Frame(
            parent,
            bg="#142033",
            bd=1,
            relief="solid",
        )

        frame.pack(
            fill="x",
            padx=15,
            pady=6,
        )

        tk.Label(
            frame,
            text=title,
            font=(
                "Segoe UI",
                8,
                "bold",
            ),
            fg="#91a0b5",
            bg="#142033",
        ).pack(
            anchor="w",
            padx=10,
            pady=(7, 0),
        )

        label = tk.Label(
            frame,
            text=value,
            font=(
                "Segoe UI",
                13,
                "bold",
            ),
            fg="#e8eef7",
            bg="#142033",
        )

        label.pack(
            anchor="w",
            padx=10,
            pady=(0, 7),
        )

        return label

    # =====================================================
    # Zone Setup
    # =====================================================

    def open_zone_setup(self) -> None:

        if self.runtime is not None:

            if self.runtime.is_running():

                self.status_label.config(
                    text=(
                        "Stop Retail OS before "
                        "opening Zone Setup."
                    )
                )

                return

        self.status_label.config(
            text="Opening zone setup..."
        )

        ZoneSetupWindow(
            self.root,
            on_close=self.zone_setup_closed,
        )

    def zone_setup_closed(self) -> None:

        if hasattr(
            self,
            "zone_management",
        ):

            self.zone_management.refresh()

        self.status_label.config(
            text=(
                "Zone setup closed. "
                "Configuration saved."
            )
        )

    # =====================================================
    # Zone Management
    # =====================================================

    def zone_edit_allowed(self) -> bool:

        if self.runtime is None:

            return True

        return not self.runtime.is_running()

    def zone_configuration_changed(self) -> None:

        # Zone changes are saved to zones.json while the
        # runtime is stopped. The next runtime start loads
        # the updated configuration.
        self.status_label.config(
            text=(
                "Zone configuration updated. "
                "Start Retail OS to load the changes."
            )
        )

    # =====================================================
    # Runtime Start
    # =====================================================

    def start_retail_os(self) -> None:

        if self.runtime is not None:

            if self.runtime.is_running():

                return

        if self.runtime_starting:

            return

        self.runtime_starting = True

        self.start_button.config(
            state="disabled"
        )

        self.setup_button.config(
            state="disabled"
        )

        self.status_label.config(
            text=(
                "Starting Retail Vision Runtime..."
            )
        )

        self.runtime_status_label.config(
            text="STARTING"
        )

        worker = threading.Thread(
            target=self._start_runtime_worker,
            daemon=True,
        )

        worker.start()

        self.root.after(
            100,
            self.poll_runtime,
        )

    def _start_runtime_worker(self) -> None:

        try:

            runtime = RetailVisionRuntime()

            runtime.start()

            self.session_people.clear()

            self.runtime = runtime

        except Exception as exc:

            self.root.after(
                0,
                lambda error=str(exc): (
                    self.runtime_start_failed(
                        error
                    )
                ),
            )

        finally:

            self.runtime_starting = False

    def runtime_start_failed(
        self,
        error: str,
    ) -> None:

        self.runtime_status_label.config(
            text="ERROR"
        )

        self.error_label.config(
            text=error
        )

        self.status_label.config(
            text="Runtime failed to start."
        )

        self.start_button.config(
            state="normal"
        )

        self.setup_button.config(
            state="normal"
        )

        self.record_button.config(
            state="disabled"
        )

        self.stop_record_button.config(
            state="disabled"
        )

    # =====================================================
    # Runtime Polling
    # =====================================================

    def poll_runtime(self) -> None:

        runtime = self.runtime

        if runtime is None:

            if self.runtime_starting:

                self.root.after(
                    100,
                    self.poll_runtime,
                )

            return

        state = runtime.get_state()

        # -------------------------------------------------
        # Product status footer
        # -------------------------------------------------

        is_running = bool(
            getattr(state, "running", False)
        )

        has_camera_frame = (
            getattr(state, "frame", None) is not None
        )

        tracker_active = (
            getattr(state, "frame_result", None) is not None
            or getattr(
                state,
                "intelligence_result",
                None,
            ) is not None
        )

        zone_count = len(
            getattr(state, "zones", ()) or ()
        )

        if is_running:
            self.footer_system_status.config(
                text="●  System Status: All Systems Operational",
                fg="#22c55e",
            )
        else:
            self.footer_system_status.config(
                text="●  System Status: Stopped",
                fg="#f59e0b",
            )

        if has_camera_frame:
            self.footer_camera_status.config(
                text="Camera: Connected",
                fg="#22c55e",
            )
        else:
            self.footer_camera_status.config(
                text="Camera: Disconnected",
                fg="#ef4444",
            )

        if tracker_active:
            self.footer_tracker_status.config(
                text="Tracker: Active",
                fg="#22c55e",
            )
        else:
            self.footer_tracker_status.config(
                text="Tracker: Inactive",
                fg="#91a0b5",
            )

        self.footer_zones_status.config(
            text=f"Zones: Loaded ({zone_count})",
            fg=(
                "#22c55e"
                if zone_count > 0
                else "#91a0b5"
            ),
        )

        self.runtime_status_label.config(
            text=(
                "RUNNING"
                if state.running
                else "STOPPED"
            )
        )

        self.fps_label.config(
            text=f"{state.fps:.1f}"
        )

        self.processing_label.config(
            text=(
                f"{state.processing_ms:.1f} ms"
            )
        )

        self.frame_label.config(
            text=str(
                state.frame_number
            )
        )

        self.zone_label.config(
            text=str(
                len(state.zones)
            )
        )

        self.error_label.config(
            text=(
                state.error
                if state.error
                else "None"
            )
        )

        # -------------------------------------------------
        # Camera + Intelligence Overlay
        # -------------------------------------------------

        if state.frame is not None:

            frame_height, frame_width = state.frame.shape[:2]

            self.camera_resolution_label.config(
                text=f"Resolution: {frame_width}x{frame_height}"
            )

            self.camera_time_label.config(
                text=(
                    "Time: "
                    + datetime.now().strftime(
                        "%d %b %Y %H:%M:%S"
                    )
                )
            )

            rendered_frame = state.frame

            if (
                state.frame_result is not None
                and state.intelligence_result is not None
            ):

                rendered_frame = render_live_frame(
                    frame=state.frame,
                    frame_result=state.frame_result,
                    intelligence_result=(
                        state.intelligence_result
                    ),
                    zones=state.zones,
                )

            self.display_camera_frame(
                rendered_frame
            )

            # Record the exact processed frame shown in
            # the camera window. This avoids opening a
            # second camera connection.
            if self.recording_active:
                self._write_recording_frame(
                    rendered_frame
                )

        # -------------------------------------------------
        # Dashboard
        # -------------------------------------------------

        if state.intelligence_result is not None:

            self.live_dashboard.update(
                intelligence_result=(
                    state.intelligence_result
                ),
                zones=state.zones,
            )

            self._update_session_people(
                state.intelligence_result
            )

            self.capture_face_button.config(
                state=(
                    "normal"
                    if (
                        state.running
                        and self._selected_track_id() is not None
                    )
                    else "disabled"
                )
            )

            self.save_data_button.config(
                state=(
                    "normal"
                    if self.session_people
                    else "disabled"
                )
            )

        # -------------------------------------------------
        # Runtime state
        # -------------------------------------------------

        if state.running:

            self.stop_button.config(
                state="normal"
            )

            if not self.recording_active:
                self.record_button.config(
                    state="normal"
                )

            self.status_label.config(
                text=(
                    "Recording surveillance."
                    if self.recording_active
                    else "Retail OS is running."
                )
            )

            self.root.after(
                30,
                self.poll_runtime,
            )

        else:

            if self.recording_active:
                self.stop_recording()

            self.stop_button.config(
                state="disabled"
            )

            self.start_button.config(
                state="normal"
            )

            self.setup_button.config(
                state="normal"
            )

            self.record_button.config(
                state="disabled"
            )

            if state.error:

                self.status_label.config(
                    text=(
                        "Retail OS stopped "
                        "because of an error."
                    )
                )

            else:

                self.status_label.config(
                    text="Retail OS stopped."
                )

    # =====================================================
    # Camera Display
    # =====================================================

    def display_camera_frame(
        self,
        frame,
    ) -> None:

        widget_width = max(
            self.camera_label.winfo_width(),
            640,
        )

        widget_height = max(
            self.camera_label.winfo_height(),
            480,
        )

        frame_height, frame_width = (
            frame.shape[:2]
        )

        scale = min(
            widget_width / frame_width,
            widget_height / frame_height,
        )

        display_width = max(
            1,
            int(
                frame_width * scale
            ),
        )

        display_height = max(
            1,
            int(
                frame_height * scale
            ),
        )

        resized = cv2.resize(
            frame,
            (
                display_width,
                display_height,
            ),
            interpolation=cv2.INTER_AREA,
        )

        rgb = cv2.cvtColor(
            resized,
            cv2.COLOR_BGR2RGB,
        )

        image = Image.fromarray(
            rgb
        )

        self.camera_photo = ImageTk.PhotoImage(
            image
        )

        self.camera_label.config(
            image=self.camera_photo,
            text="",
        )

    # =====================================================
    # Session Data
    # =====================================================

    def _selected_track_id(self) -> int | None:

        key = getattr(
            self.live_dashboard,
            "selected_person_key",
            None,
        )

        if key is None:
            return None

        try:
            return int(key[1])
        except (TypeError, ValueError):
            return None

    def _update_session_people(
        self,
        intelligence_result,
    ) -> None:

        for person in intelligence_result.persons:

            track_id = getattr(
                person,
                "track_id",
                None,
            )

            if track_id is None:
                continue

            first_seen = getattr(
                person,
                "first_seen_at",
                None,
            )

            total_dwell = getattr(
                person,
                "total_dwell",
                None,
            )

            current_dwell = getattr(
                person,
                "dwell_time",
                None,
            )

            zone_id = getattr(
                person,
                "zone_id",
                None,
            )

            self.session_people[int(track_id)] = {
                "track_id": int(track_id),
                "first_seen": first_seen,
                "last_seen": intelligence_result.timestamp,
                "zone_id": str(zone_id) if zone_id else "",
                "current_dwell_seconds": (
                    current_dwell.total_seconds()
                    if current_dwell is not None
                    else 0.0
                ),
                "total_dwell_seconds": (
                    total_dwell.total_seconds()
                    if total_dwell is not None
                    else 0.0
                ),
            }

    # =====================================================
    # Face Capture
    # =====================================================

    def capture_selected_face(self) -> None:

        runtime = self.runtime

        if runtime is None or not runtime.is_running():
            self.status_label.config(
                text="Start Retail OS before capturing a face."
            )
            return

        track_id = self._selected_track_id()

        if track_id is None:
            self.status_label.config(
                text="Select an active person first."
            )
            return

        state = runtime.get_state()

        if state.frame is None or state.frame_result is None:
            self.status_label.config(
                text="Waiting for a camera frame."
            )
            return

        tracked_person = next(
            (
                person
                for person in state.frame_result.persons
                if person.track_id == track_id
            ),
            None,
        )

        if tracked_person is None:
            self.status_label.config(
                text=f"ID {track_id} is no longer visible."
            )
            return

        bbox = tracked_person.bounding_box

        x1 = max(0, int(bbox.x_min))
        y1 = max(0, int(bbox.y_min))
        x2 = min(state.frame.shape[1], int(bbox.x_max))
        y2 = min(state.frame.shape[0], int(bbox.y_max))

        if x2 <= x1 or y2 <= y1:
            self.status_label.config(
                text=f"Invalid image region for ID {track_id}."
            )
            return

        person_crop = state.frame[y1:y2, x1:x2]

        if person_crop.size == 0:
            self.status_label.config(
                text=f"Unable to crop ID {track_id}."
            )
            return

        gray = cv2.cvtColor(
            person_crop,
            cv2.COLOR_BGR2GRAY,
        )

        cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades
            + "haarcascade_frontalface_default.xml"
        )

        if cascade.empty():
            self.status_label.config(
                text="Face detector could not be loaded."
            )
            return

        faces = cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
        )

        if len(faces) == 0:
            self.status_label.config(
                text=(
                    f"No face detected for ID {track_id}. "
                    "Move closer or face the camera."
                )
            )
            return

        fx, fy, fw, fh = max(
            faces,
            key=lambda rect: rect[2] * rect[3],
        )

        face = person_crop[
            fy:fy + fh,
            fx:fx + fw,
        ]

        if face.size == 0:
            self.status_label.config(
                text=f"Unable to crop the detected face for ID {track_id}."
            )
            return

        self.face_captures_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        output_path = (
            self.face_captures_dir
            / f"person_{track_id}_{timestamp}.jpg"
        )

        if not cv2.imwrite(
            str(output_path),
            face,
        ):
            self.status_label.config(
                text="Unable to save captured face."
            )
            return

        self.status_label.config(
            text=(
                f"Face captured for ID {track_id}: "
                f"{output_path.name}"
            )
        )

    # =====================================================
    # Save Data
    # =====================================================

    def save_session_data(self) -> None:

        if not self.session_people:
            self.status_label.config(
                text="No person data available to export."
            )
            return

        self.data_exports_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        # -------------------------------------------------
        # 1. Save the complete session data.
        # -------------------------------------------------

        output_path = (
            self.data_exports_dir
            / f"retail_session_{timestamp}.csv"
        )

        selected_track_id = (
            self._selected_track_id()
        )

        fieldnames = [
            "track_id",
            "first_seen",
            "last_seen",
            "zone_id",
            "current_dwell_seconds",
            "total_dwell_seconds",
        ]

        with output_path.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as csv_file:

            writer = csv.DictWriter(
                csv_file,
                fieldnames=fieldnames,
            )

            writer.writeheader()

            for track_id in sorted(
                self.session_people
            ):

                record = self.session_people[
                    track_id
                ]

                writer.writerow(
                    {
                        key: record.get(key, "")
                        for key in fieldnames
                    }
                )

        # -------------------------------------------------
        # 2. If an Active Person is selected, also save
        #    that person's complete dashboard details as a
        #    separate JSON snapshot.
        #
        #    No new button is introduced. SAVE DATA performs
        #    both operations.
        # -------------------------------------------------

        selected_record = None

        if selected_track_id is not None:

            selected_record = self.session_people.get(
                selected_track_id
            )

        if selected_record is not None:

            self.person_data_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            person_data = dict(
                selected_record
            )

            person_data["selected"] = True

            # Convert datetime/timedelta-like values to
            # JSON-safe strings/numbers.
            first_seen = person_data.get(
                "first_seen"
            )

            last_seen = person_data.get(
                "last_seen"
            )

            if isinstance(
                first_seen,
                datetime,
            ):
                person_data["first_seen"] = (
                    first_seen.isoformat()
                )

            if isinstance(
                last_seen,
                datetime,
            ):
                person_data["last_seen"] = (
                    last_seen.isoformat()
                )

            # Add the human-readable zone name when the
            # current dashboard has zone information.
            zone_name = ""

            try:

                current_people = getattr(
                    self.live_dashboard,
                    "current_people",
                    {},
                )

                selected_person = None

                for key, person in (
                    current_people.items()
                ):

                    if int(key[1]) == selected_track_id:
                        selected_person = person
                        break

                if selected_person is not None:

                    zone_id = getattr(
                        selected_person,
                        "zone_id",
                        None,
                    )

                    zones = getattr(
                        self.live_dashboard,
                        "_last_zones",
                        (),
                    )

                    zone_name = (
                        self.live_dashboard._get_zone_name(
                            zone_id,
                            zones,
                        )
                        if zone_id is not None
                        else ""
                    )

            except (
                AttributeError,
                TypeError,
                ValueError,
            ):
                zone_name = ""

            person_data["zone_name"] = zone_name

            person_output_path = (
                self.person_data_dir
                / (
                    f"person_{selected_track_id}_"
                    f"{timestamp}.json"
                )
            )

            with person_output_path.open(
                "w",
                encoding="utf-8",
            ) as json_file:

                json.dump(
                    person_data,
                    json_file,
                    indent=4,
                    ensure_ascii=False,
                    default=str,
                )

            self.status_label.config(
                text=(
                    f"Session + ID {selected_track_id} "
                    f"data saved."
                )
            )

        else:

            self.status_label.config(
                text=(
                    f"Session data saved: "
                    f"{output_path.name}"
                )
            )

    # =====================================================
    # Saved Files Browser
    # =====================================================

    def open_recordings(self) -> None:

        self.recordings_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.face_captures_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.data_exports_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.person_data_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        window = tk.Toplevel(
            self.root
        )

        window.title(
            "Retail Brain OS - Saved Files"
        )

        window.geometry(
            "820x500"
        )

        window.minsize(
            680,
            400,
        )

        window.configure(
            bg="#eef1f4"
        )

        tk.Label(
            window,
            text="SAVED FILES",
            font=(
                "Segoe UI",
                14,
                "bold",
            ),
            fg="#18202a",
            bg="#eef1f4",
        ).pack(
            anchor="w",
            padx=20,
            pady=(18, 2),
        )

        tk.Label(
            window,
            text=(
                "Recordings, face captures, session data "
                "and saved person details"
            ),
            font=(
                "Segoe UI",
                9,
            ),
            fg="#56616d",
            bg="#eef1f4",
        ).pack(
            anchor="w",
            padx=20,
            pady=(0, 8),
        )

        list_frame = tk.Frame(
            window,
            bg="#ffffff",
            bd=1,
            relief="solid",
        )

        list_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=8,
        )

        scrollbar = tk.Scrollbar(
            list_frame
        )

        scrollbar.pack(
            side="right",
            fill="y",
        )

        listbox = tk.Listbox(
            list_frame,
            font=("Segoe UI", 9),
            yscrollcommand=scrollbar.set,
            selectmode=tk.SINGLE,
        )

        listbox.pack(
            side="left",
            fill="both",
            expand=True,
        )

        scrollbar.config(
            command=listbox.yview
        )

        # -------------------------------------------------
        # Collect all saved Retail Brain OS files.
        #
        # Existing categories remain unchanged, with
        # session CSV exports and selected-person JSON
        # snapshots added to the same browser.
        # -------------------------------------------------

        saved_files = []

        for path in self.recordings_dir.glob(
            "surveillance_*.mp4"
        ):
            saved_files.append(
                (
                    path,
                    "SURVEILLANCE",
                )
            )

        for path in self.face_captures_dir.glob(
            "person_*.jpg"
        ):
            saved_files.append(
                (
                    path,
                    "FACE CAPTURE",
                )
            )

        for path in self.data_exports_dir.glob(
            "retail_session_*.csv"
        ):
            saved_files.append(
                (
                    path,
                    "SESSION DATA",
                )
            )

        for path in self.person_data_dir.glob(
            "person_*.json"
        ):
            saved_files.append(
                (
                    path,
                    "PERSON DATA",
                )
            )

        saved_files.sort(
            key=lambda item: item[0].stat().st_mtime,
            reverse=True,
        )

        for path, file_type in saved_files:

            size_mb = (
                path.stat().st_size
                / (1024 * 1024)
            )

            modified = datetime.fromtimestamp(
                path.stat().st_mtime
            ).strftime(
                "%d-%m-%Y %H:%M:%S"
            )

            listbox.insert(
                tk.END,
                (
                    f"[{file_type}]   "
                    f"{path.name}   |   "
                    f"{size_mb:.2f} MB   |   "
                    f"{modified}"
                ),
            )

        if not saved_files:

            listbox.insert(
                tk.END,
                "No saved recordings or face captures."
            )

        def selected_file():

            selection = listbox.curselection()

            if not selection:
                return None

            index = selection[0]

            if index >= len(saved_files):
                return None

            return saved_files[index]

        def open_selected():

            selected = selected_file()

            if selected is None:

                self.status_label.config(
                    text="Select a saved file first."
                )

                return

            path, file_type = selected

            try:

                os.startfile(
                    str(path)
                )

                self.status_label.config(
                    text=(
                        f"Opened {file_type.lower()}: "
                        f"{path.name}"
                    )
                )

            except OSError as exc:

                self.status_label.config(
                    text=(
                        "Unable to open saved file: "
                        f"{exc}"
                    )
                )

        def delete_selected():

            selected = selected_file()

            if selected is None:

                self.status_label.config(
                    text="Select a saved file first."
                )

                return

            path, file_type = selected

            confirmed = messagebox.askyesno(
                "Delete Saved File",
                f"Delete {path.name}?",
                parent=window,
            )

            if not confirmed:
                return

            try:

                path.unlink()

                window.destroy()

                self.open_recordings()

                self.status_label.config(
                    text=(
                        f"Deleted {file_type.lower()}: "
                        f"{path.name}"
                    )
                )

            except OSError as exc:

                self.status_label.config(
                    text=(
                        "Unable to delete saved file: "
                        f"{exc}"
                    )
                )

        button_frame = tk.Frame(
            window,
            bg="#eef1f4",
        )

        button_frame.pack(
            fill="x",
            padx=20,
            pady=(8, 18),
        )

        tk.Button(
            button_frame,
            text="OPEN SELECTED",
            command=open_selected,
            width=16,
            height=2,
            relief="flat",
        ).pack(
            side="left",
            padx=4,
        )

        tk.Button(
            button_frame,
            text="DELETE",
            command=delete_selected,
            width=12,
            height=2,
            relief="flat",
        ).pack(
            side="left",
            padx=4,
        )

        tk.Button(
            button_frame,
            text="CLOSE",
            command=window.destroy,
            width=12,
            height=2,
            relief="flat",
        ).pack(
            side="right",
            padx=4,
        )

    # =====================================================
    # Surveillance Recording
    # =====================================================

    def start_recording(self) -> None:

        if self.runtime is None:
            return

        if not self.runtime.is_running():
            return

        if self.recording_active:
            return

        state = self.runtime.get_state()

        if state.frame is None:
            self.status_label.config(
                text=(
                    "Waiting for a camera frame "
                    "before recording."
                )
            )
            return

        frame_height, frame_width = state.frame.shape[:2]

        self.recordings_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        output_path = (
            self.recordings_dir
            / f"surveillance_{timestamp}.mp4"
        )

        fps = state.fps if state.fps > 1.0 else 20.0

        fourcc = cv2.VideoWriter_fourcc(
            *"mp4v"
        )

        writer = cv2.VideoWriter(
            str(output_path),
            fourcc,
            float(fps),
            (
                frame_width,
                frame_height,
            ),
        )

        if not writer.isOpened():

            writer.release()

            self.status_label.config(
                text=(
                    "Unable to start surveillance "
                    "recording."
                )
            )

            return

        self.recording_writer = writer
        self.recording_path = output_path
        self.recording_active = True

        self.record_button.config(
            state="disabled"
        )

        self.stop_record_button.config(
            state="normal"
        )

        self.status_label.config(
            text=(
                f"Recording surveillance: "
                f"{output_path.name}"
            )
        )

    def _write_recording_frame(
        self,
        frame,
    ) -> None:

        writer = self.recording_writer

        if writer is None:
            return

        try:

            writer.write(frame)

        except Exception as exc:

            self.stop_recording()

            self.status_label.config(
                text=(
                    "Recording stopped because "
                    f"of an error: {exc}"
                )
            )

    def stop_recording(self) -> None:

        if not self.recording_active:
            return

        writer = self.recording_writer
        path = self.recording_path

        self.recording_writer = None
        self.recording_path = None
        self.recording_active = False

        if writer is not None:

            try:
                writer.release()

            except Exception:
                pass

        self.stop_record_button.config(
            state="disabled"
        )

        if (
            self.runtime is not None
            and self.runtime.is_running()
        ):

            self.record_button.config(
                state="normal"
            )

        else:

            self.record_button.config(
                state="disabled"
            )

        if path is not None:

            self.status_label.config(
                text=(
                    f"Recording saved: "
                    f"{path.name}"
                )
            )

    def _stop_recording_for_shutdown(self) -> None:

        if self.recording_active:
            self.stop_recording()

    # =====================================================
    # Runtime Stop
    # =====================================================

    def stop_retail_os(self) -> None:

        if self.recording_active:
            self.stop_recording()

        runtime = self.runtime

        if runtime is None:

            return

        if not runtime.is_running():

            return

        if self.runtime_stopping:

            return

        self.runtime_stopping = True

        self.stop_button.config(
            state="disabled"
        )

        self.status_label.config(
            text="Stopping Retail OS..."
        )

        worker = threading.Thread(
            target=self._stop_runtime_worker,
            args=(runtime,),
            daemon=True,
        )

        worker.start()

    def _stop_runtime_worker(
        self,
        runtime: RetailVisionRuntime,
    ) -> None:

        try:

            runtime.stop()

        finally:

            self.root.after(
                0,
                self.runtime_stopped,
            )

    def runtime_stopped(self) -> None:

        self.runtime_stopping = False

        self.runtime = None

        self.runtime_status_label.config(
            text="STOPPED"
        )

        self.start_button.config(
            state="normal"
        )

        self.setup_button.config(
            state="normal"
        )

        self.stop_button.config(
            state="disabled"
        )

        self.record_button.config(
            state="disabled"
        )

        self.stop_record_button.config(
            state="disabled"
        )

        self.capture_face_button.config(
            state="disabled"
        )

        self.save_data_button.config(
            state=(
                "normal"
                if self.session_people
                else "disabled"
            )
        )

        self.status_label.config(
            text="Retail OS stopped."
        )

        self.camera_label.config(
            image="",
            text="Camera stopped",
        )

        self.camera_resolution_label.config(
            text="Resolution: --"
        )

        self.camera_time_label.config(
            text="Time: --"
        )

        self.camera_photo = None

        self.live_dashboard.reset()

    # =====================================================
    # Application Close
    # =====================================================

    def close_application(self) -> None:

        if self.recording_active:
            self.stop_recording()

        runtime = self.runtime

        if runtime is not None:

            if runtime.is_running():

                try:

                    runtime.stop()

                except Exception:

                    pass

        self.root.destroy()

    # =====================================================
    # Run
    # =====================================================

    def run(self) -> None:

        self.root.mainloop()


def main() -> None:

    app = RetailBrainOSApp()

    app.run()


if __name__ == "__main__":

    main()