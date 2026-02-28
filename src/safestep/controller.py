from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .models import CrossingState, Mode, PedSignal


@dataclass
class CommandLog:
    commands: List[str] = field(default_factory=list)


class SignalControllerAdapter:
    """In-memory adapter that represents cabinet integration points."""

    def __init__(self) -> None:
        self.state = CrossingState()
        self.log = CommandLog()

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
