from __future__ import annotations

from typing import Any, Mapping, Sequence

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


class YOLOObjectAdapter:
    """Converts ultralytics YOLO results/boxes into internal Detection objects."""

    @staticmethod
    def _to_label(names: Mapping[int, str] | Sequence[str], cls_id: int) -> str:
        if isinstance(names, Mapping):
            return str(names.get(cls_id, str(cls_id)))
        if 0 <= cls_id < len(names):
            return str(names[cls_id])
        return str(cls_id)

    @classmethod
    def from_result(cls, result: Any, names: Mapping[int, str] | Sequence[str] | None = None) -> list[Detection]:
        resolved_names = names if names is not None else getattr(result, "names", {})
        detections: list[Detection] = []
        for box in result.boxes:
            cls_id = int(box.cls.item())
            conf = float(box.conf.item())
            x1, y1, x2, y2 = [float(v) for v in box.xyxy[0].tolist()]
            detections.append(
                Detection(
                    label=cls._to_label(resolved_names, cls_id),
                    confidence=conf,
                    box=Box(x1=x1, y1=y1, x2=x2, y2=y2),
                )
            )
        return detections


class YOLODetector:
    """Ultralytics YOLO adapter returning normalized Detection objects."""

    def __init__(self, model_path: str = "yolov8n.pt") -> None:
        from ultralytics import YOLO  # optional runtime dependency

        self.model = YOLO(model_path)

    def detect(self, frame: object) -> Sequence[Detection]:
        result = self.model(frame, verbose=False)[0]
        return YOLOObjectAdapter.from_result(result, self.model.names)
