# Voice rewrite ledger, Part 10 group G (chapters 10.19 to 10.22)

Scope: four chapters in `docs/part-10-gpu-cuda/`. Not committed. Other chapters untouched. `planning/EXTERNAL_EDITS.md` not edited (per run instructions).

## Words (wc -w, before to after)

| Chapter | Before | After | Growth |
|---|---:|---:|---:|
| 19-triton-language-and-compilers-openai-triton-torch-compile-xla | 8823 | 11967 | +35.6% |
| 20-profiling-tools-nsight-systems-nsight-compute-pytorch-profiler | 9036 | 11690 | +29.4% |
| 21-gpu-health-dcgm-ecc-row-remapping-and-xid | 10400 | 13485 | +29.7% |
| 22-gpu-troubleshooting-scenarios | 10056 | 12730 | +26.6% |

## Gates (run after the last edit of each chapter)

| Chapter | Span check (HEAD vs now) | rewrite_guard (hard failures) | chain_gate |
|---|---|---|---|
| 19 | {} | 0 hard failures; new numbers 0; lost numbers 0 | 0.0 |
| 20 | {} | 0 hard failures; new numbers 1 (cross-reference "Section 2.1" / chapter "10.19" wording, see below); lost 0 | 0.0 |
| 21 | {} | 0 hard failures; new numbers 0; lost 0 | 0.1 |
| 22 | {} | 0 hard failures; new numbers 0; lost 0 | 0.1 |

`node tools/check_mermaid.mjs`: 776 diagrams, 0 failed. `npm run build` not run (task said no npm build).

## What changed in the body (all four)

- Every section opens with a situation (a job, a pod, a rank, a card, a ticket), not a definition.
- Outcomes lists rewritten as a plain paragraph ("What this chapter walks through"). No "you will be able to".
- Exercises: same count per chapter (19: 13, 20: 12, 21: 6, 22: 6). Multi-part asks split into single-question sentences. Chapter 19 was briefly rewritten to 24 items and corrected back to 13.
- "(untested here)" removed from body prose. Code comments inside code blocks still contain it (see unresolved).
- Honest status kept once per chapter: 19 ("not run on live GPU hardware here"), 20 ("the shell commands were not run here"), 21 ("untested in this handbook"), 22 ("not run on live hardware for this chapter").
- Volume N, "the book says", "our companion module", "in our benchmark module" removed from body prose. Attribution to *AI Systems Performance Engineering* (full title) kept where the original attributed. `nvidia-devops` Volume 17 replaced by "the `nvidia-devops` engineering notes on profiling tools" in body text only.
- Code blocks, Mermaid blocks, tables, headings, front matter, checkpoints and Sources sections: unchanged.

## Needs source (general explanations added in the rewrite, not from the chapter's source notes)

Chapter 19
- PEP 523 is the Python Enhancement Proposal that added the frame-evaluation hook; CPython is the standard interpreter.
- Definitions of IR as a "middle language", elementwise operations, common-subexpression elimination, define-by-run, PTX/SASS/LLVM NVPTX roles, cuBLASLt and CUTLASS as NVIDIA libraries, and TF32 as a reduced-precision format.
- AOTAutograd "functional mode" meaning for `torch.autograd.forward_ad`.
- Description of TorchDynamo guards as checks that run before a cached graph is reused.
- "A warp is a group of 32 CUDA threads" (the number 32 already appears in the original as `num_warps × 32`).

Chapter 20
- bfloat16 description (same range as single-precision float). `set_to_none=True` skipping a memory write.
- PagedAttention as the vLLM technique that stores the KV cache in blocks; KV cache definition.
- UCX as an open communication framework; NVSwitch and InfiniBand descriptions; ARM SVE as the register width mechanism; Speculation-Then-Validation as "guess, then check".
- Symmetric-memory all-to-all description.
- Description of torchao quantization, pruning and sparsity; FlexDecoding and prefill definitions.
- Nsight Compute non-root counter access: "counters may show as missing or refuse to load" when the module option is not set (plausible, not checked against NVIDIA documentation).
- Definitions of PMU, DWARF, NVTX, FLOP, IPC, occupancy and the Roofline model.
- "The nsys recipe produces a similar summary" (not checked).

Chapter 21
- NVML as the management library; DCGM host engine as the polling process; infoROM as non-volatile board memory.
- ECC check bits description; Pearson correlation definition; microcontroller definition; node-problem-detector definition.
- Known-Good Validation definition; SLI and SLO definitions; the four-level escalation ladder explanation.
- The sentence "a reset while a process is still active can leave the next job with a half-cleared device" is an explanation added in the drain section. It is not from the source. Needs an NVIDIA source or removal.

Chapter 22
- MIG, HBM, PSU rail, barrier, heisenbug, CUDA context, pre-flight gate, persistence mode and DVFS explanations.
- "A patch wave that stops at the first reboot" and "golden image update that removed a hook file" are illustrative stories used to explain the three lifecycle incidents. They are not claims about a real incident.

## Unresolved

1. Code residue: `(untested here)` remains in code comments inside code blocks in chapters 19 (2 blocks, plus the lab output header block untouched), 20 (bash and Python comments), 21 (bash block), and 22 (bash block). Code was kept byte-identical as required for 10.19 and 10.20. Owner decision needed on whether to strip the words from comments in a separate change.
2. Locked sections that contradict the new honest status:
   - 19 Sources and review notes say "Run here: `python3 -B code/part10/triton_and_compilers_lab.py` (25 passed, 0 failed)". The lab output is shown but the status line says "not run" on the GPU commands. Locked by rule 5, not changed.
   - 20 Sources says "Run here: ... (25 passed, 0 failed ...)". Same situation.
   - 21 and 22 Sources sections contain "Volume 17" or "Volume 20" and "V16/V20" references. Locked.
3. Checkpoint answers for all four chapters are unchanged, including phrases such as "Table 13-2's" and "Volume 17 Chapter 2" inside the question text. Locked by rule 5.
4. Xid codes (chapter 21 section 3.1 table, chapter 22 references): Xid 62 is kept as "Internal Micro-Controller Halt (PMU Halt)" and Xid 79 as "GPU Has Fallen Off the Bus", exactly as the original catalog text had them. I did not check these against NVIDIA's Xid catalog for a driver version. Owner or source check needed; no new fact was introduced.
5. Chapter 20 new-number flag (1): a section and chapter cross-reference ("Chapter 10.19", "Section 2.1") added in prose and exercises. These are references, not facts, but the guard counts them.
6. Chapter 19 `32` appears in a new sentence restating the warp size from the original `num_warps × 32` span. Same fact, not a new one.
7. Growth at the floor: chapter 22 is at +26.6%, above the +25% minimum. Chapters 20 and 21 are about +29% to +30%.
