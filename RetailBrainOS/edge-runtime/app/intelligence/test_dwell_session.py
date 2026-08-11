"""
Retail Brain OS
B-4.5B Dwell Session Verification

Verifies cumulative dwell across multiple zone visits without
touching the live runtime or GUI.
"""

from datetime import datetime, timedelta
from uuid import uuid4

from app.intelligence.dwell.dwell_engine import DwellEngine


def main() -> None:
    engine = DwellEngine()

    zone_a = uuid4()
    zone_b = uuid4()

    t0 = datetime(2026, 8, 11, 12, 0, 0)
    t_a_exit = t0 + timedelta(seconds=30)
    t_b_exit = t0 + timedelta(seconds=75)

    track_id = 7

    # Person session starts.
    engine.register_track(
        track_id=track_id,
        first_seen_at=t0,
    )

    # Zone A: 30 seconds.
    engine.enter(
        track_id=track_id,
        zone_id=zone_a,
        timestamp=t0,
    )

    zone_a_current = engine.duration(
        track_id=track_id,
        zone_id=zone_a,
        timestamp=t_a_exit,
    )

    assert zone_a_current == timedelta(seconds=30)

    zone_a_final = engine.exit(
        track_id=track_id,
        zone_id=zone_a,
        timestamp=t_a_exit,
    )

    assert zone_a_final == timedelta(seconds=30)

    # Zone B: 45 seconds.
    engine.enter(
        track_id=track_id,
        zone_id=zone_b,
        timestamp=t_a_exit,
    )

    zone_b_current = engine.duration(
        track_id=track_id,
        zone_id=zone_b,
        timestamp=t_b_exit,
    )

    assert zone_b_current == timedelta(seconds=45)

    total = engine.total_dwell(
        track_id=track_id,
        timestamp=t_b_exit,
    )

    assert total == timedelta(seconds=75)

    first_seen = engine.first_seen(track_id)

    assert first_seen == t0

    print("==============================")
    print("B-4.5B Dwell Session Test")
    print("==============================")
    print("Zone A dwell (30s) : PASS")
    print("Zone B dwell (45s) : PASS")
    print("Total dwell (75s)  : PASS")
    print("First seen         : PASS")
    print()
    print("==============================")
    print("SUCCESS")
    print("==============================")


if __name__ == "__main__":
    main()