"""
Retail Brain OS
Retail Intelligence Result
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from uuid import UUID

from app.intelligence.events.entry_exit import EntryExitEvent


@dataclass(slots=True)
class PersonIntelligence:
    """
    Intelligence state for one currently visible tracked person.
    """

    track_id: int
    zone_id: UUID | None
    dwell_time: timedelta | None
    entry_exit_event: EntryExitEvent | None

    # -------------------------------------------------
    # Session information
    # -------------------------------------------------

    first_seen_at: datetime | None = None
    total_dwell: timedelta = timedelta(0)


@dataclass(slots=True)
class RetailIntelligenceResult:
    """
    Result produced by the Retail Intelligence layer
    for one FrameResult.

    ``persons`` contains only currently visible tracked
    people.

    ``events`` contains every new intelligence event produced
    while processing this frame, including events generated
    for tracks that have just disappeared.
    """

    camera_id: UUID
    timestamp: object
    frame_number: int

    persons: list[PersonIntelligence] = field(
        default_factory=list
    )

    events: list[EntryExitEvent] = field(
        default_factory=list
    )