"""
Retail Brain OS
Entry / Exit Event Contract
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class EntryExitEventType(str, Enum):
    """
    Supported customer movement events.
    """

    CUSTOMER_ENTRY = "customer_entry"
    CUSTOMER_EXIT = "customer_exit"


@dataclass(frozen=True, slots=True)
class EntryExitEvent:
    """
    Represents a customer entering or leaving the configured
    store boundary zone.

    This is an Edge Runtime intelligence event.
    It is not yet the Backend API schema.
    """

    event_id: UUID
    event_type: EntryExitEventType
    camera_id: UUID
    track_id: int
    zone_id: UUID
    timestamp: datetime

    @classmethod
    def create(
        cls,
        event_type: EntryExitEventType,
        camera_id: UUID,
        track_id: int,
        zone_id: UUID,
        timestamp: datetime,
    ) -> "EntryExitEvent":
        """
        Create a new EntryExitEvent.
        """

        return cls(
            event_id=uuid4(),
            event_type=event_type,
            camera_id=camera_id,
            track_id=track_id,
            zone_id=zone_id,
            timestamp=timestamp,
        )