# Voice rewrite ledger: Part 20, chapters 22 to 24 (run h)

Scope: `docs/part-20-nebius-sre-interview/22-operating-vllm-triton-ray-and-tensorrt-llm.md`, `23-kubernetes-failure-drills-for-gpu-platforms.md`, `24-terraform-for-resilient-gpu-clusters.md`. Not committed. `planning/EXTERNAL_EDITS.md` not edited (per run instruction, step 6 skipped). No `npm run build` (per run instruction). Only the three chapters and this ledger were touched.

## Method

Each file was rewritten from its `HEAD` version. A scratch script (`p20h_blocks.py`, in the session scratch folder) split each chapter into blocks and replaced only the prose blocks named in a mapping file. Front matter, headings, fenced code (including Mermaid and the Python, YAML and HCL listings), tables, `<details>` checkpoint blocks, and everything from `## Sources and review notes` to the end were kept byte-identical to HEAD. Where a section needed a situation before a locked element (a table, a heading with no prose, the lab, the drill list), a new paragraph was inserted in front of it. Teaching sentences that follow a table or a code block were inserted after it.

The bold closing sentences and the bold drill labels ("Interviewer opens", "Root cause", "Fix", "Prevention line") were kept, with their original wording.

## Word counts (`wc -w` style, HEAD vs worktree)

| File | Before | After | Growth |
| --- | --- | --- | --- |
| 22 operating vLLM, Triton, Ray and TensorRT-LLM | 8466 | 10970 | +29.6% |
| 23 Kubernetes failure drills | 6944 | 9175 | +32.1% |
| 24 Terraform for resilient GPU clusters | 7835 | 10159 | +29.7% |

## Gates (run on the final files)

- `python3 tools/rewrite_guard.py HEAD WORKTREE <file>`: 0 hard failures on all three.
  - 22: `words 6457 -> 8961, new numbers 0, lost numbers 0, new code spans 0 lost 0, residue 26->29`
  - 23: `words 6691 -> 8922, new numbers 0, lost numbers 0, new code spans 0 lost 0, residue 2->2`
  - 24: `words 7240 -> 9564, new numbers 0, lost numbers 0, new code spans 0 lost 0, residue 0->0`
- `python3 tools/restore/chain_gate.py <file>`: 22 = 0.0, 23 = 0.0, 24 = 0.1 per 1000 words (target 0.2 or lower). Exit 0 on all three.
- Mandatory inline-span check (HEAD vs worktree, fenced blocks excluded): `{}` for all three.
- `node tools/check_mermaid.mjs`: `checked 776 diagrams, 0 failed`.
- Structure, HEAD vs worktree: headings and table lines identical on all three (checked by diff). Fenced blocks identical. `<details>` checkpoint blocks 10/10/10 unchanged. The "Sources and review notes" tail (through the Verification log) is byte-identical on all three.
- Drill questions in 23 and 24: the checkpoint `<details>` blocks are byte-identical. The only change in that section is a one-sentence lead-in inserted before the first question.
- Banned-pattern scan on the three files: no new `!`, no "will be able to", no "should be able to", no "you will learn", no new raw `{`, no new `$...$` math. The raw `<` count is unchanged from HEAD (it is inside existing tags and Mermaid).
- Honest status words kept once in each lab: 22 "Step 5 ... was not run"; 23 "Step 6 is not run"; 24 "Not run: a real apply on Nebius ..." and "Nothing below was run against a real Nebius account".

## Rule notes

- Rule 2 (situation first): each section now opens with a situation sentence. Where a locked element (table, heading, code) sat first, the situation was added as a new paragraph in front of it. Interview answers and drill "Interviewer opens" lines kept their bold labels and quotes.
- Rule 3 (no outcomes lists): none added. No "you will be able to" phrasing.
- Rule 9 (exercises and lab steps): step counts unchanged. 22 lab has 5 steps (1 to 5), 23 lab has 6 steps (1 to 6) and the Linux-container paragraph, 24 lab has 7 steps (1 to 6 in one block, 7 in its own block). Commands, expected results and observed results are unchanged. Step sentences were split to one question or one instruction per sentence. No nested (a)(b) was added.
- Rule 13 (Part 20 first person): first-person lines that record what was verified were kept in natural voice (for example "I checked the Docker Hub tag", "I confirmed from `kubectl --help`", "This was not tested"). The phrase "Honest note:" was added once in 22 section 11 before the "not on the page" sentence.
- Nebius facts: none added. Nebius-related sentences were only reworded or framed ("Nebius has not published ..."). The Nebius Senior SRE posting, the Amsterdam anecdote, the solutions-library layout, the provider quota and strategy statements and the Object Storage backend notes keep their original wording and vendor tags.
- Gem books: named by the full title already in the original (Hands-On LLM Serving and Optimization, Generative AI on Kubernetes, LLMs in Production, Kubernetes for Generative AI Solutions, Production Kubernetes, Kubernetes: Up and Running, Terraform Up and Running, AI Systems Performance Engineering was not newly cited). No abbreviation was introduced.
- Interview answers (22 "How to answer out loud" Q1 to Q5; 23 and 24 answers): bold question lines kept exactly, answer text reworded in teacher voice, same order, same numbers.
- Residue (guard): 22 went 26 to 29. The added hits are first-person honest lines ("I did not find the item", "in the docs I read") that rule 13 keeps on purpose. 23 and 24 unchanged or better.
- Semicolon chains: chain gate 0.0 to 0.1 on all three.
- Math `$...$` with stray backticks: none found in these three chapters, so nothing to note.

## Needs source (general explanations added, no Nebius, book or vendor facts added)

These are general teaching explanations written for this rewrite. None is a claim about Nebius internals. Check before publication.

- 22: KV cache as the memory holding attention keys and values per token; kernels as small GPU programs; tensor shape as the list of dimensions; OpenAI-compatible server as one that accepts the OpenAI request shape; FP8 and FP4 as lower-precision number formats; prefill as reading the whole prompt and decode as writing one token at a time; disaggregated serving as running those two steps on different workers; checkpoint as the saved set of trained weights; prefix reuse and prefix-aware routing; instance groups as the setting for how many copies run and on which devices; activations as temporary tensors; `max_model_len` as prompt plus output; the scheduler step; preemption as removing a running request and recomputing it later; profiling as a test pass that measures memory; paged KV caching and continuous batching plain descriptions; quantisation as fewer bits per number; cache salt; hash collision; speculative decoding as draft-and-verify; QPS as queries per second; CUDA graph as a recorded list of GPU work; I/O meaning reading from storage and writing to the GPU; one-token request as a deeper health check; Prometheus as a common metrics format; thundering herd; SLO expansion as service level objective; surge pod stays Pending without a spare GPU (the chapter already labels this as inference); GPUDirect RDMA as a NIC moving data straight to GPU memory; blast radius as how much one failure takes down; engine kwargs; goodput as useful throughput that meets the latency target; the cumulative-counter remark; the claim that a cache hit saves prefill work and that the cache salt separates tenants (describes the design page's stated purpose); the note that a slow answer can make a short-timeout probe fail (follows from the original).
- 23: Lease as the small object each node renews; taint and toleration definitions; ImagePullBackOff as the kubelet backing off between pulls; cold start; the "previous container holds the last words" picture; the eviction timer; N plus 1 meaning; the claim that a network split does not start a storm (follows from the original rate-limit text); the admission webhook definition; control plane versus data plane; exit code 137 and SIGKILL, cgroup definition, and "SIGKILL cannot be caught"; the odd-count majority for etcd leader election; the note that deleting a node object early loses evidence; "the CPU is not the limit on this workload" for the GPU HPA case (reasoning from the original 40 percent CPU figure).
- 24: Terraform state as Terraform's notebook of what it built; the bulkhead picture (original), the "sealed envelope" picture for the saved plan; address as a promise of identity; write-only meaning; "best effort" as a vendor not promising behaviour; Open Policy Agent as a general policy engine; allow list as a written record of accepted risk; the claim that a fresh plan at apply time can differ from the reviewed one (general, follows from the saved-plan docs); the claim that versioning is worth its storage cost (the Nebius page says versioning adds cost; the trade-off judgement is ours); the bootstrap and migrate-state framing (original text); "one destroy with zero adds is dangerous" framing; "the guard is the check that normally blocks a destroy at plan time" (follows from the prevent_destroy text).

## Unresolved

- None of the three gates failed. No item was left unresolved in the text.
- Residue in 22 went from 26 to 29 hits, all first-person honest lines kept on purpose (rule 13). A reviewer may want to confirm that the new "in the docs I read" and "I did not find" sentences read naturally.
- The scenario steps in 22 (Scenario A, B, C) and 24 (Scenario B, C) keep their "Step one", "Step 1" labels and numbers. They are scenario steps, not lab steps, so rule 9 was applied in spirit only (one question per sentence where the original had one).
- The "Common mistakes" bullets in 24 and the table in 23 keep their original structure. Bullets in 24 hold the question and the answer in the same line, as before.
- `npm run build` was not run (per run instruction). The Mermaid check passed.
