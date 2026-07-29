from dataclasses import dataclass

from app.cameras.schemas import CameraStatus


@dataclass(slots=True)
class Camera:
    """
    Represents a registered camera within the Edge Runtime.

    This model intentionally contains only registration metadata.
    Streaming and runtime state management will be implemented in
    future milestones.
    """

    camera_id: str
    name: str
    rtsp_url: str
    enabled: bool = True
    status: CameraStatus = CameraStatus.REGISTERED