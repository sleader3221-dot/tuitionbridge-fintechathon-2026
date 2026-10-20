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
