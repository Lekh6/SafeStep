from __future__ import annotations

from dataclasses import dataclass

from .decision import DecisionOutcome
from .orchestrator import SafeStepOrchestrator, TickInput
from .perception import PerceptionEngine


@dataclass
class RuntimeOutput:
    outcome: DecisionOutcome
    fallback_timer_mode: bool


class SafeStepRuntime:
    """End-to-end runtime loop glue for camera perception and control logic."""

    def __init__(self, perception: PerceptionEngine, orchestrator: SafeStepOrchestrator) -> None:
        self.perception = perception
        self.orchestrator = orchestrator

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
            TickInput(
                ped_wait_count=perception.waiting_pedestrians,
                ped_avg_wait_s=ped_avg_wait_s,
                traffic_flow_rate=float(perception.vehicles_in_approach * 10),
                traffic_queue_length=perception.vehicles_in_approach,
                crosswalk_occupied=perception.crosswalk_occupied,
                emergency_vehicle_detected=perception.emergency_vehicle_detected,
            )
        )
        return RuntimeOutput(outcome=outcome, fallback_timer_mode=False)
