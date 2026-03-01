from safestep.decision import DecisionOutcome
from safestep.simulation import new_simulation, step_simulation
from safestep.state_machine import SignalState


def test_normal_scenario_progresses_and_populates_agents():
    orchestrator, state = new_simulation("normal")

    for _ in range(6):
        state = step_simulation(orchestrator, state)

    assert state.tick == 6
    assert len(state.cars_eastbound) > 0
    assert len(state.cars_westbound) > 0
    assert state.ped_left_waiting + state.ped_right_waiting > 0


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
