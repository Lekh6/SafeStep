"""SafeStep core package."""

from .adapters import YOLOObjectAdapter
from .admin_auth import authenticate_admin, resolve_login_input
from .controller import CommandResult, CommandStatus, SignalController, SignalControllerAdapter
from .decision import DecisionEngine, DecisionInput, DecisionOutcome
from .deployments import CameraConnection, DeploymentRegistry, SignalDeployment
from .dispatch import DispatchConfig, DispatchRecord, DispatchService
from .models import CrossingState, EventRecord, PedMetrics, TrafficMetrics
from .orchestrator import SafeStepOrchestrator
from .perception import PerceptionEngine, Zone
from .runtime import RuntimeOutput, SafeStepRuntime
from .state_machine import PhaseSnapshot, SignalState, SignalStateMachine, TimingPolicy
from .tracking import Box, Detection

__all__ = [
    "authenticate_admin",
    "resolve_login_input",
    "DecisionEngine",
    "DecisionInput",
    "DecisionOutcome",
    "SignalDeployment",
    "CameraConnection",
    "DeploymentRegistry",
    "CrossingState",
    "EventRecord",
    "PedMetrics",
    "TrafficMetrics",
    "DispatchConfig",
    "DispatchRecord",
    "DispatchService",
    "SignalController",
    "SignalControllerAdapter",
    "CommandStatus",
    "CommandResult",
    "SafeStepOrchestrator",
    "PerceptionEngine",
    "Zone",
    "SafeStepRuntime",
    "RuntimeOutput",
    "SignalState",
    "TimingPolicy",
    "PhaseSnapshot",
    "SignalStateMachine",
    "YOLOObjectAdapter",
    "Detection",
    "Box",
]
