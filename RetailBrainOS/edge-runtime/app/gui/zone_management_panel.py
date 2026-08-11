"""
Retail Brain OS
Zone Management Panel

Phase B-4.4

Provides the left-side zone management UI shown in the
Retail Brain OS target dashboard.

Responsibilities:
    - Load configured zones from zones.json
    - Display configured zones
    - Select a zone
    - Show selected-zone information
    - Delete one zone
    - Clear all zones
    - Open the existing ZoneSetupWindow for editing
    - Report configuration changes to the parent GUI

This module does NOT:
    - run the camera
    - run detection/tracking
    - modify the vision runtime
    - calculate dwell

The runtime remains the owner of live vision intelligence.
"""

from __future__ import annotations

import json
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox
from uuid import UUID
from typing import Callable

from app.gui.zone_setup_gui import ZoneSetupWindow


ZONES_PATH = (
    Path(__file__).resolve().parent.parent
    / "intelligence"
    / "zones"
    / "zones.json"
)


class ZoneManagementPanel:
    """
    Left-side zone management panel.

    The panel reads the same zones.json used by the existing
    ZoneSetupWindow and RetailVisionRuntime.
    """

    COLORS = (
        "#f0b429",
        "#00bcd4",
        "#a855f7",
        "#10b981",
        "#ef4444",
        "#3b82f6",
        "#ec4899",
        "#f97316",
    )

    def __init__(
        self,
        parent: tk.Widget,
        *,
        on_zones_changed: Callable[[], None] | None = None,
        can_edit: Callable[[], bool] | None = None,
    ) -> None:

        self.parent = parent

        self.on_zones_changed = (
            on_zones_changed
        )

        self.can_edit = (
            can_edit
            if can_edit is not None
            else lambda: True
        )

        self.zones: list[dict] = []

        self.selected_zone_id: str | None = None

        self.zone_buttons: dict[
            str,
            tk.Frame,
        ] = {}

        self.container = tk.Frame(
            parent,
            bg="#ffffff",
            bd=1,
            relief="solid",
        )

        self.container.pack(
            fill="both",
            expand=True,
        )

        self._build_ui()

        self.refresh()

    # =====================================================
    # UI
    # =====================================================

    def _build_ui(self) -> None:

        # -------------------------------------------------
        # ZONE SETUP
        # -------------------------------------------------

        setup_section = tk.Frame(
            self.container,
            bg="#ffffff",
        )

        setup_section.pack(
            fill="x",
            padx=8,
            pady=(8, 6),
        )

        tk.Label(
            setup_section,
            text="ZONE SETUP",
            font=(
                "Segoe UI",
                10,
                "bold",
            ),
            fg="#00bfae",
            bg="#ffffff",
        ).pack(
            anchor="w",
            padx=4,
            pady=(0, 7),
        )

        instruction = tk.Frame(
            setup_section,
            bg="#f4f6f8",
            bd=1,
            relief="solid",
        )

        instruction.pack(
            fill="x",
        )

        tk.Label(
            instruction,
            text="1. Setup Zones",
            font=(
                "Segoe UI",
                9,
                "bold",
            ),
            fg="#18202a",
            bg="#f4f6f8",
        ).pack(
            anchor="w",
            padx=10,
            pady=(9, 2),
        )

        tk.Label(
            instruction,
            text=(
                "Create and name the zones\n"
                "where you want to track\n"
                "customer activity."
            ),
            justify="left",
            font=(
                "Segoe UI",
                7,
            ),
            fg="#555555",
            bg="#f4f6f8",
        ).pack(
            anchor="w",
            padx=10,
            pady=(0, 8),
        )

        self.setup_button = tk.Button(
            instruction,
            text="SETUP ZONES",
            command=self.open_zone_setup,
            font=(
                "Segoe UI",
                9,
                "bold",
            ),
            fg="white",
            bg="#007f7a",
            activebackground="#006d69",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
        )

        self.setup_button.pack(
            fill="x",
            padx=10,
            pady=(0, 10),
            ipady=5,
        )

        # -------------------------------------------------
        # CONFIGURED ZONES
        # -------------------------------------------------

        self.configured_section = tk.Frame(
            self.container,
            bg="#ffffff",
        )

        self.configured_section.pack(
            fill="both",
            expand=True,
            padx=8,
            pady=(2, 6),
        )

        self.configured_title = tk.Label(
            self.configured_section,
            text="CONFIGURED ZONES (0)",
            font=(
                "Segoe UI",
                10,
                "bold",
            ),
            fg="#00bfae",
            bg="#ffffff",
        )

        self.configured_title.pack(
            anchor="w",
            padx=4,
            pady=(4, 7),
        )

        self.zone_list = tk.Frame(
            self.configured_section,
            bg="#ffffff",
        )

        self.zone_list.pack(
            fill="x",
        )

        # -------------------------------------------------
        # ZONE INFO
        # -------------------------------------------------

        self.info_section = tk.Frame(
            self.container,
            bg="#ffffff",
            bd=1,
            relief="solid",
        )

        self.info_section.pack(
            fill="x",
            padx=8,
            pady=(0, 6),
        )

        tk.Label(
            self.info_section,
            text="ZONE INFO",
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
            pady=(7, 6),
        )

        self.selected_label = self._create_info_row(
            "Selected Zone",
            "--",
        )

        self.points_label = self._create_info_row(
            "Points",
            "0",
        )

        self.area_label = self._create_info_row(
            "Area (px²)",
            "0",
        )

        self.updated_label = self._create_info_row(
            "Last Updated",
            "--",
        )

        # -------------------------------------------------
        # CLEAR ALL
        # -------------------------------------------------

        self.clear_button = tk.Button(
            self.container,
            text="CLEAR ALL ZONES",
            command=self.clear_all_zones,
            font=(
                "Segoe UI",
                8,
                "bold",
            ),
            fg="#dc2626",
            bg="#ffffff",
            activeforeground="#b91c1c",
            relief="flat",
            cursor="hand2",
        )

        self.clear_button.pack(
            fill="x",
            padx=8,
            pady=(0, 8),
            ipady=6,
        )

    def _create_info_row(
        self,
        title: str,
        value: str,
    ) -> tk.Label:

        row = tk.Frame(
            self.info_section,
            bg="#ffffff",
        )

        row.pack(
            fill="x",
            padx=8,
            pady=2,
        )

        tk.Label(
            row,
            text=title,
            font=(
                "Segoe UI",
                7,
            ),
            fg="#555555",
            bg="#ffffff",
            anchor="w",
        ).pack(
            side="left",
        )

        value_label = tk.Label(
            row,
            text=value,
            font=(
                "Segoe UI",
                7,
                "bold",
            ),
            fg="#18202a",
            bg="#ffffff",
            anchor="e",
        )

        value_label.pack(
            side="right",
        )

        return value_label

    # =====================================================
    # Configuration
    # =====================================================

    def _load_configuration(self) -> None:

        if not ZONES_PATH.exists():

            self.zones = []

            self.selected_zone_id = None

            return

        try:

            data = json.loads(
                ZONES_PATH.read_text(
                    encoding="utf-8"
                )
            )

            loaded = []

            for item in data.get(
                "zones",
                [],
            ):

                loaded.append(
                    {
                        "zone_id": str(
                            item["zone_id"]
                        ),
                        "camera_id": str(
                            item["camera_id"]
                        ),
                        "name": str(
                            item["name"]
                        ),
                        "polygon": [
                            (
                                float(point[0]),
                                float(point[1]),
                            )
                            for point in item[
                                "polygon"
                            ]
                        ],
                    }
                )

            self.zones = loaded

        except Exception as exc:

            self.zones = []

            messagebox.showerror(
                "Zone Configuration Error",
                (
                    "Could not load zones.json:\n\n"
                    f"{exc}"
                ),
                parent=self.parent.winfo_toplevel(),
            )

        ids = {
            zone["zone_id"]
            for zone in self.zones
        }

        if (
            self.selected_zone_id not in ids
        ):

            self.selected_zone_id = (
                self.zones[0]["zone_id"]
                if self.zones
                else None
            )

    def _save_configuration(
        self,
        zones: list[dict],
    ) -> bool:

        try:

            existing_data = {}

            if ZONES_PATH.exists():

                existing_data = json.loads(
                    ZONES_PATH.read_text(
                        encoding="utf-8"
                    )
                )

            camera_id = existing_data.get(
                "camera_id"
            )

            if camera_id is None:

                if zones:

                    camera_id = zones[0][
                        "camera_id"
                    ]

                else:

                    camera_id = str(
                        UUID(int=0)
                    )

            payload = {
                "camera_id": camera_id,
                "zones": [
                    {
                        "zone_id": zone[
                            "zone_id"
                        ],
                        "camera_id": zone[
                            "camera_id"
                        ],
                        "name": zone[
                            "name"
                        ],
                        "polygon": [
                            [
                                float(point[0]),
                                float(point[1]),
                            ]
                            for point in zone[
                                "polygon"
                            ]
                        ],
                    }
                    for zone in zones
                ],
            }

            ZONES_PATH.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            ZONES_PATH.write_text(
                json.dumps(
                    payload,
                    indent=4,
                ),
                encoding="utf-8",
            )

            return True

        except Exception as exc:

            messagebox.showerror(
                "Save Failed",
                (
                    "Could not save zones.json:\n\n"
                    f"{exc}"
                ),
                parent=self.parent.winfo_toplevel(),
            )

            return False

    # =====================================================
    # Refresh
    # =====================================================

    def refresh(self) -> None:

        self._load_configuration()

        for widget in (
            self.zone_list.winfo_children()
        ):

            widget.destroy()

        self.zone_buttons.clear()

        self.configured_title.config(
            text=(
                f"CONFIGURED ZONES "
                f"({len(self.zones)})"
            )
        )

        if not self.zones:

            tk.Label(
                self.zone_list,
                text="No zones configured",
                font=(
                    "Segoe UI",
                    8,
                ),
                fg="#888888",
                bg="#ffffff",
            ).pack(
                anchor="w",
                padx=8,
                pady=8,
            )

            self._update_info(None)

            return

        for index, zone in enumerate(
            self.zones
        ):

            self._create_zone_row(
                zone,
                index,
            )

        selected = next(
            (
                zone
                for zone in self.zones
                if (
                    zone["zone_id"]
                    == self.selected_zone_id
                )
            ),
            self.zones[0],
        )

        self.selected_zone_id = (
            selected["zone_id"]
        )

        self._update_info(
            selected
        )

        self._refresh_row_selection()

    # =====================================================
    # Zone Rows
    # =====================================================

    def _create_zone_row(
        self,
        zone: dict,
        index: int,
    ) -> None:

        zone_id = zone["zone_id"]

        color = self.COLORS[
            index % len(self.COLORS)
        ]

        row = tk.Frame(
            self.zone_list,
            bg="#f4f6f8",
            bd=1,
            relief="solid",
            cursor="hand2",
        )

        row.pack(
            fill="x",
            padx=3,
            pady=2,
        )

        row.bind(
            "<Button-1>",
            lambda _event, zid=zone_id: (
                self.select_zone(zid)
            ),
        )

        indicator = tk.Frame(
            row,
            bg=color,
            width=6,
        )

        indicator.pack(
            side="left",
            fill="y",
        )

        name_label = tk.Label(
            row,
            text=zone["name"],
            font=(
                "Segoe UI",
                8,
                "bold",
            ),
            fg="#18202a",
            bg="#f4f6f8",
            cursor="hand2",
        )

        name_label.pack(
            side="left",
            padx=(8, 3),
            pady=7,
        )

        name_label.bind(
            "<Button-1>",
            lambda _event, zid=zone_id: (
                self.select_zone(zid)
            ),
        )

        edit_button = tk.Button(
            row,
            text="✎",
            command=lambda zid=zone_id: (
                self.edit_zone(zid)
            ),
            font=(
                "Segoe UI",
                9,
            ),
            fg="#555555",
            bg="#f4f6f8",
            activebackground="#e7eaed",
            relief="flat",
            bd=0,
            cursor="hand2",
            width=2,
        )

        edit_button.pack(
            side="right",
            padx=(0, 1),
        )

        delete_button = tk.Button(
            row,
            text="🗑",
            command=lambda zid=zone_id: (
                self.delete_zone(zid)
            ),
            font=(
                "Segoe UI",
                8,
            ),
            fg="#dc2626",
            bg="#f4f6f8",
            activebackground="#e7eaed",
            relief="flat",
            bd=0,
            cursor="hand2",
            width=2,
        )

        delete_button.pack(
            side="right",
            padx=(0, 4),
        )

        self.zone_buttons[
            zone_id
        ] = row

    # =====================================================
    # Selection
    # =====================================================

    def select_zone(
        self,
        zone_id: str,
    ) -> None:

        self.selected_zone_id = zone_id

        zone = next(
            (
                item
                for item in self.zones
                if item["zone_id"] == zone_id
            ),
            None,
        )

        self._update_info(zone)

        self._refresh_row_selection()

    def _refresh_row_selection(
        self,
    ) -> None:

        for zone_id, row in (
            self.zone_buttons.items()
        ):

            if (
                zone_id
                == self.selected_zone_id
            ):

                row.configure(
                    bg="#e7f8f5"
                )

                for child in (
                    row.winfo_children()
                ):

                    if (
                        child.winfo_class()
                        == "Label"
                    ):

                        child.configure(
                            bg="#e7f8f5"
                        )

            else:

                row.configure(
                    bg="#f4f6f8"
                )

                for child in (
                    row.winfo_children()
                ):

                    if (
                        child.winfo_class()
                        == "Label"
                    ):

                        child.configure(
                            bg="#f4f6f8"
                        )

    # =====================================================
    # Zone Info
    # =====================================================

    def _update_info(
        self,
        zone: dict | None,
    ) -> None:

        if zone is None:

            self.selected_label.config(
                text="--"
            )

            self.points_label.config(
                text="0"
            )

            self.area_label.config(
                text="0"
            )

            self.updated_label.config(
                text="--"
            )

            return

        points = zone["polygon"]

        area = self._polygon_area(
            points
        )

        self.selected_label.config(
            text=zone["name"]
        )

        self.points_label.config(
            text=str(
                len(points)
            )
        )

        self.area_label.config(
            text=f"{area:,.0f}"
        )

        self.updated_label.config(
            text=self._last_updated_text()
        )

    @staticmethod
    def _polygon_area(
        points: list[tuple[float, float]],
    ) -> float:

        if len(points) < 3:

            return 0.0

        total = 0.0

        for index in range(
            len(points)
        ):

            x1, y1 = points[index]

            x2, y2 = points[
                (index + 1) % len(points)
            ]

            total += (
                x1 * y2
                - x2 * y1
            )

        return abs(total) / 2.0

    @staticmethod
    def _last_updated_text() -> str:

        if not ZONES_PATH.exists():

            return "--"

        try:

            modified = datetime.fromtimestamp(
                ZONES_PATH.stat().st_mtime
            )

            return modified.strftime(
                "%d %b %Y %H:%M"
            )

        except OSError:

            return "--"

    # =====================================================
    # Edit
    # =====================================================

    def edit_zone(
        self,
        zone_id: str,
    ) -> None:

        if not self.can_edit():

            messagebox.showinfo(
                "Retail OS Running",
                (
                    "Stop Retail OS before "
                    "editing zones."
                ),
                parent=self.parent.winfo_toplevel(),
            )

            return

        self.selected_zone_id = zone_id

        ZoneSetupWindow(
            self.parent.winfo_toplevel(),
            on_close=self._zone_editor_closed,
        )

    def open_zone_setup(self) -> None:

        if not self.can_edit():

            messagebox.showinfo(
                "Retail OS Running",
                (
                    "Stop Retail OS before "
                    "opening Zone Setup."
                ),
                parent=self.parent.winfo_toplevel(),
            )

            return

        ZoneSetupWindow(
            self.parent.winfo_toplevel(),
            on_close=self._zone_editor_closed,
        )

    def _zone_editor_closed(self) -> None:

        self.refresh()

        self._notify_changed()

    # =====================================================
    # Delete
    # =====================================================

    def delete_zone(
        self,
        zone_id: str,
    ) -> None:

        if not self.can_edit():

            messagebox.showinfo(
                "Retail OS Running",
                (
                    "Stop Retail OS before "
                    "changing zones."
                ),
                parent=self.parent.winfo_toplevel(),
            )

            return

        zone = next(
            (
                item
                for item in self.zones
                if item["zone_id"] == zone_id
            ),
            None,
        )

        if zone is None:

            return

        confirmed = messagebox.askyesno(
            "Delete Zone",
            (
                f'Delete "{zone["name"]}"?\n\n'
                "This removes it from the saved "
                "zone configuration."
            ),
            parent=self.parent.winfo_toplevel(),
        )

        if not confirmed:

            return

        remaining = [
            item
            for item in self.zones
            if item["zone_id"] != zone_id
        ]

        if not self._save_configuration(
            remaining
        ):

            return

        self.selected_zone_id = (
            remaining[0]["zone_id"]
            if remaining
            else None
        )

        self.refresh()

        self._notify_changed()

    # =====================================================
    # Clear All
    # =====================================================

    def clear_all_zones(self) -> None:

        if not self.can_edit():

            messagebox.showinfo(
                "Retail OS Running",
                (
                    "Stop Retail OS before "
                    "changing zones."
                ),
                parent=self.parent.winfo_toplevel(),
            )

            return

        if not self.zones:

            return

        confirmed = messagebox.askyesno(
            "Clear All Zones",
            (
                "Delete ALL configured zones?\n\n"
                "This cannot be undone."
            ),
            parent=self.parent.winfo_toplevel(),
        )

        if not confirmed:

            return

        if not self._save_configuration(
            []
        ):

            return

        self.selected_zone_id = None

        self.refresh()

        self._notify_changed()

    # =====================================================
    # Callback
    # =====================================================

    def _notify_changed(self) -> None:

        if self.on_zones_changed is None:

            return

        try:

            self.on_zones_changed()

        except Exception:

            # The panel must not crash because a
            # parent callback failed.
            pass