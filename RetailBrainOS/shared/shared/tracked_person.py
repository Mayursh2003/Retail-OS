from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from shared.bounding_box import BoundingBox


class TrackedPerson(BaseModel):
    """
    Represents one tracked person produced by the Vision Pipeline.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    track_id: int
    camera_id: UUID
    bounding_box: BoundingBox
    confidence: float
    first_seen_at: datetime
    last_seen_at: datetime