from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Protocol, Sequence

from .tracking import Box, Detection, SimpleTracker, Track


class Detector(Protocol):
    def detect(self, frame: object) -> Sequence[Detection]:
        ...


@dataclass
class Zone:
    name: str
    x1: float
    y1: float
    x2: float
    y2: float

    def contains_box_center(self, box: Box) -> bool:
        cx = (box.x1 + box.x2) / 2
        cy = (box.y1 + box.y2) / 2
        return self.x1 <= cx <= self.x2 and self.y1 <= cy <= self.y2


@dataclass
class PerceptionFrame:
    tracks: List[Track]
    waiting_pedestrians: int
    crosswalk_occupied: bool
    emergency_vehicle_detected: bool
    vehicles_in_approach: int


class PerceptionEngine:
    """Detector + tracker wrapper; detector can be YOLOv8-backed in production."""

    def __init__(
        self,
        detector: Detector,
        tracker: SimpleTracker | None = None,
        wait_zones: Iterable[Zone] = (),
        crosswalk_zone: Zone | None = None,
    ) -> None:
        self.detector = detector
        self.tracker = tracker or SimpleTracker()
        self.wait_zones = list(wait_zones)
        self.crosswalk_zone = crosswalk_zone

    def process(self, frame: object) -> PerceptionFrame:
        detections = self.detector.detect(frame)
        tracks = self.tracker.update(detections)

        waiting = 0
        crosswalk_occ = False
        emergency_seen = False
        vehicles = 0

        for tr in tracks:
            if tr.label == "pedestrian":
                if any(zone.contains_box_center(tr.box) for zone in self.wait_zones):
                    waiting += 1
                if self.crosswalk_zone and self.crosswalk_zone.contains_box_center(tr.box):
                    crosswalk_occ = True
            if tr.label in {"car", "truck", "bus"}:
                vehicles += 1
            if tr.label in {"ambulance", "fire_truck", "police_car"}:
                emergency_seen = True

        return PerceptionFrame(
            tracks=tracks,
            waiting_pedestrians=waiting,
            crosswalk_occupied=crosswalk_occ,
            emergency_vehicle_detected=emergency_seen,
            vehicles_in_approach=vehicles,
        )
