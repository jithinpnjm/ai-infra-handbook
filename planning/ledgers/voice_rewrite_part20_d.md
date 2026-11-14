# Voice rewrite, Part 20 chapters 10 to 12 (batch d)

Scope: `docs/part-20-nebius-sre-interview/10-complexity-latency-numbers-and-measuring-your-own-code.md`, `11-coding-practice-set-40-problems-with-tested-solutions.md`, `12-estimation-toolkit-for-inference-capacity.md`. Nothing committed. `planning/EXTERNAL_EDITS.md` not edited (per run instruction). No `npm run build` (per run instruction).

## Method

Each file was rebuilt from a template in the scratch folder. Locked spans were copied from `git show HEAD:<file>` by line range, so code fences, tables, Mermaid, checkpoint and drill blocks, the Sources and review notes tail and the Verification log are byte-identical to HEAD. The rewritten prose is new text. Chapter 11 problem blocks (statement, hints, the `**Insight.**` line) are copied from HEAD unchanged, and the teaching prose sits before each one.

## Word counts (`wc -w`, HEAD vs worktree)

| File | Before | After | Growth |
| --- | --- | --- | --- |
| 10 complexity, latency numbers | 6742 | 8759 | +29.9% |
| 11 coding practice set | 8824 | 11713 | +32.7% |
| 12 estimation toolkit | 8925 | 11639 | +30.4% |

## Gates (run on the final files)

- `python3 tools/rewrite_guard.py HEAD WORKTREE <file>`: 0 hard failures on all three.
  - 10: `words 5187 -> 7204, new numbers 0, lost numbers 0, new code spans 0 lost 0, residue 0->0`
  - 11: `words 7995 -> 10884, new numbers 0, lost numbers 0, new code spans 0 lost 0, residue 4->2`
  - 12: `words 7801 -> 10515, new numbers 0, lost numbers 0, new code spans 0 lost 0, residue 2->2`
- `python3 tools/restore/chain_gate.py <file>`: 0.0 per 1000 words for all three (target 0.2 or lower).
- Mandatory span check (inline code spans, HEAD vs worktree, fenced blocks excluded): `{}` for all three.
- Structure, HEAD vs worktree: heading lists identical; fenced-block lines 28/12/24 unchanged; `<details>` checkpoint and drill blocks 10/50/10 unchanged; table rows unchanged in 12.
- `node tools/check_mermaid.mjs`: `checked 776 diagrams, 0 failed`.
- Banned-pattern scan on prose: no `!`, no "will be able to", no "should be able", no "you will learn", no "In this chapter". Raw `<` only in the locked `<details>` tags.

## Rule notes

- Rule 5, locked tails: the Sources and review notes sections and the Verification log in all three files are copied from HEAD. Because of this, those tails do not open with a situation sentence. This is the one exception to "every section opens with a situation". The Drill questions blocks are locked too, but each gained one situation line above it.
- Rule 9, lab and exercise steps: step counts unchanged (10: 6 steps; 11: 5 steps; 12: 7 steps). Commands unchanged. Expected-result sentences in 10 were split so each sentence carries at most two numbers. Chapter 12 step 3 was split the same way.
- Rule 13 and honest status: 10 keeps "were not run, by instruction" (locked tail) and "Every step ran on the Apple M3 machine named above." 11 keeps the "Steps 1, 2, 3, 4 and 5 ... were run" line and "Not run: pytest on another Python version, and any timing benchmark." Its two "I ran this" sentences were reworded to "This was run" with the observed output stated. 12 keeps "Not run for this chapter." on step 7 and the "No GPU was available" line in the locked tail.
- Residue: no new "I ran", "my tool", "untested here", "the book says" or "Volume N" in prose. In 12 the prose "the book notes" was changed to "Systems Performance, chapter 2, notes" (same attribution, named).
- Drill questions and checkpoint answers (10 in 10 and 12, 40 hint blocks plus 10 answers in 11) are byte-identical to HEAD.
- Gem books: named by the same short forms the original used (Systems Performance, Fluent Python, Learning Python, Hands-On LLM Serving and Optimization, LLMs in Production, AI Systems Performance Engineering, Distributed AI Systems, AI Factory). No abbreviations added. No new book or chapter attribution was added.
- Numbers: no digit added to prose in any chapter. Number words added in prose were checked and removed where they were invented ("a week", "a thousand clients", "a month", "twenty minutes in").
- `$` in 12: the dollar signs are GPU and token prices (for example `$4.50`), not LaTeX math. Count of `$` characters in prose is 30, against 36 in HEAD including the locked tail. None was changed.

## Needs source (general explanations added, no Nebius or book facts added)

These are general teaching explanations. None is a claim about Nebius internals. Each should be checked before publication.

- 10: the coat-rack analogy for amortised append (analogy only); hash table slot and collision; Timsort as Python's sort (the original names it, the description is added); KV expanded as key and value; "memory hierarchy" as the stores a CPU reads through; "hot data" meaning; CDN expanded as content delivery network; "deterministic profiler" meaning (traces every call); M/D/1 described as random arrivals and fixed service times; "hashable" meaning and why a list cannot be a set member; "error budget" as the failure allowance; "time-series" and "queue" as waiting in line;
- 11: "oracle" meaning; "invariant" meaning; the coat-rack and file-manager analogies (analogies only); "half-open" left as the original defines it; "lazy deletion" and "property test" explained in one clause each; "canary deployment" as a context for M1 (story only).
- 12: Little's law as a plain identity from queueing theory that holds for a stable system; MFU expanded as model FLOPs utilisation (general definition); "fragmented cache" wastes memory; a node can drain for maintenance and a card can fall off the bus (general failure modes, not Nebius practice); the delivery-van analogy for decode (analogy only); the knee of the curve as the point where extra batch buys little throughput; continuous batching without it waits for the slowest request (general reasoning, consistent with the original's "finished request leaves, waiting one joins"); the failure-domain remark about fewer, larger replicas (general).

## Unresolved

- Nothing failed a gate.
- Chapter 12 sanity-check items and scenario steps are kept verbatim as numbered lines. They are short and number-dense, so the reading style there is the original's, with prose added around them.
- Chapter 11 "Insight", "Common wrong answer" and "Follow-up" lines are kept verbatim, since they carry the problem facts. The teaching prose is added before each problem block.
- Chapter 12 Connections bullets are kept verbatim (cross-reference codes such as `c15-02`).
- Check in review: the chapter 11 Sources tail still names "Learning Python, 6th edition ... background only" and the Google SRE Workbook URL as in HEAD. Not changed.
- `planning/EXTERNAL_EDITS.md` not updated (run instruction).
- Nothing committed. Owner go-ahead needed.
