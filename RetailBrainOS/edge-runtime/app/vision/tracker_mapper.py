"""
Retail Brain OS
Tracker Result Mapper

Converts raw tracker output into Retail Brain OS
shared contracts.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

import numpy as np

from shared import (
    BoundingBox,
    FrameResult,
    TrackedPerson,
)


class TrackerMapper:
    """
    Maps tracker output into Retail Brain OS shared contracts.

    The mapper is intentionally independent of the concrete
    tracker implementation.
    """

    @staticmethod
    def map(
        tracked_objects: np.ndarray,
        camera_id: UUID,
        timestamp: datetime,
        frame_number: int,
        processing_time_ms: float,
    ) -> FrameResult:
        """
        Convert tracker output into a FrameResult.

        A frame with zero tracked objects is valid and must still
        produce a FrameResult with an empty persons list.
        """

        persons: list[TrackedPerson] = []

        for row in tracked_objects:
            x1 = float(row[0])
            y1 = float(row[1])
            x2 = float(row[2])
            y2 = float(row[3])

            track_id = int(row[4])
            confidence = float(row[5])

            bounding_box = BoundingBox(
                x_min=x1,
                y_min=y1,
                x_max=x2,
                y_max=y2,
                width=x2 - x1,
                height=y2 - y1,
            )

            person = TrackedPerson(
                track_id=track_id,
                camera_id=camera_id,
                bounding_box=bounding_box,
                confidence=confidence,
                first_seen_at=timestamp,
                last_seen_at=timestamp,
            )

            persons.append(person)

        return FrameResult(
            frame_id=uuid4(),
            camera_id=camera_id,
            timestamp=timestamp,
            frame_number=frame_number,
            processing_time_ms=processing_time_ms,
            persons=persons,
        )