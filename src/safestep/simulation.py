from __future__ import annotations

from dataclasses import dataclass, field

from .decision import DecisionOutcome
from .models import PedSignal
from .orchestrator import SafeStepOrchestrator, TickInput
from .state_machine import SignalState


@dataclass(frozen=True)
class ScenarioConfig:
    name: str
    description: str
    traffic_spawn_per_tick: float
    pedestrian_arrival_per_tick: float
    base_traffic_flow_rate: float
    pedestrian_density_scale: float
    event_window: tuple[int, int] | None = None


SCENARIOS: dict[str, ScenarioConfig] = {
    "normal": ScenarioConfig(
        name="Normal traffic flow with low pedestrian density",
        description="Steady vehicles and light foot traffic.",
        traffic_spawn_per_tick=0.7,
        pedestrian_arrival_per_tick=0.25,
        base_traffic_flow_rate=24.0,
        pedestrian_density_scale=45.0,
    ),
    "heavy": ScenarioConfig(
        name="Heavy traffic flow with high pedestrian density",
        description="Both road and sidewalks fill quickly, often suspending crossings.",
        traffic_spawn_per_tick=1.25,
        pedestrian_arrival_per_tick=0.9,
        base_traffic_flow_rate=42.0,
        pedestrian_density_scale=25.0,
    ),
    "fall": ScenarioConfig(
        name="Pedestrian falling onto the crosswalk by mistake",
        description="At t=12s, unauthorized step-in is injected and forces all-red.",
        traffic_spawn_per_tick=0.8,
        pedestrian_arrival_per_tick=0.35,
        base_traffic_flow_rate=28.0,
        pedestrian_density_scale=40.0,
        event_window=(12, 20),
    ),
    "emergency": ScenarioConfig(
        name="Emergency vehicle passing through",
        description="At t=10s-18s, emergency detection is injected and forces all-red.",
        traffic_spawn_per_tick=0.9,
        pedestrian_arrival_per_tick=0.4,
        base_traffic_flow_rate=30.0,
        pedestrian_density_scale=35.0,
        event_window=(10, 18),
    ),
}


@dataclass
class SimulationState:
    scenario_key: str
    tick: int = 0
    ped_left_waiting: float = 0.0
    ped_right_waiting: float = 0.0
    crossing_people: float = 0.0
    cumulative_wait_s: float = 0.0
    car_spawn_budget: float = 0.0
    cars_eastbound: list[float] = field(default_factory=list)
    cars_westbound: list[float] = field(default_factory=list)
    last_outcome: DecisionOutcome = DecisionOutcome.HOLD_VEHICLE_GREEN


def new_simulation(scenario_key: str) -> tuple[SafeStepOrchestrator, SimulationState]:
    if scenario_key not in SCENARIOS:
        raise ValueError(f"unknown scenario: {scenario_key}")
    return SafeStepOrchestrator(), SimulationState(scenario_key=scenario_key)


def _move_lane(cars: list[float], speed: float, lower: float, upper: float, stop_line: float, can_move: bool) -> list[float]:
    moved: list[float] = []
    for x in sorted(cars):
        if can_move:
            nx = x + speed
        else:
            nx = min(x + speed, stop_line)
        if lower <= nx <= upper:
            moved.append(nx)
    return moved


def _scenario_events(scenario_key: str, tick: int) -> tuple[bool, bool, bool]:
    cfg = SCENARIOS[scenario_key]
    if scenario_key == "fall" and cfg.event_window:
        start, end = cfg.event_window
        return start <= tick < end, True, False
    if scenario_key == "emergency" and cfg.event_window:
        start, end = cfg.event_window
        return start <= tick < end, False, True
    return False, False, False


def step_simulation(orchestrator: SafeStepOrchestrator, state: SimulationState, dt_s: float = 1.0) -> SimulationState:
    cfg = SCENARIOS[state.scenario_key]

    ped_walk = orchestrator.controller.state.ped_signal == PedSignal.WALK
    if ped_walk:
        state.crossing_people += min(state.ped_left_waiting, 1.6)
        state.crossing_people += min(state.ped_right_waiting, 1.6)
        state.ped_left_waiting = max(0.0, state.ped_left_waiting - 1.6)
        state.ped_right_waiting = max(0.0, state.ped_right_waiting - 1.6)
    else:
        state.ped_left_waiting += cfg.pedestrian_arrival_per_tick
        state.ped_right_waiting += cfg.pedestrian_arrival_per_tick

    state.crossing_people = max(0.0, state.crossing_people - 1.4)

    state.car_spawn_budget += cfg.traffic_spawn_per_tick
    while state.car_spawn_budget >= 1.0:
        state.cars_eastbound.append(160.0)
        state.cars_westbound.append(700.0)
        state.car_spawn_budget -= 1.0

    vehicle_green = orchestrator.state_machine.state == SignalState.VEHICLE_GREEN
    state.cars_eastbound = _move_lane(state.cars_eastbound, speed=18.0, lower=140.0, upper=900.0, stop_line=392.0, can_move=vehicle_green)
    west = [-x for x in state.cars_westbound]
    west = _move_lane(west, speed=18.0, lower=-900.0, upper=-140.0, stop_line=-508.0, can_move=vehicle_green)
    state.cars_westbound = [-x for x in west]

    queue_count = sum(1 for x in state.cars_eastbound if 360 <= x <= 395) + sum(1 for x in state.cars_westbound if 505 <= x <= 540)

    ped_wait_count = int(round(state.ped_left_waiting + state.ped_right_waiting))
    if ped_wait_count > 0:
        state.cumulative_wait_s += dt_s * ped_wait_count
        ped_avg_wait_s = state.cumulative_wait_s / ped_wait_count
    else:
        ped_avg_wait_s = 0.0
        state.cumulative_wait_s = 0.0

    crosswalk_occupied, unauthorized_step_in, emergency_vehicle = _scenario_events(state.scenario_key, state.tick)
    crosswalk_occupied = crosswalk_occupied or state.crossing_people > 0.05

    traffic_density = min(1.0, (len(state.cars_eastbound) + len(state.cars_westbound)) / 42.0)
    pedestrian_density = min(1.0, ped_wait_count / cfg.pedestrian_density_scale)

    state.last_outcome = orchestrator.process_tick(
        TickInput(
            ped_wait_count=ped_wait_count,
            ped_avg_wait_s=ped_avg_wait_s,
            traffic_flow_rate=cfg.base_traffic_flow_rate,
            traffic_queue_length=queue_count,
            crosswalk_occupied=crosswalk_occupied,
            emergency_vehicle_detected=emergency_vehicle,
            unauthorized_step_in=unauthorized_step_in,
            pedestrian_density=pedestrian_density,
            traffic_density=traffic_density,
            dt_s=dt_s,
        )
    )

    state.tick += int(dt_s)
    return state
