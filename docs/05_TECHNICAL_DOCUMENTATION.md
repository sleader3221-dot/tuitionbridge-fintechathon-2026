# Technical documentation — TuitionBridge (Deliverable 1)

Version 0.1.0 · 20 October 2026 · Topic C, International Track · Team: [TEAM NAME — REPLACE]

## 1. Problem and users
See `03_PROBLEM_RESEARCH.md`. Primary user: an international student funding tuition from a home-currency account. Secondary: a planner (family member or adviser) who may prepare but not approve, and a viewer/reviewer.

## 2. Scope
In scope: provider comparison on total cost, affordability against a reserve, quote locking with expiry, deterministic risk policy, approval workflow, simulated execution with idempotency and recovery, hash-chained audit, grounded explanations. Out of scope: live FX, real provider APIs, KYC, sanctions screening against real lists, tax computation, multi-tenant identity.

## 3. Requirements
Functional: F1 compare providers for a target receive amount; F2 affordability verdict; F3 prepare with locked quote; F4 approve/reject; F5 sandbox execute with exactly-once debit; F6 audit and verification; F7 explanation with provenance.
Non-functional: N1 all money in Decimal strings; N2 every consequential call tier-checked server-side; N3 reproducible from a clean checkout in under 5 minutes; N4 no secrets in repo; N5 60 automated tests pass.

## 4. Architecture
See `04_SYSTEM_ARCHITECTURE.md`. Layering: API (validation, auth) → Services (policy, orchestration, evidence) → Domain (pure functions) + Persistence + Integrations + AI. The frontend holds no business rules.

## 5. Core algorithms and calculations
### 5.1 Quote (app/domain/providers.py)
For send currency S, receive currency R, provider p and mid-market rate m (1 S = m R):
- customer_rate = m × (1 − fx_margin)
- percent_fee_amount = round_half_even(send × percent_fee, S)
- total_fees = fixed_fee + percent_fee_amount
- amount_converted = send − total_fees
- receive = round_down(amount_converted × customer_rate, R)
- cost_vs_mid = round_half_even(send − receive ÷ m, S); cost_pct = cost_vs_mid ÷ send (4 dp)

Target-receive mode: send = round_up((target ÷ customer_rate + fixed_fee) ÷ (1 − percent_fee), S), then forward-quote and nudge by one minor unit until receive ≥ target (max 5 iterations). Hand-checked case: bank-wire archetype, 1,000 USD target, m = 1/88.50 → send 92,269.24 INR, cost 3,769.24 INR (4.09%).

### 5.2 Ranking and affordability (planning.py)
Quotes sorted by send amount; recommendation = lowest send amount among providers whose settlement_days ≤ days until due; otherwise fastest, with a warning. Affordability = balance − send ≥ reserve_min.

### 5.3 Risk policy (risk.py)
Block findings: DUPLICATE_EXECUTION, BENEFICIARY_NOT_FOUND, BENEFICIARY_BLOCKED, CURRENCY_MISMATCH, CORRIDOR_NOT_SUPPORTED, PROVIDER_MAX_AMOUNT, PER_TRANSFER_CAP (USD equivalent > 15,000 default), DAILY_CAP (executed today + this > 20,000 USD default), INSUFFICIENT_BALANCE, QUOTE_EXPIRED. Warning: SETTLEMENT_AFTER_DUE. Evaluated at prepare, approve and execute.

### 5.4 Audit chain (persistence/audit.py)
hash = SHA-256(canonical_json(ts, actor, action, tier, account_id, entity_type, entity_id, payload_json) ‖ prev_hash); genesis = 64 zeros. `verify()` recomputes the chain and reports the first bad sequence number. Payload keys such as `api_key`, `account_number`, `token` are redacted before hashing.

## 6. AI approach and limits
The model (optional; Anthropic Messages API via `ANTHROPIC_API_KEY`) receives the computed plan JSON and an optional user question wrapped in `<untrusted_user_question>`; it is instructed to use only numbers in the JSON. Output is accepted only if every number token (after normalising commas and trailing zeros, with percent form of cost_pct and small integers 0–31 allowed) appears in the plan. Otherwise, and whenever the key is absent, the question is flagged as injection-like, the call errors or times out (12 s default), the deterministic explanation is returned with `source = DETERMINISTIC_FALLBACK` and a `validation` reason. The model never computes amounts, ranks providers, or influences permissions or risk. If no key is configured the product reports `llm_configured: false`; we do not claim the live integration was exercised unless the evidence bundle contains an `LLM`-sourced explanation.

## 7. Data
`data/synthetic/rates.json` (mid rates dated 2026-10-01, label SYNTHETIC_FIXTURE), `providers.json` (four archetypes, label SIMULATED), `seed.json` (two synthetic accounts, five synthetic beneficiaries including one blocked and one that times out once). No real personal data anywhere.

## 8. Security design
Summarised in `06_SECURITY_SELF_ASSESSMENT.md`: API-key principals bound to one account; tiers 0–4 with 4 disabled; account scoping of beneficiaries and transfers; idempotency; per-key rate limiting; Decimal-only money; input length caps; untrusted-text guard; redaction; hash-chained audit; denial logging.

## 9. Error handling
401 unauthenticated · 403 PERMISSION_DENIED (audited) · 404 NOT_FOUND · 409 INVALID_STATE · 422 validation · 429 RATE_LIMITED · 400 INVALID_MONEY_INPUT. Provider failure → FAILED without debit, retryable. Quote expiry → EXPIRED. Atomic debit via `BEGIN IMMEDIATE`; rollback on any error.

## 10. API and schemas
Endpoints and tiers are in `README.md`; request schemas in `app/api/schemas.py`; interactive OpenAPI at `/api/docs`.

## 11. Deployment and reproducibility
`scripts/setup.sh`, `scripts/run.sh`, `scripts/test.sh`, `scripts/make_evidence.py`. Python 3.10+, pinned dependencies in `requirements.txt`. Fresh database seeded on first start; `scripts/reset_db.sh` to reset.

## 12. Testing and evidence
`08_TEST_PLAN_AND_REPORT.md`. 60 tests across unit, security and integration; evidence logs generated by the real application code.

## 13. Known risks and future work
`09_KNOWN_RISKS.md`. Next steps: live rate feed with provenance, real provider sandbox APIs, identity provider and MFA for Tier 3, external anchoring of audit head, multi-currency budgeting across the academic year, institution-side payment confirmation.

## 14. Citations
`12_RESEARCH_SOURCES.md`.
