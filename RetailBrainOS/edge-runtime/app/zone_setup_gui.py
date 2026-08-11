"""
Retail Brain OS
GUI Zone Setup

Provides a graphical zone calibration/editor workflow.

Zone coordinates are always stored in the original
640x480 camera-frame coordinate system.
"""

from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID, uuid4

import cv2
import numpy as np
import tkinter as tk
from tkinter import messagebox, simpledialog

from app.core.camera_config import (
    CAMERA_HEIGHT,
    CAMERA_INDEX,
    CAMERA_WIDTH,
)

from app.intelligence.zones.zone import Zone


ZONES_PATH = (
    Path(__file__).resolve().parent.parent
    / "intelligence"
    / "zones"
    / "zones.json"
)


class ZoneSetupWindow:
    """
    Graphical zone editor.

    The camera image is displayed at a GUI-friendly size,
    while all saved polygon coordinates remain in the
    original camera-frame coordinate system.
    """

    def __init__(
        self,
        parent: tk.Tk,
        on_close=None,
    ) -> None:

        self.parent = parent
        self.on_close = on_close

        self.window = tk.Toplevel(parent)

        self.window.title(
            "Retail Brain OS - Zone Setup"
        )

        self.window.geometry(
            "1100x700"
        )

        self.window.minsize(
            900,
            600,
        )

        self.window.protocol(
            "WM_DELETE_WINDOW",
            self.close,
        )

        # -------------------------------------------------
        # State
        # -------------------------------------------------

        self.camera_id: UUID = uuid4()

        self.zones: list[Zone] = []

        self.current_points: list[
            tuple[float, float]
        ] = []

        self.frozen = False

        self.frame: np.ndarray | None = None

        self.display_width = 640
        self.display_height = 480

        self.cap = None

        # -------------------------------------------------
        # Load existing configuration
        # -------------------------------------------------

        self.load_configuration()

        # -------------------------------------------------
        # Build interface
        # -------------------------------------------------

        self.build_ui()

        # -------------------------------------------------
        # Start camera
        # -------------------------------------------------

        self.start_camera()

        self.update_camera()

    # =====================================================
    # Configuration
    # =====================================================

    def load_configuration(self) -> None:
        """
        Load existing zones.json.
        """

        if not ZONES_PATH.exists():

            return

        try:

            data = json.loads(
                ZONES_PATH.read_text(
                    encoding="utf-8"
                )
            )

            existing_camera_id = data.get(
                "camera_id"
            )

            if existing_camera_id:

                self.camera_id = UUID(
                    existing_camera_id
                )

            loaded_zones: list[Zone] = []

            for item in data.get(
                "zones",
                [],
            ):

                zone = Zone(
                    zone_id=UUID(
                        item["zone_id"]
                    ),
                    camera_id=UUID(
                        item["camera_id"]
                    ),
                    name=item["name"],
                    polygon=tuple(
                        (
                            float(point[0]),
                            float(point[1]),
                        )
                        for point in item["polygon"]
                    ),
                )

                loaded_zones.append(zone)

            self.zones = loaded_zones

        except Exception as exc:

            messagebox.showerror(
                "Zone Configuration Error",
                f"Could not load zones.json:\n\n{exc}",
                parent=self.window,
            )

    def save_configuration(self) -> None:
        """
        Persist the complete current configuration.
        """

        configuration = {
            "camera_id": str(
                self.camera_id
            ),
            "zones": [
                {
                    "zone_id": str(
                        zone.zone_id
                    ),
                    "camera_id": str(
                        zone.camera_id
                    ),
                    "name": zone.name,
                    "polygon": [
                        [
                            float(x),
                            float(y),
                        ]
                        for x, y in zone.polygon
                    ],
                }
                for zone in self.zones
            ],
        }

        try:

            ZONES_PATH.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            ZONES_PATH.write_text(
                json.dumps(
                    configuration,
                    indent=4,
                ),
                encoding="utf-8",
            )

            self.refresh_zone_list()

            self.status_label.config(
                text=(
                    f"Saved {len(self.zones)} zone(s)"
                )
            )

        except Exception as exc:

            messagebox.showerror(
                "Save Error",
                f"Could not save zones.json:\n\n{exc}",
                parent=self.window,
            )

    # =====================================================
    # UI
    # =====================================================

    def build_ui(self) -> None:

        # -------------------------------------------------
        # Header
        # -------------------------------------------------

        header = tk.Frame(
            self.window,
            bg="#18202a",
            height=60,
        )

        header.pack(
            fill="x"
        )

        tk.Label(
            header,
            text="RETAIL BRAIN OS",
            font=(
                "Segoe UI",
                18,
                "bold",
            ),
            fg="white",
            bg="#18202a",
        ).pack(
            side="left",
            padx=20,
            pady=12,
        )

        tk.Label(
            header,
            text="Zone Setup",
            font=(
                "Segoe UI",
                11,
            ),
            fg="#b8c2cc",
            bg="#18202a",
        ).pack(
            side="left",
            padx=5,
        )

        # -------------------------------------------------
        # Main area
        # -------------------------------------------------

        main = tk.Frame(
            self.window,
            bg="#eef1f4",
        )

        main.pack(
            fill="both",
            expand=True,
        )

        # -------------------------------------------------
        # Camera area
        # -------------------------------------------------

        camera_container = tk.Frame(
            main,
            bg="#111111",
        )

        camera_container.pack(
            side="left",
            fill="both",
            expand=True,
            padx=12,
            pady=12,
        )

        self.camera_label = tk.Label(
            camera_container,
            bg="black",
        )

        self.camera_label.pack(
            fill="both",
            expand=True,
        )

        self.camera_label.bind(
            "<Button-1>",
            self.on_camera_click,
        )

        # -------------------------------------------------
        # Controls panel
        # -------------------------------------------------

        controls = tk.Frame(
            main,
            width=280,
            bg="white",
        )

        controls.pack(
            side="right",
            fill="y",
            padx=12,
            pady=12,
        )

        controls.pack_propagate(
            False
        )

        tk.Label(
            controls,
            text="ZONE SETUP",
            font=(
                "Segoe UI",
                15,
                "bold",
            ),
            bg="white",
            fg="#18202a",
        ).pack(
            anchor="w",
            padx=18,
            pady=18,
        )

        # -------------------------------------------------
        # Status
        # -------------------------------------------------

        self.status_label = tk.Label(
            controls,
            text="Live camera",
            font=(
                "Segoe UI",
                10,
            ),
            bg="white",
            fg="#555555",
            wraplength=240,
            justify="left",
        )

        self.status_label.pack(
            anchor="w",
            padx=18,
            pady=(0, 12),
        )

        # -------------------------------------------------
        # Freeze button
        # -------------------------------------------------

        self.freeze_button = tk.Button(
            controls,
            text="FREEZE FRAME",
            command=self.toggle_freeze,
            font=(
                "Segoe UI",
                10,
                "bold",
            ),
            relief="flat",
            padx=10,
            pady=8,
        )

        self.freeze_button.pack(
            fill="x",
            padx=18,
            pady=5,
        )

        # -------------------------------------------------
        # Add zone
        # -------------------------------------------------

        self.add_button = tk.Button(
            controls,
            text="ADD ZONE",
            command=self.add_zone,
            font=(
                "Segoe UI",
                10,
                "bold",
            ),
            relief="flat",
            padx=10,
            pady=8,
        )

        self.add_button.pack(
            fill="x",
            padx=18,
            pady=5,
        )

        # -------------------------------------------------
        # Clear polygon
        # -------------------------------------------------

        tk.Button(
            controls,
            text="CLEAR CURRENT",
            command=self.clear_current_polygon,
            font=(
                "Segoe UI",
                10,
            ),
            relief="flat",
            padx=10,
            pady=8,
        ).pack(
            fill="x",
            padx=18,
            pady=5,
        )

        # -------------------------------------------------
        # Zone list
        # -------------------------------------------------

        tk.Label(
            controls,
            text="CONFIGURED ZONES",
            font=(
                "Segoe UI",
                10,
                "bold",
            ),
            bg="white",
            fg="#333333",
        ).pack(
            anchor="w",
            padx=18,
            pady=(20, 5),
        )

        self.zone_listbox = tk.Listbox(
            controls,
            height=8,
            font=(
                "Segoe UI",
                10,
            ),
        )

        self.zone_listbox.pack(
            fill="x",
            padx=18,
        )

        # -------------------------------------------------
        # Delete
        # -------------------------------------------------

        tk.Button(
            controls,
            text="DELETE SELECTED",
            command=self.delete_selected_zone,
            font=(
                "Segoe UI",
                10,
            ),
            relief="flat",
            padx=10,
            pady=8,
        ).pack(
            fill="x",
            padx=18,
            pady=5,
        )

        # -------------------------------------------------
        # Reset
        # -------------------------------------------------

        tk.Button(
            controls,
            text="RESET ALL ZONES",
            command=self.reset_all_zones,
            font=(
                "Segoe UI",
                10,
            ),
            relief="flat",
            padx=10,
            pady=8,
        ).pack(
            fill="x",
            padx=18,
            pady=5,
        )

        # -------------------------------------------------
        # Save
        # -------------------------------------------------

        tk.Button(
            controls,
            text="SAVE CONFIGURATION",
            command=self.save_configuration,
            font=(
                "Segoe UI",
                10,
                "bold",
            ),
            relief="flat",
            padx=10,
            pady=8,
        ).pack(
            fill="x",
            padx=18,
            pady=5,
        )

        # -------------------------------------------------
        # Back
        # -------------------------------------------------

        tk.Button(
            controls,
            text="BACK",
            command=self.close,
            font=(
                "Segoe UI",
                10,
            ),
            relief="flat",
            padx=10,
            pady=8,
        ).pack(
            fill="x",
            padx=18,
            pady=(15, 5),
        )

        self.refresh_zone_list()

    # =====================================================
    # Camera
    # =====================================================

    def start_camera(self) -> None:

        self.cap = cv2.VideoCapture(
            CAMERA_INDEX
        )

        if not self.cap.isOpened():

            messagebox.showerror(
                "Camera Error",
                "Could not open the camera.",
                parent=self.window,
            )

            return

        self.cap.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            CAMERA_WIDTH,
        )

        self.cap.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            CAMERA_HEIGHT,
        )

    def update_camera(self) -> None:

        if not self.window.winfo_exists():

            return

        if self.cap is not None and not self.frozen:

            success, image = self.cap.read()

            if success:

                self.frame = image

        if self.frame is not None:

            display = self.draw_frame(
                self.frame
            )

            self.show_frame(
                display
            )

        self.window.after(
            30,
            self.update_camera,
        )

    # =====================================================
    # Coordinate mapping
    # =====================================================

    def frame_to_display(
        self,
        x: float,
        y: float,
    ) -> tuple[int, int]:

        if self.frame is None:

            return (
                int(x),
                int(y),
            )

        frame_height, frame_width = (
            self.frame.shape[:2]
        )

        widget_width = (
            self.camera_label.winfo_width()
        )

        widget_height = (
            self.camera_label.winfo_height()
        )

        if (
            widget_width <= 1
            or widget_height <= 1
        ):

            return (
                int(x),
                int(y),
            )

        scale = min(
            widget_width / frame_width,
            widget_height / frame_height,
        )

        displayed_width = (
            frame_width * scale
        )

        displayed_height = (
            frame_height * scale
        )

        offset_x = (
            widget_width
            - displayed_width
        ) / 2

        offset_y = (
            widget_height
            - displayed_height
        ) / 2

        return (
            int(
                x * scale + offset_x
            ),
            int(
                y * scale + offset_y
            ),
        )

    def display_to_frame(
        self,
        x: int,
        y: int,
    ) -> tuple[float, float] | None:

        if self.frame is None:

            return None

        frame_height, frame_width = (
            self.frame.shape[:2]
        )

        widget_width = (
            self.camera_label.winfo_width()
        )

        widget_height = (
            self.camera_label.winfo_height()
        )

        if (
            widget_width <= 1
            or widget_height <= 1
        ):

            return None

        scale = min(
            widget_width / frame_width,
            widget_height / frame_height,
        )

        displayed_width = (
            frame_width * scale
        )

        displayed_height = (
            frame_height * scale
        )

        offset_x = (
            widget_width
            - displayed_width
        ) / 2

        offset_y = (
            widget_height
            - displayed_height
        ) / 2

        frame_x = (
            x - offset_x
        ) / scale

        frame_y = (
            y - offset_y
        ) / scale

        if (
            frame_x < 0
            or frame_x >= frame_width
            or frame_y < 0
            or frame_y >= frame_height
        ):

            return None

        return (
            float(frame_x),
            float(frame_y),
        )

    # =====================================================
    # Mouse
    # =====================================================

    def on_camera_click(
        self,
        event,
    ) -> None:

        if not self.frozen:

            self.status_label.config(
                text=(
                    "Freeze the frame before "
                    "drawing a zone."
                )
            )

            return

        point = self.display_to_frame(
            event.x,
            event.y,
        )

        if point is None:

            return

        self.current_points.append(
            point
        )

        self.status_label.config(
            text=(
                f"Current polygon: "
                f"{len(self.current_points)} points"
            )
        )

    # =====================================================
    # Drawing
    # =====================================================

    def draw_frame(
        self,
        image: np.ndarray,
    ) -> np.ndarray:

        display = image.copy()

        # -------------------------------------------------
        # Existing zones
        # -------------------------------------------------

        for index, zone in enumerate(
            self.zones,
            start=1,
        ):

            points = [
                (
                    int(x),
                    int(y),
                )
                for x, y in zone.polygon
            ]

            if len(points) >= 3:

                cv2.polylines(
                    display,
                    [
                        np.array(
                            points,
                            dtype=np.int32,
                        )
                    ],
                    True,
                    (0, 255, 0),
                    2,
                )

            if points:

                x, y = points[0]

                cv2.putText(
                    display,
                    f"{index}. {zone.name}",
                    (
                        x,
                        max(
                            y - 10,
                            25,
                        ),
                    ),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2,
                )

        # -------------------------------------------------
        # Current polygon
        # -------------------------------------------------

        if self.current_points:

            points = [
                (
                    int(x),
                    int(y),
                )
                for x, y in self.current_points
            ]

            for point in points:

                cv2.circle(
                    display,
                    point,
                    5,
                    (0, 255, 255),
                    -1,
                )

            for index in range(
                len(points) - 1
            ):

                cv2.line(
                    display,
                    points[index],
                    points[index + 1],
                    (0, 255, 255),
                    2,
                )

        # -------------------------------------------------
        # Frozen indicator
        # -------------------------------------------------

        if self.frozen:

            cv2.rectangle(
                display,
                (0, 0),
                (
                    display.shape[1],
                    42,
                ),
                (25, 25, 25),
                -1,
            )

            cv2.putText(
                display,
                "FROZEN - DRAW ZONE",
                (12, 28),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 255),
                2,
            )

        return display

    def show_frame(
        self,
        image: np.ndarray,
    ) -> None:

        from PIL import Image, ImageTk

        frame_height, frame_width = (
            image.shape[:2]
        )

        widget_width = max(
            self.camera_label.winfo_width(),
            640,
        )

        widget_height = max(
            self.camera_label.winfo_height(),
            480,
        )

        scale = min(
            widget_width / frame_width,
            widget_height / frame_height,
        )

        new_width = max(
            1,
            int(frame_width * scale),
        )

        new_height = max(
            1,
            int(frame_height * scale),
        )

        resized = cv2.resize(
            image,
            (
                new_width,
                new_height,
            ),
            interpolation=cv2.INTER_AREA,
        )

        rgb = cv2.cvtColor(
            resized,
            cv2.COLOR_BGR2RGB,
        )

        photo = ImageTk.PhotoImage(
            Image.fromarray(rgb)
        )

        self.camera_label.configure(
            image=photo
        )

        self.camera_label.image = photo

    # =====================================================
    # Zone operations
    # =====================================================

    def toggle_freeze(self) -> None:

        self.frozen = not self.frozen

        if self.frozen:

            self.freeze_button.config(
                text="RESUME CAMERA"
            )

            self.status_label.config(
                text=(
                    "Frame frozen. "
                    "Click the camera to add "
                    "polygon points."
                )
            )

        else:

            self.freeze_button.config(
                text="FREEZE FRAME"
            )

            self.current_points.clear()

            self.status_label.config(
                text="Live camera"
            )

    def clear_current_polygon(self) -> None:

        self.current_points.clear()

        self.status_label.config(
            text="Current polygon cleared."
        )

    def add_zone(self) -> None:

        if not self.frozen:

            messagebox.showwarning(
                "Freeze Required",
                "Freeze the camera before creating a zone.",
                parent=self.window,
            )

            return

        if len(self.current_points) < 3:

            messagebox.showwarning(
                "Not Enough Points",
                "A zone requires at least 3 points.",
                parent=self.window,
            )

            return

        name = simpledialog.askstring(
            "Zone Name",
            "Enter the name for this zone:",
            parent=self.window,
        )

        if name is None:

            return

        name = name.strip()

        if not name:

            messagebox.showwarning(
                "Invalid Name",
                "Zone name cannot be empty.",
                parent=self.window,
            )

            return

        zone = Zone(
            zone_id=uuid4(),
            camera_id=self.camera_id,
            name=name,
            polygon=tuple(
                self.current_points
            ),
        )

        self.zones.append(
            zone
        )

        self.current_points.clear()

        self.refresh_zone_list()

        self.save_configuration()

        self.status_label.config(
            text=(
                f"Added '{name}'. "
                f"You can create another zone."
            )
        )

    def delete_selected_zone(self) -> None:

        selection = (
            self.zone_listbox.curselection()
        )

        if not selection:

            messagebox.showwarning(
                "No Zone Selected",
                "Select a zone first.",
                parent=self.window,
            )

            return

        index = selection[0]

        zone = self.zones[index]

        confirmed = messagebox.askyesno(
            "Delete Zone",
            f"Delete '{zone.name}'?",
            parent=self.window,
        )

        if not confirmed:

            return

        self.zones.pop(
            index
        )

        self.save_configuration()

        self.status_label.config(
            text=(
                f"Deleted '{zone.name}'."
            )
        )

    def reset_all_zones(self) -> None:

        if not self.zones:

            return

        confirmed = messagebox.askyesno(
            "Reset All Zones",
            (
                "Delete ALL configured zones?"
                "\n\nThis cannot be undone."
            ),
            parent=self.window,
        )

        if not confirmed:

            return

        self.zones.clear()

        self.current_points.clear()

        self.save_configuration()

        self.status_label.config(
            text="All zones deleted."
        )

    def refresh_zone_list(self) -> None:

        self.zone_listbox.delete(
            0,
            tk.END,
        )

        for index, zone in enumerate(
            self.zones,
            start=1,
        ):

            self.zone_listbox.insert(
                tk.END,
                f"{index}. {zone.name}",
            )

    # =====================================================
    # Close
    # =====================================================

    def close(self) -> None:

        if self.cap is not None:

            self.cap.release()

            self.cap = None

        self.window.destroy()

        if self.on_close:

            self.on_close()