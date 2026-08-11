"""
Retail Brain OS
Vision Tracker Interface

This module defines the abstract tracking interface used by the
Vision Pipeline.

Concrete implementations (e.g. Ultralytics ByteTrack) must implement
this contract while keeping third-party dependencies isolated from
the rest of the application.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Tracker(ABC):
    """
    Abstract interface for all tracker implementations.

    Each tracker instance is expected to manage the tracking lifecycle
    for exactly one camera stream.
    """

    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize tracker resources.

        Raises:
            TrackerInitializationError:
                If the tracker cannot be initialized.
        """
        raise NotImplementedError

    @abstractmethod
    def update(self, detections: Any, frame: Any) -> Any:
        """
        Update tracker state using the latest detections.

        Args:
            detections:
                Detector output for the current frame.

            frame:
                Original frame associated with the detections.

        Returns:
            Tracking results for the current frame.

        Raises:
            TrackerUpdateError:
                If tracking fails.
        """
        raise NotImplementedError

    @abstractmethod
    def reset(self) -> None:
        """
        Reset tracker state.

        Implementations should recreate internal tracker state
        rather than attempting to mutate undocumented internal
        objects.
        """
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        """
        Release tracker resources.

        Safe to call multiple times.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def initialized(self) -> bool:
        """
        Returns:
            True if the tracker has been successfully initialized.
        """
        raise NotImplementedError