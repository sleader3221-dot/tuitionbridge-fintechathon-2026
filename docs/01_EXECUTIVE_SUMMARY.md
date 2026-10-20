# Executive summary — TuitionBridge

**Competition:** 2026 Shenzhen International FinTech Competition (FinTechathon), International Track, theme "AI as a Financial Participant".
**Topic:** C — Cross-border & Student Finance Assistant.
**Team:** [TEAM NAME — REPLACE]. **Submission date:** 20 October 2026.

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
