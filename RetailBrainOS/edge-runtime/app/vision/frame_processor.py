"""
Retail Brain OS
Frame Processor

Coordinates the complete Vision Pipeline.

Pipeline:

Frame
    ↓
Detector
    ↓
Tracker
    ↓
TrackerMapper
    ↓
FrameResult
"""

from __future__ import annotations

import time

from app.streaming.frame import Frame
from app.vision.detector import Detector
from app.vision.tracker import Tracker
from app.vision.tracker_mapper import TrackerMapper

from shared import FrameResult


class FrameProcessor:
    """
    Production Vision Pipeline orchestrator.
    """

    def __init__(
        self,
        detector: Detector,
        tracker: Tracker,
    ) -> None:
        self._detector = detector
        self._tracker = tracker
        self._frame_number = 0

    @property
    def frame_number(self) -> int:
        return self._frame_number

    def process(
        self,
        frame: Frame,
    ) -> FrameResult:

        start = time.perf_counter()

        self._frame_number += 1

        detections = self._detector.detect(frame)

        tracked_objects = self._tracker.update(
            detections=detections.boxes,
            frame=frame.image,
        )

        processing_time_ms = (time.perf_counter() - start) * 1000.0

        return TrackerMapper.map(
            tracked_objects=tracked_objects,
            camera_id=frame.camera_id,
            timestamp=frame.timestamp,
            frame_number=self._frame_number,
            processing_time_ms=processing_time_ms,
        )

    def reset(self) -> None:
        self._frame_number = 0
        self._tracker.reset()

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"frame_number={self._frame_number})"
        )