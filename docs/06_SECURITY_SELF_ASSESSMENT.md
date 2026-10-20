# Security self-assessment report (Deliverable 5)

Scope: TuitionBridge v0.1.0 as in this repository. "Implemented" means present in code and covered by a test named here; "Recommended" means not implemented.

## 1. Data inventory and classification
| Data | Location | Class | Notes |
|---|---|---|---|
| Account balances, reserve | `balances`, `accounts` | Synthetic financial | Decimal strings |
| Beneficiaries | `beneficiaries` | Synthetic PII-like | account number stored masked only |
| Transfers, quotes, risk results | `transfers` | Synthetic financial | JSON columns |
| Audit log | `audit_log` | Integrity-critical | hash-chained, redacted payloads |
| API keys | environment / `.env` | Secret | never stored in DB or logs; audit uses `role:sha256[:8]` |
| LLM key | environment | Secret | optional |

## 2. Trust boundaries
Client → API (validation, auth, rate limit) → Services (tiers, account scope, idempotency, risk) → Persistence. AI layer is a separate boundary: untrusted text in, validated text out. See diagram 4 in `04_SYSTEM_ARCHITECTURE.md`.

## 3. Permission tiers (implemented, server-side)
| Tier | Operations | Enforcement | Tests |
|---|---|---|---|
| 0 READ | account, rates, providers, transfers, audit | `require_tier(READ)` + `require_account_access` | `test_no_or_bad_key`, `test_cross_account_access_denied` |
| 1 ANALYZE | compare | `require_tier(ANALYZE)` | `test_tier_boundaries` |
| 2 PREPARE | prepare, reject | `require_tier(PREPARE)` | `test_tier_boundaries` |
| 3 EXECUTE_SANDBOX | approve, execute | `require_tier(EXECUTE_SANDBOX)` | `test_tier_boundaries`, `test_happy_path_end_to_end` |
| 4 PRODUCTION | none | `PRODUCTION_TIER_ENABLED = False` constant checked before role | `test_tier4_disabled_even_for_top_role` |
Every denial is written to the audit log (`test_denials_are_audited`). The frontend confirmation buttons are convenience only; `curl` hits the same checks.

## 4. Threat model and controls
| # | Threat | Control | Status | Evidence |
|---|---|---|---|---|
| T1 | Unauthorised action / tier escalation | tiers in service layer, not UI | Implemented | security tests |
| T2 | Broken access control across accounts | principal bound to one account; beneficiaries and transfers scoped by account | Implemented | `test_cross_account_access_denied` |
| T3 | Prompt injection via memo/question | guard flags patterns, strips control chars, caps length; flagged questions never reach LLM; memo never used as instruction | Implemented | `test_guard.py`, `test_flagged_question_never_reaches_llm`, `test_memo_injection_is_flagged_but_does_not_alter_amounts` |
| T4 | Model hallucination of figures | number-grounding validator; labelled fallback | Implemented | `test_invented_number_rejected` |
| T5 | Invalid / manipulated amounts | Decimal strings only, floats rejected (422), bounds | Implemented | `test_float_amount_rejected`, `test_money.py` |
| T6 | Replay / duplicate execution | idempotency key per account; EXECUTED is terminal; DUPLICATE_EXECUTION finding | Implemented | `test_idempotent_prepare`, happy-path replay assertion |
| T7 | Incorrect financial arithmetic | explicit rounding rules; hand-checked test; invariants | Implemented | `test_providers.py` |
| T8 | External provider failure | adapter errors → FAILED, no debit, retry | Implemented | `test_failure_then_recovery` |
| T9 | Stale quote | TTL, QUOTE_EXPIRED at approve/execute | Implemented | `test_quote_expiry` |
| T10 | Limit breaches | per-transfer and daily USD caps, reserve | Implemented | `test_risk.py`, integration tests |
| T11 | Secrets exposure | env only, `.env` ignored, hashed key ids, redaction | Implemented | `test_chain_verifies_and_detects_tampering` (redaction) |
| T12 | Audit tampering | SHA-256 chain, verify endpoint | Implemented (not externally anchored) | same test |
| T13 | Denial of service | per-key sliding-window rate limit | Implemented (in-memory) | `test_rate_limit` |
| T14 | Sensitive data in logs | masked account numbers; payload redaction; no request bodies logged | Implemented | code review |
| T15 | Malicious LLM response | treated as text only; length cap; validator | Implemented | explainer tests |
| T16 | Dependency risk | 5 pinned, permissively licensed packages | Implemented | `requirements.txt` |
| T17 | Transport security | none in demo (HTTP localhost) | Recommended: TLS | — |
| T18 | Identity / MFA for Tier 3 | demo API keys | Recommended: IdP + MFA | — |
| T19 | Real sanctions screening | synthetic flag only | Recommended | — |
| T20 | Race on concurrent execute | DB lock + `BEGIN IMMEDIATE`; single process | Partially (single node) | code |

## 5. Risk register (residual)
| ID | Risk | Severity | Likelihood | Residual after controls | Planned mitigation |
|---|---|---|---|---|---|
| R1 | Synthetic rates mistaken for live | Medium | Low | Low (labels in API, UI, docs) | live feed with provenance |
| R2 | API key leakage | High | Low in demo | Medium | IdP, short-lived tokens |
| R3 | Audit DB replaced wholesale | High | Low | Medium (chain self-consistent) | anchor head hash externally |
| R4 | Rate limiter reset on restart | Low | High | Low | shared store |
| R5 | Model explanation misleading despite grounded numbers | Medium | Medium | Medium | human-readable formula panel already shown; add reviewer flagging |

## 6. Secrets management
`.env.example` documents all variables; `.gitignore` excludes `.env`; no secret is read anywhere except `config.py`; audit actors are hashed key identifiers.

## 7. Incident and recovery
Failed execution leaves balance untouched and the transfer retryable; database can be reset from fixtures; the audit chain can be verified at any time and the first inconsistent entry located.

## 8. Production deployment restrictions
This build must not be connected to real funds: Tier 4 is disabled, no provider integration exists, no identity assurance, no TLS. These are documented limitations, not oversights.
