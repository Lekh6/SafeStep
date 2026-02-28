from safestep.decision import DecisionEngine, DecisionInput, DecisionOutcome


def test_unauthorized_step_in_forces_all_red() -> None:
    engine = DecisionEngine()
    outcome = engine.decide(
        DecisionInput(
            ped_wait_count=1,
            ped_avg_wait_s=1,
            traffic_flow_rate=20,
            traffic_queue_length=2,
            crosswalk_occupied=False,
            unauthorized_step_in=True,
        )
    )
    assert outcome == DecisionOutcome.FORCE_ALL_RED


def test_high_traffic_suspends_crossing() -> None:
    engine = DecisionEngine()
    outcome = engine.decide(
        DecisionInput(
            ped_wait_count=8,
            ped_avg_wait_s=50,
            traffic_flow_rate=90,
            traffic_queue_length=5,
            crosswalk_occupied=False,
            traffic_density=0.03,
        )
    )
    assert outcome == DecisionOutcome.SUSPEND_CROSSING


def test_pedestrian_pressure_requests_crossing() -> None:
    engine = DecisionEngine()
    outcome = engine.decide(
        DecisionInput(
            ped_wait_count=10,
            ped_avg_wait_s=80,
            traffic_flow_rate=15,
            traffic_queue_length=1,
            crosswalk_occupied=False,
            pedestrian_density=0.02,
        )
    )
    assert outcome == DecisionOutcome.REQUEST_PED_PHASE
