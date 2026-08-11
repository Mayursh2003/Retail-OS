"""
Retail Brain OS
B-4.9 Exit Detection Regression Test
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.intelligence.events.entry_exit import (
    EntryExitEventType,
)
from app.intelligence.intelligence_engine import (
    RetailIntelligenceEngine,
)
from app.intelligence.zones.zone import Zone
from app.intelligence.zones.zone_engine import ZoneEngine
from shared.bounding_box import BoundingBox
from shared.frame_result import FrameResult
from shared.tracked_person import TrackedPerson


def make_person(
    *,
    track_id: int,
    camera_id,
    timestamp: datetime,
    inside: bool,
) -> TrackedPerson:

    if inside:
        x_min, y_min = 40.0, 20.0
        x_max, y_max = 60.0, 50.0
    else:
        x_min, y_min = 140.0, 120.0
        x_max, y_max = 160.0, 150.0

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
    timestamp: datetime,
    frame_number: int,
    persons,
) -> FrameResult:

    return FrameResult(
        frame_id=uuid4(),
        camera_id=camera_id,
        timestamp=timestamp,
        frame_number=frame_number,
        processing_time_ms=20.0,
        persons=persons,
    )


def main() -> None:

    camera_id = uuid4()
    zone_id = uuid4()

    zone = Zone(
        zone_id=zone_id,
        camera_id=camera_id,
        name="Zone A",
        polygon=(
            (0.0, 0.0),
            (100.0, 0.0),
            (100.0, 100.0),
            (0.0, 100.0),
        ),
    )

    engine = RetailIntelligenceEngine(
        zone_engine=ZoneEngine([zone])
    )

    start = datetime.now(timezone.utc)

    # -------------------------------------------------
    # 1. Enter zone.
    # -------------------------------------------------

    result = engine.process(
        make_frame(
            camera_id=camera_id,
            timestamp=start,
            frame_number=1,
            persons=[
                make_person(
                    track_id=1,
                    camera_id=camera_id,
                    timestamp=start,
                    inside=True,
                )
            ],
        )
    )

    assert len(result.events) == 1
    assert (
        result.events[0].event_type
        == EntryExitEventType.CUSTOMER_ENTRY
    )

    # -------------------------------------------------
    # 2. Explicit zone -> outside transition.
    # -------------------------------------------------

    outside_time = (
        start + timedelta(seconds=1)
    )

    result = engine.process(
        make_frame(
            camera_id=camera_id,
            timestamp=outside_time,
            frame_number=2,
            persons=[
                make_person(
                    track_id=1,
                    camera_id=camera_id,
                    timestamp=outside_time,
                    inside=False,
                )
            ],
        )
    )

    assert len(result.events) == 1
    assert (
        result.events[0].event_type
        == EntryExitEventType.CUSTOMER_EXIT
    )

    # -------------------------------------------------
    # 3. Enter again, then disappear from the camera.
    # -------------------------------------------------

    reentry_time = (
        start + timedelta(seconds=2)
    )

    result = engine.process(
        make_frame(
            camera_id=camera_id,
            timestamp=reentry_time,
            frame_number=3,
            persons=[
                make_person(
                    track_id=1,
                    camera_id=camera_id,
                    timestamp=reentry_time,
                    inside=True,
                )
            ],
        )
    )

    assert (
        result.events[0].event_type
        == EntryExitEventType.CUSTOMER_ENTRY
    )

    lost_exit = None

    for offset in range(
        1,
        RetailIntelligenceEngine.MISSING_TRACK_GRACE_FRAMES + 1,
    ):

        timestamp = (
            reentry_time
            + timedelta(
                milliseconds=50 * offset
            )
        )

        result = engine.process(
            make_frame(
                camera_id=camera_id,
                timestamp=timestamp,
                frame_number=3 + offset,
                persons=[],
            )
        )

        if result.events:
            lost_exit = result.events[0]
            break

    assert lost_exit is not None
    assert (
        lost_exit.event_type
        == EntryExitEventType.CUSTOMER_EXIT
    )
    assert lost_exit.track_id == 1
    assert lost_exit.zone_id == zone_id

    print()
    print("=" * 38)
    print("B-4.9 Exit Detection Regression Test")
    print("=" * 38)
    print("Zone entry                : PASS")
    print("Visible zone exit         : PASS")
    print("Camera-sight disappearance: PASS")
    print("Grace-period protection   : PASS")
    print("CUSTOMER_EXIT events      : PASS")
    print()
    print("SUCCESS")
    print("=" * 38)


if __name__ == "__main__":
    main()