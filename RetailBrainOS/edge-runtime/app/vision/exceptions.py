from __future__ import annotations


class VisionError(Exception):
    """Base exception for the vision subsystem."""


class ModelLoadError(VisionError):
    """Raised when the detector model cannot be loaded."""


class InferenceError(VisionError):
    """Raised when model inference fails."""