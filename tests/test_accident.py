from safestep.accident import VehicleMotion, detect_accident
from safestep.tracking import Box


def test_detect_accident_true_on_overlap_and_sudden_stop() -> None:
    a = VehicleMotion(12, 0.5, Box(0, 0, 40, 40), Box(10, 10, 50, 50))
    b = VehicleMotion(10, 0.4, Box(30, 30, 70, 70), Box(20, 20, 60, 60))
    assert detect_accident(a, b) is True


def test_detect_accident_false_without_overlap() -> None:
    a = VehicleMotion(12, 0.5, Box(0, 0, 40, 40), Box(0, 0, 40, 40))
    b = VehicleMotion(10, 0.4, Box(80, 80, 120, 120), Box(80, 80, 120, 120))
    assert detect_accident(a, b) is False
