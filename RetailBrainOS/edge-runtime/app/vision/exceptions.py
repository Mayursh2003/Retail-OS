"""
Retail Brain OS
Vision Exceptions

Defines the canonical exception hierarchy for the Vision Pipeline.

All vision-related components (detector, tracker, inference, etc.)
should raise exceptions derived from VisionError so that callers can
handle failures consistently.
"""

from __future__ import annotations


class VisionError(Exception):
    """Base exception for the Vision subsystem."""


# ---------------------------------------------------------------------
# Detector / Inference Exceptions
# ---------------------------------------------------------------------


class ModelLoadError(VisionError):
    """Raised when the detector model cannot be loaded."""


class InferenceError(VisionError):
    """Raised when detector inference fails."""


# ---------------------------------------------------------------------
# Tracker Exceptions
# ---------------------------------------------------------------------


class TrackerError(VisionError):
    """Base exception for all tracker-related failures."""


class TrackerInitializationError(TrackerError):
    """
    Raised when a tracker cannot be initialized.

    Examples:
        - Invalid configuration
        - Ultralytics initialization failure
        - Internal tracker creation error
    """


class TrackerConfigurationError(TrackerError):
    """
    Raised when an invalid or unsupported tracker configuration
    is supplied.
    """


class TrackerUpdateError(TrackerError):
    """
    Raised when tracker update() fails while processing
    a frame or detection results.
    """


class TrackerNotInitializedError(TrackerError):
    """
    Raised when tracker operations are attempted before
    initialize() has been called successfully.
    """