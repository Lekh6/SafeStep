from safestep.decision import DecisionOutcome
from safestep.orchestrator import SafeStepOrchestrator, TickInput


def test_collision_triggers_dispatch_all_red_and_encrypted_plate() -> None:
    orchestrator = SafeStepOrchestrator()
    orchestrator.dispatch.update_emergency_contact("112")

    outcome = orchestrator.process_tick(
        TickInput(
            ped_wait_count=0,
            ped_avg_wait_s=0,
            traffic_flow_rate=0,
            traffic_queue_length=0,
            crosswalk_occupied=True,
            pedestrian_collision_detected=True,
            collision_location="Main St & 4th",
            collision_plate="XYZ999",
        )
    )

    assert outcome == DecisionOutcome.FORCE_ALL_RED
    assert orchestrator.controller.state.vehicle_phase == "red"
    assert len(orchestrator.dispatch.records) == 1
    dispatch_record = orchestrator.dispatch.records[0]
    assert dispatch_record.contact == "112"
    assert dispatch_record.location == "Main St & 4th"
    assert dispatch_record.encrypted_plate is not None
    assert len(orchestrator.evidence.events) == 1
    assert orchestrator.evidence.events[0].event_type == "pedestrian_collision"


def test_collision_without_plate_still_dispatches() -> None:
    orchestrator = SafeStepOrchestrator()

    outcome = orchestrator.process_tick(
        TickInput(
            ped_wait_count=0,
            ped_avg_wait_s=0,
            traffic_flow_rate=0,
            traffic_queue_length=0,
            crosswalk_occupied=True,
            pedestrian_collision_detected=True,
            collision_location="Unknown Junction",
        )
    )

    assert outcome == DecisionOutcome.FORCE_ALL_RED
    assert len(orchestrator.dispatch.records) == 1
    assert orchestrator.dispatch.records[0].encrypted_plate is None
