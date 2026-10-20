#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ -d "$SCRIPT_DIR/tuitionbridge" ]]; then
  ROOT="$SCRIPT_DIR/tuitionbridge"
elif [[ -f "$SCRIPT_DIR/README.md" && -d "$SCRIPT_DIR/app" ]]; then
  ROOT="$SCRIPT_DIR"
elif [[ -d "$PWD/tuitionbridge" ]]; then
  ROOT="$(cd -- "$PWD/tuitionbridge" && pwd)"
else
  echo "Could not locate the tuitionbridge project beside this script or in the current directory." >&2
  exit 1
fi
ROOT="$(cd -- "$ROOT" && pwd)"
w() { mkdir -p "$(dirname "$ROOT/$1")"; cat > "$ROOT/$1"; }

w docs/01_EXECUTIVE_SUMMARY.md <<'__TB_EOF__'
# Executive summary — TuitionBridge

**Competition:** 2026 Shenzhen International FinTech Competition (FinTechathon), International Track, theme "AI as a Financial Participant".
**Topic:** C — Cross-border & Student Finance Assistant.
**Team:** TuitionBridge FinTech Lab. **Submission date:** 20 October 2026.

## The problem
International students make a handful of very large cross-border payments each year (tuition, deposits, rent) from a home-currency account, under time pressure and with real money at stake. The cost of a transfer is split across visible fees and an invisible FX margin, so the cheapest-looking option is often not the cheapest; the World Bank's Remittance Prices Worldwide database puts the global average cost of sending money at 6.36% of the amount sent (September 2025 report), more than double the 3% target in SDG 10.c. For India, the largest single source of outbound students in our demo corridor, resident individuals sent USD 29.56 billion abroad under the RBI's Liberalised Remittance Scheme in FY2024-25, with education one of the largest purposes. (Sources and caveats: `12_RESEARCH_SOURCES.md`.)

## What we built
TuitionBridge is an AI financial agent that takes a tuition invoice ("deliver 10,000 USD by 15 November") and:
1. **ranks providers on the true amount the student must send**, decomposing fixed fee, percentage fee and FX-margin cost against the mid-market rate;
2. **checks affordability** against a minimum reserve the student must keep;
3. **locks a quote with an expiry and runs deterministic risk checks** (per-transfer cap, daily cap, reserve, beneficiary screening flag, corridor support, duplicate execution);
4. **executes only after explicit approval, in a simulated sandbox**, debiting the balance exactly once with idempotent replay and clean failure recovery;
5. **records every step in a hash-chained audit log**, including every permission denial.

A language model explains the plan in plain English, but it is never allowed to compute or decide: its output is rejected if it contains any number not present in the deterministic plan, and a labelled deterministic explanation is used instead.

## Why it fits the judging criteria
- **Task completion (40%)** — the end-to-end job (compare → prepare → approve → execute → evidence) works in the running application and is covered by 60 automated tests.
- **Security & compliance (30%)** — five permission tiers are enforced on the server for every request; Tier 4 (production) is hard-disabled; amounts are Decimal strings; untrusted text is sanitised and never used as instruction; audit log is tamper-evident.
- **Innovation & interaction (30%)** — evidence-carrying decisions (every recommendation shows the formula inputs), a visible plan → check → approve → execute → verify loop, grounded-LLM explanations with a validator, and failure/recovery shown live rather than an ideal-path-only demo.

## Honest scope
Everything is simulated: rates and providers are labelled synthetic fixtures; there is no live FX, no real provider API, no real screening list. The deliverable is a credible, reproducible prototype of the agent's control plane, not a licensed remittance service.
__TB_EOF__

w docs/02_TRACK_SELECTION.md <<'__TB_EOF__'
# Track selection memo

Date: 20 October 2026. This is a strategic assessment by the team; the scoring weights in section 2 are **ours**, not the organiser's. The official judging weights are task completion 40%, security & compliance 30%, innovation & interaction 30%, with a 0–5 point challenge bonus for Topic F only (Appendix 2).

## 1. Constraints that shaped the decision
- Registration and submission close 20 Oct 2026 23:59 Beijing time (official).
- Build window available to the team: one working day; no paid APIs, no production financial accounts.
- Execution evidence rule (official): non-on-chain topics need simulated-account/sandbox logs and a demo video; the on-chain topic needs **real on-chain transaction hashes**.

## 2. Scoring scale
1 = weak / high risk, 5 = strong / low risk. Weights reflect what we can demonstrate in a short review, not market size.

| Factor (weight) | A Personal finance | B Wealth advisory | C Cross-border & student | D Insurance | E SME copilot | F Agent wallet |
|---|---|---|---|---|---|---|
| Clarity of a consequential, demonstrable task (0.25) | 3 | 3 | **5** | 3 | 3 | 5 |
| Deterministic, testable core (0.15) | 4 | 3 | **5** | 2 | 3 | 4 |
| Security story that is real, not decorative (0.20) | 2 | 3 | **5** | 2 | 3 | 5 |
| Feasibility in one day without credentials (0.20) | 5 | 4 | **4** | 3 | 4 | 1 |
| Evidence reproducibility (0.10) | 4 | 3 | **5** | 3 | 3 | 2 |
| Regulatory/liability exposure of claims (0.10) | 4 | 2 | **4** | 2 | 3 | 3 |
| **Weighted score** | 3.55 | 3.10 | **4.70** | 2.55 | 3.20 | 3.40 |

### Reasoning per topic
- **A** is the easiest to "complete" but its actions are advisory; permission tiers and sandbox execution would be contrived, weakening the 30% security dimension.
- **B** requires suitability logic and product data; synthetic products risk being read as fabricated financial advice.
- **C** has a natural consequential action (a tuition remittance), pure-arithmetic core (FX, fees, affordability), and an obvious sandbox; its security controls (caps, approval, screening, idempotency) are the same controls a real product would need.
- **D** depends on policy documents and coverage interpretation; conclusions are hard to make verifiably correct in a day.
- **E** needs plausible SME financial data and forecasting; demonstrable value requires more data than we can source honestly.
- **F** scores high on task and security but the evidence rule requires real chain transactions. Testnet execution with key management, funding and explorer verification is feasible in principle, but the one-day window makes it the highest-risk path, and the bonus is capped at 5 points while the rest of the rubric is identical for all topics.

### Sensitivity
If feasibility weight is halved and the security weight raised, F rises to ≈3.7 and C stays ≈4.7. If the task-clarity weight is halved, A rises to ≈3.7 and C to ≈4.5. C remains first under every reweighting we tried; the only scenario in which F wins is one where real on-chain execution is already set up before the build starts.

## 3. Decision

**SELECTED TRACK:** Topic C — Cross-border & Student Finance Assistant.

**PROBLEM STATEMENT:** International students paying tuition from a home-currency account cannot see the true cost of a transfer (fees plus FX margin), cannot easily check whether it leaves them solvent, and have no safe, auditable way to let an assistant act for them.

**TARGET USER:** A student (demo: Indian student at a US institution) and the parent/guardian who funds the account; secondary: a reviewer who must verify what the agent did.

**CORE VALUE PROPOSITION:** Cheapest in-time provider chosen on total cost, affordability checked against a reserve, execution gated by explicit approval and deterministic risk policy, with tamper-evident evidence.

**DISTINCTIVE INNOVATION:** A grounded-explanation validator: the LLM may only restate figures produced by the deterministic engine; any invented number is rejected and the fallback is labelled. Combined with server-enforced tiers and a hash-chained audit log, the agent is auditable by construction.

**WHY NOT THE OTHER FIVE:** see table and reasoning above.

**DEMONSTRATION:** compare → prepare (locked quote, risk checks) → approve → execute (SIMULATED) → replay refused → permission denial → Tier 4 refusal → provider timeout and retry → audit chain verified.

**EVIDENCE:** 60 passing tests (`evidence/test_results/`), scenario logs generated by the real code (`evidence/operation_logs/`), screenshots of the running UI.

**RISKS:** synthetic rates could be mistaken for live data (mitigated by labels everywhere); demo API keys are not a real identity layer (documented); the video is optional and may be outstanding at submission (documented in `11_SUBMISSION_CHECKLIST.md`).
__TB_EOF__

w docs/03_PROBLEM_RESEARCH.md <<'__TB_EOF__'
# Problem research — cross-border and student finance

Each claim is tagged: **[OFFICIAL]** competition rule, **[SOURCED]** external fact with a citation in `12_RESEARCH_SOURCES.md`, **[ENGINEERING]** our conclusion, **[ASSUMPTION]** made for lack of data.

## 1. The user and the job
An international student typically makes 2–4 large payments a year (tuition instalments, deposit, housing) from a home-currency account funded by family. The job is: *deliver exactly X in the institution's currency by a due date, at the lowest total cost, without endangering living expenses, and with a record the family and the institution can trust.* [ENGINEERING]

## 2. Why the existing workflow is insufficient
- **Opaque pricing.** Cost is split between a visible fee and an FX margin over the mid-market rate. Globally, sending remittances costs on average 6.36% of the amount sent (World Bank RPW, September 2025 report), against the SDG 10.c target of 3%. [SOURCED S1, S2]
- **Scale of the corridor we demo.** Outward remittances by Indian resident individuals under the RBI's Liberalised Remittance Scheme were USD 29.56 billion in FY2024-25 (RBI Bulletin, table 36). [SOURCED S3] Secondary reporting attributes about USD 2.9 billion of FY25 flows to overseas education. [SOURCED S4 — secondary; treat as indicative]
- **Regulatory friction.** Education remittances under LRS are subject to purpose codes, a USD 250,000 annual limit and tax collected at source rules. [SOURCED S5 — bank explainer; verify against RBI master direction before relying on specific rates]
- **No safe delegation.** Consumer apps let a user transact but give no way to let an assistant *prepare* a payment under limits while a human keeps the approval. [ENGINEERING]

## 3. What "good" looks like for a judge
A reviewer should be able to see, in under three minutes: the ranking with its formula inputs, an affordability verdict, a blocked action with its reason, an approved sandbox execution with a reference, a refused replay, and a verified audit chain. [ENGINEERING]

## 4. Data available and what we did
No free, licensed live FX or provider-fee API could be relied on within the window, so all rates and fee schedules are **synthetic fixtures labelled as such** (`data/synthetic/`). The fee structures are illustrative archetypes (bank wire with fixed fee and wide margin; low-margin fintech with percentage fee; hybrid; education platform with direct institution payout) and are not real companies or real pricing. [ASSUMPTION, labelled in product]

## 5. Measurable improvement claimed
We claim only what the engine computes: for the demo invoice (10,000 USD, mid 88.50 INR/USD) the cheapest in-time option costs 1.49% versus 2.66% for the bank-wire archetype, a difference of about 10,800 INR on one payment. These are fixture-based numbers, not market measurements. [ENGINEERING]

## 6. Risks specific to the domain
Wrong rate timestamp, rounding errors, duplicate execution, sending to a wrong or screened beneficiary, exceeding regulatory limits, and model hallucination in explanations. Each has a control in `06_SECURITY_SELF_ASSESSMENT.md`.
__TB_EOF__

w docs/04_SYSTEM_ARCHITECTURE.md <<'__TB_EOF__'
# System architecture

All diagrams describe the implemented code in `app/`. Nothing shown here is planned-only.

## 1. System context
```mermaid
flowchart LR
  U[Student / Planner / Viewer<br/>browser or curl] -->|HTTPS in prod, HTTP in demo<br/>X-API-Key| API[TuitionBridge API<br/>FastAPI]
  API --> DB[(SQLite<br/>accounts, transfers, audit)]
  API -. optional, env key .-> LLM[Anthropic Messages API<br/>explanations only]
  API --> SBX[Sandbox provider adapter<br/>SIMULATED settlement]
  FX[(rates.json<br/>providers.json<br/>SYNTHETIC)] --> API
```

## 2. Components
```mermaid
flowchart TB
  subgraph Frontend [app/frontend - zero build]
    UI[index.html + app.js]
  end
  subgraph API [app/api]
    R[routes.py] --> D[deps.py auth + rate limit]
    R --> S[schemas.py Pydantic v2]
  end
  subgraph Service [app/services.py]
    SV[Services: compare / prepare / approve / execute / reject]
  end
  subgraph Domain [app/domain - pure, deterministic]
    M[money.py Decimal rules] --> P[providers.py quote formulas]
    FXm[fx.py rate table] --> P
    P --> PL[planning.py ranking + affordability]
    RK[risk.py policy checks]
  end
  subgraph Security [app/security]
    PM[permissions.py tiers] 
    RL[ratelimit.py]
  end
  subgraph AI [app/ai]
    G[guard.py untrusted text] --> EX[explainer.py LLM + grounding validator + fallback]
  end
  subgraph Persistence [app/persistence]
    DBm[db.py SQLite]
    AU[audit.py hash chain]
  end
  SBX[integrations/sandbox_provider.py]
  UI --> R --> SV
  SV --> PM
  SV --> PL
  SV --> RK
  SV --> EX
  SV --> DBm
  SV --> AU
  SV --> SBX
```

## 3. Runtime sequence (happy path)
```mermaid
sequenceDiagram
  participant B as Browser
  participant A as API/deps
  participant S as Services
  participant D as Domain
  participant DB as SQLite/Audit
  participant X as Sandbox adapter
  B->>A: POST /quotes/compare (analyst key)
  A->>S: principal(role=analyst)
  S->>S: require_tier(ANALYZE)
  S->>D: build_plan()
  S->>DB: audit QUOTE_COMPARE
  S-->>B: plan + explanation(source, validation)
  B->>A: POST /transfers/prepare (planner key)
  S->>S: require_tier(PREPARE), idempotency lookup
  S->>D: quote_for_target_receive(), risk.evaluate()
  S->>DB: insert transfer PENDING_APPROVAL | BLOCKED, audit
  B->>A: POST /approve (student key)
  S->>D: risk.evaluate() again
  S->>DB: APPROVED, audit
  B->>A: POST /execute (student key)
  S->>D: risk.evaluate() again (incl. duplicate check)
  S->>X: execute()
  X-->>S: SBX-reference or SandboxExecutionError
  S->>DB: debit + EXECUTED_SIMULATED atomically, audit
  S-->>B: transfer (execution_label=SIMULATED)
```

## 4. Trust boundaries and permission enforcement
```mermaid
flowchart LR
  subgraph Untrusted
    C[Client input: JSON body, memo, question, headers]
  end
  subgraph Boundary1 [Boundary 1: API]
    V[Pydantic validation<br/>Decimal strings only, length caps]
    K[API key -> Principal<br/>rate limit]
  end
  subgraph Boundary2 [Boundary 2: Service policy]
    T[require_tier / require_account_access]
    I[idempotency key]
    RK[risk.evaluate: caps, reserve, screening, corridor, expiry, duplicate]
  end
  subgraph Boundary3 [Boundary 3: AI]
    G[guard: control chars, length, injection patterns]
    N[number-grounding validator]
  end
  subgraph Trusted
    DB[(SQLite)]
    AU[Audit chain]
  end
  C --> V --> K --> T --> I --> RK --> DB
  C --> G --> N
  T -. denial logged .-> AU
```
Tier 4 (`PRODUCTION`) is a constant `PRODUCTION_TIER_ENABLED = False`; `require_tier` raises before role evaluation.

## 5. Transfer state machine
```mermaid
stateDiagram-v2
  [*] --> BLOCKED: prepare, risk fails
  [*] --> PENDING_APPROVAL: prepare, risk passes
  PENDING_APPROVAL --> APPROVED: approve (Tier 3), risk re-check passes
  PENDING_APPROVAL --> BLOCKED: approve, risk re-check fails
  PENDING_APPROVAL --> EXPIRED: approve after quote TTL
  PENDING_APPROVAL --> REJECTED: reject (Tier 2)
  APPROVED --> REJECTED: reject
  APPROVED --> EXECUTED_SIMULATED: execute, sandbox ok, atomic debit
  APPROVED --> FAILED: execute, sandbox error, no debit
  APPROVED --> EXPIRED: execute after TTL
  FAILED --> EXECUTED_SIMULATED: retry execute
  EXECUTED_SIMULATED --> EXECUTED_SIMULATED: execute again -> same result, replayed=true
```

## 6. Data model
```mermaid
erDiagram
  ACCOUNTS ||--o{ BALANCES : has
  ACCOUNTS ||--o{ BENEFICIARIES : owns
  ACCOUNTS ||--o{ TRANSFERS : initiates
  TRANSFERS }o--|| BENEFICIARIES : pays
  AUDIT_LOG }o--o| ACCOUNTS : about
  ACCOUNTS { text id PK; text holder_name; text home_currency; text reserve_min; text institution }
  BALANCES { text account_id FK; text currency; text amount }
  BENEFICIARIES { text id PK; text account_id FK; text currency; text account_number_masked; int blocked; text simulate_failure }
  TRANSFERS { text id PK; text idempotency_key; text status; text quote_json; text risk_json; text quote_expires_at; text amount_usd_equiv; text provider_reference }
  AUDIT_LOG { int seq PK; text ts; text actor; text action; int tier; text payload_json; text prev_hash; text hash }
```
Money columns are decimal strings; `(account_id, idempotency_key)` is unique.

## 7. Integration architecture
Only two external interfaces exist: the sandbox provider adapter (in-process, deterministic, labelled SIMULATED, with injectable failure modes) and the optional Anthropic Messages API for explanations (timeout, exception → fallback). Rates and providers are file fixtures loaded at startup.

## 8. Deployment
Single process: `uvicorn app.asgi:app`. Configuration via environment or `.env` (`.env.example`). SQLite file auto-created and seeded. Frontend is static files mounted by FastAPI; no build step. For production the documented constraints are: TLS termination, real identity provider instead of API keys, KMS-held secrets, a server database, external anchoring of the audit head hash.

## 9. Failure and recovery
```mermaid
flowchart TD
  E[execute] --> R{risk re-check}
  R -- fail --> B[BLOCKED or EXPIRED, audited]
  R -- pass --> X{sandbox adapter}
  X -- error --> F[FAILED, failure_reason, no debit, audited, retryable]
  X -- ok --> T{atomic tx: debit + mark executed}
  T -- InsufficientFunds --> F
  T -- commit --> OK[EXECUTED_SIMULATED, reference, audited]
  F --> E
  L[LLM timeout / bad output] --> FB[DETERMINISTIC_FALLBACK, labelled]
```
__TB_EOF__

w docs/05_TECHNICAL_DOCUMENTATION.md <<'__TB_EOF__'
# Technical documentation — TuitionBridge (Deliverable 1)

Version 0.1.0 · 20 October 2026 · Topic C, International Track · Team: TuitionBridge FinTech Lab

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
__TB_EOF__

w docs/06_SECURITY_SELF_ASSESSMENT.md <<'__TB_EOF__'
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
__TB_EOF__

w docs/07_DATA_AND_MODEL_CARD.md <<'__TB_EOF__'
# Data and model card

## Data
| Dataset | File | Provenance | Label | Limits |
|---|---|---|---|---|
| Mid-market rates | `data/synthetic/rates.json` | authored by team, dated 2026-10-01 | SYNTHETIC_FIXTURE | not market data; single snapshot |
| Providers | `data/synthetic/providers.json` | authored archetypes | SIMULATED | not real companies or prices |
| Accounts/beneficiaries | `data/synthetic/seed.json` | authored | SYNTHETIC | no real persons; "blocked" is a demo flag |
Currency support: INR, USD, GBP, EUR, CAD, AUD (2 minor digits). USD equivalents use direct pairs or cross via INR.

## Model
- Role: explanation only; optional; `claude-haiku-5-5` by default (configurable via `LLM_MODEL`), called through the Anthropic Messages API with a 12 s timeout.
- Inputs: computed plan JSON; optional sanitised user question marked untrusted.
- Outputs: ≤ 2,000 characters of text; accepted only if number-grounded.
- Not used for: pricing, ranking, affordability, permissions, risk, execution.
- Failure modes handled: no key, timeout, HTTP error, empty output, invented numbers, flagged question → labelled deterministic fallback.
- Evaluation performed: unit tests with injected fake model responses (`tests/unit/test_explainer.py`). Live calls were not part of the automated suite; if the team ran the app with a key, the evidence bundle will contain an explanation with `source: LLM`. Do not claim otherwise.
__TB_EOF__

w docs/08_TEST_PLAN_AND_REPORT.md <<'__TB_EOF__'
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
__TB_EOF__

w docs/09_KNOWN_RISKS.md <<'__TB_EOF__'
# Known risks and limitations

1. **Synthetic market data.** Rates and fees are fixtures; any cost figure in the demo is illustrative. Labels appear in API responses, UI banner, docs.
2. **Demo authentication.** Static API keys stand in for identity; no MFA; no session expiry. Not for real funds.
3. **No real screening.** The blocked beneficiary is a demo flag, not a sanctions or PEP check.
4. **Audit anchoring.** The chain detects tampering within the log but not replacement of the whole database; external anchoring is future work.
5. **Single process.** In-memory rate limiter and SQLite are fine for a demo, not for scale.
6. **LLM optionality.** Without a key the explanation is deterministic; with a key the live integration is exercised only manually.
7. **Regulatory scope.** LRS purpose codes, TCS and institution-side requirements are discussed in research but not implemented.
8. **Demo video.** Optional per the rules; if not recorded before submission it is listed as outstanding in the checklist.
__TB_EOF__

w docs/10_DEMO_RUNBOOK.md <<'__TB_EOF__'
# Demo runbook and video storyboard

## Live demo (fits the 10-minute presentation; the product part takes ~3 minutes)
Prerequisite: `scripts/run.sh` running; browser at http://127.0.0.1:8000; role = student.
1. (0:00) Point at the SANDBOX banner and the server-enforced limits card.
2. (0:20) Compare 10,000 USD due 2026-11-15 → ranking table; call out "You send" vs "Cost vs mid" and the recommendation rule; affordability green.
3. (1:00) Prepare → `PENDING_APPROVAL`, locked quote with expiry, all risk checks passed.
4. (1:20) Approve → `APPROVED`. Execute → `EXECUTED_SIMULATED`, `SBX-…` reference, balance debited. Execute again → "replayed". 
5. (1:50) Switch role to planner, prepare a new transfer, click Approve → 403; show `PERMISSION_DENIED` in audit log. Click "Try production execute" → 403 Tier 4 disabled.
6. (2:20) Prepare 16,000 USD → `BLOCKED: PER_TRANSFER_CAP`. Prepare to "Blocked Entity" → `BENEFICIARY_BLOCKED`.
7. (2:45) Back as student: 800 USD to "Timeout Demo Beneficiary" → approve → execute → `FAILED`, balance unchanged → execute → `EXECUTED_SIMULATED`.
8. (3:10) Verify chain → VALID.

## Video storyboard (optional deliverable, ≤ 5 minutes) — STATUS: NOT YET RECORDED
| Shot | Duration | Screen | Voice-over |
|---|---|---|---|
| 1 | 0:00–0:20 | Title card + UI banner | "TuitionBridge: an AI agent that plans, checks and proves a cross-border tuition payment. Everything you'll see is a simulated sandbox." |
| 2 | 0:20–1:00 | Compare table | "Four providers ranked by what you actually send. The engine decomposes fee and FX margin; the explanation is generated by a model but validated against these numbers." |
| 3 | 1:00–1:40 | Prepare + approve + execute | "A locked quote, ten deterministic risk checks, explicit approval, sandbox settlement, balance debited once." |
| 4 | 1:40–2:30 | Role switch, 403s | "Permissions live on the server. A planner cannot approve; nobody can reach production — Tier 4 is disabled in code." |
| 5 | 2:30–3:20 | Blocked cases | "Caps, reserve and beneficiary screening block with reasons, and every block is logged." |
| 6 | 3:20–4:00 | Timeout and retry | "A provider timeout fails safely with no debit; the retry succeeds, and it still cannot double-pay." |
| 7 | 4:00–4:30 | Audit verify + tests | "A hash-chained audit log, verified live; sixty automated tests." |
| 8 | 4:30–4:50 | Closing card | "Thank you." |
Recording: 1920×1080, browser zoom 125%, OBS or built-in screen recorder; export MP4 H.264; check text legibility at 720p; keep under 5:00.
__TB_EOF__

w docs/11_SUBMISSION_CHECKLIST.md <<'__TB_EOF__'
# Submission Checklist

## Current package status

**Team:** TuitionBridge FinTech Lab
**Track and topic:** International track, Topic C (Cross-border & Student Finance Assistant)
**Public source repository:** https://github.com/sleader3221-dot/tuitionbridge-fintechathon-2026

| # | Deliverable | Location | Status |
|---|---|---|---|
| 01 | Technical documentation | `docs/05_TECHNICAL_DOCUMENTATION.md`, `docs/04_SYSTEM_ARCHITECTURE.md` | Complete in Markdown; export to PDF only if the organizer requires it. |
| 02 | Presentation, up to 10 minutes | `slides/PRESENTATION_DECK.pptx`, `slides/SPEAKER_NOTES.md` | 14-slide deck generated. Four demo screenshots are embedded; visually inspect it in PowerPoint before submission. |
| 03 | Demo video, optional, up to 5 minutes | Storyboard in `docs/10_DEMO_RUNBOOK.md` | Not recorded. Optional according to the provided checklist; confirm current rules. |
| 04 | Source, README, tests, repository URL | Repository root, `README.md`, `tests/` | Public repository exists. 60 tests passed in the recorded run; see `evidence/test_results/`. |
| 05 | Security self-assessment | `docs/06_SECURITY_SELF_ASSESSMENT.md`, `docs/09_KNOWN_RISKS.md` | Complete. |
| 06 | Execution evidence | `evidence/operation_logs/`, `evidence/test_results/`, `evidence/screenshots/` | Scenario logs, test output, and screenshots are present. Screenshots and deck still need human visual review. |
| — | Team roster and eligibility | Private working template outside this repository | Two-member roster is expected by the user; second member details and organizer eligibility criteria still need confirmation. |
| — | Registration and delivery channel | Official competition website and registration form | Current recipient address and international-track cutoff were not verified from accessible official page text. Confirm with the organizer before sending identity documents. |

## Deadline and delivery checks

A previous working note listed **20 October 2026, 23:59 China Standard Time (20 October 2026, 21:29 India Standard Time)**. China Standard Time is 2 hours 30 minutes ahead of India Standard Time. The current official website displays 2026 competition information, but the accessible page text does not establish the international-track submission deadline or delivery email. Check the current international-track notice or registration confirmation before relying on any date or recipient.

Official site: <https://fintechathon.g-ican.com/>

Do not send passport pages to an address copied from a secondary listing. Verify the recipient through the current official registration flow or directly with the organizer.

## Package contents

The repository contains the source, test results, scenario logs, screenshots, and generated PowerPoint deck. Build a clean archive from the committed revision with `git archive`; this omits ignored local files such as virtual environments and databases. If evidence or slide files are not tracked in the revision being archived, add them only after reviewing the archive contents.
__TB_EOF__

w docs/12_RESEARCH_SOURCES.md <<'__TB_EOF__'
# Research sources

Accessed 20 October 2026. Type: OFFICIAL = competition rule, PRIMARY = original data source, SECONDARY = reporting/explainer.

| ID | Title | Organisation | URL | Finding used | Decision supported | Type |
|---|---|---|---|---|---|---|
| O1 | PBCSF Appendix 2 — Problem Description and Competition Rules for International Track | Tsinghua PBCSF / WeBank | https://fintechathon.g-ican.com/ | six topics; 40/30/30 weights; F bonus 0–5; deliverables 01–06; deadline 20 Oct 2026 23:59 UTC+8; eligibility 2–5 students, ≥60% non-Chinese; English | whole submission structure | OFFICIAL |
| O2 | ITS International Office listing of the International Track | Institut Teknologi Sepuluh Nopember | https://www.its.ac.id/international/2026/10/06/2026-shenzhen-fintechathon-international-track-a-fully-funded-international-competition/ | confirms deadline, timeline (review 31 Oct, finalists 20 Nov, final 21–23 Nov) | deadline verification | SECONDARY |
| O3 | Scholarship Union listing | scholarshipunion.com | https://scholarshipunion.com/?p=27645 | registration form + passport bio pages emailed to wangyr@pbcsf.tsinghua.edu.cn; deliverables by email | submission channel (to be confirmed officially) | SECONDARY |
| S1 | Remittance Prices Worldwide (home page, latest update) | World Bank | https://remittanceprices.worldbank.org | global average cost of sending remittances 6.36% (Sept 2025 report); 367 corridors | problem statement, slide 2 | PRIMARY |
| S2 | WDI metadata SI.RMT.COST.OB.ZS | World Bank | https://databank.worldbank.org/metadataglossary/world-development-indicators/series/SI.RMT.COST.OB.ZS | methodology: cost of sending USD 200; linked to SDG 10 | definition of "cost" we mirror (fees + FX margin) | PRIMARY |
| S3 | RBI Bulletin table 36, Outward Remittances under LRS | Reserve Bank of India | https://www.rbi.org.in/Scripts/BS_ViewBulletin.aspx?Id=24216 | FY2024-25 total USD 29,563 million; monthly education component reported | corridor scale | PRIMARY |
| S4 | LRS explainer citing Indian Express | Drishti IAS | https://www.drishtiias.com/daily-updates/daily-news-analysis/liberalised-remittance-scheme-1/print_manually | FY25 student remittances ≈ USD 2.92 bn, down 16% | indicative education share | SECONDARY |
| S5 | LRS for sending money abroad from India | ICICI Bank | https://www.icici.bank.in/nri-banking/nriedge/nri-articles/lrs-for-sending-money-abroad-from-india | USD 250,000 annual limit; education permitted purpose; TCS applies | regulatory context (not implemented) | SECONDARY |

Not used: aggregator blog claims about digital vs bank costs (unverified ranges).
__TB_EOF__

w docs/13_SUBMISSION_EMAIL_DRAFT.md <<'__TB_EOF__'
# Submission email draft

To: [VERIFY OFFICIAL SUBMISSION ADDRESS]
Subject: [International Track Submission] Team TuitionBridge FinTech Lab — Topic C — TuitionBridge

Dear Competition Organizing Committee,

Please find below the submission of team **TuitionBridge FinTech Lab** for the 2026 Shenzhen International FinTech Competition, International Track, Topic C (Cross-border & Student Finance Assistant).

Project: **TuitionBridge** — an AI agent that plans, risk-checks and sandbox-executes cross-border tuition payments with server-enforced permission tiers and a tamper-evident audit log.

Deliverables (attached as `TuitionBridge_FinTechathon2026_Submission.zip`; source also at https://github.com/sleader3221-dot/tuitionbridge-fintechathon-2026):
1. Technical documentation — `docs/05_TECHNICAL_DOCUMENTATION.md` (+ `docs/04_SYSTEM_ARCHITECTURE.md`)
2. Presentation deck — `slides/PRESENTATION_DECK.pptx` (+ PDF if requested)
3. Demo video — [attached / link] or "not submitted" if optional
4. Source code — repository with README, deployment instructions and 60 test cases
5. Security self-assessment — `docs/06_SECURITY_SELF_ASSESSMENT.md`
6. Execution evidence — `evidence/` (sandbox operation logs, test results, screenshots)

Team members: complete the roster in the private local submission pack. Attach the registration form and passport bio pages only if required, and only after confirming the official recipient and submission channel.

All execution is simulated in a sandbox; no on-chain or real-money transactions are claimed.

Kind regards,
[CONTACT NAME], on behalf of team TuitionBridge FinTech Lab
[EMAIL] · [PHONE]
__TB_EOF__

w slides/SPEAKER_NOTES.md <<'__TB_EOF__'
# Speaker script — 10 slides, target 8:30, hard stop 10:00

1 (0:00–0:30) Title. "We are TuitionBridge FinTech Lab. Topic C. TuitionBridge is an AI agent that plans, checks and proves a cross-border tuition payment — and it is built so that the model can never move money or invent a number."
2 (0:30–1:30) Problem. "Students pay a few very large transfers a year. Cost hides in the FX margin. The World Bank's global average is 6.36% of the amount sent, over twice the SDG target. Indian residents alone sent 29.6 billion dollars abroad under LRS last year. The pain is cost opacity plus no safe way to delegate."
3 (1:30–2:15) Gap. "Comparison sites show headline rates; banking apps execute with no policy layer; chatbots explain but cannot be trusted with arithmetic. Nobody gives you an agent with limits, approval and evidence."
4 (2:15–3:00) Solution. "Five steps: compare on the amount you actually send; check affordability against a reserve; lock a quote; run deterministic risk checks; execute only after approval, in a sandbox, with a hash-chained audit log."
5 (3:00–3:45) Architecture. "Three boundaries. API validates and authenticates; services enforce tiers and risk; the AI layer is quarantined — it sees the computed plan and returns text we validate." 
6 (3:45–6:15) Live demo or screenshots. Follow `docs/10_DEMO_RUNBOOK.md` steps 2–8.
7 (6:15–7:00) Algorithm and AI boundary. "Quote formula on the slide; send rounds up, delivered rounds down. The grounding validator rejects any number not in the plan — here is the test that proves it."
8 (7:00–7:45) Security. "Five tiers, server-side, Tier 4 hard-disabled. Twenty threats in the self-assessment, sixteen with implemented controls and tests, four honestly marked recommended."
9 (7:45–8:15) Evidence. "Sixty tests, 2.9 seconds. Seven scenario logs produced by the real code. Everything labelled simulated."
10 (8:15–8:30) Close. "What is real: the control plane. What is not: the rates. Next: live rates with provenance and real provider sandboxes. Thank you."
__TB_EOF__

w scripts/build_slides.py <<'__TB_EOF__'
"""Build slides/PRESENTATION_DECK.pptx with python-pptx (pip install python-pptx).
Screenshots from evidence/screenshots/ are inserted when present (plan.png, executed.png, denied.png, audit.png).
Inspect every slide after generation; convert to PDF with LibreOffice if available."""
from __future__ import annotations

import sys
from pathlib import Path

try:
    from pptx import Presentation
    from pptx.util import Inches, Pt
except ImportError:
    sys.exit("python-pptx is not installed: pip install python-pptx")

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "slides" / "PRESENTATION_DECK.pptx"
SHOTS = ROOT / "evidence" / "screenshots"
TEAM = "TuitionBridge FinTech Lab"

SLIDES = [
    ("TuitionBridge", ["Plan it, check it, prove it: an AI agent for cross-border tuition payments",
                       "2026 FinTechathon · International Track · Topic C: Cross-border & Student Finance",
                       f"Team {TEAM} · all execution SIMULATED in a sandbox"],
     "Intro: the model never moves money or invents a number."),
    ("The problem: cost hides in the FX margin", [
        "Global average cost of sending remittances: 6.36% of amount sent (World Bank RPW, Sept 2025)",
        "SDG 10.c target: 3%",
        "Indian residents sent USD 29.56 bn abroad under LRS in FY2024-25 (RBI Bulletin, table 36)",
        "Students make a few very large payments a year, under deadline, from a home-currency account",
        "No safe way to let an assistant act under limits with a human approval"],
     "Cite sources; note education share is secondary reporting."),
    ("What exists and what is missing", [
        "Comparison sites: headline rates, no execution, no affordability",
        "Banking apps: execute, but no policy layer, no explanation",
        "Chatbots: explain, but cannot be trusted with arithmetic or authority",
        "Missing: an agent with limits, approval, evidence"], ""),
    ("The solution in five steps", [
        "1 Compare providers on the amount you actually send (fee + FX margin vs mid)",
        "2 Check affordability against a minimum reserve",
        "3 Lock a quote with an expiry",
        "4 Run deterministic risk checks: caps, reserve, screening, corridor, duplicate",
        "5 Execute only after explicit approval, in a sandbox, with a hash-chained audit log"], ""),
    ("Architecture: three trust boundaries", [
        "API: Pydantic validation, Decimal strings only, API-key principal, rate limit",
        "Services: permission tiers 0–4, account scoping, idempotency, risk policy",
        "AI layer quarantined: computed plan in, text out, number-grounding validator",
        "SQLite persistence; SIMULATED provider adapter; optional Anthropic API for explanations"],
     "Point to diagram 4 in docs/04."),
    ("Demo", ["Compare → Prepare → Approve → Execute (SIMULATED) → replay refused",
              "Permission denial · Tier 4 refused · caps and screening block · timeout and retry · audit verified"],
     "Run live from docs/10_DEMO_RUNBOOK.md or use the screenshot slides that follow."),
    ("Core algorithm and the AI boundary", [
        "customer_rate = mid × (1 − margin); fees = fixed + round(send × pct)",
        "receive = round_down((send − fees) × customer_rate); cost_vs_mid = send − receive ÷ mid",
        "Target mode solves send upward, re-quotes, nudges by one minor unit until receive ≥ target",
        "Hand-checked: 1,000 USD via bank-wire archetype → send 92,269.24 INR (4.09% cost)",
        "LLM may only restate plan numbers; any invented figure → rejected, labelled fallback"], ""),
    ("Security and compliance", [
        "Tier 0 read · 1 analyse · 2 prepare · 3 sandbox execute · 4 production = disabled in code",
        "Enforced in the service layer for every request; denials audited",
        "20 threats modelled; 16 controls implemented and tested; 4 marked recommended (TLS, IdP/MFA, real screening, multi-node)",
        "Decimal-only money, injection guard, redaction, SHA-256 audit chain with verify endpoint"], ""),
    ("Evidence", [
        "60 automated tests: unit, security, integration — 60 passed in 2.85 s",
        "7 scenario logs generated by the real application (evidence/operation_logs)",
        "Screenshots of the running UI; everything labelled SIMULATED / SYNTHETIC",
        "Reproducible: scripts/setup.sh · run.sh · test.sh · make_evidence.py"], ""),
    ("What is real, what is next", [
        "Real: the control plane — policy, approval, idempotency, recovery, audit, grounded explanations",
        "Not real: rates, providers, screening list (labelled fixtures)",
        "Next: live rates with provenance, provider sandbox APIs, identity + MFA for Tier 3, audit anchoring",
        "Thank you"], ""),
]
SHOT_SLIDES = [("plan.png", "Demo: provider comparison and affordability"),
               ("executed.png", "Demo: approved and executed in sandbox"),
               ("denied.png", "Demo: permission denied, logged"),
               ("audit.png", "Demo: hash-chained audit log verified")]


def add_bullets(prs, title, bullets, notes):
    s = prs.slides.add_slide(prs.slide_layouts[1])
    s.shapes.title.text = title
    tf = s.placeholders[1].text_frame
    tf.clear()
    for i, b in enumerate(bullets):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = b
        p.font.size = Pt(20)
    if notes:
        s.notes_slide.notes_text_frame.text = notes
    return s


def add_picture(prs, title, path):
    s = prs.slides.add_slide(prs.slide_layouts[5])
    s.shapes.title.text = title
    # Fit the full screenshot below the title, including portrait evidence captures.
    max_width = prs.slide_width - Inches(1)
    top = Inches(1.4)
    max_height = prs.slide_height - top - Inches(0.5)
    picture = s.shapes.add_picture(str(path), 0, top)
    scale = min(max_width / picture.width, max_height / picture.height)
    picture.width = int(picture.width * scale)
    picture.height = int(picture.height * scale)
    picture.left = int((prs.slide_width - picture.width) / 2)
    return s


def main():
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    for i, (title, bullets, notes) in enumerate(SLIDES):
        add_bullets(prs, title, bullets, notes)
        if i == 5:
            for fname, cap in SHOT_SLIDES:
                p = SHOTS / fname
                if p.exists():
                    add_picture(prs, cap, p)
                else:
                    print(f"note: {p.relative_to(ROOT)} missing, screenshot slide skipped")
    OUT.parent.mkdir(exist_ok=True)
    prs.save(OUT)
    print(f"wrote {OUT.relative_to(ROOT)} with {len(prs.slides)} slides")


if __name__ == "__main__":
    main()
__TB_EOF__

w evidence/evidence_index.md <<'__TB_EOF__'
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
__TB_EOF__

python3 - "$ROOT" "$ROOT/../tuitionbridge.zip" <<'__TB_ZIP_PY__'
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import zipfile

root = Path(sys.argv[1]).resolve()
archive = Path(sys.argv[2]).resolve()
excluded_dirs = {".git", ".venv", ".pytest_cache", "__pycache__", ".mypy_cache", ".ruff_cache"}
excluded_names = {".env"}
archive.parent.mkdir(parents=True, exist_ok=True)
tracked = subprocess.run(
    ["git", "-C", str(root), "ls-files", "-z"],
    stdout=subprocess.PIPE,
    stderr=subprocess.DEVNULL,
    check=False,
)
if tracked.returncode == 0:
    candidates = (root / Path(name) for name in tracked.stdout.decode().split("\0") if name)
else:
    candidates = root.rglob("*")
fd, temporary = tempfile.mkstemp(prefix="tuitionbridge.zip.", suffix=".tmp", dir=archive.parent)
os.close(fd)
try:
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(candidates):
            if not path.is_file():
                continue
            relative = path.relative_to(root)
            if any(part in excluded_dirs for part in relative.parts):
                continue
            if path.name in excluded_names or path.suffix.lower() in {".db", ".pyc"} or path.name.endswith((".db-wal", ".db-shm")):
                continue
            if path.resolve() == archive:
                continue
            zf.write(path, Path(root.name) / relative)
    os.replace(temporary, archive)
except BaseException:
    try:
        os.unlink(temporary)
    except FileNotFoundError:
        pass
    raise
print(f"Created {archive} ({archive.stat().st_size} bytes)")
__TB_ZIP_PY__
echo "Batch 3 added; submission archive rebuilt without local environments, caches, or databases."
