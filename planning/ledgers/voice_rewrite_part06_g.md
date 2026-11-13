# Voice rewrite, Part 6 chapters 6.17, 6.18, 6.19 (batch g)

Scope: `docs/part-06-hpc-slurm/17-other-schedulers-pbs-torque-lsf-and-flux.md`, `18-parallel-storage-concepts-and-the-limits-of-nfs.md`, `19-lustre-architecture-and-operation.md`. Uncommitted. Only these three files were edited. `planning/EXTERNAL_EDITS.md` was not edited (lead instruction, step 6 of the rewrite procedure skipped). Front matter, headings, Mermaid, all code blocks, all tables, the Sources and review notes sections and the checkpoint questions and answers are byte-identical to HEAD. Headings and the checkpoint section were checked with `diff`.

## Word counts (`wc -w`)

| Chapter | Before | After | Growth |
|---|---|---|---|
| 6.17 Other schedulers | 7087 | 9058 | +27.8% |
| 6.18 Parallel storage and NFS | 7723 | 9787 | +26.7% |
| 6.19 Lustre architecture | 8668 | 11013 | +27.1% |

Guard word column (prose only): 6.17 6506 to 8477 (+30.3%), 6.18 7444 to 9508 (+27.7%), 6.19 7935 to 10280 (+29.6%).

## Gates (run from the repo root, output seen)

`python3 tools/rewrite_guard.py HEAD WORKTREE <file>`:
- 17: ok, 0 hard failures; new numbers 0; lost numbers 0; new code spans 7; lost spans 2; residue 6 to 0.
- 18: ok, 0 hard failures; new numbers 0; lost numbers 0; new code spans 0; lost spans 0; residue 14 to 2.
- 19: ok, 0 hard failures; new numbers 0; lost numbers 0; new code spans 2; lost spans 3; residue 17 to 4.

Lost spans, checked by hand (`/private/tmp/.../scratchpad/spancheck.py`):
- 17: ` chunks are emitted as ` is a backtick pairing artifact. `(untested here)` in prose was removed on purpose. The three exercise-2 spans (`max_user_run = 12`, `resources_max.ncpus = 20`, `resources_max.walltime = 336:00:00`) were restored exactly.
- 19: ` removes limits. The book's commands are (` and ` sets up the project. The book also adjusts the grace times to ` are pairing artifacts between real spans. `(untested here)` in prose was removed on purpose. The real spans `lfs project -r /lustre/testdir` and `1d8h` are intact.
- 18: none.

New code spans (typed or seen on screen, all from the original text or from explanations of it): 17 `# TODO`, `#PBS -N bert`, `--partition=gpuq`, `-q gpuq`, `gpu`, `gpuq`; 19 `--print0`.

`python3 tools/restore/chain_gate.py <file>`:
- 17: 0.5 per 1000 words (target 0.2 or lower, limit 1.5: pass).
- 18: 0.1 per 1000 words.
- 19: 0.2 per 1000 words.

`node tools/check_mermaid.mjs` and `npm run build`: NOT RUN (lead instruction: "No npm build or full Mermaid"). The Mermaid blocks are byte-identical to HEAD, so no Mermaid change was made.

## Rule self-check

- Every section opens with a situation (a stalled queue, a 4,096-GPU checkpoint, a "storage is slow" ticket, a teammate's folder of PBS scripts, and so on).
- No "you will be able to" or "by the end" lines. The outcomes lists in the Prerequisites section became plain paragraphs. A grep for `you will be able|should be able|By the end` finds only the heading "Arithmetic you should be able to do", which is heading text that rule 5 keeps.
- Exercises: 17 six, 18 fifteen, 19 six. Lab steps: 17 six, 18 seven, 19 nine. Counts and commands are unchanged. Multi-part items were split into one-question sentences.
- Honest status, once per chapter, above or inside the lab:
  - 17: "The converter part of this lab was run on a laptop. The live scheduler steps that follow have not been run on a live cluster." (The status row also keeps "labs **untested**".)
  - 18: "The first two tasks run on one machine. The last five need two or three VMs, and this chapter did not test them." (original sentence kept)
  - 19: "The Python model in this section was run on a laptop. The Lustre steps after it have not been run, because they need a test cluster."
- No exclamation marks in prose. No raw `<` or `{` outside code spans or code blocks (checked by script; the only raw braces are inside the original `$...$` math in the 6.19 exercise 2, which is kept as-is).
- Bold count per chapter unchanged from HEAD (17: 2, 18: 9, 19: 11, all inside tables or original labels).
- "the book" in prose replaced by the full title *Supercomputers for Linux SysAdmins* (rule 12). The gem book is never abbreviated.

## Needs source (explanations added, not in the original text)

6.17:
- Expansions: PBS = Portable Batch System; EDA = electronic design automation; LLNL = Lawrence Livermore National Laboratory.
- Definitions: fair-share, backfill, NUMA, job slot, LSF licence-aware scheduling, Flux broker, `&&` as the shell "and then, if that succeeded" operator.
- Torque `$ideal_load` and `$max_load` described as limits on how loaded a node may get before it stops taking work (general knowledge).
- Cloud bursting described as adding cloud machines when the local cluster is full. Kubernetes-to-Slurm bridges described as virtual kubelets that hand pods to a batch queue.
- Inference: a converter that copied `ncpus` straight across would request 64 CPUs per task and would not fit on the node.
- Migration advice (wrapper compatibility, one full allocation cycle, accounting continuity) is advice, not a sourced fact.

6.18:
- Expansions and definitions: RPC, NAS head, HA, NSD, PTP, Munge, CIDR, jumbo frames, page cache, fsync, stale file handle, failure domain, burst buffer, erasure coding, IO500, Adam (optimiser), token, failure domain.
- IBM Storage Scale described as the renamed GPFS (general knowledge).
- Stateless NFSv3 server described as simple to restart (general knowledge).
- chrony "private clock" explanation (inference from the `allow` directive).
- Two-rank boundary alignment example (inference from the N-to-1 row of the table).

6.19:
- RAID-10 described as mirror plus stripe, and RAID-6 as surviving two disk failures (general knowledge).
- Definitions: NVMe-oF, JBOD, MTU, statahead, RAID-Z, vdev, inode, LND, NRS and TBF (named in the original, explained here), quota soft versus hard limit and grace period, `--print0`.
- Pools "typical use" (flash for a hot dataset, disk for the archive) is an example, not a sourced fact.
- PFL reason for the larger stripe size in the last component (inference).
- Failover event timeline in section 1 is the usual recovery sequence (general knowledge; the original names the parts but not the order).
- Changing a NID on a running target can leave clients on a dead address (inference).
- Per-team directory tree advice in DNE paragraph is advice, not a sourced fact.

## Unresolved

1. Headings keep their original drafting text, because rule 5 forbids heading changes: 18 `### NFS server and mount essentials (general practice, untested here)`; 19 `### Non-HA install order from the book`, 18 `### Minimal NFS server and client steps from the book`; 17 `## 3. IBM Spectrum LSF (general knowledge, unverified)` and `## 9. Lab (... untested)`.
2. `(untested here)` remains in code-block comments (17 about 6 hits, 18 about 4, 19 about 10, counting headings and Sources too). Code blocks are frozen by the guard. A later code pass could move the honest note into the surrounding text.
3. The Sources and review notes sections of all three chapters are unchanged. They still carry "untested here", "Run here" and the NVIDIA-DevOps `volume-15` path, which is a source reference, not reader text.
4. Status rows are unchanged. The 6.19 status row still names "NVIDIA-DevOps volume-15 chapter".
5. Checkpoint sections are unchanged (rule 5). The 6.19 checkpoint answer 3 still says "The book recommends RAID-10 for MDTs", and other checkpoint answers use "the book" wording.
6. Possible fact conflict noticed, not changed: 6.17 prose says the original OpenPBS came from MRJ in 1998 (kept). The Part 6 ledger `planning/ledgers/6-17.md` lists "1991 NASA/MRJ". Check against the book before publishing.
7. 6.19 exercise 4 keeps `oss_ram_sizing_mb(8, 640, 32)` with the original `N_threads = 640 / 32 = 20` wording. The argument meaning was not re-derived.
8. Not run: `node tools/check_mermaid.mjs`, `npm run build`, `python3 tools/language_audit.py`. Per lead instruction the build and full Mermaid check were skipped.
