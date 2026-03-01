from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Protocol

from .models import CrossingState, Mode, PedSignal
from .state_machine import SignalState


class CommandStatus(str, Enum):
    ACK = "ACK"
    NACK = "NACK"


@dataclass
class CommandResult:
    status: CommandStatus
    command: str
    message: str = ""


class SignalController(Protocol):
    def set_state(self, state: SignalState) -> CommandResult:
        ...


@dataclass
class CommandLog:
    commands: List[str] = field(default_factory=list)


class SignalControllerAdapter:
    """Mock controller adapter with abstract state API and ACK/NACK simulation."""

    def __init__(self) -> None:
        self.state = CrossingState()
        self.log = CommandLog()

    def set_state(self, state: SignalState) -> CommandResult:
        if state == SignalState.PEDESTRIAN_GREEN:
            self.request_ped_phase()
            return CommandResult(status=CommandStatus.ACK, command="set_state:pedestrian_green")
        if state == SignalState.ALL_RED:
            self.force_all_red()
            return CommandResult(status=CommandStatus.ACK, command="set_state:all_red")
        if state == SignalState.VEHICLE_GREEN:
            self.resume_normal_operation()
            return CommandResult(status=CommandStatus.ACK, command="set_state:vehicle_green")
        return CommandResult(status=CommandStatus.NACK, command="set_state", message="unknown state")

    def request_ped_phase(self) -> None:
        self.log.commands.append("request_ped_phase")
        self.state.ped_signal = PedSignal.WALK
        self.state.vehicle_phase = "red"

    def force_all_red(self) -> None:
        self.log.commands.append("force_all_red")
        self.state.mode = Mode.EMERGENCY
        self.state.ped_signal = PedSignal.DONT_WALK
        self.state.vehicle_phase = "red"

    def suspend_ped_service(self) -> None:
        self.log.commands.append("suspend_ped_service")
        self.state.mode = Mode.SUSPENDED
        self.state.ped_signal = PedSignal.DONT_WALK

    def resume_normal_operation(self) -> None:
        self.log.commands.append("resume_normal_operation")
        self.state.mode = Mode.NORMAL
        self.state.vehicle_phase = "green"

    def enter_failsafe(self) -> None:
        self.log.commands.append("enter_failsafe")
        self.state.mode = Mode.FAILSAFE
        self.state.ped_signal = PedSignal.DONT_WALK
        self.state.vehicle_phase = "controller_automatic"
