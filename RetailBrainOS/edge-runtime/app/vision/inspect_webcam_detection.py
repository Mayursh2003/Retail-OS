from __future__ import annotations

import cv2

from app.streaming.frame import Frame
from app.vision.detector import Detector

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

        result = detector.detect(frame)

        print("\n==============================")
        print("Detector Output Inspection")
        print("==============================")

        print("Result type :", type(result))
        print("Boxes type  :", type(result.boxes))

        print("conf shape  :", result.boxes.conf.shape)
        print("cls shape   :", result.boxes.cls.shape)
        print("xywh shape  :", result.boxes.xywh.shape)

        print("conf        :", result.boxes.conf)
        print("cls         :", result.boxes.cls)
        print("xywh        :", result.boxes.xywh)

        print("==============================")

    finally:
        capture.release()


if __name__ == "__main__":
    main()