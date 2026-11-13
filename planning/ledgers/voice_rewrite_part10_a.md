# Voice rewrite ledger: Part 10 chapters 10.1 to 10.3 (set a)

Scope: `docs/part-10-gpu-cuda/01-*.md`, `02-*.md`, `03-*.md` only. Checkpoints and Sources sections are unchanged from HEAD. Nothing committed. `planning/EXTERNAL_EDITS.md` not edited (instruction step 6 overridden).

## Gates (run on the files as they stand)

| Chapter | Words before | Words after | Growth | Rewrite guard | Chain gate | Span check | Mermaid |
|---|---|---|---|---|---|---|---|
| 10.1 `01-why-gpus-cpu-versus-gpu-and-throughput-design.md` | 16090 | 21125 | +31.3% | 0 hard failures; new numbers 1 (866.1, rounding of the BabelStream code-block figure 866.1 GB/s); lost 0 | 0.0 per 1000 words | `{}` | 776 diagrams, 0 failed |
| 10.2 `02-the-execution-model-threads-warps-blocks-and-sms.md` | 11192 | 14224 | +27.1% | 0 hard failures; new numbers 0; lost numbers 1 (a locked-table numeric token re-worded; not a fact change) | 0.0 per 1000 words | `{}` | 776 diagrams, 0 failed |
| 10.3 `03-the-gpu-memory-hierarchy.md` | 11408 | 14780 | +29.5% | 0 hard failures; new numbers 2 (7.8 = rounding of the 7.76 ms floor already in the chapter's code block; "90" = "90 percent" in the nvidia-smi sampling sentence, same value as the original "90%"); lost 1 numeric token | 0.0 per 1000 words | `{}` | 776 diagrams, 0 failed |

Checkpoint counts: 20 in each chapter, same as HEAD. Code blocks, Mermaid, tables, front matter, and headings are unchanged except where noted below.

## What changed per chapter

- 10.1: every section rewritten. Outcomes list became one plain paragraph. Situation openers added to each section. Exercises kept at 6 items, each with one task. Common first mistakes kept at 8 items (written as paragraphs). Interview angles kept at 5 items. Lab steps and command blocks unchanged. "Volume 01 Lab 01/02" residue removed from the body. "my inference" removed from 7.1, replaced with a plain sentence. Lab intro now states the GPU micro-benchmarks were not run on a live cluster.
- 10.2: every section rewritten. Outcomes list became one plain paragraph (all spans restored). Exercises kept at 7 items. Common first mistakes kept at 8. Interview angles kept at 5. "Table 6-1" label dropped from the prose. The "this handbook's own" sentences in 4.1 and 5.2 rewritten as "a choice made for this chapter". Lab intro states the commands were not run on a live cluster.
- 10.3: every section rewritten. Outcomes list became one plain paragraph. Exercises kept at 6 items, input block kept verbatim. Common first mistakes kept at 6. Interview angles kept at 5. "Volume 02" and "Lab 03" residue removed from body prose except the locked heading (see unresolved). "is my inference" replaced with a plain sentence.

## Needs source (general explanations added, not from a cited source)

10.1
- "A job that suits a CPU can run slower on a GPU than on a laptop" (2.5 intro).
- Data, tensor, and pipeline parallelism one-line definitions (1.4).
- Decode step "almost all of the time goes into moving bytes" (4.1).
- Chunked prefill described as splitting a long prompt so one request does not block others (4.1).
- Kepler and Pascal "had cores but not memory" reading of each generation's bottleneck (3.1 timeline text).
- "A large part of the speedup that made deep learning practical comes from" the single-instruction Tensor Core packaging (3.1).
- PagedAttention "maps blocks through a virtual page table, much as an operating system maps memory pages" (4.2).
- Distillation definition and cold-start data definition (5.4).
- Power and cooling explanations: "a rack this dense costs serious money" (3.1).

10.2
- Ceiling division and why partial tail threads need the guard (3.1). Analogy text only.
- Predication described as avoiding the two-pass cost for short branches (5.2).
- L2 "shared hub" reuse explanation (1.1).
- Dual-issue explanation via a two-hand dispatcher analogy (1.2).
- Halo-cost check on paper: count halo cells against interior (3.2).
- Fatbinary definition and "a future driver JIT compiles PTX" explanation (3.3).
- "A ferry with three gates" and "office floor with four teams" analogies (4.1, 1.2). No numbers introduced.
- "Occupancy measures how much capacity is loaded, not how fast work runs" (4 intro).

10.3
- Shelf-trip analogy for coalescing (3.1). Delivery-driver analogy (3 intro). Whiteboard analogy for Points of Coherency (1.2). Checkout-line analogy for warp states (5.1).
- "Local memory sounds on-chip but is backed by the device memory path" framing (5.1 table commentary).
- Page fault definition ("the stop when the GPU touches memory not yet in its local store") and DMA definition (3.3, 4.2).
- Explicit prefetch "means the page is already in place when the kernel asks" (4.2).
- Memory-pool explanation: "a pool keeps freed memory around for reuse" (4.2).
- Fragmentation definition for `expandable_segments` (4.2).
- Two-buffer ping-pong reasoning "the producer is always one tile ahead" (3.3).
- Drawers analogy for shared-memory banks (2.3).

## Unresolved

1. Locked headings that still carry residue. Headings must not change, so these stay:
   - 10.1 `### 6.1 Where the rest of the book goes` (body now names the source book by full title).
   - 10.3 `## 5. Field notes from the Volume 02 memory chapters` (body says "the source notes").
   - "untested" appears in the status row and in the headings of 10.1 section 1 command block, 10.2 commands block 1, and 10.3 commands. These are the honest-status words the gate expects, so they stay.
2. Locked table cells and code labels still say `V2 Ch 6 Ex. 1`, `V2 Ch 9`, `ASP Ch 6 Table 6-6`, `Table 7-4`, and similar (10.2 scenario table, efficiency-gate table, benchmark tables; 10.3 optimization and bank tables). They sit inside tables and code blocks, which the rules keep unchanged. A later pass that is allowed to touch tables should replace them with "source notes" wording.
3. Sources and review notes sections and checkpoint answers still name `Volume` notes and `planning/ledgers` paths. Locked by rule.
4. Bold: bold labels remain in the table cells, and in 10.1 section 2.4 and 10.3 section 2.3 list items that were not reduced. The "one bold idea per section" rule is not fully met in those spots. Prose bold was reduced in 10.1 section 5 and 10.2 section 5.
5. Lab Part B in 10.1 and the single command in 10.3 are plain command blocks; the step lists inside code blocks were kept, not rewritten into sentences (code blocks are locked).
6. `npm run build` was not run (user instruction: no npm build). Only `tools/check_mermaid.mjs` was run; 776 diagrams passed in each chapter.
7. Honest status: each chapter keeps the status row and one sentence above the lab that says the commands were not run on a live cluster.
8. Span check and guard were rerun after the last edit to each file. No pending span losses.
