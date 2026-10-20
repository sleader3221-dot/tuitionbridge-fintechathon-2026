# TuitionBridge

**2026 Shenzhen International FinTech Competition (FinTechathon) — International Track**
**Topic C: Cross-border & Student Finance Assistant**

Source repository: https://github.com/sleader3221-dot/tuitionbridge-fintechathon-2026

TuitionBridge is an AI financial agent that helps an international student pay tuition across borders
safely: it compares remittance providers on true cost, checks affordability against a minimum reserve,
locks a quote, runs deterministic risk checks, and — only with explicit approval — executes the payment
in a **simulated sandbox**, leaving a hash-chained audit trail. Every number is computed by deterministic
code; the language model only explains, and its output is rejected if it introduces any figure that is
not in the computed plan.

> Everything in this repository is **SIMULATED**. Rates, providers, accounts and beneficiaries are
> synthetic fixtures. No real money moves and no production credentials are required.

## What the judge will see

1. **Plan (Tier 1)** — enter a tuition amount and due date; four simulated providers are ranked by the
   amount you must send, with fees, FX margin cost versus mid-market, settlement time and affordability.
2. **Prepare (Tier 2)** — the quote is locked with an expiry; risk checks (caps, reserve, beneficiary
   screening, corridor, duplicate) decide `PENDING_APPROVAL` or `BLOCKED`, with reasons.
3. **Approve & execute (Tier 3)** — risk checks re-run at approval and again at execution; the sandbox
   adapter settles and the balance is debited exactly once. Re-executing returns the same result.
4. **Safety cases** — permission denials (enforced server-side, logged), Tier 4 production execution
   always refused, provider timeout with no debit and clean retry, prompt-injection memo flagged,
   quote expiry, tamper-evident audit log.

## Permission tiers (backend-enforced)

| Tier | Name | Demo role / key | Allowed |
|---|---|---|---|
| 0 | READ | `viewer` / `demo-viewer-key` | account, rates, providers, transfers, audit |
| 1 | ANALYZE | `analyst` / `demo-analyst-key` | + compare providers, explanations |
| 2 | PREPARE | `planner` / `demo-planner-key` | + prepare / reject transfers |
| 3 | EXECUTE_SANDBOX | `student` / `demo-student-key` | + approve / execute in sandbox |
| 4 | PRODUCTION | nobody | **disabled in this build** (`PRODUCTION_TIER_ENABLED = False`) |

Every API call carries `X-API-Key`; `app/services.py` calls `require_tier` and `require_account_access`
before any work. A frontend bypass (curl) hits the same checks. See `docs/06_SECURITY_SELF_ASSESSMENT.md`.

## Quick start

Requirements: Python 3.10+ (tested on 3.10 and 3.12), no other services.

```bash
bash scripts/setup.sh            # venv + dependencies + .env from .env.example
bash scripts/run.sh              # http://127.0.0.1:8000  (API docs at /api/docs)
bash scripts/test.sh             # 60 tests; writes evidence/test_results/
python scripts/make_evidence.py  # writes evidence/operation_logs/*.json + INDEX.md
bash scripts/reset_db.sh         # fresh synthetic data
```

Windows (PowerShell): `python -m venv .venv; .venv\Scripts\activate; pip install -r requirements.txt;
uvicorn app.asgi:app --port 8000`.

Optional LLM explanations: put an Anthropic API key in `.env` (`ANTHROPIC_API_KEY=`). Without it the app
uses a labelled deterministic explanation; with it, model output is validated against the plan's numbers.

## Demo runbook (3 minutes)

1. Open http://127.0.0.1:8000 as **student**. Compare 10,000.00 USD due 2026-11-15 → Demo Fintech A recommended, affordable.
2. Prepare → `PENDING_APPROVAL` with locked quote and expiry. Approve → `APPROVED`. Execute → `EXECUTED_SIMULATED`, reference `SBX-…`, balance debited. Execute again → "replayed".
3. Switch to **planner**, click Approve on a new transfer → 403 shown; audit log records `PERMISSION_DENIED`.
4. Click "Try production execute" → 403 Tier 4 disabled.
5. Prepare 16,000 USD → `BLOCKED: PER_TRANSFER_CAP`. Prepare to "Blocked Entity" → `BENEFICIARY_BLOCKED`.
6. Prepare 800 USD to "Timeout Demo Beneficiary" → approve → execute → `FAILED`, balance unchanged → execute → `EXECUTED_SIMULATED`.
7. Verify chain → VALID.

## API

| Method | Path | Tier |
|---|---|---|
| GET | `/api/health` | — |
| GET | `/api/accounts/{id}`, `/api/rates`, `/api/providers`, `/api/transfers?account_id=`, `/api/transfers/{id}`, `/api/audit`, `/api/audit/verify` | 0 |
| POST | `/api/quotes/compare` | 1 |
| POST | `/api/transfers/prepare`, `/api/transfers/{id}/reject` | 2 |
| POST | `/api/transfers/{id}/approve`, `/api/transfers/{id}/execute` | 3 |
| POST | `/api/transfers/{id}/production-execute` | 4 (always 403) |

Amounts are decimal strings (`"10000.00"`); JSON floats are rejected with 422. Errors: 401 unauthenticated,
403 `PERMISSION_DENIED`, 404, 409 `INVALID_STATE`, 422 validation, 429 rate limit.

Example:
```bash
curl -s -H "X-API-Key: demo-analyst-key" -H "Content-Type: application/json" \
  -d '{"account_id":"acct_demo_student","target_receive_amount":"10000.00","receive_currency":"USD","due_date":"2026-11-15"}' \
  http://127.0.0.1:8000/api/quotes/compare
```

## Project layout
```
tuitionbridge/
  app/                 backend and frontend
  data/synthetic/      fixture data
  docs/diagrams/       architecture diagrams
  evidence/            generated test and operation evidence
  scripts/             setup, run, test, reset, evidence
  tests/               unit, security, integration
```
