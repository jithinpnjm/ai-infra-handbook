# docs/part-20-nebius-sre-interview/21-request-routing-retries-and-overload-control.md
- ## What the interviewer is testing | 240 words | NO FIGURE NEEDED interview context framing
- ## The core ideas | 10 words | NO FIGURE NEEDED section container
- ### 1. Decide what is safe to retry before you decide how | 380 words | COVERED(x21-retry-commit-point-flow)
- ### 2. Timeouts must nest: client above gateway above engine | 370 words | COVERED(p2-2021-nested-timeouts, m20-21-1)
- ### 3. Why per-request retries amplify an outage | 470 words | COVERED(p3-2021-retry-layers, x21-retry-amplification-loop)
- ### 4. Retry budgets cap the damage | 430 words | COVERED(p3-2021-retry-sim-two-queues, x21-retry-budget-token-bucket)
- ### 5. Exponential backoff with jitter, and the maths | 420 words | COVERED(p3-2021-jitter-maths)
- ### 6. Hedged requests and what they cost on GPUs | 340 words | COVERED(p3-2021-hedge-cost)
- ### 7. Circuit breakers, outlier ejection and the panic threshold | 440 words | COVERED(p3-2021-ejection-cap)
- ### 8. Load shedding, priority, 429 versus 503 and Retry-After | 410 words | COVERED(p2-2021-429-503)
- ### 9. Backpressure on streaming responses | 320 words | COVERED(p3-2021-stream-backpressure)
- ### 10. Cache-aware routing versus load-aware routing | 310 words | COVERED(p3-2021-cache-vs-load)
- ### 11. Connection draining and graceful termination | 490 words | COVERED(x21-rolling-update-sigterm-race)
- ### 12. Failover across regions with data-residency limits | 290 words | COVERED(p3-2021-failover-headroom)
- ### 13. The code, in full | 800 words | NO FIGURE NEEDED complete python and yaml reference implementations
- ## How to answer out loud | 280 words | NO FIGURE NEEDED spoken interview answer scripts
- ## Worked scenarios | 10 words | NO FIGURE NEEDED section container
- ### Scenario A. Two of eight replicas fail and the whole service goes down | 230 words | COVERED(p3-2021-retry-storm-ladder)
- ### Scenario B. A timeout audit | 250 words | COVERED(p3-2021-timeout-audit)
- ### Scenario C. Streams die on every deploy | 240 words | NEEDS FIGURE timeline comparison of default 30s grace period causing SIGKILL stream truncation vs 135s grace period arithmetic
- ## Hands-on lab | 250 words | NO FIGURE NEEDED step-by-step bash commands and test steps
- ## Drill questions | 250 words | NO FIGURE NEEDED interactive interview questions and answers
- ## Common mistakes and weak answers | 240 words | NO FIGURE NEEDED list of common candidate pitfalls
- ## Connections to the rest of the handbook | 100 words | NO FIGURE NEEDED cross-chapter reference links
- ## Sources and review notes | 320 words | NO FIGURE NEEDED citation list and methodology notes
- ### Verification log (fact-check pass, 2026-11-09) | 170 words | NO FIGURE NEEDED factual verification audit log

Specs kept 1, dropped 0: []
