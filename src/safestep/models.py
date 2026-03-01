from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Optional


class Mode(str, Enum):
    NORMAL = "normal"
    EMERGENCY = "emergency"
    SUSPENDED = "suspended"
    FAILSAFE = "failsafe"


class PedSignal(str, Enum):
    DONT_WALK = "dont_walk"
    WALK = "walk"
    FLASHING_DONT_WALK = "flashing_dont_walk"


@dataclass
class CrossingState:
    mode: Mode = Mode.NORMAL
    ped_signal: PedSignal = PedSignal.DONT_WALK
    vehicle_phase: str = "green"
    crosswalk_occupied: bool = False


@dataclass
class PedMetrics:
    wait_count: int
    avg_wait_s: float
    intent_score: float = 0.0


@dataclass
class TrafficMetrics:
    flow_rate: float
    queue_length: int
    occupancy: float = 0.0


@dataclass
class EventRecord:
    event_type: str
    confidence: float
    details: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))
    encrypted_identifier: Optional[str] = None
