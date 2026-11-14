# Voice rewrite ledger: Part 14 chapters 10, 11, 12

Scope: docs/part-14-training-finetuning/10-multi-node-training-architecture.md, 11-checkpointing-fault-tolerance-and-elastic-training.md, 12-training-performance-engineering-and-troubleshooting.md. Not committed. EXTERNAL_EDITS.md was not edited (step 6 skipped per run instructions).

## Word counts (wc -w, whole file)

| File | Before | After | Growth |
|---|---|---|---|
| 10-multi-node-training-architecture.md | 11412 | 14920 | +30.8% |
| 11-checkpointing-fault-tolerance-and-elastic-training.md | 6442 | 8336 | +29.4% |
| 12-training-performance-engineering-and-troubleshooting.md | 10662 | 13787 | +29.3% |

## Gates (run on the final file for each chapter)

- `python3 tools/rewrite_guard.py HEAD WORKTREE <file>`: 0 hard failures in all three. New numbers 0, lost numbers 0, new code spans 0, lost code spans 0 in all three.
- `python3 tools/restore/chain_gate.py <file>`: ch10 0.1, ch11 0.0, ch12 0.2.
- Span check (inline code spans, HEAD vs worktree, fenced code excluded): `{}` for all three. One span (`nvidia-smi`) was dropped in ch12 during the first pass and restored in the Outcomes paragraph.
- `node tools/check_mermaid.mjs`: checked 776 diagrams, 0 failed (repo-wide script).
- `npm run build`: not run (run instructions say no npm build).
- Locked tails (Checkpoint questions, Sources and review notes, and the inference notes after them) are spliced byte-for-byte from HEAD. Headings, front matter, code blocks, tables and Mermaid blocks are also byte-identical to HEAD (copied by block index, not retyped).
- Honest status: each chapter has one plain sentence above its lab ("These steps were not run on a live cluster"). Existing `untested here` / `tested` spans are unchanged.
- Style scan: no exclamation marks, no raw `<` or `{` in prose, no `$...$` math, no "you will be able to" lines in body prose.

## Structural changes made

- Outcomes lists (ch10, ch11) and the outcome list in ch12 were rewritten as plain paragraphs. The outcome items' code spans (`PyTorchJob`, `JobSet`, `c10d`, `TCPStore`, `.distcp`) are kept.
- ch10 Exercises: 12 items kept, each now opens with a short situation and asks one question per sentence. Each sentence was checked by eye for at most two numbers.
- ch11 Exercises: 5 items kept. ch12 Exercises: 13 items kept. Same facts and same numbers as HEAD. The number-per-sentence rule is not machine-checked.
- ch11 Key takeaways: bold lead-ins removed from the five items (one bold idea per section).
- ch11 section 1 list: bold lead-ins removed from the five items, same five components.
- ch10 Interview angles: each "Strong answer" gained one situation sentence in front. The remaining answer text is the original.
- Every H2 and H3 section now opens with a situation sentence (the first sentence under "Outcomes" is the situation in ch10, ch11, ch12).

## Needs source (added general explanations, not from the HEAD text)

ch10:
- AdamW is the optimizer most large language model runs use (Why this matters).
- Pipeline Parallelism tolerates a slower link better than Tensor Parallelism (1.2).
- Gang scheduling means all pods of a job start together or not at all; Slurm described as an open-source workload manager (2.2).
- NUMA definition: a core reaches its own socket's memory faster than the other socket's (4.1).
- Unset thread counts can oversubscribe cores per worker (4.2).
- "Handler should only set a flag or save state; the loop does the heavy work at a safe point" (5.3).
- Virtual Slurm nodes share one network stack, so they cannot show real rail behavior under load (5.2).

ch11:
- Out-of-memory killer described as the kernel's last resort that chooses a process without asking (4).
- Pinned memory locked in RAM and not swappable (already in HEAD for the fact; the swap-file consequence is added).
- Elastic agent walkthrough in 6.3 (stop surviving workers, re-form rendezvous, load latest checkpoint) needs a check against the torchrun elastic docs.
- Advice: check the kernel log before the training code when a stall happens (6.2).
- Advice on keeping a node range and restart limit with the batch in mind (6.3).

ch12:
- Perfetto is a browser-based trace viewer, so a view can be shared with a teammate (3.2).
- Advice: measure after each fix, not only at the end (2.2).
- Advice: report P50, P95 and P99 with the average (3.3). P99 is described as the slow tail users feel.
- "The method works the same way at 64 nodes" (3.2) is an inference from the 8-rank example, not a measured result.
- Analogies used: car tachometer in the mud (HEAD), relay race (3.2), phone line dialing (3.1), lecture twice for recomputation (1.2), warehouse door (ch11, section 2). No numbers introduced in any analogy.

## Unresolved

- ch10 "Common first mistakes" and "How it fails" intro: the five mistake items keep close to the HEAD wording. Only the framing sentence was added.
- ch10 Interview answers: body text is the original stiff answer, with one situation sentence added in front of each. Full reword not done.
- ch12 Key takeaways: four of five paragraphs keep HEAD wording closely. Fragments in HEAD were fixed where noted, not fully reworded.
- ch12 Exercise 6 still cites "Table 13-2", "Table 13-3" and similar labels because the original exercise did. Those labels come from a gem book (AI Systems Performance Engineering), and the chapter keeps its original attribution. Not re-checked against the book.
- ch12 Outcomes: "six common production failures" kept as HEAD says. The "How it fails" table has six rows, so the count matches.
- Math `$...$` with stray backticks: none found in the three chapters, nothing to note.
- Sources and review notes and the "corrected 2026-11-11" paragraph in ch12 are locked and were not checked for accuracy.
- EXTERNAL_EDITS.md line not added (instruction said not to edit it).
- No commits made.
