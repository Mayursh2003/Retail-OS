"""
Retail Brain OS
Zone Contract
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Zone:
    """
    Polygonal region associated with a camera.
    """

    zone_id: UUID
    camera_id: UUID
    name: str
    polygon: tuple[tuple[float, float], ...]