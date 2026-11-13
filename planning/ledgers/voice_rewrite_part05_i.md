# Voice rewrite, Part 5 chapters 5.22 to 5.24 (batch i)

Scope: docs/part-05-kubernetes/22, 23, 24. Uncommitted. Gates run per chapter with
`python3 tools/rewrite_guard.py HEAD WORKTREE <file>` and `python3 tools/restore/chain_gate.py <file>`.
Not run (out of scope): `npm run build`, full Mermaid check, language_audit, pytest.

## Per chapter

| Chapter | Words before | Words after | Growth | Guard (hard failures) | New numbers | Lost numbers | Chain gate |
|---|---|---|---|---|---|---|---|
| 5.22 multitenancy and platform services | 13747 | 17421 | +26.7% | 0 | 0 | 0 | 0.0 per 1000 |
| 5.23 autoscaling (HPA, VPA, KEDA, CA, Karpenter) | 9640 | 12884 | +33.6% | 0 | 0 | 0 | 0.0 per 1000 |
| 5.24 observability for Kubernetes | 10822 | 14009 | +29.5% | 0 | 0 | 0 | 0.1 per 1000 |

Code spans: 5.22 +4 / -0 (field names in the onboarding spec and exercises), 5.23 +14 / -0, 5.24 +17 / -0.
All added spans are typed field or metric names. No code block, Mermaid block, table, front matter, heading
or checkpoint block changed. Checkpoint count is 20 in each file. Sources sections unchanged.

## Method

- Whole-file rewrite per chapter (every section, in order). Headings, code blocks, Mermaid and tables copied.
- Each section opens with a situation or keeps its original situation opener, then the mechanism.
- Added: analogies (keycards and room keys, shared car park, kitchen and cooking, apartment vs house,
  relay race, light switch and dimmer, tailoring shop, rowing crew, switchboard, parcel tracking),
  worked walkthroughs (5.22 new-team first week, showback over a month, idle-GPU and quota rows;
  5.23 one scale-up spike from time zero, Prometheus Adapter `describe` conditions, flapping diagnosis;
  5.24 Fluent Bit pipeline stages, Events timeline, burn-rate reading, Go tracing handoff), and "why" sentences.
- Residue removed: "The book's authors" (5.22), "The book's rule of thumb" and "The book notes / works
  through" (5.24) now name *Production Kubernetes*. "(untested here)" removed from reader text in 5.22 and 5.24.
  It remains only inside the Sources sections, as the rule keeps.
- Honest status kept once per chapter: status row ("labs **untested**") plus one sentence above the lab.
- Exclamation marks: none in prose. The only "!" characters are `!=` in PromQL and Go, and one example log
  line inside a code span in 5.24 (`hello world!`).
- Exercises rewritten per rule 9 (same count: 5.22 six, 5.23 nine, 5.24 six). Fixed three sentences
  that carried more than two numbers (5.23 exercise 9, 5.24 exercise 3 and exercise 6). Each still keeps its facts.
- Lab steps rewritten (5.22 thirteen, 5.23 fourteen, 5.24 thirteen; same count and commands). Closing
  paragraphs added after each lab (reading order, expectation-versus-result habit, what to write down).
- Inline code spans: a few exercise names had been unwrapped in the first pass and were restored
  (`ResourceQuota`, `LimitRange`, `Team`, `AcmeNamespace`, `PriorityClass`, `vGPU`, the StorageClass key).

## Kept on purpose

- Checkpoint blocks verbatim (count 20 each). Checkpoint answer voice not rewritten, as in batches a to h.
- Sources sections verbatim, including "(`untested here`)" and "not verified" lists.
- The 5.22 final line "corrected 2026-11-11: PodSecurityPolicy ..." kept.
- 5.24 dcgm-exporter 4.9.0 version note kept verbatim (fact-bearing, links to 17.4).
- 5.23 heading "Cluster Autoscaler (CA)" etc. unchanged.

## Unresolved / Needs source

5.22
- Added general claim, "a delete command in an init container cannot guarantee every block is clean". Needs source
  (NVMe wiping guarantees). Reasoning only, no number.
- Added judgement: kernel and control plane are the layers most often separated by sandboxing or a separate
  cluster. Needs a check against the multi-tenancy docs, or keep as the author's view.
- Original "Needs source" items unchanged: Stage 2 Helm sample values, Pinterest 25 vs 350 lines, Waypoint file.

5.23
- Added explanation: `cooldownPeriod` is the quiet time before scale to zero; `pollingInterval` is the trigger check
  rate. Consistent with checkpoint 8. Source check optional.
- Added explanation: `preStop` hook meaning, and Karpenter drift meaning ("replaces nodes after AMI update").
  Consistent with the original line. Optional source check.
- Lab and exercise "70B cold start from 12 minutes" kept as study items (original numbers).

5.24
- Added general claims without a number: conntrack table full "silently drops new connections" (dashboard
  section 6). Needs source.
- Added: agent mode "saves disk on small clusters" (section 7). Judgement. Needs source check.
- Added: Alertmanager gossip keeps alert history when one instance fails. Judgement. Needs source check
  against Alertmanager HA docs.
- Added: WAL meaning ("may lose the most recent data after a broken WAL"). Needs source check.
- Original "Needs source" items still open: scrape interval ranges (15 to 30 s), retention and PVC sizes,
  the 1 to 2 bytes per sample estimate, the "several KB per series" estimate, checkpoint 20 timings.

## Attribution

- Gem book titles in full. *Production Kubernetes* chapter references kept. *Kubernetes: Up and Running* unchanged.
- Chapter cross references (5.5, 5.9, 5.18, 4.24, 4.26, 17.4, Part 12, Part 17) kept.
