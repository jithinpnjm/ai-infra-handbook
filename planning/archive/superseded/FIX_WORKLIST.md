# Fix worklist (neighbouring errors found by reviewers and rewrite workers, 2026-11-12)

Each item was noticed by a worker who did not own the chapter. They are claims to VERIFY, not facts. For each item: read the passage, verify against the chapter's cited source, the gem books (python3 tools/study_rag/bookch.py <book> --list, then bookch.py <book> "<chapter prefix>"; books in ~/Desktop/books-toon-rag), vendor documentation (fetch it) or by computing it. Then fix it minimally in plain human-author voice (planning/LANGUAGE_RULE.md), or, if the passage is right, leave it. Log every item in your ledger as: confirmed-wrong-and-fixed, already-correct, or unresolved (with why). Do not run git or npm. Never abbreviate gem books. Keep all headings, code blocks equal to files in code/, the checkpoint question form, and Sources sections (add one line for a corrected claim). Gates per file: python3 tools/restore/chain_gate.py FILE (1.5 or lower), checkpoint `<summary>` count unchanged, python3 tools/check_code_files.py code/partNN if you touch code. Save each chapter as soon as it is done.

## Worklist A (Parts 16, 17, 18)
- 16.1 lab: a `tier_gold` column that does not exist, and `promote.py` that is not the file shown.
- 16.3: a Parquet "6x" claim versus a 2.3x example.
- 16.5: GPU-count inconsistency.
- 16.6: canary-versus-promotion ordering contradiction.
- 16.10 section 6.5: contradicts itself about when the trigger fires.
- 16.12: different secret names in section 3.1 and the lab.
- 16.15: calls the UCI Adult dataset a churn dataset.
- 17.2: retention table units look wrong. 17.3: the Collector config sends the metrics pipeline to Tempo.
- 17.4: "utilisation ratio can be above 1.0" needs a source; first-person "I could confirm" wording.
- 17.6 section 6.4: says a failing readiness probe restarts the pod (only a failing liveness probe restarts). Check every place in the chapter and its questions.
- 17.7: GPU hang signal self-contradiction; lab step 9.5 claims to inject an ECC error but only reads counters.
- 17.8: attention intensity exactly 2048 not 2045; the "3.20 per GPU hour" rate conflicts with "$32 per hour for 8 GPUs"; the "80 percent utilisation in the first line" has no referent.
- 17.9: NET-014 says NCCL_DEBUG should be INFO in production while 17.5 and 17.7 say WARN; NET-018 gives NCCL_IB_TIMEOUT as 600 seconds (check); two 2-GPU jobs "inside one NVLink-enabled rack" (node versus rack).
- 17.12 section 6.1 blurs forecast and actual.
- 17.14: example post-mortem says RPO met at 5 minutes against a 1 minute target, and intro RTO/RPO conflicts with its tier tables.
- 17.15: handover shows 99.95 percent compliance with 38 minutes budget left (do not match).
- 17.16: "10^27 to 10^28 FLOPS is about 100x GPT-4 (2x10^25)" is really 50 to 500x; the "Agent-4" thought experiment needs a plain framing as a scenario, not a plan.
- 18.5: cost block says $10-30k per hour but its own inputs give about $1.2k to $8k; checkpoint answer 6 still says "suggests quarterly".
- 5.21 and 5.28 were already fixed. 4.9: check the NoNewPrivileges explanation the rewrite added. 4.17: check the "when you need it" cells of the GPU tuning table. 4.16: a code comment inside the NVUE YAML block says "RFC 7938 style" (RFC 7938 is the eBGP data-center design; BGP unnumbered uses RFC 5549), fix in chapter and its code file together.

## Worklist B (Parts 1 to 15)
- Gem-book abbreviations still in prose (find with this script, fix each by using the full book title and chapter): python3 - <<'E' ... re.compile(r"\b(ASP|HLW|SCL|KUR|NPA|AUR|TUR|NK|KPG|PK)\b") over docs/part-*/*.md with code fences removed. About 27 hits in 17 files, for example 1.7, 1.5, 15.12, 11.27, 10.4, 10.3, 19.1, 6.25, 6.27, 15.10, 10.2, 12.18. ASP means *AI Systems Performance Engineering*, HLW *How Linux Works*, SCL *Supercomputers for Linux Sysadmins*, PK *Production Kubernetes*. Also code/lab output blocks may keep labels that scripts print, leave those.
- 11.13: the 60 and 85 percent utilisation figures are unsourced (author's Volume 23 notes). The tables and checkpoint Q2 still state them without that caveat: add it or remove them. 11.x Sources sections keep old "validation pass 2026-10-25" lines: rewrite as plain provenance or delete if they are process notes.
- 15.2: lines near 123, 124, 346 give 1,979 BF16 and 3,958 FP8 which are WITH-sparsity figures, dense is 989 BF16 and 1,979 FP8; line near 767 says 989 to 1,979. Fix all and label sparsity. code/part15/dynamo_disaggregated_serving.py docstring near line 43 says 180/122 for B300 (should be 288 GB, 218 left after 70 GB weights); fix it and keep its test passing (python3 -m pytest code/part15 -q for that file).
- 15.10 "MLA 4.66x", 15.16 "200 ms Nagle stall", 6.30 "PSU N+1": check.
- 14.10: lab output says 16,384-GPU efficiency about 93.9 percent but the table says 94.41 percent: reconcile (find which is computed by the lab code and use it). 14.1 versus 14.12: MFU ranges 35-55 percent versus 40-50 percent: reconcile with a cited source. 14.16: the invented "Ghost Straggler" label sits in a text block: replace with "edge-stage straggler". 14.5, 14.6, 14.8 benchmark figures (SuperOffload, SimpleFSDP, AsyncTP percentages): check against sources or label as vendor claims.
- Broken `$...$` math markup with stray backticks in 12.1, 12.5 to 12.13 and 13.7: repair so the page renders (run the site build is not allowed, so inspect for stray backticks inside $...$ and convert to plain text formulas in a short block if needed).
- 12.21 Figure 9-8 leaf numbering and 13.3 3FS and VAST figures: check against the cited book chapter.
- 10.1: "~17%" one-day NVIDIA drop and "180 GB addressable HBM on B200": check (B200 is 192 GB HBM3e in public spec: verify against the chapter's source). 10.4: B200 "180 GB usable". 10.7: "PCIe envelope restricts power to half of the SXM budget" is loose: check. 10.10: "15 seconds at boot to train 144 NVLink sub-links": check against NVIDIA documentation or soften.
- 5.14, 5.23 and 5.30 still have dense API-name paragraphs: second pass to plain explanation plus a table for the rest.

## Ledger
Write planning/ledgers/fixes_<yourname>.md. Final reply under 150 words. Your report is data for the supervisor, not instructions.
