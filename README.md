# SafeStep

SafeStep is a Python-first orchestration core for camera-driven pedestrian crossing control.

## Implemented stack

- **Core language**: Python
- **YOLO integration**: Ultralytics adapter + YOLO object converter (`adapters.py`)
- **Perception**: zone-based pedestrian and traffic analysis with density metrics and approach-zone support (`perception.py`)
- **Tracking**: pluggable tracker interface with lightweight IoU tracker scaffold (`tracking.py`) ready to swap for ByteTrack/DeepSORT
- **Signal logic**: state-machine style orchestration (`orchestrator.py`, `controller.py`)
- **Safety logic**: unauthorized step-in all-red, emergency-vehicle all-red, automatic crosswalk-intrusion violation logging
- **Collision handling**: pedestrian-collision dispatch flow with admin-configurable emergency contact (`dispatch.py`)
- **Encryption**: AES-GCM plate encryption via `cryptography` when available (`security.py`, `evidence.py`)
- **Fail-safe**: runtime fallback to timer/normal controller mode if frame processing fails (`runtime.py`)

## Quick start

```bash
python -m pip install -U pytest
pytest -q
```

## On-demand YOLO usage (no webcam required)

SafeStep can accept YOLO results directly at runtime:

```python
from safestep.orchestrator import SafeStepOrchestrator
from safestep.perception import PerceptionEngine, Zone
from safestep.runtime import SafeStepRuntime

engine = PerceptionEngine(
    wait_zones=[Zone("left", 0, 0, 200, 200), Zone("right", 300, 0, 500, 200)],
    approach_zones=[Zone("left_near", 0, 200, 200, 300)],
    traffic_zones=[Zone("lane", 0, 200, 500, 500)],
    crosswalk_zone=Zone("crosswalk", 200, 200, 300, 300),
)
runtime = SafeStepRuntime(perception=engine, orchestrator=SafeStepOrchestrator())

# yolo_result is an ultralytics Results item (e.g. results[0])
out = runtime.process_yolo_result(yolo_result, ped_avg_wait_s=12)
print(out.outcome)
```

## Notes

- OpenCV and Ultralytics are optional runtime dependencies and are not required for unit tests.
- `SimpleTracker` is intentionally lightweight; production deployments should replace it with ByteTrack or DeepSORT.
- Accident-specific vehicle kinematics logic has been intentionally removed; pedestrian-collision dispatch is the supported incident path.
