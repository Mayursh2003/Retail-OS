"""
Retail Brain OS
Ultralytics ByteTrack Adapter

Concrete tracker implementation backed by Ultralytics BYTETracker.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

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

        Parameters
        ----------
        detections:
            Ultralytics Boxes-like object exposing:

                conf
                cls
                xywh (or xywhr)

        frame:
            Original OpenCV frame.
        """
        if not self._initialized or self._tracker is None:
            raise TrackerNotInitializedError(
                "Tracker has not been initialized."
            )

        if detections is None:
            return []

        required_attributes = ("conf", "cls")

        for attribute in required_attributes:
            if not hasattr(detections, attribute):
                raise TrackerUpdateError(
                    f"Detections object is missing required attribute '{attribute}'."
                )

        if not (
            hasattr(detections, "xywh")
            or hasattr(detections, "xywhr")
        ):
            raise TrackerUpdateError(
                "Detections object must expose either 'xywh' or 'xywhr'."
            )

        try:
            return self._tracker.update(
                detections,
                img=frame,
            )

        except Exception as exc:
            raise TrackerUpdateError(
                "Ultralytics tracker update failed."
            ) from exc

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