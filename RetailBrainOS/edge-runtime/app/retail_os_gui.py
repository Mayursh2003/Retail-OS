"""
Retail Brain OS
Main Desktop GUI

Phase B-3.2
GUI <-> RetailVisionRuntime integration.
"""

from __future__ import annotations

import threading
import tkinter as tk

import cv2
from PIL import Image, ImageTk

from app.gui.live_overlay import (
    render_live_frame,
)

from app.gui.zone_setup_gui import (
    ZoneSetupWindow,
)

from app.intelligence.retail_vision_runtime import (
    RetailVisionRuntime,
)

from app.gui.live_dashboard import (
    LiveDashboard,
)


class RetailBrainOSApp:
    """
    Main Retail Brain OS desktop application.

    The GUI owns presentation and user controls.

    RetailVisionRuntime owns:
        Camera
        Detector
        Tracker
        Zone Engine
        Intelligence Engine
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
        # Header
        # -------------------------------------------------

        header = tk.Frame(
            self.root,
            bg="#18202a",
            height=80,
        )

        header.pack(
            fill="x"
        )

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
            pady=(15, 0),
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
            pady=(0, 10),
        )

        # -------------------------------------------------
        # Main body
        # -------------------------------------------------

        body = tk.Frame(
            self.root,
            bg="#eef1f4",
        )

        body.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=20,
        )

        # -------------------------------------------------
        # Camera panel
        # -------------------------------------------------

        camera_panel = tk.Frame(
            body,
            bg="#111111",
            bd=1,
            relief="solid",
        )

        camera_panel.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, 10),
        )

        tk.Label(
            camera_panel,
            text="LIVE CAMERA",
            font=(
                "Segoe UI",
                12,
                "bold",
            ),
            fg="#00d9c6",
            bg="#111111",
        ).pack(
            anchor="w",
            padx=15,
            pady=(12, 5),
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

        self.camera_label.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10,
        )

        # -------------------------------------------------
        # Right status panel
        # -------------------------------------------------

        status_panel = tk.Frame(
            body,
            width=300,
            bg="#ffffff",
            bd=1,
            relief="solid",
        )

        status_panel.pack(
            side="right",
            fill="y",
        )

        status_panel.pack_propagate(
            False
        )

        tk.Label(
            status_panel,
            text="LIVE STATUS",
            font=(
                "Segoe UI",
                14,
                "bold",
            ),
            fg="#00bfae",
            bg="#ffffff",
        ).pack(
            anchor="w",
            padx=18,
            pady=(18, 15),
        )

        # -------------------------------------------------
        # Runtime status
        # -------------------------------------------------

        self.runtime_status_label = self.create_status_card(
            status_panel,
            "SYSTEM STATUS",
            "STOPPED",
        )

        self.fps_label = self.create_status_card(
            status_panel,
            "FPS",
            "0.0",
        )

        self.processing_label = self.create_status_card(
            status_panel,
            "PROCESSING",
            "0.0 ms",
        )

        self.frame_label = self.create_status_card(
            status_panel,
            "FRAME",
            "0",
        )

        self.zone_label = self.create_status_card(
            status_panel,
            "ACTIVE ZONES",
            "0",
        )

        self.error_label = self.create_status_card(
            status_panel,
            "ERROR",
            "None",
        )

        self.live_dashboard = LiveDashboard(
            status_panel
        )

        # -------------------------------------------------
        # Control panel
        # -------------------------------------------------

        controls = tk.Frame(
            self.root,
            bg="#18202a",
            height=90,
        )

        controls.pack(
            fill="x",
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
                11,
                "bold",
            ),
            width=18,
            height=2,
            relief="flat",
        )

        self.setup_button.pack(
            side="left",
            padx=(20, 8),
            pady=18,
        )

        # -------------------------------------------------
        # Start
        # -------------------------------------------------

        self.start_button = tk.Button(
            controls,
            text="START RETAIL OS",
            command=self.start_retail_os,
            font=(
                "Segoe UI",
                11,
                "bold",
            ),
            width=20,
            height=2,
            relief="flat",
        )

        self.start_button.pack(
            side="left",
            padx=8,
            pady=18,
        )

        # -------------------------------------------------
        # Stop
        # -------------------------------------------------

        self.stop_button = tk.Button(
            controls,
            text="STOP RETAIL OS",
            command=self.stop_retail_os,
            font=(
                "Segoe UI",
                11,
                "bold",
            ),
            width=20,
            height=2,
            relief="flat",
            state="disabled",
        )

        self.stop_button.pack(
            side="left",
            padx=8,
            pady=18,
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
                11,
                "bold",
            ),
            width=12,
            height=2,
            relief="flat",
        )

        self.close_button.pack(
            side="right",
            padx=20,
            pady=18,
        )

        # -------------------------------------------------
        # Footer
        # -------------------------------------------------

        self.status_label = tk.Label(
            self.root,
            text="System ready",
            font=(
                "Segoe UI",
                9,
            ),
            bg="#eef1f4",
            fg="#555555",
        )

        self.status_label.pack(
            pady=6,
        )

    # =====================================================
    # Status cards
    # =====================================================

    def create_status_card(
        self,
        parent: tk.Widget,
        title: str,
        value: str,
    ) -> tk.Label:

        frame = tk.Frame(
            parent,
            bg="#f4f6f8",
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
            fg="#777777",
            bg="#f4f6f8",
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
            fg="#18202a",
            bg="#f4f6f8",
        )

        label.pack(
            anchor="w",
            padx=10,
            pady=(0, 7),
        )

        return label

    # =====================================================
    # Zone setup
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

        self.status_label.config(
            text=(
                "Zone setup closed. "
                "Configuration saved."
            )
        )

    # =====================================================
    # Runtime start
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

    # =====================================================
    # Runtime polling
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

        if state.frame is not None:

            rendered_frame = state.frame

            if (
                state.frame_result is not None
                and state.intelligence_result is not None
            ):

                rendered_frame = render_live_frame(
                    frame=state.frame,
                    frame_result=state.frame_result,
                    intelligence_result=state.intelligence_result,
                    zones=state.zones,
                )

            self.display_camera_frame(
                rendered_frame
            )

            if state.intelligence_result is not None:

                self.live_dashboard.update(
                intelligence_result=(
                    state.intelligence_result
                ),
                zones=state.zones,
            )

        if state.running:

            self.stop_button.config(
                state="normal"
            )

            self.status_label.config(
                text="Retail OS is running."
            )

            self.root.after(
                30,
                self.poll_runtime,
            )

        else:

            self.stop_button.config(
                state="disabled"
            )

            self.start_button.config(
                state="normal"
            )

            self.setup_button.config(
                state="normal"
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
    # Camera display
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
    # Runtime stop
    # =====================================================

    def stop_retail_os(self) -> None:

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

        self.status_label.config(
            text="Retail OS stopped."
        )

        self.camera_label.config(
            image="",
            text="Camera stopped",
        )

        self.camera_photo = None

    # =====================================================
    # Application close
    # =====================================================

    def close_application(self) -> None:

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