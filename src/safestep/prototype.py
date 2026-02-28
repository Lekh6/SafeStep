from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .decision import DecisionOutcome
from .orchestrator import SafeStepOrchestrator, TickInput


@dataclass
class PrototypeTick:
    second: int
    ped_wait_count: int
    ped_avg_wait_s: float
    traffic_flow_rate: float
    traffic_queue_length: int
    crosswalk_occupied: bool
    emergency_vehicle_detected: bool = False
    unauthorized_step_in: bool = False
    violation_plate: str | None = None


@dataclass
class PrototypeResult:
    second: int
    outcome: DecisionOutcome
    mode: str
    ped_signal: str
    vehicle_phase: str
    event_count: int


DEFAULT_PITCH_SCENARIO: List[PrototypeTick] = [
    PrototypeTick(second=0, ped_wait_count=1, ped_avg_wait_s=5, traffic_flow_rate=30, traffic_queue_length=2, crosswalk_occupied=False),
    PrototypeTick(second=10, ped_wait_count=4, ped_avg_wait_s=20, traffic_flow_rate=35, traffic_queue_length=3, crosswalk_occupied=False),
    PrototypeTick(second=20, ped_wait_count=8, ped_avg_wait_s=45, traffic_flow_rate=28, traffic_queue_length=2, crosswalk_occupied=False),
    PrototypeTick(second=30, ped_wait_count=5, ped_avg_wait_s=10, traffic_flow_rate=25, traffic_queue_length=1, crosswalk_occupied=True, violation_plate="PITCH123"),
    PrototypeTick(second=40, ped_wait_count=1, ped_avg_wait_s=5, traffic_flow_rate=20, traffic_queue_length=1, crosswalk_occupied=False, emergency_vehicle_detected=True),
    PrototypeTick(second=50, ped_wait_count=0, ped_avg_wait_s=0, traffic_flow_rate=18, traffic_queue_length=1, crosswalk_occupied=False, unauthorized_step_in=True),
]


def run_pitch_scenario(
    ticks: List[PrototypeTick] | None = None,
    orchestrator: SafeStepOrchestrator | None = None,
) -> List[PrototypeResult]:
    scenario = ticks or DEFAULT_PITCH_SCENARIO
    orch = orchestrator or SafeStepOrchestrator()
    results: List[PrototypeResult] = []

    for tick in scenario:
        outcome = orch.process_tick(
            TickInput(
                ped_wait_count=tick.ped_wait_count,
                ped_avg_wait_s=tick.ped_avg_wait_s,
                traffic_flow_rate=tick.traffic_flow_rate,
                traffic_queue_length=tick.traffic_queue_length,
                crosswalk_occupied=tick.crosswalk_occupied,
                emergency_vehicle_detected=tick.emergency_vehicle_detected,
                unauthorized_step_in=tick.unauthorized_step_in,
                violation_plate=tick.violation_plate,
            )
        )
        results.append(
            PrototypeResult(
                second=tick.second,
                outcome=outcome,
                mode=orch.controller.state.mode.value,
                ped_signal=orch.controller.state.ped_signal.value,
                vehicle_phase=orch.controller.state.vehicle_phase,
                event_count=len(orch.evidence.events),
            )
        )

    return results
