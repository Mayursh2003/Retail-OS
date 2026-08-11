from __future__ import annotations

from datetime import datetime, timezone

import cv2

from app.streaming.exceptions import (
    FrameAcquisitionError,
    StreamConnectionError,
)
from app.streaming.frame import Frame
from app.streaming.rtsp_stream import RTSPStream


class FrameReader:
    """
    Production-ready frame acquisition component.

    This is the ONLY class in the Edge Runtime that directly interacts
    with cv2.VideoCapture.

    Responsibilities:
    - Open an RTSP stream.
    - Acquire frames.
    - Wrap frames in an immutable Frame object.
    - Release OpenCV resources safely.

    This class intentionally performs NO:
    - Image preprocessing
    - AI inference
    - Tracking
    - Threading
    - Buffer management
    """

    def __init__(self, stream: RTSPStream) -> None:
        self._stream = stream
        self._capture: cv2.VideoCapture | None = None

    def open(self) -> None:
        """
        Open the RTSP stream.

        Raises:
            StreamConnectionError:
                If the RTSP stream is not marked as connected or
                OpenCV cannot open the underlying stream.
        """
        if not self._stream.is_connected():
            raise StreamConnectionError(
                f"RTSP stream '{self._stream.camera_id}' is not connected."
            )

        capture = cv2.VideoCapture(self._stream.rtsp_url)

        if not capture.isOpened():
            capture.release()
            raise StreamConnectionError(
                f"Failed to open RTSP stream '{self._stream.camera_id}'."
            )

        self._capture = capture

    def close(self) -> None:
        """
        Release all OpenCV resources.

        This method is idempotent and safe to call multiple times.
        """
        if self._capture is not None:
            self._capture.release()
            self._capture = None

    def read_frame(self) -> Frame:
        """
        Read a single frame from the stream.

        Returns:
            Frame

        Raises:
            StreamConnectionError:
                If the capture device has not been opened.

            FrameAcquisitionError:
                If OpenCV fails to retrieve a valid frame.
        """
        if self._capture is None:
            raise StreamConnectionError(
                "FrameReader has not been opened."
            )

        try:
            success, image = self._capture.read()

            if not success or image is None:
                raise FrameAcquisitionError(
                    f"Failed to acquire frame from "
                    f"camera '{self._stream.camera_id}'."
                )

            return Frame(
                camera_id=self._stream.camera_id,
                image=image,
                timestamp=datetime.now(timezone.utc),
            )

        except Exception:
            self.close()
            raise