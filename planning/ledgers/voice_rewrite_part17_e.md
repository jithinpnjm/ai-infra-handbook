# Voice rewrite ledger, Part 17 chapters 13 to 16 (run E)

Scope: `docs/part-17-operations/13-reliability-engineering-for-ai-infrastructure.md`, `14-disaster-recovery-and-data-resilience.md`, `15-on-call-runbooks.md`, `16-ai-assisted-operations-and-scaling-toward-very-large-clusters.md`. Not touched: `planning/EXTERNAL_EDITS.md` (rulebook step 6 skipped on instruction), other chapters, code, commits.

Method: each body (front matter through the Exercises block) was rewritten as a whole, section by section. Front matter, the title, the metadata table, every heading, every fenced block (bash, yaml, python, promql, text, markdown, Mermaid), every table and every inline code span were copied from HEAD. The checkpoint block and the Sources tail were spliced in byte-for-byte from HEAD (`## Checkpoint questions` to end of file). The splice script lives outside the repo.

## Word counts (`wc -w`)

| File | Before | After | Growth |
|---|---|---|---|
| 13 reliability engineering | 6370 | 8868 | +39.2 percent |
| 14 disaster recovery | 6303 | 8581 | +36.1 percent |
| 15 on-call runbooks | 5880 | 8143 | +38.5 percent |
| 16 AI-assisted operations | 8061 | 10893 | +35.1 percent |

## Gates (run on the final files)

- `python3 tools/rewrite_guard.py HEAD WORKTREE <file>`, all four: `0 chapters with hard failures`; new numbers 0, lost numbers 0, new code spans 0, lost 0.
  - 13: `words 5741 -> 8239`; 14: `5267 -> 7545`; 15: `4842 -> 7105`; 16: `6947 -> 9779` (the guard counts without fences).
- `python3 tools/restore/chain_gate.py <file>`: 0.0 per 1000 words on all four (target 0.2 or lower).
- Span check (inline code spans, fences removed), all four: `{}` missing, `{}` added.
- Checkpoint count unchanged (20 in each). Checkpoint blocks and Sources tails are byte-identical to HEAD.
- Exclamation marks in prose: none.
- Outcome phrases ("will be able", "should be able", "By the end"): none left in the bodies.
- Honest status: one body sentence per chapter. 13 and 16 lab intros say the commands were not run on hardware for the book. 14 and 15 lab intros say the lab is untested in this repository. The second status sentences in the lab wrap-ups (13 section 7.7, 14 section 8.8, 15 section 7.9, 16 section 8.8) were reworded so the body has one honest-status word.
- Not run: `node tools/check_mermaid.mjs` and `npm run build` (the run said no npm build). Mermaid blocks are byte-identical to HEAD, confirmed by the guard's code-block check.

## Shape checks

- Each `##` and `###` section opens with a situation sentence ("Picture ...", "Imagine ...", "Suppose ..."). Where a locked heading sits above (Outcomes, Exercises, How it fails, Hands-on lab), the situation is the first sentence under it.
- Outcomes lists in 13, 14, 15 and 16 are rewritten as a plain paragraph of what the chapter walks through. No "will be able to" lines remain.
- Exercises: titles, counts (6 in each chapter), solution sketches and the intro sentence (rewritten) are kept. Lab step counts and commands are unchanged. 15 section 7 keeps 7 steps (7.2 to 7.8 plus 7.9 questions) and 16 section 8 keeps 6 steps (8.2 to 8.7 plus 8.8 questions); 13 section 7 keeps 5 steps (7.2 to 7.6) plus 7.7 questions; 14 section 8 keeps 6 steps (8.2 to 8.7) plus 8.8 questions.
- Bold: the three-part "Symptom / Diagnosis / Fix" labels in 13 section 6 and 14 section 7 were turned into plain sentences. Bold list lead-ins in 13 section 1.4, 14 "Three things" list and 16 section 5.6 were removed. Bold that remains in prose: 13 "Why this matters" (one bold line), 16 section 1.1 and 6.3 (one each). Bold inside locked tables (for example the 14 backup-type and RTO/RPO matrix rows) and exercise titles were kept as HEAD had them.
- Numbers: no digit was added to the prose (guard: new numbers 0). Two number words that were not in HEAD were removed during review ("two days", "two in the morning"). "Picture" openers use only words already in the chapter, or "a few", "a dozen", "thousands", "a whole quarter".
- Semicolon chains: none added (chain gate 0.0 on all four).
- Raw `<` or `{` in prose: none added. The remaining cases are inside locked tables (for example `< 300 ms` and `< 25%` cells) and inside fenced code.
- Math `$...$`: none in these four chapters.
- Gem books: no abbreviations added. Attributions are the ones HEAD already made (Production Kubernetes chapters 2, 4, 9 and 14; NVIDIA Zero-to-Hero volumes 10 and 19; AI Systems Performance Engineering, Table 4-4 in the tail). Nothing new was attributed to a book.

## Needs source (general explanations added in prose, not attributed to any book)

Chapter 13:
- Service level indicator (SLI) and service level objective (SLO) spelled out at first use; p99 meaning ("the slowest tail of requests").
- Model quality as a concern separate from speed and uptime (explanation).
- Error budget and burn rate as a fuel-tank analogy (analogy only).
- Incident commander (IC) meaning; blast radius meaning (the users and systems an experiment could touch).
- Grafana as an open dashboard tool; NVLink as NVIDIA's high-speed GPU link inside one server.
- ECC (error-correcting code memory) and what an uncorrectable error is.
- Spare-teller analogy for repair time; spare house analogy for regional failover.
- Advice lines (not sourced): "the drill is the only proof the restart works", "freeze non-critical work", "a rule that depends on memory fails on the bad night".

Chapter 14:
- Pre-warmed, air-gapped and zone meanings; warm standby and cold standby meanings.
- Synchronous versus asynchronous replication described with a registered-post analogy.
- Etcd as the key-value store holding cluster state; control-plane member meaning.
- KubeFed and cluster API federation as tools that let one control plane manage several clusters (explanation).
- Standby cluster meaning; CronJob meaning; Pod meaning; staging meaning; retention meaning; checksum meaning; object versioning meaning.
- Ransomware meaning; S3 (Amazon Web Services object storage) and GCS (Google Cloud Storage) expansions.
- Origin of the "air gap" term (a physical gap of air between networks).
- Advice: "a bucket the cluster's account can write to is not truly air-gapped" is HEAD's point, restated; the separate-accounts advice is general practice.
- Advice: an audit log an attacker can rewrite "shows a clean story".

Chapter 15:
- MTTA (mean time to acknowledge) and MTTR (mean time to resolve) meanings.
- Heartbeat alert meaning; Git and continuous integration (CI) meanings; API meaning; annotation meaning; template meaning.
- Paging schedule meaning; PagerDuty as the paging service.
- Claim (inference, needs a check): "a threshold that still says 90 against a ratio metric will never fire". Follows from the unit change in the HEAD note; confirm against the 17.4 mapping.
- Claim (inference): "a stale step or copied node name gets through because a reviewer was tired" is advice, not sourced.

Chapter 16:
- Trace, span, traceback, Xid (numbered NVIDIA driver error code written to the system log) meanings.
- Prophet as a forecasting library that separates trend and seasonal rhythms; FinOps meaning; RMA (return merchandise authorisation) meaning.
- Kueue flavor, ClusterQueue and LocalQueue meanings; namespace meaning; Helm meaning (package manager for Kubernetes objects).
- Courier and traffic-cop analogies for replication and the load balancer.
- Advice (not sourced): hold out confirmed anomalies before training; a summary that names a cluster-level pattern is safer than one that names a root cause; the peer comparison "does not need a long history".
- Claim (opinion): "most rows in the validator-failure table are about people". Reader reading of the table; flag if the owner wants it removed.

## Unresolved (for the owner; not changed in this run)

1. Checkpoints are locked by rule 5. Several are recall or definition-style and would fail rule 10 for Parts 16-18. Examples: 13 checkpoint 8 ("Why does the chapter say a team with SLOs ...") and 14 checkpoint 8 ("Why does replication lag count against your RPO?"). Owner decision for a later pass.
2. Repeated opening verb. The word "Picture" opens most subsections (24 to 40 times per chapter). It meets the situation rule, but a reviewer may find it formulaic. A later pass can vary the verb ("Imagine", "Suppose", "Think of a team").
3. Raw `<` in locked table cells (13 section 1.2 and 1.3, 14 section 6.1 SLO column, 15 section 5.1 and 5.3). These are HEAD table cells, so they stay.
4. Bold in locked table rows (14 section 2.1 backup-type table, 14 section 1.3 matrix) and bold exercise titles were kept as HEAD had them.
5. Attributions kept as HEAD wrote them and not verified in this run: Production Kubernetes chapters 2, 4, 9 and 14; NVIDIA Zero-to-Hero volumes 10 and 19; AI Systems Performance Engineering Table 4-4 (13 tail); Meta's Llama 3 paper figures (13 section 1.4, kept as HEAD).
6. 13 section 3.3: the claim that the current PodChaos CRD has no scheduler field (kept as HEAD). Not re-checked in this run.
7. 14 section 3.1 and 8.2: the Storage Transfer Service command and the `gsutil` note are HEAD commands and were kept. Not run.
8. 15 section 1.4: the dcgm-exporter 4.9.0 note is HEAD's content, rewritten as a plain blockquote. Its link `04-dcgm-exporter-and-interpreting-gpu-metrics.md#14-what-dcgm-exporter-490-renamed` was kept. Anchor not checked in this run.
9. 16 section 1.1 and 3.1: the PromQL and the Python snippets are HEAD code, kept byte-identical. Not executed.
10. The lab in each chapter is untested against a live GKE cluster. The honest-status sentence is kept once in each lab intro.
11. `node tools/check_mermaid.mjs` and `npm run build` were not run (see Gates).
12. `planning/EXTERNAL_EDITS.md` was not edited, per the run instruction to skip step 6.
