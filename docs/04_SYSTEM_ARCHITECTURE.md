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
