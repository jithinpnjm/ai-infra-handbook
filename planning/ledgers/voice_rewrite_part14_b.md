# Voice rewrite ledger: Part 14 chapters 04, 05, 06

Scope: docs/part-14-training-finetuning/04-data-parallelism-and-ddp.md, 05-fsdp-and-parameter-sharding.md, 06-deepspeed-and-zero.md. Not committed. planning/EXTERNAL_EDITS.md not edited (per run instructions).

## Results

| File | Words before | Words after | Growth | rewrite_guard (hard failures / new numbers / lost numbers / new code spans / lost spans) | chain_gate | Span check |
|---|---|---|---|---|---|---|
| 04-data-parallelism-and-ddp.md | 11785 | 15144 | +28.5% | 0 / 0 / 0 / 0 / 0 | 0.0 | {} |
| 05-fsdp-and-parameter-sharding.md | 12634 | 16327 | +29.2% | 0 / 0 / 0 / 0 / 0 | 0.0 | {} |
| 06-deepspeed-and-zero.md | 12335 | 15925 | +29.1% | 0 / 0 / 0 / 0 / 0 | 0.0 | {} |

Gate notes:
- Code blocks, Mermaid blocks, tables, front matter, headings, checkpoint count, Sources sections and checkpoint Q/A blocks were not edited. The guard reports no structure change.
- Every digit token added to prose was avoided. Where a new example needed a count, words were used or an existing number from the chapter was reused.
- `npm run build` and `node tools/check_mermaid.mjs` were not run. The run instructions said no npm build, and no Mermaid source changed.

## Honest-status wording (one per chapter, plus original)

- 04: the existing `untested` span in Part B is kept. The new text adds no second status sentence.
- 05: the original sentence "The commands below were not run on live multi-GPU hardware." is kept.
- 06: the original "were not run on live multi-GPU hardware" sentence is kept, and the original "not measured in this chapter" note on the SuperOffload figure is kept.

## Needs source (general explanations added, not from the book text)

04:
- Tensor Parallelism splits one layer; Pipeline Parallelism splits the layer stack into stages.
- Ring AllReduce: each GPU sends and receives about the same amount of data.
- Page-locked host memory allows a direct DMA copy.
- Deterministic algorithms run slower.
- GIL definition and the claim that threads queue behind one another.
- Definition of MFU as share of theoretical math throughput.

05:
- Master weights keep full precision so small updates are not lost to 16-bit rounding.
- Psi as a symbol for the parameter count; momentum and variance as AdamW running averages.
- DeviceMesh as a grid mapping GPUs to node and slot.
- Eager mode definition; graph break and recompilation definitions.
- Dimension zero as the first (row) axis.
- The claim that a shared-embedding (weight tying) pair must sit in one FSDP unit is from the original text; the "weight tying means two layers share one tensor" gloss is added.
- The FP32 master-weight preference for the 16-byte convention ("the honest one") is a teaching judgment, not a sourced claim.

06:
- Page-locked memory and AVX vector instruction set (DeepSpeedCPUAdam).
- NVMe as flash on the PCIe bus; RAID0 has no redundancy; queue depth as reads in flight.
- Raw device path skips the filesystem the engine expects (stated as a reason for the nvme_path rule).
- Block-based quantization keeps rounding accurate; the master copy stays exact in ZeRO++.
- Softmax denominators, causal mask load balance, FlashAttention description.
- Mixture-of-Experts routes each token to a few experts.
- 1F1B alternates forward and backward micro-batches.
- NCCL user buffer registration reduces SM use; GPUDirect RDMA definition.
- Colliding process groups can interleave and hang (stated as general reasoning).
- Speculation-Then-Validation rollback description follows the original wording; the "CPU works on a guess" gloss is added.

## Unresolved

1. Math with stray backticks: none found in the three chapters (no `$...$` in prose; `$` appears only in shell code blocks).
2. Section openers: a few sections open with an explanation rather than a concrete situation, because the original section content was dense and the first sentence is a definition or claim. Examples: 04 "1.1 When data parallelism applies" (opens "Distributed training exists because of two separate limits"), 05 "1.2 Hierarchy of FSDP sharding" (opens "Think of sharding as a dial"), 06 "1.2 Side-by-side memory math" (opens with the miscalculation risk). Flagged for the Claude review pass; not fixed in this run.
3. Original facts were not audited. Examples kept as written: 06 "Stage 2 shards seven-eighths of the mixed-precision state" (common-mistakes item 2) and the ZeRO-2 "25 GB headroom" wording. These are the original text, not new claims.
4. Interview answers in 04 and 05 keep the original content with light rewording. The 06 interview answers keep the original wording except for the new intro paragraph.
5. Exercise 2 in 06 now asks for both FP32 and FP16 weight cases in separate sentences; the reference block is unchanged.
6. The 04 Interview answer 3 keeps the original "Strong answer" label, which is a format label and was left as-is.
