from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class DispatchConfig:
    emergency_contact: str = "911"
    default_location: str = "UNKNOWN"


@dataclass
class DispatchRecord:
    incident_type: str
    contact: str
    location: str
    encrypted_plate: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))


class DispatchService:
    """Simple dispatch gateway; replace with phone/SMS/API integration in production."""

    def __init__(self, config: DispatchConfig | None = None) -> None:
        self.config = config or DispatchConfig()
        self.records: List[DispatchRecord] = []

    def update_emergency_contact(self, contact: str) -> None:
        self.config.emergency_contact = contact

    def update_default_location(self, location: str) -> None:
        self.config.default_location = location

    def dispatch_pedestrian_collision(
        self,
        location: str | None = None,
        encrypted_plate: str | None = None,
    ) -> DispatchRecord:
        record = DispatchRecord(
            incident_type="pedestrian_collision",
            contact=self.config.emergency_contact,
            location=location or self.config.default_location,
            encrypted_plate=encrypted_plate,
        )
        self.records.append(record)
        return record
