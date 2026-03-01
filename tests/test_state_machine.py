from safestep.controller import CommandStatus, SignalControllerAdapter
from safestep.state_machine import SignalState, SignalStateMachine, TimingPolicy


def test_state_machine_respects_min_and_max_pedestrian_time() -> None:
    sm = SignalStateMachine(
        TimingPolicy(base_walk_s=30, clearance_s=10, min_pedestrian_s=20, max_pedestrian_s=60)
    )
    sm.start_pedestrian_phase(ped_pressure=5)

    assert sm.state == SignalState.PEDESTRIAN_GREEN

    sm.tick(10, crosswalk_occupied=False)
    assert sm.state == SignalState.PEDESTRIAN_GREEN

    sm.tick(20, crosswalk_occupied=False)
    assert sm.state in {SignalState.PEDESTRIAN_GREEN, SignalState.VEHICLE_GREEN}

    sm.tick(60, crosswalk_occupied=True)
    assert sm.state == SignalState.VEHICLE_GREEN


def test_mock_controller_returns_ack_for_state_changes() -> None:
    controller = SignalControllerAdapter()

    result = controller.set_state(SignalState.PEDESTRIAN_GREEN)
    assert result.status == CommandStatus.ACK
    assert controller.state.ped_signal.value == "walk"

    result = controller.set_state(SignalState.ALL_RED)
    assert result.status == CommandStatus.ACK
    assert controller.state.vehicle_phase == "red"
