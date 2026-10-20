"""Backend-enforced permission tiers. Every service method calls require_tier."""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class Tier(IntEnum):
    READ = 0
    ANALYZE = 1
    PREPARE = 2
    EXECUTE_SANDBOX = 3
    PRODUCTION = 4


ROLE_MAX_TIER = {"viewer": Tier.READ, "analyst": Tier.ANALYZE, "planner": Tier.PREPARE, "student": Tier.EXECUTE_SANDBOX}
PRODUCTION_TIER_ENABLED = False  # deliberately hard-disabled in this build; no code path can flip it at runtime


@dataclass(frozen=True)
class Principal:
    key_id: str
    role: str
    account_id: str

    @property
    def max_tier(self) -> Tier:
        return ROLE_MAX_TIER[self.role]


class PermissionDenied(Exception):
    def __init__(self, message: str, *, required: Tier, principal: Principal, account_id: str | None = None):
        super().__init__(message)
        self.required = required
        self.principal = principal
        self.account_id = account_id


def require_tier(principal: Principal, tier: Tier) -> None:
    if tier >= Tier.PRODUCTION and not PRODUCTION_TIER_ENABLED:
        raise PermissionDenied("Tier 4 (production / irreversible operations) is disabled in this build",
                               required=tier, principal=principal)
    if principal.max_tier < tier:
        raise PermissionDenied(
            f"Role '{principal.role}' is limited to Tier {int(principal.max_tier)} ({principal.max_tier.name}); "
            f"this action requires Tier {int(tier)} ({tier.name})", required=tier, principal=principal)


def require_account_access(principal: Principal, account_id: str) -> None:
    if principal.account_id != account_id:
        raise PermissionDenied("Principal is not authorised for this account",
                               required=Tier.READ, principal=principal, account_id=account_id)
