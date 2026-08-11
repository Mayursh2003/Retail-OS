from __future__ import annotations

from pathlib import Path
from typing import Any

from ultralytics import YOLO

from app.streaming.frame import Frame
from app.vision.exceptions import InferenceError, ModelLoadError


class Detector:
    """
    Production person detector.

    Responsibilities:
    - Load the YOLO model once.
    - Perform person detection.
    - Return raw Ultralytics detections.

    This class intentionally does NOT perform:
    - Tracking
    - Result formatting
    - Analytics
    - UI rendering
    """

    PERSON_CLASS_ID = 0

    def __init__(
        self,
        model_path: str,
        confidence: float = 0.25,
        image_size: int = 640,
    ) -> None:
        self._confidence = confidence
        self._image_size = image_size

        model_file = Path(model_path)

        if not model_file.exists():
            raise ModelLoadError(
                f"Model file not found: {model_file}"
            )

        try:
            self._model = YOLO(str(model_file))
        except Exception as exc:
            raise ModelLoadError(
                f"Unable to load YOLO model: {exc}"
            ) from exc

    @property
    def confidence(self) -> float:
        return self._confidence

    @property
    def image_size(self) -> int:
        return self._image_size

    def detect(self, frame: Frame) -> Any:
        """
        Run person detection on a single frame.

        Args:
            frame:
                Frame received from the Frame Reader.

        Returns:
            Raw Ultralytics Results object.

        Raises:
            InferenceError:
                If inference fails.
        """

        try:
            results = self._model.predict(
                source=frame.image,
                classes=[self.PERSON_CLASS_ID],
                conf=self._confidence,
                imgsz=self._image_size,
                verbose=False,
            )

            return results[0]

        except Exception as exc:
            raise InferenceError(
                f"Detection failed: {exc}"
            ) from exc