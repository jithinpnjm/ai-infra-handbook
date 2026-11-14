# Voice rewrite ledger: Part 15 chapters 10, 11, 12 (run d)

Scope: docs/part-15-inference/10-prefill-and-decode-disaggregation.md, 11-advanced-prefill-decode-and-kv-cache-tuning.md, 12-dynamic-and-adaptive-inference-engine-optimisations.md. Nothing committed. EXTERNAL_EDITS.md not touched (per run instructions). Checkpoints, Sources and review notes, code fences, tables, Mermaid, front matter and heading text are unchanged.

## Word counts (wc -w, whole file)

| Chapter | Before | After | Growth |
|---|---|---|---|
| 10 prefill-and-decode-disaggregation | 13893 | 17894 | +28.8% |
| 11 advanced-prefill-decode-and-kv-cache-tuning | 15877 | 20352 | +28.2% |
| 12 dynamic-and-adaptive-inference-engine-optimisations | 25142 | 32186 | +28.0% |

Body-only (rewrite_guard): 10: 10733 -> 14734; 11: 11512 -> 15987; 12: 19436 -> 26480.

## Gates (run from repo root, after the final edit)

- `python3 tools/rewrite_guard.py HEAD WORKTREE <file>`: all three report 0 hard failures, new numbers 0, lost numbers 0, new code spans 0, lost 0. Residue: ch10 2->2, ch11 2->2, ch12 11->11 (unchanged from HEAD; these are original attribution phrases, not new residue).
- `python3 tools/restore/chain_gate.py <file>`: 0.0 per 1000 words for all three (target <= 0.2).
- Span check (inline code spans, HEAD vs worktree): `{}` for all three. One span (`QoSController`, ch10 exercise 5) was dropped during drafting and restored.
- `node tools/check_mermaid.mjs`: checked 776 diagrams, 0 failed (run once, repo-wide script).
- `npm run build`: not run (run instructions said no npm build).

## Number checks

- New digits in prose were removed during drafting (for example a "90th percentile" phrase, "50 GB/s" in an exercise, "10.0 RPS" and "1.6 RPS" in the ch10 2P1D paragraph, "2 a.m.", "9 a.m.", "2,000-token"). Guard shows 0 new numbers for all three.
- Spelled-out scenario words were added in a few analogies (for example "several times the usual traffic", "a small group of GPUs"). They are illustrations, not facts.

## Honest status

- ch10: the lab table keeps `untested here` (span wins). One plain sentence above the lab says the steps were not run on a live cluster.
- ch11: the original hardware-execution note is kept. The lab intro is now a situation.
- ch12: the original Sources note ("not run on live GPU hardware") is kept.

## Needs source (general explanations added, no new facts intended)

ch10:
- Attribution of the claim that the first generated token "does not need to be transferred" was not added; the rewrite only restates the original.
- "The network becomes the bottleneck long before the GPUs do" (4.2), an inference from the saturation numbers already in the chapter.
- Racing: "the price is extra work on the losing branch; reserve it for requests where a slow tail really hurts" (2.5).
- UCX rendezvous explanation in the 6.2 intro (what `UCX_RNDV_THRESH` does).
- "Each tier is larger and slower than the one above it" (4.3 intro).

ch11:
- "The result matches the unsplit computation" is standard online-softmax math; no citation was added.
- "Words like 'the' and 'of' carry little weight ... dropping them saves work without losing much meaning" (LazyLLM explanation, 3.3). Needs a source or a qualifier.
- "Model was trained to rely on [the first tokens]" (sliding-window collapse, 3.3). Explanation, not sourced.
- "Five strategies ... the cheapest of the five when the pair fits on one box" (shared-memory IPC, 4.3).
- Lab intro and exercise intro are scenarios, not claims.
- "TF32, a faster matrix format that the Tensor Cores support" (1.4).
- "Pinned RAM is memory the operating system is not allowed to move" (5.1 Tier 2).
- Cost-per-request decision table advice (6.3). Advice, not a claim.

ch12:
- "Shared memory and L1 come from one on-chip pool on most NVIDIA GPUs" (in the NVIDIA GPUs share one on-chip pool paragraph). Hardware claim, verify against the NVIDIA architecture guide for the target GPU.
- Tree versus ring crossover explanation (collective algorithms). General; the runtime table should record the measured crossover.
- "Autocast covers only..." sentence was kept original, with an explanation that newer formats need their own path. Verify against the PyTorch version in use.
- Compression lossless/lossy explanation.
- Prefetch hit-rate and wasted-bytes guidance, shadow-mode tuner rollout, and rollback guidance are operational advice, not facts.

## Unresolved

1. ch10 section 4.4, original arithmetic inconsistency kept as written: "weights at 70 GB on a 180 GB GPU, which leaves about 122 GB for KV" and the same paragraph's "180 GB minus 70 GB is 110 GB". The numbers were not changed (rule: never restate a number differently). Owner should decide which figure is right.
2. ch10 4.1 and 4.3: a few original statements mix KiB, MiB, and decimal GB. Not touched.
3. ch11 3.2 cites "Volume 12, Chapter 5" and "AI Systems Performance Engineering (Chapter 19)" as original attributions. Kept, not verified in this run.
4. ch11 6.4 and 6.6 keep original forward-looking claims such as "not common in interactive inference" and "Mooncake's early rejection"; left as in the original.
5. ch12 residue count (11) is unchanged from HEAD. Original phrases like "The book notes", "The book labels these experimental" remain. They are attribution, not drafting residue, but a reviewer may want them reworded to "the book" with the full title per the gem-book rule.
6. Math with stray backticks ($...$): not searched for in these three files in this run; none were edited, so none were repaired silently.
7. ch12 "Picture a ..." openers are used heavily. A reviewer may want to vary them.
8. Exercise and lab step lists keep the original counts (ch10: 5 exercises, ch11: 4 exercises, ch12: original count). Lab commands unchanged.
