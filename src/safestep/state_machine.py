from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SignalState(str, Enum):
    VEHICLE_GREEN = "vehicle_green"
    PEDESTRIAN_GREEN = "pedestrian_green"
    ALL_RED = "all_red"


@dataclass
class TimingPolicy:
    base_walk_s: float = 30.0
    clearance_s: float = 10.0
    min_pedestrian_s: float = 20.0
    max_pedestrian_s: float = 120.0


@dataclass
class PhaseSnapshot:
    state: SignalState
    elapsed_s: float
    required_pedestrian_s: float


class SignalStateMachine:
    """Abstract signal state machine for software-only control."""

    def __init__(self, policy: TimingPolicy | None = None) -> None:
        self.policy = policy or TimingPolicy()
        self.state = SignalState.VEHICLE_GREEN
        self.elapsed_s = 0.0
        self.required_pedestrian_s = self.policy.base_walk_s + self.policy.clearance_s

    def start_pedestrian_phase(self, ped_pressure: float = 0.0) -> SignalState:
        dynamic_walk = self.policy.base_walk_s + min(max(ped_pressure, 0.0), 40.0)
        self.required_pedestrian_s = min(
            self.policy.max_pedestrian_s,
            max(self.policy.min_pedestrian_s, dynamic_walk + self.policy.clearance_s),
        )
        self.state = SignalState.PEDESTRIAN_GREEN
        self.elapsed_s = 0.0
        return self.state

    def force_all_red(self) -> SignalState:
        self.state = SignalState.ALL_RED
        self.elapsed_s = 0.0
        return self.state

    def resume_vehicle_green(self) -> SignalState:
        self.state = SignalState.VEHICLE_GREEN
        self.elapsed_s = 0.0
        return self.state

    def tick(self, dt_s: float, crosswalk_occupied: bool) -> SignalState:
        self.elapsed_s += max(dt_s, 0.0)

        if self.state != SignalState.PEDESTRIAN_GREEN:
            return self.state

        if self.elapsed_s < self.policy.min_pedestrian_s:
            return self.state

        if self.elapsed_s >= self.policy.max_pedestrian_s:
            return self.resume_vehicle_green()

        if self.elapsed_s >= self.required_pedestrian_s and not crosswalk_occupied:
            return self.resume_vehicle_green()

        return self.state

    def snapshot(self) -> PhaseSnapshot:
        return PhaseSnapshot(
            state=self.state,
            elapsed_s=self.elapsed_s,
            required_pedestrian_s=self.required_pedestrian_s,
        )
