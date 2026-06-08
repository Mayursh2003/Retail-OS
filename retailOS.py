import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../..")
)
sys.path.insert(0, PROJECT_ROOT)

from vision.zones.zone_manager import ZoneManager
from ultralytics import YOLO
import cv2
import time
import numpy as np


# Load YOLOv8 Nano model
model = YOLO("yolov8n.pt")

# Open webcam
cap = cv2.VideoCapture(0)

# Frame settings
FRAME_WIDTH = 960
FRAME_HEIGHT = 720
DASHBOARD_WIDTH = 420
MAX_TRAIL_LENGTH = 30

cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

if not cap.isOpened():
    print("Error: Cannot access camera")
    exit()

# Timing
prev_time = time.time()

# Visitor tracking data
total_visitor_ids = set()
visitor_data = {}

# Zone manager
zone_manager = ZoneManager()

# Create resizable window
window_name = "Retail Brain OS - Zone Intelligence Dashboard"
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
cv2.resizeWindow(window_name, 1400, 800)


while True:
    ret, frame = cap.read()

    if not ret:
        print("Failed to grab frame")
        break

    frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

    results = model.track(
        frame,
        classes=[0],
        persist=True,
        tracker="bytetrack.yaml",
        verbose=False
    )

    annotated_frame = frame.copy()
    active_ids = set()

    current_time = time.time()

    if results and results[0].boxes is not None:
        boxes = results[0].boxes

        for box in boxes:
            if box.id is None:
                continue

            x1, y1, x2, y2 = map(
                int,
                box.xyxy[0].cpu().numpy()
            )

            track_id = int(box.id[0])

            active_ids.add(track_id)
            total_visitor_ids.add(track_id)

            center_x = int((x1 + x2) / 2)
            center_y = int((y1 + y2) / 2)
            center_position = (center_x, center_y)

            event = zone_manager.update_visitor_position(
                track_id,
                center_position
            )


            if track_id not in visitor_data:
                visitor_data[track_id] = {
                    "first_seen": current_time,
                    "last_seen": current_time,
                    "frames_visible": 1,
                    "current_position": center_position,
                    "previous_position": center_position,
                    "path": [center_position],
                }
            else:
                previous_position = visitor_data[track_id]["current_position"]

                visitor_data[track_id]["previous_position"] = previous_position
                visitor_data[track_id]["current_position"] = center_position
                visitor_data[track_id]["last_seen"] = current_time
                visitor_data[track_id]["frames_visible"] += 1
                visitor_data[track_id]["path"].append(center_position)

                if len(visitor_data[track_id]["path"]) > MAX_TRAIL_LENGTH:
                    visitor_data[track_id]["path"].pop(0)

            cv2.rectangle(
                annotated_frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

            label = f"ID: {track_id}"

            cv2.putText(
                annotated_frame,
                label,
                (x1, max(y1 - 10, 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 0),
                2
            )

            cv2.circle(
                annotated_frame,
                center_position,
                4,
                (0, 255, 255),
                -1
            )

            path_points = visitor_data[track_id]["path"]

            for i in range(1, len(path_points)):
                cv2.line(
                    annotated_frame,
                    path_points[i - 1],
                    path_points[i],
                    (255, 0, 255),
                    2
                )

    # Draw calibrated zones after detections
    zone_manager.draw_zones(annotated_frame)

    fps = 1 / max((current_time - prev_time), 0.0001)
    prev_time = current_time

    cv2.putText(
        annotated_frame,
        f"FPS: {int(fps)}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 255, 0),
        2
    )

    dashboard = np.zeros(
        (FRAME_HEIGHT, DASHBOARD_WIDTH, 3),
        dtype=np.uint8
    )

    cv2.putText(
        dashboard,
        "Retail Brain OS",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (0, 255, 255),
        2
    )

    cv2.putText(
        dashboard,
        "Day 4: Zone Intelligence",
        (20, 75),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (200, 200, 200),
        1
    )

    stats_y = 125

    stats = [
        f"Active Visitors: {len(active_ids)}",
        f"Total Seen: {len(total_visitor_ids)}",
        f"Entries: {zone_manager.entry_count}",
        f"Exits: {zone_manager.exit_count}",
        f"Occupancy: {zone_manager.occupancy_count}",
        f"FPS: {int(fps)}"
    ]

    for stat in stats:
        cv2.putText(
            dashboard,
            stat,
            (20, stats_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )

        stats_y += 35

    cv2.line(
        dashboard,
        (20, stats_y + 10),
        (380, stats_y + 10),
        (100, 100, 100),
        1
    )

    cv2.putText(
        dashboard,
        "Recent Events",
        (20, stats_y + 45),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )

    event_y = stats_y + 80

    for event in zone_manager.recent_events[:5]:

        text = (
            f"ID {event['track_id']} "
            f"{event['event']} "
            f"{event['time']}"
        )

        cv2.putText(
            dashboard,
            text,
            (20, event_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 165, 255),
            2
        )

        event_y += 30

    cv2.line(
        dashboard,
        (20, event_y + 10),
        (380, event_y + 10),
        (100, 100, 100),
        1
    )

    y = event_y + 50

    cv2.putText(
        dashboard,
        "Visitor Details",
        (20, event_y + 45),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )

    y = event_y + 80

    for visitor_id in list(visitor_data.keys())[-3:]:
        data = visitor_data[visitor_id]

        visible_seconds = int(current_time - data["first_seen"])
        last_seen_seconds = int(current_time - data["last_seen"])
        position = data["current_position"]


        cv2.putText(
            dashboard,
            f"ID {visitor_id}",
            (20, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 255),
            2
        )


        cv2.putText(
            dashboard,
            f"Visible: {visible_seconds}s",
            (20, y + 62),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (200, 200, 200),
            1
        )

        cv2.putText(
            dashboard,
            f"Last Seen: {last_seen_seconds}s ago",
            (20, y + 82),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (200, 200, 200),
            1
        )

        cv2.putText(
            dashboard,
            f"Pos: {position}",
            (20, y + 102),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (200, 200, 200),
            1
        )

        y += 130

        if y > FRAME_HEIGHT - 20:
            break

    combined_frame = np.hstack(
        (annotated_frame, dashboard)
    )

    cv2.imshow(window_name, combined_frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


cap.release()
cv2.destroyAllWindows()