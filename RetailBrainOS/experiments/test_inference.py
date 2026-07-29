#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import cv2
from ultralytics import YOLO

WINDOW_NAME = "Retail Brain OS - Person Tracking Prototype"


def parse_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--model",
        default="yolo11n.pt"
    )

    parser.add_argument(
        "--source",
        default=None
    )

    parser.add_argument(
        "--conf",
        type=float,
        default=0.25
    )

    parser.add_argument(
        "--imgsz",
        type=int,
        default=640
    )

    parser.add_argument(
        "--tracker",
        default="bytetrack.yaml",
        help="Ultralytics tracker configuration"
    )

    return parser.parse_args()


def open_capture(source):

    if source is None:
        cap = cv2.VideoCapture(0)
    else:
        cap = cv2.VideoCapture(source)

    if not cap.isOpened():
        raise RuntimeError("Unable to open source.")

    return cap


def main():

    args = parse_arguments()

    if not Path(args.model).exists():
        print("Model not found.")
        return 1

    model = YOLO(args.model)

    capture = open_capture(args.source)

    print("=" * 50)
    print("Retail Brain OS")
    print("Person Tracking Prototype")
    print("=" * 50)
    print(f"Model      : {args.model}")
    print(f"Tracker    : {args.tracker}")
    print(f"Source     : {args.source or 'Webcam'}")
    print(f"Confidence : {args.conf}")
    print(f"Image Size : {args.imgsz}")
    print("=" * 50)

    previous_time = time.perf_counter()

    frame_count = 0
    total_latency = 0.0
    total_fps = 0.0

    unique_ids = set()
    maximum_people = 0

    print("Press Q to quit.")

    try:

        while True:

            success, frame = capture.read()

            if not success:
                if args.source is None:
                    print("Camera frame capture failed.")
                else:
                    print("End of video reached.")
                break

            inference_start = time.perf_counter()

            results = model.track(
                frame,
                persist=True,
                tracker=args.tracker,
                classes=[0],
                conf=args.conf,
                imgsz=args.imgsz,
                verbose=False,
            )

            latency = time.perf_counter() - inference_start

            annotated = frame.copy()

            current_people = 0

            boxes = results[0].boxes

            if boxes is not None:

                ids = boxes.id

                if ids is not None:

                    ids = ids.int().cpu().tolist()

                else:

                    ids = [None] * len(boxes)

                xyxy = boxes.xyxy.cpu().numpy()
                confs = boxes.conf.cpu().numpy()

                for box, track_id, confidence in zip(
                    xyxy,
                    ids,
                    confs,
                ):

                    x1, y1, x2, y2 = map(int, box)

                    current_people += 1

                    if track_id is not None:
                        unique_ids.add(track_id)
                        label = (
                            f"Person #{track_id} "
                            f"{confidence:.2f}"
                        )
                    else:
                        label = (
                            f"Person "
                            f"{confidence:.2f}"
                        )

                    cv2.rectangle(
                        annotated,
                        (x1, y1),
                        (x2, y2),
                        (0, 255, 0),
                        2,
                    )

                    cv2.putText(
                        annotated,
                        label,
                        (x1, y1 - 8),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        2,
                    )

            maximum_people = max(
                maximum_people,
                current_people,
            )

            frame_count += 1
            total_latency += latency

            current_time = time.perf_counter()

            fps = 1.0 / (
                current_time - previous_time
            )

            previous_time = current_time

            total_fps += fps

            average_latency = (
                total_latency / frame_count
            )

            cv2.putText(
                annotated,
                f"Tracked: {current_people}",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
            )

            cv2.putText(
                annotated,
                f"FPS: {fps:.1f}",
                (20, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 255),
                2,
            )

            cv2.putText(
                annotated,
                f"Latency: {average_latency*1000:.1f} ms",
                (20, 105),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 0),
                2,
            )

            cv2.imshow(
                WINDOW_NAME,
                annotated,
            )

            key = cv2.waitKey(1)

            if key & 0xFF == ord("q"):
                break

    except KeyboardInterrupt:
        pass

    except Exception as exc:
        print(exc)

    finally:

        capture.release()
        cv2.destroyAllWindows()

    average_fps = (
        total_fps / frame_count
        if frame_count
        else 0
    )

    average_latency = (
        total_latency / frame_count
        if frame_count
        else 0
    )

    print("\n========== Benchmark ==========")
    print(f"Frames Processed            : {frame_count}")
    print(f"Average FPS                : {average_fps:.2f}")
    print(f"Average Latency            : {average_latency*1000:.2f} ms")
    print(f"Maximum Tracked People     : {maximum_people}")
    print(f"Unique Person IDs Assigned : {len(unique_ids)}")
    print("================================")

    return 0


if __name__ == "__main__":
    sys.exit(main())