from typing import Dict, Optional, Sequence

from app.cameras.camera import Camera
from app.cameras.schemas import CameraStatus


class CameraManager:
    """
    In-memory camera registry.

    This manager is intentionally storage-agnostic and does not perform
    networking, RTSP validation, frame capture, or background execution.

    It is designed to be extended in future milestones with streaming
    and lifecycle management while maintaining a stable public API.
    """

    def __init__(self) -> None:
        self._cameras: Dict[str, Camera] = {}

    def register_camera(self, camera: Camera) -> Camera:
        """
        Register a new camera.

        Raises:
            ValueError: If the camera data is invalid or the camera ID
            already exists.
        """

        if not camera.camera_id.strip():
            raise ValueError("Camera ID cannot be empty.")

        if not camera.name.strip():
            raise ValueError("Camera name cannot be empty.")

        if not (
            camera.rtsp_url.startswith("rtsp://")
            or camera.rtsp_url.startswith("rtsps://")
        ):
            raise ValueError(
                "Camera RTSP URL must start with rtsp:// or rtsps://"
            )

        if camera.camera_id in self._cameras:
            raise ValueError(
                f"Camera '{camera.camera_id}' is already registered."
            )

        self._cameras[camera.camera_id] = camera
        return camera

    def remove_camera(self, camera_id: str) -> bool:
        """
        Remove a camera.

        Returns:
            True if removed, otherwise False.
        """
        return self._cameras.pop(camera_id, None) is not None

    def get_camera(self, camera_id: str) -> Optional[Camera]:
        """
        Retrieve a camera by ID.
        """
        return self._cameras.get(camera_id)

    def list_cameras(self) -> Sequence[Camera]:
        """
        Return all registered cameras.
        """
        return tuple(self._cameras.values())

    def enable_camera(self, camera_id: str) -> Camera:
        """
        Enable a registered camera.
        """
        camera = self._require_camera(camera_id)
        camera.enabled = True

        if camera.status == CameraStatus.STOPPED:
            camera.status = CameraStatus.REGISTERED

        return camera

    def disable_camera(self, camera_id: str) -> Camera:
        """
        Disable a registered camera.
        """
        camera = self._require_camera(camera_id)
        camera.enabled = False
        camera.status = CameraStatus.STOPPED
        return camera

    def _require_camera(self, camera_id: str) -> Camera:
        camera = self.get_camera(camera_id)

        if camera is None:
            raise KeyError(
                f"Camera '{camera_id}' is not registered."
            )

        return camera