# Voice rewrite, Part 6 chapter 6.1 (batch l)

Scope: docs/part-06-hpc-slurm/01-what-a-supercomputer-is-top500-linpack-hpc-versus-ai-factory.md only. Uncommitted. The owner's step 6 (EXTERNAL_EDITS.md) was not done, per the run instructions.

## Gates (run, output seen)

| Gate | Result |
|---|---|
| `python3 tools/rewrite_guard.py 43d879a~1 WORKTREE <file>` | 0 hard failures; words 9049 to 12567 (guard count); new numbers 0; lost numbers 0; new code spans 0; lost code spans 0; residue 0 to 0 |
| `python3 tools/restore/chain_gate.py <file>` | 0.1 per 1000 words (target 0.2 or lower; limit 1.5) |
| `wc -w` | 9363 original, 12881 now: +37.6 percent (owner's bar +28 percent, about 11,985 words) |
| Code blocks, table lines, checkpoints, Sources, H2 headings | identical to HEAD (checked by script: 9 code blocks, 61 table lines, 20 `<details>`) |

Note on the word bar: the owner's brief says "+28 percent (about 11,600+ wc words)". 9363 times 1.28 is 11,985, so the brief's parenthetical number is inconsistent with its percentage. This run meets the percentage (and the parenthetical).

## What changed

- Sections 2 to 9: deepened with situations, walkthroughs, analogies (jeweler and warehouse scales, highway lanes, delivery-van test drive, DevOps versus training job, war-room "the cluster is down", kitchen cooks, assembly-line car). Analogies carry no numbers.
- Section 1 kept, with one added orchestra case (afternoon fan failure) and a plain definition of MPI.
- "Prerequisites and outcomes": the self-check list ("you should now be able to") was replaced by one plain paragraph. The heading text is unchanged.
- Section 5: the Cloud/Fog/Edge paragraph was removed (see Needs source).
- Section 9 lab steps and Exercises 1 to 6: same count, same commands, same facts. Long items split into one question per sentence. Exercise 4 now ends on the multi-node LLM pre-training question (supported by the table in section 5) instead of the fog and edge question.
- Lab step 4: "(not run here)" removed. The one honest status in reader text is the status row ("**untested** here") plus the sentence above the lab ("have not been run on a live cluster").
- Section 5 "When people say cluster" and sections 7, 8 and 9 now open with a situation.
- Inline code spans restored: the eight lost spans were from the pipeline paragraphs (`K`, `S`, `1 × (100 - 1) + 5`). Original sentences were restored in "Now the arithmetic", "Read the formula in two parts", and "Inside a processor". Guard reports 0 lost.
- Checkpoint questions and answers: unchanged (rule 5).

## Needs source

- Section 5, Cloud/Fog/Edge paragraph: the earlier draft said fog and edge sites handle low-latency inference and attributed the tier description to *AI Factory*. The original text had no such paragraph, and the claim is not in the cited chapter. The paragraph was removed. The Sources section still lists Cloud/Fog/Edge as a covered topic of *AI Factory* Chapter 9; that line is unchanged because the Sources section is fixed. Check that line before the next publication pass.
- Section 2: "Sparsity assumes the data has many zeros that the hardware can skip" is general explanation, not from the sources. Check against a vendor sparsity document if the owner wants a citation.
- Section 2: the MFU hand-check ("count the useful FLOPs in one training step, divide by the time") restates the definition in checkpoint 9. No new fact, but no source.
- Section 2: "AVX-512, short for Advanced Vector Extensions 512" and "FMA stands for fused multiply-add" are standard expansions. No source cited.

## Unresolved

- Exercise 3 and `hpl_efficiency(38, 48)` in `code/part06/flops.py`: the function needs an Rpeak argument, and the exercise does not say which Rpeak to pair with the 38 PFLOP/s Rmax. The script uses 48. The original exercise had the same ambiguity. Left as the original wording.
- Lab step 3: the chapter says the node "reports 448 GB instead of 512 GB". `filter_nodes_missing_ram()` compares kB values against `expected_kb` (the code uses 528,482,304 kB, about 504 GiB). The GB wording is from the original and was kept. A reader may ask how 512 GB maps to that kB value. Needs a unit check before the lab is used.
- Checkpoint 3 says "pipeline acceleration time". The body now says "pipeline fill time", which is the standard term. Checkpoint text is fixed by rule 5, so the mismatch stays until the owner allows a checkpoint edit.
- Lab step 2 and the call `vector_pipeline_cycles(1000, 1, 5)` carry three numbers in one command. The rule of at most two numbers per sentence was applied to prose. The command is kept exact.
- Exercise 3 and the 800-GPU example: the 800-GPU BF16 peak (1000 TFLOP/s per GPU) is labeled illustrative in the original. Kept.
- `node tools/check_mermaid.mjs`: run, output "checked 776 diagrams, 0 failed". `npm run build` not run (owner said no npm build).
