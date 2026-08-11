"""
Retail Brain OS
Live Retail Intelligence Runner

Pipeline:

    Camera
      ↓
    Frame
      ↓
    Detector
      ↓
    Tracker
      ↓
    FrameResult
      ↓
    RetailIntelligenceEngine
      ↓
    Zone + Entry/Exit + Dwell
      ↓
    Live Visualization
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import cv2
import numpy as np

from app.core.camera_config import (
    CAMERA_HEIGHT,
    CAMERA_INDEX,
    CAMERA_WIDTH,
    KEEP_ASPECT_RATIO,
    WINDOW_HEIGHT,
    WINDOW_NAME,
    WINDOW_WIDTH,
)

from app.streaming.frame import Frame

from app.vision.detector import Detector
from app.vision.frame_processor import FrameProcessor
from app.vision.tracker_config import TrackerConfig
from app.vision.tracker_factory import TrackerFactory

from app.intelligence.intelligence_engine import (
    RetailIntelligenceEngine,
)
from app.intelligence.zones.zone import Zone
from app.intelligence.zones.zone_engine import ZoneEngine


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

MODEL_PATH = "yolo11n.pt"

ZONES_PATH = (
    Path(__file__).resolve().parent
    / "zones"
    / "zones.json"
)


# ---------------------------------------------------------
# Load calibrated zones
# ---------------------------------------------------------

def load_zone_configuration() -> tuple[UUID, list[Zone]]:
    """
    Load camera ID and calibrated zones from zones.json.
    """

    if not ZONES_PATH.exists():

        raise FileNotFoundError(
            f"Zone configuration not found: "
            f"{ZONES_PATH}"
        )

    data = json.loads(
        ZONES_PATH.read_text(
            encoding="utf-8"
        )
    )

    camera_id = UUID(
        data["camera_id"]
    )

    zones: list[Zone] = []

    for item in data.get("zones", []):

        zone = Zone(
            zone_id=UUID(
                item["zone_id"]
            ),
            camera_id=UUID(
                item["camera_id"]
            ),
            name=item["name"],
            polygon=tuple(
                (
                    float(point[0]),
                    float(point[1]),
                )
                for point in item["polygon"]
            ),
        )

        zones.append(zone)

    return camera_id, zones

# ---------------------------------------------------------
# Zone name lookup
# ---------------------------------------------------------

def get_zone_name(
    zone_id,
    zones: list[Zone],
) -> str:
    """
    Convert a zone UUID into its configured human-readable name.
    """

    if zone_id is None:
        return "Outside"

    zone_id_str = str(zone_id)

    for zone in zones:
        if str(zone.zone_id) == zone_id_str:
            return zone.name

    return "Unknown"


# ---------------------------------------------------------
# Coordinate helpers
# ---------------------------------------------------------

def frame_to_display_coordinates(
    point: tuple[float, float],
    source_width: int,
    source_height: int,
) -> tuple[int, int]:
    """
    Convert original frame coordinates into the current
    display-window coordinate system.
    """

    _, _, window_width, window_height = (
        cv2.getWindowImageRect(
            WINDOW_NAME
        )
    )

    if window_width <= 0:
        window_width = source_width

    if window_height <= 0:
        window_height = source_height

    if not KEEP_ASPECT_RATIO:

        scale_x = (
            window_width / source_width
        )

        scale_y = (
            window_height / source_height
        )

        offset_x = 0
        offset_y = 0

    else:

        scale = min(
            window_width / source_width,
            window_height / source_height,
        )

        displayed_width = int(
            source_width * scale
        )

        displayed_height = int(
            source_height * scale
        )

        offset_x = (
            window_width - displayed_width
        ) // 2

        offset_y = (
            window_height - displayed_height
        ) // 2

        scale_x = scale
        scale_y = scale

    x, y = point

    return (
        int(x * scale_x + offset_x),
        int(y * scale_y + offset_y),
    )


# ---------------------------------------------------------
# Draw calibrated zones
# ---------------------------------------------------------

def draw_zones(
    image: np.ndarray,
    zones: list[Zone],
) -> None:

    for zone in zones:

        points = [
            (
                int(x),
                int(y),
            )
            for x, y in zone.polygon
        ]

        if len(points) < 3:
            continue

        points_array = np.array(
            points,
            dtype=np.int32,
        )

        cv2.polylines(
            image,
            [points_array],
            isClosed=True,
            color=(0, 255, 255),
            thickness=2,
        )

        label_x, label_y = points[0]

        cv2.putText(
            image,
            zone.name,
            (
                label_x,
                max(label_y - 10, 25),
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (0, 255, 255),
            2,
        )


# ---------------------------------------------------------
# Draw dashboard
# ---------------------------------------------------------

def draw_dashboard(
    image: np.ndarray,
    intelligence_result,
    fps: float,
    processing_ms: float,
    zones: list[Zone],
) -> None:

    height, width = image.shape[:2]

    # -----------------------------------------------------
    # Dashboard panel
    # -----------------------------------------------------

    panel_width = 310

    panel_x = max(
        width - panel_width,
        0,
    )

    overlay = image.copy()

    cv2.rectangle(
        overlay,
        (
            panel_x,
            0,
        ),
        (
            width,
            height,
        ),
        (20, 20, 20),
        -1,
    )

    # Slight transparency
    cv2.addWeighted(
        overlay,
        0.82,
        image,
        0.18,
        0,
        image,
    )

    # -----------------------------------------------------
    # Header
    # -----------------------------------------------------

    cv2.putText(
        image,
        "RETAIL BRAIN OS",
        (
            panel_x + 18,
            35,
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        (255, 255, 255),
        2,
    )

    cv2.putText(
        image,
        "LIVE INTELLIGENCE",
        (
            panel_x + 18,
            62,
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (0, 255, 255),
        2,
    )

    # -----------------------------------------------------
    # System statistics
    # -----------------------------------------------------

    current_people = len(
        intelligence_result.persons
    )

    stats = [
        f"FPS: {fps:.1f}",
        f"Processing: {processing_ms:.1f} ms",
        f"Tracked: {current_people}",
        f"Zones: {len(zones)} configured",
    ]

    y = 95

    for text in stats:

        cv2.putText(
            image,
            text,
            (
                panel_x + 18,
                y,
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.52,
            (220, 220, 220),
            1,
        )

        y += 25

    # -----------------------------------------------------
    # People
    # -----------------------------------------------------

    y += 10

    cv2.putText(
        image,
        "TRACKED PEOPLE",
        (
            panel_x + 18,
            y,
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2,
    )

    y += 28

    if not intelligence_result.persons:

        cv2.putText(
            image,
            "No people detected",
            (
                panel_x + 18,
                y,
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (170, 170, 170),
            1,
        )

        return

    # -----------------------------------------------------
    # Person details
    # -----------------------------------------------------

    for person in intelligence_result.persons:

        if y > height - 100:
            break

        track_id = person.track_id

        zone_name = get_zone_name(
            person.zone_id,
            zones,
        )

        # Dwell
        dwell_text = "N/A"

        if person.dwell_time is not None:

            dwell_seconds = (
                person.dwell_time.total_seconds()
            )

            dwell_text = (
                f"{dwell_seconds:.1f}s"
            )

        cv2.putText(
            image,
            f"ID {track_id}",
            (
                panel_x + 18,
                y,
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 255, 0),
            2,
        )

        y += 21

        cv2.putText(
            image,
            f"Zone: {zone_name}",
            (
                panel_x + 30,
                y,
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (220, 220, 220),
            1,
        )

        y += 19

        cv2.putText(
            image,
            f"Dwell: {dwell_text}",
            (
                panel_x + 30,
                y,
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (0, 255, 255),
            1,
        )

        y += 28

# ---------------------------------------------------------
# Draw zone diagnostics
# ---------------------------------------------------------

def draw_zone_diagnostics(
    image: np.ndarray,
    frame_result,
    intelligence_result,
    zones: list[Zone],
    zone_engine: ZoneEngine,
) -> None:
    """
    Temporary diagnostic overlay.

    Shows the bounding-box overlap percentage for every
    configured zone for each tracked person.
    """

    if not intelligence_result.persons:
        return

    # -----------------------------------------------------
    # Match intelligence people to their tracked person.
    # -----------------------------------------------------

    for person_index, person in enumerate(
        intelligence_result.persons
    ):

        tracked_person = next(
            (
                tracked
                for tracked in frame_result.persons
                if tracked.track_id
                == person.track_id
            ),
            None,
        )

        if tracked_person is None:
            continue

        box = tracked_person.bounding_box

        x_min = float(box.x_min)
        y_min = float(box.y_min)
        x_max = float(box.x_max)
        y_max = float(box.y_max)

        # -------------------------------------------------
        # Diagnostic panel position.
        # -------------------------------------------------

        x = 15
        y = 30 + (
            person_index * 150
        )

        cv2.putText(
            image,
            f"ZONE DEBUG - ID {person.track_id}",
            (x, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            2,
        )

        y += 25

        # -------------------------------------------------
        # Calculate overlap for EVERY zone.
        # -------------------------------------------------

        for zone in zones:

            overlap = (
                zone_engine._bbox_zone_overlap_ratio(
                    x_min=x_min,
                    y_min=y_min,
                    x_max=x_max,
                    y_max=y_max,
                    polygon=zone.polygon,
                )
            )

            cv2.putText(
                image,
                f"{zone.name}: "
                f"{overlap * 100:.1f}%",
                (x, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.48,
                (0, 255, 255),
                1,
            )

            y += 22

        # -------------------------------------------------
        # Current selected zone.
        # -------------------------------------------------

        current_zone = get_zone_name(
            person.zone_id,
            zones,
        )

        cv2.putText(
            image,
            f"Selected: {current_zone}",
            (x, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            (0, 255, 0),
            2,
        )

# ---------------------------------------------------------
# Draw tracked people
# ---------------------------------------------------------

def draw_people(
    image: np.ndarray,
    frame_result,
    intelligence_result,
    zones: list[Zone],
) -> None:

    for person in intelligence_result.persons:

        tracked_person = next(
            (
                tracked
                for tracked in frame_result.persons
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
        # Zone membership test point
        # -------------------------------------------------

        anchor_x = int(
            (box.x_min + box.x_max) / 2.0
        )

        anchor_y = int(
            (box.y_min + box.y_max) / 2.0
        )

        cv2.circle(
            image,
            (anchor_x, anchor_y),
            6,
            (0, 0, 255),
            -1,
        )

        # -------------------------------------------------
        # Bounding box
        # -------------------------------------------------

        cv2.rectangle(
            image,
            (
                x1,
                y1,
            ),
            (
                x2,
                y2,
            ),
            (0, 255, 0),
            2,
        )

        # -------------------------------------------------
        # Zone label
        # -------------------------------------------------

        zone_name = get_zone_name(
            person.zone_id,
            zones,
        )

        zone_text = (
            "OUTSIDE"
            if zone_name == "Outside"
            else zone_name.upper()
        )

        label = f"ID {person.track_id}"

        cv2.putText(
            image,
            label,
            (
                x1,
                max(
                    y1 - 10,
                    20,
                ),
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 255, 0),
            2,
        )

        # -------------------------------------------------
        # Dwell
        # -------------------------------------------------

        if person.dwell_time is not None:

            dwell_seconds = (
                person.dwell_time.total_seconds()
            )

            cv2.putText(
                image,
                f"Dwell: {dwell_seconds:.1f}s",
                (
                    x1,
                    min(
                        y2 + 22,
                        image.shape[0] - 10,
                    ),
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 255, 255),
                2,
            )

        # -------------------------------------------------
        # Entry / Exit event
        # -------------------------------------------------

        if person.entry_exit_event is not None:

            event_type = (
                person.entry_exit_event
                .event_type
                .value
            )

            cv2.putText(
                image,
                event_type.upper(),
                (
                    x1,
                    min(
                        y2 + 45,
                        image.shape[0] - 10,
                    ),
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 255, 255),
                2,
            )


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main() -> None:

    print()
    print("=" * 60)
    print("Retail Brain OS - Live Intelligence")
    print("=" * 60)
    print()

    # -----------------------------------------------------
    # Load calibrated zones
    # -----------------------------------------------------

    try:

        camera_id, zones = (
            load_zone_configuration()
        )

    except Exception as exc:

        print(
            f"ERROR: Could not load zones: {exc}"
        )

        return

    print(
        f"Camera ID : {camera_id}"
    )

    print(
        f"Zones     : {len(zones)}"
    )

    for zone in zones:

        print(
            f"  - {zone.name}"
        )

    print()

    # -----------------------------------------------------
    # Camera
    # -----------------------------------------------------

    cap = cv2.VideoCapture(
        CAMERA_INDEX
    )

    if not cap.isOpened():

        print(
            "ERROR: Could not open webcam."
        )

        return

    cap.set(
        cv2.CAP_PROP_FRAME_WIDTH,
        CAMERA_WIDTH,
    )

    cap.set(
        cv2.CAP_PROP_FRAME_HEIGHT,
        CAMERA_HEIGHT,
    )

    # -----------------------------------------------------
    # Vision pipeline
    # -----------------------------------------------------

    print("Loading detector...")

    detector = Detector(
        model_path=MODEL_PATH
    )

    print("Creating tracker...")

    tracker = TrackerFactory.create(
        TrackerConfig()
    )

    tracker.initialize()

    processor = FrameProcessor(
        detector,
        tracker,
    )

    # -----------------------------------------------------
    # Intelligence
    # -----------------------------------------------------

    zone_engine = ZoneEngine(
        zones
    )

    intelligence = (
        RetailIntelligenceEngine(
            zone_engine=zone_engine,
        )
    )

    # -----------------------------------------------------
    # Window
    # -----------------------------------------------------

    cv2.namedWindow(
        WINDOW_NAME,
        cv2.WINDOW_NORMAL
        | cv2.WINDOW_KEEPRATIO,
    )

    cv2.resizeWindow(
        WINDOW_NAME,
        WINDOW_WIDTH,
        WINDOW_HEIGHT,
    )

    print()
    print(
        "Retail Brain OS is LIVE."
    )
    print(
        "Press Q to stop."
    )
    print()

    frame_number = 0

    previous_time = time.perf_counter()

    try:

        while True:

            success, image = (
                cap.read()
            )

            if not success:

                print(
                    "ERROR: Failed to read "
                    "camera frame."
                )

                break

            frame_number += 1

            # -------------------------------------------------
            # Frame
            # -------------------------------------------------

            camera_frame = Frame(
                camera_id=camera_id,
                image=image,
                timestamp=datetime.now(
                    timezone.utc
                ),
            )

            # -------------------------------------------------
            # Vision
            # -------------------------------------------------

            processing_start = (
                time.perf_counter()
            )

            frame_result = (
                processor.process(
                    camera_frame
                )
            )

            processing_ms = (
                time.perf_counter()
                - processing_start
            ) * 1000.0

            if frame_result is None:

                cv2.imshow(
                    WINDOW_NAME,
                    image,
                )

                if (
                    cv2.waitKey(1)
                    & 0xFF
                    == ord("q")
                ):
                    break

                continue

            # -------------------------------------------------
            # Retail Intelligence
            # -------------------------------------------------

            intelligence_result = (
                intelligence.process(
                    frame_result
                )
            )

            # -------------------------------------------------
            # FPS
            # -------------------------------------------------

            current_time = (
                time.perf_counter()
            )

            elapsed = (
                current_time
                - previous_time
            )

            previous_time = current_time

            fps = (
                1.0 / elapsed
                if elapsed > 0
                else 0.0
            )

            # -------------------------------------------------
            # Draw
            # -------------------------------------------------

            draw_zones(
                image,
                zones,
            )

            draw_people(
                image,
                frame_result,
                intelligence_result,
                zones,
            )
            # -------------------------------------------------
            # Display
            # -------------------------------------------------

            cv2.imshow(
                WINDOW_NAME,
                image,
            )

            key = (
                cv2.waitKey(1)
                & 0xFF
            )

            if key in (
                ord("q"),
                ord("Q"),
            ):
                break

    finally:

        cap.release()

        cv2.destroyAllWindows()

        intelligence.reset()

    print()
    print("=" * 60)
    print("Retail Brain OS stopped")
    print("=" * 60)
    print(
        f"Frames processed: {frame_number}"
    )
    print()


if __name__ == "__main__":
    main()