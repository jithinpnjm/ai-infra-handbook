# docs/part-20-nebius-sre-interview/18-how-llm-serving-fails.md
- ## What the interviewer is testing | 220 words | NO FIGURE NEEDED plain intro and interview context
- ## The core ideas | 30 words | NO FIGURE NEEDED introductory sentence
- ### 1. Every failure is a story about three places where a request can wait | 290 words | COVERED(p2-2018-three-waits, m20-18-1)
- ### 2. Queue growth and TTFT spikes | 270 words | COVERED(p2-2018-queue-triage)
- ### 3. KV-cache exhaustion and preemption | 340 words | COVERED(x18-kv-budget)
- ### 4. Long-context head-of-line blocking | 270 words | COVERED(p2-2018-long-prompt-block)
- ### 5. GPU OOM at startup versus at load | 300 words | COVERED(p2-2018-startup-or-runtime)
- ### 6. CUDA and NCCL hangs and Xid errors | 520 words | COVERED(p3-2018-hang-health-lies)
- ### 7. Slow weight load, cold start and thundering herd on restart | 370 words | COVERED(x18-herd-load)
- ### 8. Probes that hurt: liveness kills and silent pool shrink [vendor] | 400 words | COVERED(p3-2018-silent-shrink, x18-liveness-loop)
- ### 9. Retry amplification during a partial outage | 260 words | COVERED(p3-2018-retry-attempts)
- ### 10. Noisy tenants | 160 words | NEEDS FIGURE gateway prompt-token breakdown reveals starvation masked by aggregate metrics
- ### 11. Quality failures: finish_reason drift, corruption, speculative decoding and quantisation | 460 words | COVERED(p2-2018-quality-checks)
- ### 12. Version skew between router and engine | 240 words | COVERED(p3-2018-metric-deprecation)
- ### 13. A decision tree, an alert-to-cause table and a classifier | 680 words | COVERED(p3-2018-alert-to-cause, m20-18-2)
- ## How to answer out loud | 360 words | NO FIGURE NEEDED interview script patterns and verbal walkthroughs
- ## Worked scenarios | 30 words | NO FIGURE NEEDED section intro
- ### Scenario A. The 16-request burst | 390 words | COVERED(p3-2018-burst-sim)
- ### Scenario B. Pods restart under load | 210 words | NO FIGURE NEEDED liveness cascade and silent shrink loop covered in section 8
- ### Scenario C. A rolling restart of eight replicas | 140 words | COVERED(p3-2018-rolling-restart-gap)
- ## Hands-on lab | 240 words | NO FIGURE NEEDED command line exercise steps
- ## Drill questions | 380 words | NO FIGURE NEEDED recall questions and answers
- ## Common mistakes and weak answers | 260 words | NO FIGURE NEEDED bullet list of interview pitfalls
- ## Connections to the rest of the handbook | 130 words | NO FIGURE NEEDED navigational cross-references
- ## Sources and review notes | 250 words | NO FIGURE NEEDED citations and methodology
- ### Verification log (fact-check pass, 2026-11-09) | 180 words | NO FIGURE NEEDED verification log

Specs kept 1, dropped 0: []
