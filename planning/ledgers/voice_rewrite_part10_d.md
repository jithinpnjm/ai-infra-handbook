# Voice rewrite, Part 10 chapters 10-12 (batch d)

Scope: `docs/part-10-gpu-cuda/10-fabric-manager-nvsm-and-nvlink-domains.md`, `11-cuda-programming-basics-kernels-indexing-and-memory.md`, `12-streams-events-asynchronous-copies-and-pinned-memory.md`. Front matter, headings, code blocks, Mermaid, tables, checkpoints (20 each) and the Sources tail were left as they were. Nothing committed. `planning/EXTERNAL_EDITS.md` was not edited (per run instruction).

## Word counts (`wc -w`)

| Chapter | Before | After | Growth |
|---|---|---|---|
| 10 fabric manager, NVSM, NVLink domains | 9407 | 12258 | +30.3% |
| 11 CUDA basics | 10597 | 13390 | +26.4% |
| 12 streams, events, pinned memory | 8086 | 10312 | +27.5% |

## Gates (run on each file)

- `python3 tools/rewrite_guard.py HEAD WORKTREE <file>`: 0 hard failures on all three.
  - 10: new numbers 0, lost numbers 0, new code spans 2 (informational). An earlier draft had `dgx-[001-002]` in a span, which the guard flagged as new numbers; that sentence was reworded and the guard then reported 0.
  - 11: new numbers 0, lost numbers 0, new code spans 24 (identifiers such as `threadIdx.x`, `cudaStream_t`, `threadsPerBlock`, all named in prose on purpose).
  - 12: new numbers 0, lost numbers 0, new code spans 6 (informational).
- `python3 tools/restore/chain_gate.py <file>`: 10 = 0.1, 11 = 0.1, 12 = 0.1 (target 0.2 or lower; all pass).
- Span check (HEAD vs worktree, prose only, code fences excluded): `{}` on all three. In 12, two `nvidia-devops` spans were dropped by the first pass and restored in prose.
- Checkpoints: 20 `<summary>` tags in each chapter, unchanged.
- Mermaid: `node tools/check_mermaid.mjs` = checked 776 diagrams, 0 failed (repo-wide run, after all three chapters were finished).
- `npm run build`: not run (the run instruction said no npm build).

## Rule checks

- No "you will be able to" remains in any of the three files. The Outcomes lists in 10, 11 and 12 were rewritten as one plain paragraph each (the 11 and 12 lists were rewritten in a second pass, after the first gate run had shown them still in place).
- Exercise counts unchanged: 10 = 11, 11 = 6, 12 = 6. Each exercise is now a short series of single-question sentences. Commands, figures and parameters kept. Where an exercise pointed to a table by a label that does not exist in the chapter (for example "Table 4.1", "Table 3.4"), the reference now names the section instead ("the policy table in Section 4.1").
- Every section opens with a situation (a real ticket, a pull request, a crew on a shelf, a training job that crawls). Section headings and their order are unchanged.
- No exclamation marks in prose. No raw `<` or `{` added outside code.
- Volume and book residue removed from the body of all three. Remaining "Volume" strings are only inside locked code comments, checkpoint answers and the Sources tail.
- Honest status: each chapter keeps a plain "not run on live hardware" sentence above its lab or command section. Locked headings and code comments keep their "(untested here)" text (for example the 12 section 4.2 heading).
- Gem book named only by full title where the original attributed it (*AI Systems Performance Engineering*, *AI Data Center Network Design and Technologies*). No new attributions added.
- 10.10: the sentence "Treat 15 seconds as an illustrative figure ..." and the loose "15 seconds ... 144 NVLink sub-links" claim are kept exactly as they were, per the run instruction.
- 10.11 and 12: every code block is byte-identical to HEAD (guard code-block check passed). The C++ and shell code is walked through line by line in plain words with analogies (crew dispatch, stream as a checkout lane, stopwatch markers, bakery trays, smoke alarm macro, parcel and loading dock for DMA). The analogies introduce no new numbers.

## Needs source (general explanations added, not in the original text)

Each item is background the original did not state. A reviewer should confirm or cut it.

- 10: NCCL expansion (NVIDIA Collective Communications Library); kubelet as the node agent; ABI expansion; systemd meaning of Wants/After and the claim that only After= sets order; BMC, Redfish, IPMI definitions; BCM as cluster software on the head node; "transient service" meaning; multicast meaning; latency vs bandwidth and scale-up vs scale-out definitions; FRU and RMA definitions; NUMA meaning; the Guaranteed QoS class receiving exclusive CPU cores; integer vs fractional CPU requests; non-blocking and fat-tree definitions; "rail-optimized means each rail to its own leaf switch"; SmartNIC and OEM expansions; PCIe, TCP/IP and MTU definitions; RDMA definition; DMA meaning; BAR1 as the bus window to GPU memory; drop-in file meaning; 3D parallelism, collective, micro-step and rank definitions; the "two post offices" and "neighborhood" analogies (no numbers).
- 11: "Unified Memory first touch: fault, driver migrates page, read continues" mechanics; "cudaEventRecord marker timing measures device time" statement; reading of `do { } while (0)` macro; backslash line joining as a preprocessor step; explanation that ceiling division is an integer rounding trick; warp "bus" analogy; grid-stride loop as a crew taking boxes; the "2D version sizes the grid to the picture" framing; the claim that a pointer valid in host code can be invalid in a kernel (the kernel runs on the other processor).
- 12: stream as checkout lane (FIFO analogy); "copy engines are loading docks, SMs are ovens" analogy; the non-blocking cudaStreamCreateWithFlags behavior; `cudaStreamWaitEvent` flags argument zero meaning default; cudaEventSynchronize wait pattern in the first loop branch and the else branch behaving the same; PyTorch reads `PYTORCH_ALLOC_CONF` at startup; a missing environment variable changes which allocator a run uses; pageable memory "parcel" and DMA "fixed address" analogy; stream-ordered pool as a tool crib; the state machine as a list of allowed moves; relay-race and sign-on-a-door analogies for the wait and deadlock; "registration is useful when the buffer already exists" (paraphrase of the original mechanism, verify).

## Residue handling

- Removed from body: "Volume 03" and "Volume 07" references in prose (12: notes, table intro, section 3.2, lab, 4 intro; 10 and 11 had none in prose), "(untested here)" in prose (12 section 6 venue sentence), "our reference notes" and "reference sources" wording (10 and 11, 12).
- Kept (locked): Sources tail wording ("Volume", "the author's notes"), checkpoint answers, code comments with "(untested here)", the 12 section 4.2 heading "(untested here)".

## Unresolved

1. Locked headings and code comments still carry "(untested here)" and "V3 Ch / ASP Ch" labels. These are heading or code text the rulebook keeps unchanged.
2. The Sources tail still uses "Volume 03", "Volume 07" and "Corrections to the author's notes" wording. Not touched (tail is locked).
3. 11 has two honest sentences (the callout note and the section 5 intro sentence). Both are accurate. Owner may trim the callout if one is enough.
4. 10: the "15 seconds" claim left as instructed. Owner should decide whether to tighten it.
5. `npm run build` not run (instruction). Owner should run it before commit.
