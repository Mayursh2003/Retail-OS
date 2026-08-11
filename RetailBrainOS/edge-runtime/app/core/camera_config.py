"""
Retail Brain OS
Shared Camera Display Configuration

This module defines the common camera/display behavior used by
the zone calibrator and live Retail Brain OS runner.
"""

from __future__ import annotations

CAMERA_INDEX = 0

# Preferred capture resolution.
# The camera may not support this exact resolution. The actual
# frame returned by OpenCV remains the authoritative coordinate
# system.
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

# Initial OpenCV window size.
# This affects only the desktop window, not the saved coordinates.
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480

WINDOW_NAME = "Retail Brain OS"

# Keep the camera frame aspect ratio when resizing the window.
KEEP_ASPECT_RATIO = True