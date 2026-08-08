"""
Retail Brain OS
Vision Service Integration Test

Verifies:
- Worker registration
- Worker lookup
- Worker start
- Worker stop
- Worker restart
- Running status
- Worker listing
- Worker unregistration
- Stop-all lifecycle
"""

from __future__ import annotations

from uuid import uuid4

from app.vision.vision_service import VisionService


class FakeCameraWorker:
    """
    Lightweight worker stub used to test VisionService lifecycle
    without requiring a real camera or RTSP connection.
    """

    def __init__(self) -> None:
        self.is_running = False
        self.start_count = 0
        self.stop_count = 0

    def start(self) -> None:
        self.is_running = True
        self.start_count += 1

    def stop(self) -> None:
        self.is_running = False
        self.stop_count += 1

    def __repr__(self) -> str:
        return f"FakeCameraWorker(running={self.is_running})"


def main() -> None:
    service = VisionService()

    camera_a = uuid4()
    camera_b = uuid4()

    worker_a = FakeCameraWorker()
    worker_b = FakeCameraWorker()

    print("\n==============================")
    print("Vision Service Integration Test")
    print("==============================")

    # Register workers
    service.register_worker(camera_a, worker_a)
    service.register_worker(camera_b, worker_b)

    assert service.get_worker(camera_a) is worker_a
    assert service.get_worker(camera_b) is worker_b

    print("Worker registration       : PASS")

    # Verify worker listing
    workers = service.list_workers()

    assert len(workers) == 2
    assert camera_a in workers
    assert camera_b in workers

    print("Worker listing             : PASS")

    # Start camera A
    service.start_camera(camera_a)

    assert worker_a.is_running is True
    assert service.is_running(camera_a) is True

    print("Start camera               : PASS")

    # Stop camera A
    service.stop_camera(camera_a)

    assert worker_a.is_running is False
    assert service.is_running(camera_a) is False

    print("Stop camera                : PASS")

    # Restart camera A
    service.restart_camera(camera_a)

    assert worker_a.is_running is True
    assert worker_a.start_count == 2
    assert worker_a.stop_count == 2

    print("Restart camera             : PASS")

    # Start camera B
    service.start_camera(camera_b)

    assert worker_b.is_running is True

    print("Multi-camera lifecycle     : PASS")

    # Stop all
    service.stop_all()

    assert worker_a.is_running is False
    assert worker_b.is_running is False

    print("Stop all workers           : PASS")

    # Unregister camera A
    service.unregister_worker(camera_a)

    workers = service.list_workers()

    assert camera_a not in workers
    assert camera_b in workers

    print("Worker unregistration     : PASS")

    print("\n==============================")
    print("SUCCESS")
    print("==============================")


if __name__ == "__main__":
    main()