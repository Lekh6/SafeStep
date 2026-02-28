from safestep.decision import DecisionOutcome
from safestep.prototype import DEFAULT_PITCH_SCENARIO, run_pitch_scenario


def test_run_pitch_scenario_generates_timeline() -> None:
    results = run_pitch_scenario()
    assert len(results) == len(DEFAULT_PITCH_SCENARIO)
    assert results[0].second == 0


def test_pitch_scenario_contains_safety_critical_outcomes() -> None:
    results = run_pitch_scenario()
    outcomes = {result.outcome for result in results}
    assert DecisionOutcome.REQUEST_PED_PHASE in outcomes
    assert DecisionOutcome.FORCE_ALL_RED in outcomes
    assert results[-1].event_count >= 1
