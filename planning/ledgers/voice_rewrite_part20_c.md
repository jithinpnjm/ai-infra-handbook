# Voice rewrite, Part 20 chapters 20.7 to 20.9 (batch c)

Scope: `docs/part-20-nebius-sre-interview/07-the-console-round-text-tools-systemd-and-everyday-operations.md`, `08-the-coding-round-what-to-expect-and-how-to-perform.md`, `09-algorithm-patterns-for-sre-flavoured-problems.md`. Nothing committed. `planning/EXTERNAL_EDITS.md` not edited (per owner instruction, step 6 skipped).

Method: each chapter's prose lines were replaced line by line against the HEAD version. Fenced code, tables, headings, front matter, the checkpoint `<details>` blocks, the Mermaid diagrams and the Sources and review notes (plus the Verification log in 20.9) were not targeted, and a script check confirms they are byte-identical to HEAD.

## Word counts (`wc -w`, HEAD vs worktree)

| File | Before | After | Growth |
| --- | --- | --- | --- |
| 20.7 | 8635 | 11444 | +32.5% |
| 20.8 | 7103 | 9640 | +35.7% |
| 20.9 | 10893 | 14117 | +29.6% |

## Gates (run on the final files)

- Mandatory span check (inline code spans, HEAD vs worktree, fenced blocks excluded): `{}` for all three.
- `python3 tools/rewrite_guard.py HEAD WORKTREE <file>`:
  - 20.7: `words 7010 -> 9819, new numbers 0, lost numbers 0, new code spans 0 lost 0`, 0 hard failures
  - 20.8: `words 6264 -> 8801, new numbers 0, lost numbers 0, new code spans 0 lost 0`, 0 hard failures
  - 20.9: `words 6895 -> 10119, new numbers 0, lost numbers 0, new code spans 0 lost 0`, 0 hard failures
- `python3 tools/restore/chain_gate.py <file>`: 20.7 0.0, 20.8 0.1, 20.9 0.0 per 1000 words (target 0.2 or lower).
- Locked-block identity (script, HEAD vs worktree): fenced code blocks identical, headings identical, front matter identical, table rows identical, the 10 `<details>` checkpoint blocks identical in each chapter, Mermaid identical, Sources and review notes identical.
- Rule 9 counts unchanged: 20.7 lab has 6 steps, 20.8 lab has 5 steps, 20.9 lab has 3 steps. Commands and expected results kept.
- No exclamation marks in prose (the only `!` in 20.7 sits inside a quoted output span, as in HEAD). No "will be able to", "should be able to" or "you will learn" in any of the three.
- Semicolon count unchanged from HEAD in each chapter.
- Honest status words kept once per lab or section: 20.7 "Mostly not run" and "Not verified" section; 20.8 "This exact mutation was not run" and "Not verified" section; 20.9 "These lab steps were not run in a container" and "Not verified" section.
- `node tools/check_mermaid.mjs` and `npm run build` not run. The batch instruction said "No npm build". The Mermaid blocks are byte-identical to HEAD.

## Rule and gate notes

- Rule 13 (test-log language): first-person run records kept in natural voice. 20.7 "I ran this with Docker" paragraph was split into three short paragraphs (what PID 1 is, what the Docker run showed, the zombie count). Test-log sentences were not moved, because the headings and the Sources and Verification sections are locked.
- Section openers: every section now opens with a situation. Where the original opened on a definition or a rule (20.7 section 2 and 4, 20.8 sections 1 and 2, 20.9 "The last two small patterns" and the "How to answer out loud" intro), a situation sentence was put first. Where a locked heading sits above (the "Question N" bold lines in 20.9 and the "Task N" headings in 20.7), the situation sits in the first sentence under the heading.
- Bold: the original bold markers were kept where they sat. Bold was not added to new sentences.
- Connections lists (20.7, 20.8, 20.9): one intro sentence added above each list. The original bullets are unchanged. In 20.7 the 20.3 bullet was restored to its full original text after a first pass truncated it. The guard counted that as lost numbers 1 at that point. It is now 0.
- Exercises (20.7 "Task" statements): the original "Task: ..." sentences were kept inside each statement, with a situation sentence added before them. No exercise count changed. The "Why it works" and "Common wrong approach" paragraphs were expanded in place.
- Numbers: none added to prose beyond the original's facts. Number words that restated an original figure were removed ("sixteen" in 20.9 and "three in the morning" in the 20.9 alert scenario, and "ninety-five percent" in the 20.9 percentile addition). The "signal 13" and "03:00" mentions are the same numbers as the original.
- Code spans: none removed. Some were repeated in added sentences, which the guard does not count as new spans.

## Needs source (general explanations added, no Nebius or book facts added)

These are teaching explanations written for this rewrite. None is a claim about Nebius internals. Check before publication.

- 20.7: the idea that a unit is a small contract (what runs, needs, order); the web server and database example for `Requires` and `Wants`; the restart-loop sequence and the statement that a start-limit hit marks the unit failed (systemd behaviour, check against systemd.unit); the timer and service as two halves of one job; `journalctl -u` as a filter on the unit field; a stop-timeout escalation note; the zombie as an unread note, holding a process table slot; `$?` as a note overwritten by the next command; the TERM cleanup explanation (flush buffers, remove temporary state) and why KILL loses in-memory data; the log rotation sequence (rename, new file, open handle still points to the old file); the copy-then-truncate gap explanation; the passwd field description as labelled boxes; trailing-slash rsync explanation; the POSIX definition as a common core; the mawk and gawk explanation; the photocopy-style explanation of percentile rank; the `$?` and `set -e` teaching points.
- 20.8: the streetlight framing (original cites Systems Performance; the added self-check sentence is teaching); the rollback analogy; the plain-editor typo narrative; the dictionary-order and stable-sort definitions; IEEE binary floating point explanation for `0.1 + 0.2`; the explanation for `[[0] * 2] * 2` and why the comprehension works (general Python semantics); the explanation for why the slice copy is O(n) (general Python semantics); the lift-queue picture for the deque maximum; the photocopy picture for slicing; the Go byte and rune note; the stress-test and checklist teaching notes.
- 20.9: the shop-with-closed-door picture for backoff; the explanation of why jitter spreads retries; idempotent retry safety example (a retry cannot charge a customer twice); amortised cost definition (general); building-block and team-leader pictures for topological sort and union-find; ticket-office and savings-account pictures for the rate limiters; the clock-face picture for consistent hashing; the claim that a restarted router with a different hash would move every session (follows from the original's statement that the built-in string hash changes between processes); the restaurant-host picture for asyncio gather and timeouts; the conveyor-belt picture for a bounded queue and backpressure; the lock explanation of the read-add-write race and the two-increment example (general); the reservoir and histogram trade-off sentence; the advice to prefer a tested library for t-digest; the picture for the sorted list of response times and p95; the heap picture of the top-k root; the desk picture for LRU (general); the reading of the reversed edges during a blast-radius walk.

## Gem books

No new book references added. Attributions in the original were kept as they were: "Systems Performance", "How Linux Works", "Production Kubernetes", "Fluent Python", "Learning Python", "Distributed AI Systems". These are the short forms the original used. Rule 12 asks for full titles in gem-book attributions. Expanding them to full titles would change attribution text, so this was left for a later pass.

## Unresolved

- Nothing failed a gate.
- Mermaid and `npm run build` not run for this batch (instruction said no npm build).
- Gem book short forms kept as in the original (see Gem books).
- `$...$` math with stray backticks: none found in these three files.
- `planning/EXTERNAL_EDITS.md` not updated (owner instruction to skip step 6).
- Review by Claude: check the 20.7 Restart and Timer paragraphs and the 20.9 Question paragraphs against their sources (see Needs source).
