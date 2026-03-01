from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .adapters import YOLOObjectAdapter
from .decision import DecisionOutcome
from .orchestrator import SafeStepOrchestrator, TickInput
from .perception import PerceptionEngine
from .tracking import Detection


@dataclass
class RuntimeOutput:
    outcome: DecisionOutcome
    fallback_timer_mode: bool


class SafeStepRuntime:
    """End-to-end runtime loop glue for perception and control logic."""

    def __init__(self, perception: PerceptionEngine, orchestrator: SafeStepOrchestrator) -> None:
        self.perception = perception
        self.orchestrator = orchestrator

    def _to_tick_input(
        self,
        ped_avg_wait_s: float,
        waiting: int,
        vehicles: int,
        occupied: bool,
        emergency: bool,
        pedestrian_density: float,
        traffic_density: float,
        vehicles_in_crosswalk: int,
    ) -> TickInput:
        return TickInput(
            ped_wait_count=waiting,
            ped_avg_wait_s=ped_avg_wait_s,
            traffic_flow_rate=float(vehicles * 10),
            traffic_queue_length=vehicles,
            crosswalk_occupied=occupied,
            emergency_vehicle_detected=emergency,
            pedestrian_density=pedestrian_density,
            traffic_density=traffic_density,
            vehicles_in_crosswalk=vehicles_in_crosswalk,
        )

    def process_frame(self, frame: object, ped_avg_wait_s: float = 0.0) -> RuntimeOutput:
        try:
            perception = self.perception.process(frame)
        except Exception:
            self.orchestrator.controller.resume_normal_operation()
            return RuntimeOutput(
                outcome=DecisionOutcome.HOLD_VEHICLE_GREEN,
                fallback_timer_mode=True,
            )

        outcome = self.orchestrator.process_tick(
            self._to_tick_input(
                ped_avg_wait_s=ped_avg_wait_s,
                waiting=perception.waiting_pedestrians,
                vehicles=perception.vehicles_in_approach,
                occupied=perception.crosswalk_occupied,
                emergency=perception.emergency_vehicle_detected,
                pedestrian_density=perception.pedestrian_density,
                traffic_density=perception.traffic_density,
                vehicles_in_crosswalk=perception.vehicles_in_crosswalk,
            )
        )
        return RuntimeOutput(outcome=outcome, fallback_timer_mode=False)

    def process_detections(
        self,
        detections: Sequence[Detection],
        ped_avg_wait_s: float = 0.0,
    ) -> RuntimeOutput:
        perception = self.perception.process_detections(detections)
        outcome = self.orchestrator.process_tick(
            self._to_tick_input(
                ped_avg_wait_s=ped_avg_wait_s,
                waiting=perception.waiting_pedestrians,
                vehicles=perception.vehicles_in_approach,
                occupied=perception.crosswalk_occupied,
                emergency=perception.emergency_vehicle_detected,
                pedestrian_density=perception.pedestrian_density,
                traffic_density=perception.traffic_density,
                vehicles_in_crosswalk=perception.vehicles_in_crosswalk,
            )
        )
        return RuntimeOutput(outcome=outcome, fallback_timer_mode=False)

    def process_yolo_result(
        self,
        yolo_result: Any,
        names: Mapping[int, str] | Sequence[str] | None = None,
        ped_avg_wait_s: float = 0.0,
    ) -> RuntimeOutput:
        detections = YOLOObjectAdapter.from_result(yolo_result, names=names)
        return self.process_detections(detections=detections, ped_avg_wait_s=ped_avg_wait_s)
