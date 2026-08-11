from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

import numpy as np


@dataclass(frozen=True, slots=True)
class Frame:
    """
    Immutable frame container passed through the vision pipeline.

    This model intentionally contains only the metadata required by
    downstream vision components. It performs no image processing,
    validation, or transformation.
    """

    camera_id: UUID
    image: np.ndarray
    timestamp: datetime