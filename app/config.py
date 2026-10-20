"""Settings from environment (plus optional .env). No secrets are hard-coded anywhere."""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "synthetic"

DEMO_API_KEYS = (
    "demo-viewer-key:viewer:acct_demo_student,"
    "demo-analyst-key:analyst:acct_demo_student,"
    "demo-planner-key:planner:acct_demo_student,"
    "demo-student-key:student:acct_demo_student,"
    "demo-other-key:student:acct_other"
)
VALID_ROLES = {"viewer", "analyst", "planner", "student"}


@dataclass(frozen=True)
class ApiKeyRecord:
    key_id: str  # non-secret label used in audit logs
    role: str
    account_id: str


@dataclass(frozen=True)
class Settings:
    database_path: str = str(BASE_DIR / "tuitionbridge.db")
    data_dir: Path = DATA_DIR
    api_keys: dict[str, ApiKeyRecord] = field(default_factory=dict)
    per_transfer_cap_usd: Decimal = Decimal("15000")
    daily_cap_usd: Decimal = Decimal("20000")
    quote_ttl_seconds: int = 900
    rate_limit_per_minute: int = 120
    llm_api_key: str | None = None
    llm_model: str = "claude-haiku-5-5"
    llm_timeout_seconds: float = 12.0


def load_dotenv(path: Path = BASE_DIR / ".env") -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def parse_api_keys(raw: str) -> dict[str, ApiKeyRecord]:
    out: dict[str, ApiKeyRecord] = {}
    for item in filter(None, (s.strip() for s in raw.split(","))):
        parts = item.split(":")
        if len(parts) != 3:
            raise ValueError(f"Bad API_KEYS entry (expected key:role:account): {item!r}")
        key, role, account = (p.strip() for p in parts)
        if role not in VALID_ROLES:
            raise ValueError(f"Unknown role {role!r}; valid roles: {sorted(VALID_ROLES)}")
        digest = hashlib.sha256(key.encode()).hexdigest()[:8]
        out[key] = ApiKeyRecord(key_id=f"{role}:{digest}", role=role, account_id=account)
    return out


def load_settings() -> Settings:
    load_dotenv()
    e = os.environ
    return Settings(
        database_path=e.get("DATABASE_PATH", str(BASE_DIR / "tuitionbridge.db")),
        api_keys=parse_api_keys(e.get("API_KEYS", DEMO_API_KEYS)),
        per_transfer_cap_usd=Decimal(e.get("PER_TRANSFER_CAP_USD", "15000")),
        daily_cap_usd=Decimal(e.get("DAILY_CAP_USD", "20000")),
        quote_ttl_seconds=int(e.get("QUOTE_TTL_SECONDS", "900")),
        rate_limit_per_minute=int(e.get("RATE_LIMIT_PER_MINUTE", "120")),
        llm_api_key=e.get("ANTHROPIC_API_KEY") or None,
        llm_model=e.get("LLM_MODEL", "claude-haiku-5-5"),
        llm_timeout_seconds=float(e.get("LLM_TIMEOUT_SECONDS", "12")),
    )
