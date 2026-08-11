"""
Retail Brain OS
Person Zone State

Maintains the previous zone observed for each tracked person.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class PersonZoneState:
    """
    Current state of one tracked person.
    """

    track_id: int
    zone_id: UUID | None


class PersonStateTracker:
    """
    Maintains zone state for tracked people.

    This component does not generate events.
    It only remembers the previous zone so that the
    event layer can detect transitions.
    """

    def __init__(self) -> None:
        self._states: dict[int, PersonZoneState] = {}

    def get_zone(self, track_id: int) -> UUID | None:
        """
        Return the previously known zone for a track.
        """

        state = self._states.get(track_id)

        if state is None:
            return None

        return state.zone_id

    def update_zone(
        self,
        track_id: int,
        zone_id: UUID | None,
    ) -> UUID | None:
        """
        Update the person's current zone.

        Returns the previous zone.
        """

        previous_zone = self.get_zone(track_id)

        self._states[track_id] = PersonZoneState(
            track_id=track_id,
            zone_id=zone_id,
        )

        return previous_zone

    def remove(self, track_id: int) -> None:
        """
        Remove state for a tracked person.
        """

        self._states.pop(track_id, None)

    def clear(self) -> None:
        """
        Clear all tracked-person state.
        """

        self._states.clear()

    def active_tracks(self) -> list[int]:
        """
        Return currently tracked person IDs.
        """

        return list(self._states.keys())