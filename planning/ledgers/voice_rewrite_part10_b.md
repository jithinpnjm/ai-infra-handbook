# Voice rewrite, Part 10 chapters 04-06 (batch b)

Scope: `docs/part-10-gpu-cuda/04-tensor-cores-and-numerical-precision.md`, `05-the-roofline-model-and-performance-modelling.md`, `06-gpu-interconnects-pcie-nvlink-nvswitch-and-nvlink-c2c.md`. Front matter, headings, code blocks, Mermaid, tables, checkpoints (20 each) and Sources tail kept from HEAD. Nothing committed. `planning/EXTERNAL_EDITS.md` not edited (per run instruction).

## Word counts (`wc -w`)

| Chapter | Before | After | Growth |
|---|---|---|---|
| 04 tensor cores and precision | 8790 | 11766 | +33.9% |
| 05 roofline | 8876 | 11376 | +28.2% |
| 06 interconnects | 8882 | 11230 | +26.4% |

## Gates (run on each file)

- `python3 tools/rewrite_guard.py HEAD WORKTREE <file>`: 0 hard failures on all three.
  - 04: new numbers 33,554,432 / 524,288 / 65,536 / 67,108,864. These are the values already in the original worked `[4096, 4096]` text block, repeated in prose as a step-by-step walkthrough. No new facts.
  - 05: new numbers 0 (the one new decimal, 0.125, was rewritten as "one eighth").
  - 06: new numbers 0.9 and 7.2 (TB/s figures already in the original NVSwitch summary block, repeated in prose). No new facts.
  - Lost code spans 0, new code spans 0, residue cleared on all three.
- `python3 tools/restore/chain_gate.py <file>`: 04 = 0.0, 05 = 0.0, 06 = 0.1 (target 0.2 or lower; all pass).
- Span check (HEAD vs worktree, prose only, code fences excluded): `{}` on all three after restoring spans in prose. Earlier drafts had lost `GradScaler`, `torch.amp.autocast`, `tcgen05.mma`, `cuSPARSELt`, `to_sparse_semi_structured()` (04), `ncu`, `ert` (05), `simpleP2P` (06). All restored.
- Mermaid: `node tools/check_mermaid.mjs` = checked 776 diagrams, 0 failed (repo-wide run).
- `npm run build`: not run (the run instruction said no npm build).
- Checkpoint count: `<summary>` tags = 20 in each chapter, unchanged.

## Needs source (general explanations added, not in the original text)

Each item is general background that the original did not state. A reviewer should confirm or cut it.

- 04: "Tensor Core is a machine that multiplies whole grids" framing; amax histogram meaning; TMA as a hardware copy engine; cache line as the 128-byte block moved per transaction; double buffering meaning; MoE expansion (mixture of experts); GEMM expansion (general matrix multiply); the "bit fields as a measuring tape" analogy; the claim that the Transformer Engine picks precision per layer by watching number size (paraphrase of the original 3.1 bullet, not a new fact); "training limited by math, inference by weight arrival" in interview answer 1.
- 05: log-log graph explanation; "coalescing means neighboring threads read neighboring addresses"; "deterministic means the same inputs give the same answer"; stove and delivery-truck analogy (no numbers; replaces the chef and waiter analogy); "for most teams the framework is the first place to look" (opinion, reword or drop if unwanted).
- 06: OEM expansion (original equipment manufacturer); DMA meaning; NUMA meaning; GPUDirect RDMA as "NIC reads GPU memory directly"; CXL as a memory and device protocol over PCIe hardware; NCCL as NVIDIA's collective library and CollNet as its name for the network-side SHARP path; SHARP expansion "Scalable Hierarchical Aggregation and Reduction Protocol" (not in the original, verify against NVIDIA docs before keeping); CRC expansion (cyclic redundancy check); MIG expansion (Multi-Instance GPU); sysfs as the Linux file tree; KV cache meaning; prefetching meaning; barrier and fence meaning; bisection bandwidth meaning; non-blocking meaning; kubelet as the node agent; admission time meaning; the new paragraph in 3.1 on choosing tiers by where data travels (general reasoning, no numbers).

Attribution check: gem book named only by full title (*AI Systems Performance Engineering*, *AI Data Center Network Design and Technologies*, *Parallel and High Performance Computing*) where the original named it. The "The book defines a scale-up system" line became "*AI Data Center Network Design and Technologies* defines ..." to replace the bare "The book".

## Residue handling

- Removed: "Volume 02" in body (04 section 2.1 and 4.2), "(untested here)" on exercise 6 in 05 body text, "is my inference" (05 section 2.2 and 4; 06 section 5), "cited notes" in body (05, 06), "the notes" in body (05 section 2.2 and 4; 06 intro), "first-person" lines.
- Kept (locked): "verified here" inside level-3 headings in 04 and 05 ("Self-checking Python model (... — verified here)"). The rulebook says heading text is locked, so these were not changed. Owner decision: rename the headings or accept.
- Kept (locked): "(untested here)" inside code fence in 04 exercise 6 reference block, and "untested here" in 05 reference block.
- Kept (locked table cells): "V7 Lab 01", "V2 Lab 04" and similar labels in 06 section 5 table and lab output. These are table and code content, not body prose.

## Honest status (one per chapter)

- 04: status row (table, locked) reads "Drafted ... GPU profiler commands **untested** on live Nebius GPU VM"; one plain sentence above the lab says the GPU commands were not run on a live cluster.
- 05: status row (table, locked) reads "... `ncu` or `ert` commands untested on a live Nebius GPU VM"; one plain sentence above the lab says the `ncu` and `ert` commands were not executed on a live Nebius GPU VM.
- 06: no status row exists in this chapter's header table. One plain sentence above the lab says the live Linux and CUDA commands were not run on a GPU server.

## Structural rules applied

- Outcomes lists rewritten as plain paragraphs (04, 05, 06 "Prerequisites and outcomes"). No "you will be able to" remains.
- Every section opens with a situation or a picture. Subsections also open with a situation where the section heading allowed it.
- Exercises: counts unchanged (04 = 6, 05 = 6, 06 = 6). Each exercise has one question per sentence and at most two numbers per sentence. Commands and parameters kept. Lab steps: 04 = one Python command plus one `dcgmi`/`ncu` block (unchanged); 05 = same command set; 06 = same command set.
- Interview answers (04, 05) kept as Q and Answer pairs, with explanatory sentences added.

## Unresolved

1. Two locked level-3 headings still contain "verified here" (04 and 05 lab headings). Needs owner decision.
2. 06 SHARP expansion needs a source check before it stays.
3. Locked Sources sections still use "Volume" and "the author's notes" wording. This is tail content the rulebook keeps unchanged, so it was not touched.
4. 06 status-row absence is the original header design; not added.
5. `npm run build` not run (instruction). Owner should run it before commit.
