from ultralytics import YOLO
import cv2
import time
import numpy as np

# Load YOLOv8 nano model
model = YOLO("yolov8n.pt")

# Open webcam
cap = cv2.VideoCapture(0)

# Camera resolution
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
DASHBOARD_WIDTH = 360

cap.set(3, FRAME_WIDTH)
cap.set(4, FRAME_HEIGHT)

if not cap.isOpened():
    print("Error: Cannot access camera")
    exit()

prev_time = time.time()

# Visitor tracking data
total_visitor_ids = set()
visitor_data = {}

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

    if results[0].boxes is not None:
        boxes = results[0].boxes

        for box in boxes:
            if box.id is None:
                continue

            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
            confidence = float(box.conf[0])
            track_id = int(box.id[0])

            active_ids.add(track_id)
            total_visitor_ids.add(track_id)

            center_x = int((x1 + x2) / 2)
            center_y = int((y1 + y2) / 2)

            if track_id not in visitor_data:
                visitor_data[track_id] = {
                    "first_seen": current_time,
                    "last_seen": current_time,
                    "frames_visible": 1,
                    "current_position": (center_x, center_y),
                    "path": [(center_x, center_y)]
                }
            else:
                visitor_data[track_id]["last_seen"] = current_time
                visitor_data[track_id]["frames_visible"] += 1
                visitor_data[track_id]["current_position"] = (center_x, center_y)
                
                visitor_data[track_id]["path"].append((center_x, center_y))
                # Keep only recent trail points
                if len(visitor_data[track_id]["path"]) > 30:
                    visitor_data[track_id]["path"].pop(0)

            # Draw clean bounding box
            cv2.rectangle(
                annotated_frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

            # Only essential label on camera frame
            label = f"ID: {track_id}"

            cv2.putText(
                annotated_frame,
                label,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

            # Draw center point
            cv2.circle(
                annotated_frame,
                (center_x, center_y),
                4,
                (0, 255, 255),
                -1
            )

            # Draw movement trail
            path_points = visitor_data[track_id]["path"]

            for i in range(1, len(path_points)):
                cv2.line(
                    annotated_frame,
                    path_points[i - 1],
                    path_points[i],
                    (255, 0, 255),
                    2
                )

    # FPS calculation
    fps = 1 / (current_time - prev_time)
    prev_time = current_time

    # Only FPS on camera frame
    cv2.putText(
        annotated_frame,
        f"FPS: {int(fps)}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 255, 0),
        2
    )

    # Create dashboard panel
    dashboard = np.zeros((FRAME_HEIGHT, DASHBOARD_WIDTH, 3), dtype=np.uint8)

    # Dashboard title
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
        "Day 2: Tracking Dashboard",
        (20, 75),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (200, 200, 200),
        1
    )

    # Summary stats
    cv2.putText(
        dashboard,
        f"Active Visitors: {len(active_ids)}",
        (20, 125),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2
    )

    cv2.putText(
        dashboard,
        f"Total Seen: {len(total_visitor_ids)}",
        (20, 160),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2
    )

    cv2.putText(
        dashboard,
        f"FPS: {int(fps)}",
        (20, 195),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2
    )

    # Divider line
    cv2.line(dashboard, (20, 220), (340, 220), (100, 100, 100), 1)

    cv2.putText(
        dashboard,
        "Visitor Details",
        (20, 250),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )

    y = 285

    # Show latest few visitors
    for visitor_id in list(visitor_data.keys())[-5:]:
        data = visitor_data[visitor_id]

        first_seen_seconds = int(current_time - data["first_seen"])
        last_seen_seconds = int(current_time - data["last_seen"])
        frames_visible = data["frames_visible"]
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
            f"Visible: {first_seen_seconds}s",
            (20, y + 22),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            (200, 200, 200),
            1
        )

        cv2.putText(
            dashboard,
            f"Last Seen: {last_seen_seconds}s ago",
            (20, y + 42),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            (200, 200, 200),
            1
        )

        cv2.putText(
            dashboard,
            f"Frames: {frames_visible}",
            (20, y + 62),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            (200, 200, 200),
            1
        )

        cv2.putText(
            dashboard,
            f"Pos: {position}",
            (20, y + 82),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            (200, 200, 200),
            1
        )

        y += 105

        if y > 455:
            break

    # Combine camera and dashboard
    combined_frame = np.hstack((annotated_frame, dashboard))

    cv2.imshow("Retail Brain OS - Live Tracking Dashboard", combined_frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()