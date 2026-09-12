"""Retail Brain OS - Saved Customer / Session Viewer."""

from __future__ import annotations

import json
import re
import tkinter as tk
from datetime import datetime
from pathlib import Path
from typing import Any

from PIL import Image, ImageTk


class SavedCustomerViewer:
    """Presentation-only viewer for saved person snapshots and face captures."""

    BG = "#eef1f4"
    WHITE = "#ffffff"
    ALT = "#f4f6f8"
    TEXT = "#18202a"
    MUTED = "#66717d"
    ACCENT = "#00a896"
    GREEN = "#16a34a"
    BORDER = "#d9dee4"

    def __init__(
        self,
        parent: tk.Misc,
        person_data_dir: str | Path,
        face_captures_dir: str | Path,
    ) -> None:
        self.person_data_dir = Path(person_data_dir)
        self.face_captures_dir = Path(face_captures_dir)

        self.window = tk.Toplevel(parent)
        self.window.title("Retail Brain OS - Saved Customer Sessions")
        self.window.geometry("1120x720")
        self.window.minsize(900, 600)
        self.window.configure(bg=self.BG)

        self._customers: list[dict[str, Any]] = []
        self._image_refs: list[ImageTk.PhotoImage] = []
        self._detail_image: ImageTk.PhotoImage | None = None

        self._build()
        self._load()

    # ---------------------------------------------------------
    # UI
    # ---------------------------------------------------------

    def _build(self) -> None:
        header = tk.Frame(self.window, bg=self.TEXT, height=82)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="SAVED CUSTOMER SESSIONS",
            font=("Segoe UI", 18, "bold"),
            fg="white",
            bg=self.TEXT,
        ).pack(anchor="w", padx=24, pady=(14, 0))

        tk.Label(
            header,
            text="Captured face + session intelligence",
            font=("Segoe UI", 9),
            fg="#b8c2cc",
            bg=self.TEXT,
        ).pack(anchor="w", padx=26, pady=(0, 10))

        self.summary = tk.Label(
            self.window,
            text="Loading...",
            font=("Segoe UI", 9, "bold"),
            fg=self.MUTED,
            bg=self.BG,
        )
        self.summary.pack(anchor="w", padx=20, pady=(14, 6))

        main = tk.Frame(self.window, bg=self.BG)
        main.pack(fill="both", expand=True, padx=20, pady=(4, 16))

        left = tk.Frame(
            main, bg=self.WHITE, bd=1, relief="solid", width=590
        )
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        left.pack_propagate(False)

        tk.Label(
            left,
            text="CUSTOMERS",
            font=("Segoe UI", 9, "bold"),
            fg=self.ACCENT,
            bg=self.WHITE,
        ).pack(anchor="w", padx=14, pady=13)

        self.canvas = tk.Canvas(
            left, bg=self.WHITE, highlightthickness=0, bd=0
        )
        scrollbar = tk.Scrollbar(left, orient="vertical", command=self.canvas.yview)
        self.cards = tk.Frame(self.canvas, bg=self.WHITE)

        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.cards, anchor="nw"
        )
        self.canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.cards.bind(
            "<Configure>",
            lambda _e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            ),
        )
        self.canvas.bind("<Configure>", self._resize_cards)

        self.detail = tk.Frame(
            main, bg=self.WHITE, bd=1, relief="solid", width=420
        )
        self.detail.pack(side="right", fill="both", padx=(10, 0))
        self.detail.pack_propagate(False)

        self._empty_detail()

    # ---------------------------------------------------------
    # Loading / joining
    # ---------------------------------------------------------

    def _load(self) -> None:
        self.person_data_dir.mkdir(parents=True, exist_ok=True)
        self.face_captures_dir.mkdir(parents=True, exist_ok=True)

        grouped: dict[int, list[tuple[Path, dict[str, Any]]]] = {}

        for path in self.person_data_dir.glob("person_*.json"):
            try:
                with path.open("r", encoding="utf-8") as f:
                    record = json.load(f)
            except (OSError, json.JSONDecodeError, TypeError):
                continue

            if not isinstance(record, dict):
                continue

            track_id = self._track_id(path, record)
            if track_id is not None:
                grouped.setdefault(track_id, []).append((path, record))

        customers = []

        for track_id, snapshots in grouped.items():
            snapshots.sort(
                key=lambda item: item[0].stat().st_mtime,
                reverse=True,
            )
            json_path, record = snapshots[0]

            faces = sorted(
                self.face_captures_dir.glob(f"person_{track_id}_*.jpg"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )

            customers.append(
                {
                    "track_id": track_id,
                    "record": record,
                    "json_path": json_path,
                    "face": faces[0] if faces else None,
                    "snapshot_count": len(snapshots),
                }
            )

        customers.sort(
            key=lambda x: str(
                x["record"].get("store_entry_time")
                or x["record"].get("first_seen")
                or ""
            ),
            reverse=True,
        )

        self._customers = customers
        self._render()

    @staticmethod
    def _track_id(path: Path, record: dict[str, Any]) -> int | None:
        try:
            return int(record.get("track_id"))
        except (TypeError, ValueError):
            match = re.search(r"person_(\d+)_", path.name)
            return int(match.group(1)) if match else None

    # ---------------------------------------------------------
    # Customer cards
    # ---------------------------------------------------------

    def _render(self) -> None:
        for child in self.cards.winfo_children():
            child.destroy()

        self._image_refs.clear()

        count = len(self._customers)
        self.summary.configure(
            text=f"{count} saved customer{'s' if count != 1 else ''}"
        )

        if not self._customers:
            tk.Label(
                self.cards,
                text="No saved customer sessions found.",
                font=("Segoe UI", 11, "bold"),
                fg=self.MUTED,
                bg=self.WHITE,
            ).pack(pady=70)
            return

        for customer in self._customers:
            self._card(customer)

    def _card(self, customer: dict[str, Any]) -> None:
        """Render one saved customer as a compact intelligence status card."""
        record = customer["record"]
        track_id = customer["track_id"]

        card = tk.Frame(
            self.cards,
            bg=self.ALT,
            bd=1,
            relief="solid",
            cursor="hand2",
        )
        card.pack(fill="x", padx=10, pady=6)

        # Face
        face_box = tk.Frame(
            card,
            width=82,
            height=82,
            bg="#e2e8f0",
        )
        face_box.pack(side="left", padx=(10, 8), pady=10)
        face_box.pack_propagate(False)

        image = self._image(customer["face"], (72, 72))

        if image:
            tk.Label(
                face_box,
                image=image,
                bg="#e2e8f0",
            ).pack(expand=True)
            self._image_refs.append(image)
        else:
            tk.Label(
                face_box,
                text="NO\nFACE",
                font=("Segoe UI", 8, "bold"),
                fg=self.MUTED,
                bg="#e2e8f0",
            ).pack(expand=True)

        # Customer identity and state
        info = tk.Frame(card, bg=self.ALT)
        info.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(2, 10),
            pady=9,
        )

        header = tk.Frame(info, bg=self.ALT)
        header.pack(fill="x")

        identity = tk.Frame(header, bg=self.ALT)
        identity.pack(side="left", fill="x", expand=True)

        tk.Label(
            identity,
            text=f"TRACK #{track_id}",
            font=("Segoe UI", 11, "bold"),
            fg=self.TEXT,
            bg=self.ALT,
        ).pack(anchor="w")

        tk.Label(
            identity,
            text="CUSTOMER SESSION",
            font=("Segoe UI", 7, "bold"),
            fg=self.MUTED,
            bg=self.ALT,
        ).pack(anchor="w", pady=(1, 0))

        status = self._status(record)

        tk.Label(
            header,
            text=f"● {status.upper()}",
            font=("Segoe UI", 8, "bold"),
            fg=self.GREEN if status == "Inside Store" else self.MUTED,
            bg=self.ALT,
        ).pack(side="right", anchor="n")

        # Compact session metrics
        metrics = tk.Frame(info, bg=self.ALT)
        metrics.pack(fill="x", pady=(8, 0))

        zone = (
            record.get("current_zone")
            or record.get("zone_name")
            or "Outside"
        )

        metric_values = (
            ("ENTRY", self._time(record.get("store_entry_time"))),
            ("EXIT", self._time(record.get("store_exit_time"))),
            (
                "DWELL",
                self._duration(
                    record.get("total_dwell_seconds", 0)
                ),
            ),
            ("LAST ZONE", str(zone)),
        )

        for index, (title, value) in enumerate(metric_values):
            metric = tk.Frame(metrics, bg="#e9edf2")
            metric.grid(
                row=0,
                column=index,
                sticky="ew",
                padx=2,
            )
            metrics.grid_columnconfigure(index, weight=1)

            tk.Label(
                metric,
                text=title,
                font=("Segoe UI", 6, "bold"),
                fg=self.MUTED,
                bg="#e9edf2",
            ).pack(anchor="w", padx=6, pady=(4, 0))

            tk.Label(
                metric,
                text=value,
                font=("Segoe UI", 7, "bold"),
                fg=self.TEXT,
                bg="#e9edf2",
            ).pack(anchor="w", padx=6, pady=(0, 4))

        # Make the complete card clickable.
        for widget in self._walk(card):
            widget.bind(
                "<Button-1>",
                lambda _e, c=customer: self._show(c),
            )

    def _label(self, parent: tk.Widget, text: str, bold: bool = False) -> None:
        tk.Label(
            parent,
            text=text,
            font=("Segoe UI", 8, "bold" if bold else "normal"),
            fg=self.TEXT if bold else self.MUTED,
            bg=self.ALT,
        ).pack(anchor="w", pady=(3, 0))

    # ---------------------------------------------------------
    # Detail view
    # ---------------------------------------------------------

    def _empty_detail(self) -> None:
        for child in self.detail.winfo_children():
            child.destroy()

        tk.Label(
            self.detail,
            text="CUSTOMER DETAILS",
            font=("Segoe UI", 9, "bold"),
            fg=self.ACCENT,
            bg=self.WHITE,
        ).pack(anchor="w", padx=18, pady=(18, 8))

        tk.Label(
            self.detail,
            text="Select a saved customer",
            font=("Segoe UI", 11, "bold"),
            fg=self.MUTED,
            bg=self.WHITE,
        ).pack(pady=90)

    def _show(self, customer: dict[str, Any]) -> None:
        for child in self.detail.winfo_children():
            child.destroy()

        record = customer["record"]
        track_id = customer["track_id"]
        status = self._status(record)

        tk.Label(
            self.detail,
            text=f"CUSTOMER #{track_id}",
            font=("Segoe UI", 15, "bold"),
            fg=self.TEXT, bg=self.WHITE,
        ).pack(anchor="w", padx=18, pady=(16, 2))

        tk.Label(
            self.detail,
            text=f"● {status}",
            font=("Segoe UI", 9, "bold"),
            fg=self.GREEN if status == "Inside Store" else self.MUTED,
            bg=self.WHITE,
        ).pack(anchor="w", padx=20, pady=(0, 10))

        face_box = tk.Frame(
            self.detail, width=190, height=190,
            bg="#e2e8f0", bd=1, relief="solid"
        )
        face_box.pack(pady=(2, 12))
        face_box.pack_propagate(False)

        self._detail_image = self._image(customer["face"], (175, 175))
        if self._detail_image:
            tk.Label(
                face_box, image=self._detail_image, bg="#e2e8f0"
            ).pack(expand=True)
        else:
            tk.Label(
                face_box, text="NO CAPTURED FACE",
                font=("Segoe UI", 9, "bold"),
                fg=self.MUTED, bg="#e2e8f0"
            ).pack(expand=True)

        details = tk.Frame(self.detail, bg=self.WHITE)
        details.pack(fill="x", padx=20)

        fields = (
            ("First Seen", self._time(record.get("first_seen"))),
            ("Store Entry", self._time(record.get("store_entry_time"))),
            ("Store Exit", self._time(record.get("store_exit_time"))),
            ("Current Zone", record.get("current_zone") or record.get("zone_name") or "Outside"),
            ("Current Dwell", self._duration(record.get("current_dwell_seconds", 0))),
            ("Total Dwell", self._duration(record.get("total_dwell_seconds", 0))),
        )

        for title, value in fields:
            r = tk.Frame(details, bg=self.ALT)
            r.pack(fill="x", pady=2)
            tk.Label(
                r, text=title, font=("Segoe UI", 8),
                fg=self.MUTED, bg=self.ALT
            ).pack(side="left", padx=8, pady=6)
            tk.Label(
                r, text=str(value), font=("Segoe UI", 8, "bold"),
                fg=self.TEXT, bg=self.ALT
            ).pack(side="right", padx=8, pady=6)

        self._zone_activity(details, record)
        self._journey(details, record)

    def _zone_activity(self, parent: tk.Frame, record: dict[str, Any]) -> None:
        tk.Label(
            parent, text="ZONE ACTIVITY",
            font=("Segoe UI", 8, "bold"),
            fg=self.ACCENT, bg=self.WHITE
        ).pack(anchor="w", pady=(12, 4))

        totals = record.get("zone_dwell_seconds") or {}
        if not isinstance(totals, dict) or not totals:
            tk.Label(
                parent, text="No zone dwell recorded.",
                font=("Segoe UI", 8),
                fg=self.MUTED, bg=self.WHITE
            ).pack(anchor="w")
            return

        for zone, seconds in totals.items():
            r = tk.Frame(parent, bg=self.ALT)
            r.pack(fill="x", pady=1)
            tk.Label(
                r, text=str(zone), font=("Segoe UI", 8),
                fg=self.MUTED, bg=self.ALT
            ).pack(side="left", padx=8, pady=5)
            tk.Label(
                r, text=self._duration(seconds),
                font=("Segoe UI", 8, "bold"),
                fg=self.TEXT, bg=self.ALT
            ).pack(side="right", padx=8, pady=5)

    def _journey(self, parent: tk.Frame, record: dict[str, Any]) -> None:
        tk.Label(
            parent, text="JOURNEY",
            font=("Segoe UI", 8, "bold"),
            fg=self.ACCENT, bg=self.WHITE
        ).pack(anchor="w", pady=(12, 4))

        visits = record.get("zone_visits") or []
        names = []

        if isinstance(visits, list):
            for visit in visits:
                if isinstance(visit, dict):
                    names.append(
                        str(visit.get("zone_name") or visit.get("zone") or "Unknown")
                    )

        journey = "  →  ".join(names) if names else "No zone journey recorded."
        tk.Label(
            parent,
            text=f"Entry  →  {journey}  →  Exit",
            font=("Segoe UI", 8),
            fg=self.TEXT, bg=self.WHITE,
            wraplength=365, justify="left"
        ).pack(anchor="w")

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    @staticmethod
    def _status(record: dict[str, Any]) -> str:
        value = str(record.get("status") or "").lower()
        if value in {"exited", "exit", "outside"}:
            return "Exited"
        if record.get("store_exit_time") is not None:
            return "Exited"
        return "Inside Store"

    @staticmethod
    def _time(value: Any) -> str:
        if value in (None, "", "None"):
            return "--"
        text = str(value)
        try:
            return datetime.fromisoformat(text).strftime("%d-%m-%Y %H:%M:%S")
        except (ValueError, TypeError):
            return text.replace("T", " ")[:19]

    @staticmethod
    def _duration(value: Any) -> str:
        try:
            total = max(0, int(float(value)))
        except (TypeError, ValueError):
            total = 0

        h, rem = divmod(total, 3600)
        m, s = divmod(rem, 60)
        if h:
            return f"{h}h {m}m {s}s"
        if m:
            return f"{m}m {s}s"
        return f"{s}s"

    @staticmethod
    def _image(path: Path | None, size: tuple[int, int]):
        if path is None or not path.exists():
            return None
        try:
            image = Image.open(path).convert("RGB")
            image.thumbnail(size, Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(image)
        except (OSError, ValueError):
            return None

    @staticmethod
    def _walk(widget: tk.Widget):
        yield widget
        for child in widget.winfo_children():
            yield from SavedCustomerViewer._walk(child)

    def _resize_cards(self, event: tk.Event) -> None:
        self.canvas.itemconfigure(self.canvas_window, width=event.width)
