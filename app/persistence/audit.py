"""Hash-chained, append-only audit log with payload redaction."""
from __future__ import annotations

import hashlib
import json
from decimal import Decimal

from ..clock import Clock
from .db import Database

GENESIS = "0" * 64
SENSITIVE_KEYS = {"api_key", "x-api-key", "authorization", "account_number", "password", "secret", "token"}
HASHED_FIELDS = ("ts", "actor", "action", "tier", "account_id", "entity_type", "entity_id", "payload_json")


def redact(obj):
    if isinstance(obj, dict):
        return {k: ("[REDACTED]" if k.lower() in SENSITIVE_KEYS else redact(v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact(v) for v in obj]
    if isinstance(obj, Decimal):
        return format(obj, "f")
    return obj


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)


def compute_hash(entry: dict, prev_hash: str) -> str:
    material = canonical({k: entry[k] for k in HASHED_FIELDS}) + prev_hash
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


class AuditLog:
    def __init__(self, db: Database, clock: Clock):
        self.db = db
        self.clock = clock

    def append(self, *, actor: str, action: str, tier: int, account_id: str | None,
               entity_type: str | None, entity_id: str | None, payload: dict) -> dict:
        entry = {
            "ts": self.clock.now().isoformat(), "actor": actor, "action": action, "tier": int(tier),
            "account_id": account_id, "entity_type": entity_type, "entity_id": entity_id,
            "payload_json": canonical(redact(payload)),
        }
        with self.db.lock:
            prev = self.db.audit_last_hash() or GENESIS
            entry["prev_hash"] = prev
            entry["hash"] = compute_hash(entry, prev)
            entry["seq"] = self.db.audit_insert(entry)
        return entry

    def entries(self, account_id: str | None = None) -> list[dict]:
        out = []
        for e in self.db.audit_all(account_id):
            e = dict(e)
            e["payload"] = json.loads(e.pop("payload_json"))
            out.append(e)
        return out

    def verify(self) -> dict:
        prev, checked = GENESIS, 0
        for e in self.db.audit_all(None):
            if e["prev_hash"] != prev or compute_hash(e, prev) != e["hash"]:
                return {"valid": False, "entries_checked": checked, "first_bad_seq": e["seq"]}
            prev = e["hash"]
            checked += 1
        return {"valid": True, "entries_checked": checked, "head_hash": prev}
