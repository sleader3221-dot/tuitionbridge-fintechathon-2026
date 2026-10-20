from app.clock import FixedClock
from app.persistence.audit import AuditLog
from app.persistence.db import Database
from tests.helpers import FIXED_NOW


def test_chain_verifies_and_detects_tampering(tmp_path):
    db = Database(str(tmp_path / "a.db"))
    log = AuditLog(db, FixedClock(FIXED_NOW))
    for i in range(3):
        log.append(actor="t", action="X", tier=0, account_id="a", entity_type="e", entity_id=str(i),
                   payload={"i": i, "api_key": "should-be-redacted"})
    assert log.verify()["valid"] is True
    assert log.entries("a")[0]["payload"]["api_key"] == "[REDACTED]"
    db.raw_execute("UPDATE audit_log SET payload_json='{\"i\":99}' WHERE seq=2")
    v = log.verify()
    assert v["valid"] is False and v["first_bad_seq"] == 2
