# Voice rewrite ledger: Part 15 chapters 01, 02, 03

Scope: docs/part-15-inference/01-the-anatomy-of-an-inference-request.md, 02-batching-the-kv-cache-and-quantization-fundamentals.md, 03-vllm-in-depth.md. Not committed. EXTERNAL_EDITS.md not edited (per run instructions).

## Words (wc -w, HEAD vs worktree)

| Chapter | Before | After | Growth |
|---|---|---|---|
| 15.1 anatomy of an inference request | 12651 | 17705 | +39.9% |
| 15.2 batching, KV cache, quantization | 12612 | 16735 | +32.7% |
| 15.3 vLLM in depth | 14235 | 18976 | +33.3% |

## Gates (run on the files on disk)

- `tools/rewrite_guard.py HEAD WORKTREE <file>`: 0 hard failures in all three. Code blocks, tables, Mermaid, front matter, headings, checkpoint count unchanged.
  - 15.1: new numbers 0, lost numbers 0, new code spans 0, lost 0.
  - 15.2: new numbers 1 (`2.51`), lost 0.
  - 15.3: new numbers 5 (`557`, `24`, `0.84`, `96`, `91`), lost 0. All five are restated from the locked worked examples and reference blocks, not new facts. See Unresolved.
- `tools/restore/chain_gate.py <file>`: 0.1 (15.1), 0.1 (15.2), 0.2 (15.3). All under 0.2.
- Span check (`old - new` on inline code spans outside fences): `{}` for all three.
- Heading list identical to HEAD for all three.
- `node tools/check_mermaid.mjs`: 776 diagrams, 0 failed (whole repo run).
- `npm run build`: not run (the run instructions said no npm build).
- Locked tail (Checkpoint questions and answers, Sources and review notes) is byte-identical to HEAD; the build script copied those blocks from HEAD.

## How each chapter was built

- Each file was written as draft sections, then assembled by a script that copies every code fence, table, checkpoint block and Sources block from `git show HEAD:` in order. The assembler checks the count and kind of each locked block.
- The `Outcomes` headings were kept. Their lists became a short plain paragraph; the first sentence under each is an on-call or platform-team situation.
- Exercises and lab steps keep the same count, commands and spans. Sentences were split to at most two numbers each. Nested (a)/(b) labels were replaced with "first part / second part" wording.
- Bold labels in bullets and key takeaways were removed, so each section carries at most one bold idea.
- Honest status: each chapter keeps one status sentence above its live-hardware steps. Chapter 15.1 uses "remain untested"; 15.2 and 15.3 keep the original `untested` and `untested here` spans, which the span check requires.

## Needs source (general explanations and small claims added in the rewrite)

15.1
- Tokenizer as a translator between words and model numbers; a token as a small chunk of text.
- A tensor as a block of numbers whose shape gives rows, columns and layers.
- Foundation model as a large model trained once and reused for many tasks.
- Poisson arrival as requests landing at random moments with an average rate.
- SLO as a target a team sets for a metric.
- TLS and DMA one-line definitions; CUDA stream as an ordered queue of GPU work.
- GIL as a lock that lets one Python thread run Python code at a time.
- Autoregressive as each new token depending on the tokens before it.
- Pageable memory can be moved or swapped by the OS during a transfer.
- "The compile step fixes the batch and length caps, so changing them means building again" (section 6.1, TensorRT-LLM build).
- Nginx timeouts keep a slow stream from being cut off (section 6.1).
- "Apply these settings to streaming routes only, where the goal is a steady flow of small frames" (section 6.1 guidance).
- A stopping check ends a sequence when the client disconnects, freeing its blocks (section 5.2, restated from the original).

15.2
- Arithmetic intensity as math done per byte read; FP16 as a 16-bit format; a dot product as K multiplications and K additions.
- A rectangular tensor as a grid where shorter rows must be filled in.
- Dequantize as turning packed small numbers back into the larger format before the math runs.
- Chunked prefill trade: a lower token budget gives faster steps but more steps for the prompt; a higher budget does the reverse (section 1.3).
- Sparsity needs the model to be built or pruned to use it (section 1.1).
- "If you later need a longer context, you rebuild the engine" (section 4.2, same point as 15.1).
- Side-channel as a leak carried by timing (section 2.3).
- "Holding a large cache is not free, so the per-request price is not always lower" (section 2.3, read from the cost table).

15.3
- Query, Key and Value roles; softmax as the step that turns scores into weights that sum to one.
- A hash as a fingerprint; LRU as least recently used; reference counts as the number of users of a block.
- "Forking is cheap because only the table is copied" (section 2.1). Consistent with the original's fork description; the cheapness claim is an inference.
- Column-parallel and row-parallel layers and why the pair needs one combining step (section 4.3).
- AllReduce and All-to-All as collective operations, with plain definitions.
- Watchdog timer and replica flapping (section 5.2, 6 Failure Mode 4).
- Batch-invariant kernels as kernels that give the same result however requests are grouped (section 4.2).
- Gather-scatter kernel and LoRA as a small add-on matrix (section 4.4).
- Cache-aware routing and prefix-aware routing as sending requests to the worker that already holds their prefix (section 4.3 and 6 Failure Mode 5).
- Headroom as the free margin the framework needs (6 Failure Mode 2).
- Mixture-of-Experts router picking a few specialist sub-networks per token (section 2.3 analogy).
- Canonical order as the same layout for every request, so hashes match (section 2.3).
- Preemption as pausing a request so another can use its memory (section 3.3).

## Unresolved

- 15.1 length is at +39.9 percent, close to the top of the +25 to +40 range. Not trimmed further; the rulebook says never trim.
- 15.2 has one new number, `2.51`, from the locked SmoothQuant worked example (smoothed activation peak at strength 0.8). Restated, not invented. The text says "about 2.51".
- 15.3 new numbers `557`, `24`, `0.84`, `96`, `91`:
  - `557` (chunk step total), `24` (chunks), `0.84` (cache usage in the crash-fix telemetry), `96` (running requests), `91` (node KV usage). All five appear in the locked code or in the original reference blocks, and the prose restates them.
- Sources and checkpoints are untouched, including the original "Volume 12" labels inside them. The "Volume 12" label was removed from the 15.3 section 5.1 prose (it was a source label, not a fact); the number 12 still appears in other places in the chapter, so the lost-number check stays at 0.
- The 15.3 Part B lab was not run on a live GPU, and the chapter says so. Lab outputs quoted in the locked blocks were not re-run here.
- Mixed attribution in the original (for example Mistral-7B with block_size 16 in one failure mode, Meta-Llama-3-8B in another) was left as it was; those are locked-looking facts in prose, and checking them needs the source material, which this run did not read.
- Original prose had a few stiff bullets (for example the 15.2 AWQ and GPTQ bullets). They were rewritten and their facts kept; no fact was dropped.
