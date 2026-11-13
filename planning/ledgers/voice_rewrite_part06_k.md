# Voice rewrite, Part 6 chapters 6.29, 6.30, 6.31 (batch k)

Scope: the three files below only. Uncommitted. `planning/EXTERNAL_EDITS.md` was NOT edited (owner instruction overrides step 6 of the rulebook). Other part-06 chapters and other ledgers were not touched.

- docs/part-06-hpc-slurm/29-containers-and-reproducibility-in-hpc-apptainer-and-enroot.md
- docs/part-06-hpc-slurm/30-facility-basics-power-cooling-racks-and-liquid-cooling.md
- docs/part-06-hpc-slurm/31-capstone-build-and-operate-a-small-slurm-gpu-cluster.md

## Words (wc -w, before to after)

| File | Before | After | Growth |
|---|---|---|---|
| 29 Containers, Apptainer, enroot | 7636 | 10819 | +41.7% |
| 30 Facility basics | 7650 | 10083 | +31.8% |
| 31 Capstone | 8760 | 11540 | +31.7% |

Guard prose counts: 29 7258 to 10441 (+43.9%), 30 7327 to 9760 (+33.2%), 31 8132 to 10912 (+34.2%).

29 is above the +40% band. The cause is the locked duplicate `## Exercises` heading and block (see Unresolved). Nothing was added to pad it; the extra words are the lab walkthroughs and the expanded explanations.

## Gates (run after the last edit)

| Gate | Result |
|---|---|
| `tools/rewrite_guard.py HEAD WORKTREE <file>` (each file) | 29: 0 hard, new numbers 0, lost numbers 0, lost code spans 0. 30: 0 hard, new numbers 0, lost 0, lost spans 0. 31: 0 hard, new numbers 0, lost numbers 0, lost spans 0. Front matter, code blocks, checkpoint summary count (20 each), Mermaid, H2 headings unchanged. Residue 3 to 0, 1 to 0, 1 to 0 |
| `tools/restore/chain_gate.py <file>` | 29: 0.0; 30: 0.0; 31: 0.0 (target 0.2 or lower, met) |
| Checkpoint block and Sources block | byte-identical to HEAD in all three files |
| Mermaid blocks | byte-identical to HEAD. `node tools/check_mermaid.mjs` NOT RUN (brief said no full Mermaid) |
| `npm run build` | NOT RUN (brief said no npm build) |

Code spans: no inline code span from the original was lost in the final state. New spans added: `-E`, `inspect`, `old.sif` (29), `PartitionName` (31). These are commands or names taken from the chapter text.

Numbers: no new numeric token in the final state. A section cross-reference "4.2" that the guard flagged in 30 was reworded to "the room conditions listed earlier in this section". Every number in the new text already existed in the original.

## What changed, by rule

- Each section now opens with a situation (a job that stalls, a rack that trips, a cooling alarm on a weekend, a whiteboard, a pallet on a dock).
- Outcome lists ("By the end, you will be able to") became a short paragraph in all three files.
- Residue removed from reader text: "The book describes", "This book notes", "the books' planning numbers", "volume-10" in the 31 status row. Gem books are named in full (*Supercomputers for Linux SysAdmins*, *AI Data Center Network Design and Technologies*, *AI Factory*).
- Honest "not run" status: 29 status row and the sentence above the lab; 30 status row and a sentence at the top of the exercises ("Nothing in these steps was run on a live facility."); 31 status row and a sentence above the exercises.
- Exercises (29: 6 items, 30: 6 items, 31: 13 items): one situation each, one question per sentence, same commands and same numbers.
- 29 lab (9 items): same commands; each item gained a plain "why" sentence. The tested and not-run split is kept.
- 31 lab: the ten pipeline stages (3.2) each have a plain-language walkthrough paragraph after the table; the 3.3 config details and the 3.4 PASS lines are explained; drills 1 and 2 get a walkthrough; the 6.x scenarios each open with an interview situation. No command was changed.
- Acronyms spelled out at first use where new text needed them (cgroups, libc, PMI, ABI, CDI, CFM, RDMA, DAC, AOC, NDR, DCGM, BMC, SNMP, CFD, STONITH, NAS, OST, MDS, PMIx, UFM, SuperPOD, SU, OCI, SPANK, GRES, QOS, NHC, HPL, IOR).

## Needs source (general knowledge added as explanation, no numbers, no attribution)

- 29: definitions of CUDA, cuDNN, NCCL, MPI, OCI, libc, ABI, PMI, hooks and SPANK, the page cache, garbage collection, cron, prolog and epilog, parallel file systems (Lustre, GPFS), node-local NVMe, the mount-as-view explanation.
- 30: definitions of SNMP, CFD, anemometer, heat sink, DAC and AOC cable construction, PSU and power shelf, the purpose of an ASHRAE class, MERV rating, the Uptime Institute tier names are original text and are not new.
- 31: definitions of STONITH, NAS, quorum, heartbeat link, gang scheduling, fat-tree, oversubscription, rail, boot storm, D state, OST and MDS, Xid and SXid, ECC and GSP, p99, feature gate and alpha, the floor() rounding explanation, the ring and canary rollout explanation, what a golden image is.

## Unresolved (owner or Claude to decide)

1. 29 duplicate `## Exercises` heading and identical block. Both headings are locked by the rulebook, so both are kept and rewritten the same way. The owner may want one removed. This is also why 29 is at +41.7%.
2. 29 original claim, kept as written: "Almost every line in a Dockerfile creates a new squashfs layer." Docker layers are not usually squashfs, so this may be wrong. It was not changed because facts must stay exact. Needs a source check.
3. 31 status row says "Validated" (the laptop harness passed end to end) and the acceptance gates were not run on hardware. Both are stated. Kept as the original status.
4. 31 Sources item 1 names `volume-10/00c-slurm-bcm-interview-lab.md`. Sources is locked, so it stays. It is the only "Volume" residue left in the three files and it is outside reader text.
5. 31 checkpoint answers and 6.1 facts were kept verbatim; not re-verified against the vendor documents in this run.
6. 29 and 30 changed on disk after my first write, during this run. I took the current state and did not revert it. The exercise blocks and lab items were rewritten on top of that state by heading and exact-line match. If those edits were in the exercise or lab areas, they were overwritten. Please check with the owner.
7. Mermaid check and `npm run build` were not run (brief said no full Mermaid and no npm build).
