from __future__ import annotations

from dataclasses import dataclass

from .controller import SignalControllerAdapter
from .decision import DecisionEngine, DecisionInput, DecisionOutcome
from .dispatch import DispatchService
from .evidence import EvidenceService
from .models import EventRecord, PedSignal
from .state_machine import SignalState, SignalStateMachine
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
    pedestrian_density: float = 0.0
    traffic_density: float = 0.0
    vehicles_in_crosswalk: int = 0
    violation_plate: str | None = None
    pedestrian_collision_detected: bool = False
    collision_location: str | None = None
    collision_plate: str | None = None
    dt_s: float = 1.0


class SafeStepOrchestrator:
    def __init__(
        self,
        decision_engine: DecisionEngine | None = None,
        controller: SignalControllerAdapter | None = None,
        evidence: EvidenceService | None = None,
        supervisor: SafetySupervisor | None = None,
        dispatch: DispatchService | None = None,
        state_machine: SignalStateMachine | None = None,
    ) -> None:
        self.decision_engine = decision_engine or DecisionEngine()
        self.controller = controller or SignalControllerAdapter()
        self.evidence = evidence or EvidenceService()
        self.supervisor = supervisor or SafetySupervisor()
        self.dispatch = dispatch or DispatchService()
        self.state_machine = state_machine or SignalStateMachine()

    def _log_violation(self, plate: str | None, source: str) -> None:
        encrypted = self.evidence.encrypt_identifier(plate or "UNKNOWN")
        self.evidence.log_event(
            EventRecord(
                event_type="crosswalk_violation",
                confidence=0.95 if plate else 0.7,
                encrypted_identifier=encrypted,
                details={"source": source},
            )
        )

    def _handle_pedestrian_collision(self, location: str | None, plate: str | None) -> None:
        encrypted = self.evidence.encrypt_identifier(plate) if plate else None
        self.evidence.log_event(
            EventRecord(
                event_type="pedestrian_collision",
                confidence=0.9,
                encrypted_identifier=encrypted,
                details={"location": location or self.dispatch.config.default_location},
            )
        )
        self.dispatch.dispatch_pedestrian_collision(
            location=location,
            encrypted_plate=encrypted,
        )

    def process_tick(self, signal: TickInput) -> DecisionOutcome:
        if self.supervisor.should_enter_failsafe():
            self.controller.enter_failsafe()
            return DecisionOutcome.HOLD_VEHICLE_GREEN

        current_state = self.state_machine.tick(signal.dt_s, signal.crosswalk_occupied)
        if current_state == SignalState.VEHICLE_GREEN and self.controller.state.ped_signal == PedSignal.WALK:
            self.controller.set_state(SignalState.VEHICLE_GREEN)

        if signal.pedestrian_collision_detected:
            self._handle_pedestrian_collision(
                location=signal.collision_location,
                plate=signal.collision_plate,
            )
            self.state_machine.force_all_red()
            self.controller.set_state(SignalState.ALL_RED)
            return DecisionOutcome.FORCE_ALL_RED

        decision = self.decision_engine.decide(
            DecisionInput(
                ped_wait_count=signal.ped_wait_count,
                ped_avg_wait_s=signal.ped_avg_wait_s,
                traffic_flow_rate=signal.traffic_flow_rate,
                traffic_queue_length=signal.traffic_queue_length,
                crosswalk_occupied=signal.crosswalk_occupied,
                emergency_vehicle_detected=signal.emergency_vehicle_detected,
                unauthorized_step_in=signal.unauthorized_step_in,
                pedestrian_density=signal.pedestrian_density,
                traffic_density=signal.traffic_density,
            )
        )

        if decision == DecisionOutcome.REQUEST_PED_PHASE:
            ped_pressure = signal.ped_wait_count * 5 + signal.ped_avg_wait_s
            self.state_machine.start_pedestrian_phase(ped_pressure=ped_pressure)
            self.controller.set_state(SignalState.PEDESTRIAN_GREEN)
        elif decision == DecisionOutcome.FORCE_ALL_RED:
            self.state_machine.force_all_red()
            self.controller.set_state(SignalState.ALL_RED)
        elif decision == DecisionOutcome.SUSPEND_CROSSING:
            self.controller.suspend_ped_service()

        if signal.violation_plate:
            self._log_violation(signal.violation_plate, source="plate_input")

        if (
            signal.vehicles_in_crosswalk > 0
            and self.controller.state.ped_signal == PedSignal.WALK
        ):
            self._log_violation(signal.violation_plate, source="auto_crosswalk_intrusion")
            self.state_machine.force_all_red()
            self.controller.set_state(SignalState.ALL_RED)
            return DecisionOutcome.FORCE_ALL_RED

        return decision
