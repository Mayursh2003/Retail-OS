import cv2
import json
import os

FRAME_WIDTH = 960
FRAME_HEIGHT = 720
OUTPUT_PATH = "configs/zones_config.json"

zone_points = []


def mouse_callback(event, x, y, flags, param):
    global zone_points

    if event == cv2.EVENT_LBUTTONDOWN:
        zone_points.append([x, y])
        print(f"Point added: {x}, {y}")


cap = cv2.VideoCapture(0)
cap.set(3, FRAME_WIDTH)
cap.set(4, FRAME_HEIGHT)

if not cap.isOpened():
    print("Error: Cannot access camera")
    exit()

print("Instructions:")
print("1. Place laptop at final testing angle.")
print("2. Press F to freeze current camera frame.")
print("3. Click points around the door / entry-exit zone.")
print("4. Press S to save zone.")
print("5. Press R to reset points.")
print("6. Press Q to quit.")

cv2.namedWindow("Zone Calibrator", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Zone Calibrator", 1280, 720)
cv2.setMouseCallback("Zone Calibrator", mouse_callback)

frozen = False
frozen_frame = None

while True:
    if not frozen:
        ret, frame = cap.read()

        if not ret:
            print("Failed to read camera frame")
            break

        frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
        display = frame.copy()
    else:
        display = frozen_frame.copy()

    for point in zone_points:
        cv2.circle(display, tuple(point), 5, (0, 255, 255), -1)

    if len(zone_points) > 1:
        for i in range(1, len(zone_points)):
            cv2.line(
                display,
                tuple(zone_points[i - 1]),
                tuple(zone_points[i]),
                (0, 255, 0),
                2
            )

    if len(zone_points) > 2:
        cv2.line(
            display,
            tuple(zone_points[-1]),
            tuple(zone_points[0]),
            (0, 255, 0),
            2
        )

    cv2.putText(
        display,
        "F: Freeze | Click Zone | S: Save | R: Reset | Q: Quit",
        (20, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (0, 0, 255),
        2
    )

    cv2.imshow("Zone Calibrator", display)

    key = cv2.waitKey(1) & 0xFF

    if key == ord("f"):
        if not frozen:
            frozen_frame = display.copy()
            frozen = True
            print("Frame frozen. Now click the door zone points.")
        else:
            frozen = False
            zone_points = []
            print("Unfrozen. Points reset.")

    elif key == ord("s"):
        if len(zone_points) < 3:
            print("At least 3 points are required.")
            continue

        os.makedirs("configs", exist_ok=True)

        zones_data = {
            "entry_exit_zone": zone_points
        }

        with open(OUTPUT_PATH, "w") as file:
            json.dump(zones_data, file, indent=4)

        print(f"Zone saved successfully to {OUTPUT_PATH}")
        break

    elif key == ord("r"):
        zone_points = []
        print("Points reset.")

    elif key == ord("q"):
        print("Calibration cancelled.")
        break

cap.release()
cv2.destroyAllWindows()