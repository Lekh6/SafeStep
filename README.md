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
- **Pitch prototype**: scenario replay module + Streamlit dashboard (`prototype.py`, `app.py`)

## Quick start

```bash
python -m pip install -U pytest
pytest -q
```

## Pitch demo (prototype)

```bash
python -m pip install -U streamlit pandas
PYTHONPATH=src streamlit run app.py
```

This dashboard replays a prebuilt scenario that demonstrates:

- Pedestrian demand-based walk requests
- Violation evidence logging
- Emergency vehicle all-red handling
- Unauthorized step-in emergency all-red behavior

## Notes

- OpenCV, Ultralytics, and Streamlit are optional runtime dependencies for demo/live operation and are not required for unit tests.
- `SimpleTracker` is intentionally lightweight; production deployments should replace it with ByteTrack or DeepSORT.
