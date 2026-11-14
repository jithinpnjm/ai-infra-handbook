# Voice rewrite ledger: Part 20, chapters 37 and 38 (run m)

Scope: `docs/part-20-nebius-sre-interview/37-observability-status-and-operations-on-nebius.md` and `38-token-factory-inference-engineering-everything-nebius-has-published.md`. Nothing committed. `planning/EXTERNAL_EDITS.md` not edited (step 6 ignored per run instruction). `npm run build` and `node tools/check_mermaid.mjs` not run (per run instruction). Only the two chapters and this ledger were touched.

## Word counts (`wc -w`, HEAD vs worktree)

| File | Before | After | Growth (`wc -w`) | Guard prose words |
| --- | --- | --- | --- | --- |
| 37 Observability, status and operations | 4787 | 6569 | +37.2% | 4563 to 6345 (+39.1%) |
| 38 Token Factory inference engineering | 6479 | 8420 | +29.9% | 6228 to 8169 (+31.2%) |

Both are inside the +28% to +40% band on total file words.

## Gates (run on the final files)

- Mandatory inline-span check (HEAD vs worktree, fenced blocks excluded): `{}` for both.
- `python3 tools/rewrite_guard.py HEAD WORKTREE <file>`:
  - 37: 0 hard failures, new numbers 0, lost numbers 0, new code spans 0, lost 0, residue 6 to 6.
  - 38: 0 hard failures, new numbers 0, lost numbers 0, new code spans 0, lost 0, residue 2 to 2.
- `python3 tools/restore/chain_gate.py <file>`: 37 = 0.0, 38 = 0.0 per 1000 words (target 0.2 or lower, limit 1.5).
- Structure, HEAD vs worktree, checked by script: front matter identical; H1 to H4 headings identical and in order; all tables identical (37: 4 tables; 38: 5 tables, the tag table, the routing results table, the master table, the component table and the verification table); all fenced blocks identical (37: 1 Mermaid, 1 yaml, 1 python, 2 bash; 38: 1 Mermaid, 1 python); all 10 checkpoint `<details>` blocks in each chapter identical; the Sources and review notes tail, including the Verification log, identical in both.
- Banned-pattern scan: no `!`, no "will be able to", no "should be able to", no "you will learn", no raw `{` outside code.
- `$...$` math: none in either chapter, so nothing to repair.
- Raw `<` outside code: only the checkpoint `<details>` and `<summary>` markup, unchanged from HEAD.

## What was kept (rule 5)

- Front matter, H1 and every heading, in order.
- Every inline code span, every fenced block, every table, every Mermaid block, every checkpoint question and answer.
- Every number from the original prose. The guard reports 0 new and 0 lost numbers on both files.
- Evidence tags as written: `[official]`, `[vendor]`, `[inference]`, `[source-code]`, `[third-party]`.
- Lab step counts and commands: 37 has 4 steps (steps 1 to 3 run, step 4 "Not run."); 38 has 5 steps (all commands and "Expected" facts unchanged).
- Honest status: 37 "I ran steps 1 to 3 on this Mac. I did not run step 4..."; 38 "All steps below were run on 2026-11-11 ..." and "Not run in CI" on step 5.
- First-person lines kept as the original recorded them ("I fetched them on 2026-11-11", "I could not do this, because I have no key", "I found no Token Factory SLA page", "My run, impact at least major", "It is my arithmetic on their numbers", "Job postings I read ...").
- Book attributions: none added. Chapter 37 and 38 name no gem book in the original; none was added.

## Section openers

Every section now opens with a situation: a pager at 02:10, a customer's question about what they can see, a Thursday SLO review, a 429 that the team cannot explain, a status page that says "All Systems Operational", a 02:10 incident with 8 percent errors, an agent sending fifty requests, a colleague's claim about prefill and decode, a product owner's 99% slide, a model ID that stopped working overnight, a storm hitting a data centre, a benchmark record shown in a slide. Where a locked heading had no prose under it ("## How to answer out loud", "## Worked scenarios"), the situation is the first sentence of the first subsection.

## Needs source

General explanations added in the prose. Each is a textbook definition, not a Nebius fact. Check against a primary source before any external use.

- 37: a histogram as bucketed counts that can answer any limit (removed in the final pass, but "three percentiles give you three points" relies on the same idea).
- 37: KV-cache meaning (attention keys and values kept for reuse).
- 37: federation as one Prometheus server pulling series from another.
- 37: failure domain as the set of things that break together.
- 37: building management system and chilled-water loop as the facility software and cooling loop.
- 37: a cold start in dependency order (bring up the parts others need first).
- 37: DCGM as NVIDIA's data center GPU manager, the field IDs the exporter reports, the throttle bitmask as one number whose bits give the reasons for slowdown, and XID errors as NVIDIA driver error codes.
- 37: a health check that sends a real request, versus process liveness.
- 38: ClusterIP as the default Kubernetes spreading of traffic across pods, without cache awareness.
- 38: prefill as building attention keys and values for the prompt, and the KV cache as where they are kept.
- 38: backpressure as a signal to slow the front when the back cannot keep up.
- 38: prefill as a compute-heavy burst and decode as a series of small token steps that want steady batches.
- 38: speculative decoding as a smaller drafter proposing tokens that the main model checks in one pass; accepted tokens nearly free, rejected ones discarded.
- 38: MoE as a mixture-of-experts model where only part of the network runs per token.
- 38: quantisation as storing numbers with fewer bits, which can change answers at the edges.
- 38: flavor as a variant of the same model with its own settings.
- 38: cache offload as moving old blocks to host memory or disk instead of discarding them.
- 38: HBM as high-bandwidth GPU memory, fast and small.
- 38: RDMA as reading another machine's memory over the network without the usual copying.
- 38: a LoRA adapter as a small set of extra weights, and merging as folding them into a full base copy.
- 38: admission as the gate that decides whether a request gets in, and a tier as its priority class.
- 38: MLPerf as a benchmark suite with fixed models and rules, and a harness as the software that drives a test.
- 38: acceptance rate as the share of drafted tokens the main model keeps.
- 38: sticky sessions as routing one conversation to the same place so its first-turn cache is reused.

Inference lines added and labelled as inference or as reasoning in the text:

- 38: "It is reasonable to expect that such a request waits first when the platform gets busy, although the docs do not say so in those words." (labelled as reasoning, docs silent)
- 38: "SlimSpec's gain sits in the drafter's output step, so it matters most when that step is the bottleneck." (follows from the original "shrinks the drafter's output projection cost")
- 38: the scenario and design-review advice on merged-checkpoint validation (advice, not a fact).

## Unresolved

- 38, section 5: the original says "use the signals in section 12". The chapter has no section 12. Left as written because it is original text and changing it is outside this rewrite. Owner should fix the pointer.
- 38, Scenario B: the original says requests served in eight hours were 55,694 versus 23,015, "about 6,960 versus 2,880 per hour". 55,694 divided by 8 is about 6,962, so "about 6,960" is a small rounding slip in the original. Left unchanged under the number rule. Owner should decide whether to restate it.
- 37 and 38: the Mermaid blocks are byte-identical to HEAD, so `node tools/check_mermaid.mjs` should give the same result as before. Not re-run here.
- 37, section 6: "Cautions come first" is followed by the original caution list. Read once for flow; no factual change.
- Semicolons: 37 has 5 in prose and 38 has 1. Some came from the original table cells and bullets. Not reduced in this run.
- Honest unverified lines kept as the original gave them: 37 "Not verified: federation against a live key..."; 38 "Not verified: no live Token Factory calls were made...".
