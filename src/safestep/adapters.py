from __future__ import annotations

from typing import Sequence

from .tracking import Box, Detection


class OpenCVVideoSource:
    """Optional OpenCV-backed video source."""

    def __init__(self, device: int = 0) -> None:
        import cv2  # optional runtime dependency

        self.cv2 = cv2
        self.cap = cv2.VideoCapture(device)

    def read(self) -> object:
        ok, frame = self.cap.read()
        if not ok:
            raise RuntimeError("camera frame read failed")
        return frame


class YOLODetector:
    """Ultralytics YOLO adapter returning normalized Detection objects."""

    def __init__(self, model_path: str = "yolov8n.pt") -> None:
        from ultralytics import YOLO  # optional runtime dependency

        self.model = YOLO(model_path)

    def detect(self, frame: object) -> Sequence[Detection]:
        result = self.model(frame, verbose=False)[0]
        detections: list[Detection] = []
        for box in result.boxes:
            cls_id = int(box.cls.item())
            conf = float(box.conf.item())
            x1, y1, x2, y2 = [float(v) for v in box.xyxy[0].tolist()]
            label = self.model.names[cls_id]
            detections.append(
                Detection(label=label, confidence=conf, box=Box(x1=x1, y1=y1, x2=x2, y2=y2))
            )
        return detections
