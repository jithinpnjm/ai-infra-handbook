# Voice rewrite, Part 6 chapters 6.11, 6.12, 6.13 (batch d)

Scope: docs/part-06-hpc-slurm/11-submitting-and-launching-jobs-sbatch-srun-salloc-arrays-dependencies.md, 12-multi-node-training-on-slurm-pmix-torchrun-nccl-environment-binding-to.md, 13-containers-on-slurm-enroot-and-pyxis.md. Uncommitted. Only these three files were edited. EXTERNAL_EDITS.md was not edited (lead instruction).

## Word counts (`wc -w`)

| Chapter | Before | After | Growth |
|---|---|---|---|
| 6.11 Submitting and launching jobs | 8483 | 11868 | +39.9% |
| 6.12 Multi-node training on Slurm | 7209 | 9331 | +29.4% |
| 6.13 Containers on Slurm, enroot and pyxis | 6901 | 8905 | +29.0% |

## Gates (run from the repo root, output seen)

`python3 tools/rewrite_guard.py HEAD WORKTREE <file>`:
- 11: 0 hard failures; new numbers 0; lost numbers 0; code blocks unchanged. Lost spans 1 (pairing artifact, the guard regex pairs backticks across text; checked by hand: no real span lost).
- 12: 0 hard failures; new numbers 0; lost numbers 0; code blocks unchanged. Lost spans 2 (`. In `, ` first. In `: pairing artifacts, not real spans).
- 13: 0 hard failures; new numbers 0; lost numbers 0; code blocks unchanged; residue 3 to 0. Lost spans 3 (pairing artifacts; `For NGC, the URI is `nvcr.io#nvidia/pytorch:TAG`` is still present).

`python3 tools/restore/chain_gate.py <file>`:
- 11: 0.2 per 1000 words
- 12: 0.5 per 1000 words (the remaining hits are inside original table cells, kept verbatim as data)
- 13: 0.0 per 1000 words

`node tools/check_mermaid.mjs` and `npm run build`: not run, per the lead's instruction ("No npm build or full Mermaid").

## What changed

- Every section opens with a situation: a job that waits silently on a node, a second `srun` that hangs, a researcher whose log is empty, a 64-node job that hits the registry at once, a Monday after a Slurm upgrade.
- The outcomes lists ("By the end of this chapter, you can ...") became one plain paragraph per chapter. The heading "Prerequisites and outcomes" is kept.
- Lab (6.12 and 6.11): 6.12 had its lab as a paragraph. It is now a numbered list of the same ten steps, with the same commands. 6.11 lab steps 1 to 8 keep their commands and counts, with one situation per sentence.
- Exercises: 6.11 six, 6.12 six, 6.13 six. Counts and commands unchanged. Multi-part items split so each sentence has one question and at most two numbers.
- Honest status: each status row keeps its original text (including the **untested** marker). One plain sentence sits above each lab. 6.11: the cluster steps were not run. 6.12: the laptop steps were run and the cluster steps were not run on live hardware. 6.13: the Python checks were run on a workstation, and the enroot and pyxis steps were not run on a live cluster.
- "(untested here)" removed from reader text in these three chapters. Sources and review notes were not touched, so the Sources sections still carry their original "untested here" wording (out of scope, see Unresolved).
- Bold: at most one bold idea per prose section. 6.12 section 2 lost three of its four bold labels; one bold idea (srun-per-GPU) remains.
- "The book" sentences in 6.13 now name the source by its full title, *Supercomputers for Linux SysAdmins*. The attribution itself is kept from the original text.
- No checkpoint question or answer was changed. No Sources section was changed. Front matter, headings and Mermaid blocks are unchanged.

## Needs source check (explanation added, not in the original text)

6.11:
- SPANK plugin described as an add-on that adds flags to `sbatch`/`srun`. Original named the mechanism; the plain description is ours.
- QoS described as "a quality-of-service policy that sets limits and priorities for a class of jobs or users".
- Prolog described as "a script the administrator runs before user code starts"; Epilog as "the mirror image of the Prolog".
- Draining described as "the node stops taking new work until someone checks it".
- Backfill described as slipping short jobs into gaps.
- Fair-share described as "giving less priority to users who have already used more than their share".
- `0:15` read as "stopped by signal 15, which is SIGTERM".
- `--time-min` described as giving the scheduler more room to fit the job.
- Collective described as "an operation where every rank must take part, such as an all-reduce".

6.12:
- NVLink, InfiniBand, RoCE and RDMA defined in plain words in the prerequisites.
- NCCL unique id described as "a small token that every rank needs before NCCL can build its communication rings".
- NUMA, HGX ("NVIDIA's reference server board for eight GPUs") and "rail-optimised" described.
- Tensor parallelism and pipeline parallelism described (which dimension each splits).
- DDP and FSDP described (all-gather, reduce-scatter, sharding); `find_unused_parameters` cost described.
- Pinned memory described as host memory the GPU copies from directly.
- Ring buffer described as a fixed-size log that overwrites its oldest entries.
- `nvidia_peermem` described as "the GPU memory module for RDMA".
- Claim that a blocked port "can leave the other nodes waiting with no clear error" (plausible, not sourced).
- Claim that a 1-element round trip divides by 200 messages (follows from the original formula).

6.13:
- Capabilities described as "the fine-grained root powers that Linux splits into separate permissions".
- netrc described as a plain-text host/login/password file format.
- Thundering herd and rate limit described.
- Manifest described as the index file listing an image's layers; caching it too long can serve an old version under a moved tag.
- Digest versus `:latest` explained.
- MOFED described as Mellanox's InfiniBand software stack.
- `ENROOT_MAX_PROCESSORS` trade-off (more threads, more CPU taken from the node).
- Charliecloud "auditability" explained as the runtime being small enough for a security team to read.
- "*Supercomputers for Linux SysAdmins* takes the view that in 2025 you almost cannot use Docker directly in HPC" and "calls this inefficient" and "calls this technology really easy to use": attributions kept from the original. Confirm against chapter 16 before publishing.
- The sentence "The ease of use ... comes from a tight fit with one vendor's hardware" is our interpretation.

## Unresolved

1. 6.11 checkpoint 20 (untouched, per rule 5) lists `--mem-per-cpu` among the mutually exclusive memory flags, but the linter output in section 9 reports only `--mem, --mem-per-gpu`. Not fixed here; checkpoint text is off limits for this run.
2. The Sources and review notes sections in all three chapters still contain the original drafting words ("untested here", "Run here", "W4 rework 2026-11-12" in 6.12). They were out of scope for this run and were not touched.
3. 6.12 section 5 and 7 keep their original data tables. Those tables carry the dense cell text that drives the 0.5 chain-gate hit; leave them as data.
4. 6.12 section 8.2 and 8.3 kept the original numbered-list form with one bold item each.
5. The Mermaid block in 6.11 and 6.12 is unchanged. Mermaid was not rendered (see Gates).
6. 6.13 lab steps: the step list was already numbered; the wording was tightened, the commands are unchanged.
7. Growth in 6.11 is +39.9 percent, at the top of the allowed range. Any further edit should not add more prose to this file.
