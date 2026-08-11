"""
Retail Brain OS
Retail Intelligence Engine
"""

from __future__ import annotations

from app.intelligence.dwell.dwell_engine import DwellEngine
from app.intelligence.events.entry_exit_engine import (
    EntryExitEngine,
)
from app.intelligence.result import (
    PersonIntelligence,
    RetailIntelligenceResult,
)
from app.intelligence.tracking.person_state import (
    PersonStateTracker,
)
from app.intelligence.zones.zone_engine import ZoneEngine
from shared.frame_result import FrameResult


class RetailIntelligenceEngine:
    """
    Orchestrates the retail intelligence pipeline.

    Input:
        FrameResult

    Output:
        RetailIntelligenceResult
    """

    # A short tracker-loss grace period prevents an ordinary
    # one-off detection/tracking dropout from becoming a false
    # customer exit.
    MISSING_TRACK_GRACE_FRAMES = 15

    def __init__(
        self,
        zone_engine: ZoneEngine,
    ) -> None:
        self._zone_engine = zone_engine

        self._state_tracker = PersonStateTracker()

        self._entry_exit_engine = EntryExitEngine(
            self._state_tracker
        )

        self._dwell_engine = DwellEngine()

        self._missing_track_counts: dict[
            int,
            int,
        ] = {}

    def process(
        self,
        frame_result: FrameResult,
    ) -> RetailIntelligenceResult:
        """
        Process one vision FrameResult.

        Handles both:
            1. explicit zone -> outside transitions
            2. tracks that disappear from the FrameResult
        """

        persons: list[PersonIntelligence] = []
        events = []

        current_track_ids = {
            person.track_id
            for person in frame_result.persons
        }

        # -------------------------------------------------
        # Handle tracks missing from the current frame.
        # -------------------------------------------------

        known_track_ids = set(
            self._state_tracker.active_tracks()
        )

        missing_track_ids = (
            known_track_ids
            - current_track_ids
        )

        for track_id in missing_track_ids:

            count = (
                self._missing_track_counts.get(
                    track_id,
                    0,
                )
                + 1
            )

            self._missing_track_counts[
                track_id
            ] = count

            if (
                count
                < self.MISSING_TRACK_GRACE_FRAMES
            ):
                continue

            previous_zone_id = (
                self._state_tracker.get_zone(
                    track_id
                )
            )

            event = (
                self._entry_exit_engine.process_lost_track(
                    track_id=track_id,
                    camera_id=frame_result.camera_id,
                    timestamp=frame_result.timestamp,
                )
            )

            # Finalize active dwell before the track is removed.
            if previous_zone_id is not None:

                self._dwell_engine.exit(
                    track_id=track_id,
                    zone_id=previous_zone_id,
                    timestamp=frame_result.timestamp,
                )

            self._dwell_engine.remove_track(
                track_id,
                timestamp=frame_result.timestamp,
            )

            self._missing_track_counts.pop(
                track_id,
                None,
            )

            if event is not None:
                events.append(event)

        # -------------------------------------------------
        # Process currently visible tracks.
        # -------------------------------------------------

        for tracked_person in frame_result.persons:

            track_id = tracked_person.track_id

            # Track returned before grace period expired.
            self._missing_track_counts.pop(
                track_id,
                None,
            )

            self._dwell_engine.register_track(
                track_id=track_id,
                first_seen_at=(
                    tracked_person.first_seen_at
                ),
            )

            zone = self._zone_engine.locate_person(
                tracked_person
            )

            zone_id = (
                zone.zone_id
                if zone is not None
                else None
            )

            previous_zone_id = (
                self._state_tracker.get_zone(
                    track_id
                )
            )

            event = (
                self._entry_exit_engine.process(
                    track_id=track_id,
                    camera_id=frame_result.camera_id,
                    current_zone_id=zone_id,
                    timestamp=frame_result.timestamp,
                )
            )

            if event is not None:
                events.append(event)

            # Finalize previous zone dwell when the person
            # changes zones or leaves the zone.
            if (
                previous_zone_id is not None
                and previous_zone_id != zone_id
            ):
                self._dwell_engine.exit(
                    track_id=track_id,
                    zone_id=previous_zone_id,
                    timestamp=frame_result.timestamp,
                )

            if zone_id is not None:

                self._dwell_engine.enter(
                    track_id=track_id,
                    zone_id=zone_id,
                    timestamp=frame_result.timestamp,
                )

                dwell_time = (
                    self._dwell_engine.duration(
                        track_id=track_id,
                        zone_id=zone_id,
                        timestamp=frame_result.timestamp,
                    )
                )

            else:

                dwell_time = None

            total_dwell = (
                self._dwell_engine.total_dwell(
                    track_id=track_id,
                    timestamp=frame_result.timestamp,
                )
            )

            persons.append(
                PersonIntelligence(
                    track_id=track_id,
                    zone_id=zone_id,
                    dwell_time=dwell_time,
                    entry_exit_event=event,
                    first_seen_at=(
                        tracked_person.first_seen_at
                    ),
                    total_dwell=total_dwell,
                )
            )

        return RetailIntelligenceResult(
            camera_id=frame_result.camera_id,
            timestamp=frame_result.timestamp,
            frame_number=frame_result.frame_number,
            persons=persons,
            events=events,
        )

    def reset(self) -> None:
        """
        Reset all intelligence state.
        """

        self._state_tracker.clear()
        self._dwell_engine.reset()
        self._missing_track_counts.clear()