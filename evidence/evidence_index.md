# Evidence index

| Claim | Evidence | How to reproduce |
|---|---|---|
| 60 tests pass | `test_results/pytest_summary.txt`, `pytest_verbose.txt` | `bash scripts/test.sh` |
| End-to-end sandbox execution, exactly-once debit, replay refused | `operation_logs/s01_happy_path.json` | `python scripts/make_evidence.py` |
| Deterministic blocks with reasons | `operation_logs/s02_blocked_actions.json` | same |
| Permission tiers, Tier 4 refusal, cross-account denial, float rejection | `operation_logs/s03_permission_tiers.json` | same |
| Failure without debit, successful retry | `operation_logs/s04_failure_recovery.json` | same |
| Injection memo flagged; reject flow | `operation_logs/s05_injection_and_reject.json` | same |
| Hash-chained audit verified | `operation_logs/s06_audit_chain.json` | same |
| Quote expiry enforced | `operation_logs/s07_quote_expiry.json` | same |
| Running UI (desktop and mobile) | `screenshots/*.png` | `bash scripts/run.sh`, follow `docs/10_DEMO_RUNBOOK.md` |

All data is SYNTHETIC and all execution is SIMULATED. No on-chain or real-money transactions are claimed.
