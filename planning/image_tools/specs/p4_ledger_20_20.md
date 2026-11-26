# docs/part-20-nebius-sre-interview/20-autoscaling-gpu-inference.md
- ## What the interviewer is testing | 300 | NO FIGURE NEEDED conversational interview framing and scope
- ## The core ideas | 10 | NO FIGURE NEEDED structural section header
- ### 1. Why CPU and GPU utilisation fail for LLM engines | 580 | COVERED(x20-utilisation-saturates-queue-grows)
- ### 2. Signals that work, and the difference between leading and lagging | 460 | COVERED(p3-2020-signal-ramp-test, p2-2020-leading-lagging)
- ### 3. The HPA formula, with a worked example | 450 | COVERED(p3-2020-hpa-guard-rules, x20-hpa-two-syncs-worked)
- ### 4. Stabilization windows and flapping | 480 | COVERED(p3-2020-window-defaults, x20-stabilization-window-rolling-max)
- ### 5. Scale-up latency, broken down | 560 | COVERED(p2-2020-scale-up-clock, m20-20-1)
- ### 6. Minimum replicas, X+1, and cost against latency | 440 | COVERED(p3-2020-floor-tradeoff)
- ### 7. Scale-down safety and connection draining | 700 | COVERED(p3-2020-who-dies-scaledown, x20-scale-down-termination-steps)
- ### 8. Cluster autoscaler and GPU node pools | 520 | COVERED(p3-2020-ca-pending-to-node)
- ### 9. Multi-model fleets and placement | 450 | NEEDS FIGURE comparison of dedicated vs shared multi-model placement and disaggregated prefill-decode scaling
- ### 10. What other platforms do, kept separate from Nebius | 160 | NO FIGURE NEEDED short comparative summary of external research
- ## How to answer out loud | 450 | NO FIGURE NEEDED interview dialogue recommendations
- ## Worked scenarios | 15 | NO FIGURE NEEDED structural section header
- ### Scenario A. The HPA arithmetic during a burst | 230 | NO FIGURE NEEDED covered by x20-hpa-two-syncs-worked in section 3
- ### Scenario B. The ramp that no reaction can catch | 210 | COVERED(p3-2020-ramp-headroom)
- ### Scenario C. The sawtooth and the cut streams | 210 | COVERED(p3-2020-sawtooth-two-fixes)
- ### Scenario D. The finance question | 130 | NO FIGURE NEEDED numerical walkthrough referencing section 6 table
- ## Hands-on lab | 400 | NO FIGURE NEEDED command-line test instructions
- ### The files | 1500 | NO FIGURE NEEDED Python simulation and YAML manifests
- ## Drill questions | 600 | NO FIGURE NEEDED flashcard study questions
- ## Common mistakes and weak answers | 300 | NO FIGURE NEEDED list of interview antipatterns
- ## Connections to the rest of the handbook | 120 | NO FIGURE NEEDED cross reference links
- ## Sources and review notes | 450 | NO FIGURE NEEDED bibliography and citations
- ### Verification log (fact-check pass, 2026-11-09) | 180 | NO FIGURE NEEDED changelog log

Specs kept 1, dropped 0: []
