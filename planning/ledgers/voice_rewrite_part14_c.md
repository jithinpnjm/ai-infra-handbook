# Voice rewrite ledger: Part 14 chapters 07, 08, 09 (batch c)

Scope: `docs/part-14-training-finetuning/07-*`, `08-*`, `09-*` only. Not committed. `planning/EXTERNAL_EDITS.md` not edited (per task instruction).

## Results

| File | Total wc before -> after | Body wc (guard) before -> after | Body growth | Guard | Chain gate | Span check (inline spans, HEAD vs worktree) | Mermaid |
|---|---|---|---|---|---|---|---|
| 07-tensor-pipeline-and-expert-parallelism-megatron.md | 13365 -> 15924 (+19.2%) | 8125 -> 10684 | +31.5% | ok, hard failures 0, new numbers 0, lost numbers 0 | 0.0 | {} both ways | 776 diagrams checked, 0 failed (repo-wide run) |
| 08-pytorch-performance-profiling-tuning-and-scaling.md | 10919 -> 13389 (+22.6%) | 8377 -> 10847 | +29.5% | ok, hard failures 0, new numbers 0, lost numbers 0 | 0.0 | {} both ways | same |
| 09-pytorch-compilers-and-kernels-torch-compile.md | 10410 -> 12801 (+23.0%) | 8093 -> 10484 | +29.5% | ok, hard failures 0, new numbers 0, lost numbers 0, residue 2 -> 0 | 0.0 | {} both ways | same |

Notes on the numbers:
- The task asked for +28% or more. The guard's body count (prose outside code fences, headings excluded) is the number the rule targets. All three clear +28% on that count. The whole-file `wc -w` growth is lower because the checkpoints, Sources tables, code blocks and tables are locked.
- `node tools/check_mermaid.mjs`: 776 diagrams checked, 0 failed. `npm run build` was not run, as the task said.
- Guard "new code spans / lost" lines (ch07: 2/3, ch08: 3/3) and the earlier "lost 3" counts are an artifact of the guard's span regex: single-character spans such as `v`, `k` and `W` shift the backtick pairing on the same line. The authoritative span check (exact multiset of inline spans outside fences) returns `{}` for all three files.

## Standing checks run (all three)

- Heading lists identical to HEAD (no H1/H2/H3 added or dropped).
- Checkpoint blocks, Sources sections, code fences, Mermaid, tables and front matter untouched.
- No "will be able", "should be able", "you will learn", "By the end" in prose.
- No exclamation marks in prose.
- Honest status present once per chapter in prose:
  - 07: "These lab steps were not run on a live cluster during the handbook build." (above the lab)
  - 08: the original verification-status blockquote kept verbatim (contains "not run on live GPU hardware").
  - 09: "These steps were not run on live GPU hardware during the handbook build." (above the lab)
- Gem books named by full title where the original attributed (AI Systems Performance Engineering). "Chapter 14 of the book" and "Figure 14-5 of the book" were rewritten to the full title. The bare "Chapter 14 demonstrates..." attributions were given the full title.

## What changed (summary)

- Every section opens with a situation (a job, a trace, a pod-level symptom). Where a locked heading sits above, the situation is the first sentence under it.
- "Outcomes" lists rewritten as a plain paragraph. ch07 keeps the `### Outcomes` heading. ch08 keeps the bold `**Outcomes**` label (the original label was a bold line, not a heading). ch09 keeps the `### Outcomes` heading.
- Exercises: one situation each, one question per sentence. Where a data list had more than two numbers (ch08 exercise 8), the list was kept verbatim (see Unresolved).
- Lab step lists: same count and same commands. Only the surrounding prose was rewritten.
- Config labels in ch07 Commands section: the bold markers on "Configuration A-D" were dropped (titles kept verbatim) to meet the one-bold-idea rule.

## Needs source (general explanations added; none adds a number or a claim about the chapter's subject)

ch07
- FSDP2 expansion "PyTorch's fully sharded data parallel system" (in Why this matters).
- AllGather definition ("every GPU collects the pieces the other GPUs hold").
- Half precision explanation (fewer bits per number).
- Rank as "one GPU's seat in the Tensor Parallel group".
- LayerNorm and RMSNorm as normalization steps that keep numbers in a stable range; normalization works per token across the hidden dimension.
- GeLU and SwiGLU described as non-linear functions; element-wise definition.
- Point-to-point message vs collective definitions.
- Process group definition.
- Streaming Multiprocessor described as "the GPU's compute units" (ch07 5.3).
- FP8 as an 8-bit floating-point format; GEMM as a general matrix multiply; dynamic range definition.
- ReduceScatter sums partial results and leaves one slice per GPU.
- Capacity Factor as a ceiling on tokens per expert; overflow tokens dropped or passed through on a residual path (this sentence paraphrases the original).
- "Orthogonal" defined as independently choosable axes.
- Overlap efficiency definition (fraction of communication hidden under math).
- Rule-of-thumb sentence in 1 "at that point, gathering the full layer costs more than splitting the math".
- Explanation of why NVLink versus PCIe matters for the `nvidia-smi topo -m` cells.
- "Pick the matching row" guidance in the failure-table intro.

ch08
- Host-to-device copy definition; pinned memory described as memory the GPU can copy from directly.
- Roofline chart definition (kernel speed against compute and memory limits).
- Arithmetic intensity definition (math per byte moved).
- CUPTI described as "the CUDA profiling interface".
- Instructions per cycle (IPC) definition and the reading that low IPC means waiting on memory or mispredicted branches.
- CUDA stream definition as an ordered queue of GPU work; DMA copy engine described as moving data without using compute cores.
- Warp definition as 32 threads in lockstep.
- SM wave definition (one batch of thread blocks filling the SMs).
- DTensor described as a tensor that knows its sharding.
- `torch.allclose` explained as a tolerance check (the original cites it; the tolerance reading is added).
- KV cache described as keys and values of earlier tokens; 2:4 sparsity as two of four weights zero.
- `sysfs` described as the kernel device file system.
- Caching allocator behavior: fragments too small for the next request force a new allocation.
- Pattern A / Pattern B reading of the two allocator settings ("fixed ladder" vs "stitched virtual range"); "more predictable when sizes cluster" is an inference, not a source claim.
- Zero-copy reduction described as reading data in place; PGAS as "one shared address space".
- "Dual CUDA streams" and "one-sided" wording kept, explained in plain words.
- Warm-up advice "watch the reserved memory counter after several hours" (a practice suggestion, not a measured claim).

ch09
- FX graph described as "a plain data structure that lists each operation and its inputs".
- Guard definition as "a small check that the captured trace still applies".
- PEP 523 described as a CPython hook (original cites PEP 523; "hook" wording added).
- Frame described as "the bookkeeping record for one running function call".
- SymPy described as algebra objects rather than fixed numbers.
- FakeTensor described as shape propagation without allocating GPU memory (the original says the same; the "compiler can compute output shapes" wording is added).
- Triton JIT described as compiling at run time.
- Stage-3 "three arrows leaving Stage 3" (read from the Mermaid, not a source claim).
- StableHLO and HLO described as intermediate formats XLA compilers read.
- Philox described as the pseudo-random generator behind dropout (original); split-K defined as splitting one reduction across work items.
- SIMT vs SPMD explanation in plain words (original names both models).
- Minifier described as shrinking the failing case to a small script you can send to a colleague.
- "cuBLAS underneath torch.matmul": general knowledge, not checked against the source (ch09 4.2).
- "Stock PyTorch layers, and the compiler only fuses what surrounds them" (ch09 1.4 first fact) is a reading of the original claim.
- Proton score "moves in the same direction as the time column" is read from the table values.

## Unresolved

1. ch07 "Why this matters": the original said "fails in four ways" and then listed three limits. The sentence now says "that assumption breaks, and the next paragraph shows how", so the count is gone. The mismatch still exists in the source sense and should be fixed by the owner if the intended count is four.
2. ch07 and ch08 and ch09 Sources sections (locked) contain inline spans with `$` (ch07: `< $6M`, `~$100M`, `~$191M`). They were not repaired, per the rule for stray `$` with backticks. Note only. Prose outside the Sources table has no `$` math.
3. ch08 exercise 8 keeps the original data list (ranks 0 to 6 and rank 7 compute times) as one sentence with more than two numbers, because the list is the input data and must not be changed. This is a deliberate exception to rule 9.
4. ch07 Exercise 7 and ch09 Exercise 9 keep "8 GPUs" and "10,000 elements" with the same numbers. Sentences with two numbers were kept; no sentence was split in a way that changes a fact.
5. ch08 `**Outcomes**` is a bold label, not a `###` heading. The original was a bold line, so the heading list is unchanged.
6. ch09 "Interview angles" answers were left as in the original (not rewritten). ch07 and ch08 interview answers were rewritten in place. Questions are unchanged in all three.
7. Locked "(untested here)" strings in code-block comments (ch09 commands section) and in the ch09 Sources table are kept as original. Prose has one honest status sentence above the lab, as required.
8. Guard "new/lost code spans" lines for ch07 (2/3) and ch08 (3/3) are a regex artifact (see Results). Exact span check is clean.
9. The original ch09 Mermaid edge text and ch07 Mermaid labels were not touched; `check_mermaid` passes.
10. Verification of technical claims in the added explanations was not done online (per the no-browse rule for this repo). The "Needs source" list above is the review list.
