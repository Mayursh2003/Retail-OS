"""
Retail Brain OS
Tracker Factory

Creates tracker implementations for the Vision Pipeline.

The factory isolates the rest of the application from concrete tracker
implementations and provides a single entry point for tracker creation.
"""

from __future__ import annotations

from .exceptions import (
    TrackerConfigurationError,
    TrackerInitializationError,
)
from .tracker import Tracker
from .tracker_config import TrackerConfig
from .ultralytics_tracker import UltralyticsTracker


class TrackerFactory:
    """
    Factory responsible for creating tracker implementations.
    """

    @staticmethod
    def create(config: TrackerConfig) -> Tracker:
        """
        Create a tracker instance.

        Args:
            config:
                Tracker configuration.

        Returns:
            Tracker implementation.

        Raises:
            TrackerConfigurationError:
                Unsupported tracker type.

            TrackerInitializationError:
                Failed to create tracker.
        """

        if config.tracker_type == "bytetrack":
            try:
                return UltralyticsTracker(config)
            except Exception as exc:
                raise TrackerInitializationError(
                    "Failed to create Ultralytics tracker."
                ) from exc

        raise TrackerConfigurationError(
            f"Unsupported tracker type: {config.tracker_type}"
        )