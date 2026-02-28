from __future__ import annotations

from dataclasses import dataclass

from .controller import SignalControllerAdapter
from .decision import DecisionEngine, DecisionInput, DecisionOutcome
from .evidence import EvidenceService
from .models import EventRecord
from .supervisor import SafetySupervisor


@dataclass
class TickInput:
    ped_wait_count: int
    ped_avg_wait_s: float
    traffic_flow_rate: float
    traffic_queue_length: int
    crosswalk_occupied: bool
    emergency_vehicle_detected: bool = False
    unauthorized_step_in: bool = False
    violation_plate: str | None = None


class SafeStepOrchestrator:
    def __init__(
        self,
        decision_engine: DecisionEngine | None = None,
        controller: SignalControllerAdapter | None = None,
        evidence: EvidenceService | None = None,
        supervisor: SafetySupervisor | None = None,
    ) -> None:
        self.decision_engine = decision_engine or DecisionEngine()
        self.controller = controller or SignalControllerAdapter()
        self.evidence = evidence or EvidenceService()
        self.supervisor = supervisor or SafetySupervisor()

    def process_tick(self, signal: TickInput) -> DecisionOutcome:
        if self.supervisor.should_enter_failsafe():
            self.controller.enter_failsafe()
            return DecisionOutcome.HOLD_VEHICLE_GREEN

        decision = self.decision_engine.decide(
            DecisionInput(
                ped_wait_count=signal.ped_wait_count,
                ped_avg_wait_s=signal.ped_avg_wait_s,
                traffic_flow_rate=signal.traffic_flow_rate,
                traffic_queue_length=signal.traffic_queue_length,
                crosswalk_occupied=signal.crosswalk_occupied,
                emergency_vehicle_detected=signal.emergency_vehicle_detected,
                unauthorized_step_in=signal.unauthorized_step_in,
            )
        )

        if decision == DecisionOutcome.REQUEST_PED_PHASE:
            self.controller.request_ped_phase()
        elif decision == DecisionOutcome.FORCE_ALL_RED:
            self.controller.force_all_red()
        elif decision == DecisionOutcome.SUSPEND_CROSSING:
            self.controller.suspend_ped_service()

        if signal.violation_plate:
            encrypted = self.evidence.encrypt_identifier(signal.violation_plate)
            self.evidence.log_event(
                EventRecord(
                    event_type="crosswalk_violation",
                    confidence=0.95,
                    encrypted_identifier=encrypted,
                    details={"source": "orchestrator"},
                )
            )

        return decision
