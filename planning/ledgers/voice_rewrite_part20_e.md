# Voice rewrite, Part 20 chapters 13 to 15 (run e)

Scope: docs/part-20-nebius-sre-interview/13-design-a-multi-tenant-llm-inference-api.md, 14-design-dedicated-endpoints-and-safe-model-rollout.md, 15-design-an-observability-pipeline-for-very-high-volume.md. Nothing committed. EXTERNAL_EDITS.md not touched (step 6 skipped per run instructions).

## Measurements (wc -w, whole file, HEAD vs worktree)

| Chapter | Before | After | Growth |
|---|---|---|---|
| 13 multi-tenant LLM API | 8021 | 10354 | +29.1% |
| 14 dedicated endpoints and rollout | 7103 | 9190 | +29.4% |
| 15 observability pipeline | 8032 | 10382 | +29.2% |

## Gates (run, output seen)

- `tools/rewrite_guard.py HEAD WORKTREE <file>`: 0 hard failures for all three. New numbers 0, lost numbers 0, new code spans 0, lost 0 for all three.
- `tools/restore/chain_gate.py <file>`: 0.0 per 1000 words for all three (target 0.2 or lower).
- Span check (backtick spans, fences removed): `{}` for all three.
- Structure check (scratch script, not committed): front matter, headings, every code fence, every table row, every `<details>` checkpoint block (10 each), and the Sources and review notes section are byte-identical to HEAD for all three.
- Not run: `node tools/check_mermaid.mjs` and `npm run build`. The run instructions say no npm build. Mermaid blocks are byte-identical to HEAD.

## Fixes made during the run

- Ch13: a new "99%" numeral in the percentile sentence was replaced with words.
- Ch13: a new "four" count word in the rate-limit table lead-in was removed.
- Ch14: a new "16-bit" numeral was replaced with "half-precision".
- Ch14: a number-heavy cluster example was rewritten without number words.
- Ch15: new clock-time numerals (02:00, 03:00) were replaced with "in the middle of the night".
- Ch15: a new `promtool` code span in the lab intro was reworded.
- Ch15: four new code spans (`honor_labels`, `without`, `le`, `histogram_quantile`) added in prose were reverted to plain text.
- Ch15: a claim about CI stopping merges was reworded to a neutral statement.

## Needs source (general explanations added, not from the original text)

Teaching definitions added in the new prose. None carries a Nebius fact, none carries a number, and none attributes a claim to a book. A reviewer should check the wording against a standard reference.

- Ch13: transient failure; SLO; token; context length; KV cache (why it grows with requests in flight); fail open and fail closed; at-least-once delivery; finish_reason meaning; strong consistency; audit log; signed snapshot; TTFT and percentile meaning; hop; backoff and jitter; circuit breaker and outlier ejection; SLI; cardinality; shadow stage; radix tree; prefill and decode roles; chunked prefill; backpressure; write timeout; NVMe; CUDA graph; bin-packing; hypervisor; RBAC; side channel; reconcile wording; burst and refill analogy.
- Ch14: state machine; reconcile loop; quantising; activations; tensor parallelism; FP16 as half precision; content hash; model registry; checkpoint; eval score; tick as a simulator unit; SIGKILL against SIGTERM; mounted volume; herd effect; surge slot; ceiling of traffic; drain; burn alert; sticky routing; rollback lock; human approval step for first rollback (a design option, labelled as reasoning).
- Ch15: SLI and series; span; write-ahead log; shard; sidecar; Pushgateway; failure domain; selector; ledger and append-only; compaction; downsampling; fan-out; code point; garbage collection; StatefulSet; structured metadata; hash for sampling; watch; promtool; synthetic probe; showback and chargeback wording; reconciliation wording.

## Unresolved

- Original Sources, Verification log and Not verified tails are unchanged, so no new attribution was added there. The new teaching sentences that rely on general knowledge are the ones listed above.
- Bold takeaway lines kept as in the original (one per section). Their wording was not rewritten, because each one is a short plain sentence already.
- Spelled-out number words were added in a few new sentences (for example "two customers" in ch13 section 11 and "ten" or "three" in some lead-ins). The guard only counts numerals, which show 0 new numbers. Flagging for the owner in case the stricter reading applies.
- Checkpoint answers are byte-identical to HEAD (rule 5), so they keep their original wording and were not reworded.
- The phrase "by the endpoint's region" in ch13 matches a naive outcome-list grep. It is not an outcome list.
- Math `$...$` with stray backticks: none found in these three chapters.
- "Not run" or "not verified" word present in all three (ch13 "Not verified" tail, ch14 "Step 5 was not run", ch15 "Not run.").
