"""
Basic runtime test for UltralyticsTracker.
"""

from app.vision.tracker_config import TrackerConfig
from app.vision.ultralytics_tracker import UltralyticsTracker


def main():
    config = TrackerConfig()

    tracker = UltralyticsTracker(config)

    print(f"Initialized before initialize(): {tracker.initialized}")

    tracker.initialize()

    print(f"Initialized after initialize(): {tracker.initialized}")

    tracker.close()

    print(f"Initialized after close(): {tracker.initialized}")

    print("SUCCESS")


if __name__ == "__main__":
    main()