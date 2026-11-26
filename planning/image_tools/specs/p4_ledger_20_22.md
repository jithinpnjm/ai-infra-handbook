# docs/part-20-nebius-sre-interview/22-operating-vllm-triton-ray-and-tensorrt-llm.md
- ## What the interviewer is testing | 340 | NO FIGURE NEEDED interview context and exam framing
- ## The core ideas | 10 | NO FIGURE NEEDED structural section header
- ### 1. Four tools, three layers: engine, server, orchestrator | 370 | COVERED(p2-2022-three-layers, m20-22-1)
- ### 2. What each engine is for | 630 | NEEDS FIGURE comparison of 5 engines by architectural mechanism and ideal workload
- ### 3. The knobs that decide memory | 680 | COVERED(p3-2022-memory-knobs, x22-memory-budget-stack)
- ### 4. The knobs that decide latency: token budget and chunked prefill | 450 | COVERED(p3-2022-token-budget-dial)
- ### 5. Parallelism: tensor, pipeline, data and expert | 480 | COVERED(p2-2022-parallelism-cost)
- ### 6. Quantisation, prefix caching and speculative decoding | 450 | COVERED(p3-2022-prefix-cache-keys, p3-2022-quantisation-example)
- ### 7. Start-up: what takes the time | 430 | COVERED(p3-2022-startup-remedies, m20-22-2)
- ### 8. Health endpoints: what they prove and what they do not | 450 | COVERED(p3-2022-health-per-engine, x22-health-what-each-proves)
- ### 9. Upgrades and version skew | 430 | COVERED(p3-2022-upgrade-changes)
- ### 10. Reading each engine's metrics | 430 | COVERED(p3-2022-metrics-by-question)
- ### 11. The one-page comparison | 220 | NO FIGURE NEEDED multi-dimensional comparison table covers it directly
- ## How to answer out loud | 430 | NO FIGURE NEEDED interview script and dialogue tips
- ## Worked scenarios | 50 | NO FIGURE NEEDED structural scenario header
- ### Scenario A. The command line that passes review and still preempts | 230 | COVERED(p3-2022-cap-vs-cache)
- ### Scenario B. Slow rollout, pods killed during start | 220 | COVERED(x22-startup-probe-budget-timeline)
- ### Scenario C. Picking an engine for a new customer | 200 | NEEDS FIGURE decision flow between 70B strict TTFT, 40 small models, mixed non-LLM, and cluster orchestration
- ## The code | 20 | NO FIGURE NEEDED structural code header
- ### Engine config reviewer | 1200 | NO FIGURE NEEDED Python script with unit tests
- ### Kubernetes Deployment for vLLM | 450 | NEEDS FIGURE pod spec anatomy showing resource limits, shm volume mount, PVC model cache, and probe configuration
- ## Hands-on lab | 280 | NO FIGURE NEEDED CLI verification steps
- ## Drill questions | 380 | NO FIGURE NEEDED drill questions and answers
- ## Common mistakes and weak answers | 140 | NO FIGURE NEEDED list of antipatterns
- ## Connections to the rest of the handbook | 120 | NO FIGURE NEEDED cross-reference navigation list
- ## Sources and review notes | 520 | NO FIGURE NEEDED citation list
- ### Verification log (fact-check pass, 2026-11-09) | 230 | NO FIGURE NEEDED verification changelog

Specs kept 3, dropped 0: []
