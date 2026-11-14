# Voice rewrite, Part 20 chapters 16 to 18 (batch f)

Scope: `docs/part-20-nebius-sre-interview/16-design-gpu-fleet-health-and-capacity.md`, `17-system-design-drill-sheet-twelve-prompts.md`, `18-how-llm-serving-fails.md`. Nothing committed. `planning/EXTERNAL_EDITS.md` not edited (per run instruction, step 6 skipped). No `npm run build` (per run instruction).

## Method

Each file was rewritten block by block. A scratch script (`p20f_apply.py`, in the session scratch folder) replaced only the prose blocks named in a mapping file. Code fences, tables, Mermaid, headings, front matter, the 10 `<details>` checkpoint blocks, the drill questions, the Sources and review notes tail and the Verification log were left byte-identical to HEAD. Where a block needed a situation before a locked element (interviewer blockquotes, H2 openers, the drill and table openers), the new text was added in front of the original block.

## Word counts (`wc -w`, HEAD vs worktree)

| File | Before | After | Growth |
| --- | --- | --- | --- |
| 16 design GPU fleet health | 8240 | 10995 | +33.4% |
| 17 system design drill sheet | 7494 | 10111 | +34.9% |
| 18 how LLM serving fails | 7848 | 10281 | +31.0% |

## Gates (run on the final files)

- `python3 tools/rewrite_guard.py HEAD WORKTREE <file>`: 0 hard failures on all three.
  - 16: `words 6576 -> 9331, new numbers 0, lost numbers 0, new code spans 0 lost 0, residue 11->10`
  - 17: `words 6216 -> 8833, new numbers 0, lost numbers 0, new code spans 0 lost 0, residue 3->3`
  - 18: `words 6790 -> 9223, new numbers 0, lost numbers 0, new code spans 0 lost 0, residue 16->16`
- `python3 tools/restore/chain_gate.py <file>`: 16 = 0.0, 17 = 0.0, 18 = 0.0 per 1000 words (target 0.2 or lower). Exit 0 on all three.
- Mandatory span check (inline code spans, HEAD vs worktree, fenced blocks excluded): `{}` for all three.
- Structure, HEAD vs worktree: `<details>` blocks 10/10/10, code fences 16/32/20, heading lines 34/31/31, table lines 37/120/18 (all unchanged).
- `node tools/check_mermaid.mjs`: `checked 776 diagrams, 0 failed`.
- Banned-pattern scan on the three files: no `!` in prose, no "will be able to", no "should be able to", no "you will learn". "in this chapter" occurs once in 16 and once in 18, both in original text (not a learning-goal line).
- Honest status word per chapter: 16 "marked not run" in the lab intro and "Not verified" tail; 17 "Not verified:" tail (locked); 18 "was not run" in step 6 and the Not verified tail.

## Rule notes

- Rule 2 (situation first): every section now opens with a situation sentence. Prompt sections in 17 gained a situation line before each interviewer blockquote. H2 sections with no prose in HEAD (17 decision checklist, drill questions, worked scenarios, connections; 18 how-to-answer and drill questions) gained a short opener line in front of the locked element.
- Rule 9 (exercises and lab steps): counts unchanged. 16 lab has 6 steps, 17 lab has 2 prose steps plus the run commands (step 1 and step 3 unchanged), 18 lab has 6 steps. Commands unchanged. Lab sentences split to one question per sentence where the original had two. Step 2 of 17 and steps 4 and 6 of 18 were reworded.
- Drill questions and checkpoint answers: byte-identical to HEAD in all three chapters.
- Interview answers (16 "How to answer out loud" Q1 to Q5, 18 Q1 to Q5): bold question lines kept exactly; answer text rewritten in teacher voice, same order as the original (frame, first check, mitigation, follow-up). Numbers kept. In 16 Q4 the one long sentence with two sets of numbers was split into two sentences.
- Gem books: named by the full title already in the original (AI Systems Performance Engineering, Distributed AI Systems, Hands-On LLM Serving and Optimization, Production Kubernetes, Supercomputers for Linux Sysadmins). No abbreviations added. No new book or chapter attribution was added.
- Honest first-person lines ("I fetched it", "I did not verify", "my reasoning", "I ran it") kept as natural uncertainty.
- Nebius facts: no new Nebius claim was added. The Nebius case-study sentences in 16, 17 and 18 keep their original wording and vendor tags. Nebius-related added sentences are only framing ("a reasonable design is", "Nebius has not published").
- Residue (guard): 16 went 11 to 10, 17 stayed at 3, 18 stayed at 16 (the residue is the original "I did not verify" and "I ran" lines kept on purpose).
- Semicolon chains: chain gate 0.0 on all three.

## Changes that needed a second look

- 18, the lab-adjacent sentence about `--load-format dummy` was first extended with an explanation of what the flag does. That claim was not in the original, so it was removed. Only the original sentence remains.
- 18, the `VLLM_FORCE_AOT_LOAD=1` sentence: a clause I added ("so a stale cache cannot hide") was removed. The original claim is kept as written.
- 17, the rack-stage paragraph: added "so the real total is likely less than the sum". This follows from the original "overlaps with seeding" but is an inference. Listed below.

## Needs source (general explanations added, no Nebius or book facts added)

These are general teaching explanations written for this rewrite. None is a claim about Nebius internals. Check before publication.

- 16: GPU expanded as graphics processing unit in the question framing; ECC as error-correcting memory; PCIe as the bus between GPU and host; NVLink as the GPU-to-GPU link; Xid as NVIDIA's numbered GPU fault code; throttling as self-slowing to protect hardware; the fleet median and the "runner who slows" picture; DCGM as NVIDIA's data center GPU manager and the exporter as the scrape bridge; labels as tags on series; gauge and counter definitions; NCCL as NVIDIA's collective library; tensor parallelism as a split across GPUs; Slurm as the HPC scheduler; cron and ssh roles; the "bottleneck" reading of a central checker (marked as my reading); daemon and API server roles; controller definition; the sign and logbook picture for condition and event; "fuse" picture for repeated Xids; smoke-alarm picture for passive checks; failure domain as a shared rack, power feed or switch; hysteresis-free wording in the drain-limit prose; Little's law as an identity from queueing theory; Poisson model assumptions (random arrivals, steady rate, no memory); "dedicated endpoint" as a private serving setup; availability as the share of time the endpoint can answer; pre-stop hook and SIGTERM roles; endpoint slices as the traffic lists; HTTP 429 as "too many requests"; PodDisruptionBudget as a limit on how many replicas may be down; SLI and burn-rate definitions; RMA expansion as the vendor replacement process (original gave the expansion; the explanation is general); bandwidth test purpose; uncordon as the reverse of cordon; readiness probe role; device plugin as the GPU advertiser; "vLLM is an open-source server for running language models"; in-flight request definition; the cold-floor technician picture; the spare-count reasoning "one spare for a whole fleet is too few for some groups and wasteful for others" (my reasoning).
- 17: TTFT and p99 definitions (p99 now described as the slow tail, no new number); PB as petabytes; parameter definition; checkpoint definition; gang scheduling and fragmentation; preemption definition; continuous batching definition; object store and origin definitions; RTO and RPO expansions (recovery time objective, recovery point objective); hysteresis and manual lock; lease definition; fail-open and fail-closed definitions; partition as a network split; blast radius definition; gray failure definition; at-least-once and idempotent consumption definitions; sticky routing; coincident fault; stuck gauge; "KV cache holds the attention keys and values" wording; prefill definition; system prompt as the instruction block; cache hit rate definition; TFLOPS as trillions of floating-point operations per second; fabric as the fast inter-node network; checksum and immutable version definitions; bounded lead-time picture; the "rack stage overlaps, so the real total is likely less" inference; the "gold" picture of a customer call and the finance colleague picture (illustrative); queue, shed, prioritise definitions; the 3x burst "cold start" wording.
- 18: TTFT spelled out at first use; runbook as the written step list; "the line outside a busy kitchen" queue picture; PromQL as the Prometheus query language; HTTP 503 meaning; bounded queue; spare capacity cushion; swapping versus recomputation; tensor and pipeline parallel size definitions; context length definition and the short-context-model remark; quantisation as fewer bits and the canary definition; head-of-line blocking definition; decoding definition; the p50 and p99 wording; pool definition; co-tenant, activations and fragmentation definitions; CUDA graph definition; OOM expansion; rank and collective definitions; NCCL and IPC expansions; `dmesg` and kernel driver definitions; stack dump and watchdog definitions; network filesystem definition; staggering definition; failure threshold as the kubelet's tolerance (general Kubernetes behaviour, check against the probe docs); jitter and back-off hint definitions; fair-share queueing; series definition; NaN and logits definitions; speculative decoding (small draft model proposes, main model checks); sampling settings; pool as a group of replicas sharing one config; fixed prompt set; hop definition; compatibility matrix and CI definitions; "output loop" as the task that streams tokens; the Friday-deploy and two-replica pictures (illustrative); the 0.5 MB and 10 GB walkthrough wording (arithmetic already in original).

## Gem books

No new book references. Existing full titles kept in place. No abbreviation was introduced.

## Unresolved

- Nothing failed a hard gate. Guard lost numbers 0, new numbers 0, lost code spans 0, chain gate 0.0 on all three.
- `npm run build` not run (instruction: no npm build). `node tools/check_mermaid.mjs` passed.
- `python3 tools/language_audit.py` not run in this batch.
- Math `$...$` with stray backticks: none found in these three files. The `$` signs in 17 are currency (for example `$0.10`), as in HEAD, and were not changed.
- Common-mistakes and connections lists in 16 and 17 kept as in HEAD, except the 18 connections and common-mistakes bullets that were given a short opener. Review may ask for the remaining bullets to be expanded.
- The honest status lines are kept as written in HEAD. No Verification log heading was moved (rule 13 would move test-log language there, but the headings and tails are locked).
- Review by Claude: check the "Needs source" items above, especially the kubelet failure-threshold wording in 18 and the rack-stage inference in 17.
- Nothing committed. Owner go-ahead needed.
