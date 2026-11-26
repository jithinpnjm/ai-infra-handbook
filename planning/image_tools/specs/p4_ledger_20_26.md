# docs/part-20-nebius-sre-interview/26-the-stress-interview-production-incident-role-play.md
- ## What the interviewer is testing | 250 | NO FIGURE NEEDED high-level framing and context for SRE role-play interview
- ## The core ideas | 35 | NO FIGURE NEEDED brief transition paragraph introducing six incident response principles
- ### 1. Take control in the first two minutes | 320 | COVERED(p2-2026-first-two-minutes)
- ### 2. Mitigate before you find the root cause | 260 | COVERED(p2-2026-mitigate-first)
- ### 3. Narrate hypotheses in order of likelihood and cost to test | 240 | NEEDS FIGURE 2x2 decision space of likelihood versus test cost with concrete falsification examples
- ### 4. Communicate status on a cadence | 180 | COVERED(p2-2026-status-cadence)
- ### 5. Know when to roll back, and avoid the destructive command | 170 | COVERED(p2-2026-rollback-decision)
- ### 6. How the drill runner works | 750 | NEEDS FIGURE drill session event loop and 100-point scorecard grading architecture
- ## How to answer out loud | 220 | NO FIGURE NEEDED concise conversational templates for common interview questions
- ## Worked scenarios | 100 | NO FIGURE NEEDED intro text outlining format and shared scoring rubric
- ### Incident 1: TTFT spike after a deploy | 450 | COVERED(p3-2026-ttft-evidence-map)
- ### Incident 2: GPU pool shrinking silently | 450 | COVERED(x26-liveness-loop-workers)
- ### Incident 3: KV-cache pressure and a 429 storm | 500 | COVERED(p3-2026-429-storm-math)
- ### Incident 4: Regional partial outage with retry amplification | 500 | COVERED(x26-retry-multiplication-layers)
- ### Incident 5: Model weights download stuck at cold start | 480 | COVERED(x26-cold-start-download-race)
- ### Incident 6: Disk full on a GPU node | 480 | COVERED(p2-2026-df-du-gap)
- ### Incident 7: Certificate expiry | 480 | COVERED(p3-2026-cert-expiry-timeline)
- ### Incident 8: DNS: intermittent resolution failures | 480 | COVERED(p3-2026-ndots-amplification)
- ### Incident 9: etcd latency | 460 | COVERED(p3-2026-etcd-fsync)
- ### Incident 10: Bad config push | 460 | COVERED(x26-config-push-stop-spread)
- ## Hands-on lab | 850 | NO FIGURE NEEDED step-by-step CLI commands and verified console outputs
- ## Drill questions | 420 | NO FIGURE NEEDED drill Q and A cards with expandable summaries
- ## Common mistakes and weak answers | 180 | NO FIGURE NEEDED two-column comparison table of anti-patterns versus replacements
- ## Connections to the rest of the handbook | 120 | NO FIGURE NEEDED cross-reference links list
- ## Sources and review notes | 220 | NO FIGURE NEEDED references, citations, and metadata
- ### Verification log | 180 | NO FIGURE NEEDED audit notes and test platform details

Specs kept 2, dropped 0: []
