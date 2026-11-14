# Voice rewrite ledger, Part 17 chapters 01 to 03 (run A)

Scope: `docs/part-17-operations/01-observability-foundations-metrics-logs-and-traces.md`, `02-prometheus-and-grafana.md`, `03-logging-with-loki-and-tracing-with-opentelemetry.md`. Not touched: `planning/EXTERNAL_EDITS.md` (rulebook step 6 skipped on instruction), other chapters, code, commits.

Method: each file was assembled from a template. Front matter, the title and metadata table, every code fence, every table, every Mermaid block, all headings, the Exercises code spans, the checkpoint block and the Sources and review notes tail were copied byte-for-byte from `HEAD`. Only prose paragraphs, opening sentences and the Outcomes paragraphs were rewritten or added.

## Word counts (`wc -w`)

| File | Before | After | Growth |
|---|---|---|---|
| 01 observability foundations | 7086 | 9178 | +29.5 percent |
| 02 Prometheus and Grafana | 9096 | 11827 | +30.0 percent |
| 03 Loki and OpenTelemetry | 8211 | 10672 | +30.0 percent |

## Gates (run on the final files)

- `python3 tools/rewrite_guard.py HEAD WORKTREE <file>`: 0 hard failures on all three. New numbers 0, lost numbers 0, new code spans 0, lost 0, residue unchanged.
- `python3 tools/restore/chain_gate.py <file>`: 0.0 per 1000 words on all three (target 0.2 or lower).
- Span check (inline code spans, code fences removed), all three: missing `{}`, added `{}`.
- Not run: `node tools/check_mermaid.mjs` and `npm run build` (the handoff said no npm build; Mermaid blocks are byte-identical to HEAD).

## Shape checks

- Each section opens with a situation. Locked headings (Outcomes, Exercises, How it fails) sit above a situation sentence.
- Outcomes lists rewritten as a plain paragraph in all three chapters. No "will be able to" or "by the end" lines remain in the body.
- Lab steps keep the same commands, the same `# expected:` comments and the same step count. Exercises keep their count (6 in each chapter) and their solution-sketch code spans.
- Checkpoint blocks and Sources tails are unchanged (locked).
- One honest status per chapter in the body: the lab intro says the lab is untested and that the steps were not run on a live cluster. The Sources tail keeps its own "Not verified on live hardware" note (locked).
- Bold labels for "Symptom", "Diagnosis" and "Fix" were turned into plain sentences in the failure sections, to meet the one-bold-idea rule. The chapter 01 realities list keeps its one bold lead-in, and chapter 02 keeps its "Warning" and "Before a team runs" bold lines from HEAD.
- Exclamation marks: none added.
- Raw `<` or `{` in prose: none added.
- Math `$...$`: none in prose. The `$` characters in chapters 02 and 03 are inside shell, YAML or kubectl fences only.

## Needs source (general explanations added in prose, not attributed to any book)

Chapter 01:
- Service level objective (SLO) meaning in one sentence.
- p99 meaning ("the time that almost all requests finish within").
- NCCL as the GPU data-movement library, and "pending collective" meaning.
- Prefill and decode meanings in the 800 ms worked example.
- "Scraping" and "exporter" definitions.
- Golden signals as a short starting set (explanatory, not quoted).
- Method for picking the cardinality limit from memory (working backward).
- Schema meaning (a written list of field names, types and meanings).
- Prometheus sharding described as splitting series across several servers.

Chapter 02:
- "De facto standard" meaning.
- GitOps meaning (desired state in Git, a tool applies it).
- IAM meaning.
- Admission control meaning and the claim that a Pod without the required label is rejected at admission.
- Overcommitted node meaning.
- Certificate Authority file meaning.
- Webhook meaning.
- Counter and histogram behaviour, and how rate and the percentile function read them.
- Compaction meaning.
- Claim that a full disk makes Prometheus stop writing samples and dashboards show gaps.
- Claim that the Prometheus adapter lets the autoscaler query Prometheus.
- Dead-man's-switch "silence becomes the signal" phrasing.
- Silence practice (comment and expiry time) is advice, not sourced.

Chapter 03:
- Reading order of LogQL (selector, filter, aggregation).
- Chunk and index split in Loki.
- Standard out and standard error meaning.
- etcd meaning.
- APM meaning.
- OTLP carried over gRPC or HTTP.
- memory_limiter behaviour (refuses new data near its ceiling).
- Advice about old OpenTracing snippets.
- Claim that a mesh proxy can time a hop but cannot see application logic.

## Unresolved (for the owner; not changed in this run)

1. Chapter 01, section 2.3: `--storage.tsdb.max-label-values-per-label-name` is named as a Prometheus flag. Verify it exists in the target Prometheus version before the next review. Left as in HEAD.
2. Chapter 02, section 1.8 and 1.10: sample manifests pin Prometheus v2.20.0 and Alertmanager v0.21.0. These are old pins. Left as in HEAD.
3. Chapter 02, section 7.4 and chapter 01, section 4.1: the dcgm-exporter 4.9.0 note (renames) is kept as in HEAD. The 4.8.x to 4.9.0 mapping is in chapter 17.4, which is not part of this run. Per the 19-07 ledger, `code/part17` dashboard JSON still uses pre-4.9.0 names.
4. Chapter 03, section 1.5: the paragraph about logs written to standard out is near-duplicate in content with the paragraph before it. Left as in HEAD apart from the rewrite. A merge would be a content edit and should be a separate pass.
5. Chapter 03, section 6.8 queries Tempo on port 3100 while the lab's Tempo receiver listens on 4317. Not run, so the port pair is unverified.
6. The lab in all three chapters is untested against a live GKE cluster (status kept honest in the body and in the Sources tail).
7. Locked checkpoint answers were kept as they were. Several answers in chapter 02 and 03 are short and describe the chapter rather than teach from scratch. Parts 16-18 rule 10 asks for scenario-style checkpoints; that change is out of scope for this run because checkpoints were locked.
8. Original voice notes in chapter 01 section 1.2 and 2.2 cite "Production Kubernetes, chapter 9" and "the source notes". Kept as attributed in HEAD; not verified in this run.
