# docs/part-20-nebius-sre-interview/16-design-gpu-fleet-health-and-capacity.md
- ## What the interviewer is testing | 275 | NO FIGURE NEEDED interview context and problem framing
- ## The core ideas | 10 | NO FIGURE NEEDED structural section divider
- ### 1. A failing GPU shows up in three places before the customer notices | 260 | COVERED(p3-2016-three-places)
- ### 2. The signals, with their real names | 340 | COVERED(p3-2016-xid-gauge-trap)
- ### 3. What each Xid means for the fleet | 360 | COVERED(x16-xid-policy)
- ### 4. Passive and active checks | 340 | COVERED(p3-2016-passive-active-ladder)
- ### 5. Kubernetes node problem detector: where it fits | 250 | COVERED(p3-2016-detect-decide-act)
- ### 6. The node lifecycle | 190 | COVERED(p2-2016-node-words, m20-16-1)
- ### 7. Blast radius: how automation avoids draining the fleet | 550 | COVERED(x16-blast-radius)
- ### 8. Spare pool and X+1 sizing | 470 | COVERED(p3-2016-repair-time-spares, x16-spare-math)
- ### 9. Silent capacity loss: nodes that never rejoin | 310 | COVERED(p3-2016-silent-capacity-layers)
- ### 10. Draining a node that is serving inference | 550 | COVERED(x16-grace-period, m20-16-2)
- ### 11. A fleet-level capacity SLO | 250 | COVERED(p3-2016-capacity-slos)
- ### 12. The vendor RMA flow, at a conceptual level | 280 | COVERED(p2-2016-rma-queue)
- ## How to answer out loud | 480 | NO FIGURE NEEDED verbal interview coaching scripts and speaking outline
- ## Worked scenarios | 10 | NO FIGURE NEEDED structural section divider
- ### Scenario A. Three GPUs report Xid 79 within five minutes | 200 | COVERED(p3-2016-xid79-triage)
- ### Scenario B. The spare pool for a growing fleet | 180 | COVERED(p3-2016-spare-growth)
- ### Scenario C. A node has been cordoned for nine days | 150 | COVERED(p3-2016-cordoned-nine-days)
- ## Hands-on lab | 600 | NO FIGURE NEEDED executable test commands and Prometheus rule definitions
- ## Drill questions | 350 | NO FIGURE NEEDED review questions and answers
- ## Common mistakes and weak answers | 180 | NO FIGURE NEEDED list of interview pitfalls
- ## Connections to the rest of the handbook | 110 | NO FIGURE NEEDED cross-reference list
- ## Sources and review notes | 320 | NO FIGURE NEEDED source citations and verification notes

Specs kept 0, dropped 0: []
