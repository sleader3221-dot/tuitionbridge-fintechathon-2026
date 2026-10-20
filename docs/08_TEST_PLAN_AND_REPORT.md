# Test plan and report

## Plan
| Layer | File | Count | Purpose |
|---|---|---|---|
| Unit | `tests/unit/test_money.py` | 3 | float rejection, rounding modes, invalid input |
| Unit | `tests/unit/test_fx.py` | 3 | direct/inverse rates, cross via INR |
| Unit | `tests/unit/test_providers.py` | 20 | hand-checked quote, 16 target-mode invariants, send-mode, fee overflow, corridor |
| Unit | `tests/unit/test_risk.py` | 7 | each policy code incl. exact boundaries |
| Unit | `tests/unit/test_audit.py` | 1 | chain validity, redaction, tamper detection |
| Unit | `tests/unit/test_guard.py` | 3 | injection flagging, benign text, control chars/truncation |
| Unit | `tests/unit/test_explainer.py` | 5 | fallback, ungrounded rejection, grounded acceptance, flagged question isolation, error fallback |
| Security | `tests/security/test_permissions.py` | 7 | auth, tiers, Tier 4, cross-account, denial audit, float, rate limit |
| Integration | `tests/integration/test_api_flow.py` | 11 | happy path, idempotency, blocks, daily cap, expiry, reject, failure/recovery, injection memo, 404/422 |
| **Total** | | **60** | |

Acceptance criteria mapping: valid request completes (happy path); invalid input errors cleanly (422/400 tests); disallowed action cannot execute via API (security tests); permission checks hold without the UI (all tests use the HTTP API directly); every amount has a currency (schema + views); calculations independently tested (unit); simulated action has reproducible input/decision/result/evidence (evidence script); failed dependency does not fabricate results (failure/recovery test); fresh reviewer can launch (README + scripts).

## Report (actual run)
Environment: Python 3.10 virtualenv (host Python 3.12.10), Linux under WSL. Command: `python -m pytest -q`.
Result: **60 passed, 1 warning in 2.85 s** (warning: Starlette TestClient anyio deprecation, not a product issue).
Raw output: `evidence/test_results/pytest_summary.txt` and `pytest_verbose.txt` (produced by `scripts/test.sh`).

Not executed by automation: browser rendering (checked manually, screenshots in `evidence/screenshots/`), live LLM call (optional, requires key), load testing.
