from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence


@dataclass
class Box:
    x1: float
    y1: float
    x2: float
    y2: float


@dataclass
class Detection:
    label: str
    confidence: float
    box: Box


@dataclass
class Track:
    track_id: int
    label: str
    box: Box
    age: int = 0
    hits: int = 1


def iou(a: Box, b: Box) -> float:
    inter_x1 = max(a.x1, b.x1)
    inter_y1 = max(a.y1, b.y1)
    inter_x2 = min(a.x2, b.x2)
    inter_y2 = min(a.y2, b.y2)
    iw = max(0.0, inter_x2 - inter_x1)
    ih = max(0.0, inter_y2 - inter_y1)
    inter = iw * ih
    if inter == 0:
        return 0.0
    area_a = (a.x2 - a.x1) * (a.y2 - a.y1)
    area_b = (b.x2 - b.x1) * (b.y2 - b.y1)
    union = max(area_a + area_b - inter, 1e-6)
    return inter / union


class SimpleTracker:
    """Lightweight IoU tracker; replace with ByteTrack/DeepSORT in production."""

    def __init__(self, match_threshold: float = 0.3, max_age: int = 10) -> None:
        self.match_threshold = match_threshold
        self.max_age = max_age
        self._next_id = 1
        self._tracks: List[Track] = []

    def update(self, detections: Sequence[Detection]) -> List[Track]:
        for tr in self._tracks:
            tr.age += 1

        for det in detections:
            best = None
            best_iou = 0.0
            for tr in self._tracks:
                if tr.label != det.label:
                    continue
                score = iou(tr.box, det.box)
                if score > best_iou:
                    best = tr
                    best_iou = score

            if best and best_iou >= self.match_threshold:
                best.box = det.box
                best.age = 0
                best.hits += 1
            else:
                self._tracks.append(
                    Track(track_id=self._next_id, label=det.label, box=det.box)
                )
                self._next_id += 1

        self._tracks = [t for t in self._tracks if t.age <= self.max_age]
        return list(self._tracks)
