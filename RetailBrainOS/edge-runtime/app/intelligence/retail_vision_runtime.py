"""
Retail Brain OS
Vision Runtime

Owns the live camera + vision + intelligence pipeline.

This module does NOT create a GUI or OpenCV display window.
It exposes the latest processed frame and intelligence result
for consumers such as the Retail Brain OS GUI.
"""

from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import UUID

import cv2
import numpy as np

from app.core.camera_config import (
    CAMERA_HEIGHT,
    CAMERA_INDEX,
    CAMERA_WIDTH,
)

from app.streaming.frame import Frame

from app.vision.detector import Detector
from app.vision.frame_processor import FrameProcessor
from app.vision.tracker_config import TrackerConfig
from app.vision.tracker_factory import TrackerFactory

from app.intelligence.intelligence_engine import (
    RetailIntelligenceEngine,
)

from app.intelligence.zones.zone import Zone
from app.intelligence.zones.zone_engine import ZoneEngine


MODEL_PATH = "yolo11n.pt"

ZONES_PATH = (
    Path(__file__).resolve().parent
    / "zones"
    / "zones.json"
)


@dataclass
class VisionRuntimeState:
    """
    Snapshot of the current Retail Vision state.
    """

    frame: Optional[np.ndarray] = None
    frame_result: object | None = None
    intelligence_result: object | None = None

    fps: float = 0.0
    processing_ms: float = 0.0

    frame_number: int = 0

    camera_id: UUID | None = None
    zones: tuple[Zone, ...] = ()

    running: bool = False
    error: str | None = None


class RetailVisionRuntime:
    """
    Owns the complete live vision pipeline.

    Camera
        ↓
    Frame
        ↓
    Detector
        ↓
    Tracker
        ↓
    FrameResult
        ↓
    RetailIntelligenceEngine
    """

    def __init__(
        self,
        model_path: str = MODEL_PATH,
    ) -> None:

        self.model_path = model_path

        self._capture = None

        self._detector = None
        self._tracker = None
        self._processor = None

        self._zone_engine = None
        self._intelligence = None

        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

        self._lock = threading.Lock()

        self._state = VisionRuntimeState()

    def load_zone_configuration(
        self,
    ) -> tuple[UUID, list[Zone]]:

        if not ZONES_PATH.exists():

            raise FileNotFoundError(
                f"Zone configuration not found: "
                f"{ZONES_PATH}"
            )

        data = json.loads(
            ZONES_PATH.read_text(
                encoding="utf-8"
            )
        )

        camera_id = UUID(
            data["camera_id"]
        )

        zones: list[Zone] = []

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

            zones.append(zone)

        return camera_id, zones

    def start(self) -> None:

        if self.is_running():

            return

        camera_id, zones = (
            self.load_zone_configuration()
        )

        capture = cv2.VideoCapture(
            CAMERA_INDEX
        )

        if not capture.isOpened():

            capture.release()

            raise RuntimeError(
                "Could not open webcam."
            )

        capture.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            CAMERA_WIDTH,
        )

        capture.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            CAMERA_HEIGHT,
        )

        detector = Detector(
            model_path=self.model_path
        )

        tracker = TrackerFactory.create(
            TrackerConfig()
        )

        tracker.initialize()

        processor = FrameProcessor(
            detector,
            tracker,
        )

        zone_engine = ZoneEngine(
            zones
        )

        intelligence = (
            RetailIntelligenceEngine(
                zone_engine=zone_engine,
            )
        )

        self._capture = capture

        self._detector = detector
        self._tracker = tracker
        self._processor = processor

        self._zone_engine = zone_engine
        self._intelligence = intelligence

        self._stop_event.clear()

        with self._lock:

            self._state = VisionRuntimeState(
                camera_id=camera_id,
                zones=tuple(zones),
                running=True,
            )

        self._thread = threading.Thread(
            target=self._run,
            name="retail-vision-runtime",
            daemon=True,
        )

        self._thread.start()

    def _run(self) -> None:

        previous_time = time.perf_counter()

        try:

            while not self._stop_event.is_set():

                success, image = (
                    self._capture.read()
                )

                if not success:

                    with self._lock:

                        self._state.error = (
                            "Failed to read camera frame."
                        )

                    break

                frame_number = (
                    self._state.frame_number + 1
                )

                camera_id = self._state.camera_id

                if camera_id is None:

                    raise RuntimeError(
                        "Camera ID is not loaded."
                    )

                camera_frame = Frame(
                    camera_id=camera_id,
                    image=image,
                    timestamp=datetime.now(
                        timezone.utc
                    ),
                )

                processing_start = (
                    time.perf_counter()
                )

                frame_result = (
                    self._processor.process(
                        camera_frame
                    )
                )

                processing_ms = (
                    time.perf_counter()
                    - processing_start
                ) * 1000.0

                if frame_result is None:

                    continue

                intelligence_result = (
                    self._intelligence.process(
                        frame_result
                    )
                )

                current_time = (
                    time.perf_counter()
                )

                elapsed = (
                    current_time
                    - previous_time
                )

                previous_time = current_time

                fps = (
                    1.0 / elapsed
                    if elapsed > 0
                    else 0.0
                )

                with self._lock:

                    self._state.frame = image.copy()

                    self._state.frame_result = (
                        frame_result
                    )

                    self._state.intelligence_result = (
                        intelligence_result
                    )

                    self._state.fps = fps

                    self._state.processing_ms = (
                        processing_ms
                    )

                    self._state.frame_number = (
                        frame_number
                    )

                    self._state.error = None

        except Exception as exc:

            with self._lock:

                self._state.error = str(exc)

        finally:

            with self._lock:

                self._state.running = False

    def get_state(self) -> VisionRuntimeState:

        with self._lock:

            return VisionRuntimeState(
                frame=(
                    self._state.frame.copy()
                    if self._state.frame is not None
                    else None
                ),

                frame_result=(
                    self._state.frame_result
                ),

                intelligence_result=(
                    self._state.intelligence_result
                ),
                fps=self._state.fps,
                processing_ms=(
                    self._state.processing_ms
                ),
                frame_number=(
                    self._state.frame_number
                ),
                camera_id=self._state.camera_id,
                zones=self._state.zones,
                running=self._state.running,
                error=self._state.error,
            )

    def is_running(self) -> bool:

        with self._lock:

            return self._state.running

    def stop(self) -> None:

        self._stop_event.set()

        if self._thread is not None:

            self._thread.join(
                timeout=3.0
            )

        if self._capture is not None:

            self._capture.release()

        self._capture = None
        self._thread = None

        if self._intelligence is not None:

            self._intelligence.reset()

        with self._lock:

            self._state.running = False

    def get_error(self) -> str | None:

        with self._lock:

            return self._state.error