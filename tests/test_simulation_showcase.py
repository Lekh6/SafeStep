from safestep.decision import DecisionOutcome
from safestep.simulation import new_simulation, seek_simulation, step_simulation
from safestep.state_machine import SignalState


def test_normal_scenario_progresses_and_populates_agents():
    orchestrator, state = new_simulation("normal")

    for _ in range(6):
        state = step_simulation(orchestrator, state)

    assert state.tick == 6
    assert len(state.cars_eastbound) > 0
    assert len(state.cars_westbound) > 0
    assert state.ped_left_waiting >= 0
    assert state.ped_right_waiting >= 0
    assert isinstance(state.ped_left_waiting, int)
    assert isinstance(state.ped_right_waiting, int)


def test_visible_car_count_is_frame_limited_and_queues_track_pileup():
    orchestrator, state = new_simulation("heavy")

    for _ in range(20):
        state = step_simulation(orchestrator, state)

    assert len(state.cars_eastbound) <= 4
    assert len(state.cars_westbound) <= 4
    assert state.queue_eastbound >= 0
    assert state.queue_westbound >= 0


def test_seek_simulation_supports_reverse_time_controls():
    orchestrator, state = seek_simulation("normal", 25)
    rewound_orchestrator, rewound_state = seek_simulation("normal", 15)

    assert state.tick == 25
    assert rewound_state.tick == 15
    assert orchestrator.state_machine.state in SignalState
    assert rewound_orchestrator.state_machine.state in SignalState


def test_fall_scenario_forces_all_red_using_core_rules():
    orchestrator, state = new_simulation("fall")

    for _ in range(13):
        state = step_simulation(orchestrator, state)

    assert state.last_outcome == DecisionOutcome.FORCE_ALL_RED
    assert orchestrator.state_machine.state == SignalState.ALL_RED


def test_emergency_scenario_forces_all_red_using_core_rules():
    orchestrator, state = new_simulation("emergency")

    for _ in range(11):
        state = step_simulation(orchestrator, state)

    assert state.last_outcome == DecisionOutcome.FORCE_ALL_RED
    assert orchestrator.state_machine.state == SignalState.ALL_RED
