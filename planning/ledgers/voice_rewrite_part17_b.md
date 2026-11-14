# Voice rewrite ledger, Part 17 chapters 04 to 06 (run B)

Scope: `docs/part-17-operations/04-dcgm-exporter-and-interpreting-gpu-metrics.md`, `05-distributed-observability-and-profiling.md`, `06-alerting-slos-and-health-checks-for-gpu-clusters.md`. Not touched: `planning/EXTERNAL_EDITS.md` (step 6 skipped on instruction), other chapters, code, commits. Each file was rewritten with a full Write after reading it end to end, then grown with Edit passes. Front matter, the metadata table, headings and their order, every fenced block (including the `text` and `markdown` fences and all Mermaid blocks), every table, every checkpoint and the Sources tail are byte-identical to HEAD.

## Word counts (`wc -w`)

| File | Before | After | Growth |
|---|---|---|---|
| 04 DCGM exporter and GPU metrics | 7179 | 9411 | +31.1 percent |
| 05 Distributed observability and profiling | 6289 | 8425 | +33.9 percent |
| 06 Alerting, SLOs and health checks | 6694 | 8705 | +30.1 percent |

## Gates (run on the final files)

- `python3 tools/rewrite_guard.py HEAD WORKTREE <file>`:
  - 04: `1 chapters, 0 with hard failures. words 6000 -> 8232. new numbers 0, lost numbers 0, new code spans 0, lost 0`
  - 05: `1 chapters, 0 with hard failures. words 5324 -> 7460. new numbers 0, lost numbers 0, new code spans 1, lost 0` (the one new span is the shell redirect `2>` in section 5.1, a typed command token)
  - 06: `1 chapters, 0 with hard failures. words 5839 -> 7850. new numbers 0, lost numbers 0, new code spans 0, lost 0`
- `python3 tools/restore/chain_gate.py <file>`: 04 = 0.1, 05 = 0.0, 06 = 0.0 per 1000 words (target 0.2 or lower; all pass).
- Span check (inline code spans, fences removed), all three: `{}` (no missing spans).
- Fence identity (all fenced blocks, Mermaid blocks included), all three: identical to HEAD (16, 21 and 15 fences).
- Checkpoint count unchanged: 20, 20, 20. Checkpoint blocks and Sources tails byte-identical.
- Exclamation marks in prose: none (the only `!` in 06 is `severity!="critical"` in a YAML fence).
- Outcome phrases ("will be able to", "should be able to", "By the end"): none left in the three bodies.
- Not run: `node tools/check_mermaid.mjs` and `npm run build` (this run was told no npm build; the Mermaid blocks are byte-identical to HEAD, so no new diagram syntax was introduced).

## Shape checks

- Every section now opens with a situation sentence. Where a locked heading sits above (Outcomes, Exercises, How it fails, Hands-on lab), the situation is the first sentence under the heading.
- Outcomes lists in all three chapters are rewritten as a plain paragraph of what the chapter walks through. No learning-goal lines remain.
- Exercises: the six titles, six sentences and six solution sketches keep their wording and numbers. Only the intro paragraph was rewritten.
- Lab steps: same step count and same commands in each chapter (04: six steps 6.2 to 6.6 plus 6.7 what to record; 05: six steps 8.2 to 8.7 plus 8.8 questions; 06: six steps 7.2 to 7.7 plus 7.8 questions). The `# expected:` comments are unchanged. Lab step prose has one situation and one question per sentence where a question appears.
- Honest status: 04 lab intro says the commands "were not run on hardware for this book"; 05 lab intro says "untested in this repository"; 06 lab intro says "not run on hardware for this book". Locked Sources tails keep their "not run" / "untested" lines.
- Bold: no new bold was added in any chapter. Existing bold lines stay as HEAD had them (04: the intro "Page on fault signals" line and the 1.4 "inferred, not stated" note; 05: the table row labels, the 05 intro "A workload without a profile" line and the 2.3 blockquote lead-in; 06: the intro "Before a team runs" line, the table labels and the "A page should mean" line).
- Numbers added to prose: none. Every digit token in the new text already existed in HEAD (guard: new numbers 0). Number words were used only where HEAD already had them, or in general phrases ("a few", "dozens").
- No invented attribution. The only book references are the ones HEAD already made (AI Systems Performance Engineering chapters 13 and 16, Production Kubernetes chapters 9 and 14, Chapter 10.21 and 20.19 cross-references).
- Semicolon chains: none added (chain gate 0.0 to 0.1).
- Raw `<` or `{` in prose: none added. `kubectl cordon <node>` stays inside the `markdown` fence, as in HEAD.
- Math `$...$`: none in these three chapters.
- Mermaid blocks: byte-identical.

## Needs source (general explanations added in prose, not attributed to any book)

Chapter 04:
- DaemonSet meaning (one pod per node) and Helm chart meaning.
- Taint and toleration meaning.
- Prometheus exposition format described as plain-text metric lines; scraping described as timed pulls.
- Claim that two exporters on one node scrape the same GPUs and double the series.
- Cordon, drain and RMA meanings, and the order "cordon, then drain, then RMA".
- Row remap as "moving a damaged row to a spare row in the same bank"; bank meaning.
- Xid meaning as a numbered driver error code written to the kernel log.
- Claim that a stuck NCCL wait keeps a kernel running, so utilisation stays high.
- NCCL meaning as NVIDIA's library for collective communication.
- Key-value cache meaning for vLLM memory.
- SM (streaming multiprocessor) meaning and "idle GPU drops its SM clock to a few hundred megahertz" phrasing (the figure is HEAD's own wording).
- All-reduce meaning (every GPU shares results) and the claim that one slow link slows the whole step.
- PCIe expansion (Peripheral Component Interconnect Express).
- The `for` clause meaning (condition must hold for that long before firing).
- Promtool meaning (Prometheus rule checker and unit-test runner).
- Claim that the PrometheusRule `release` label must match the Prometheus selector or the operator silently ignores the rules.
- Host engine meaning (the DCGM process that talks to the driver).
- Explanation that exporter restarts and frozen graphs look like a healthy GPU (restates HEAD; no new fact).
- Ordering advice for a stuck job (metrics to fault signals to links to throttle to utilisation, from HEAD's checkpoint 20).

Chapter 05:
- NVTX meaning (named range markers) and that NVTX is a naming convention you choose.
- Chrome Trace Event Format and the B and E phase meanings.
- Span and trace ID meanings.
- Claim that warm-up steps are slower and would distort a profile.
- Nsight Compute replays each kernel several times to collect counters, so it is slow (general fact, not in HEAD).
- Instrumentation versus sampling meaning.
- Register pressure and occupancy meanings.
- Stderr meaning and the `2>` redirect.
- Ring algorithm and protocol meanings in the NCCL log.
- Initialization phase meaning (GPUs find each other and set up links).
- P99 meaning (all but the slowest one percent of calls finish within the value).
- Small messages latency-bound and large messages bandwidth-bound (general performance explanation).
- Object storage and cold storage meanings.
- IAM expansion and the rationale for separating reader, writer and admin roles.
- SLO meaning in section 6.1 (already defined in chapter 17.6; repeated here in short form).
- Grafana data source meaning.
- Claim that profiles never travel through Tempo (inferred from the Mermaid diagram).

Chapter 06:
- SLI, target and window in plain words, and "bank account for failure" error-budget analogy.
- Canary release meaning.
- Advice that an SLI should match what the customer feels (a recommendation, not a sourced rule).
- Burn rate as a speedometer for the budget (analogy only, no new numbers).
- Route and receiver meanings; claim that routes are checked in order so a narrow early route catches first.
- Group wait meaning (short pause before the first notification).
- Probe framing: readiness is a traffic question and liveness is a survival question.
- Startup probe ordering (runs first, then liveness and readiness take over).
- Model weights meaning.
- SIGTERM meaning (signal asking a process to shut down).
- Post-mortem meaning.
- Annotation meaning.
- Claim that Prometheus does not contact PagerDuty or Slack directly (inferred from the Mermaid diagram).
- Advice that on-call engineers should not be able to edit routing during an incident (recommendation, not sourced).
- Claim that a bad health script can look thorough and still pass a broken node (opinion).
- Claim that a route with no owner leaves its alerts unanswered (opinion from the section text).

## Unresolved (for the owner; not changed in this run)

1. Checkpoints in all three chapters are locked by rule 5, so they stay recall-style. Chapter 04 is closest to the Parts 16-18 scenario style (checkpoints 18 to 20 are scenarios). Chapters 05 and 06 have many "Why does X" and "What is Y" questions that rule 10 of RULES_AND_WORKFLOW would call bare definitions. Rewriting them needs an owner decision because checkpoints are locked here.
2. Chapter 05, section 6.2: the sentence "The profile cardinality is the profile's storage cost" uses "cardinality" in a non-standard sense (the metric label sense is the usual one). Kept as HEAD. Suggest the owner rename the term in a separate pass.
3. Chapter 05, the `text` fence in "Why this matters" (background reading with "60-80%" and "20-40%" figures) reads like prose. Kept as a fence because rule 2.9 forbids turning fences into prose in this run. Owner decision for a later pass.
4. Chapter 05, section 2.3 blockquote keeps its bold lead-in "dcgm-exporter 4.9.0 version note." (HEAD text). It is the only bold idea in that section.
5. Chapter 04 section 1.4: the NVLink factor remains "not confirmed" and the helper refuses to scale it (HEAD). Unchanged.
6. Chapter 05 section 8.4 and 8.5 commands (for example `gsutil cp /profiles/*.json`) and the Pyroscope data source type in 8.6 were not verified in this run. Kept as HEAD.
7. Chapter 06 section 1.4 "Chapter 20.19 owns what to measure" and the 20.19 tested rule file path are cross-references HEAD made; not re-checked here.
8. The lab in all three chapters remains untested against a live GKE cluster (HEAD status, kept).
9. Mermaid checker and `npm run build` were not run in this run (see gates). The Mermaid blocks are byte-identical to HEAD, so the build result should match HEAD's.
10. The 04 "Why this matters" paragraph says "800 GPUs" and the checkpoint 18 cost range is HEAD's example; both kept.
