# Voice rewrite ledger, Part 17 chapters 07 to 09 (run C)

Scope: `docs/part-17-operations/07-failure-modes-and-detection.md`, `08-performance-engineering-methodology-and-decision-trees.md`, `09-the-ai-systems-performance-checklist-master.md`. Not touched: `planning/EXTERNAL_EDITS.md` (step 6 skipped on instruction), other chapters, code, commits.

Method: paragraph-level rewrite. Front matter, headings, tables, code fences, Mermaid, the lab step commands and their `# expected:` comments, the solution sketches, checkpoint blocks and the Sources tail are byte-identical to HEAD. Prose paragraphs were rewritten or extended, and new explanatory paragraphs were inserted after existing ones. Each section's first paragraph now opens with a situation (a page at night, a pod stuck in Pending, a checklist row that no one has verified).

## Word counts (`wc -w`)

| File | Before | After | Growth |
|---|---|---|---|
| 07 failure modes and detection | 7919 | 10382 | +31.1 percent |
| 08 performance methodology and decision trees | 7264 | 9429 | +29.8 percent |
| 09 AI systems performance checklist (master) | 16476 | 21904 | +33.0 percent |

## Gates (run on the final files)

- `python3 tools/rewrite_guard.py HEAD WORKTREE <file>`: 0 hard failures on all three. New numbers 0, lost numbers 0, new code spans 0, lost 0. Residue: chapter 08 went from 1 to 0 (the "The book's advice" sentence in the busy-time paragraph was reworded to "The same source advises"); chapters 07 and 09 unchanged at 0.
- `python3 tools/restore/chain_gate.py <file>`: 07 at 0.1, 08 at 0.0, 09 at 0.0 per 1000 words (target 0.2 or lower).
- Span check (inline code spans, fences removed), all three: missing `{}`, added `{}`.
- Raw `<`, `{` or `!` in prose: none outside the locked checkpoint `<details>` lines.
- Not run: `node tools/check_mermaid.mjs` and `npm run build` (the task said no npm build). Mermaid blocks are byte-identical to HEAD.

## Shape checks

- Outcomes: 07, 08 and 09 each have "you will be able to" or "you should be able to" removed. The outcomes list is now a plain paragraph of what the chapter walks through. The list items are deleted.
- "should be able" sentences in body prose: removed from 08 (dashboard permissions sentence, the lab question lead-in) and 09 (security evidence sentence, lab question lead-in). None remain in the body.
- Every section opens with a situation. Table-first sections (07 none; 09 sections 1.1 to 1.3, 2.1 to 2.3, 3.1, 3.2, 4.1 to 4.3) got a one-paragraph situation inserted under the locked heading.
- Bold labels: "Symptom", "Diagnosis" and "Fix" were converted to plain sentences in the How it fails sections of all three chapters (the headings stay). The 09 "Why this matters" bold leads were turned into a plain numbered list. The one bold idea per section rule now holds, except the exercise titles (kept bold as in HEAD) and the bold closing line of 09's "Why this matters".
- Exercises: 6 in each chapter, same titles, same solution sketches. Lab steps: 6 in 07, 6 in 08, 5 in 09, same commands and expected lines. "What to record" lists keep their 5 questions each.
- Honest status, once per body: 07 lab intro ("The commands were not run on hardware for this book"), 08 lab intro ("The lab is untested in this repository"), 09 lab intro ("The lab is **untested** in this repository"). The status sentences that repeated this in 08 section 8.8, 09 section 13.7 and 07 section 9.8 were removed. The Sources tails keep their own locked wording.
- Checkpoints: unchanged (locked by the brief). 07 has 20, 08 has 20, 09 has 20 `<details>` blocks, same as HEAD.
- Numbers: every number from HEAD is kept as written. Digits were not added to prose. One added "99 percent" was caught by the guard and reworded to "almost all requests" in 08, and one "32-bit" in 09 was reworded to "full-precision".

## Wording changes to check

- 07 section 1.1: "holds the tested alert rules" became "holds the alert rules". The word "tested" was dropped because the lab in this chapter is not run. Owner to confirm.
- Several paragraphs restate an original idea in plainer words, for example the warp divergence and occupancy paragraphs in 09 section 2.7. No fact was changed on purpose.
- 09 section 13.7: the lab-status sentence "The lab is **untested** against a live GKE cluster" was removed, leaving the one status line above the lab.

## Needs source (general explanations added in prose, not attributed to any book)

Chapter 07:
- DCGM as the NVIDIA GPU health tool, and what the DCGM exporter publishes.
- HBM3 as the high-bandwidth memory on the GPU package.
- NCCL as the NVIDIA collective library, collective operation, all-reduce, rank, and the PyTorch watchdog as a timer.
- Ansible as a tool that runs a command on many hosts.
- Object storage and client library. HTTP 5xx meaning server failure and 4xx meaning request error.
- cgroup as the Linux memory-limit mechanism, CUDA as NVIDIA's GPU platform, Trivy as an open-source scanner, CVE as the flaw identifier, CI as the build pipeline.
- Pull secret as a stored registry credential. Admission check as the gate before a pod is accepted. Signature as a cryptographic proof. Key rotation meaning.
- KV cache meaning (key-value cache of attention data per request). Backpressure meaning. Drift meaning.
- PrometheusRule as the Kubernetes object that loads alert rules. promtool as a rule checker. Port-forward meaning for the Alertmanager lab step.
- Precision and recall definitions. Hysteresis meaning. Circuit breaker and bulkhead definitions. Inhibit rule meaning. Anti-affinity explanation kept as original.
- Claim that a GPU that fails in silence may print nothing, and claim that a restart before investigation can wipe out evidence.

Chapter 08:
- Grafana as an open-source dashboard tool that can read from Prometheus.
- Nsight Compute as NVIDIA's kernel profiler. SM and copy engine meanings. Tensor Cores as matrix units.
- Roofline picture explanation (roof, slope, flat top) and the claim that the ridge point is a hardware property.
- Element-wise versus large matrix multiply placement on the roofline (left and right of the ridge).
- FlashAttention tiling explanation and the "large table of scores" description of standard attention.
- p99 meaning (now worded as "almost all requests"). Goodput definition. FinOps definition. Latency and cost trade-off framing.
- Speculative decoding and chunked prefill descriptions (chapter 09 side, but added in 08 only as reader guides). Head-of-line blocking definition.
- Claim that a formula-based FLOP count can miss an operator.
- Claim that thresholds drift as workloads change and that a dashboard is only as good as its data feed.

Chapter 09:
- NVLink-C2C as the chip-to-chip link. Pinned memory as memory the OS will not move. TLB, NUMA, jitter, THP explanations.
- Warp, bank, occupancy, spilling, residency, cooperative group, PTX and SASS, CUTLASS, Triton, Perfetto, MLPerf, MIG, MPS, SLURM, Fabric Manager, Transformer Engine, RDMA and RoCE, InfiniBand, cardinality, vLLM, prefill and decode, head-of-line blocking, KV cache, calibration.
- TF32 and BF16 format explanations. The claim that FP8 scaling is mostly handled by Transformer Engine. The 2:4 pattern description (two zeros in every four weights) and "pipeline bubble" name.
- ZeRO explanation of removing duplicate optimizer state. Stale update description for asynchronous SGD.
- Scaling efficiency definition. Claim that a stalled save still stalls the job. Claim that compression can hurt accuracy and needs testing.
- Advice that a silent network fault shows up only as retries or slow steps, and that a regular utilisation dip is easy to find once logged.

## Unresolved (for the owner; not changed in this run)

1. Rule 10 of `planning/RULES_AND_WORKFLOW.md` asks Part 16 to 18 checkpoints to be scenario-style. The three checkpoint sets here are the locked HEAD text, as the brief required, so they remain definition-style in places (for example 07 checkpoint 11, 08 checkpoint 14, 09 checkpoint 9). Needs a separate pass with an agreed rewrite.
2. The "not verified" claims in the original text were kept as they were. The dcgm-exporter 4.9.0 metric renames, the NVL72 bandwidth figures in 09 section 3.3, the Meta interruption counts (checked earlier by the 2026-11-11 corrections, which are in the Sources tail), and the lab expected outputs have not been checked in this run.
3. The math-like `$...$` markers: none present in these three chapters, so nothing to repair.
4. The 07 Sources tail (locked, unchanged) still names "Table 4-4" from the AI Systems Performance Engineering book. Left as written.
5. Mermaid and `npm run build` were not run (see Gates).
