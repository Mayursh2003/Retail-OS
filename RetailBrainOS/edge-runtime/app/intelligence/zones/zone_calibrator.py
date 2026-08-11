"""
Retail Brain OS
Zone Calibrator / Zone Editor

Persistent zone configuration workflow:

    Run calibrator
          ↓
    Load existing zones.json
          ↓
    Edit current zones
      ├── Add zone
      ├── Delete zone
      └── Reset all zones
          ↓
    Save zones.json
          ↓
    live_retail_os.py automatically loads
    the latest configuration.

The saved polygon coordinates always use the ORIGINAL
camera-frame coordinate system, regardless of the
OpenCV window size.
"""

from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID, uuid4

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

from app.intelligence.zones.zone import Zone


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

OUTPUT_PATH = (
    Path(__file__).resolve().parent / "zones.json"
)


# ---------------------------------------------------------
# Calibration state
# ---------------------------------------------------------

camera_id: UUID = uuid4()

frozen = False
frame: np.ndarray | None = None

current_points: list[tuple[float, float]] = []

zones: list[Zone] = []


# ---------------------------------------------------------
# Configuration loading
# ---------------------------------------------------------

def load_existing_configuration() -> None:
    """
    Load the existing camera ID and zones from zones.json.

    If zones.json does not exist, a new camera identity is
    created and calibration starts with zero zones.
    """

    global camera_id
    global zones

    if not OUTPUT_PATH.exists():

        print(
            "No existing zones.json found."
        )

        print(
            "Starting a new zone configuration."
        )

        print(
            f"New camera ID: {camera_id}"
        )

        return

    try:

        data = json.loads(
            OUTPUT_PATH.read_text(
                encoding="utf-8"
            )
        )

        # -------------------------------------------------
        # Preserve camera identity
        # -------------------------------------------------

        existing_camera_id = data.get(
            "camera_id"
        )

        if existing_camera_id:

            camera_id = UUID(
                existing_camera_id
            )

        # -------------------------------------------------
        # Load zones
        # -------------------------------------------------

        loaded_zones: list[Zone] = []

        for item in data.get(
            "zones",
            [],
        ):

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

            loaded_zones.append(zone)

        zones = loaded_zones

        print()
        print("=" * 60)
        print("Existing zone configuration loaded")
        print("=" * 60)

        print(
            f"Camera ID : {camera_id}"
        )

        print(
            f"Zones     : {len(zones)}"
        )

        if zones:

            for index, zone in enumerate(
                zones,
                start=1,
            ):

                print(
                    f"  {index}. {zone.name}"
                )

        else:

            print(
                "  No zones configured."
            )

        print()

    except Exception as exc:

        print()
        print(
            "WARNING: Could not load existing "
            f"zones.json: {exc}"
        )

        print(
            "Starting with a new configuration."
        )

        print()


# ---------------------------------------------------------
# Zone serialization
# ---------------------------------------------------------

def zone_to_dict(
    zone: Zone,
) -> dict:

    return {
        "zone_id": str(
            zone.zone_id
        ),
        "camera_id": str(
            zone.camera_id
        ),
        "name": zone.name,
        "polygon": [
            [
                float(x),
                float(y),
            ]
            for x, y in zone.polygon
        ],
    }


def save_configuration() -> None:
    """
    Save the complete current zone configuration.

    The JSON file represents the current truth.
    """

    configuration = {
        "camera_id": str(
            camera_id
        ),
        "zones": [
            zone_to_dict(zone)
            for zone in zones
        ],
    }

    OUTPUT_PATH.write_text(
        json.dumps(
            configuration,
            indent=4,
        ),
        encoding="utf-8",
    )

    print()
    print("-" * 60)
    print("Configuration saved")
    print("-" * 60)
    print(
        f"File      : {OUTPUT_PATH}"
    )
    print(
        f"Camera ID : {camera_id}"
    )
    print(
        f"Zones     : {len(zones)}"
    )
    print()


# ---------------------------------------------------------
# Display coordinate mapping
# ---------------------------------------------------------

def get_display_scale(
    source_width: int,
    source_height: int,
) -> tuple[
    float,
    float,
    int,
    int,
]:

    try:
        _, _, window_width, window_height = (
            cv2.getWindowImageRect(WINDOW_NAME)
    )
    except cv2.error:
        window_width = WINDOW_WIDTH
        window_height = WINDOW_HEIGHT

    if (
        window_width <= 0
        or window_height <= 0
    ):

        return (
            1.0,
            1.0,
            0,
            0,
        )

    if not KEEP_ASPECT_RATIO:

        scale_x = (
            window_width / source_width
        )

        scale_y = (
            window_height / source_height
        )

        return (
            scale_x,
            scale_y,
            0,
            0,
        )

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

    return (
        scale,
        scale,
        offset_x,
        offset_y,
    )


def display_to_frame_coordinates(
    x: int,
    y: int,
    source_width: int,
    source_height: int,
) -> tuple[float, float] | None:

    (
        scale_x,
        scale_y,
        offset_x,
        offset_y,
    ) = get_display_scale(
        source_width,
        source_height,
    )

    if (
        scale_x <= 0
        or scale_y <= 0
    ):

        return None

    frame_x = (
        x - offset_x
    ) / scale_x

    frame_y = (
        y - offset_y
    ) / scale_y

    if (
        frame_x < 0
        or frame_x >= source_width
        or frame_y < 0
        or frame_y >= source_height
    ):

        return None

    return (
        float(frame_x),
        float(frame_y),
    )


def frame_to_display_coordinates(
    point: tuple[float, float],
    source_width: int,
    source_height: int,
) -> tuple[int, int]:

    (
        scale_x,
        scale_y,
        offset_x,
        offset_y,
    ) = get_display_scale(
        source_width,
        source_height,
    )

    x, y = point

    display_x = int(
        x * scale_x + offset_x
    )

    display_y = int(
        y * scale_y + offset_y
    )

    return (
        display_x,
        display_y,
    )


# ---------------------------------------------------------
# Mouse callback
# ---------------------------------------------------------

def mouse_callback(
    event: int,
    x: int,
    y: int,
    flags: int,
    param,
) -> None:

    if not frozen:
        return

    if frame is None:
        return

    if event != cv2.EVENT_LBUTTONDOWN:
        return

    source_height, source_width = (
        frame.shape[:2]
    )

    point = display_to_frame_coordinates(
        x,
        y,
        source_width,
        source_height,
    )

    if point is None:
        return

    current_points.append(point)


# ---------------------------------------------------------
# Zone management
# ---------------------------------------------------------

def print_zone_list() -> None:
    """
    Print the current zones with selectable numbers.
    """

    print()
    print("=" * 60)
    print("CURRENT ZONES")
    print("=" * 60)

    if not zones:

        print(
            "No zones configured."
        )

    else:

        for index, zone in enumerate(
            zones,
            start=1,
        ):

            print(
                f"{index}. {zone.name}"
            )

    print()


def delete_zone() -> None:
    """
    Delete one selected zone.
    """

    global zones

    if not zones:

        print(
            "There are no zones to delete."
        )

        return

    print_zone_list()

    try:

        value = input(
            "Enter zone number to delete "
            "(0 = cancel): "
        ).strip()

        if not value:

            print(
                "Delete cancelled."
            )

            return

        index = int(value)

    except ValueError:

        print(
            "Invalid zone number."
        )

        return

    if index == 0:

        print(
            "Delete cancelled."
        )

        return

    if (
        index < 1
        or index > len(zones)
    ):

        print(
            "Zone number is out of range."
        )

        return

    deleted_zone = zones.pop(
        index - 1
    )

    print()
    print(
        f"Deleted zone: "
        f"{deleted_zone.name}"
    )

    print(
        f"Remaining zones: "
        f"{len(zones)}"
    )

    # Immediately persist the new configuration.
    save_configuration()


def reset_all_zones() -> None:
    """
    Delete all configured zones after confirmation.
    """

    global zones

    if not zones:

        print(
            "There are no zones to reset."
        )

        return

    print()
    print("WARNING!")
    print(
        "This will DELETE ALL existing zones."
    )

    print(
        f"Current zones: {len(zones)}"
    )

    confirmation = input(
        "Type YES to confirm: "
    ).strip()

    if confirmation != "YES":

        print(
            "Reset cancelled."
        )

        return

    zones.clear()

    print()
    print(
        "All zones deleted."
    )

    # Persist empty zone configuration.
    save_configuration()


# ---------------------------------------------------------
# Drawing
# ---------------------------------------------------------

def draw_interface(
    image: np.ndarray,
) -> np.ndarray:

    display = image.copy()

    source_height, source_width = (
        image.shape[:2]
    )

    # -----------------------------------------------------
    # Existing zones
    # -----------------------------------------------------

    for index, zone in enumerate(
        zones,
        start=1,
    ):

        points = [
            (
                int(x),
                int(y),
            )
            for x, y in zone.polygon
        ]

        points_array = np.array(
            points,
            dtype=np.int32,
        )

        if len(points) >= 3:

            cv2.polylines(
                display,
                [points_array],
                isClosed=True,
                color=(0, 255, 0),
                thickness=2,
            )

        # ---------------------------------------------
        # Zone number
        # ---------------------------------------------

        if points:

            label_x, label_y = points[0]

            label = (
                f"{index}. {zone.name}"
            )

            cv2.putText(
                display,
                label,
                (
                    label_x,
                    max(
                        label_y - 10,
                        25,
                    ),
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 0),
                2,
            )

    # -----------------------------------------------------
    # Current polygon
    # -----------------------------------------------------

    display_points = [
        (
            int(x),
            int(y),
        )
        for x, y in current_points
    ]

    for point in display_points:

        cv2.circle(
            display,
            point,
            5,
            (0, 255, 255),
            -1,
        )

    for index in range(
        len(display_points) - 1
    ):

        cv2.line(
            display,
            display_points[index],
            display_points[
                index + 1
            ],
            (0, 255, 255),
            2,
        )

    # -----------------------------------------------------
    # Header
    # -----------------------------------------------------

    cv2.rectangle(
        display,
        (0, 0),
        (
            display.shape[1],
            48,
        ),
        (25, 25, 25),
        -1,
    )

    status = (
        "FROZEN - DRAW ZONE"
        if frozen
        else "LIVE CAMERA"
    )

    cv2.putText(
        display,
        f"RETAIL BRAIN OS | {status}",
        (15, 32),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        (255, 255, 255),
        2,
    )

    # -----------------------------------------------------
    # Resolution
    # -----------------------------------------------------

    resolution_text = (
        f"{source_width}x{source_height}"
    )

    cv2.putText(
        display,
        resolution_text,
        (
            display.shape[1] - 150,
            32,
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2,
    )

    # -----------------------------------------------------
    # Zone count
    # -----------------------------------------------------

    zone_count_text = (
        f"Zones: {len(zones)}"
    )

    cv2.putText(
        display,
        zone_count_text,
        (
            display.shape[1] - 150,
            70,
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 255, 255),
        1,
    )

    # -----------------------------------------------------
    # Footer
    # -----------------------------------------------------

    cv2.rectangle(
        display,
        (
            0,
            display.shape[0] - 38,
        ),
        (
            display.shape[1],
            display.shape[0],
        ),
        (25, 25, 25),
        -1,
    )

    instructions = (
        "SPACE: Freeze | "
        "ENTER: Add | "
        "D: Delete | "
        "R: Reset | "
        "S: Save | "
        "Q: Quit"
    )

    cv2.putText(
        display,
        instructions,
        (
            10,
            display.shape[0] - 12,
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        1,
    )

    return display


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main() -> None:

    global frozen
    global frame
    global current_points

    print()
    print("=" * 60)
    print("Retail Brain OS - Zone Calibrator / Editor")
    print("=" * 60)
    print()

    # -----------------------------------------------------
    # Load existing configuration
    # -----------------------------------------------------

    load_existing_configuration()

    print(
        f"Camera index        : {CAMERA_INDEX}"
    )

    print(
        f"Preferred resolution: "
        f"{CAMERA_WIDTH}x{CAMERA_HEIGHT}"
    )

    print(
        f"Initial window size : "
        f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}"
    )

    print()
    print("CONTROLS")
    print("-" * 60)
    print(
        "SPACE  - Freeze / Resume camera"
    )
    print(
        "ENTER  - Finish and add current zone"
    )
    print(
        "D      - Delete an existing zone"
    )
    print(
        "R      - Delete ALL zones"
    )
    print(
        "C      - Clear current polygon"
    )
    print(
        "S      - Save configuration"
    )
    print(
        "Q      - Save and quit"
    )
    print()

    cap = cv2.VideoCapture(
        CAMERA_INDEX
    )

    if not cap.isOpened():

        print(
            "ERROR: Could not open webcam."
        )

        return

    # -----------------------------------------------------
    # Request preferred capture resolution
    # -----------------------------------------------------

    cap.set(
        cv2.CAP_PROP_FRAME_WIDTH,
        CAMERA_WIDTH,
    )

    cap.set(
        cv2.CAP_PROP_FRAME_HEIGHT,
        CAMERA_HEIGHT,
    )

    # -----------------------------------------------------
    # Create resizable window
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

    cv2.setMouseCallback(
        WINDOW_NAME,
        mouse_callback,
    )

    try:

        while True:

            # -------------------------------------------------
            # Capture while live
            # -------------------------------------------------

            if not frozen:

                success, captured = (
                    cap.read()
                )

                if not success:

                    print(
                        "ERROR: Failed to read "
                        "webcam frame."
                    )

                    break

                frame = captured

            if frame is None:
                continue

            # -------------------------------------------------
            # Draw interface
            # -------------------------------------------------

            display = draw_interface(
                frame
            )

            cv2.imshow(
                WINDOW_NAME,
                display,
            )

            key = (
                cv2.waitKey(1)
                & 0xFF
            )

            # -------------------------------------------------
            # SPACE
            # -------------------------------------------------

            if key == ord(" "):

                frozen = not frozen

                if frozen:

                    print()
                    print(
                        "Frame frozen."
                    )

                    print(
                        "Draw a new zone."
                    )

                else:

                    current_points.clear()

                    print(
                        "Camera resumed."
                    )

            # -------------------------------------------------
            # C - Clear current polygon
            # -------------------------------------------------

            elif key in (
                ord("c"),
                ord("C"),
            ):

                current_points.clear()

                print(
                    "Current polygon cleared."
                )

            # -------------------------------------------------
            # ENTER - Add zone
            # -------------------------------------------------

            elif key in (
                13,
                10,
            ):

                if not frozen:

                    print(
                        "Freeze the frame first."
                    )

                    continue

                if len(current_points) < 3:

                    print(
                        "A zone requires at least "
                        "3 points."
                    )

                    continue

                print()
                print(
                    f"Polygon contains "
                    f"{len(current_points)} points."
                )

                name = input(
                    "Enter new zone name: "
                ).strip()

                if not name:

                    print(
                        "Zone name cannot be empty."
                    )

                    continue

                zone = Zone(
                    zone_id=uuid4(),
                    camera_id=camera_id,
                    name=name,
                    polygon=tuple(
                        current_points
                    ),
                )

                zones.append(
                    zone
                )

                current_points.clear()

                print()
                print(
                    f"Created zone: {zone.name}"
                )

                print(
                    f"Total zones: {len(zones)}"
                )

                # ---------------------------------------------
                # Automatically persist after adding.
                # ---------------------------------------------

                save_configuration()

            # -------------------------------------------------
            # D - Delete zone
            # -------------------------------------------------

            elif key in (
                ord("d"),
                ord("D"),
            ):

                delete_zone()

            # -------------------------------------------------
            # R - Reset all zones
            # -------------------------------------------------

            elif key in (
                ord("r"),
                ord("R"),
            ):

                reset_all_zones()

            # -------------------------------------------------
            # S - Save
            # -------------------------------------------------

            elif key in (
                ord("s"),
                ord("S"),
            ):

                save_configuration()

            # -------------------------------------------------
            # Q - Save and quit
            # -------------------------------------------------

            elif key in (
                ord("q"),
                ord("Q"),
            ):

                save_configuration()

                break

    finally:

        cap.release()

        cv2.destroyAllWindows()

    print()
    print("=" * 60)
    print("Zone calibration finished")
    print("=" * 60)

    print(
        f"Camera ID : {camera_id}"
    )

    print(
        f"Zones     : {len(zones)}"
    )

    print(
        f"Configuration: {OUTPUT_PATH}"
    )

    print()


if __name__ == "__main__":
    main()