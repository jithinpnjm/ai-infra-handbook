# docs/part-20-nebius-sre-interview/14-design-dedicated-endpoints-and-safe-model-rollout.md
- ## What the interviewer is testing | 105 | NO FIGURE NEEDED - introductory framing of interview expectations
- ### What is public, and what is my reasoning | 240 | NO FIGURE NEEDED - vendor doc citation breakdown and distinction of public vs reasoned facts
- ## The core ideas | 0 | NO FIGURE NEEDED - section container header
- ### 1. The endpoint as a spec, owned by a control plane | 382 | COVERED(p3-2014-endpoint-lifecycle, m20-14-1) - already covered by lifecycle state machine and control plane diagram
- ### 2. Sizing the endpoint: GPU type, GPUs per replica, min and max | 308 | COVERED(p3-2014-endpoint-sizing) - covered by sizing worked example figure
- ### 3. Cold start has three costs | 267 | COVERED(x14-cold-start) - covered by cold start breakdown figure
- ### 4. Weights distribution and the custom-weights flow | 321 | COVERED(m20-14-2) - covered by weights flow diagram
- ### 5. Readiness versus liveness for an engine | 511 | COVERED(x14-probe-windows) - covered by probe windows diagram
- ### 6. Rolling, blue/green and canary when you cannot double your GPUs | 473 | COVERED(p2-2014-rollout-compare) - covered by rollout comparison table/figure
- ### 7. Surge budgets when GPUs are scarce | 358 | COVERED(p3-2014-surge-contiguity, x14-surge-slot) - covered by surge contiguity and surge slot figures
- ### 8. Traffic shifting with a router, and the gates | 467 | COVERED(p3-2014-decision-order, x14-canary-ladder) - covered by decision flow and canary ladder figures
- ### 9. Automatic rollback signals | 277 | COVERED(p2-2014-rollback-signals) - covered by rollback signals figure
- ### 10. Version skew | 359 | COVERED(p3-2014-version-skew) - covered by version skew cases figure
- ### 11. Scale-to-zero and the minimum replica decision | 288 | COVERED(p2-2014-scale-zero-cost) - covered by scale-to-zero cost figure
- ## How to answer out loud | 370 | NEEDS FIGURE - high-yield summary of the entire interview answer flow across the 5 canonical interview questions
- ## Worked scenarios | 0 | NO FIGURE NEEDED - scenario container header
- ### Scenario A. Eight replicas, one spare GPU | 148 | NEEDS FIGURE - step-by-step trace of rolling update with surge 1 vs surge 0/unavailable 1 vs stall on 0 spare GPUs
- ### Scenario B. Latency is green, quality is not | 185 | COVERED(p3-2014-quality-regression) - covered by quality regression metrics figure
- ### Scenario C. Shipping a custom checkpoint to a live endpoint | 171 | COVERED(p3-2014-custom-checkpoint-timeline) - covered by custom checkpoint timeline figure
- ## Hands-on lab | 165 | NO FIGURE NEEDED - executable step-by-step commands and verification test suite
- ## Drill questions | 276 | NO FIGURE NEEDED - flashcard-style interview drill Q&A
- ## Common mistakes and weak answers | 208 | NO FIGURE NEEDED - bulleted review of pitfall traps and corrections
- ## Connections to the rest of the handbook | 108 | NO FIGURE NEEDED - cross references to other chapters
- ## Sources and review notes | 279 | NO FIGURE NEEDED - bibliographic citations and review log
- ### Verification log | 101 | NO FIGURE NEEDED - verification checklist and log

Specs kept 2, dropped 0: []
