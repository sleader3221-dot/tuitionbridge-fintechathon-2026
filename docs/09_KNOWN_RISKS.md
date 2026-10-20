# Known risks and limitations

1. **Synthetic market data.** Rates and fees are fixtures; any cost figure in the demo is illustrative. Labels appear in API responses, UI banner, docs.
2. **Demo authentication.** Static API keys stand in for identity; no MFA; no session expiry. Not for real funds.
3. **No real screening.** The blocked beneficiary is a demo flag, not a sanctions or PEP check.
4. **Audit anchoring.** The chain detects tampering within the log but not replacement of the whole database; external anchoring is future work.
5. **Single process.** In-memory rate limiter and SQLite are fine for a demo, not for scale.
6. **LLM optionality.** Without a key the explanation is deterministic; with a key the live integration is exercised only manually.
7. **Regulatory scope.** LRS purpose codes, TCS and institution-side requirements are discussed in research but not implemented.
8. **Demo video.** Optional per the rules; if not recorded before submission it is listed as outstanding in the checklist.
