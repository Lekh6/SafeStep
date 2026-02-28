from safestep.decision import DecisionOutcome
from safestep.orchestrator import SafeStepOrchestrator, TickInput


def test_orchestrator_logs_violation_with_encrypted_plate() -> None:
    orchestrator = SafeStepOrchestrator()

    outcome = orchestrator.process_tick(
        TickInput(
            ped_wait_count=2,
            ped_avg_wait_s=10,
            traffic_flow_rate=20,
            traffic_queue_length=1,
            crosswalk_occupied=False,
            violation_plate="ABC123",
        )
    )

    assert outcome in {
        DecisionOutcome.HOLD_VEHICLE_GREEN,
        DecisionOutcome.REQUEST_PED_PHASE,
        DecisionOutcome.SUSPEND_CROSSING,
    }
    assert len(orchestrator.evidence.events) == 1
    encrypted = orchestrator.evidence.events[0].encrypted_identifier
    assert encrypted is not None
    assert encrypted != "ABC123"
    assert orchestrator.evidence.decrypt_identifier(encrypted) == "ABC123"


def test_orchestrator_enters_failsafe_after_persistent_errors() -> None:
    orchestrator = SafeStepOrchestrator()
    orchestrator.supervisor.report_error()
    orchestrator.supervisor.report_error()
    orchestrator.supervisor.report_error()

    orchestrator.process_tick(
        TickInput(
            ped_wait_count=5,
            ped_avg_wait_s=20,
            traffic_flow_rate=15,
            traffic_queue_length=1,
            crosswalk_occupied=False,
        )
    )

    assert orchestrator.controller.state.mode.value == "failsafe"
    assert "enter_failsafe" in orchestrator.controller.log.commands
