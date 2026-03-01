from __future__ import annotations

from typing import List

from .models import EventRecord
from .security import EncryptionService


class EvidenceService:
    def __init__(self, encryption: EncryptionService | None = None) -> None:
        self.events: List[EventRecord] = []
        self.encryption = encryption or EncryptionService.generate()

    def encrypt_identifier(self, plain_text: str) -> str:
        return self.encryption.encrypt(plain_text)

    def decrypt_identifier(self, encrypted: str) -> str:
        return self.encryption.decrypt(encrypted)

    def log_event(self, record: EventRecord) -> None:
        self.events.append(record)
