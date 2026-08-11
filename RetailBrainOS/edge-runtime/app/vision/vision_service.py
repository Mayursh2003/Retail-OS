"""
Retail Brain OS
Vision Service

Manages the lifecycle of CameraWorker instances.

Responsibilities:
- Register workers per camera.
- Start individual workers.
- Stop individual workers.
- Restart individual workers.
- Report worker status.
- Stop all workers during shutdown.

This service does not perform:
- Detection
- Tracking
- Analytics
- Backend communication
- Database operations
- Dashboard operations
"""

from __future__ import annotations

from threading import RLock
from uuid import UUID

from app.vision.camera_worker import CameraWorker


class VisionService:
    """
    Lifecycle manager for camera vision workers.

    Each camera owns an independent CameraWorker instance.
    """

    def __init__(self) -> None:
        self._workers: dict[UUID, CameraWorker] = {}
        self._lock = RLock()

    def register_worker(
        self,
        camera_id: UUID,
        worker: CameraWorker,
    ) -> None:
        """
        Register a worker for a camera.

        Raises:
            ValueError:
                If a worker is already registered for the camera.
        """
        with self._lock:
            if camera_id in self._workers:
                raise ValueError(
                    f"Worker already registered for camera {camera_id}"
                )

            self._workers[camera_id] = worker

    def unregister_worker(
        self,
        camera_id: UUID,
    ) -> None:
        """
        Stop and remove a camera worker.
        """
        with self._lock:
            worker = self._workers.pop(camera_id, None)

        if worker is not None:
            worker.stop()

    def start_camera(
        self,
        camera_id: UUID,
    ) -> None:
        """
        Start the worker assigned to a camera.
        """
        worker = self._get_worker(camera_id)
        worker.start()

    def stop_camera(
        self,
        camera_id: UUID,
    ) -> None:
        """
        Stop the worker assigned to a camera.
        """
        worker = self._get_worker(camera_id)
        worker.stop()

    def restart_camera(
        self,
        camera_id: UUID,
    ) -> None:
        """
        Restart the worker assigned to a camera.
        """
        worker = self._get_worker(camera_id)

        worker.stop()
        worker.start()

    def get_worker(
        self,
        camera_id: UUID,
    ) -> CameraWorker:
        """
        Return the worker assigned to a camera.
        """
        return self._get_worker(camera_id)

    def list_workers(self) -> dict[UUID, CameraWorker]:
        """
        Return a snapshot of registered workers.
        """
        with self._lock:
            return dict(self._workers)

    def is_running(
        self,
        camera_id: UUID,
    ) -> bool:
        """
        Return whether a camera worker is currently running.
        """
        worker = self._get_worker(camera_id)
        return worker.is_running

    def stop_all(self) -> None:
        """
        Stop all registered camera workers.

        Workers remain registered after shutdown so the service
        can be started again without reconstructing the registry.
        """
        with self._lock:
            workers = list(self._workers.values())

        for worker in workers:
            worker.stop()

    def _get_worker(
        self,
        camera_id: UUID,
    ) -> CameraWorker:
        """
        Retrieve a registered worker or raise an explicit error.
        """
        with self._lock:
            worker = self._workers.get(camera_id)

        if worker is None:
            raise KeyError(
                f"No worker registered for camera {camera_id}"
            )

        return worker

    def __repr__(self) -> str:
        with self._lock:
            return (
                f"{self.__class__.__name__}("
                f"workers={len(self._workers)})"
            )