"""
Retail Brain OS
Automatic Face Capture Manager

Handles automatic face capture for active tracked customers.

Face capture is independent of:
- customer entry / exit state
- dwell-time calculation
- zone transitions
- customer session state
- GUI rendering

A track is registered after CUSTOMER_ENTRY.
The manager then observes that person's bounding box
until a sufficiently good face is detected.

Once a valid face is captured, exactly one image is
saved for that active track.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import cv2
import numpy as np


class FaceCaptureManager:
    """
    Automatically captures a usable face for tracked customers.

    Flow:

        CUSTOMER_ENTRY
              ↓
        Register track
              ↓
        Observe track
              ↓
        Person bounding box
              ↓
        Face detection
              ↓
        Face quality check
              ↓
        Save face
              ↓
        Mark track as captured
    """

    # Minimum acceptable detected face dimensions.
    MIN_FACE_WIDTH = 30
    MIN_FACE_HEIGHT = 30

    # Minimum Laplacian variance used as a basic
    # sharpness / blur rejection threshold.
    MIN_SHARPNESS = 80.0

    def __init__(
        self,
        save_directory: Path | None = None,
    ) -> None:

        if save_directory is None:

            save_directory = (
                Path(__file__).resolve().parents[2]
                / "face_captures"
            )

        self._save_directory = Path(
            save_directory
        )

        self._cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades
            + "haarcascade_frontalface_default.xml"
        )

        if self._cascade.empty():

            raise RuntimeError(
                "Face detector could not be loaded."
            )

        # Tracks waiting for a usable face.
        self._pending_tracks: set[int] = set()

        # Tracks for which a face has already been saved.
        self._captured_tracks: set[int] = set()

    def register_track(
        self,
        track_id: int,
    ) -> None:
        """
        Register a newly entered track for automatic
        face capture.
        """

        if track_id in self._captured_tracks:

            return

        self._pending_tracks.add(
            track_id
        )

    def process(
        self,
        *,
        track_id: int,
        frame: np.ndarray,
        bounding_box: object,
        timestamp: datetime,
    ) -> bool:
        """
        Attempt automatic face capture for one active track.

        The track remains pending when:
        - no face is detected
        - the face is too small
        - the face is too blurry
        - the bounding box is invalid

        Returns:
            True  if a face was successfully saved.
            False otherwise.
        """

        if track_id not in self._pending_tracks:

            return False

        if (
            frame is None
            or frame.size == 0
        ):

            return False

        # -------------------------------------------------
        # Clamp person bounding box to frame boundaries.
        # -------------------------------------------------

        x1 = max(
            0,
            int(bounding_box.x_min),
        )

        y1 = max(
            0,
            int(bounding_box.y_min),
        )

        x2 = min(
            frame.shape[1],
            int(bounding_box.x_max),
        )

        y2 = min(
            frame.shape[0],
            int(bounding_box.y_max),
        )

        if x2 <= x1 or y2 <= y1:

            return False

        # -------------------------------------------------
        # Crop the selected tracked person's ROI.
        # -------------------------------------------------

        person_crop = frame[
            y1:y2,
            x1:x2,
        ]

        if person_crop.size == 0:

            return False

        # -------------------------------------------------
        # Face detection.
        # -------------------------------------------------

        gray = cv2.cvtColor(
            person_crop,
            cv2.COLOR_BGR2GRAY,
        )

        faces = self._cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(
                self.MIN_FACE_WIDTH,
                self.MIN_FACE_HEIGHT,
            ),
        )

        if len(faces) == 0:

            return False

        # -------------------------------------------------
        # Evaluate all detected faces.
        #
        # If multiple faces are detected inside the
        # person's ROI, use the largest one.
        # -------------------------------------------------

        fx, fy, fw, fh = max(
            faces,
            key=lambda rect: (
                rect[2] * rect[3]
            ),
        )

        if (
            fw < self.MIN_FACE_WIDTH
            or fh < self.MIN_FACE_HEIGHT
        ):

            return False

        face = person_crop[
            fy:fy + fh,
            fx:fx + fw,
        ]

        if face.size == 0:

            return False

        # -------------------------------------------------
        # Basic sharpness / blur check.
        # -------------------------------------------------


        # -------------------------------------------------
        # Valid face found.
        #
        # Save immediately because this face has already
        # satisfied the configured quality requirements.
        # -------------------------------------------------

        saved = self._save_face(
            track_id=track_id,
            face=face,
            timestamp=timestamp,
        )

        if not saved:

            return False

        self._pending_tracks.discard(
            track_id
        )

        self._captured_tracks.add(
            track_id
        )

        return True

    @staticmethod
    def _calculate_sharpness(
        image: np.ndarray,
    ) -> float:
        """
        Calculate image sharpness using Laplacian variance.
        """

        gray = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY,
        )

        return float(
            cv2.Laplacian(
                gray,
                cv2.CV_64F,
            ).var()
        )

    def _save_face(
        self,
        *,
        track_id: int,
        face: np.ndarray,
        timestamp: datetime,
    ) -> bool:
        """
        Save a captured face using the existing
        face_captures directory and filename convention.
        """

        self._save_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        timestamp_text = timestamp.strftime(
            "%Y%m%d_%H%M%S"
        )

        output_path = (
            self._save_directory
            / (
                f"person_{track_id}_"
                f"{timestamp_text}.jpg"
            )
        )

        return bool(
            cv2.imwrite(
                str(output_path),
                face,
            )
        )

    def is_captured(
        self,
        track_id: int,
    ) -> bool:
        """
        Return whether this track already has a
        successfully captured face.
        """

        return track_id in self._captured_tracks

    def remove_track(
        self,
        track_id: int,
    ) -> None:
        """
        Remove temporary face-capture state for a track.

        This does not remove the fact that the track was
        already captured during its current lifecycle.
        """

        self._pending_tracks.discard(
            track_id
        )

    def reset(self) -> None:
        """
        Reset all face-capture state.
        """

        self._pending_tracks.clear()
        self._captured_tracks.clear()
