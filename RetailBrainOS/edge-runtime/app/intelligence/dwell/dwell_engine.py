"""
Retail Brain OS
Dwell Time Engine
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID


@dataclass(slots=True)
class DwellState:
    """
    Tracks when a person entered a specific zone.
    """

    track_id: int
    zone_id: UUID
    entered_at: datetime


@dataclass(slots=True)
class PersonSessionState:
    """
    Tracks cumulative zone dwell for one person during
    the current tracking session.
    """

    track_id: int
    first_seen_at: datetime
    total_dwell: timedelta


class DwellEngine:
    """
    Calculates current zone dwell and cumulative dwell
    across zone visits for each tracked person.

    Current zone dwell remains independent from cumulative
    session dwell.
    """

    def __init__(self) -> None:
        self._states: dict[
            tuple[int, UUID],
            DwellState,
        ] = {}

        self._sessions: dict[
            int,
            PersonSessionState,
        ] = {}

    # =====================================================
    # Person Session
    # =====================================================

    def register_track(
        self,
        *,
        track_id: int,
        first_seen_at: datetime,
    ) -> None:
        """
        Register a tracked person if a session does not
        already exist.

        Existing sessions are preserved.
        """

        if track_id in self._sessions:
            return

        self._sessions[track_id] = (
            PersonSessionState(
                track_id=track_id,
                first_seen_at=first_seen_at,
                total_dwell=timedelta(0),
            )
        )

    def first_seen(
        self,
        track_id: int,
    ) -> datetime | None:
        """
        Return the first-seen timestamp for a track.
        """

        state = self._sessions.get(track_id)

        if state is None:
            return None

        return state.first_seen_at

    def total_dwell(
        self,
        *,
        track_id: int,
        timestamp: datetime,
    ) -> timedelta:
        """
        Return cumulative dwell across completed and
        currently active zone visits.
        """

        session = self._sessions.get(track_id)

        if session is None:
            return timedelta(0)

        total = session.total_dwell

        for (state_track_id, _zone_id), state in (
            self._states.items()
        ):
            if state_track_id != track_id:
                continue

            current_duration = (
                timestamp - state.entered_at
            )

            if current_duration > timedelta(0):
                total += current_duration

        return total

    # =====================================================
    # Zone Dwell
    # =====================================================

    def enter(
        self,
        *,
        track_id: int,
        zone_id: UUID,
        timestamp: datetime,
    ) -> None:
        """
        Start dwell tracking for a person entering a zone.

        If dwell tracking already exists for this person/zone,
        the original entry time is preserved.
        """

        key = (track_id, zone_id)

        if key in self._states:
            return

        self._states[key] = DwellState(
            track_id=track_id,
            zone_id=zone_id,
            entered_at=timestamp,
        )

    def duration(
        self,
        *,
        track_id: int,
        zone_id: UUID,
        timestamp: datetime,
    ) -> timedelta | None:
        """
        Return the current dwell duration.
        """

        state = self._states.get(
            (track_id, zone_id)
        )

        if state is None:
            return None

        return timestamp - state.entered_at

    def exit(
        self,
        *,
        track_id: int,
        zone_id: UUID,
        timestamp: datetime,
    ) -> timedelta | None:
        """
        Finish dwell tracking and add the completed duration
        to the person's cumulative session dwell.
        """

        key = (track_id, zone_id)

        state = self._states.pop(
            key,
            None,
        )

        if state is None:
            return None

        duration = timestamp - state.entered_at

        if duration < timedelta(0):
            duration = timedelta(0)

        session = self._sessions.get(track_id)

        if session is not None:
            session.total_dwell += duration

        return duration

    def remove_track(
        self,
        track_id: int,
        *,
        timestamp: datetime | None = None,
    ) -> None:
        """
        Remove active zone dwell state for a track.

        If a timestamp is supplied, active zone durations are
        finalized into the cumulative session before removal.
        """

        keys = [
            key
            for key in self._states
            if key[0] == track_id
        ]

        if timestamp is not None:
            for key in keys:
                zone_id = key[1]

                self.exit(
                    track_id=track_id,
                    zone_id=zone_id,
                    timestamp=timestamp,
                )

        else:
            for key in keys:
                self._states.pop(
                    key,
                    None,
                )

    def reset(self) -> None:
        """
        Clear all dwell and session state.
        """

        self._states.clear()
        self._sessions.clear()