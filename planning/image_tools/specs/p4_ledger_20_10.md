# docs/part-20-nebius-sre-interview/10-complexity-latency-numbers-and-measuring-your-own-code.md
- ## What the interviewer is testing | 150 | NO FIGURE NEEDED introductory meta-guidance for interview context
- ## The core ideas | 10 | NO FIGURE NEEDED structural section header
- ### 1. Say Big-O in a way that survives a follow-up | 450 | COVERED(p2-2010-blocklist-bigo)
- ### 2. The hidden costs of Python operations, measured | 550 | NEEDS FIGURE mechanism of list.insert shifting contiguous memory vs deque.appendleft O(1) head insert
- ### 3. Space against time | 220 | COVERED(p2-2010-set-memory)
- ### 4. The latency numbers, with sources and dates | 450 | COVERED(p2-2010-latency-ladder)
- ### 5. Arithmetic that makes the numbers useful | 600 | COVERED(p3-2010-md1-curve)
- ### 6. Why the p99 of a fan-out is worse than the p99 of one call | 750 | COVERED(p2-2010-fanout-tail, m20-10-1)
- ### 7. Caches and locality | 280 | COVERED(p2-2010-locality-bars)
- ### 8. Measuring your own code with timeit and cProfile | 850 | COVERED(p3-2010-cprofile-anatomy, p2-2010-measure-loop)
- ### 9. Why measured numbers differ from the textbook | 160 | NO FIGURE NEEDED concise conceptual discussion of four divergence factors
- ### 10. Will this loop of ten million items finish in a second? | 450 | COVERED(p2-2010-loop-budget)
- ## How to answer out loud | 300 | NO FIGURE NEEDED interview dialogue scripts and verbal formulas
- ## Worked scenarios | 20 | NO FIGURE NEEDED section container
- ### Scenario A. The blocklist check | 120 | NO FIGURE NEEDED brief worked scenario applying set lookup from section 1
- ### Scenario B. The fan-out dashboard that looks healthy | 120 | NO FIGURE NEEDED brief worked scenario applying fan-out math from section 6
- ## Hands-on lab | 650 | NO FIGURE NEEDED terminal commands, code listings, and verification tests
- ## Drill questions | 350 | NO FIGURE NEEDED review questions and answers
- ## Common mistakes and weak answers | 150 | NO FIGURE NEEDED bullet list of interview pitfalls
- ## Connections to the rest of the handbook | 100 | NO FIGURE NEEDED chapter cross-references
- ## Sources and review notes | 350 | NO FIGURE NEEDED bibliographic sources and citations
- ### Verification log | 120 | NO FIGURE NEEDED editorial verification checklist

Specs kept 1, dropped 0: []
