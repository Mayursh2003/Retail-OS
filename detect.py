from ultralytics import YOLO
import cv2

# Load YOLOv8 model
model = YOLO("yolov8n.pt")

# Video path
video_path = r"C:\Users\jverm\OneDrive\Desktop\retail-brain-os\vision\videos\CCTV Video 1.mp4"

# Open video
cap = cv2.VideoCapture(video_path)

# Check if video opened successfully
if not cap.isOpened():
    print("Error opening video")
    exit()

while True:
    ret, frame = cap.read()

    # Stop if video ends
    if not ret:
        break

    # Run YOLO detection
    results = model(frame)

    # Draw detections
    annotated_frame = results[0].plot()

    # Display output
    cv2.imshow("Retail Brain OS - Detection", annotated_frame)

    # Press Q to quit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()