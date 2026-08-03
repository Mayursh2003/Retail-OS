"""
Retail Brain OS
End-to-End Frame Processor Test
"""

from ultralytics import YOLO

from app.streaming.frame import Frame
from app.vision.detector import Detector
from app.vision.frame_processor import FrameProcessor
from app.vision.tracker_config import TrackerConfig
from app.vision.tracker_factory import TrackerFactory

import cv2
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def main():

    model_path = "yolo11n.pt"

    image_path = "bus.jpg"

    if not Path(image_path).exists():
        model = YOLO(model_path)
        model.predict(
            source="https://ultralytics.com/images/bus.jpg",
            save=False,
            verbose=False,
        )

    image = cv2.imread(image_path)

    frame = Frame(
        camera_id=uuid4(),
        image=image,
        timestamp=datetime.now(timezone.utc),
    )

    detector = Detector(model_path=model_path)

    tracker = TrackerFactory.create(
        TrackerConfig()
    )

    tracker.initialize()

    processor = FrameProcessor(
        detector=detector,
        tracker=tracker,
    )

    result = processor.process(frame)

    print("\n==============================")
    print("Frame Processor Test")
    print("==============================")

    print(result)

    print("\nPeople Detected :", len(result.persons))
    print("Frame Number    :", result.frame_number)
    print("Processing Time :", result.processing_time_ms)

    print("\nSUCCESS")


if __name__ == "__main__":
    main()