# Voice rewrite ledger, Part 13 chapters 01 to 03 (run A)

Scope: `docs/part-13-ai-storage/01-the-ai-data-path-from-storage-to-gpu.md`, `02-local-nvme-and-data-staging.md`, `03-gpudirect-storage-architecture.md`. Not touched: `planning/EXTERNAL_EDITS.md` (rulebook step 6 skipped on instruction), chapters 04 to 09, code, Mermaid, tables, front matter, headings, checkpoint questions and answers, Sources and review notes, reference blocks.

## Measurements

| File | Words before (wc -w) | Words after | Growth |
|---|---|---|---|
| 01 | 11875 | 15258 | +28.5% |
| 02 | 11463 | 14723 | +28.5% |
| 03 | 12327 | 15894 | +28.9% |

## Gates (run, output seen)

- Span check (`git show HEAD:<file>` vs worktree, inline code spans outside fences): `{}` for all three.
- `python3 tools/rewrite_guard.py HEAD WORKTREE <file>`:
  - 01: 0 hard failures, new numbers 0, lost numbers 0, new code spans 1 (distinct span), lost 0, residue 0 to 0 (body-only word count 9195 to 12578).
  - 02: 0 hard failures, new numbers 0, lost numbers 0, new code spans 0, lost 0, residue 0 to 0.
  - 03: 0 hard failures, new numbers 0, lost numbers 0, new code spans 0, lost 0, residue 1 to 0.
- `python3 tools/restore/chain_gate.py <file>`: 0.0 per 1000 words for all three (target 0.2 or lower met).
- `node tools/check_mermaid.mjs`: 776 diagrams checked, 0 failed (repo-wide run).
- Not run: `npm run build` (task said no npm build), `tools/language_audit.py`, code tests (no code changed).
- Self-check: grep for "you will be able", "should be able to", "by the end of this chapter", "will learn", exclamation marks: none in prose. No raw `<` or `{` outside code spans. No duplicate paragraphs (one mistake found during the run was fixed by de-duplicating the inserted blocks; re-checked).

## Structural changes

- Outcome lists rewritten as plain paragraphs under the locked "Prerequisites and outcomes" headings (01 and 03 had "you will be able to" lists; 02 had "By the end of this chapter, you will be able to:" with four items). Every item's facts and code spans kept.
- Section openers: each section now opens with a concrete situation (a job that crawls, a node that was just racked, a Monday-morning page). Where a locked heading sat above, the situation is the first sentence under it.
- Bold list leads removed from prose lists where a section had several bold ideas (01 1.1 and 2.x, 02 sections 3 and 5, 03 section 5). Bold kept on one idea per section where it was already there.
- Exercises: every multi-part exercise split into single-question sentences. Same six exercises per chapter, same numbers, same spans. Reference blocks untouched.
- Lab: Part A and Part B prose expanded. Same commands, same expected-output blocks.
- Interview answers rewritten in plain voice; the question lines are untouched.
- Mistakes lists: same count (five per chapter), each item kept its spans and numbers.
- Added "bridge" paragraphs before several locked headings to explain what the next section does. These sit between sections, not inside tables or code.

## Facts deliberately kept, but flagged

- 02, section 5.1 ("Three rules of thumb"): the example "Suppose you measure 3.5 GB per second on NVMe and 1.5 GB per second on shared storage. A tenfold gap means staging saves 90 percent of the synchronous wait." The example numbers give 2.33x, not tenfold. Original sentence kept (numbers are locked). Needs a human decision: change the example to match the 2x rule, or change the claim.
- 02, section 2.1 and table: `$N$` and `$C$` math in the alignment table header are unchanged. Not a stray-backtick case, so nothing repaired. Math stays as in the original.
- 02, section 3.1: "about 1.75 GB per second for each GPU" from 3.5 GB per second sustained is not a clean division by the GPU count in the same chapter. Kept as the original's claim. Flag for the source owner.
- 03, section 5.2 example ("healthy case"): changed "comfortably inside the five-year warranty" to "outlasts the five-year warranty". The original phrase was wrong for a 6.4-year lifespan against a five-year warranty; the numbers are unchanged.
- 03, "Treat these figures with care": kept the chapter's own caveat about the 3FS arithmetic (two 100 Gb/s NICs per node give about 25 GB/s, so 68 nodes cannot reach 6.6 TB/s from NICs alone). Not resolved here.

## Needs source (general explanations added in new prose)

Chapter 01:
- Definitions of a collective operation, an epoch, and a checkpoint as a saved training snapshot.
- Definitions of NUMA, PCIe as the bus for cards, DMA, POSIX, pinned memory, HBM as memory next to the GPU die, and the interrupt and context-switch wording.
- RPC, the Metadata Server's role (answers file lookups, not contents), read-ahead as kernel prefetch, NVMe as a flash interface on PCIe, and thrashing of the page cache.
- WebDataset (tar archives) and TFRecord (TensorFlow record format) packaging descriptions.
- Lustre as a parallel filesystem spreading files over storage targets, stripe count meaning, and SLA expansion.
- Blast radius and block size definitions in the chapter intro; nanosecond and millisecond size comparisons; "one lane is one serial wire pair".
- Non-blocking and rail-optimized fabric meaning; oversubscribed and leaf-spine meaning; path diversity.
- CSI expansion as the Kubernetes storage plugin standard; syscall as a kernel request.

Chapter 02:
- Tensor Cores as matrix units; KV cache as an inference server's text memory; RDMA expansion.
- Sharded metadata; mdadm chunk and stripe definitions; deck-of-cards analogy (analogy only, no numbers).
- Parity as rebuild information; read-modify-write latency explanation; SATA as the older interface; lock-contended queue; spinlock definition; queue depth meaning; read-ahead meaning.
- io_uring and pread descriptions; "order of magnitude means roughly ten times".
- DALI as a data-loading library; JPEG decoding as CPU-heavy work.
- Pinned host memory as page-locked RAM; event timers.
- DWPD, NAND, WAF, TBW, and SMART definitions; write and clear cycles; TRIM via fstrim.
- Slurm as scheduler; Prolog and Epilog as scripts that run before and after the job; daemon definition; kubelet as the node agent.

Chapter 03:
- Goodput definition; kernel launch definition; L3 cache and memory channel description; VFS as a common filesystem interface; BAR1 as the GPU address window.
- Magnum IO as NVIDIA's data-movement stack (the original attributes it; the explanatory gloss is new).
- Dma-buf and peermem roles; Peer-to-peer packet description.
- Ceph as an open-source distributed storage system; FUSE expansion and daemon description; object storage connectors.
- UPI and xGMI as the Intel and AMD CPU socket links; DCGM as NVIDIA's data center GPU manager; Host-to-Device (H2D) meaning.
- Ring buffer meaning; kvikio as a Python wrapper over cuFile; polling meaning and CPU spin.
- Kernel-module coupling meaning; line rate definition; compression ratio meaning.

No gem book was newly attributed in these rewrites. Where a gem book appears, the original text already named it (for example "AI Systems Performance Engineering" in 03 "Treat these figures with care" and the Sources section).

## Unresolved

1. 02 section 5.1 tenfold example (see above).
2. 02 section 3.1 "1.75 GB per second for each GPU" division (see above).
3. 02 table header `$N$` and `$C$` math kept as-is (no stray backticks, not repaired).
4. 03 3FS throughput arithmetic caveat kept as the chapter's own caveat.
5. Checkpoint answers and Sources sections are locked and unchanged. Any answer that disagrees with the rewritten prose was not edited (none found on a read-through).
6. `planning/EXTERNAL_EDITS.md` not edited, per instruction.
