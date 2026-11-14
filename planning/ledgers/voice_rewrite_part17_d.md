# Voice rewrite ledger, Part 17 chapters 10 to 12 (run D)

Scope: `docs/part-17-operations/10-cluster-lifecycle-upgrades-and-change-management.md`, `11-incident-response-and-game-days.md`, `12-capacity-planning-and-cost-optimisation.md`. Not touched: `planning/EXTERNAL_EDITS.md` (rulebook step 6 ignored on instruction), other chapters, code, commits.

Method: each file was rewritten with a full Write after reading it end to end, then grown and trimmed with Edit passes. Front matter, the metadata table, every heading (text and order), every fenced block (`text`, `markdown`, `yaml`, `bash`, `sql`, Mermaid), every table, all 20 checkpoint blocks and the Sources and review notes tail are byte-identical to HEAD.

## Word counts (`wc -w`, whole file)

| File | Before | After | Growth |
|---|---|---|---|
| 10 cluster lifecycle and upgrades | 6120 | 8226 | +34.4 percent |
| 11 incident response and game days | 6837 | 8781 | +28.4 percent |
| 12 capacity planning and cost | 5814 | 7536 | +29.6 percent |

Chapter 11 is just above the +28 floor. The locked checkpoint and Sources tails are large, so the body grew by well over 30 percent in each chapter.

## Gates (run on the final files)

- `python3 tools/rewrite_guard.py HEAD WORKTREE <file>`:
  - 10: `1 chapters, 0 with hard failures. words 5324 -> 7430. new numbers 0, lost numbers 0, new code spans 0, lost 0`
  - 11: `1 chapters, 0 with hard failures. words 5500 -> 7444. new numbers 0, lost numbers 0, new code spans 0, lost 0`
  - 12: `1 chapters, 0 with hard failures. words 4976 -> 6698. new numbers 0, lost numbers 0, new code spans 0, lost 0`
  - residue: chapter 12 had one "the book" (section 2.3, "The book argues"); reworded to "That chapter argues" so the residue count is 0.
- `python3 tools/restore/chain_gate.py <file>`: 10 = 0.0, 11 = 1.1, 12 = 0.1 per 1000 words. All pass the 1.5 hard limit. Chapter 11 stays above the 0.2 target only because of semicolon chains inside the locked IC responsibilities table (section 3.1). Tables are locked by rule 5, so they were not changed.
- Span check (inline code spans, fences removed), all three: `{}` (no missing spans).
- Checkpoint count: 20, 20, 20 (HEAD 20, 20, 20). Checkpoint blocks and Sources tails byte-identical (checked with a string compare of the tail from `## Checkpoint questions`).
- Heading text and order: identical to HEAD in all three (checked with a diff of `grep '^#'`). One heading was lost during a first pass in chapter 12 (`### 5.1 The components`) and restored before this check.
- Exclamation marks in prose: none. Outcome phrases ("will be able to", "should be able to", "by the end"): none left in any body.
- Raw `<` or `{` added in prose: none.
- Math `$...$`: none in prose. Chapter 12 section 3.1 keeps the original "$3.20" in prose (currency, not math). It is the only `$` in prose.
- Not run: `node tools/check_mermaid.mjs` and `npm run build`. The run instructions say no npm build. The Mermaid blocks are byte-identical to HEAD, so no new diagram syntax was added.
- Number words: the guard counts digits only. I also checked number words (two, three, four, twice and so on). Quantity words I had added (for example "four upgrade types", "two suspects", "two owners", "three checks", "Three questions", "twice") were replaced with non-numeric wording. Remaining number words are the ones HEAD already had, plus "one" used as a pronoun.

## Shape checks

- Every section opens with a situation sentence. Where a locked heading sits above (Outcomes, Prerequisites, Exercises, Checkpoint questions, Hands-on lab, "Capacity and cost at a glance"), the situation is the first sentence under it. In chapter 12 the Mermaid block under "Capacity and cost at a glance" is preceded by a situation paragraph, and the Mermaid block itself is unchanged.
- Outcomes lists in chapters 10 and 11, and the outcomes list in chapter 12, are rewritten as a plain paragraph of what the chapter walks through. No outcome-style lines remain.
- Failure sections (8.x, 7.x, 6.x) lost their bold "Symptom", "Diagnosis" and "Fix" labels. The three ideas are plain sentences in the same order, following the part 17 chapters 01 to 03 precedent.
- Bold: chapter 10 keeps its one bold sentence in the intro ("Before you upgrade a GPU fleet..."). Chapter 11 keeps its one bold sentence in the intro and the two table bold labels from HEAD. Chapter 12 keeps its one bold sentence and the bold lead words in the table. Exercise titles in all three chapters are bold, as in HEAD (six bold titles per chapter, see unresolved item 6).
- Exercises: six per chapter, same titles and same solution-sketch text. Prompts were rewritten as one situation plus one question. Chapter 10 exercise 1 and exercise 4 solution sketches were split so no sentence carries more than two numbers. Exercise 4 is split into two sentences (180 nodes and 15 minutes; then 25 percent).
- Lab steps: same step count (chapter 10: 9.2 to 9.8; chapter 11: 8.2 to 8.9; chapter 12: 7.2 to 7.7), same commands, same `# expected:` comments. Step prose has one situation and at most one question per sentence.
- Honest status: chapter 10 lab intro says the commands "were not run on hardware for this book" (kept from HEAD). Chapter 11 lab intro says the lab is **untested** in this repository (kept from HEAD); a second "untested" sentence in section 8.9 was removed. Chapter 12 lab intro keeps **untested** in this repository; the sentence in 7.7 about the lab not being tested against a live cluster was reworded. Locked Sources tails keep their own "not run" and "untested" lines.
- Invented attribution: none. Book and chapter references in the body are the ones HEAD already made. Chapter 12 section 2.3 keeps "AI Systems Performance Engineering, chapter 2"; "The book argues" was changed to "That chapter argues" with the same source.
- Semicolon chains: none added in prose (chain gate 0.0 to 0.1 for chapters 10 and 12).
- Chapter 12 WORKLIST item (line 33, "17.12 section 6.1 blurs forecast and actual"): section 6.1 now says plainly that the forecast is the prediction and the actual is what the cluster used. The numbers (156, 100, 56) and the "assumed actual" note are unchanged. Owner to confirm the item is closed.
- Chapter 10 section 6.2 keeps the "inference, must be tested in staging" wording and the NVIDIA page statement from HEAD. No new claim was added about rollback behaviour.

## Needs source (general explanations added in prose, not attributed to any book)

Chapter 10:
- Kernel module meaning; GPU driver as a kernel module.
- One-line definitions of CUDA and NCCL.
- SLO as a written target for behaviour.
- Canary pool, soak time, and drain policy meanings.
- Cordon, drain, and uncordon meanings (draining moves work off a node; uncordon makes it schedulable again).
- Controller meaning (keeps comparing desired and actual state, then acts).
- Load balancer as the place where the traffic switch happens in blue/green.
- Backup meaning; stateful workload as one that keeps data that matters.
- CI pipeline behaviour (a failing stage stops later stages).
- Pull request meaning and what `gh` does.
- PodDisruptionBudget meaning; `preStop` hook meaning; eviction and reschedule behaviour.
- etcd as the cluster state database; a snapshot as the nearest thing to an undo for the control plane.
- Control plane and node pool meanings; surge node meaning.
- "High end of latency" as the place to look because averages hide the slowest users.
- Xid as numbered GPU driver error codes (the table keeps the term; the prose gloss is new).

Chapter 11:
- IAM meaning (identity and access management).
- Runbook meaning; purpose of an acknowledgement.
- Dead man's switch explanation ("silence becomes the signal"). The attribution to Production Kubernetes, chapter 9, is HEAD's own and was not checked in this run.
- Rollback needs no root-cause knowledge (general reasoning, consistent with checkpoint 8).
- Handoff risk between stages; the advice to record handoff points.
- Three triage questions (what changed, who is affected, is it getting worse). Advice, not sourced.
- MTTA, MTTM and MTTR expanded in prose as means of acknowledge, mitigate and resolve; "look at individual incidents behind an average".
- Game day roles (one person injects, one responds, one keeps the timeline). Practice advice.
- Blameless meaning; post-mortem as a record for later readers; a repeated action item means the earlier fix did not stick.
- Fallbacks for the paging tool (phone tree, status page).
- On-call handover content and written IC rotation.
- Cadence as a promise to stakeholders; late update with a reason.
- SEV-1 decision rule: "if customers cannot use the service at all, it is a SEV-1" (added as a reading aid for the table; owner to confirm it matches the team's policy).
- "A SEV-1 is the one case where normal planning stops for the people involved" (opinion; owner to confirm).

Chapter 12:
- FinOps meaning (managing spend with finance and engineering from one set of numbers).
- Network egress and licensing meanings; cost centre meaning; IAM meaning.
- HBM as the high-bandwidth memory on the GPU.
- Spot as capacity the provider can take back.
- p99 as the response time nearly all requests beat.
- Why the buffer multiplies the grown fleet, not the old one (explanation of the formula's order).
- "A single strong quarter can look like a trend" (opinion).
- "A workload with large memory may look idle on the compute graph" (general explanation).
- Kubecost namespace reasons; a default admin password on a shared Grafana as a risk.
- Reading the script's behaviour: it multiplies the inputs it is given (inferred from the expected output in HEAD, not from the script source).
- Freeing GPUs for an hour a day is worth less than round-the-clock (arithmetic logic).
- Commitment length changes what the utilisation target measures (explanation; the table numbers are HEAD's).

## Unresolved (for the owner; not changed in this run)

1. Checkpoints are locked by rule 5. Several are recall-style questions that rule 10 would treat as bare definitions. Examples: chapter 10 checkpoint 14 ("How do you pause the driver upgrade..."), chapter 11 checkpoint 5 (what the chapter says went wrong and what three changes it recommends), chapter 12 checkpoint 1 (what should have existed). Owner decision for a later pass.
2. Chapter 11 chain gate 1.1 comes from semicolon chains inside locked table cells (section 3.1 IC responsibilities table). Rule 5 keeps tables; chain gate passes the 1.5 limit.
3. Chapter 11 severity rule and the "planning stops" sentence are a policy claim I added for clarity. Owner to confirm against the team's real severity policy.
4. Exercise titles are bold in all three chapters (six bold titles in one section each). Kept as in HEAD. If the one-bold-idea rule applies to exercise titles, they need a separate decision.
5. Attributions kept as HEAD wrote them and not verified in this run: Production Kubernetes chapters 2, 6 and 9; AI Systems Performance Engineering chapters 1, 2 and its appendix; Zero-to-Hero volumes 7, 8, 10, 16, 19 and 21; Engineering AI Systems chapter 7; AI Factory chapter 8; Scalable Kubernetes Infrastructure for AI Platforms chapter 2; the Meta "Revisiting Reliability" paper; the NVIDIA GPU Operator page dated 2026-11-12.
6. Chapter 10 section 6.2 rollback procedure is an inference from the controller (HEAD's own labelling). It still needs a staging test before anyone relies on it.
7. Chapter 12 trailing "corrected 2026-11-11" line after the Sources section is kept byte-identical, as the tail rule requires.
8. Mermaid check and `npm run build` not run (the run instructions say no npm build). Mermaid blocks are byte-identical to HEAD.
9. Lab status: all three labs remain untested against a live GKE cluster (HEAD status, kept). Chapter 12 lab still needs a pinned Kubecost version (HEAD's own note in the Sources tail).
10. Chapter 12 section 5.2 IAM table and chapter 11 section 6.2 IAM table are HEAD tables and were kept. Their role names (`finops.admin`, `incident.commander`) have not been checked against any real IAM configuration.
