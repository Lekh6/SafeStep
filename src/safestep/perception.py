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

    @property
    def area(self) -> float:
        return max(1.0, (self.x2 - self.x1) * (self.y2 - self.y1))

    def contains_box_center(self, box: Box) -> bool:
        cx = (box.x1 + box.x2) / 2
        cy = (box.y1 + box.y2) / 2
        return self.x1 <= cx <= self.x2 and self.y1 <= cy <= self.y2


@dataclass
class PerceptionFrame:
    tracks: List[Track]
    waiting_pedestrians: int
    approaching_pedestrians: int
    crosswalk_occupied: bool
    vehicles_in_crosswalk: int
    emergency_vehicle_detected: bool
    vehicles_in_approach: int
    pedestrian_density: float
    traffic_density: float


class PerceptionEngine:
    """Detector + tracker wrapper; detector can be YOLOv8-backed in production."""

    def __init__(
        self,
        detector: Detector | None = None,
        tracker: SimpleTracker | None = None,
        wait_zones: Iterable[Zone] = (),
        approach_zones: Iterable[Zone] = (),
        crosswalk_zone: Zone | None = None,
        traffic_zones: Iterable[Zone] = (),
    ) -> None:
        self.detector = detector
        self.tracker = tracker or SimpleTracker()
        self.wait_zones = list(wait_zones)
        self.approach_zones = list(approach_zones)
        self.crosswalk_zone = crosswalk_zone
        self.traffic_zones = list(traffic_zones)

    @staticmethod
    def _density(count: int, total_area: float) -> float:
        return round(count / max(total_area, 1.0), 6)

    def process(self, frame: object) -> PerceptionFrame:
        if self.detector is None:
            raise RuntimeError("PerceptionEngine.detector is not configured for frame-based processing")
        detections = self.detector.detect(frame)
        return self.process_detections(detections)

    def process_detections(self, detections: Sequence[Detection]) -> PerceptionFrame:
        tracks = self.tracker.update(detections)

        waiting = 0
        approaching = 0
        crosswalk_occ = False
        vehicles_in_crosswalk = 0
        emergency_seen = False
        vehicles = 0

        for tr in tracks:
            if tr.label == "pedestrian":
                in_wait_zone = any(zone.contains_box_center(tr.box) for zone in self.wait_zones)
                in_approach_zone = any(zone.contains_box_center(tr.box) for zone in self.approach_zones)
                if in_wait_zone:
                    waiting += 1
                elif in_approach_zone:
                    approaching += 1
                if self.crosswalk_zone and self.crosswalk_zone.contains_box_center(tr.box):
                    crosswalk_occ = True

            if tr.label in {"car", "truck", "bus"}:
                in_traffic = True
                if self.traffic_zones:
                    in_traffic = any(zone.contains_box_center(tr.box) for zone in self.traffic_zones)
                if in_traffic:
                    vehicles += 1
                if self.crosswalk_zone and self.crosswalk_zone.contains_box_center(tr.box):
                    vehicles_in_crosswalk += 1

            if tr.label in {"ambulance", "fire_truck", "police_car"}:
                emergency_seen = True

        wait_area = sum(zone.area for zone in self.wait_zones) if self.wait_zones else 1.0
        approach_area = sum(zone.area for zone in self.approach_zones) if self.approach_zones else 0.0
        traffic_area = sum(zone.area for zone in self.traffic_zones) if self.traffic_zones else 1.0

        ped_density = self._density(waiting + approaching, wait_area + approach_area if (wait_area + approach_area) > 0 else 1.0)

        return PerceptionFrame(
            tracks=tracks,
            waiting_pedestrians=waiting,
            approaching_pedestrians=approaching,
            crosswalk_occupied=crosswalk_occ,
            vehicles_in_crosswalk=vehicles_in_crosswalk,
            emergency_vehicle_detected=emergency_seen,
            vehicles_in_approach=vehicles,
            pedestrian_density=ped_density,
            traffic_density=self._density(vehicles, traffic_area),
        )
