"""
Retail Brain OS
Entry / Exit Engine

Converts zone-state transitions into customer entry/exit events.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.intelligence.events.entry_exit import (
    EntryExitEvent,
    EntryExitEventType,
)
from app.intelligence.tracking.person_state import PersonStateTracker


class EntryExitEngine:
    """
    Converts previous-zone/current-zone transitions into
    CUSTOMER_ENTRY and CUSTOMER_EXIT events.

    The engine does not perform detection or zone geometry.
    """

    def __init__(
        self,
        state_tracker: PersonStateTracker,
    ) -> None:
        self._state_tracker = state_tracker

    def process(
        self,
        *,
        track_id: int,
        camera_id: UUID,
        current_zone_id: UUID | None,
        timestamp: datetime,
    ) -> EntryExitEvent | None:
        """
        Process one person's zone transition.
        """

        previous_zone_id = self._state_tracker.update_zone(
            track_id=track_id,
            zone_id=current_zone_id,
        )

        if (
            previous_zone_id is None
            and current_zone_id is not None
        ):
            return EntryExitEvent.create(
                event_type=(
                    EntryExitEventType.CUSTOMER_ENTRY
                ),
                camera_id=camera_id,
                track_id=track_id,
                zone_id=current_zone_id,
                timestamp=timestamp,
            )

        if (
            previous_zone_id is not None
            and current_zone_id is None
        ):
            return EntryExitEvent.create(
                event_type=(
                    EntryExitEventType.CUSTOMER_EXIT
                ),
                camera_id=camera_id,
                track_id=track_id,
                zone_id=previous_zone_id,
                timestamp=timestamp,
            )

        return None

    def process_lost_track(
        self,
        *,
        track_id: int,
        camera_id: UUID,
        timestamp: datetime,
    ) -> EntryExitEvent | None:
        """
        Convert a genuinely lost track into CUSTOMER_EXIT
        when its last known state was inside a configured zone.

        The intelligence layer decides when a track is genuinely
        lost by applying a grace period first.
        """

        previous_zone_id = (
            self._state_tracker.get_zone(
                track_id
            )
        )

        if previous_zone_id is None:
            self._state_tracker.remove(track_id)
            return None

        event = EntryExitEvent.create(
            event_type=(
                EntryExitEventType.CUSTOMER_EXIT
            ),
            camera_id=camera_id,
            track_id=track_id,
            zone_id=previous_zone_id,
            timestamp=timestamp,
        )

        self._state_tracker.remove(track_id)

        return event

    def remove_track(
        self,
        track_id: int,
    ) -> None:
        self._state_tracker.remove(track_id)

    def reset(self) -> None:
        self._state_tracker.clear()