from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import List


@dataclass
class SignalDeployment:
    signal_id: str
    location: str
    controller_endpoint: str
    emergency_contact: str
    camera_ids: List[str] = field(default_factory=list)


@dataclass
class CameraConnection:
    camera_id: str
    connected: bool


class DeploymentRegistry:
    """File-backed deployment registry for admin configuration."""

    def __init__(self, path: str | Path = "data/deployments.json") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _read_all(self) -> List[SignalDeployment]:
        if not self.path.exists():
            return []
        raw = json.loads(self.path.read_text())
        return [SignalDeployment(**item) for item in raw]

    def _write_all(self, deployments: List[SignalDeployment]) -> None:
        self.path.write_text(json.dumps([asdict(d) for d in deployments], indent=2))

    def list_deployments(self) -> List[SignalDeployment]:
        return self._read_all()

    def add_deployment(self, deployment: SignalDeployment) -> None:
        deployments = self._read_all()
        deployments = [d for d in deployments if d.signal_id != deployment.signal_id]
        deployments.append(deployment)
        self._write_all(deployments)

    def get_camera_connections(self, signal_id: str) -> List[CameraConnection]:
        deployments = self._read_all()
        deployment = next((d for d in deployments if d.signal_id == signal_id), None)
        if deployment is None:
            return []
        return [CameraConnection(camera_id=cid, connected=bool(cid.strip())) for cid in deployment.camera_ids]
