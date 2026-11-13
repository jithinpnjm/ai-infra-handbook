# Voice rewrite, Part 6 chapters 6.2, 6.3, 6.4 (batch b)

Scope: the three files below only. Uncommitted. Chapters 6.1, 6.5 and 6.6 were not touched by this run.

- docs/part-06-hpc-slurm/02-cluster-anatomy-head-login-compute-storage-and-management-nodes.md
- docs/part-06-hpc-slurm/03-parallel-computing-concepts-amdahl-scaling-shared-memory-versus-messag.md
- docs/part-06-hpc-slurm/04-mpi-in-practice-open-mpi-ranks-collectives-and-tuning.md

Method: prose rewritten section by section. Front matter, headings, every table, every fenced code block (including Mermaid), the 20-question checkpoint block and the Sources and review notes section were carried over byte for byte from HEAD. Rule 5 keeps the checkpoints and Sources unchanged.

## Words (wc)

| Chapter | Before | After | Growth |
|---|---|---|---|
| 6.2 | 9708 | 12366 | +27.4 percent |
| 6.3 | 9412 | 12136 | +28.9 percent |
| 6.4 | 8806 | 11164 | +26.8 percent |

## Gates (run, output seen)

6.2
- `python3 tools/rewrite_guard.py HEAD WORKTREE <6.2 file>`: 1 chapters, 0 with hard failures. words 9548 -> 12206. new numbers 0, lost numbers 0, new code spans 0, lost 0
- `python3 tools/restore/chain_gate.py <6.2 file>`: 0.0 per 1000 words (12287 words)

6.3
- guard: 1 chapters, 0 with hard failures. words 8929 -> 11653. new numbers 0, lost numbers 0, new code spans 0, lost 0
- chain gate: 0.2 per 1000 words (11728 words)

6.4
- guard: 1 chapters, 0 with hard failures. words 8457 -> 10815. new numbers 0, lost numbers 0, new code spans 0, lost 0
- chain gate: 0.0 per 1000 words (10886 words)

Not run: `node tools/check_mermaid.mjs` and `npm run build`. The task brief said no npm build and no full Mermaid, so the Mermaid blocks are unchanged from HEAD (byte-identical) and nothing was rendered.

## Self-check

- No "you will be able to", "by the end", or "in this chapter you will learn" lines. The 6.2 outcomes bullet list became a plain paragraph of what the chapter walks through.
- Every section opens with a situation (a Monday-morning request, a night-time incident, a vendor quote, a Friday job that hangs, and so on). Situations use no new numbers.
- Exercises: 6 in 6.2, 6 in 6.3, 6 in 6.4 (same counts as HEAD). Each exercise keeps the same functions, commands and numbers. Lab steps: 3 in 6.2, 3 in 6.3, 3 in 6.4, same commands.
- Interview angles: 5 per chapter, kept as questions.
- No exclamation marks in prose (the one "!" in 6.3 is the code span `!$omp`). No raw `<` or `{` in prose.
- Honest status: the status row keeps "untested" in 6.2 and 6.3 and "have not been tested" in 6.4. Each chapter has one plain sentence above its lab ("not run on a live cluster" or "were not run on a live cluster"). Prose residue "(untested here)" was removed.
- Last section checked: the Sources and review notes section ends each file, and the file ends with it.

## Needs source (explanations added by this run, not in HEAD)

6.2
- PXE is a network boot method, described as "boot over the network without a local operating system". General explanation.
- UPS and PDU definitions in section 1.
- `pam_slurm_adopt` behavior, described as letting a user in only on a node where that user has a running job. Check against the Slurm PAM documentation.
- Ownership paragraph in section 1 (facilities team owns layer 1, vendor installs layer 2). General practice, not from the book.
- Time-drift paragraph in section 6 ("the scheduler makes odd decisions"). General explanation.
- Two-factor authentication parenthetical, LDAP parenthetical, the NAT and firewall sizing sentence, and the front-desk office analogy.

6.3
- One-sided communication definition in PGAS paragraph ("does not need the other side to post a matching call").
- Cache coherence definition in the OpenMP-across-nodes paragraph.
- Most AI training questions are weak-scaling questions (section 3). Judgment, not sourced.
- "Latency is the toll, bandwidth is the road" analogy and the message-size example in section 8.
- Relay-team analogy (section 6), and the weather-model block example (section 9).
- Claim that a slow node makes the whole pool look like a dashboard efficiency loss (section 6). General.
- Statement that a misleading speedup usually comes from a single-worker parallel baseline. The mechanism is from the chapter; the "usually" is judgment.

6.4
- Exit-code arithmetic (128 plus the signal number). This is the standard shell convention. It is not stated in HEAD and should be checked against the shell documentation if it is used in teaching material.
- "Check this line first when a fast cluster feels slow" (NCCL Socket fallback). Recommendation, not sourced. The fact that Socket is slower than InfiniBand is general.
- "A missing process on one node points to the launcher" and "keep collective calls unconditional" (general MPI practice).
- Rendezvous explanation ("both sides wait for each other") and the bounce-buffer description are general MPI behavior. HEAD states the same mechanism.

## Unresolved

1. Code-block comments still say "(untested here)": 6.3 `SLmake.inc` comment, 6.3 PETSc bash comment, 6.4 HCOLL and UCX bash comments. Code blocks are guarded as verbatim, so they were left alone. Fix in a follow-up that allows code-comment edits (same as the 6.1 note).
2. Sources and review notes kept byte for byte, including the "(`untested here`)" and "untested" wording in the 6.2 and 6.3 Sources sections, because rule 5 names that section as unchanged.
3. Checkpoint blocks kept byte for byte (form and count). They were not voice-rewritten.
4. Several long bullets and "In one minute" blocks keep their original semicolon-heavy wording, especially 6.4 section 10 Layer 4. A later pass could split them.
5. Growth is +26.8 to +28.9 percent by wc, above the +25 percent floor. The 6.4 margin is the smallest.
6. Mermaid and `npm run build` not run, per the brief.
