# Voice rewrite, Part 6 chapters 6.5, 6.6, 6.7 (batch c)

Scope: docs/part-06-hpc-slurm/05-openmp-compilers-and-optimisation-flags.md, 06-environment-modules-spack-and-easybuild.md, 07-slurm-architecture-and-installation.md. Uncommitted. Other Part 6 files (01 to 04) were not touched by this run. The EXTERNAL_EDITS.md step was skipped on the lead's instruction.

## Word counts (`wc -w`)

| Chapter | Before | After | Growth |
|---|---|---|---|
| 6.5 OpenMP, compilers and optimisation flags | 8040 | 10063 | +25.1% |
| 6.6 Environment modules, Spack and EasyBuild | 7007 | 8764 | +25.1% |
| 6.7 Slurm architecture and installation | 12418 | 15537 | +25.1% |

## Gates (run from the repo root, output seen)

`python3 tools/rewrite_guard.py HEAD WORKTREE <file>`:
- 05: 0 hard failures; new numbers 0; lost numbers 0; new code spans 0; lost code spans 0.
- 06: 0 hard failures; new numbers 0; lost numbers 0; new code spans 0; lost code spans 0.
- 07: 0 hard failures; new numbers 0; lost numbers 0; new code spans 0; lost code spans 0.

`python3 tools/restore/chain_gate.py <file>`:
- 05: 0.0 per 1000 words (9801 words)
- 06: 0.0 per 1000 words (8277 words)
- 07: 0.1 per 1000 words (14642 words)

Fence count (```` ``` ````) unchanged in each file (05: 19 blocks, 06: 26, 07: 36 as in HEAD). Checkpoint blocks, Sources sections, front matter, tables with numbers, and Mermaid blocks are unchanged.

`node tools/check_mermaid.mjs` and `npm run build`: not run, per the lead's instruction ("No npm build or full Mermaid").

## What changed

- Every section opens with a situation: an overnight training slowdown, a shared cluster with fifty researchers, a controller that dies mid-run, a user who runs the wrong `mpirun`, a new node that drains, a first install where the controller starts before the database.
- The outcomes lists ("By the end of this chapter, you will be able to") became one plain paragraph in each chapter.
- Exercise and checkpoint-adjacent lists: exercise counts unchanged (05: 6, 06: 6, 07: 6). Each exercise now has one question per sentence. The interview-angle lists keep their five items, with a short lead sentence.
- Lab steps keep their commands and counts. Lab sentences were rewritten to say what each step checks.
- Honest status: the status row keeps **untested**. One plain sentence above the lab in each chapter says the labs were not run on a live cluster (05 says the multi-node Slurm scripts were not run; 06 says the module swap and Spack parser were not run on a live software tree; 07 says the three VM labs were not run on a live cluster).
- Removed "(untested here)" from reader text in prose. Kept the code comment `# (untested here)` inside the bash block in 05 (CUDA reinit) and in 06 (EasyBuild venv step), because the guard blocks code edits. Those two comments remain as drafting residue. See Unresolved.
- Bold labels on daemon names, plugin families and similar points were removed in 07 to keep one bold idea per section.

## Needs source check (added explanation, not in the original text)

- 05: "FP64 means 64-bit floating point, a high-precision format" (plain definition).
- 05: "SIMD stands for single instruction, multiple data" (standard expansion).
- 05: the cache-line explanation of coherency bouncing and "coherence-locks whole cache lines" wording is original; the sentence "A cache line is the unit of memory that moves between RAM and the cache" is new plain explanation.
- 06: "Those two lines let MPI pin enough memory for fast transfers." (explains `memlock unlimited`; general knowledge, not from the source).
- 06: "A shallow clone copies only the latest history" (explains `--depth=2`).
- 06: "Spack starts from a spec ... solves for the rest" (general description of Spack; original cites the Spack docs for concepts).
- 07: "SPANK (the Slurm plug-in architecture for the job launch path)". The acronym expansion is ours. Check the expansion against the SchedMD SPANK page before publishing.
- 07: "PAM (Pluggable Authentication Modules, the Linux login gatekeeper)" (plain definition).
- 07: "gang scheduling, which starts all the pieces of a job together or not at all" (plain definition).
- 07: the fire-drill picture of `slurmstepd`/launch and the "second pilot" picture of the backup controller are analogies. They carry no numbers and no facts beyond the original text.

## Unresolved

1. Code comments `# (untested here)` remain inside code blocks in 05 (CUDA reinit, `rmmod nvidia`) and 06 (EasyBuild venv step). Changing them breaks the rule that code blocks must not change. Fix in a follow-up that allows a comment-only change.
2. 06 and 07 keep the original Sources-section and checkpoint text that contains "(untested here)" as an inline label. Those sections were out of scope and were not touched.
3. Lab items in 07 (Lab A steps 1 to 8) were kept as original text, including the step wording and code. Their prose was not voice-rewritten beyond the lab intro and the lab headings. A later pass can bring the lab steps to rule 9 wording (one question per sentence).
4. Checkpoint questions and answers were not changed in any of the three chapters (rule 5). The answers are the next place where the warm tone could be carried further.
5. The original "untested" wording in 06 and 07 status rows is kept on purpose (status row). No other "untested" remains in prose.
6. Growth was reached by adding explanation paragraphs and rewriting prose. The new text adds no digits, flags, or versions beyond the original.
