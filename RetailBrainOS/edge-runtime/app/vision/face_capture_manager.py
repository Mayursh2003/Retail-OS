"""
Retail Brain OS
Automatic Face Capture Manager

Selects the best usable face frame for each active anonymous
track instead of saving the first face detected.

Face capture is independent of:
- customer entry / exit state
- dwell-time calculation
- zone transitions
- customer session state
- GUI rendering

The manager observes a tracked person while the track is pending.
It evaluates every detected face and saves only when a sufficiently
strong candidate is available.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np


@dataclass
class _FaceCandidate:
    """Best face candidate currently observed for one track."""

    face: np.ndarray
    score: float
    timestamp: datetime


class FaceCaptureManager:
    """
    Automatically captures a high-quality face for each tracked person.

    Flow:

        Track appears
             ↓
        Register track
             ↓
        Observe frames
             ↓
        Detect face candidates
             ↓
        Score candidate quality
             ↓
        Keep best candidate
             ↓
        Strong candidate available?
             ↓
        Save face
    """

    # A face smaller than this is not useful for the saved record.
    MIN_FACE_WIDTH = 40
    MIN_FACE_HEIGHT = 40

    # A strong candidate is saved as soon as it reaches this score.
    # There is deliberately no time-based forced capture.
    AUTO_CAPTURE_SCORE = 0.78

    # Candidate quality components.
    MIN_SHARPNESS = 45.0

    # Face should occupy a meaningful portion of the tracked-person ROI.
    MIN_FACE_AREA_RATIO = 0.025

    # Keep a small amount of context around the detected face.
    FACE_PADDING_RATIO = 0.12

    def __init__(
        self,
        save_directory: Path | None = None,
    ) -> None:

        if save_directory is None:
            save_directory = (
                Path(__file__).resolve().parents[2]
                / "face_captures"
            )

        self._save_directory = Path(save_directory)

        self._cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades
            + "haarcascade_frontalface_default.xml"
        )

        if self._cascade.empty():
            raise RuntimeError(
                "Face detector could not be loaded."
            )

        # Haar eye detection provides an additional signal that the
        # detected region is actually a useful frontal face rather than
        # an accidental false-positive rectangle.
        self._eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades
            + "haarcascade_eye.xml"
        )

        if self._eye_cascade.empty():
            raise RuntimeError(
                "Eye detector could not be loaded."
            )

        # Tracks waiting for a usable face.
        self._pending_tracks: set[int] = set()

        # Tracks for which a face has already been saved.
        self._captured_tracks: set[int] = set()

        # Best candidate retained while a track is pending.
        self._best_candidates: dict[int, _FaceCandidate] = {}

    # =========================================================
    # Track lifecycle
    # =========================================================

    def register_track(
        self,
        track_id: int,
    ) -> None:
        """
        Register a tracked person for automatic face capture.

        Registration is intentionally independent of customer-entry
        events. The runtime can register a person as soon as the
        tracker produces the track.
        """

        if track_id in self._captured_tracks:
            return

        self._pending_tracks.add(track_id)

    # =========================================================
    # Processing
    # =========================================================

    def process(
        self,
        *,
        track_id: int,
        frame: np.ndarray,
        bounding_box: object,
        timestamp: datetime,
    ) -> bool:
        """
        Observe one frame for an active track.

        The manager does NOT save the first detected face.

        Instead it:
        - validates the person ROI
        - detects all candidate faces
        - evaluates each candidate
        - retains the best candidate seen so far
        - saves when a strong candidate is available

        A track remains pending indefinitely when no sufficiently
        good face is presented. This avoids saving a poor angle merely
        because a face detector fired once.

        Returns:
            True when a face was successfully saved.
            False otherwise.
        """

        if track_id not in self._pending_tracks:
            return False

        if frame is None or frame.size == 0:
            return False

        # -----------------------------------------------------
        # Clamp person bounding box to frame boundaries.
        # -----------------------------------------------------

        try:
            x1 = max(0, int(bounding_box.x_min))
            y1 = max(0, int(bounding_box.y_min))
            x2 = min(frame.shape[1], int(bounding_box.x_max))
            y2 = min(frame.shape[0], int(bounding_box.y_max))
        except (AttributeError, TypeError, ValueError):
            return False

        if x2 <= x1 or y2 <= y1:
            return False

        person_crop = frame[y1:y2, x1:x2]

        if person_crop.size == 0:
            return False

        # -----------------------------------------------------
        # Face detection.
        # -----------------------------------------------------

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

        # -----------------------------------------------------
        # Evaluate every detected face.
        #
        # Do not blindly choose the largest detection. A slightly
        # smaller but frontal/sharp face can be a better customer
        # capture than a larger poor-angle detection.
        # -----------------------------------------------------

        best_frame_candidate: tuple[
            float,
            np.ndarray,
        ] | None = None

        for fx, fy, fw, fh in faces:

            if (
                fw < self.MIN_FACE_WIDTH
                or fh < self.MIN_FACE_HEIGHT
            ):
                continue

            face = person_crop[
                fy:fy + fh,
                fx:fx + fw,
            ]

            if face.size == 0:
                continue

            score = self._quality_score(
                face=face,
                face_width=fw,
                face_height=fh,
                person_width=x2 - x1,
                person_height=y2 - y1,
            )

            if (
                best_frame_candidate is None
                or score > best_frame_candidate[0]
            ):
                # Keep a natural amount of the original camera image
                # around the detected face. This is better than adding
                # synthetic padding after the crop has already been made.
                padded = self._crop_with_context(
                    person_crop=person_crop,
                    face_x=fx,
                    face_y=fy,
                    face_width=fw,
                    face_height=fh,
                )

                best_frame_candidate = (
                    score,
                    padded,
                )

        if best_frame_candidate is None:
            return False

        score, face = best_frame_candidate

        # -----------------------------------------------------
        # Retain the best candidate observed so far.
        # -----------------------------------------------------

        previous = self._best_candidates.get(track_id)

        if previous is None or score > previous.score:
            self._best_candidates[track_id] = _FaceCandidate(
                face=face,
                score=score,
                timestamp=timestamp,
            )
        else:
            # The previous candidate remains the best one.
            face = previous.face
            score = previous.score
            timestamp = previous.timestamp

        # -----------------------------------------------------
        # Save only after reaching the strong-candidate threshold.
        #
        # This is the critical difference from the old logic:
        # a weak first detection does not become the permanent
        # customer face.
        # -----------------------------------------------------

        if score < self.AUTO_CAPTURE_SCORE:
            return False

        candidate = self._best_candidates[track_id]

        saved = self._save_face(
            track_id=track_id,
            face=candidate.face,
            timestamp=candidate.timestamp,
        )

        if not saved:
            return False

        self._pending_tracks.discard(track_id)
        self._captured_tracks.add(track_id)
        self._best_candidates.pop(track_id, None)

        return True

    # =========================================================
    # Quality scoring
    # =========================================================

    def _quality_score(
        self,
        *,
        face: np.ndarray,
        face_width: int,
        face_height: int,
        person_width: int,
        person_height: int,
    ) -> float:
        """
        Score a detected face from 0.0 to 1.0.

        Signals:
        - face size within the person ROI
        - sharpness
        - brightness
        - local contrast
        - eye visibility

        The score is deliberately conservative: a detector rectangle
        alone is not sufficient to become the saved customer face.
        """

        face_area = float(face_width * face_height)
        person_area = float(
            max(1, person_width * person_height)
        )

        area_ratio = face_area / person_area

        if area_ratio < self.MIN_FACE_AREA_RATIO:
            return 0.0

        # A face occupying roughly 8%+ of the person ROI is considered
        # large enough to provide a strong saved image.
        size_score = min(
            1.0,
            area_ratio / 0.08,
        )

        sharpness = self._calculate_sharpness(face)

        if sharpness < self.MIN_SHARPNESS:
            sharpness_score = 0.0
        else:
            # Saturates gradually rather than creating a hard cliff.
            sharpness_score = min(
                1.0,
                sharpness / 250.0,
            )

        gray = cv2.cvtColor(
            face,
            cv2.COLOR_BGR2GRAY,
        )

        mean_brightness = float(np.mean(gray))

        # Well-exposed faces generally sit away from the extreme
        # black/white ends of the camera range.
        brightness_score = max(
            0.0,
            1.0
            - abs(mean_brightness - 128.0) / 128.0,
        )

        contrast = float(np.std(gray))
        contrast_score = min(
            1.0,
            contrast / 64.0,
        )

        # Eyes are an additional frontal-face signal. We do not require
        # both eyes because glasses, lighting, or partial occlusion can
        # legitimately hide one eye.
        eye_score = self._eye_visibility_score(gray)

        # Weighted quality score.
        score = (
            (0.25 * size_score)
            + (0.30 * sharpness_score)
            + (0.10 * brightness_score)
            + (0.10 * contrast_score)
            + (0.25 * eye_score)
        )

        return float(
            max(
                0.0,
                min(1.0, score),
            )
        )

    def _eye_visibility_score(
        self,
        gray_face: np.ndarray,
    ) -> float:
        """Return a soft score based on detected eyes."""

        height, width = gray_face.shape[:2]

        if height < 30 or width < 30:
            return 0.0

        upper_face = gray_face[
            : int(height * 0.62),
            :
        ]

        eyes = self._eye_cascade.detectMultiScale(
            upper_face,
            scaleFactor=1.1,
            minNeighbors=4,
            minSize=(10, 10),
        )

        if len(eyes) >= 2:
            return 1.0

        if len(eyes) == 1:
            return 0.55

        return 0.0

    @staticmethod
    def _calculate_sharpness(
        image: np.ndarray,
    ) -> float:
        """Calculate sharpness using Laplacian variance."""

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

    # =========================================================
    # Saving
    # =========================================================

    def _save_face(
        self,
        *,
        track_id: int,
        face: np.ndarray,
        timestamp: datetime,
    ) -> bool:
        """
        Save a captured face using the existing directory and
        filename convention.
        """

        self._save_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        timestamp_text = timestamp.strftime(
            "%Y%m%d_%H%M%S_%f"
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

    def _crop_with_context(
        self,
        *,
        person_crop: np.ndarray,
        face_x: int,
        face_y: int,
        face_width: int,
        face_height: int,
    ) -> np.ndarray:
        """
        Return the detected face with a small amount of real camera
        context around it.

        Context is taken from the original tracked-person ROI; no
        synthetic pixels are introduced.
        """

        height, width = person_crop.shape[:2]

        pad_x = max(
            2,
            int(face_width * self.FACE_PADDING_RATIO),
        )
        pad_y = max(
            2,
            int(face_height * self.FACE_PADDING_RATIO),
        )

        x1 = max(0, face_x - pad_x)
        y1 = max(0, face_y - pad_y)
        x2 = min(width, face_x + face_width + pad_x)
        y2 = min(height, face_y + face_height + pad_y)

        return person_crop[y1:y2, x1:x2].copy()

    # =========================================================
    # State
    # =========================================================

    def is_captured(
        self,
        track_id: int,
    ) -> bool:
        """Return whether this track already has a saved face."""

        return track_id in self._captured_tracks

    def remove_track(
        self,
        track_id: int,
    ) -> None:
        """
        Remove temporary candidate state for a track.

        A successfully captured track remains marked as captured for
        its current manager lifecycle.
        """

        self._pending_tracks.discard(track_id)
        self._best_candidates.pop(track_id, None)

    def reset(self) -> None:
        """Reset all face-capture state."""

        self._pending_tracks.clear()
        self._captured_tracks.clear()
        self._best_candidates.clear()
