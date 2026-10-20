from datetime import datetime, timezone

from app.config import DATA_DIR, DEMO_API_KEYS, Settings, parse_api_keys

KEYS = {"viewer": "demo-viewer-key", "analyst": "demo-analyst-key", "planner": "demo-planner-key",
        "student": "demo-student-key", "other": "demo-other-key"}
FIXED_NOW = datetime(2026, 10, 20, 9, 0, tzinfo=timezone.utc)
ACCOUNT = "acct_demo_student"


def H(role: str) -> dict:
    return {"X-API-Key": KEYS[role]}


def make_settings(tmp_path, **overrides) -> Settings:
    base = dict(database_path=str(tmp_path / "test.db"), data_dir=DATA_DIR,
                api_keys=parse_api_keys(DEMO_API_KEYS), llm_api_key=None)
    base.update(overrides)
    return Settings(**base)


def prepare_body(**overrides) -> dict:
    body = dict(account_id=ACCOUNT, beneficiary_id="benef_univ_bursar", provider_id="demo_fintech_a",
                target_receive_amount="10000.00", receive_currency="USD", due_date="2026-11-15",
                memo="Fall semester tuition", idempotency_key="idem-0001-fall-tuition")
    body.update(overrides)
    return body
