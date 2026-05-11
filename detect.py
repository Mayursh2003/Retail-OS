from ultralytics import YOLO
import cv2
import time

# Load YOLOv8 nano model
model = YOLO("yolov8n.pt")

# Open webcam
cap = cv2.VideoCapture(0)

# Optional camera resolution
cap.set(3, 640)   # Width
cap.set(4, 480)   # Height

# Previous frame time
prev_time = 0

# Check camera
if not cap.isOpened():
    print("Error: Cannot access camera")
    exit()

while True:
    ret, frame = cap.read()

    if not ret:
        print("Failed to grab frame")
        break

    # Resize frame for faster processing
    frame = cv2.resize(frame, (640, 480))

    # YOLO inference (detect only person class)
    results = model(frame, classes=[0], verbose=False)

    # Draw detections
    annotated_frame = results[0].plot()

    # FPS Calculation
    current_time = time.time()
    fps = 1 / (current_time - prev_time)
    prev_time = current_time

    # Show FPS
    cv2.putText(
        annotated_frame,
        f"FPS: {int(fps)}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2
    )

    # Show output
    cv2.imshow("Retail Brain OS - Live Detection", annotated_frame)

    # Press Q to quit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()
