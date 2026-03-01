from __future__ import annotations

import hashlib
import importlib
import importlib.util
import os
from dataclasses import dataclass

_HAS_CRYPTOGRAPHY = importlib.util.find_spec("cryptography") is not None
if _HAS_CRYPTOGRAPHY:
    AESGCM = importlib.import_module("cryptography.hazmat.primitives.ciphers.aead").AESGCM


@dataclass
class EncryptionService:
    key: bytes

    @classmethod
    def generate(cls) -> "EncryptionService":
        if _HAS_CRYPTOGRAPHY:
            return cls(key=AESGCM.generate_key(bit_length=128))
        return cls(key=os.urandom(32))

    def encrypt(self, plaintext: str) -> str:
        if _HAS_CRYPTOGRAPHY:
            aesgcm = AESGCM(self.key)
            nonce = os.urandom(12)
            ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), associated_data=None)
            return "aesgcm:" + (nonce + ciphertext).hex()

        nonce = os.urandom(16)
        stream = hashlib.sha256(self.key + nonce).digest()
        plain = plaintext.encode("utf-8")
        xored = bytes([b ^ stream[i % len(stream)] for i, b in enumerate(plain)])
        return "fallback:" + (nonce + xored).hex()

    def decrypt(self, payload_hex: str) -> str:
        kind, payload = payload_hex.split(":", maxsplit=1)
        raw = bytes.fromhex(payload)

        if kind == "aesgcm" and _HAS_CRYPTOGRAPHY:
            nonce, ciphertext = raw[:12], raw[12:]
            aesgcm = AESGCM(self.key)
            plain = aesgcm.decrypt(nonce, ciphertext, associated_data=None)
            return plain.decode("utf-8")

        nonce, ciphertext = raw[:16], raw[16:]
        stream = hashlib.sha256(self.key + nonce).digest()
        plain = bytes([b ^ stream[i % len(stream)] for i, b in enumerate(ciphertext)])
        return plain.decode("utf-8")
