"""
Retail Brain OS
CameraWorker Lifecycle Test
"""

from __future__ import annotations

import time
from uuid import uuid4

from app.vision.camera_worker import CameraWorker
from app.streaming.rtsp_stream import RTSPStream


class FakeFrameReader:
    def __init__(self) -> None:
        self.open_count = 0
        self.close_count = 0
        self.read_count = 0
        self.is_open = False

    def open(self) -> None:
        self.open_count += 1
        self.is_open = True

    def close(self) -> None:
        self.close_count += 1
        self.is_open = False

    def read_frame(self):
        if not self.is_open:
            raise RuntimeError("Reader is not open")

        self.read_count += 1

        # Keep the test loop alive without requiring real frames.
        time.sleep(0.01)

        return object()


class FakeFrameProcessor:
    def __init__(self) -> None:
        self.frame_number = 0
        self.process_count = 0
        self.reset_count = 0

    def process(self, frame):
        self.process_count += 1
        self.frame_number += 1
        return {
            "frame_number": self.frame_number,
            "camera_id": uuid4(),
        }

    def reset(self) -> None:
        self.reset_count += 1
        self.frame_number = 0


def main() -> None:
    reader = FakeFrameReader()
    processor = FakeFrameProcessor()

    camera_id = uuid4()

    stream = RTSPStream(
        camera_id=camera_id,
        rtsp_url="rtsp://test-camera/stream",
    )

    worker = CameraWorker(
        frame_reader=reader,
        frame_processor=processor,
        stream=stream,
        reconnect_delay=0.05,
    )

    print("\n==============================")
    print("CameraWorker Lifecycle Test")
    print("==============================")

    # Start
    worker.start()

    time.sleep(0.15)

    assert worker.is_running is True
    assert reader.open_count >= 1
    assert processor.process_count > 0

    print("Worker start              : PASS")
    print("Stream open               : PASS")
    print("Frame processing          : PASS")

    # Stop
    worker.stop()

    assert worker.is_running is False
    assert reader.close_count >= 1

    print("Worker stop               : PASS")
    print("Stream close              : PASS")

    # Verify thread termination
    worker.join(timeout=1.0)

    assert worker._thread is None or not worker._thread.is_alive()

    print("Thread termination        : PASS")

    print("\n==============================")
    print("SUCCESS")
    print("==============================")


if __name__ == "__main__":
    main()