"""
Retail Brain OS
Live Laptop Camera Vision Test

Pipeline:

Laptop Webcam
    ↓
Frame
    ↓
Detector
    ↓
Tracker
    ↓
TrackerMapper
    ↓
FrameResult
    ↓
OpenCV Display
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from uuid import uuid4

import cv2
import numpy as np

from app.streaming.frame import Frame
from app.vision.detector import Detector
from app.vision.frame_processor import FrameProcessor
from app.vision.tracker_config import TrackerConfig
from app.vision.tracker_factory import TrackerFactory


MODEL_PATH = "yolo11n.pt"
CAMERA_INDEX = 0


def main() -> None:
    print("Starting Retail Brain OS live camera test...")

    detector = Detector(model_path=MODEL_PATH)

    tracker = TrackerFactory.create(
        TrackerConfig()
    )

    tracker.initialize()

    processor = FrameProcessor(
        detector=detector,
        tracker=tracker,
    )

    capture = cv2.VideoCapture(CAMERA_INDEX)

    if not capture.isOpened():
        raise RuntimeError(
            f"Unable to open laptop camera index {CAMERA_INDEX}."
        )

    previous_time = time.perf_counter()

    print("Camera opened successfully.")
    print("Press Q to stop.")

    try:
        while True:
            success, image = capture.read()

            if not success or image is None:
                print("Failed to read camera frame.")
                break

            frame = Frame(
                camera_id=uuid4(),
                image=image,
                timestamp=datetime.now(timezone.utc),
            )

            result = processor.process(frame)

            current_time = time.perf_counter()

            elapsed = current_time - previous_time
            previous_time = current_time

            fps = 1.0 / elapsed if elapsed > 0 else 0.0

            display = image.copy()

            for person in result.persons:
                box = person.bounding_box

                x1 = int(box.x_min)
                y1 = int(box.y_min)
                x2 = int(box.x_max)
                y2 = int(box.y_max)

                cv2.rectangle(
                    display,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2,
                )

                label = (
                    f"ID {person.track_id} "
                    f"{person.confidence:.2f}"
                )

                cv2.putText(
                    display,
                    label,
                    (x1, max(y1 - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2,
                )

            cv2.putText(
                display,
                f"FPS: {fps:.1f}",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
            )

            cv2.putText(
                display,
                f"People: {len(result.persons)}",
                (20, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
            )

            cv2.imshow(
                "Retail Brain OS - Live Vision",
                display,
            )

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

    finally:
        capture.release()
        cv2.destroyAllWindows()
        tracker.close()

        print("\nLive camera test stopped.")
        print(f"Frames processed: {processor.frame_number}")


if __name__ == "__main__":
    main()