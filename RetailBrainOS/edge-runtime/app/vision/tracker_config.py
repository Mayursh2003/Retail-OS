"""
Retail Brain OS
Tracker Configuration

Defines the configuration model for object tracking.

This module provides a validated configuration object that is
independent of any third-party tracking implementation. Adapter
implementations (e.g. Ultralytics ByteTrack) are responsible for
translating this configuration into the format expected by the
underlying library.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TrackerConfig(BaseModel):
    """
    Canonical tracker configuration used by Retail Brain OS.

    This configuration intentionally mirrors the commonly used
    ByteTrack parameters while remaining independent of the
    underlying tracking library.
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )

    tracker_type: Literal["bytetrack"] = Field(
        default="bytetrack",
        description="Tracker implementation."
    )

    track_high_thresh: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="High confidence association threshold."
    )

    track_low_thresh: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Low confidence association threshold."
    )

    new_track_thresh: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Minimum confidence required to initialize a new track."
    )

    track_buffer: int = Field(
        default=30,
        ge=1,
        description="Maximum number of frames to retain lost tracks."
    )

    match_thresh: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Association matching threshold."
    )

    fuse_score: bool = Field(
        default=True,
        description="Fuse confidence scores during matching."
    )

    def to_dict(self) -> dict:
        """
        Export the configuration as a plain dictionary.

        Returns:
            Dictionary representation suitable for adapter-specific
            conversion.
        """
        return self.model_dump()