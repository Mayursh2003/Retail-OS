"""
Retail Brain OS
Live Retail Intelligence Test

Webcam
    ↓
Frame
    ↓
Vision Pipeline
    ↓
FrameResult
    ↓
Retail Intelligence
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import cv2

from app.intelligence.intelligence_engine import (
    RetailIntelligenceEngine,
)
from app.intelligence.zones.zone import Zone
from app.intelligence.zones.zone_engine import ZoneEngine

from app.streaming.frame import Frame

from app.vision.detector import Detector
from app.vision.frame_processor import FrameProcessor
from app.vision.tracker_config import TrackerConfig
from app.vision.tracker_factory import TrackerFactory


MODEL_PATH = "yolo11n.pt"


def main() -> None:
    print("Starting Retail Brain OS live intelligence test...")
    print("Press Q to stop.")

    # ---------------------------------------------------------
    # Camera identity
    # ---------------------------------------------------------

    camera_id = uuid4()

    # ---------------------------------------------------------
    # Open webcam
    # ---------------------------------------------------------

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("ERROR: Could not open webcam.")
        return

    # ---------------------------------------------------------
    # Vision Pipeline
    # ---------------------------------------------------------

    detector = Detector(
        model_path=MODEL_PATH,
    )

    tracker = TrackerFactory.create(
        TrackerConfig()
    )

    tracker.initialize()

    processor = FrameProcessor(
        detector,
        tracker,
    )

    # ---------------------------------------------------------
    # Intelligence
    # ---------------------------------------------------------

    intelligence: RetailIntelligenceEngine | None = None
    zone: Zone | None = None

    frame_number = 0

    try:
        while True:

            # -------------------------------------------------
            # Read webcam frame
            # -------------------------------------------------

            success, image = cap.read()

            if not success:
                print("Failed to read webcam frame.")
                break

            frame_number += 1

            # -------------------------------------------------
            # Convert OpenCV ndarray into the project's
            # canonical Frame contract.
            # -------------------------------------------------

            camera_frame = Frame(
                camera_id=camera_id,
                image=image,
                timestamp=datetime.now(timezone.utc),
            )

            # -------------------------------------------------
            # Existing Vision Pipeline
            # -------------------------------------------------

            result = processor.process(
                camera_frame
            )

            # -------------------------------------------------
            # No detections / no FrameResult
            # -------------------------------------------------

            if result is None:

                cv2.imshow(
                    "Retail Brain OS - Live Intelligence",
                    image,
                )

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

                continue

            # -------------------------------------------------
            # Create temporary test zone once.
            # -------------------------------------------------

            if intelligence is None:

                height, width = image.shape[:2]

                margin_x = int(width * 0.15)
                margin_y = int(height * 0.15)

                zone = Zone(
                    zone_id=uuid4(),
                    camera_id=camera_id,
                    name="Store Zone",
                    polygon=(
                        (
                            float(margin_x),
                            float(margin_y),
                        ),
                        (
                            float(width - margin_x),
                            float(margin_y),
                        ),
                        (
                            float(width - margin_x),
                            float(height - margin_y),
                        ),
                        (
                            float(margin_x),
                            float(height - margin_y),
                        ),
                    ),
                )

                zone_engine = ZoneEngine(
                    [zone]
                )

                intelligence = (
                    RetailIntelligenceEngine(
                        zone_engine=zone_engine,
                    )
                )

                print()
                print("Camera ID :", camera_id)
                print(
                    "Frame Size:",
                    f"{width}x{height}",
                )
                print(
                    "Test Zone :",
                    "15% margin from frame edges",
                )
                print(
                    "Intelligence pipeline ready."
                )
                print()

            # -------------------------------------------------
            # Retail Intelligence
            # -------------------------------------------------

            intelligence_result = (
                intelligence.process(result)
            )

            # -------------------------------------------------
            # Draw configured zone
            # -------------------------------------------------

            if zone is not None:

                points = [
                    (
                        int(x),
                        int(y),
                    )
                    for x, y in zone.polygon
                ]

                for index in range(len(points)):

                    start = points[index]

                    end = points[
                        (index + 1) % len(points)
                    ]

                    cv2.line(
                        image,
                        start,
                        end,
                        (0, 255, 255),
                        2,
                    )

            # -------------------------------------------------
            # Draw intelligence information
            # -------------------------------------------------

            for person in intelligence_result.persons:

                tracked_person = next(
                    (
                        tracked
                        for tracked in result.persons
                        if tracked.track_id
                        == person.track_id
                    ),
                    None,
                )

                if tracked_person is None:
                    continue

                box = tracked_person.bounding_box

                x1 = int(box.x_min)
                y1 = int(box.y_min)
                x2 = int(box.x_max)
                y2 = int(box.y_max)

                # -------------------------------------------------
                # Bounding box
                # -------------------------------------------------

                cv2.rectangle(
                    image,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2,
                )

                # -------------------------------------------------
                # Track status
                # -------------------------------------------------

                label = (
                    f"ID {person.track_id}"
                )

                if person.zone_id is not None:
                    label += " | IN ZONE"
                else:
                    label += " | OUTSIDE"

                cv2.putText(
                    image,
                    label,
                    (
                        x1,
                        max(y1 - 10, 20),
                    ),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2,
                )

                # -------------------------------------------------
                # Dwell time
                # -------------------------------------------------

                if person.dwell_time is not None:

                    dwell_seconds = (
                        person.dwell_time
                        .total_seconds()
                    )

                    cv2.putText(
                        image,
                        f"Dwell: "
                        f"{dwell_seconds:.1f}s",
                        (
                            x1,
                            y2 + 25,
                        ),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 255),
                        2,
                    )

                # -------------------------------------------------
                # Entry / Exit event
                # -------------------------------------------------

                if (
                    person.entry_exit_event
                    is not None
                ):

                    event = (
                        person.entry_exit_event
                        .event_type
                        .value
                    )

                    print(
                        f"Track "
                        f"{person.track_id}: "
                        f"{event}"
                    )

                    cv2.putText(
                        image,
                        event.upper(),
                        (
                            x1,
                            y2 + 50,
                        ),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 255),
                        2,
                    )

            # -------------------------------------------------
            # Display
            # -------------------------------------------------

            cv2.imshow(
                "Retail Brain OS - Live Intelligence",
                image,
            )

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:

        cap.release()
        cv2.destroyAllWindows()

        if intelligence is not None:
            intelligence.reset()

        print()
        print(
            "Live intelligence test stopped."
        )
        print(
            f"Frames processed: "
            f"{frame_number}"
        )


if __name__ == "__main__":
    main()