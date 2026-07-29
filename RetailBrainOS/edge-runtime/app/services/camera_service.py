from typing import Optional, Sequence

from app.cameras.camera import Camera
from app.cameras.camera_manager import CameraManager


class CameraService:
    """
    Lightweight orchestration layer for camera management.

    This service delegates camera operations to the CameraManager and
    provides a stable abstraction for future extensions such as
    validation, auditing, or lifecycle orchestration.
    """

    def __init__(self, camera_manager: CameraManager) -> None:
        self._camera_manager = camera_manager

    def register_camera(self, camera: Camera) -> Camera:
        return self._camera_manager.register_camera(camera)

    def remove_camera(self, camera_id: str) -> bool:
        return self._camera_manager.remove_camera(camera_id)

    def get_camera(self, camera_id: str) -> Optional[Camera]:
        return self._camera_manager.get_camera(camera_id)

    def list_cameras(self) -> Sequence[Camera]:
        return self._camera_manager.list_cameras()

    def enable_camera(self, camera_id: str) -> Camera:
        return self._camera_manager.enable_camera(camera_id)

    def disable_camera(self, camera_id: str) -> Camera:
        return self._camera_manager.disable_camera(camera_id)