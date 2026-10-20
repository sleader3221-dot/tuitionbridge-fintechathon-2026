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
