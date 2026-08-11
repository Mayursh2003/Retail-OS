from __future__ import annotations

import cv2

from app.streaming.frame import Frame
from app.vision.detector import Detector
from app.vision.tracker_config import TrackerConfig
from app.vision.tracker_factory import TrackerFactory

from datetime import datetime, timezone
from uuid import uuid4


def main() -> None:
    detector = Detector(model_path="yolo11n.pt")

    capture = cv2.VideoCapture(0)

    if not capture.isOpened():
        raise RuntimeError("Unable to open webcam.")

    try:
        success, image = capture.read()

        if not success or image is None:
            raise RuntimeError("Unable to read webcam frame.")

        frame = Frame(
            camera_id=uuid4(),
            image=image,
            timestamp=datetime.now(timezone.utc),
        )

        detections = detector.detect(frame)

        print("\n==============================")
        print("Tracker Input Inspection")
        print("==============================")

        print("detections type :", type(detections))
        print("conf            :", detections.boxes.conf)
        print("cls             :", detections.boxes.cls)
        print("xywh            :", detections.boxes.xywh)

        tracker = TrackerFactory.create(TrackerConfig())
        tracker.initialize()

        print("\nCalling tracker.update()...")

        tracked = tracker.update(
            detections=detections.boxes,
            frame=image,
        )

        print("\nTracker output:")
        print(tracked)

        tracker.close()

    finally:
        capture.release()


if __name__ == "__main__":
    main()