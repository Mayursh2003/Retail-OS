"""
Retail Brain OS
Live Intelligence Dashboard

Phase B-4.2.1

Responsible for presenting live runtime intelligence.

This component does NOT:
    - run detection
    - run tracking
    - calculate zones
    - calculate dwell
    - own the camera

B-4.2.1 focuses on stable and efficient Tkinter updates.
"""

from __future__ import annotations

from datetime import datetime, timedelta
import time
import tkinter as tk
from typing import Any


class LiveDashboard:
    """
    Right-side live intelligence dashboard.

    Displays:
        - Live statistics
        - Current zone-wise dwell
        - Recent entry/exit events

    The dashboard does not calculate intelligence.
    It only presents the intelligence produced by
    the Retail Vision Runtime.
    """

    # =====================================================
    # Configuration
    # =====================================================

    RECENT_EVENT_WINDOW = timedelta(
        minutes=5
    )

    # Dashboard does not need to refresh at camera FPS.
    # 5 updates per second is enough for human-facing UI.
    DASHBOARD_REFRESH_INTERVAL = 0.20

    # =====================================================
    # Initialization
    # =====================================================

    def __init__(
        self,
        parent: tk.Widget,
    ) -> None:

        self.parent = parent

        # -------------------------------------------------
        # Historical counters
        # -------------------------------------------------

        self.total_entered = 0
        self.total_exited = 0

        self.processed_event_ids: set[str] = set()

        # -------------------------------------------------
        # Recent events
        # -------------------------------------------------

        self.recent_events: list[
            dict[str, Any]
        ] = []

        # -------------------------------------------------
        # Stable dwell rows
        #
        # Key:
        #
        #     (zone_id, track_id)
        #
        # Value:
        #
        #     row widget information
        # -------------------------------------------------

        self.dwell_rows: dict[
            tuple[Any, Any],
            dict[str, tk.Widget],
        ] = {}

        self.dwell_signature: tuple[Any, ...] = ()

        # -------------------------------------------------
        # Stable active-person rows
        #
        # Key:
        #
        #     (zone_id, track_id)
        # -------------------------------------------------

        self.person_rows: dict[
            tuple[Any, Any],
            dict[str, tk.Widget],
        ] = {}

        self.person_signature: tuple[Any, ...] = ()

        # -------------------------------------------------
        # Selected person state
        # -------------------------------------------------

        self.selected_person_key: tuple[Any, Any] | None = None

        self.current_people: dict[
            tuple[Any, Any],
            Any,
        ] = {}

        self._last_zones: Any = []

        # -------------------------------------------------
        # Event UI state
        # -------------------------------------------------

        self.events_signature: tuple[Any, ...] = ()

        # -------------------------------------------------
        # Dashboard throttling
        # -------------------------------------------------

        self.last_update_time = 0.0

        # =================================================
        # Main container
        # =================================================

        self.container = tk.Frame(
            parent,
            bg="#ffffff",
        )

        self.container.pack(
            fill="x",
            padx=8,
            pady=(0, 8),
        )

        # =================================================
        # LIVE INTELLIGENCE
        # =================================================

        tk.Label(
            self.container,
            text="LIVE INTELLIGENCE",
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
            pady=(4, 6),
        )

        # =================================================
        # Statistics
        # =================================================

        stats_frame = tk.Frame(
            self.container,
            bg="#ffffff",
        )

        stats_frame.pack(
            fill="x",
        )

        stats_frame.grid_columnconfigure(
            0,
            weight=1,
        )

        stats_frame.grid_columnconfigure(
            1,
            weight=1,
        )

        self.people_value = (
            self._create_stat_card(
                stats_frame,
                "PEOPLE IN STORE",
                "0",
                0,
                0,
            )
        )

        self.entered_value = (
            self._create_stat_card(
                stats_frame,
                "TOTAL ENTERED",
                "0",
                0,
                1,
            )
        )

        self.exited_value = (
            self._create_stat_card(
                stats_frame,
                "TOTAL EXITED",
                "0",
                1,
                0,
            )
        )

        self.zones_value = (
            self._create_stat_card(
                stats_frame,
                "ACTIVE ZONES",
                "0",
                1,
                1,
            )
        )

        # =================================================
        # Connection Status
        # =================================================

        self.status_label = tk.Label(
            self.container,
            text="Waiting for Retail OS...",
            font=(
                "Segoe UI",
                8,
            ),
            fg="#777777",
            bg="#ffffff",
        )

        self.status_label.pack(
            anchor="w",
            padx=4,
            pady=(6, 8),
        )

        # =================================================
        # ZONE WISE DWELL
        # =================================================

        self.dwell_section = tk.Frame(
            self.container,
            bg="#ffffff",
        )

        self.dwell_section.pack(
            fill="x",
            pady=(0, 8),
        )

        tk.Label(
            self.dwell_section,
            text="ZONE WISE DWELL TIME",
            font=(
                "Segoe UI",
                9,
                "bold",
            ),
            fg="#00bfae",
            bg="#ffffff",
        ).pack(
            anchor="w",
            padx=4,
            pady=(0, 5),
        )

        self.dwell_list = tk.Frame(
            self.dwell_section,
            bg="#ffffff",
        )

        self.dwell_list.pack(
            fill="x",
        )

        # Initial empty state.
        self._show_empty_dwell_state()

        # =================================================
        # ACTIVE PEOPLE
        # =================================================

        self.people_section = tk.Frame(
            self.container,
            bg="#ffffff",
        )

        self.people_section.pack(
            fill="x",
            pady=(0, 8),
        )

        tk.Label(
            self.people_section,
            text="ACTIVE PEOPLE",
            font=(
                "Segoe UI",
                9,
                "bold",
            ),
            fg="#00bfae",
            bg="#ffffff",
        ).pack(
            anchor="w",
            padx=4,
            pady=(0, 5),
        )

        self.people_list = tk.Frame(
            self.people_section,
            bg="#ffffff",
        )

        self.people_list.pack(
            fill="x",
        )

        self._show_empty_people_state()

        # =================================================
        # PERSON DETAILS
        # =================================================

        self.person_details_section = tk.Frame(
            self.container,
            bg="#ffffff",
        )

        self.person_details_section.pack(
            fill="x",
            pady=(0, 8),
        )

        tk.Label(
            self.person_details_section,
            text="PERSON DETAILS (SELECTED)",
            font=(
                "Segoe UI",
                9,
                "bold",
            ),
            fg="#00bfae",
            bg="#ffffff",
        ).pack(
            anchor="w",
            padx=4,
            pady=(0, 5),
        )

        self.person_details_frame = tk.Frame(
            self.person_details_section,
            bg="#f4f6f8",
            bd=1,
            relief="solid",
        )

        self.person_details_frame.pack(
            fill="x",
            padx=3,
        )

        self.person_details_empty = tk.Label(
            self.person_details_frame,
            text="Select an active person to view details",
            font=(
                "Segoe UI",
                8,
            ),
            fg="#888888",
            bg="#f4f6f8",
        )

        self.person_details_empty.pack(
            anchor="w",
            padx=8,
            pady=8,
        )

        # =================================================
        # RECENT EVENTS
        # =================================================

        self.events_section = tk.Frame(
            self.container,
            bg="#ffffff",
        )

        self.events_section.pack(
            fill="x",
            pady=(0, 8),
        )

        tk.Label(
            self.events_section,
            text="RECENT EVENTS",
            font=(
                "Segoe UI",
                9,
                "bold",
            ),
            fg="#00bfae",
            bg="#ffffff",
        ).pack(
            anchor="w",
            padx=4,
            pady=(0, 2),
        )

        tk.Label(
            self.events_section,
            text="Last 5 Minutes",
            font=(
                "Segoe UI",
                7,
            ),
            fg="#888888",
            bg="#ffffff",
        ).pack(
            anchor="w",
            padx=4,
            pady=(0, 5),
        )

        self.events_list = tk.Frame(
            self.events_section,
            bg="#ffffff",
        )

        self.events_list.pack(
            fill="x",
        )

        self._show_empty_events_state()

    # =====================================================
    # Statistic Card
    # =====================================================

    def _create_stat_card(
        self,
        parent: tk.Widget,
        title: str,
        value: str,
        row: int,
        column: int,
    ) -> tk.Label:

        card = tk.Frame(
            parent,
            bg="#f4f6f8",
            bd=1,
            relief="solid",
        )

        card.grid(
            row=row,
            column=column,
            sticky="nsew",
            padx=3,
            pady=3,
        )

        tk.Label(
            card,
            text=title,
            font=(
                "Segoe UI",
                7,
                "bold",
            ),
            fg="#777777",
            bg="#f4f6f8",
        ).pack(
            anchor="w",
            padx=7,
            pady=(5, 0),
        )

        value_label = tk.Label(
            card,
            text=value,
            font=(
                "Segoe UI",
                13,
                "bold",
            ),
            fg="#18202a",
            bg="#f4f6f8",
        )

        value_label.pack(
            anchor="w",
            padx=7,
            pady=(0, 5),
        )

        return value_label

    # =====================================================
    # Main Update
    # =====================================================

    def update(
        self,
        intelligence_result: Any,
        zones: Any,
    ) -> None:

        if intelligence_result is None:
            return

        # -------------------------------------------------
        # Throttle GUI dashboard updates.
        #
        # Camera remains completely independent.
        # -------------------------------------------------

        now = time.monotonic()

        if (
            now - self.last_update_time
            < self.DASHBOARD_REFRESH_INTERVAL
        ):
            return

        self.last_update_time = now

        persons = (
            intelligence_result.persons
        )

        # -------------------------------------------------
        # Current people count
        # -------------------------------------------------

        people_in_store = len(
            persons
        )

        # -------------------------------------------------
        # Process entry/exit events
        # -------------------------------------------------

        new_event_added = False

        for person in persons:

            event = (
                person.entry_exit_event
            )

            if event is None:
                continue

            event_id = str(
                event.event_id
            )

            if event_id in (
                self.processed_event_ids
            ):
                continue

            self.processed_event_ids.add(
                event_id
            )

            event_type = (
                event.event_type.value
            )

            zone_name = (
                self._get_zone_name(
                    event.zone_id,
                    zones,
                )
            )

            event_record = {
                "event_id": event_id,
                "track_id": event.track_id,
                "event_type": event_type,
                "zone_name": zone_name,
                "timestamp": event.timestamp,
            }

            self.recent_events.insert(
                0,
                event_record,
            )

            new_event_added = True

            if event_type == (
                "customer_entry"
            ):

                self.total_entered += 1

            elif event_type == (
                "customer_exit"
            ):

                self.total_exited += 1

        # -------------------------------------------------
        # Remove expired events
        # -------------------------------------------------

        reference_time = (
            intelligence_result.timestamp
        )

        events_changed = (
            self._remove_old_events(
                reference_time
            )
        )

        # -------------------------------------------------
        # Update statistics
        # -------------------------------------------------

        self.people_value.config(
            text=str(
                people_in_store
            )
        )

        self.entered_value.config(
            text=str(
                self.total_entered
            )
        )

        self.exited_value.config(
            text=str(
                self.total_exited
            )
        )

        self.zones_value.config(
            text=str(
                len(zones)
            )
        )

        self.status_label.config(
            text="Live intelligence connected"
        )

        # -------------------------------------------------
        # Update dwell
        # -------------------------------------------------

        self._update_dwell_list(
            persons,
            zones,
        )

        # -------------------------------------------------
        # Update active people
        # -------------------------------------------------

        self._update_people_list(
            persons,
            zones,
        )

        self._last_zones = zones

        # -------------------------------------------------
        # Update events only when necessary
        # -------------------------------------------------

        if (
            new_event_added
            or events_changed
        ):

            self._update_events_list()

    # =====================================================
    # Zone Name
    # =====================================================

    @staticmethod
    def _get_zone_name(
        zone_id: Any,
        zones: Any,
    ) -> str:

        if zone_id is None:
            return "Outside"

        for zone in zones:

            if zone.zone_id == zone_id:

                return zone.name

        return "Unknown"

    # =====================================================
    # Format Duration
    # =====================================================

    @staticmethod
    def _format_duration(
        duration: Any,
    ) -> str:

        if duration is None:
            return "--:--"

        total_seconds = max(
            0,
            int(
                duration.total_seconds()
            ),
        )

        hours = (
            total_seconds // 3600
        )

        minutes = (
            (total_seconds % 3600)
            // 60
        )

        seconds = (
            total_seconds % 60
        )

        if hours > 0:

            return (
                f"{hours:02d}:"
                f"{minutes:02d}:"
                f"{seconds:02d}"
            )

        return (
            f"{minutes:02d}:"
            f"{seconds:02d}"
        )

    # =====================================================
    # Zone Wise Dwell
    # =====================================================

    def _update_dwell_list(
        self,
        persons: list[Any],
        zones: Any,
    ) -> None:

        # -------------------------------------------------
        # Build current stable row set.
        # -------------------------------------------------

        current_rows: dict[
            tuple[Any, Any],
            Any,
        ] = {}

        for person in persons:

            if (
                person.zone_id is None
                or person.dwell_time is None
            ):
                continue

            key = (
                person.zone_id,
                person.track_id,
            )

            current_rows[key] = person

        current_keys = tuple(
            sorted(
                current_rows.keys(),
                key=lambda item: (
                    str(item[0]),
                    str(item[1]),
                ),
            )
        )

        # -------------------------------------------------
        # Create/remove rows only when membership changes.
        # -------------------------------------------------

        if (
            current_keys
            != self.dwell_signature
        ):

            self._sync_dwell_rows(
                current_rows,
                zones,
            )

            self.dwell_signature = (
                current_keys
            )

        # -------------------------------------------------
        # Update values of existing rows.
        # This happens without destroying widgets.
        # -------------------------------------------------

        for key, person in (
            current_rows.items()
        ):

            row_data = (
                self.dwell_rows.get(key)
            )

            if row_data is None:
                continue

            zone_name = (
                self._get_zone_name(
                    person.zone_id,
                    zones,
                )
            )

            row_data[
                "zone_label"
            ].config(
                text=zone_name
            )

            row_data[
                "id_label"
            ].config(
                text=f"ID: {person.track_id}"
            )

            row_data[
                "dwell_label"
            ].config(
                text=self._format_duration(
                    person.dwell_time
                )
            )

    # =====================================================
    # Synchronize Dwell Rows
    # =====================================================

    def _sync_dwell_rows(
        self,
        current_rows: dict[
            tuple[Any, Any],
            Any,
        ],
        zones: Any,
    ) -> None:

        current_keys = set(
            current_rows.keys()
        )

        existing_keys = set(
            self.dwell_rows.keys()
        )

        # -------------------------------------------------
        # Remove rows that no longer exist.
        # -------------------------------------------------

        removed_keys = (
            existing_keys
            - current_keys
        )

        for key in removed_keys:

            row_data = (
                self.dwell_rows.pop(key)
            )

            row_data[
                "row"
            ].destroy()

        # -------------------------------------------------
        # Empty state.
        # -------------------------------------------------

        if not current_keys:

            self._show_empty_dwell_state()

            return

        # Remove empty-state widget if present.
        self._remove_dwell_empty_state()

        # -------------------------------------------------
        # Create only genuinely new rows.
        # -------------------------------------------------

        sorted_keys = sorted(
            current_keys,
            key=lambda item: (
                str(item[0]),
                str(item[1]),
            ),
        )

        for index, key in enumerate(
            sorted_keys
        ):

            if key in self.dwell_rows:
                continue

            person = current_rows[key]

            row = tk.Frame(
                self.dwell_list,
                bg="#f4f6f8",
                bd=1,
                relief="solid",
            )

            row.pack(
                fill="x",
                padx=3,
                pady=2,
            )

            indicator_color = (
                self._get_zone_color(
                    index
                )
            )

            indicator = tk.Frame(
                row,
                bg=indicator_color,
                width=5,
            )

            indicator.pack(
                side="left",
                fill="y",
            )

            zone_label = tk.Label(
                row,
                text=self._get_zone_name(
                    person.zone_id,
                    zones,
                ),
                font=(
                    "Segoe UI",
                    8,
                    "bold",
                ),
                fg="#18202a",
                bg="#f4f6f8",
            )

            zone_label.pack(
                side="left",
                padx=(7, 3),
                pady=6,
            )

            id_label = tk.Label(
                row,
                text=f"ID: {person.track_id}",
                font=(
                    "Segoe UI",
                    7,
                ),
                fg="#666666",
                bg="#f4f6f8",
            )

            id_label.pack(
                side="left",
                padx=3,
            )

            dwell_label = tk.Label(
                row,
                text=self._format_duration(
                    person.dwell_time
                ),
                font=(
                    "Segoe UI",
                    8,
                    "bold",
                ),
                fg="#00a98f",
                bg="#f4f6f8",
            )

            dwell_label.pack(
                side="right",
                padx=7,
            )

            self.dwell_rows[key] = {
                "row": row,
                "zone_label": zone_label,
                "id_label": id_label,
                "dwell_label": dwell_label,
            }

    # =====================================================
    # Empty Dwell State
    # =====================================================

    def _show_empty_dwell_state(
        self,
    ) -> None:

        if hasattr(
            self,
            "dwell_empty_label",
        ):

            if (
                self.dwell_empty_label.winfo_exists()
            ):

                return

        self.dwell_empty_label = tk.Label(
            self.dwell_list,
            text="No active zone dwell",
            font=(
                "Segoe UI",
                8,
            ),
            fg="#888888",
            bg="#ffffff",
        )

        self.dwell_empty_label.pack(
            anchor="w",
            padx=5,
            pady=4,
        )

    def _remove_dwell_empty_state(
        self,
    ) -> None:

        label = getattr(
            self,
            "dwell_empty_label",
            None,
        )

        if label is None:
            return

        if label.winfo_exists():

            label.destroy()

    # =====================================================
    # Active People
    # =====================================================

    def _update_people_list(
        self,
        persons: list[Any],
        zones: Any,
    ) -> None:

        current_people: dict[
            tuple[Any, Any],
            Any,
        ] = {}

        for person in persons:

            if person.track_id is None:
                continue

            key = (
                person.zone_id,
                person.track_id,
            )

            current_people[key] = person

        current_keys = tuple(
            sorted(
                current_people.keys(),
                key=lambda item: (
                    str(item[1]),
                    str(item[0]),
                ),
            )
        )

        self.current_people = current_people

        if (
            self.selected_person_key is not None
            and self.selected_person_key not in current_people
        ):
            self.selected_person_key = None

        if current_keys != self.person_signature:

            self._sync_person_rows(
                current_people,
                zones,
            )

            self.person_signature = current_keys

        for key, person in current_people.items():

            row_data = self.person_rows.get(key)

            if row_data is None:
                continue

            zone_name = self._get_zone_name(
                person.zone_id,
                zones,
            )

            row_data["id_label"].config(
                text=f"ID: {person.track_id}"
            )

            row_data["zone_label"].config(
                text=f"Zone: {zone_name}"
            )

            row_data["dwell_label"].config(
                text=(
                    f"Dwell: {self._format_duration(person.dwell_time)}"
                    if person.dwell_time is not None
                    else "Dwell: --:--"
                )
            )

        self._update_selected_person_details(zones)

    def _sync_person_rows(
        self,
        current_people: dict[
            tuple[Any, Any],
            Any,
        ],
        zones: Any,
    ) -> None:

        current_keys = set(current_people.keys())
        existing_keys = set(self.person_rows.keys())

        for key in existing_keys - current_keys:

            row_data = self.person_rows.pop(key)
            row = row_data["row"]

            if row.winfo_exists():
                row.destroy()

        if not current_keys:
            self._show_empty_people_state()
            return

        self._remove_people_empty_state()

        sorted_keys = sorted(
            current_keys,
            key=lambda item: (
                str(item[1]),
                str(item[0]),
            ),
        )

        for index, key in enumerate(sorted_keys):

            if key in self.person_rows:
                continue

            person = current_people[key]

            row = tk.Frame(
                self.people_list,
                bg="#f4f6f8",
                bd=1,
                relief="solid",
            )

            row.pack(
                fill="x",
                padx=3,
                pady=2,
            )

            indicator = tk.Frame(
                row,
                bg=self._get_zone_color(index),
                width=5,
            )

            indicator.pack(
                side="left",
                fill="y",
            )

            text_frame = tk.Frame(
                row,
                bg="#f4f6f8",
            )

            text_frame.pack(
                side="left",
                fill="x",
                expand=True,
                padx=(7, 3),
                pady=5,
            )

            id_label = tk.Label(
                text_frame,
                text=f"ID: {person.track_id}",
                font=(
                    "Segoe UI",
                    8,
                    "bold",
                ),
                fg="#18202a",
                bg="#f4f6f8",
                anchor="w",
            )

            id_label.pack(
                anchor="w",
            )

            zone_label = tk.Label(
                text_frame,
                text=(
                    f"Zone: "
                    f"{self._get_zone_name(person.zone_id, zones)}"
                ),
                font=(
                    "Segoe UI",
                    7,
                ),
                fg="#666666",
                bg="#f4f6f8",
                anchor="w",
            )

            zone_label.pack(
                anchor="w",
            )

            dwell_label = tk.Label(
                row,
                text=(
                    f"Dwell: "
                    f"{self._format_duration(person.dwell_time)}"
                    if person.dwell_time is not None
                    else "Dwell: --:--"
                ),
                font=(
                    "Segoe UI",
                    8,
                    "bold",
                ),
                fg="#00a98f",
                bg="#f4f6f8",
            )

            dwell_label.pack(
                side="right",
                padx=7,
            )

            self.person_rows[key] = {
                "row": row,
                "id_label": id_label,
                "zone_label": zone_label,
                "dwell_label": dwell_label,
            }

            for widget in (
                row,
                text_frame,
                id_label,
                zone_label,
                dwell_label,
            ):
                widget.bind(
                    "<Button-1>",
                    lambda _event, person_key=key:
                        self.select_person(person_key),
                )

        self._refresh_person_row_selection()

    def _show_empty_people_state(
        self,
    ) -> None:

        if hasattr(
            self,
            "people_empty_label",
        ):

            if self.people_empty_label.winfo_exists():
                return

        self.people_empty_label = tk.Label(
            self.people_list,
            text="No active people",
            font=(
                "Segoe UI",
                8,
            ),
            fg="#888888",
            bg="#ffffff",
        )

        self.people_empty_label.pack(
            anchor="w",
            padx=5,
            pady=4,
        )

    def _remove_people_empty_state(
        self,
    ) -> None:

        label = getattr(
            self,
            "people_empty_label",
            None,
        )

        if label is None:
            return

        if label.winfo_exists():
            label.destroy()

    # =====================================================
    # Selected Person Details
    # =====================================================

    def select_person(
        self,
        person_key: tuple[Any, Any],
    ) -> None:

        if person_key not in self.current_people:
            return

        self.selected_person_key = person_key
        self._refresh_person_row_selection()
        self._update_selected_person_details(
            self._last_zones
        )

    def _refresh_person_row_selection(self) -> None:

        for key, row_data in self.person_rows.items():

            row = row_data["row"]
            background = (
                "#e7f8f5"
                if key == self.selected_person_key
                else "#f4f6f8"
            )

            row.configure(bg=background)

            for widget in row.winfo_children():

                try:
                    widget.configure(bg=background)
                except tk.TclError:
                    pass

                for child in widget.winfo_children():

                    try:
                        child.configure(bg=background)
                    except tk.TclError:
                        pass

    def _update_selected_person_details(
        self,
        zones: Any,
    ) -> None:

        self._last_zones = zones

        for widget in self.person_details_frame.winfo_children():
            widget.destroy()

        key = self.selected_person_key

        if key is None or key not in self.current_people:

            empty = tk.Label(
                self.person_details_frame,
                text="Select an active person to view details",
                font=("Segoe UI", 8),
                fg="#888888",
                bg="#f4f6f8",
            )

            empty.pack(
                anchor="w",
                padx=8,
                pady=8,
            )

            return

        person = self.current_people[key]

        zone_name = self._get_zone_name(
            person.zone_id,
            zones,
        )

        header = tk.Frame(
            self.person_details_frame,
            bg="#f4f6f8",
        )

        header.pack(
            fill="x",
            padx=8,
            pady=(7, 3),
        )

        tk.Label(
            header,
            text=f"ID: {person.track_id}",
            font=("Segoe UI", 10, "bold"),
            fg="#18202a",
            bg="#f4f6f8",
        ).pack(side="left")

        status_text = (
            "● Inside Store"
            if person.zone_id is not None
            else "● Outside"
        )

        status_color = (
            "#16a34a"
            if person.zone_id is not None
            else "#777777"
        )

        tk.Label(
            header,
            text=status_text,
            font=("Segoe UI", 7, "bold"),
            fg=status_color,
            bg="#f4f6f8",
        ).pack(side="right")

        self._create_person_detail_row(
            "First Seen",
            self._format_person_timestamp(
                getattr(
                    person,
                    "first_seen_at",
                    None,
                )
            ),
        )

        self._create_person_detail_row(
            "Current Zone",
            zone_name,
        )

        self._create_person_detail_row(
            "Dwell Time",
            self._format_duration(
                person.dwell_time
            ),
        )

        self._create_person_detail_row(
            "Total Dwell",
            self._format_duration(
                getattr(
                    person,
                    "total_dwell",
                    None,
                )
            ),
        )

    @staticmethod
    def _format_person_timestamp(
        timestamp: Any,
    ) -> str:

        if not isinstance(
            timestamp,
            datetime,
        ):
            return "--:--:--"

        if timestamp.tzinfo is not None:
            timestamp = timestamp.astimezone()

        return timestamp.strftime(
            "%I:%M:%S %p"
        )

    def _create_person_detail_row(
        self,
        title: str,
        value: str,
    ) -> None:

        row = tk.Frame(
            self.person_details_frame,
            bg="#f4f6f8",
        )

        row.pack(
            fill="x",
            padx=8,
            pady=2,
        )

        tk.Label(
            row,
            text=title,
            font=("Segoe UI", 7),
            fg="#666666",
            bg="#f4f6f8",
        ).pack(side="left")

        tk.Label(
            row,
            text=value,
            font=("Segoe UI", 7, "bold"),
            fg="#18202a",
            bg="#f4f6f8",
        ).pack(side="right")

    # =====================================================
    # Zone Color
    # =====================================================

    @staticmethod
    def _get_zone_color(
        index: int,
    ) -> str:

        colors = (
            "#f0b429",
            "#00bcd4",
            "#a855f7",
            "#10b981",
            "#ef4444",
            "#3b82f6",
        )

        return colors[
            index % len(colors)
        ]

    # =====================================================
    # Remove Old Events
    # =====================================================

    def _remove_old_events(
        self,
        reference_time: Any,
    ) -> bool:

        if not isinstance(
            reference_time,
            datetime,
        ):

            return False

        cutoff = (
            reference_time
            - self.RECENT_EVENT_WINDOW
        )

        original_count = len(
            self.recent_events
        )

        retained_events = []

        for event in (
            self.recent_events
        ):

            event_time = (
                event["timestamp"]
            )

            if not isinstance(
                event_time,
                datetime,
            ):

                continue

            if event_time >= cutoff:

                retained_events.append(
                    event
                )

        self.recent_events = (
            retained_events
        )

        return (
            len(self.recent_events)
            != original_count
        )

    # =====================================================
    # Recent Events UI
    # =====================================================

    def _update_events_list(
        self,
    ) -> None:

        signature = tuple(
            (
                event["event_id"],
                event["track_id"],
                event["event_type"],
                event["zone_name"],
                event["timestamp"],
            )
            for event in self.recent_events[:8]
        )

        if (
            signature
            == self.events_signature
        ):

            return

        self.events_signature = (
            signature
        )

        # -------------------------------------------------
        # Rebuild only when the actual event data changes.
        # -------------------------------------------------

        for widget in (
            self.events_list.winfo_children()
        ):

            widget.destroy()

        if not self.recent_events:

            self._show_empty_events_state()

            return

        self._remove_events_empty_state()

        for event in (
            self.recent_events[:8]
        ):

            event_type = (
                event["event_type"]
            )

            track_id = (
                event["track_id"]
            )

            zone_name = (
                event["zone_name"]
            )

            timestamp = (
                event["timestamp"]
            )

            if event_type == (
                "customer_entry"
            ):

                icon = "↑"

                icon_color = "#16a34a"

                description = (
                    f"ID: {track_id}  "
                    f"Entered {zone_name}"
                )

            elif event_type == (
                "customer_exit"
            ):

                icon = "↓"

                icon_color = "#dc2626"

                description = (
                    f"ID: {track_id}  "
                    f"Exited {zone_name}"
                )

            else:

                icon = "•"

                icon_color = "#777777"

                description = (
                    f"ID: {track_id}  "
                    "Event"
                )

            row = tk.Frame(
                self.events_list,
                bg="#ffffff",
            )

            row.pack(
                fill="x",
                pady=2,
            )

            tk.Label(
                row,
                text=icon,
                font=(
                    "Segoe UI",
                    10,
                    "bold",
                ),
                fg=icon_color,
                bg="#ffffff",
                width=2,
            ).pack(
                side="left",
            )

            text_frame = tk.Frame(
                row,
                bg="#ffffff",
            )

            text_frame.pack(
                side="left",
                fill="x",
                expand=True,
            )

            tk.Label(
                text_frame,
                text=description,
                font=(
                    "Segoe UI",
                    7,
                ),
                fg="#333333",
                bg="#ffffff",
                anchor="w",
            ).pack(
                anchor="w",
            )

            tk.Label(
                text_frame,
                text=self._format_timestamp(
                    timestamp
                ),
                font=(
                    "Segoe UI",
                    6,
                ),
                fg="#999999",
                bg="#ffffff",
                anchor="w",
            ).pack(
                anchor="w",
            )

    # =====================================================
    # Empty Events State
    # =====================================================

    def _show_empty_events_state(
        self,
    ) -> None:

        if hasattr(
            self,
            "events_empty_label",
        ):

            if (
                self.events_empty_label.winfo_exists()
            ):

                return

        self.events_empty_label = tk.Label(
            self.events_list,
            text="No recent events",
            font=(
                "Segoe UI",
                8,
            ),
            fg="#888888",
            bg="#ffffff",
        )

        self.events_empty_label.pack(
            anchor="w",
            padx=5,
            pady=4,
        )

    def _remove_events_empty_state(
        self,
    ) -> None:

        label = getattr(
            self,
            "events_empty_label",
            None,
        )

        if label is None:
            return

        if label.winfo_exists():

            label.destroy()

    # =====================================================
    # Timestamp
    # =====================================================

    @staticmethod
    def _format_timestamp(
        timestamp: Any,
    ) -> str:

        if not isinstance(
            timestamp,
            datetime,
        ):

            return "--:--:--"

        # If timestamp already carries timezone information,
        # display it in the local machine timezone.
        if timestamp.tzinfo is not None:

            return timestamp.astimezone().strftime(
                "%H:%M:%S"
            )

        # Naive timestamp: use it as supplied.
        return timestamp.strftime(
            "%H:%M:%S"
        )

    # =====================================================
    # Reset
    # =====================================================

    def reset(self) -> None:

        self.total_entered = 0

        self.total_exited = 0

        self.processed_event_ids.clear()

        self.recent_events.clear()

        self.dwell_signature = ()

        self.person_signature = ()

        self.selected_person_key = None
        self.current_people.clear()

        self.events_signature = ()

        self.last_update_time = 0.0

        # -------------------------------------------------
        # Remove active-person rows
        # -------------------------------------------------

        for row_data in (
            self.person_rows.values()
        ):

            row = row_data["row"]

            if row.winfo_exists():
                row.destroy()

        self.person_rows.clear()

        self._show_empty_people_state()

        # -------------------------------------------------
        # Remove dwell rows
        # -------------------------------------------------

        for row_data in (
            self.dwell_rows.values()
        ):

            row = row_data["row"]

            if row.winfo_exists():

                row.destroy()

        self.dwell_rows.clear()

        self._show_empty_dwell_state()

        # -------------------------------------------------
        # Remove event widgets
        # -------------------------------------------------

        for widget in (
            self.events_list.winfo_children()
        ):

            widget.destroy()

        self._show_empty_events_state()

        # -------------------------------------------------
        # Reset statistics
        # -------------------------------------------------

        self.people_value.config(
            text="0"
        )

        self.entered_value.config(
            text="0"
        )

        self.exited_value.config(
            text="0"
        )

        self.zones_value.config(
            text="0"
        )

        self._update_selected_person_details([])

        self.status_label.config(
            text="Waiting for Retail OS..."
        )