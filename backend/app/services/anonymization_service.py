from __future__ import annotations

import base64
import hashlib
import hmac
from dataclasses import dataclass


@dataclass
class AnonymizationConfig:
    secret: str


class AnonymizationService:
    def __init__(self, cfg: AnonymizationConfig) -> None:
        self._key = cfg.secret.encode("utf-8")

    def hash_identifier(self, identifier: str) -> str:
        """
        Deterministic salted hash suitable for anonymized client IDs.
        """
        digest = hmac.new(self._key, identifier.encode("utf-8"), hashlib.sha256).digest()
        return base64.urlsafe_b64encode(digest[:18]).decode("utf-8").rstrip("=")

