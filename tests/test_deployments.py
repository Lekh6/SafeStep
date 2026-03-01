from pathlib import Path

from safestep.deployments import DeploymentRegistry, SignalDeployment


def test_admin_can_add_and_list_deployment(tmp_path: Path) -> None:
    registry = DeploymentRegistry(tmp_path / "deployments.json")

    registry.add_deployment(
        SignalDeployment(
            signal_id="SIG-001",
            location="Main St & 4th",
            controller_endpoint="tcp://controller.local:502",
            emergency_contact="112",
            camera_ids=["CAM-01", "CAM-02"],
        )
    )

    rows = registry.list_deployments()
    assert len(rows) == 1
    assert rows[0].signal_id == "SIG-001"
    assert rows[0].emergency_contact == "112"


def test_camera_connections_return_by_signal(tmp_path: Path) -> None:
    registry = DeploymentRegistry(tmp_path / "deployments.json")
    registry.add_deployment(
        SignalDeployment(
            signal_id="SIG-100",
            location="Park Ave",
            controller_endpoint="tcp://controller2.local:502",
            emergency_contact="911",
            camera_ids=["CAM-A", "CAM-B"],
        )
    )

    cameras = registry.get_camera_connections("SIG-100")
    assert len(cameras) == 2
    assert all(item.connected for item in cameras)
    assert {item.camera_id for item in cameras} == {"CAM-A", "CAM-B"}
