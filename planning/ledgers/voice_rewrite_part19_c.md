# Voice rewrite ledger: Part 19 chapters 19.7, 19.8, 19.9 (pass c, 2026-11-14)

Scope: `docs/part-19-capstone/07-*.md`, `08-*.md`, `09-*.md`. Not committed. No other chapter touched. `planning/EXTERNAL_EDITS.md` not edited (per instruction).

## Method

- Prose was rewritten section by section in scratch files. Code fences, tables and Mermaid blocks were inserted byte-identically from `git HEAD` by an assembly step (block markers, one per fence or table, checked to be used exactly once). Front matter, H1, the top table, and everything from `## Checkpoint questions` to the end (checkpoints, Sources, Verification log) are byte-identical to HEAD.
- Headings (H1 to H4) equal HEAD in each chapter (55, 55 and 59 headings).
- Outcomes lists (numbered, "you will be able to") were rewritten as one plain paragraph under the locked `### Outcomes` heading. Each section opens with a situation.
- Exercise count, lab step count, lab commands and checkpoint count (20 each) are unchanged.

## Gates (run 2026-11-14, output copied)

| File | Words before (wc) | Words after (wc) | Growth (wc) | Prose words (guard) | rewrite_guard | chain_gate | span check |
|---|---|---|---|---|---|---|---|
| 07 observability platform | 9157 | 11831 | +29.2% | 7895 to 10569 | ok, 0 hard, new numbers 0, lost numbers 0, new code spans 0, lost 0, residue 6 to 0 | 0.0 per 1000 words | {} |
| 08 MIG multi-tenancy | 9117 | 11964 | +31.2% | 7848 to 10695 | ok, 0 hard, new numbers 0, lost numbers 0, new code spans 0, lost 0, residue 1 to 0 | 0.0 per 1000 words | {} |
| 09 capacity planning | 11057 | 14416 | +30.4% | 7696 to 11055 | ok, 0 hard, new numbers 0, lost numbers 0, new code spans 0, lost 0, residue 6 to 0 | 0.0 per 1000 words | {} |

Span check: `{}` for all three (no span missing). Chapter 07 adds one plain identifier without backticks (`DCGM_FI_DEV_` written as plain text) so the span set is unchanged.

Code fences, top matter, tail: identical to HEAD (checked with a script: fences list equal, tail from `## Checkpoint questions` equal, top before `## Why this matters` equal).

Mermaid: the three chapters' Mermaid blocks are byte-identical to HEAD. `node tools/check_mermaid.mjs` and `npm run build` were not run in this pass (the task named the guard, chain gate and span check only).

## Changes that touch facts or cross-references

- 09, section 4.3: "The next section shows how easily it flips." changed to "Section 6 shows how easily it flips." The flip is in section 6.1 (pricey hardware row). The original pointed at section 5, which does not show the flip. Owner should confirm.
- 07, section 3: the Kubernetes AI book's vLLM names are now said to differ "in a later release" as an inference, and the sentence says it is an inference, not a statement from the book (original had the author's reasoning in first person).
- 08, section 6: the older NCCL advice is attributed to *AI Systems Performance Engineering* by name. The original said "Older book advice". The claim is the same and the book is the one that the Sources section lists for chapter 3.
- 09, section 2.2: "Adam ... keeps two extra running values for each weight" is an added explanation (see Needs source).
- 08, section 5 and 09 section 3.3 use plain words for "chargeback", "utilisation target" and "queueing delay".
- Numbers: no digit token was added to prose or removed (guard: new 0, lost 0 in all three). Word numbers ("two", "three", "six") appear only where the original had them.
- The first-person "I", "my" and "we" were removed from reader text in all three chapters (e.g. "The reserved share is an assumption", "This chapter's author did not have"). The locked Sources and Verification log still contain first person (see Unresolved).

## Needs source (general explanations added in this pass, not from the original)

Chapter 07
- Helm release label (what the Operator selects by default); selector and empty-selector explanation.
- Cardinality as the count of distinct series; head series; histogram buckets as one series each; fill factor meaning (only some label combinations appear).
- DCGM expansion "NVIDIA Data Center GPU Manager"; Prometheus as "metrics database and rule engine"; OpenTelemetry Collector as "a small agent on each node".
- Watchdog and dead man's switch as an outside service; canary as a test alert.
- Xid as an error code the NVIDIA driver writes; regular expression as a pattern matching several names.
- DaemonSet; GPU Feature Discovery as the labelling component; toleration and taint explanation.
- cAdvisor as the container resource reporter; linter as a checker; sidecar as a helper container.
- Environment variable explanation; `0400` as owner-read-only.
- Loki as the log store; MinIO as an object store that the chart brings; the Loki canary as a test writer.
- Linux capabilities as special privileges; loopback binding; provisioned file read at startup.
- Dashboard uid as a unique identifier; a dashboard variable as a drop-down; PromQL as the query language.
- USE and RED expansions (saturation as work waiting; duration as request time); the `for` clause as an alert wait.
- Polling as asking again on a timer; scraping as reading numbers from each address on a timer.
- SLO and error budget definitions; burn-rate as spend pace (bank-account analogy, no numbers).
- Preset as a bundle of settings; the memory limiter's purpose.

Chapter 08
- Pending as the pod state before placement; drain as emptying a node of work; cordon as marking a node.
- SM as the streaming multiprocessor; copy engine as the unit that moves data; L2 as the shared second-level cache.
- MPS and CUDA IPC definitions; NCCL as the multi-GPU library; GPUDirect as NVIDIA's direct data path.
- Driver as the kernel module; minimum driver as the oldest supported one.
- Crossbar as the link between compute and memory; thrashing as caches evicting each other's data.
- NVML as the library behind `nvidia-smi`; RBAC; hypervisor as the VM layer; media engines as video encode and decode units.
- Profile-name reading rule (first number is SM slices, number after the dot is memory in GB) as a reading aid, checked against the table.
- Strategy as the naming rule; node pool; constant series; ResourceFlavor and cohort definitions; "Limited IPC" left as printed.
- Analogies (seat row, furniture in a narrow room, rent versus flat) carry no numbers.

Chapter 09
- Floating-point operation (FLOP) definition; dense transformer definition; sparsity explanation for "dense".
- Precision as bits per number; the MFU efficiency-grade framing.
- First-order rule definition; Adam as the optimizer with two running values per weight; fixed point definition; independent failures meaning.
- Geometric growth; P90 meaning; quantile and degrees of freedom definitions; logarithm turning percentage growth into a line; prediction interval as the range of likely values.
- Triangular distribution shape; seed as the random generator start; amortised meaning; adapters as small add-on layers.
- Queueing delay definition; repair state; rework fraction and spot trade-off; stack-of-blocks, lane, fan and flat analogies (no numbers).
- Constant series as a fixed price list; the 20 percent sensitivity swing reading.

## Unresolved (not changed)

- Checkpoint questions that are near bare definitions, left byte-identical per rule 5 (list for the owner):
  - 07: Q14 (which collector metric names the run observed) and Q17 (what the reserved share is and where its value comes from).
  - 08: Q13 (what a slice's weight is) and Q19 (how kube-state-metrics spells a resource).
  - 09: Q2 (what the 6ND rule is) and Q8 (what Young's formula is and how sure we are of it).
- Locked Sources and Verification log text (not in reader body) still has first-person residue, flagged for the owner:
  - 09 Sources: "I did not fetch it again", "I claim no exact `nvidia-devops` path", "is my first-order model", "is my simplification", and "my first-order model" in the inferences list.
  - 07 and 08: no first-person residue found in the locked tail.
- Chapter 09 Sources and the Verification log count the removed items and the "Still unverified" list. They were not edited.
- Chapter 09 Section 4.3 cross-reference fix (above) needs the owner's confirmation.
- Chapter 07 Exercise 5 and checkpoint 18 say the disk at two bytes per sample is "about 88 GB"; the text says 87.8 GB. Left as in the original (locked fact, rounding not changed).
- Chapter 07 Section 3 still names two older dashboard metric names from chapter 17.4 by code span (`DCGM_FI_DEV_GPU_UTIL`, `DCGM_FI_DEV_GPU_TEMP`). These are intentional examples of the old names.
- Math: no `$...$` math in any of the three files. `$labels`, `$PWD` and `$MIGPARTED_VALIDATOR` appear only inside code blocks or code spans.
- Chapter 08 "Expected shape of the output" lines in Step 4 now read as separate sentences (for the two-numbers-per-sentence rule). The same counts and profile names appear as in the original.
- Lab steps in all three chapters: the cluster and GPU steps were not run. Chapter 07 says so in the lab intro; chapter 08 in the intro and in "What was run here and what was not"; chapter 09 in "What was run and what was not". Chapter 09's lab did run on the laptop (stated).
- Gem books are named by full title where the original attributed them. Chapter 09 keeps "the gem books" in the Young's formula sentence (original wording).
