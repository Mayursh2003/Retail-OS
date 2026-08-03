"""
End-to-end runtime test for UltralyticsTracker.

This test verifies:

1. YOLO model loads.
2. Inference runs.
3. Detections are passed to BYTETracker.
4. Tracking executes successfully.
"""

from ultralytics import YOLO

from app.vision.tracker_config import TrackerConfig
from app.vision.ultralytics_tracker import UltralyticsTracker


def main():
    model = YOLO("yolo11n.pt")

    results = model(
        "https://ultralytics.com/images/bus.jpg",
        verbose=False,
    )

    boxes = results[0].boxes
    frame = results[0].orig_img

    tracker = UltralyticsTracker(TrackerConfig())

    tracker.initialize()

    tracked = tracker.update(
        detections=boxes,
        frame=frame,
    )

    print("\nTracker Output")
    print("-" * 60)
    print(tracked)

    print("\nShape:", tracked.shape)
    print("Dtype:", tracked.dtype)

    tracker.close()

    print("\nSUCCESS")


if __name__ == "__main__":
    main()