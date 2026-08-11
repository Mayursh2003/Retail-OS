"""
Retail Brain OS
Retail Intelligence Integration Test

Validates:

FrameResult
    ↓
RetailIntelligenceEngine
    ↓
Zone detection
    ↓
Entry / Exit
    ↓
Dwell time
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.intelligence.intelligence_engine import RetailIntelligenceEngine
from app.intelligence.zones.zone import Zone
from app.intelligence.zones.zone_engine import ZoneEngine

from shared.bounding_box import BoundingBox
from shared.frame_result import FrameResult
from shared.tracked_person import TrackedPerson


def make_person(
    *,
    track_id: int,
    camera_id,
    x_min: float,
    y_min: float,
    x_max: float,
    y_max: float,
    timestamp: datetime,
) -> TrackedPerson:
    """
    Create a valid TrackedPerson using the shared contract.
    """

    return TrackedPerson(
        track_id=track_id,
        camera_id=camera_id,
        bounding_box=BoundingBox(
            x_min=x_min,
            y_min=y_min,
            x_max=x_max,
            y_max=y_max,
            width=x_max - x_min,
            height=y_max - y_min,
        ),
        confidence=0.95,
        first_seen_at=timestamp,
        last_seen_at=timestamp,
    )


def make_frame(
    *,
    camera_id,
    frame_number: int,
    timestamp: datetime,
    persons: list[TrackedPerson],
) -> FrameResult:
    """
    Create a valid FrameResult.
    """

    return FrameResult(
        frame_id=uuid4(),
        camera_id=camera_id,
        timestamp=timestamp,
        frame_number=frame_number,
        processing_time_ms=10.0,
        persons=persons,
    )


def main() -> None:
    print()
    print("==============================")
    print("Retail Intelligence Integration Test")
    print("==============================")

    camera_id = uuid4()
    zone_id = uuid4()

    # Test store zone.
    #
    # Coordinates:
    #
    # (100,100) ---------------- (500,100)
    #     |                         |
    #     |       STORE ZONE        |
    #     |                         |
    # (100,500) ---------------- (500,500)
    #
    zone = Zone(
        zone_id=zone_id,
        camera_id=camera_id,
        name="Store Zone",
        polygon=(
            (100.0, 100.0),
            (500.0, 100.0),
            (500.0, 500.0),
            (100.0, 500.0),
        ),
    )

    zone_engine = ZoneEngine([zone])

    intelligence = RetailIntelligenceEngine(
        zone_engine=zone_engine,
    )

    start = datetime(
        2026,
        8,
        9,
        10,
        0,
        0,
        tzinfo=timezone.utc,
    )

    # ---------------------------------------------------------
    # FRAME 1
    # Person is outside the store zone.
    # ---------------------------------------------------------

    frame_1 = make_frame(
        camera_id=camera_id,
        frame_number=1,
        timestamp=start,
        persons=[
            make_person(
                track_id=1,
                camera_id=camera_id,
                x_min=600.0,
                y_min=200.0,
                x_max=700.0,
                y_max=400.0,
                timestamp=start,
            )
        ],
    )

    result_1 = intelligence.process(frame_1)

    person_1 = result_1.persons[0]

    assert person_1.zone_id is None
    assert person_1.entry_exit_event is None
    assert person_1.dwell_time is None

    print("Frame 1 - Outside        : PASS")

    # ---------------------------------------------------------
    # FRAME 2
    # Person enters the store zone.
    #
    # Bottom-center:
    # ((250 + 350) / 2, 400) = (300, 400)
    #
    # This is inside the zone.
    # ---------------------------------------------------------

    frame_2_time = start + timedelta(seconds=10)

    frame_2 = make_frame(
        camera_id=camera_id,
        frame_number=2,
        timestamp=frame_2_time,
        persons=[
            make_person(
                track_id=1,
                camera_id=camera_id,
                x_min=250.0,
                y_min=200.0,
                x_max=350.0,
                y_max=400.0,
                timestamp=frame_2_time,
            )
        ],
    )

    result_2 = intelligence.process(frame_2)

    person_2 = result_2.persons[0]

    assert person_2.zone_id == zone_id
    assert person_2.entry_exit_event is not None
    assert (
        person_2.entry_exit_event.event_type.value
        == "customer_entry"
    )
    assert person_2.dwell_time == timedelta(0)

    print("Frame 2 - Entry          : PASS")

    # ---------------------------------------------------------
    # FRAME 3
    # Person remains inside for another 30 seconds.
    # ---------------------------------------------------------

    frame_3_time = start + timedelta(seconds=40)

    frame_3 = make_frame(
        camera_id=camera_id,
        frame_number=3,
        timestamp=frame_3_time,
        persons=[
            make_person(
                track_id=1,
                camera_id=camera_id,
                x_min=250.0,
                y_min=200.0,
                x_max=350.0,
                y_max=400.0,
                timestamp=frame_3_time,
            )
        ],
    )

    result_3 = intelligence.process(frame_3)

    person_3 = result_3.persons[0]

    assert person_3.zone_id == zone_id
    assert person_3.entry_exit_event is None
    assert person_3.dwell_time == timedelta(seconds=30)

    print("Frame 3 - Dwell 30s      : PASS")

    # ---------------------------------------------------------
    # FRAME 4
    # Person leaves the store zone.
    # ---------------------------------------------------------

    frame_4_time = start + timedelta(seconds=70)

    frame_4 = make_frame(
        camera_id=camera_id,
        frame_number=4,
        timestamp=frame_4_time,
        persons=[
            make_person(
                track_id=1,
                camera_id=camera_id,
                x_min=600.0,
                y_min=200.0,
                x_max=700.0,
                y_max=400.0,
                timestamp=frame_4_time,
            )
        ],
    )

    result_4 = intelligence.process(frame_4)

    person_4 = result_4.persons[0]

    assert person_4.zone_id is None
    assert person_4.entry_exit_event is not None
    assert (
        person_4.entry_exit_event.event_type.value
        == "customer_exit"
    )

    print("Frame 4 - Exit           : PASS")

    print()
    print("==============================")
    print("SUCCESS")
    print("==============================")


if __name__ == "__main__":
    main()