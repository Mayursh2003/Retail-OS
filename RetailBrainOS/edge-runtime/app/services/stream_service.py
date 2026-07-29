from typing import Dict

from app.cameras.camera_manager import CameraManager
from app.cameras.schemas import CameraStatus


class StreamService:
    """
    Placeholder orchestration layer for future stream lifecycle
    management.

    No streaming, networking, RTSP, threading, or frame processing is
    implemented in this milestone.
    """

    def __init__(self, camera_manager: CameraManager) -> None:
        self._camera_manager = camera_manager

    def start_stream(self, camera_id: str) -> Dict[str, str]:
        camera = self._camera_manager.get_camera(camera_id)

        if camera is None:
            raise KeyError(f"Camera '{camera_id}' is not registered.")

        camera.status = CameraStatus.RUNNING

        return {
            "camera_id": camera.camera_id,
            "status": camera.status.value,
        }

    def stop_stream(self, camera_id: str) -> Dict[str, str]:
        camera = self._camera_manager.get_camera(camera_id)

        if camera is None:
            raise KeyError(f"Camera '{camera_id}' is not registered.")

        camera.status = CameraStatus.STOPPED

        return {
            "camera_id": camera.camera_id,
            "status": camera.status.value,
        }

    def restart_stream(self, camera_id: str) -> Dict[str, str]:
        camera = self._camera_manager.get_camera(camera_id)

        if camera is None:
            raise KeyError(f"Camera '{camera_id}' is not registered.")

        camera.status = CameraStatus.RUNNING

        return {
            "camera_id": camera.camera_id,
            "status": camera.status.value,
        }

    def stream_status(self, camera_id: str) -> Dict[str, str]:
        camera = self._camera_manager.get_camera(camera_id)

        if camera is None:
            raise KeyError(f"Camera '{camera_id}' is not registered.")

        return {
            "camera_id": camera.camera_id,
            "status": camera.status.value,
        }