# Execution evidence index (SIMULATED sandbox)

Generated 2026-10-20T07:22:16.655192+00:00 by `scripts/make_evidence.py` against a fresh SQLite database.
All balances, rates, providers and beneficiaries are synthetic; no real money moved.

## s01_happy_path.json — Compare -> prepare -> approve -> execute (sandbox) -> replay refused
- account before -> 200
- compare providers -> 200
- prepare -> 200 PENDING_APPROVAL
- approve -> 200 APPROVED
- execute (SIMULATED) -> 200 EXECUTED_SIMULATED
- execute again (idempotent replay) -> 200 EXECUTED_SIMULATED
- account after -> 200

## s02_blocked_actions.json — Deterministic risk blocks: cap, blocked beneficiary, reserve breach
- over per-transfer cap -> 200 BLOCKED
- blocked beneficiary -> 200 BLOCKED
- breaches reserve -> 200 BLOCKED

## s03_permission_tiers.json — Backend permission enforcement incl. Tier 4 refusal and cross-account
- no key -> 401
- viewer tries compare -> 403
- analyst tries prepare -> 403
- planner prepares -> 200 PENDING_APPROVAL
- planner tries approve -> 403
- other account tries approve -> 403
- student tries production execute (Tier 4) -> 403
- float amount rejected -> 422

## s04_failure_recovery.json — Simulated provider timeout, no debit, successful retry
- prepare to timeout beneficiary -> 200 PENDING_APPROVAL
- approve -> 200 APPROVED
- execute -> FAILED -> 200 FAILED
- balance unchanged -> 200
- retry -> EXECUTED_SIMULATED -> 200 EXECUTED_SIMULATED
- balance debited once -> 200

## s05_injection_and_reject.json — Prompt-injection memo flagged; reject flow
- prepare with hostile memo -> 200 PENDING_APPROVAL
- reject -> 200 REJECTED
- approve after reject -> 409 -> 409

## s06_audit_chain.json — Hash-chained audit log and verification
- audit entries -> 200
- verify chain -> 200

## s07_quote_expiry.json — Locked quote expires (TTL 1s) and approval is refused
- prepare -> 200 PENDING_APPROVAL
- approve after expiry -> EXPIRED -> 200 EXPIRED
