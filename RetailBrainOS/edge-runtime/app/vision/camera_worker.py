"""
Retail Brain OS
Camera Worker

Owns the runtime lifecycle for a single camera.

Lifecycle:

start
    ↓
FrameReader.open()
    ↓
read frame
    ↓
FrameProcessor.process()
    ↓
repeat
    ↓
camera failure
    ↓
FrameReader.close()
    ↓
FrameProcessor.reset()
    ↓
reconnect
    ↓
FrameReader.open()
    ↓
resume processing
    ↓
stop
    ↓
FrameReader.close()
"""

from __future__ import annotations

import threading
import time

from app.streaming.frame_reader import FrameReader
from app.vision.frame_processor import FrameProcessor


class CameraWorker:
    """
    Production worker responsible for one camera stream.

    A CameraWorker owns exactly one FrameReader and one
    FrameProcessor for the lifetime of the camera.
    """

    def __init__(
        self,
        frame_reader: FrameReader,
        frame_processor: FrameProcessor,
        stream: RTSPStream,
        reconnect_delay: float = 2.0,
    ) -> None:
        self._frame_reader = frame_reader
        self._stream = stream
        self._frame_processor = frame_processor
        self._reconnect_delay = reconnect_delay

        self._running = False
        self._thread: threading.Thread | None = None

        self._state_lock = threading.RLock()

    @property
    def is_running(self) -> bool:
        """Return True when the worker is running."""
        with self._state_lock:
            return self._running

    def start(self) -> None:
        """
        Start the worker thread.

        Calling start() while already running is a no-op.
        """
        with self._state_lock:
            if self._running:
                return

            self._running = True

            self._thread = threading.Thread(
                target=self._run,
                daemon=True,
                name="CameraWorker",
            )

            self._thread.start()

    def stop(self) -> None:
        """
        Stop the worker and release the camera resource.
        """
        with self._state_lock:
            self._running = False

        if self._thread is not None:
            self._thread.join(timeout=5.0)

        self._frame_reader.close()

    def _run(self) -> None:
        """
        Main camera processing loop.
        """
        try:
            while self.is_running:

                if not self._open_stream():
                    self._wait_for_reconnect()
                    continue

                try:
                    self._process_stream()

                except Exception as exc:
                    self._handle_error(exc)

                finally:
                    self._frame_reader.close()
                    self._stream.disconnect()

                if self.is_running:
                    self._reset_processor()
                    self._wait_for_reconnect()

        finally:
            self._frame_reader.close()

    def _open_stream(self) -> bool:
        """
        Connect the RTSP stream and open the frame reader.
        """
        try:
            self._stream.connect()
            self._frame_reader.open()
            return True

        except Exception as exc:
            self._handle_error(exc)
            self._frame_reader.close()
            self._stream.disconnect()
            return False

    def _process_stream(self) -> None:
        """
        Continuously acquire and process frames from the camera.
        """
        while self.is_running:
            frame = self._frame_reader.read_frame()

            if frame is None:
                continue

            result = self._frame_processor.process(frame)

            self._handle_result(result)

    def _reset_processor(self) -> None:
        """
        Reset frame/tracker state after a stream interruption.

        This prevents stale tracking state from leaking across
        camera reconnections.
        """
        self._frame_processor.reset()

    def _wait_for_reconnect(self) -> None:
        """
        Wait before attempting to reconnect.

        Uses a short sleep so the worker does not busy-loop
        when a camera is unavailable.
        """
        if self._reconnect_delay <= 0:
            return

        time.sleep(self._reconnect_delay)

    def _handle_result(self, result) -> None:
        """
        Handle a processed FrameResult.

        Backend/event integration will be added in a later milestone.
        """
        pass

    def _handle_error(self, exception: Exception) -> None:
        """
        Handle runtime errors.

        Backend reporting and structured monitoring will be added
        in later milestones.
        """
        print(f"[CameraWorker] {exception}")

    def join(self, timeout: float | None = None) -> None:
        """
        Wait for the worker thread to terminate.
        """
        if self._thread is not None:
            self._thread.join(timeout=timeout)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"running={self.is_running}, "
            f"frame_number={self._frame_processor.frame_number})"
        )