from safestep.adapters import YOLOObjectAdapter
from safestep.decision import DecisionOutcome
from safestep.orchestrator import SafeStepOrchestrator
from safestep.perception import PerceptionEngine, Zone
from safestep.runtime import SafeStepRuntime


class FakeScalar:
    def __init__(self, value: float) -> None:
        self._value = value

    def item(self) -> float:
        return self._value


class FakeTensorRow:
    def __init__(self, values):
        self._values = values

    def tolist(self):
        return self._values


class FakeTensor2D:
    def __init__(self, values):
        self._values = values

    def __getitem__(self, index: int):
        if index != 0:
            raise IndexError(index)
        return FakeTensorRow(self._values)


class FakeBox:
    def __init__(self, cls_id: int, conf: float, xyxy):
        self.cls = FakeScalar(cls_id)
        self.conf = FakeScalar(conf)
        self.xyxy = FakeTensor2D(xyxy)


class FakeResult:
    def __init__(self):
        self.names = {0: "pedestrian", 1: "car", 2: "ambulance"}
        self.boxes = [
            FakeBox(0, 0.95, [10, 10, 20, 20]),
            FakeBox(1, 0.88, [120, 120, 160, 160]),
            FakeBox(2, 0.91, [200, 200, 260, 260]),
        ]


class NoopDetector:
    def detect(self, frame):
        return []


def test_yolo_adapter_and_on_demand_runtime_flow() -> None:
    result = FakeResult()

    detections = YOLOObjectAdapter.from_result(result)
    assert [d.label for d in detections] == ["pedestrian", "car", "ambulance"]

    engine = PerceptionEngine(
        detector=NoopDetector(),
        wait_zones=[Zone("left_wait", 0, 0, 100, 100)],
        traffic_zones=[Zone("lane_1", 100, 100, 300, 300)],
        crosswalk_zone=Zone("xwalk", 0, 0, 50, 50),
    )
    runtime = SafeStepRuntime(perception=engine, orchestrator=SafeStepOrchestrator())

    output = runtime.process_yolo_result(result, ped_avg_wait_s=15)

    assert output.fallback_timer_mode is False
    assert output.outcome in {
        DecisionOutcome.HOLD_VEHICLE_GREEN,
        DecisionOutcome.REQUEST_PED_PHASE,
        DecisionOutcome.SUSPEND_CROSSING,
        DecisionOutcome.FORCE_ALL_RED,
    }

    perception = engine.process_detections(detections)
    assert perception.waiting_pedestrians == 1
    assert perception.vehicles_in_approach == 1
    assert perception.crosswalk_occupied is True
    assert perception.emergency_vehicle_detected is True
    assert perception.pedestrian_density == 0.0001
    assert perception.traffic_density == 0.000025
