# Voice rewrite ledger: Part 14 chapters 01-03 (batch a)

Scope: `docs/part-14-training-finetuning/` chapters 01, 02, 03 only. Not committed. `planning/EXTERNAL_EDITS.md` deliberately not edited (run instruction overrode step 6).

## Per-chapter results

| Chapter | Words before | Words after | Growth | Guard (rewrite_guard) | Chain gate | Span check |
|---|---|---|---|---|---|---|
| 01-ml-and-deep-learning-fundamentals-for-infrastructure-engineers.md | 15252 | 19677 | +29.0% | 0 hard failures; guard words 11624 -> 16049; new numbers 2; lost numbers 0; new code spans 2; lost 0 | 0.0 per 1000 words | {} |
| 02-transformers-and-llm-architecture.md | 15392 | 19801 | +28.6% | 0 hard failures; guard words 10709 -> 15118; new numbers 0; lost numbers 0; new code spans 2; lost 0 | 0.1 per 1000 words | {} |
| 03-training-memory-and-compute-anatomy.md | 12762 | 16369 | +28.3% | 0 hard failures; guard words 9056 -> 12663; new numbers 0; lost numbers 0; new code spans 1; lost 0 | 0.0 per 1000 words | {} |

Other gates run: `node tools/check_mermaid.mjs` returned `checked 776 diagrams, 0 failed`. `npm run build` was not run (run instruction said no npm build). Checkpoint count unchanged at 20 in each file. Front matter, headings, code fences, Mermaid, data tables, Sources and checkpoint blocks were not edited.

## Guard "new numbers" explained (chapter 01)

- `15.79` and `42.86`: restated from the locked bubble table in section 4.2 and from the table row in the pipeline-bubble paragraph. Same values, same form as the table. No new fact.

## Needs source (general explanations added in prose)

Chapter 01
- Underflow definition ("rounds to zero and the update disappears").
- NVLink and InfiniBand glossing ("fast link between GPUs in one server", "high-speed network between them").
- Cosine decay shape description (flat at the start, steepest in the middle, flat near the floor).
- Pipeline micro-batch memory cost ("memory for the extra in-flight micro-batches").
- Ensemble caveat that the member models must make different mistakes (general ML).
- Reading a stack trace bottom-up (Python convention).
- Uniform guess perplexity equals vocabulary size (follows from PPL = exp(loss) for uniform q; restated, not new).
- Mixed precision described as a "speed and activation-memory decision" (interpretation).

Chapter 02
- KV cache definition ("memory that stores past attention results").
- Key-value cache explanation of what is stored per token.
- ReLU/GELU as "bends" and SwiGLU gate description.
- RDMA expansion ("remote direct memory access between machines").
- SRAM described as "small memory next to the compute units"; HBM as "large but comparatively slow".
- Warp definition and warp specialization.
- Temperature divides logits before softmax; top-p keeps the smallest set reaching the threshold.
- Hospital analogy for MoE routing (analogy only, no numbers).
- Restaurant kitchen analogy for prefill vs decode (analogy only).
- Tokenizer fertility wording (repeats the chapter term).

Chapter 03
- `set_to_none=True` drops tensors rather than zero-filling (PyTorch behavior, general).
- Setting `PYTORCH_ALLOC_CONF` before the process starts because the allocator reads it at init (general PyTorch behavior).
- Convention 3 "can lose small updates" (follows from BF16 precision, general).
- Adafactor storing row and column statistics (restates the table, general).
- Checkpointing as "keep the doorways, rebuild one room" (analogy only).

## Corrections made (fact-level wording)

- Chapter 01, ensemble example: original said the vote "succeeds whenever at least two of the three classifiers agree". Changed to "is right whenever at least two of the three classifiers are correct", which matches the 0.784 calculation.
- Chapter 01, interview item 4 and mistakes: restated the same numbers, no change in value.
- Chapter 02, model-table note: first draft said Llama 3 "kept" grouped KV heads. Corrected to "the 8B and 70B rows both use grouped KV heads" (the table shows GQA-8 for those rows; Llama 2-7B is MHA).
- Chapter 03, interview item 3: first draft said later steps are "cheaper in memory terms". Corrected to "adds more compute or communication cost".
- Chapter 03, mistakes intro: removed an unsupported "costs a day of cluster time" claim.

## Unresolved

- Chapter 02, interview item 2 (original text kept): says PagedAttention eliminates "20 to 30 percent HBM fragmentation". Section 3.3 of the same chapter gives 20.4 to 38.2 percent as the unpaged token-state share. The two figures describe different things and the interview line is not reconciled. Left as original, needs owner decision.
- Chapter 03, Sources/Checkpoint locked blocks contain original numbers that were not re-checked in this pass (out of scope, locked).
- Honest status: chapter 01 keeps "were not run on live hardware" above the commands. Chapter 02 gained one plain sentence above the lab ("were not run on live hardware, so treat them as untested"). Chapter 03 keeps "marked `untested` on live hardware" in section 5.1 and the lab intro. The `(untested here)` code comments are original and locked.
- Math `$...$` with stray backticks: none found in these three chapters' prose; nothing repaired.
- Exercise and interview answers in chapter 02 items 2-4 are close to the original wording; they gained a closing paragraph but were not fully re-voiced. Owner may want a second pass.
- Chapter 03 exercise numbering uses plain lines, with the original (a)/(b) sub-items flattened into single-question sentences. Counts unchanged (6 exercises, 6 reference bullets).
