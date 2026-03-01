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

### Unix/macOS (bash/zsh)

```bash
python -m pip install -U pytest
pytest -q
```

### Windows (PowerShell)

```powershell
python -m pip install -U pytest
pytest -q
```

### Windows (cmd.exe)

```bat
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

## Admin deployment configuration (Streamlit)

Admins can configure live deployments directly in the dashboard:

- Log in as admin using credential **values** (defaults: username `admin`, password `admin123`).
- You can set custom values via env vars:
  - `SAFESTEP_ADMIN_USER`
  - `SAFESTEP_ADMIN_PASSWORD`
- For convenience, the login form also accepts those env var key names and resolves them to their configured values.
- Open **Deployed Signals** and add:
  - Signal ID
  - Location
  - Controller endpoint
  - Emergency contact number
  - Camera IDs
- Config is persisted in `data/deployments.json` and camera IDs are shown back under **Connected Cameras**.

Run dashboard:

### Unix/macOS (bash/zsh)

```bash
PYTHONPATH=src streamlit run app.py
```

### Windows (PowerShell)

```powershell
$env:PYTHONPATH = "src"
streamlit run app.py
```

### Windows (cmd.exe)

```bat
set PYTHONPATH=src
streamlit run app.py
```

## Abstract controller + state machine (software-only)

SafeStep now includes a protocol-agnostic control layer so hardware specifics can be plugged in later:

- `SignalState`: `VEHICLE_GREEN`, `PEDESTRIAN_GREEN`, `ALL_RED`
- `SignalStateMachine`: min/max pedestrian timing, dynamic pedestrian phase duration, and occupancy-based release
- `SignalControllerAdapter.set_state(...)`: mock ACK/NACK-style command response (`ACK` / `NACK`)

This keeps current logic simulation-ready while preserving a clean integration point for real controller adapters in the future.
