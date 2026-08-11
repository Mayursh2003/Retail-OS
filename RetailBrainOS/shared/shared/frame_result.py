from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from shared.tracked_person import TrackedPerson


class FrameResult(BaseModel):
    """
    Represents the output of one processed video frame.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    frame_id: UUID
    camera_id: UUID
    timestamp: datetime
    frame_number: int
    processing_time_ms: float
    persons: list[TrackedPerson]