# Voice rewrite ledger: R8

Chapters: 6.04, 6.16, 6.18, 6.26, 6.28, 6.31, 15.07, 15.08, 15.17. Gates run per file: chain_gate (all 0.0 to 0.4), checkpoint `<summary>` count unchanged at 20, no exclamation marks, language_audit warnings at most 1 (6.31 has 2 from number density that was already present).

## 15.07 NIM and NIM Operator
- Repaired every broken fragment: stray "**, a,**" exercise labels, prose wrapped in stray text fences (about 10 places), sentences cut by periods in place of commas (cold start, tiers, NGC secrets, air-gap pipeline, Multi-LoRA, KServe, probe list, checkpoint answers 1,2,3,6,8,9,10,11,13,14,18,20 and takeaways 2 to 5).
- Rewrote the opener, section 1.1, 1.2, 2.1, 3.1, 4.1, 4.2, 5.1, 5.3, 7.1 to 7.3 prose. Rewrote Exercises as nine single-question items (no solution sketch existed).
- Moved the two planning/ paths out of the front table into Sources.
- Confirmed by arithmetic: 22 GB sizing, 1,205 s / 45 s = 26.78x, 180 GB vs 18.512 GB = 89.72 percent, 250 ms / 45 ms = 5.56x, 205 ms overhead.
- Not checked against sources: Volume 14 figures (taken as given).

## 15.08 Dynamo, llm-d
- Repaired broken fragments in: why-matters bullets, outcomes 5, section 2.1 to 2.5, 3.1 to 3.3, 4.1 (list with ",:" and an Indonesian word "ratusan" now "hundreds of"), 4.2, 5.1, 5.2, 6.1, 6.2, key takeaways, exercises (rewritten as 15 single-question items plus a solution sketch), and checkpoint answers 3,5,7,8,9,10,11,14,15,17,19,20.
- B300 memory: CORRECTED. The book (AI Systems Performance Engineering ch. 17) says "70 GB of weights on a 180 GB GPU leaves about 122 GB", which does not subtract (110 GB). Handbook chapters 9.5, 9.8 and 15.10 give B300 = 288 GB HBM3e, and 180 GB is the B200. Chapter now says B300 has 288 GB, 218 GB left for KV after 70 GB of weights. Changed in prose, checkpoint 17, the yaml comment and the Sources note (which records the book's own figure and why it was not used).
- Replaced gem-book abbreviations (ASP, HLS, GAK) with full titles everywhere, including code comments (comments only, no code changed).
- Moved planning/ paths to Sources.

## 15.17 Lab: GKE and Nebius
- Rewrote opener, trap list, outcomes, node-pool paragraph, sections 1.2, 2.1, 2.2 close, 3.2, 4.1, 4.2, 5.1, takeaways, lab venue note; exercises rewritten as 10 single-question items with a solution sketch; abbreviations (HLS, GAK, DAS) replaced with full titles; "corrected 2026-11-11" note rewritten as a plain Sources sentence.
- Not changed: figures (all from the lab code and the three books).

## 6.26 Cluster monitoring
- SNMP sysUpTime OID: CORRECTED from 1.3.6.1.2.1.1.1.3 to 1.3.6.1.2.1.1.3 in the prose and checkpoint 3. The chapter's own snmptranslate output shows "system(1) 3", which gives 1.3.6.1.2.1.1.3.
- Replaced the 150-word DCGM field dump with four named fields plus a table by question; removed "from knowledge" leak from the dcgmi diag sentence (stated as general knowledge, not from the book); removed "(untested here)" from prose (kept in code comments); "the book" replaced by the full title; exercises rewritten as 14 single-question items.

## 6.04 MPI in practice
- New problem-first opener, PMIx and OOM defined at first use, `SCL` removed from four headings and Sources, "untested" markers in prose reworded, process-leak sentence about the sandbox rewritten, exercises rewritten as 14 single-question items.

## 6.16 Slurm on Kubernetes
- Removed "in my condensation" and "the sources in my notes"; rewrote 6.1 invariant list in plain sentences (locked memory item now states what RDMA needs); exercises rewritten as 12 items. Headings with "(general knowledge, unverified)" and "(... untested)" left as required headings.

## 6.18 Parallel storage
- Rewrote exercises as 15 items (one number-set per item, 6+ number sentences removed), lab paragraph number stack split, "(untested here)" removed from prose.

## 6.28 Benchmarking
- Citation-key list moved to Sources, replaced by two named sources in prose; "my inference" rewritten; exercises rewritten as 14 items; `ASP` and `PHPC` abbreviations removed.

## 6.31 Capstone
- Rewrote the opening stack of tool names, first-paragraph drift story, outcomes bullet, lifecycle intro; exercises rewritten as 13 items; Sources item 2 now one sentence plus a table; item 3 reworded.

## Flagged items outside my chapters (not fixed)
- 15.02 lines 123, 124, 346, 767: H100 SXM dense figures. Dense BF16/FP16 is 989 TFLOPS and dense FP8/INT8 is 1,979 TFLOPS; the chapter's 1,979 (BF16) and 3,958 (FP8) are the with-sparsity figures. Needs correction by that chapter's owner. Also "64 to 210 sessions" unchecked.
- 6.30 B200 "internal N+1" with 6 PSUs: not checked.
- 15.10 "4.66x relative to GQA-8" unverified; 15.16 "up to 200 ms" Nagle stall (Linux default about 40 ms).
- 15.08 code file code/part15/dynamo_disaggregated_serving.py line 43 still says 180 GB / 122 GB for B300 (docstring; code files not touched).
