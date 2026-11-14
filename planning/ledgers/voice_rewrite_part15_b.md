# Voice rewrite ledger: Part 15 chapters 04, 05, 06 (batch b)

Scope: `docs/part-15-inference/04-sglang-and-cross-request-optimisation.md`, `05-tensorrt-and-tensorrt-llm.md`, `06-triton-inference-server.md`. Front matter, headings, code blocks, Mermaid, tables, inline code spans, numbers, checkpoint questions and Sources sections are unchanged. `planning/EXTERNAL_EDITS.md` was not edited (per run instructions). Nothing was committed.

## 1. Word counts (`wc -w`)

| File | Before | After | Growth |
|---|---|---|---|
| 04-sglang-and-cross-request-optimisation.md | 11155 | 14706 | +31.8% |
| 05-tensorrt-and-tensorrt-llm.md | 10362 | 13625 | +31.5% |
| 06-triton-inference-server.md | 10120 | 13096 | +29.4% |

## 2. Gates (run on the final files)

- `python3 tools/rewrite_guard.py HEAD WORKTREE <3 files>`: 3 chapters, 0 hard failures. New numbers 0, lost numbers 0, new code spans 0, lost 0. Residue 0->0 (ch04), 1->1 (ch05, the `untested here` span in the lab venue line), 7->2 (ch06).
- `python3 tools/restore/chain_gate.py <file>`: 0.0 per 1000 words for all three (target 0.2 or lower).
- Span check (inline code spans in prose, HEAD vs worktree): `{}` missing, `{}` added for all three chapters.
- Mermaid: `node tools/check_mermaid.mjs` reported "checked 776 diagrams, 0 failed" (repository-wide script, run once).
- `npm run build`: not run (run instructions said no npm build).

## 3. Structure checks

- Every H2 and H3 section now opens with a situation sentence (under "Outcomes" and "Lab Venue" too).
- No "you will be able to" lines remain. The Outcomes lists are short paragraphs.
- Exercises: flat items labelled `1a`, `1b`, ... with no nested lists. Same number of sub-parts as the original (ch04: 10, ch05: 6 items, ch06: 8 sub-parts).
- Bold: reduced to about one bold idea per section. Key takeaways are plain text.
- Honest status: each chapter keeps its `untested` / `untested here` spans (ch04 sections 5.1 and 7; ch05 lab venue line; ch06 sections 7.1 and 7.3 heading).
- Checkpoint questions and Sources sections are byte-identical to HEAD (trailing newline restored).
- Ch06 order kept as in the original: Checkpoints come before Key takeaways and Exercises.

## 4. Needs source (general explanations added in the prose, no new facts or numbers)

Chapter 04
- Tensor Parallelism and Pipeline Parallelism one-line descriptions in "Why this matters".
- Definitions: KV cache, prefill, decode, token, few-shot template, RAG expansion, RDMA, NVIDIA NIM expansion, Google Kubernetes Engine (GKE) expansion, Server-Sent Events role, AWQ, QKV projection, dense model, collective, Hopper (includes H100 and H200), warm worker.
- Claims: the saving from overlap depends on CPU work being shorter than the GPU work it hides; exponential backoff with jitter definition; the Radix Tree leaf definition; dynamic-range and chunked-prefill descriptions.

Chapter 05
- Definitions: autograd, eager mode, ONNX, dead node, histogram, serialization, asynchronous launch, split-K, timing cache and SKU, online softmax, arithmetic intensity, barrier, CUDA Graph, Post-Training Quantization and Quantization-Aware Training, hidden channel, Kullback-Leibler divergence, dynamic range, W8A8, microblock, drain.
- Claims: a quadratic attention score matrix grows with the square of prompt length (so doubling the prompt quadruples its memory); the calibrator learns only the distribution it is shown.

Chapter 06
- Definitions: Global Interpreter Lock, histogram in telemetry, KServe v2 as an open protocol, atomic rename, loopback socket, DMA, open-loop test, Pareto frontier, trace, padding tokens, directed acyclic graph, kubelet, CUDA stream mutex, counter versus gauge.
- Claims: the separation of frontend, repository manager, and schedulers; a lost end flag holds a sequence slot until the idle timeout; the three-step triage routine.

## 5. Unresolved

- Ch04 section 2.2: the original text says the Radix Tree lifecycle has "nine operational stages" but its list gives five. Kept as written, and the list now says it walks through the five it spells out. Owner to decide whether to fix the source wording or add the missing stages.
- Ch04 and ch05 exercises: quoted arrays such as `[1, 2, 3, 4, 5]` carry more than two numbers per sentence. They are code spans, so they were kept verbatim.
- Ch05 and ch06 keep original abbreviations P50, P99 and the `untested` labels inside code spans. Span check wins.
- Ch06 section 3.2 keeps the original claim that the failure was documented on an 80 GB A100. The explicit chapter reference was dropped from the prose, and the Sources section still lists it.
- Ch06 prose no longer cites "Volume 12" chapters. Checkpoint and Sources sections still do (locked, unchanged).
- Math `$...$` with stray backticks: none found in these three chapters.
- Ch04 and ch05 Sources sections keep their original wording, including the explicit "untested here" note.
