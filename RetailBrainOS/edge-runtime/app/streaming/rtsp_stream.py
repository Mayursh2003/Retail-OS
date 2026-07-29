from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass(slots=True)
class RTSPStream:
    """
    Lifecycle abstraction for an RTSP stream.

    This class intentionally manages only stream state.
    No networking, RTSP communication, or frame acquisition
    is performed in this milestone.
    """

    camera_id: str
    rtsp_url: str

    connected: bool = False
    reconnect_attempts: int = 0
    last_connected_at: Optional[datetime] = field(default=None)

    def connect(self) -> None:
        """
        Mark the stream as connected.

        Actual RTSP connection logic will be implemented
        in a future milestone.
        """
        self.connected = True
        self.reconnect_attempts = 0
        self.last_connected_at = datetime.now(timezone.utc)

        if not (
            self.rtsp_url.startswith("rtsp://")
            or self.rtsp_url.startswith("rtsps://")
        ):
            raise ValueError(
                "Invalid RTSP URL."
            )

    def disconnect(self) -> None:
        """
        Mark the stream as disconnected.

        No network resources are released in this milestone.
        """
        self.connected = False
        self.last_connected_at = None

    def is_connected(self) -> bool:
        """
        Return the current connection state.
        """
        return self.connected