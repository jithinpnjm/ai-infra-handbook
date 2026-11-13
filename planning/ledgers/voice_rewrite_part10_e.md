# Voice rewrite ledger: Part 10 chapters 13, 14, 15 (batch e)

Scope: `docs/part-10-gpu-cuda/13-memory-access-patterns-and-profiling.md`, `14-occupancy-warp-efficiency-and-instruction-level-parallelism.md`, `15-kernel-efficiency-and-arithmetic-intensity.md`. Not committed. No other chapter touched. `planning/EXTERNAL_EDITS.md` not edited (per run instructions).

## Word counts (`wc -w`, HEAD to worktree)

| Chapter | Before | After | Growth |
|---|---|---|---|
| 13 memory access patterns | 13348 | 17198 | +28.8% |
| 14 occupancy, warp efficiency, ILP | 13508 | 17414 | +28.9% |
| 15 kernel efficiency and intensity | 10140 | 12888 | +27.1% |

## Gates (run and seen)

- `tools/rewrite_guard.py HEAD WORKTREE <file>`: 0 hard failures on all three. New numbers 0, lost numbers 0 on all three. Ch13 reports "new code spans 3", all additions of existing terms (`torch.index_select`, `torch.compile`, `__syncthreads()`), no spans lost.
- `tools/restore/chain_gate.py <file>`: 0.0 on all three (target 0.2 or lower).
- Span check (backtick spans in prose, fenced blocks excluded): `{}` for all three.
- `node tools/check_mermaid.mjs`: 776 diagrams, 0 failed. `npm run build` not run (instruction: no npm build).
- Checkpoints: 20 per chapter, form and text unchanged (locked tail). Sources section unchanged.
- Exercises: ch13 9, ch14 6, ch15 6 (same counts as the originals). Multi-part exercises split into single-question sentences; spans and commands kept.
- Prose-only scan (before checkpoints): no exclamation marks, no raw `<` or `{`, no "you will be able", no "the book says", no "Volume N", no "I ran", no "earlier draft".

## Structural changes (deliberate)

- Outcomes lists in the "Prerequisites and outcomes" section rewritten as a single plain paragraph labelled "What the chapter covers" (ch13 Outcomes list, ch14 Outcomes list, ch15 Outcomes list).
- The "(untested here)" parenthetical removed from the 5.1 headings of ch13 and ch14 and from the Section 5 bold line of ch13. Heading text otherwise identical.
- Ch14 and ch15 Section 5 prose now says the commands "were not run on a live cluster". Ch15 Section 3.4 says the example "is not compiled or run in this handbook".
- Ch15 Section 4.3 bullet list (five bullets) rewritten as questions with the same five cases.
- "Table 7-3" label in ch13 body text replaced with "The table below". Heading labels (e.g. "Table 7-1" in a heading) kept because headings are locked.

## Honest status

- One honest marker kept per chapter in running text: ch13 Section 7 venue line keeps the span `(untested here)` (the span guard requires it); ch14 and ch15 say the commands were not run on a live cluster.
- Code-block comments that still say "(untested here)" (ch13 bash block, ch14 bash block, ch15 bash block) are kept byte-identical, as the code-block rule requires. The Sources "Not verified on live hardware" entries are in the locked tail.

## Needs source (general explanations added to the body; no new numbers)

Chapter 13:
- SRAM as static RAM cells; DMA (direct memory access) expansion; L2 as the chip-wide cache between SMs and HBM.
- Gather definition (reading values at positions named by an index list); thread block shares its shared memory.
- XOR swizzle as an exclusive-or of row and column index; "coprime" explanation for 33 and 32; compile-time transform costs nothing at run time.
- `torch.utils.cpp_extension` described as the route for compiling your own CUDA code; `clone()` as a device-to-device copy; a PyTorch view changes labels, not bytes.
- Pinned memory lets the GPU read host memory directly; GFLOPS as billions of floating-point operations per second.
- Nsight Systems as the timeline profiler and Nsight Compute as the single-kernel view (role split).
- Hopper as the generation before Blackwell; "a Blackwell thread still gets serviced in 128-byte chunks" was original, kept.

Chapter 14:
- NVML as the management library that `nvidia-smi` uses; compute capability as a feature-set version number (a higher number does not mean more warp slots).
- Kineto, CUPTI, and `perf` roles; replay in Nsight Compute as several passes collecting different counters; PTX and SASS as intermediate and machine-level forms.
- Pointwise definition; ReLU definition in the fusion paragraph; a host wait drains the GPU queue; CUDA Graphs record launches once.
- CPU out-of-order execution analogy; cooperative groups as a CUDA API for groups of threads of different sizes; launch overhead definition.
- Memory-level parallelism definition; structured sparsity definition; Thread-Level Parallelism definition.
- `torch.compile` builds the fused kernel on the first call (in the threshold example).
- Rewrote one original claim for accuracy: the original said "each load waits for its own multiply". The rewrite says "each iteration finishes its load and its multiply before the next one begins". Owner should confirm this matches the intent.

Chapter 15:
- TMEM described as the tensor memory beside the Tensor Cores; microscaling as a small shared scale per small group of values; two-level micro-scaling; Transformer Engine as NVIDIA's precision-management library for transformers.
- Special Function Unit as the block for transcendental functions; multiplexer definition; NVLink-C2C as the chip-to-chip link between Grace CPU and Blackwell GPU.
- Warp specialization definition; epilogue definition; "third stage writes results out" in the three-stage pipeline.
- CUB and Thrust described as NVIDIA's parallel-primitive libraries; persistent kernel definition.
- Mixture-of-Experts routing, all-to-all, and RDMA descriptions; cache thrashing definition; DeepEP "delivery door" framing (analogy only).
- Exponent and mantissa roles; gradient underflow as very small gradients rounding to zero.
- Fast math intrinsics as trading a little accuracy for speed.
- Grace Blackwell description.

## Unresolved

1. Ch14 Section 1.2 contradiction, kept as in the original: the prose says `Stall: Not Selected` means the warp waited for free memory transaction slots, while the table row (same section) says the scheduler picked another eligible warp. Owner should decide which definition is right. I did not change either.
2. Ch13 and ch14 Section 5 bash blocks still contain "(untested here)" inside code comments (byte-identical rule). Remove only if the owner agrees to edit code blocks.
3. Ch13 guard lists "new code spans 3" (added existing terms). Not a failure; listed for transparency.
4. Attribution wording: ch14 "The book lists" and ch15 "The book shows" / "The book recommends" were replaced with the full gem-book title. The ch15 opening "in the book" phrase was reworded.
5. The Sources section in each chapter still says "**my inference**" (ch14, ch15) and "marked `(untested here)`" (ch13, ch14, ch15). These are in the locked tail, left as written.
