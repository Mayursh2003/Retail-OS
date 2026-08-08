"""
Retail Brain OS
Ultralytics ByteTrack Adapter

Concrete tracker implementation backed by Ultralytics BYTETracker.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import numpy as np

from ultralytics.trackers.byte_tracker import BYTETracker

from .exceptions import (
    TrackerInitializationError,
    TrackerNotInitializedError,
    TrackerUpdateError,
)
from .tracker import Tracker
from .tracker_config import TrackerConfig


class UltralyticsTracker(Tracker):
    """
    Adapter around Ultralytics BYTETracker.

    One instance should be used for one camera stream.
    """

    DEFAULT_FRAME_RATE = 30

    def __init__(self, config: TrackerConfig):
        self._config = config
        self._tracker: BYTETracker | None = None
        self._initialized = False

    @property
    def initialized(self) -> bool:
        """Return True if the tracker has been initialized."""
        return self._initialized

    def initialize(self) -> None:
        """
        Create the underlying BYTETracker instance.
        """
        if self._initialized:
            return

        try:
            args = SimpleNamespace(
                track_high_thresh=self._config.track_high_thresh,
                track_low_thresh=self._config.track_low_thresh,
                new_track_thresh=self._config.new_track_thresh,
                track_buffer=self._config.track_buffer,
                match_thresh=self._config.match_thresh,
                fuse_score=self._config.fuse_score,
            )

            self._tracker = BYTETracker(
                args=args,
                frame_rate=self.DEFAULT_FRAME_RATE,
            )

            self._initialized = True

        except Exception as exc:
            raise TrackerInitializationError(
                "Failed to initialize Ultralytics BYTETracker."
            ) from exc

    def update(
        self,
        detections: Any,
        frame: Any,
    ) -> Any:
        """
        Update tracker state using detector results.

        Ultralytics 8.3.0 BYTETracker performs NumPy operations
        internally. The detector returns PyTorch-backed Boxes,
        so this adapter explicitly converts the tracker inputs
        to NumPy arrays before calling BYTETracker.

        Parameters
        ----------
        detections:
            Ultralytics Boxes-like object exposing:
                conf
                cls
                xywh

        frame:
            Original OpenCV frame.
        """
        if not self._initialized or self._tracker is None:
            raise TrackerNotInitializedError(
                "Tracker has not been initialized."
            )

        if detections is None:
            return np.empty((0, 7), dtype=np.float32)

        required_attributes = ("conf", "cls", "xywh")

        for attribute in required_attributes:
            if not hasattr(detections, attribute):
                raise TrackerUpdateError(
                    f"Detections object is missing required "
                    f"attribute '{attribute}'."
                )

        try:
            conf = detections.conf.detach().cpu().numpy()
            cls = detections.cls.detach().cpu().numpy()
            xywh = detections.xywh.detach().cpu().numpy()

            conf = np.asarray(conf, dtype=np.float32).reshape(-1)
            cls = np.asarray(cls, dtype=np.float32).reshape(-1)
            xywh = np.asarray(xywh, dtype=np.float32).reshape(-1, 4)

            if not (
                len(conf) == len(cls) == len(xywh)
            ):
                raise TrackerUpdateError(
                    "Detection arrays have inconsistent lengths: "
                    f"conf={len(conf)}, "
                    f"cls={len(cls)}, "
                    f"xywh={len(xywh)}."
                )

            if len(xywh) == 0:
                return np.empty((0, 8), dtype=np.float32)

            tracker_input = SimpleNamespace(
                conf=conf,
                cls=cls,
                xywh=xywh,
            )

            return self._tracker.update(
                tracker_input,
                img=frame,
            )

        except TrackerUpdateError:
            raise

    def reset(self) -> None:
        """
        Reset the internal tracker state.
        """
        if not self._initialized or self._tracker is None:
            return

        try:
            self._tracker.reset()

        except Exception as exc:
            raise TrackerUpdateError(
                "Failed to reset tracker."
            ) from exc

    def close(self) -> None:
        """
        Release tracker resources.

        BYTETracker does not expose an explicit close() API, so
        releasing the internal reference is sufficient.
        Safe to call multiple times.
        """
        self._tracker = None
        self._initialized = False

    def __enter__(self) -> "UltralyticsTracker":
        """
        Context manager entry.
        """
        self.initialize()
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        """
        Context manager exit.
        """
        self.close()

    def __repr__(self) -> str:
        """
        Developer-friendly representation.
        """
        state = "initialized" if self._initialized else "not_initialized"

        return (
            f"{self.__class__.__name__}("
            f"tracker_type='{self._config.tracker_type}', "
            f"state='{state}')"
        )