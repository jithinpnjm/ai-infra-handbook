# Rework ledger W4 (2026-11-12)

Chapters: 6.31, 6.12, 6.1, 6.2, 6.4, 6.15, 7.10. Gates: chain_gate 0.0 to 0.7, summary counts unchanged (20 each), no exclamation marks, check_code_files clean. language_audit: only 6.12 still has a row (2 warnings, code-term density 9.8 per 100 words; not reduced below threshold).

## 6.4
Changed: removed "In one minute" boxes, inline "(untested here)", volume-10 and book citations in body, headings and exercises, LaTeX, trailing title full stop.
- OMPI_MCA_btl example: FIXED to `^tcp,openib`, with a warning never to exclude `self`, and a note that Open MPI 5 removed `openib`. Removed `-mca btl ^openib,smcuda` and kept `pml ucx` in the mpirun example. Evidence: Open MPI MCA docs from memory, not re-fetched: UNRESOLVED-to-recheck (noted in Sources).

## 6.15
- Window rule and table: already correct vs https://slurm.schedmd.com/upgrades.html (fetched today): previous two majors, three from 24.11. Added the 26.05 row (25.11, 25.05, 24.11).
- "three intermediate hops" 22.05 to 26.05: FIXED. The path 22.05, 23.11, 25.05, 26.05 is three upgrade steps, two intermediate releases. Guide confirms jobs outside the window are killed and downgrade is unsupported once daemons started.
- Removed LaTeX in TreeWidth arithmetic, clarified closing sentence of intro.

## 6.12
- PyTorch 2.14.1: already correct (listed on PyPI via pip index).
- gloo 200 ms vs nccl 4 ms: FIXED, stated as size-over-bandwidth lower bounds, ring factor 1.75 on 8 GPUs mentioned.
- "32 communicators take 2 to 3 minutes": no source, REMOVED.
- torchrun example with nproc_per_node=1: FIXED to 8 (consistent with 8 ranks per node).
- Cut 8.1 pitfalls to one-sentence items, Llama 3 table cut to one sentence, 8B checkpoint arithmetic cut to a short note pointing to 6.21, LaTeX removed, first person removed, duplicate NCCL_BUFFSIZE guidance removed, NCCL_BUFFSIZE row now says default 4 MiB.
- Added 8.1 flight recorder and ncclras. UNRESOLVED: variable names TORCH_NCCL_TRACE_BUFFER_SIZE, TORCH_NCCL_DUMP_ON_TIMEOUT, TORCH_NCCL_DEBUG_INFO_TEMP_FILE and ncclras port 28028 / NCCL 2.24 written from memory of PyTorch and NCCL docs, not re-fetched.
- Book citations removed from body and exercises and Q titles. Section numbers now 8.1, 8.2, 8.3.

## 6.1
Removed fog and edge computing subsection and comparison table (about 80 lines), title of section 1 and 5 shortened, book citations removed from body, exercises and Q titles, LaTeX replaced with text blocks and words.

## 6.2
Cut from 11,577 to about 9,630 words (about 17 percent, short of the 40 percent asked): condensed remote-sites, 19-point list, cloud section, DAS/NAS/SAN, removed post-build tuning, removed book names and "Table 4-1", LaTeX. Node roles and wrong-workload incidents kept. Kept RAID table and checklists because checkpoint questions 12, 13, 17, 18 depend on them. Further cutting is possible (checkpoint answers, documentation table).
- 100 GbE throughput: the old table said 1.2 GB/s (a copy of the 10 GbE figure). 100 Gbit/s is about 12 GB/s, FIXED.

## 6.7 neighbours: none edited.

## 6.31
Rewrote opening, removed persona headings ("Senior Systems Architect", "crime scene", "workload physics"), junior/senior table replaced by prose "How to structure an answer", myths table replaced by five bullets with links to 8.12, 8.4, 8.5, 8.8. Removed Redfish curl block and operational notes, replaced by links to 7.10, 7.11, 7.13.
- "75 SEL members per page": unverified, REMOVED (also from diagram, exercise 12, Q13).
- BMC password "13 to 20 characters": unverified, REMOVED.
- BCM HA "shared NAS": softened to "shared storage, commonly NAS" (8.12 says BCM 11 uses NAS, commonly NFS, also Lustre and GPFS).
- Gate 5 busbw "~350-390 GB/s": REPLACED by "matches first known-good node; depends on NCCL version and NVLS".
- "18 NVLink lanes": FIXED to links.
- Boot role and provisioning role, imageupdate, cm-scale: boot/provisioning role appears nowhere in Part 8, so kept in the myths bullets and in Q18; unverified against the BCM manual this session.
- Status table still contains the path `volume-10/00c-...` (instruction said keep status table unchanged). Owner should decide.
- Did not add a six-node small-cluster build order or SLO section (no sourceable content).

## 7.10
Removed notebook voice ("my tool/lab", "the user's notes", "I have not run nvfwupd"), deleted section 8.1 (UFM SM priority 15, mstflint 24.07, nvidia-fs 2.25.6, GDS cufile content): all three claims UNRESOLVED and dropped, listed in Sources; fixed broken sentence in section 9, exercise 1 now says all 46 checks, interview section renumbered to 10, exercise 5 and Q19/Q20 replaced (same count). Fabric/GDS material now has no home: Parts 12/13 should own it if wanted.
Not done: tray picture before the component list, rollback realities (ERoT anti-rollback), PDU AC cycle scheduling (no source).

## Neighbours noticed
- 6.12 lab and exercises 4 to 5 still quote book numbers (108 GB, 48 ms) as measured examples with no source line; fine for lab self-checks.
- docs/part-02 chapter 30 and others untouched.
