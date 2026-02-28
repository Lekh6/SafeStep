# SafeStep

SafeStep is a Python-first orchestration core for camera-driven pedestrian crossing control.

## Implemented stack

- **Core language**: Python
- **CV adapters**: OpenCV video source, Ultralytics YOLO detector adapter (`adapters.py`)
- **Tracking**: pluggable tracker interface with lightweight IoU tracker scaffold (`tracking.py`) ready to swap for ByteTrack/DeepSORT
- **Signal logic**: state-machine style orchestration (`orchestrator.py`, `controller.py`)
- **Accident heuristic**: overlap + sudden-stop detection (`accident.py`)
- **Emergency handling**: emergency vehicle class integration in perception + all-red decision path
- **Encryption**: AES-GCM plate encryption via `cryptography` when available (`security.py`, `evidence.py`)
- **Fail-safe**: runtime fallback to timer/normal controller mode if camera processing fails (`runtime.py`)

## Quick start

```bash
python -m pip install -U pytest
pytest -q
```

## Notes

- OpenCV and Ultralytics are optional runtime dependencies for live operation and are not required for unit tests.
- `SimpleTracker` is intentionally lightweight; production deployments should replace it with ByteTrack or DeepSORT.
