from safestep.decision import DecisionOutcome
from safestep.orchestrator import SafeStepOrchestrator
from safestep.perception import PerceptionEngine, Zone
from safestep.runtime import SafeStepRuntime
from safestep.tracking import Box, Detection


class FakeDetector:
    def __init__(self, detections):
        self._detections = detections

    def detect(self, frame):
        return self._detections


class FailingDetector:
    def detect(self, frame):
        raise RuntimeError("camera down")


def test_perception_counts_waiting_and_emergency() -> None:
    detector = FakeDetector(
        [
            Detection("pedestrian", 0.9, Box(10, 10, 20, 20)),
            Detection("ambulance", 0.8, Box(40, 40, 80, 80)),
            Detection("car", 0.95, Box(100, 100, 150, 150)),
        ]
    )
    engine = PerceptionEngine(
        detector=detector,
        wait_zones=[Zone("left", 0, 0, 30, 30)],
        crosswalk_zone=Zone("crosswalk", 0, 0, 25, 25),
    )

    frame = engine.process(object())
    assert frame.waiting_pedestrians == 1
    assert frame.crosswalk_occupied is True
    assert frame.emergency_vehicle_detected is True
    assert frame.vehicles_in_approach == 1


def test_runtime_fallbacks_to_timer_mode_on_camera_failure() -> None:
    engine = PerceptionEngine(detector=FailingDetector())
    runtime = SafeStepRuntime(perception=engine, orchestrator=SafeStepOrchestrator())

    out = runtime.process_frame(object())

    assert out.fallback_timer_mode is True
    assert out.outcome == DecisionOutcome.HOLD_VEHICLE_GREEN
    assert "resume_normal_operation" in runtime.orchestrator.controller.log.commands
