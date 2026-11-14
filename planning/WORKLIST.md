# Worklist and state (updated 2026-11-12)

Per-chapter status table: `planning/STATUS.md` (auto-scaffolded, partly stale). Ledgers: `planning/ledgers/`. Reviews: `planning/review/`.

## Rewrite progress (Kimi/DeepSeek voice)
| Part | State |
|---|---|
| 1 Linux (30) | done by owner with Kimi/DeepSeek, committed |
| 3 Python (17) | done, committed |
| 2 Networking (30) | Claude light polish rejected; deep rewrite by two agents in progress, uncommitted. Check `git status docs/part-02-networking` and ledgers `voice_rewrite_part02_a.md`, `_b.md`. Open: 2.15 exercise 5 "mashed-potato routing" undefined; 2.19 and 2.22 metadata cells say "(untested here)"; SNAT figure about 64k in 2.23 vs about 60,000 in 2.30. |
| 0, 4-20 | not yet rewritten in the new voice (suggested order in README) |

## Open decisions (asked, unanswered)
Checkpoint shrink, chapter merges or splits, a 0.4 bridge chapter, Part 6-8 ordering, deleting the top status tables.

## Open factual issues (verify, then fix minimally or leave; log confirmed-wrong-and-fixed / already-correct / unresolved)
GB300 memory figures differ across 9.4/15.11 vs 9.5 (17 TB); 3FS 68-node/Ceph claim in 13.1-13.3 and 6.21; time-slicing field names possibly wrong in 11.21-11.26; vLLM 0.90 vs 0.92 default; 0.1 Llama 3 figures written from memory; Nebius Token Factory SLA statements conflict across docs/sales/legal; Nebius role text only on aggregator copies. No human has read any new chapter; nothing ran on GPUs, real Slurm, bare metal or live Nebius. Part 18 is thin; Parts 7-8 code-span density high.

## Fix worklist A (Parts 16-18)
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

## Fix worklist B (Parts 1-15)
- Gem-book abbreviations still in prose (find with this script, fix each by using the full book title and chapter): python3 - <<'E' ... re.compile(r"\b(ASP|HLW|SCL|KUR|NPA|AUR|TUR|NK|KPG|PK)\b") over docs/part-*/*.md with code fences removed. About 27 hits in 17 files, for example 1.7, 1.5, 15.12, 11.27, 10.4, 10.3, 19.1, 6.25, 6.27, 15.10, 10.2, 12.18. ASP means *AI Systems Performance Engineering*, HLW *How Linux Works*, SCL *Supercomputers for Linux Sysadmins*, PK *Production Kubernetes*. Also code/lab output blocks may keep labels that scripts print, leave those.
- 11.13: the 60 and 85 percent utilisation figures are unsourced (author's Volume 23 notes). The tables and checkpoint Q2 still state them without that caveat: add it or remove them. 11.x Sources sections keep old "validation pass 2026-10-25" lines: rewrite as plain provenance or delete if they are process notes.
- 15.2: lines near 123, 124, 346 give 1,979 BF16 and 3,958 FP8 which are WITH-sparsity figures, dense is 989 BF16 and 1,979 FP8; line near 767 says 989 to 1,979. Fix all and label sparsity. code/part15/dynamo_disaggregated_serving.py docstring near line 43 says 180/122 for B300 (should be 288 GB, 218 left after 70 GB weights); fix it and keep its test passing (python3 -m pytest code/part15 -q for that file).
- 15.10 "MLA 4.66x", 15.16 "200 ms Nagle stall", 6.30 "PSU N+1": check.
- 14.10: lab output says 16,384-GPU efficiency about 93.9 percent but the table says 94.41 percent: reconcile (find which is computed by the lab code and use it). 14.1 versus 14.12: MFU ranges 35-55 percent versus 40-50 percent: reconcile with a cited source. 14.16: the invented "Ghost Straggler" label sits in a text block: replace with "edge-stage straggler". 14.5, 14.6, 14.8 benchmark figures (SuperOffload, SimpleFSDP, AsyncTP percentages): check against sources or label as vendor claims.
- Broken `$...$` math markup with stray backticks in 12.1, 12.5 to 12.13 and 13.7: repair so the page renders (run the site build is not allowed, so inspect for stray backticks inside $...$ and convert to plain text formulas in a short block if needed).
- 12.21 Figure 9-8 leaf numbering and 13.3 3FS and VAST figures: check against the cited book chapter.
- 10.1: "~17%" one-day NVIDIA drop and "180 GB addressable HBM on B200": check (B200 is 192 GB HBM3e in public spec: verify against the chapter's source). 10.4: B200 "180 GB usable". 10.7: "PCIe envelope restricts power to half of the SXM budget" is loose: check. 10.10: "15 seconds at boot to train 144 NVLink sub-links": check against NVIDIA documentation or soften.
- 5.14, 5.23 and 5.30 still have dense API-name paragraphs: second pass to plain explanation plus a table for the rest.


Note: Kimi rewrote Parts 1 and 3 after this list was written; re-check items touching those parts before acting (gem-book abbreviation scan: regex (ASP|HLW|SCL|KUR|NPA|AUR|TUR|NK|KPG|PK) over prose with code fences removed).

## Part 2 status update (2026-11-13)
Deep rewrite done and committed: words 284,384 to 326,912 across Part 2 (guard 0 hard failures, 776 Mermaid OK, build OK). Weakest remaining (thin, still need walkthroughs): 2.27 lab steps, 2.28 SDN examples, 2.29 Ansible/Nornir/Terraform sections; chapters 2.16-2.25 grew only 10-20 percent versus 11 percent average for 2.1-2.15 and 25-42 percent for 2.26-2.30. 2.15 exercise 5 "mashed-potato routing" undefined. Not human-read. Checkpoint questions and Sources not rewritten.

## Part 2 second deepening (2026-11-13)
2.15 exercise 5 fixed (hot/cold potato wording). 2.19 serialization example corrected to about 0.005 ms and about 140x. 2.27-2.29 and 2.16, 2.17, 2.19-2.22 deepened (Part 2 now about 338k words). Open: 2.15 intro and Sources mention resource segmentation and flow pinning that the body never teaches; 2.21 checkpoint 14 says "seven" classic L2 attacks but the answer covers six (check and reconcile); 2.19 and 2.22 metadata cells still say "(untested here)"; 2.18 and 2.23-2.25 only grew 10-20 percent; checkpoints and Sources not rewritten.

## Part 4 automation status (2026-11-13, uncommitted until all batches finish)
Warm rewrite in progress, small batches of 2-3 chapters per agent (larger batches ran out of context). Done and passing guards: 14-27 (growth +25-43%). Light pass only (+5-13%), being deepened to +25-40%: 1-13 in batches 1-3 and 4-6 (running), 7-9, 10-13 still to do. Ledgers: planning/ledgers/voice_rewrite_part04_*.md. Notes: chapters 20-21 moved some inline code spans into prose (check no command changed); 4.17 GPU tuning table cells checked by agent in batch e (see ledger). After all batches: node tools/check_mermaid.mjs, npm run build, rewrite_guard HEAD WORKTREE docs/part-04-automation, then commit. Remove any remaining 'untested here' in Part 4 first (grep -rli).


## Part 4 DONE and committed (2026-11-13)
All 27 chapters warm-rewritten (190,750 to 266,133 words), gates green. Next: Part 5 Kubernetes. Method that worked: batches of 2-4 chapters per agent, edit section by section, run only rewrite_guard + chain_gate per chapter, full Mermaid + build once at the end. Some exercises lost inline code spans (181 per guard); not human-read.

## Status update 2026-11-13 (Parts 5, 6, 7 and next steps)
- Part 5 Kubernetes (35 chapters): warm rewrite DONE and committed (6412960). +29 percent words. Open: Needs-source lists in planning/ledgers/voice_rewrite_part05_*.md; checkpoints and Sources not rewritten.
- Part 6 HPC and Slurm (31 chapters): DONE and committed (43d879a, 0ab0931). 6.1 was drafted by Haiku in opencode then deepened by Claude. Open: Needs-source lists in voice_rewrite_part06_*.md; lab steps in 6.7 only lightly touched; the Bacula example names in 6.27 and the duplicate Exercises block in 6.29 are original issues left for an owner decision.
- Part 7 Redfish and BMC (15 chapters): chapters 7.1-7.12 rewritten (+25 to +32 percent). 7.13-7.15 were delegated last; check `git status docs/part-07-redfish-bmc` and `planning/ledgers/voice_rewrite_part07_*.md` for the true state, then run the gates and commit.
- Part 8 BCM (16 chapters): 8.1-8.3 delegated; rest not started.
- NEXT: finish Part 7 (commit), then Part 8, then Part 9 (NVIDIA systems), then 10, 11 (not 11.31-11.34), 12-15, 16-19, 20, 0.
- Process that works (use it again): two agents at once, 3 chapters each; brief points to planning/HAIKU_REWRITE_INSTRUCTIONS.md sections 0-3 as the rulebook (tell the agent NOT to edit EXTERNAL_EDITS.md) plus a tone-bar chapter, e.g. docs/part-06-hpc-slurm/02-*.md; every agent writes its OWN new ledger file (voice_rewrite_partNN_<letter>.md, never overwrite another); say "start editing immediately, do not report until the files are rewritten" (several agents reported early without editing, and SendMessage-resuming them did not help: start a fresh agent instead). After all batches: rewrite_guard HEAD WORKTREE on the whole part, chain_gate, `node tools/check_mermaid.mjs`, `npm run build`, then commit only that part's docs and ledgers. Check lost code spans by set comparison (the guard's span count has pairing artifacts). Ask the owner before commits unless the owner already said to commit.
- Standing owner instruction (2026-11-13): commit each finished part, then continue with the next volume. If the usage limit is hit, resume after it resets.

## Part 7 committed with an open span-restoration item (2026-11-13)
Literal Counter comparison (HEAD vs worktree, code fences removed) shows inline code spans that were turned into plain words by the rewrite, although agents reported none lost: 7.1 (about 25 spans: ssh, kubectl, 8U, AST2600, I2C, SMBus, 10.148.0.0/16, lan, power, mc, sensor, sdr, user, channel, sol, -I lan, -I lanplus, 623, ipmitool mc reset cold, conman, powerman, iKVM, credentialsoverview --inverse, code/part07/oob_sim.py, code/part07/cred_audit.py), 7.2 (generic), 7.3 (GET, PUT, DELETE, OPTIONS, If-Match), 7.14 (plan x2, bmc, mc). Fix: restore the backticks in prose where the original had them (compare `git show <commit-before>:<file>`), do not change code blocks. After any batch, run this Counter check (script is in the 2026-11-13 session transcript: spans() = Counter of backticked text outside ``` fences; print old - new) on every chapter, because the guard's span count has pairing artifacts but agents also over-trusted it. Parts 5 and 6 were checked only partly (6.8-6.10 clean); run the same check there.

## Status update (Parts 7, 8, 9 done) 2026-11-13
- Part 7 committed (2315acc, spans fixed 7266ad1). Part 8 committed (e4f971e, +34 percent). Part 9 committed (14 chapters, +44 percent words; 9.13 numbers are restated from its own code blocks, verified). Part 10 (22 chapters) in progress: batches a (10.1-10.3) and b (10.4-10.6) delegated; next 10.7 onward.
- Before every commit run the literal span check (Counter of backticked text outside fences, HEAD vs worktree) on the part; Part 5 and Part 6 still need that check run.
- Owner decisions pending: first-person headings locked in 8.13 and 8.15; 8.14 says 13 steps but lists nine; 6.27 Bacula names; 6.29 duplicate Exercises block; 9.13 exercise 5 room power cap 120 kW (table) vs 150 kW (text).

## Status update: Part 10 committed (2026-11-13)
Part 10 GPU and CUDA (22 chapters, 182,197 -> 252,122 words, +38 percent): gates green, span check clean, Mermaid and build pass. Guard shows 2 expected "hard" failures in 10.17 (9 fences) and 10.18 (11 fences): prose that the original had wrongly placed inside ```text fences was turned into normal paragraphs; content preserved, accepted. Open: 10.14 section 1.2 contradiction (Not Selected explanation vs table row); 10.17 PDL "supported on Hopper and Blackwell" sentence needs confirming; 10.21 Xid 62/79 kept per catalog but not rechecked; Needs-source lists in voice_rewrite_part10_*.md.
Part 11 (GPU Kubernetes): 11.1-11.3 done, 11.4-11.6 and 11.7-11.9 delegated, rest not started. Skip 11.31-11.34 (NVKE) per README. Next after Part 11: Parts 12-15, 16-19, 20, 0.

## Part 11 status (2026-11-14)
Chapters 11.1-11.30 rewritten in the warm voice (+37% words, guard 0 hard, chain <=0.1, spans 0 lost, Mermaid 776 ok, build ok). 11.31-11.34 (NVKE) untouched on purpose. Open: "(tested here)" headings in 11.21-11.27, 11.25 time-slicing field names. Part 12 in progress (12.1-12.6 running).

## Part 12 status (2026-11-14)
Chapters 12.1-12.24 rewritten and committed (6 commits, +28-34% words, guard 0 hard, chain <=0.1, spans 0 lost, Mermaid 776 ok, build ok). Open: the guard flagged one bare "100" lost in 12.12 exercise titles (unidentified); "(untested here)"/"(tested here)" spans kept in locked headings and code comments (span check wins); 21.x "the book" attributions now name the gem book, owner to confirm; 12.22 checkpoint answers contain `$...$` with stray backticks (locked tail). Part 13 (9 chapters) next.

## Parts 13 and 14 status (2026-11-14)
Part 13 (9 ch) and Part 14 (16 ch) rewritten and committed (+28-31% words, guard 0 hard, chain <=0.2, spans 0 lost, Mermaid 776 ok, build ok). Open items are in ledgers voice_rewrite_part13_*.md and part14_*.md: 13.5 interview "3 hours" vs "180 minutes" vs 45.3 min cold wait (owner to reconcile); 13.2 "tenfold gap" is 2.33x; 14.2 HBM fragmentation 20-30% vs 20.4-38.2%; 14.7 "four ways" vs three listed; 14.11 elastic agent walkthrough needs torchrun-doc check. Part 15 (18 ch) in progress.
