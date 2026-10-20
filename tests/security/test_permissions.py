from fastapi.testclient import TestClient

from app.main import create_app
from tests.helpers import ACCOUNT, H, make_settings, prepare_body

COMPARE = dict(account_id=ACCOUNT, target_receive_amount="10000.00", receive_currency="USD", due_date="2026-11-15")


def test_no_or_bad_key(client):
    assert client.get(f"/api/accounts/{ACCOUNT}").status_code == 401
    assert client.get(f"/api/accounts/{ACCOUNT}", headers={"X-API-Key": "nope"}).status_code == 401


def test_tier_boundaries(client):
    r = client.post("/api/quotes/compare", json=COMPARE, headers=H("viewer"))
    assert r.status_code == 403 and r.json()["error"]["code"] == "PERMISSION_DENIED"
    assert r.json()["error"]["required_tier"] == 1
    assert client.post("/api/transfers/prepare", json=prepare_body(), headers=H("analyst")).status_code == 403
    t = client.post("/api/transfers/prepare", json=prepare_body(), headers=H("planner")).json()
    assert t["status"] == "PENDING_APPROVAL"
    assert client.post(f"/api/transfers/{t['id']}/approve", json={}, headers=H("planner")).status_code == 403
    assert client.post(f"/api/transfers/{t['id']}/execute", headers=H("planner")).status_code == 403
    assert client.get(f"/api/transfers/{t['id']}", headers=H("planner")).json()["status"] == "PENDING_APPROVAL"


def test_tier4_disabled_even_for_top_role(client):
    t = client.post("/api/transfers/prepare", json=prepare_body(), headers=H("planner")).json()
    r = client.post(f"/api/transfers/{t['id']}/production-execute", headers=H("student"))
    assert r.status_code == 403 and r.json()["error"]["required_tier"] == 4


def test_cross_account_access_denied(client):
    assert client.get(f"/api/accounts/{ACCOUNT}", headers=H("other")).status_code == 403
    t = client.post("/api/transfers/prepare", json=prepare_body(), headers=H("planner")).json()
    assert client.post(f"/api/transfers/{t['id']}/approve", json={}, headers=H("other")).status_code == 403
    # beneficiaries are scoped to the account: another account's beneficiary cannot be used
    r = client.post("/api/transfers/prepare", json=prepare_body(account_id="acct_other", target_receive_amount="500.00",
                                                                 idempotency_key="idem-other-00001"), headers=H("other"))
    assert r.status_code == 200 and r.json()["status"] == "BLOCKED"
    assert "BENEFICIARY_NOT_FOUND" in {f["code"] for f in r.json()["risk"]["findings"]}


def test_denials_are_audited(client):
    client.post("/api/quotes/compare", json=COMPARE, headers=H("viewer"))
    entries = client.get("/api/audit", headers=H("viewer")).json()
    assert any(e["action"] == "PERMISSION_DENIED" for e in entries)


def test_float_amount_rejected(client):
    r = client.post("/api/quotes/compare", json={**COMPARE, "target_receive_amount": 10000.5}, headers=H("analyst"))
    assert r.status_code == 422


def test_rate_limit(tmp_path, clock):
    app = create_app(make_settings(tmp_path, rate_limit_per_minute=3), clock=clock)
    c = TestClient(app)
    for _ in range(3):
        assert c.get("/api/rates", headers=H("viewer")).status_code == 200
    assert c.get("/api/rates", headers=H("viewer")).status_code == 429
    clock.advance(61)
    assert c.get("/api/rates", headers=H("viewer")).status_code == 200
