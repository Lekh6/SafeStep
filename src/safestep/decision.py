from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DecisionOutcome(str, Enum):
    HOLD_VEHICLE_GREEN = "hold_vehicle_green"
    REQUEST_PED_PHASE = "request_ped_phase"
    FORCE_ALL_RED = "force_all_red"
    SUSPEND_CROSSING = "suspend_crossing"


@dataclass
class DecisionInput:
    ped_wait_count: int
    ped_avg_wait_s: float
    traffic_flow_rate: float
    traffic_queue_length: int
    crosswalk_occupied: bool
    emergency_vehicle_detected: bool = False
    unauthorized_step_in: bool = False
    pedestrian_density: float = 0.0
    traffic_density: float = 0.0


@dataclass
class DecisionConfig:
    base_ped_threshold: float = 25.0
    ped_count_weight: float = 2.0
    ped_wait_weight: float = 0.25
    ped_density_weight: float = 300.0
    traffic_density_weight: float = 300.0
    ped_priority_weight: float = 1.0
    traffic_priority_weight: float = 0.6
    traffic_suspend_threshold: float = 120.0
    min_ped_threshold: float = 1.0


class DecisionEngine:
    def __init__(self, config: DecisionConfig | None = None) -> None:
        self.config = config or DecisionConfig()

    def ped_threshold(self, ped_wait_count: int, ped_avg_wait_s: float, pedestrian_density: float = 0.0) -> float:
        threshold = (
            self.config.base_ped_threshold
            - self.config.ped_count_weight * ped_wait_count
            - self.config.ped_wait_weight * ped_avg_wait_s
            - self.config.ped_density_weight * pedestrian_density
        )
        return max(self.config.min_ped_threshold, threshold)

    def pedestrian_pressure(self, ped_wait_count: int, ped_avg_wait_s: float, pedestrian_density: float = 0.0) -> float:
        return ped_wait_count * 5 + ped_avg_wait_s + (self.config.ped_density_weight * pedestrian_density)

    def traffic_pressure(self, traffic_flow_rate: float, traffic_queue_length: int, traffic_density: float = 0.0) -> float:
        return traffic_flow_rate + (traffic_queue_length * 8) + (self.config.traffic_density_weight * traffic_density)

    def decide(self, signal: DecisionInput) -> DecisionOutcome:
        if signal.unauthorized_step_in:
            return DecisionOutcome.FORCE_ALL_RED
        if signal.emergency_vehicle_detected:
            return DecisionOutcome.FORCE_ALL_RED
        if signal.crosswalk_occupied:
            return DecisionOutcome.HOLD_VEHICLE_GREEN

        t_pressure = self.traffic_pressure(
            signal.traffic_flow_rate,
            signal.traffic_queue_length,
            signal.traffic_density,
        )
        if t_pressure >= self.config.traffic_suspend_threshold:
            return DecisionOutcome.SUSPEND_CROSSING

        p_pressure = self.pedestrian_pressure(
            signal.ped_wait_count,
            signal.ped_avg_wait_s,
            signal.pedestrian_density,
        )
        threshold = self.ped_threshold(
            signal.ped_wait_count,
            signal.ped_avg_wait_s,
            signal.pedestrian_density,
        )

        weighted_score = (
            self.config.ped_priority_weight * p_pressure
            - self.config.traffic_priority_weight * t_pressure
        )

        if weighted_score >= threshold:
            return DecisionOutcome.REQUEST_PED_PHASE
        return DecisionOutcome.HOLD_VEHICLE_GREEN
