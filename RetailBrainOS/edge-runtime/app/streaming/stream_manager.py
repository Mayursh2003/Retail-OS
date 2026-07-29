from __future__ import annotations

from typing import Dict, Sequence

from app.streaming.exceptions import (
    StreamConnectionError,
    StreamNotFoundError,
)
from app.streaming.rtsp_stream import RTSPStream


class StreamManager:
    """
    In-memory registry for RTSP stream lifecycle management.

    This component is intentionally independent of networking,
    threading, frame capture, and video decoding.
    """

    def __init__(self) -> None:
        self._streams: Dict[str, RTSPStream] = {}

    def add_stream(self, stream: RTSPStream) -> RTSPStream:
        """
        Register a new stream.
        """
        if stream.camera_id in self._streams:
            raise StreamConnectionError(
                f"Stream '{stream.camera_id}' is already registered."
            )

        self._streams[stream.camera_id] = stream
        return stream

    def remove_stream(self, camera_id: str) -> bool:
        """
        Remove a registered stream.

        Returns:
            True if removed, otherwise False.
        """
        return self._streams.pop(camera_id, None) is not None

    def get_stream(self, camera_id: str) -> RTSPStream:
        """
        Retrieve a stream by camera ID.
        """
        stream = self._streams.get(camera_id)

        if stream is None:
            raise StreamNotFoundError(
                f"Stream '{camera_id}' was not found."
            )

        return stream

    def list_streams(self) -> Sequence[RTSPStream]:
        """
        Return all registered streams.
        """
        return tuple(self._streams.values())

    def connect_stream(self, camera_id: str) -> RTSPStream:
        """
        Transition a stream to the connected state.
        """
        stream = self.get_stream(camera_id)

        if stream.is_connected():
            raise StreamConnectionError(
                f"Stream '{camera_id}' is already connected."
            )

        stream.connect()
        return stream

    def disconnect_stream(self, camera_id: str) -> RTSPStream:
        """
        Transition a stream to the disconnected state.
        """
        stream = self.get_stream(camera_id)

        if not stream.is_connected():
            raise StreamConnectionError(
                f"Stream '{camera_id}' is already disconnected."
            )

        stream.disconnect()
        return stream