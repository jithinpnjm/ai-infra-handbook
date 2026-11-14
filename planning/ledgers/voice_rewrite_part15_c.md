# Voice rewrite ledger: Part 15 chapters 07, 08, 09

Scope: docs/part-15-inference/07-nvidia-nim-and-the-nim-operator.md, 08-nvidia-dynamo-llm-d-and-disaggregated-serving.md, 09-multinode-inference-parallelism-decoding-and-routing.md. Not committed. EXTERNAL_EDITS.md not edited (per run instructions). No other chapter touched.

## Words (wc -w, HEAD vs worktree)

| Chapter | Before | After | Growth |
|---|---|---|---|
| 15.7 NIM and the NIM Operator | 9481 | 12439 | +31.2% |
| 15.8 Dynamo, llm-d and disaggregated serving | 11327 | 14719 | +29.9% |
| 15.9 Multinode inference | 16306 | 21065 | +29.2% |

Guard body-only word column (prose outside fences): 15.7 6638 -> 9596; 15.8 8467 -> 11859; 15.9 13410 -> 18169.

## Gates (run on the files on disk)

- `python3 tools/rewrite_guard.py HEAD WORKTREE <file>`: 0 hard failures in all three.
  - 15.7: new numbers 0, lost numbers 0, new code spans 0, lost 0.
  - 15.8: new numbers 0, lost numbers 0, new code spans 0, lost 0.
  - 15.9: new numbers 0, lost numbers 0, new code spans 0, lost 0.
- `python3 tools/restore/chain_gate.py <file>`: 15.7 0.0, 15.8 0.1, 15.9 0.0. All under 0.2.
- Span check (`old - new` on inline code spans outside fences): `{}` for all three.
- Heading list identical to HEAD for all three (43, 54, 48 headings).
- Front matter, all code fences, Mermaid blocks, tables, checkpoint blocks (20, 20, 20 as in HEAD) and the Sources and review notes sections are byte-identical to HEAD. Only prose lines were edited.
- `node tools/check_mermaid.mjs`: 776 diagrams, 0 failed (repo-wide run).
- `npm run build`: not run (launcher instruction: no npm build).

## How each chapter was built

- Edits were made section by section with the Edit tool. Code fences, tables and the locked tail were not touched.
- Each section opens with a situation (a job that crawls, a pod that stays Pending, a 2 a.m. style page rephrased without new numbers). Where a locked heading sits above, the situation is the first sentence under it. Exercises and Key takeaways also open with a situation line.
- Outcomes lists (15.7 five items, 15.8 seven items, 15.9 five items) became one plain paragraph describing what the chapter walks through. No "you will be able to" lines remain.
- Bold labels on bullets, list items and exercise titles were removed. The first bold phrase in each prose section was kept (15.7 the NIM packaging sentence, 15.8 the goodput sentence, 15.9 the Tensor Parallelism rule), and later bold phrases were unwrapped by the formatting pass described under Unresolved.
- Exercises kept the same count and the same commands and facts. Each sentence carries one question or one fact, and at most two numbers. Nested (a)/(b) labels in 15.9 were replaced with sequential sentences ("Next, ...", "Last, ...") under the same item. Numbers stayed as in HEAD.
- Original numbers that were written as words ("Forty", "four" etc.) were not added. Where a draft added a number word by mistake, it was removed before the gate ran (15.7 "five"/"nine", 15.8 "section 7" and "section 4", 15.9 "Forty", "four copies", "sixteen", "70B").
- Backtick spans were not added in prose (two were added in 15.9 and removed again before the guard run).
- Honest status kept once per chapter: 15.7 the 7.1 bullet ("have not been run on a live GPU cluster") and the 7.3 heading "(not run on live hardware)"; 15.8 the 8 scope bullet ("have not been run on live multi-node GPU hardware") and the Sources note; 15.9 the 7 lab bullet keeps the original `untested here` span.
- The word "untested" also appears in prose as ordinary English ("an untested mix of versions" in 15.7 and 15.8). These are not status lines.

## Needs source (general explanations and small claims added in the rewrite)

15.7
- CUDA as NVIDIA's GPU platform; cuDNN as a deep learning primitives library; NCCL as the library that moves data between GPUs; NVML as NVIDIA's GPU management library (the original named NVML, the one-line gloss is new).
- NIM entrypoint as the startup script that runs first.
- Tier 2 wording "so the next pod that mounts that cache can reuse it" (logical consequence of persisting the engine, not stated in the source).
- Tier 3 "slower but more flexible profiles" (inferred from the table row descriptions).
- Safetensors as a weight file format; Docker layers as stacked file snapshots.
- PersistentVolume "outlives any single pod"; "the download cost is paid once" (follows from the cache design).
- Kubelet as the per-node agent; DMZ, bastion host, firewall, egress, CVE, Trivy one-line definitions.
- Liveness, readiness and startup probe one-line definitions, and the reading of the probe block (liveness has the least patience).
- Multi-LoRA "a single busy adapter can crowd out the others", and "a dedicated pod still makes sense for its own limits or release schedule" (inference, not from the source).
- Controller as a thermostat analogy; a wrong manifest is re-applied until fixed (general controller behavior).
- Helm, Kubernetes Job, namespace as a labeled folder, deterministic completion, canary as a small group receiving live traffic.
- Opening scenarios (platform team by next week, Friday evening rollout, customer's pods slow to start, bank with a midnight reboot) are illustrations, not facts.

15.8
- Definitions: Tensor Cores as matrix units; Key-Value cache as stored attention keys and values; HBM as the GPU's own fast memory; CUDA stream as an ordered GPU work queue; memory wall; latency budget; percentile target; etcd as a consistent key-value store; lease as a time-limited claim; NATS as a lightweight message bus; RDMA; doorbell; bounce buffer; context switch; pinned memory; transpose kernel; NVLink domain; Nsight Systems as NVIDIA's profiler; UCX as the transport framework NIXL uses; sidecar; control plane; round-robin; exponential moving average.
- "Quadratic" recomputation cost (attention work grows with the square of the length). The source says "quadratic prefill recomputation"; the one-line gloss is new.
- "Often the cheaper fix is a different layout of the same hardware" (judgement, not sourced).
- Tiering as a placement policy by reuse interval; "a slower load is acceptable when the alternative is recomputing" (reasoned).
- Reading of FailClose as "request refused when the picker cannot answer" (interpretation of the source's `failureMode: FailClose`; verify against llm-d/Gateway API Inference Extension docs).
- "A rejected free-tier request gets a quick, clear refusal, which is far kinder..." (judgement).
- "Dynamo is the control layer; the engines underneath do the math" (interpretive framing).
- EAGLE "reuses what the big model already computed, so its guesses start from better information" (interpretation of feature-level drafting; verify).
- Decode-centric entry point described as the design choice (no rationale added beyond the source).
- Pipeline stage and handoff walkthrough for the lifecycle block (order of steps is from the source; the "polling yields while the GPU keeps decoding" reading is interpretive).
- Restaurant/kitchen/circuit-breaker analogies (no numbers).

15.9
- Definitions: Mixture-of-Experts; micro-batch; quantization; NVLink domain; rail; pipeline bubble; Context Parallelism boundary overhead; expert activation density; barrier; microburst; queue pressure; straggler; gating softmax; load-balancing loss; ECC error; headless worker; gang scheduling; DNS discovery; scaling efficiency; n-gram; Jacobi iteration; backtracking in Medusa trees; dtype; bonding of InfiniBand ports (one failed cable does not take the path down); non-blocking fabric; temperature in draft sampling; Roofline knee.
- The flat-versus-hierarchical AllToAll example (one token's two experts on the same remote node means one network trip under the hierarchical route). Illustrative; verify against the hierarchical AllToAll description it paraphrases.
- "Two rail" / same-rail peer reading of the activation shard send (interpretation of the source's wording).
- "Mode A keeps every GPU on the same request ... Mode B lets each GPU own its own requests" (restates the source's flowchart labels).
- Advice without source: replay long prompts and compare warm versus cold TTFT; benchmark before and after NCCL changes; launch both speculative commands on staging with the same prompt set; check queue labels against node pools; alert rules as early warnings.
- "A router that changes its mind too often can make answers less consistent" (judgement).
- Surgical team and cashier analogies for single-node versus multi-node (no numbers).
- LeaderWorkerSet `replicas` and `size` reading (what each field counts, from the manifest comments).
- EAGLE, Medusa and Multi-Token Prediction "validated like any other model change" (advice).

## Changes that need the owner's eye

- 15.8 Key takeaway 2 says the uncached prompt "must exceed 256 tokens". The code in the same chapter (`eff_len >= PREFILL_LENGTH_THRESHOLD`) uses `>= 256`. Original wording kept; facts not changed. Unresolved: the word "exceed" should be "at least" if the owner agrees.
- 15.8 Solution sketch paragraph was left as in HEAD (stiff but unchanged; no numbers touched).
- 15.9 Exercise 4 still says "the Section 6.2 Pipeline Parallel incident", "Section 4.2", "Section 5.1": these are original cross-references and are kept as-is.
- 15.7 and 15.8 keep the Volume 14 / Volume 12 / BCM 11 / Generative AI on Kubernetes attributions that the original made. Nothing new was attributed.

## Unresolved

- Math-like `$...$` with stray backticks: none found in these three chapters' prose. The literal `$oauthtoken` (15.7 prose and table) is a shell variable name, not math, and was left as in HEAD.
- Bold: a formatting pass after the rewrite unwrapped every bold phrase after the first one in each prose section (33 in 15.9, 1 in 15.8, 0 in 15.7). Tables, code, the checkpoint block and the Sources block were skipped. No words changed. Each prose section now carries at most one bold phrase.
- The 15.8 and 15.9 "Inferences and Unverified Claims Note" and the Sources tables are locked and were not revised, including their "untested" and "not run" wording.
