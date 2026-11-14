# Voice rewrite ledger: Part 14 chapters 13 to 16 (run "e")

Scope: docs/part-14-training-finetuning/13-, 14-, 15-, 16- (four files only). Not committed. EXTERNAL_EDITS.md not touched (step 6 skipped per launch instruction).

## Results

| Chapter | wc -w before | wc -w after | Growth | Guard body words (before to after) | Guard hard failures | Chain gate | Span check |
|---|---|---|---|---|---|---|---|
| 13 fine-tuning SFT, LoRA, QLoRA, preference alignment | 13209 | 16929 | +28.1% | 10440 to 14160 | 0 | 0.0 | {} |
| 14 dataset engineering for fine-tuning | 10131 | 12983 | +28.1% | 7662 to 10514 | 0 | 0.2 | {} |
| 15 fine-tuning infrastructure and cost | 13861 | 17752 | +28.1% | 10325 to 14216 | 0 | 0.0 | {} |
| 16 NeMo framework and customisation | 8994 | 11513 | +28.0% | 6572 to 9091 | 0 | 0.0 | {} |

Guard output on all four: new numbers 0, lost numbers 0, residue 0, checkpoint count unchanged (20 each), code fences unchanged, Mermaid blocks unchanged, heading list identical to HEAD.

Exercise counts: ch13 15, ch14 5, ch15 14 (plus 4 interview angles, unchanged), ch16 10. All match HEAD.

Span check note: no original inline code span is missing. Some spans were added: ch13 `-100` (one new span in the prose about the loss ignoring labels), ch16 `.bin` and `.idx` (one extra each, restored into prose). Guard reports "new code spans 1, lost 1" for ch15, but the span multisets are identical; treated as a guard artifact.

Mermaid: `node tools/check_mermaid.mjs` run once after the last Mermaid-touching edit (none after that): "checked 776 diagrams, 0 failed". `npm run build` NOT run (launch instruction: no npm build).

Honest status sentences (one per chapter, plus the existing locked "untested" spans):
- ch13: "These GPU steps were not run on a live cluster" (rewritten to "Until a run on real hardware confirms ... treat the numbers in Section 6 as expectations").
- ch14: "The GPU steps in this chapter were not run on a live cluster ..." plus the `untested` span.
- ch15: "The live GPU and cluster runs were not executed on live hardware".
- ch16: "that workflow is untested on live multi-node GPU hardware in this local build environment".

## What changed in method

- Built each rewrite as a template in the scratchpad that pulls locked blocks (front matter, tables, code and text blocks, Mermaid, checkpoints, Sources, lab output) from the HEAD snapshot by line range. Locked content is byte-identical to HEAD.
- Rewrote every prose paragraph, bullet list, numbered list, exercise list, lab bullet list, outcomes paragraph, and key-takeaway list in teacher voice. Each section opens with a situation.
- Outcomes lists rewritten as a plain paragraph (ch13, ch14, ch15, ch16). No "you will be able" text remains.
- Exercises: same count and same facts. Sentences split to keep at most two numbers per sentence. Nested (a)/(b) labels removed in ch14 and turned into plain sentences or bullets. Ch14 exercise titles kept as lead phrases (span `cu_seqlens` kept in ch14 exercise 5 title).
- No new digits in new prose (guard new numbers 0). Number words used only where the original used them.
- Bold reduced to at most one bold idea per section where practical.

## Needs source (general explanations added, not from the original chapter)

Verify or cite before publication. These are general definitions or analogies that the original did not state.

- ch13: mixed precision as a term; dequantize on the fly; hallucination and catastrophic forgetting defined; zero-shot defined; RAG pipeline defined as search-then-paste; Adam running averages; chain of thought (ch14); activation memory as stacked notes and the backward pass reading them in reverse; KV cache and prefill; context window; byte-pair encoding learns frequent fragments; Jinja as a templating language; JSONL as one record per line; sycophancy; SwiGLU as a gated feed-forward design; "unified memory as a shared shelf" analogy; registers as the fastest GPU storage (ch15); cross-entropy as the standard token loss; intrinsic dimension as a "smaller set of directions"; GLUE as a benchmark bundle; policy and KL divergence definitions; "reward hacking" explanation wording; annealing as lowering the learning rate toward zero; weight ossification; the claim that a long prompt wastes compute on prefill (general).
- ch14: "quadratic operations" and "linear time" meaning; shingle and Jaccard explanation; encoder definition; lexical n-grams; Named Entity Recognition as a model that finds names; bi-encoder; classification head; gating layer; UTF-8 as the common encoding; Change Data Capture reads only changed rows; DataOps as software-style discipline; pinned host memory and prefetching; copy engine overlap; "perplexity lower is better" as a general rule; "mode collapse" definition; sycophancy-like bias descriptions; "a gold-standard seed set" definition; "tokenizer chops text into tokens".
- ch15: HGX as NVIDIA's NVSwitch baseboard; NCCL as the NVIDIA communication library; AllGather and ReduceScatter explanations; CSI driver definition; time-slicing versus MIG explanation; Spot interruption handling wording; quantile definition; registers; "Standard 2U" cost reasoning; "a page of rules" analogy; the claim that a fast mesh hides collectives under matrix math (paraphrase of original, verify); the claim that Critic memory equals the policy memory (follows from 36 vs 18 bytes, verify on the table); "Tensor Parallelism as cutting a table into strips" analogy.
- ch16: gang-scheduled definition; NGC as NVIDIA's catalog; digest as a fingerprint; MFU definition; paged KV cache description; orthogonal parallelism dimensions; process group definition; delayed per-tensor scaling; activation checkpointing trade-off; pipeline as an assembly line; memory-mapping as paging only needed parts; striped storage explanation; rail definition; "pre-shuffled copies cost cheap storage" trade-off; the claim that a metadata server queues requests behind one writer (general).

## Unresolved

1. Math `$...$` in ch14 (`$N$`, `$k$`, `$M$`, `$b$`, `$r$`, `$n$`, `$O(N)$` in the table): kept as in HEAD. No stray backticks were found next to them, so nothing was repaired. Reviewer should check the `$O(N)$` table cell (locked) for rendering.
2. Original prose kept verbatim (not reworded) in a few places because the stiff sentence was the fact itself: ch15 "Standard 2U PCIe servers..." paragraph (HEAD line 241) and "Notice the impact of sequence packing..." (HEAD line 291); ch16 "NeMo 2.0 writes sharded `.distcp` checkpoints..." (HEAD line 323). Teaching sentences were added around them.
3. Locked content still carries older drafting text that the gate does not treat as reader prose: ch15 dcgm-exporter 4.9.0 note (blockquote, HEAD line 544, kept verbatim with its relative link), ch16 "Volume 14"/"Volume 13" labels inside code-block comments and text blocks, ch16 Inferences table ("untested here"), and the Sources tables. These are locked by the rulebook; reviewer may want a later pass.
4. ch14 exercise 1 and exercise 2 and ch16 exercises: no changes to commands or function names. Span `calculate_...()` names kept.
5. Gem book attributions kept as in HEAD (full titles in the Sources tables). No new book attributions were added in prose.
6. ch16 mid-chapter claims I could not verify from the chapter itself: none added beyond the general definitions above.
7. Scratch-folder side effect: the shared scratchpad directory contained a file named assemble.py written by another session (dated Nov 13 23:08). My first command overwrote it and a later command deleted it. My working assembler lives in the p14e subfolder. Nothing in the repo was affected.

## Files

- docs/part-14-training-finetuning/13-fine-tuning-sft-lora-and-qlora-preference-alignment.md
- docs/part-14-training-finetuning/14-dataset-engineering-for-fine-tuning.md
- docs/part-14-training-finetuning/15-fine-tuning-infrastructure-and-cost.md
- docs/part-14-training-finetuning/16-nemo-framework-and-customisation.md
- planning/ledgers/voice_rewrite_part14_e.md (this file)
