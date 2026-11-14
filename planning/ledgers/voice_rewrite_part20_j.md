# Voice rewrite ledger: Part 20, chapters 28 to 30 (run j)

Scope: `docs/part-20-nebius-sre-interview/28-the-project-deep-dive-and-the-final-round.md`, `29-the-8-week-plan-the-final-week-and-the-cheat-sheet.md`, `30-nebius-ai-factory-to-token-factory-architecture.md`. Not committed. `planning/EXTERNAL_EDITS.md` not edited (step 6 ignored per run instruction). `npm run build` not run (per run instruction). Only the three chapters and this ledger were touched.

## Method

Each chapter was rebuilt from its `HEAD` version by a scratch script that splits the file into units (blank-line separated; fenced code, Mermaid and `<details>` blocks are atomic). Only the prose units named in a per-chapter map were replaced, and new teaching paragraphs were inserted after named prose units. Headings, tables, fenced code, Mermaid, checkpoint `<details>` blocks, front matter, the Sources and review notes tail and the Verification log are byte-identical to HEAD (checked by a structure comparison, all `True`). Each section's first prose unit was rewritten to open with a situation. Where a locked element (a table or a heading followed by a table) came first, the situation was added as a new paragraph in front of it, as in the Common mistakes section of 28 and 29.

## Word counts (`wc -w`, HEAD vs worktree)

| File | Before | After | Growth |
| --- | --- | --- | --- |
| 28 project deep dive and final round | 6972 | 8996 | +29.0% |
| 29 8-week plan, final week, cheat sheet | 7814 | 10539 | +34.9% |
| 30 AI factory to Token Factory architecture | 6227 | 8462 | +35.9% |

## Gates (run on the final files)

- `python3 tools/rewrite_guard.py HEAD WORKTREE <file>`: 0 hard failures on all three.
  - 28: `words 5662 -> 7686, new numbers 0, lost numbers 0, new code spans 0 lost 0`
  - 29: `words 6425 -> 9150, new numbers 0, lost numbers 0, new code spans 0 lost 0`
  - 30: `words 6068 -> 8303, new numbers 0, lost numbers 0, new code spans 0 lost 0`
- `python3 tools/restore/chain_gate.py <file>`: 28 = 0.0, 29 = 0.0, 30 = 0.0 per 1000 words (target 0.2 or lower). Exit OK on all three.
- Mandatory inline-span check (HEAD vs worktree, fenced blocks excluded): `{}` for all three.
- `node tools/check_mermaid.mjs`: `checked 776 diagrams, 0 failed`.
- Structure, HEAD vs worktree: headings, fenced blocks, `<details>` checkpoint blocks (10, 11 and 10 blocks, unchanged), table lines and the Sources and review notes tail are identical on all three.
- Banned-pattern scan on the three files: no new `!`, no "will be able to", no "should be able to", no "you will learn", no "In this chapter". Raw `<` and `{` counts equal HEAD (all inside existing code or tags). Semicolon count equal to HEAD (29 keeps its 8 original semicolons in the code and tables, and none were added in prose).
- Honest status kept once per chapter: 28 "Steps 5 and 6 are practice you do yourself, and they were not run here."; 29 "It was not run here." (step 4); 30 "I did not run any of it against a live endpoint."
- Opening word of new section leads varied between "Imagine" and "Consider" to avoid one repeated opener.

## Rule notes

- Rule 2 (situation first): every section opens with a situation sentence. Locked headings are untouched; the situation sits in the first prose line under them, or in an inserted paragraph before a locked table.
- Rule 3 (no outcomes lists): none added. The "How to answer out loud" blocks keep bold question labels and the original order.
- Rule 5 (facts exact): no digits added to any prose. Every number in the original prose survived in the same unit. Attribution tags ([official], [vendor], [inference], [report], [gap]) kept where they stood.
- Rule 9 (exercises and lab steps): step counts unchanged. 28 lab has 6 steps, 29 lab has 4 steps (the original text says "All three steps" and its step 4 is a practice step; this is pre-existing and kept), 30 lab has 5 steps. Commands, expected results and span contents are unchanged. Step text was reworded to one instruction per sentence.
- Checkpoint `<details>` blocks and the drill questions were not edited. A situation lead-in was added before the "Drill questions" heading in each chapter.
- Nebius facts: none added. Nebius-related sentences were only reworded. Where a sentence described a Nebius fact, the fact and its tag stayed exactly as in HEAD.
- Gem books: named by the full title already in the original (Systems Performance, Production Kubernetes). No abbreviation was introduced.

## Needs source (general explanations added, not Nebius, book or vendor facts)

These are general teaching explanations written for this rewrite. None is a claim about Nebius internals. Check before publication.

- 28: control plane as where settings are managed and data plane as where user requests travel; retry amplification as a slowdown made worse by client retries; site reliability engineering (SRE) expansion; KV cache as the memory a model fills with attention keys and values.
- 29: Leitner scheme as an old flashcard method; toil as repetitive manual work that does not improve the service; PodDisruptionBudget (PDB) as the rule limiting how many pods a drain may remove; NVIDIA Xid messages as GPU error codes in the kernel log, read from the NVIDIA catalog; "load factor" as a small multiplier; the claim that a dry run helps (advice).
- 30: InfiniBand as a high-speed network fabric; NCCL as NVIDIA's collective communication library and AllReduce as the gradient-combining step; stateful and stateless firewall meanings; Preview as a status that may change (paraphrase of the source's "intended for testing and feedback"); Prometheus as the metrics server and Grafana as the chart tool; LoRA as a method that trains small adapter layers on a frozen model; continuous batching; prefill and decode as the read-prompt and write-answer steps; backpressure; "trajectory" as one agent's full sequence of steps; CoreDNS as in-cluster name lookup and Cilium as cluster networking; cordon and drain meanings; etcd as the key-value store for cluster state; OpenAPI schema as a machine-readable API description; canary and drain as rollout terms; X+1 redundancy as a spare unit beyond need; error budget and burn rate as used in SLI paragraph; p50, p90 and p99 as median and high percentiles; "best-effort" meaning; peak-to-average ratio; registry and cost allocation; non-preemptible meaning; degraded mode; jitter as random spacing between retries; the "service level agreement (SLA)" expansion.

## Unresolved

- Checkpoint form in 28 is `<details><summary>Answer</summary>` after a numbered question line, not the `<details><summary>N. Question?</summary>` form in the rulebook. It was kept byte-identical (rule 5). The owner may want that form changed in a later pass.
- Ch 29 lab intro says "All three steps ran" while the lab has four steps. Pre-existing and kept.
- Ch 30 uses "Devlabs" (original term, not checked here). Kept as in HEAD.
- Math `$...$` with stray backticks: none found in these three chapters, nothing to note.
- `python3 tools/language_audit.py` and `npm run build` were not run in this run (per run instruction only the Mermaid check was required).
- Not committed. The working tree also shows other agents' changes (for example chapter 31 is modified); those were not touched.
