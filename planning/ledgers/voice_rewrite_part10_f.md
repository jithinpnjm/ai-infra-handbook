# Voice rewrite ledger: Part 10 chapters 10.16, 10.17, 10.18 (set f)

Scope: `docs/part-10-gpu-cuda/16-*.md`, `17-*.md`, `18-*.md` only. Nothing committed. `planning/EXTERNAL_EDITS.md` not edited (instruction step 6 overridden). Other part-10 chapters untouched.

Method: each chapter was rebuilt from its HEAD text. Code blocks, Mermaid, tables, front matter, headings, checkpoint `<details>` blocks and the Sources section are copied byte-identical from HEAD. Only prose, bullets, numbered lists and the `:::note` body were written new. Headings and checkpoint summaries are identical to HEAD (checked).

## Gates (run on the files as they stand)

| Chapter | Words before | Words after | Growth | Rewrite guard | Chain gate | Span check | Mermaid |
|---|---|---|---|---|---|---|---|
| 10.16 `16-intra-kernel-pipelining-warp-specialization-and-thread-block-clusters.md` | 10986 | 14214 | +29.4% | ok, 0 hard failures; new numbers 0; lost numbers 0; new code spans 6, lost 0 | 0.0 per 1000 words | `{}` | unchanged, not separately run |
| 10.17 `17-inter-kernel-pipelining-synchronization-and-stream-ordered-allocation.md` | 9622 | 12416 | +29.0% | HARD: code blocks changed +0 -9 (see Unresolved 1); new numbers 2 (`132`, `16,384`, see Unresolved 2); lost 0 | 0.0 per 1000 words | `{}` | unchanged, not separately run |
| 10.18 `18-dynamic-scheduling-cuda-graphs-and-device-initiated-orchestration.md` | 12321 | 15667 | +27.2% | HARD: code blocks changed +0 -11 (see Unresolved 1); new numbers 0; lost 0; new code spans 18, lost 0 | 0.0 per 1000 words | `{}` | unchanged, not separately run |

Checkpoint counts: 20 in each chapter, identical to HEAD. Heading lists identical to HEAD. Mermaid blocks byte-identical to HEAD. Mermaid check and `npm run build` were not run (task said no npm build; the Mermaid blocks are unchanged).

## What changed per chapter

- 10.16: every section rewritten in place. Section openers are situations (a tiled kernel with idle Tensor Cores, a laundry analogy, a decode server with idle GPUs). The Outcomes list became one plain paragraph and keeps `<cuda/pipeline>`, `cudaLaunchKernelEx`, `cluster.sync()`, `cluster.map_shared_rank()`, `grid.sync()`, `cudaLaunchCooperativeKernel` and `warp_specialized_cluster_pipeline`. The note block is rewritten as prose; "the book" wording became the full title. Exercises kept at 11 items, one question per sentence. Lab intro states the steps were not run on a live cluster (the one honest status line). "(untested here)" is kept only inside locked code comments and the 5.1 and 5.2 code-block lead-ins are plain prose. Section 5 opener and section 6 opener are situations.
- 10.17: every section rewritten. The four Why bullets became four paragraphs. Outcomes and Prerequisites became plain paragraphs. The note block is prose. Prose that was wrapped in ```` ```text ```` fences (3.2 opener, 4.1 pattern prose, 5.1 patterns 1 and 2, 6.2 opener) is now prose. Exercises kept at 6 items (the original count); the original exercise fences are now plain numbered text, one question per sentence. The lab intro says the commands were not run on a live cluster. Heading 7.1 keeps its original "(untested here)" text because headings are locked.
- 10.18: every section rewritten. Outcomes became one paragraph. Note block is prose and now says "the source" or names *AI Systems Performance Engineering* and the nvidia-devops CUDA notes, without "Volume 03" in body text. Prose wrapped in fences (the note body, 1.2 opener, 2.1 opener, 3.1 opener, 3.2 opener, 4 opener, 5.3 opener, lab intro) is now prose. The 2.1 calculation block is kept as a fenced text block because it is a calculation, not prose. Exercises kept at 13 items. "Volume 03" remains only inside locked headings, locked checkpoint answers and the locked Sources section.

## Needs source (general explanations added, not from a cited source)

10.16
- Coalesced loads, Shared Memory, SIMT, ring buffer and assembly-line descriptions (Why, 1.1).
- MMA, L2 cache, FP16 and FLOPS expansions (1.2, 2.1).
- Online softmax rescaling as "the bookkeeping that keeps a running softmax correct" (1.2).
- Compiler flag meanings for `-O3`, `-std=c++20`, `-lineinfo` (5.1).
- `sm_90a` and `sm_100a` "a suffix turns on the architecture-specific instructions" (5.1).
- Occupancy meaning (3.1), register file and Tensor Memory descriptions (4.4), TMA and UMMA/CUTLASS expansions (4.4), GPC description (4.1), NVLink and RDMA references (4.2).
- "Bank serialization" and register spill and bank conflict definitions (1.1, 2.1 sidebar, 1.1 bullets).
- Grid-stride loop definition (3.3), persistent-kernel taxi analogy (3.1), decode and prefill definitions (3.2, 2.1 context), Nsight Compute as NVIDIA's kernel profiler (2.1).
- Analogies only, with no numbers: laundry, cooks and oven, cars, relay team, shuffled deck, factory trucks.
- The "Hopper and Blackwell are NVIDIA GPU generations" expansion (Why).
- Lab sentence "needs no GPU and no extra packages" (7). The source says the lab is standard-library Python on any Linux machine; the no-GPU reading follows from that.

10.17
- Copy engine, pinned memory, page table, fragmentation, event-dependency, and cache-miss definitions (1.1, 2.1).
- Stream as a checkout lane; three-lane steady-state walkthrough; pinned-memory explanation for the lanes (1.1, 1.2).
- Supermarket, shared-stove, two-chef-one-oven, shelf-and-warehouse (release threshold), and recipe-card (capture) analogies (no numbers).
- NCCL, NIXL, RDMA, KV-cache, and SHARP expansions (Why, 5.1). "SHARP switch hardware performs the reduction inside the network switch" is a general description of SHARP.
- NVTX definition (3.1).
- Explanation of why per-thread default streams help third-party libraries in multi-threaded apps (3.1).
- Explanation that a blocking host callback approach is wasteful and that spinning on event queries burns CPU (3.2).
- "Programmatic Dependent Launch, supported on Hopper and Blackwell GPUs" (Why, 6.1). The HEAD sentence is ambiguous ("supported on Hopper. Blackwell GPUs, breaks..."); please confirm the support statement.
- Tail-launch fork and join explanation; capture-as-recording explanation (5.2).
- GEMM and MLP-block expansions (6.2).
- Pointer stability explanation (2.2) and the statement that a recorded graph replays against fixed addresses.
- Stage-count tradeoff: each extra stage needs its own Shared Memory buffers (4.1 closing).

10.18
- Speculative decoding and expert routing definitions (3.2). Prefill, decode, padding, and bucketing definitions (2.2).
- Topology definition (2.3). Slot ownership rationale (2.3). Patch-versus-recapture rule of thumb (2.3).
- Rank, work stealing, coalescing, and MPI/DDP expansions (5, 5.1, 5.2).
- Mail-parcel analogy for the quiet-then-flag ordering (5.1); "the flag could arrive before the data" is the reason for the quiet call, general reasoning.
- Clipboard dispatcher analogy for the scheduler kernel (3.1).
- Explanation that the single-thread guard prevents duplicate child grids (4).
- WHILE-loop explanation that one graph launch covers the loop (3.2).
- Explanation that mixing captured and uncaptured streams leaves part of a step outside the graph (5.2).
- Triage order (first decide slowdown, wrong answer, hang, or memory) (7). The mapping to table rows is a reading aid, not a source claim.
- Stall-reason reading tip (1.1). Reading order for the funnel table (5.3).
- "Lab checks the model and the arithmetic, not your GPU" (8).

## Unresolved

1. Rewrite guard HARD failures, explained and not reverted. The guard counts every fenced block as code. Some HEAD fences were prose or exercise text inside ```` ```text ````, which breaks rendering. Those were converted to prose:
   - 10.17: 9 blocks (HEAD lines 263-265, 282-284, 477-479, 480-482, 552-554, and exercise fences 723-725, 727-729, 730-732, 733-735). Also 3.2 and 6.2 openers.
   - 10.18: 11 blocks (HEAD lines 43-46 note body, 112-114, 205-207, 209-211, 339-341, 387-389, 493-495, 529-531, 649-651, 669-671, 758-760).
   Real code, config, calculation and output fences are unchanged. Owner should confirm the conversion or ask for the fences back.
2. 10.17 guard "new numbers 132 and 16,384". These came from HEAD exercise 5, which sat inside a `text` fence, and the guard reads the removed fence as new prose. They are the same facts, not new ones.
3. Locked text that still carries drafting residue (rules keep these unchanged): "untested here" inside code comments of all three chapters; headings 10.17 7.1, 10.18 6.1 and 10.18 section 5 and 8 "Volume 03" wording; "Volume 03" and "Lab 04" inside 10.18 checkpoint answers 8, 18, 19, 20 and the Sources section. A later pass allowed to touch headings or checkpoints should replace them.
4. The HEAD check "Run here" and "Not verified on live hardware" bullets in 10.17 and 10.18 Sources are locked and unchanged.
5. Mermaid check and `npm run build` not run (task instruction: no npm build). Mermaid blocks byte-identical to HEAD.
6. Lab scripts (`code/part10/*_lab.py`) were not run in this pass. Expected output blocks are unchanged from HEAD.
