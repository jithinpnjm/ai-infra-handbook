# docs/part-20-nebius-sre-interview/12-estimation-toolkit-for-inference-capacity.md
- ## What the interviewer is testing | 270 words | NO FIGURE NEEDED plain prose overview of the interview format and goals
- ## The core ideas | 5 words | NO FIGURE NEEDED structural container heading
- ### 1. The estimation chain | 290 words | COVERED(p2-2012-estimation-chain, m20-12-1)
- ### 2. Weights memory by precision | 410 words | COVERED(p2-2012-weights-precision)
- ### 3. KV-cache memory per token and per request | 430 words | COVERED(p2-2012-kv-per-token)
- ### 4. Concurrent requests per GPU | 370 words | COVERED(m20-12-2)
- ### 5. Prefill is compute-bound, decode is bandwidth-bound | 540 words | COVERED(x12-ridge)
- ### 6. How batching changes the numbers | 480 words | COVERED(x12-batch-curve)
- ### 7. Tokens per second and requests per second per GPU | 410 words | COVERED(x12-gpu-seconds)
- ### 8. GPUs for a target QPS, with headroom and N+1 | 370 words | COVERED(x12-replica-headroom)
- ### 9. Cost per million tokens | 410 words | COVERED(p2-2012-cost-levers)
- ### 10. Utilisation and goodput | 310 words | COVERED(p3-2012-goodput-vs-utilisation)
- ### 11. The sanity checks | 260 words | COVERED(p3-2012-sanity-checks)
- ### 12. Numbers every inference SRE should know | 250 words | NO FIGURE NEEDED reference lookup table of facts and sources
- ## How to answer out loud | 420 words | NO FIGURE NEEDED script outlines and spoken interview phrasing
- ## Worked scenarios | 40 words | NO FIGURE NEEDED structural container heading
- ### Scenario 1: the opening question | 230 words | NEEDS FIGURE worked step-by-step pipeline tracing the 9 sizing calculations
- ### Scenario 2: the long-context customer | 210 words | COVERED(p3-2012-long-context-fit)
- ### Scenario 3: the alert that disagrees with the estimate | 210 words | COVERED(x12-alert-backtrack)
- ### Scenario 4: is the cheaper GPU cheaper per token? | 270 words | COVERED(p3-2012-cheaper-gpu-per-token)
- ## Hands-on lab | 850 words | NO FIGURE NEEDED code listings and terminal execution steps
- ## Drill questions | 490 words | NO FIGURE NEEDED self-study drill questions with expandable answers
- ## Common mistakes and weak answers | 270 words | NO FIGURE NEEDED bulleted list of interview pitfalls
- ## Connections to the rest of the handbook | 120 words | NO FIGURE NEEDED list of cross references
- ## Sources and review notes | 720 words | NO FIGURE NEEDED bibliography and citations
- ### Verification log | 170 words | NO FIGURE NEEDED audit changelog

Specs kept 1, dropped 0: []
