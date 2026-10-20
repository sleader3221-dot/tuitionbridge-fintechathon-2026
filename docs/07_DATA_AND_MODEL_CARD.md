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
