# Checkpoint rewrite report: agent E (chapters 17.11 to 17.16)

All six chapters: 20 questions each, all 20 replaced (none kept, old ones were definition or recall questions). Mix per chapter: 6 scenario, 5 mechanism, 4 trade-off, 3 numbers, 2 debugging order. chain_gate: 17.11 1.4, 17.12 0.2, 17.13 0.0, 17.14 0.0, 17.15 0.0, 17.16 0.0. No questions dropped.

## Errors noticed elsewhere (not fixed)
- 17.14: Section 5.3 example post-mortem says "The RPO was met (5 minutes)" but the critical RPO is 1 minute. The lab step 8.6 itself says the 5-minute RPO misses the 1-minute target.
- 17.14: the "why this matters" block says a typical critical commitment is 4-hour RTO and 1-hour RPO, but the tier tables say critical is 1 hour RTO and 1 minute RPO.
- 17.15: handover example shows 99.95% compliance with 38 minutes of budget left. The chapter itself says they do not clearly match.
- 17.15: the escalation trigger text names an SLO breach trigger but the table has no row for it (the chapter says so).
- 17.16: Section 5.10 says 10^27 to 10^28 FLOPS is "about 100 times" GPT-4 at 2 x 10^25. That is 50 to 500 times.
- 17.12: Section 6.1 example "forecast asked for 156, team used 100" treats forecast growth as already due, so the example blurs forecast and actual.
