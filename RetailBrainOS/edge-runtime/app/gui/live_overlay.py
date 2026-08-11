"""
Retail Brain OS
Live Camera Overlay Renderer

Responsible only for rendering:
    - configured zones
    - tracked people
    - track IDs
    - zone names
    - dwell time
    - entry/exit event labels

It does NOT:
    - run detection
    - run tracking
    - calculate zones
    - calculate dwell
    - own the camera
"""

from __future__ import annotations

from typing import Any

import cv2
import numpy as np

from app.intelligence.zones.zone import Zone


# =========================================================
# Zone lookup
# =========================================================

def get_zone_name(
    zone_id: Any,
    zones: tuple[Zone, ...] | list[Zone],
) -> str:
    """
    Resolve a zone UUID to its configured human-readable name.
    """

    if zone_id is None:
        return "Outside"

    for zone in zones:

        if zone.zone_id == zone_id:
            return zone.name

    return "Unknown"


# =========================================================
# Zone colors
# =========================================================

ZONE_COLORS = [
    (0, 215, 255),
    (255, 190, 0),
    (180, 80, 255),
    (0, 180, 120),
    (255, 100, 100),
    (100, 220, 100),
]


def get_zone_color(
    index: int,
) -> tuple[int, int, int]:

    return ZONE_COLORS[
        index % len(ZONE_COLORS)
    ]


# =========================================================
# Draw zones
# =========================================================

def draw_zones(
    image: np.ndarray,
    zones: tuple[Zone, ...] | list[Zone],
) -> None:
    """
    Draw configured polygon zones on the camera frame.

    Coordinates are already in the original camera-frame
    coordinate system, so no GUI/window coordinate conversion
    is required here.
    """

    for index, zone in enumerate(zones):

        if len(zone.polygon) < 3:
            continue

        color = get_zone_color(index)

        points = np.array(
            [
                (
                    int(x),
                    int(y),
                )
                for x, y in zone.polygon
            ],
            dtype=np.int32,
        )

        # -------------------------------------------------
        # Transparent zone fill
        # -------------------------------------------------

        overlay = image.copy()

        cv2.fillPoly(
            overlay,
            [points],
            color,
        )

        cv2.addWeighted(
            overlay,
            0.12,
            image,
            0.88,
            0,
            image,
        )

        # -------------------------------------------------
        # Zone boundary
        # -------------------------------------------------

        cv2.polylines(
            image,
            [points],
            isClosed=True,
            color=color,
            thickness=2,
        )

        # -------------------------------------------------
        # Zone label
        # -------------------------------------------------

        label_x = int(
            points[0][0]
        )

        label_y = int(
            points[0][1]
        )

        label_y = max(
            label_y - 8,
            25,
        )

        text_size = cv2.getTextSize(
            zone.name,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            2,
        )[0]

        cv2.rectangle(
            image,
            (
                label_x - 5,
                label_y - text_size[1] - 8,
            ),
            (
                label_x + text_size[0] + 5,
                label_y + 5,
            ),
            color,
            -1,
        )

        cv2.putText(
            image,
            zone.name,
            (
                label_x,
                label_y,
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (20, 20, 20),
            2,
        )


# =========================================================
# Draw person
# =========================================================

def draw_person(
    image: np.ndarray,
    tracked_person: Any,
    intelligence_person: Any,
    zones: tuple[Zone, ...] | list[Zone],
) -> None:
    """
    Draw one tracked person.

    The bounding box comes from the canonical FrameResult.
    Zone/dwell/event information comes from the intelligence
    result.
    """

    box = tracked_person.bounding_box

    x1 = max(
        0,
        int(box.x_min),
    )

    y1 = max(
        0,
        int(box.y_min),
    )

    x2 = min(
        image.shape[1] - 1,
        int(box.x_max),
    )

    y2 = min(
        image.shape[0] - 1,
        int(box.y_max),
    )

    # -----------------------------------------------------
    # Person bounding box
    # -----------------------------------------------------

    person_color = (
        0,
        255,
        0,
    )

    cv2.rectangle(
        image,
        (x1, y1),
        (x2, y2),
        person_color,
        2,
    )

    # -----------------------------------------------------
    # ID label
    # -----------------------------------------------------

    track_id = intelligence_person.track_id

    zone_name = get_zone_name(
        intelligence_person.zone_id,
        zones,
    )

    label = f"ID: {track_id}"

    label_size = cv2.getTextSize(
        label,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        2,
    )[0]

    label_top = max(
        y1 - label_size[1] - 12,
        0,
    )

    cv2.rectangle(
        image,
        (
            x1,
            label_top,
        ),
        (
            x1 + label_size[0] + 10,
            y1,
        ),
        person_color,
        -1,
    )

    cv2.putText(
        image,
        label,
        (
            x1 + 5,
            y1 - 6,
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (10, 10, 10),
        2,
    )

    # -----------------------------------------------------
    # Zone / dwell information
    # -----------------------------------------------------

    info_y = min(
        y2 + 20,
        image.shape[0] - 10,
    )

    zone_text = f"Zone: {zone_name}"

    cv2.putText(
        image,
        zone_text,
        (
            x1,
            info_y,
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.48,
        (255, 255, 255),
        1,
    )

    # -----------------------------------------------------
    # Dwell
    # -----------------------------------------------------

    if intelligence_person.dwell_time is not None:

        dwell_seconds = (
            intelligence_person
            .dwell_time
            .total_seconds()
        )

        dwell_text = (
            f"Dwell: {dwell_seconds:.1f}s"
        )

        cv2.putText(
            image,
            dwell_text,
            (
                x1,
                min(
                    info_y + 18,
                    image.shape[0] - 10,
                ),
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            (0, 255, 255),
            1,
        )

    # -----------------------------------------------------
    # Entry / exit event
    # -----------------------------------------------------

    event = (
        intelligence_person.entry_exit_event
    )

    if event is not None:

        event_text = (
            event.event_type.value.upper()
        )

        cv2.putText(
            image,
            event_text,
            (
                x1,
                min(
                    info_y + 36,
                    image.shape[0] - 10,
                ),
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (0, 255, 0),
            1,
        )


# =========================================================
# Draw all people
# =========================================================

def draw_people(
    image: np.ndarray,
    frame_result: Any,
    intelligence_result: Any,
    zones: tuple[Zone, ...] | list[Zone],
) -> None:
    """
    Match intelligence people to their corresponding
    tracked FrameResult people using track_id.
    """

    if intelligence_result is None:
        return

    for intelligence_person in (
        intelligence_result.persons
    ):

        tracked_person = next(
            (
                tracked
                for tracked in frame_result.persons
                if (
                    tracked.track_id
                    == intelligence_person.track_id
                )
            ),
            None,
        )

        if tracked_person is None:
            continue

        draw_person(
            image=image,
            tracked_person=tracked_person,
            intelligence_person=intelligence_person,
            zones=zones,
        )


# =========================================================
# Main renderer
# =========================================================

def render_live_frame(
    frame: np.ndarray,
    frame_result: Any,
    intelligence_result: Any,
    zones: tuple[Zone, ...] | list[Zone],
) -> np.ndarray:
    """
    Produce a GUI-ready frame with only camera intelligence
    overlays.

    No dashboard panel is drawn.
    """

    output = frame.copy()

    draw_zones(
        output,
        zones,
    )

    draw_people(
        output,
        frame_result,
        intelligence_result,
        zones,
    )

    return output