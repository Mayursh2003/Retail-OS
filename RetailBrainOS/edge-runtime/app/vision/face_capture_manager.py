"""
Retail Brain OS
Automatic Face Capture Manager

Handles automatic face capture for active tracked customers.

This component is independent of:
- customer entry/exit state
- dwell-time calculation
- zone transitions
- GUI rendering

A tracked customer can be registered for face capture when a
CUSTOMER_ENTRY event occurs. The manager then observes that
track across subsequent frames and captures the best usable
face automatically.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np


@dataclass
class FaceCaptureCandidate:
    """
    Represents the best face observed so far for a tracked person.
    """

    image: np.ndarray
    score: float


class FaceCaptureManager:
    """
    Manages automatic face capture for tracked customers.

    Capture flow:

        Track ID
            ↓
        Person bounding box
            ↓
        Face detection
            ↓
        Face quality evaluation
            ↓
        Best candidate
            ↓
        Save one face image
    """

    MIN_FACE_SIZE = 40

    # Higher values indicate a sharper image.
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

        self._pending_tracks: set[int] = set()

        self._captured_tracks: set[int] = set()

        self._candidates: dict[
            int,
            FaceCaptureCandidate,
        ] = {}

    def register_track(
        self,
        track_id: int,
    ) -> None:
        """
        Register a tracked customer for automatic face capture.
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
        Process the current frame for one tracked person.

        Returns:
            True  -> a face was successfully captured.
            False -> no capture occurred.
        """

        if track_id not in self._pending_tracks:

            return False

        if frame is None or frame.size == 0:

            return False

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

        person_crop = frame[
            y1:y2,
            x1:x2,
        ]

        if person_crop.size == 0:

            return False

        gray = cv2.cvtColor(
            person_crop,
            cv2.COLOR_BGR2GRAY,
        )

        faces = self._cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(
                self.MIN_FACE_SIZE,
                self.MIN_FACE_SIZE,
            ),
        )

        if len(faces) == 0:

            return False

        for (
            fx,
            fy,
            fw,
            fh,
        ) in faces:

            face = person_crop[
                fy:fy + fh,
                fx:fx + fw,
            ]

            if face.size == 0:

                continue

            sharpness = self._sharpness(
                face
            )

            if sharpness < self.MIN_SHARPNESS:

                continue

            face_area = fw * fh

            score = (
                float(face_area)
                * min(
                    sharpness,
                    1000.0,
                )
            )

            current_candidate = (
                self._candidates.get(
                    track_id
                )
            )

            if (
                current_candidate is None
                or score > current_candidate.score
            ):

                self._candidates[
                    track_id
                ] = FaceCaptureCandidate(
                    image=face.copy(),
                    score=score,
                )

        return self._save_best_candidate(
            track_id=track_id,
            timestamp=timestamp,
        )

    @staticmethod
    def _sharpness(
        image: np.ndarray,
    ) -> float:
        """
        Estimate image sharpness using Laplacian variance.
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

    def _save_best_candidate(
        self,
        *,
        track_id: int,
        timestamp: datetime,
    ) -> bool:
        """
        Save the best face candidate found so far.
        """

        candidate = self._candidates.get(
            track_id
        )

        if candidate is None:

            return False

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

        if not cv2.imwrite(
            str(output_path),
            candidate.image,
        ):

            return False

        self._pending_tracks.discard(
            track_id
        )

        self._captured_tracks.add(
            track_id
        )

        self._candidates.pop(
            track_id,
            None,
        )

        return True

    def is_captured(
        self,
        track_id: int,
    ) -> bool:
        """
        Return whether a face has already been captured
        for the current tracked person.
        """

        return track_id in self._captured_tracks

    def remove_track(
        self,
        track_id: int,
    ) -> None:
        """
        Remove temporary capture state for a track.
        """

        self._pending_tracks.discard(
            track_id
        )

        self._candidates.pop(
            track_id,
            None,
        )

    def reset(self) -> None:
        """
        Reset all face-capture state.
        """

        self._pending_tracks.clear()
        self._captured_tracks.clear()
        self._candidates.clear()