# docs/part-20-nebius-sre-interview/24-terraform-for-resilient-gpu-clusters.md
- ## What the interviewer is testing | 280 | NO FIGURE NEEDED interview context and evaluation criteria
- ## The core ideas | 20 | NO FIGURE NEEDED section introduction
- ### 1. A cluster module is an API, and its inputs decide what mistakes are possible | 520 | COVERED(p3-2024-module-api-repos)
- ### 2. Remote state, locking and why the state is the crown jewel | 430 | COVERED(p3-2024-lock-race)
- ### 3. State splitting and blast radius | 440 | COVERED(p3-2024-split-by-rate)
- ### 4. Safe changes: read the plan, guard the stateful things, keep history | 650 | COVERED(p3-2024-guards-two-layers)
- ### 5. Node pool design for GPUs: capacity, zones, drivers and upgrades | 580 | COVERED(p3-2024-pool-design-questions)
- ### 6. Drift, and why the plan is a health check | 280 | COVERED(p3-2024-drift-three-way)
- ### 7. Secrets in a world where state is plain text | 250 | COVERED(p3-2024-secrets-in-state)
- ### 8. Testing a module before it touches a cluster | 470 | COVERED(x24-test-pyramid)
- ### 9. CI/CD for infrastructure | 330 | COVERED(x24-ci-plan-gate)
- ### 10. Disaster recovery of the state itself | 310 | COVERED(x24-state-restore-order)
- ## How to answer out loud | 410 | NO FIGURE NEEDED spoken interview answer scripts
- ## Worked scenarios | 10 | NO FIGURE NEEDED section introduction
- ### Scenario A. A plan says one destroy | 380 | COVERED(x24-key-rename-destroy)
- ### Scenario B. Apply deleted a production node pool | 430 | COVERED(p3-2024-pool-deleted-order)
- ### Scenario C. The state bucket is deleted | 240 | NEEDS FIGURE concrete bottom-up import loop in dependency order with zero-diff plan verification
- ## Hands-on lab | 420 | NO FIGURE NEEDED command line steps and verification walkthrough
- ## Drill questions | 300 | NO FIGURE NEEDED question and answer drill
- ## Common mistakes and weak answers | 210 | NO FIGURE NEEDED list of interview failure modes
- ## Connections to the rest of the handbook | 160 | NO FIGURE NEEDED cross-references to other chapters
- ## Sources and review notes | 460 | NO FIGURE NEEDED source citations and review notes
- ### Verification log | 240 | NO FIGURE NEEDED verification table and audit details

Specs kept 1, dropped 0: []
