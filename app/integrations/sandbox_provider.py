"""SIMULATED remittance provider. Nothing here moves real money; references are labelled SBX-."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


class SandboxExecutionError(Exception):
    pass


@dataclass(frozen=True)
class SandboxResult:
    reference: str
    status: str
    executed_at: str
    label: str = "SIMULATED"


class SandboxProviderAdapter:
    LABEL = "SIMULATED"

    def __init__(self):
        self._failed_once: set[str] = set()

    def execute(self, *, transfer_id: str, provider_id: str, send_amount: Decimal, send_currency: str,
                receive_amount: Decimal, receive_currency: str, beneficiary: dict, now: datetime) -> SandboxResult:
        mode = beneficiary.get("simulate_failure")
        if mode == "TIMEOUT_ONCE" and transfer_id not in self._failed_once:
            self._failed_once.add(transfer_id)
            raise SandboxExecutionError("SIMULATED provider timeout: no settlement confirmation received")
        if mode == "TIMEOUT_ALWAYS":
            raise SandboxExecutionError("SIMULATED provider unavailable")
        material = f"{transfer_id}|{provider_id}|{send_amount}|{send_currency}|{receive_amount}|{receive_currency}"
        ref = "SBX-" + hashlib.sha256(material.encode()).hexdigest()[:12].upper()
        return SandboxResult(reference=ref, status="SETTLED_SIMULATED", executed_at=now.isoformat())
