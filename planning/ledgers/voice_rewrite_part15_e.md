# Voice rewrite ledger: Part 15 chapters 13, 14, 15

Scope: docs/part-15-inference/13-profiling-debugging-and-tuning-inference-at-scale.md, 14-benchmarking-genai-perf-latency-percentiles-and-goodput.md, 15-autoscaling-inference-hpa-keda-and-scale-to-zero.md. Not committed. EXTERNAL_EDITS.md not edited (per run instructions). No other chapter touched. Locked: front matter, headings, tables, code and Mermaid blocks, checkpoint questions and answers, Sources and review notes.

## Words (wc -w, HEAD vs worktree)

| Chapter | Before | After | Growth |
|---|---|---|---|
| 15.13 Profiling, debugging and tuning | 22831 | 29225 | +28.0% |
| 15.14 Benchmarking | 13956 | 18051 | +29.3% |
| 15.15 Autoscaling | 10532 | 13687 | +29.9% |

## Gates (run on the files on disk)

- `python3 tools/rewrite_guard.py HEAD WORKTREE <file>`: 0 hard failures on all three. New numbers 0, lost numbers 0.
  - 15.13: body words 19278 -> 25672; new code spans 0 (one extra span `record_function()` in an added sentence, not a loss).
  - 15.14: body words 9447 -> 13542; new code span `histogram_quantile` (added once in prose).
  - 15.15: body words 7482 -> 10637; new code spans `curl`, `sum`, `count` (added in prose, typed terms).
- `python3 tools/restore/chain_gate.py <file>`: 15.13 0.0, 15.14 0.0, 15.15 0.1 per 1000 words.
- Span check (HEAD vs worktree, prose spans only): empty result for all three after restoring the lost spans in the Outcomes text.
- Exclamation marks in prose: 0 in all three.
- Outcome-style learning-goal lines: removed. Outcomes sections converted to plain paragraphs (headings kept).
- Exercises rewritten to rule 9 form (no nested (a)/(b)); same four exercises, same function names and values. 15.13 exercise parts now run as one sentence sequence per exercise. Numbers per sentence kept to 2 or fewer in the rewritten exercise text.
- Build: `node tools/check_mermaid.mjs` and `npm run build` NOT run in this pass (only the chapter-level gates above were run). Mermaid blocks are unchanged.

## Honest status

- 15.13: "not run on live GPU hardware" in the lab venue block (kept), plus the existing reference-template status line.
- 15.14: "(`untested` on live GPUs)" span kept in 7.1; "This handbook did not run AIPerf" kept in 3.1.
- 15.15: lab venue note "not verified on live GPU hardware" kept; multi-node manifests remain marked untested.

## Needs source (general explanations added, no new facts)

- 15.14: Little's Law holds without assumptions about arrival spread (distribution-free). Presented as general knowledge.
- 15.14: Explanation of why one slow item blocks a line (head-of-line blocking) and what a histogram bucket counts.
- 15.14: Explanation of forward pass, GIL behavior in a process pool, and why fixed seeds make prompt mixes comparable.
- 15.15: Definitions of PagedAttention block storage, ConfigMap/cluster-admin, DaemonSet, PriorityClass, taint NoSchedule, bounce buffer, page cache.
- 15.15: Traffic-light reading of the cache zones is an explanation of the table, not a new threshold.
- 15.13: NVTX/CUPTI roles, stream and warp definitions, L1/L2 role, NIC definition, busy-wait explanation, Alertmanager role, kubelet role in probe failures.
- 15.13: Analogies (warehouse allocator, parking garage, kitchen, coffee shop, bus timetable, two-lane road, waiting room) carry no numbers and are explanations only.

## Unresolved

- Math `$...$` with stray backticks: none found in these three chapters, so nothing to repair. `$` in 15.15 is currency text in the original (cost tables, `$/1M` labels) and was left as is.
- Key takeaways in 15.14 and 15.15 are unchanged in wording beyond a lead-in sentence (15.13 has a new lead-in too). Their bullets were not rewritten.
- Blockquote dcgm-exporter version notes (15.13 and 15.15) are original text and were not reworded.
- The Mermaid/build gates still need one run by the owner or a later pass.
