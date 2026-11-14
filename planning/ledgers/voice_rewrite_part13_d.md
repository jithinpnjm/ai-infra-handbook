# Voice rewrite ledger, Part 13 (chapters 13.8 Exercises split, 13.9 full rewrite)

Run date: 2026-11-14. Rulebook: planning/HAIKU_REWRITE_INSTRUCTIONS.md sections 0-3. Step 6 (EXTERNAL_EDITS.md) intentionally skipped as instructed.

## docs/part-13-ai-storage/08-capacity-performance-and-cost-planning.md (job B: Exercises only)

- Scope: the six numbered exercises and their lead-in sentences only. Input text blocks, commands, function names and every number kept. Count stays 6. Nested (a)/(b) removed; each sentence asks or states one thing.
- Before-edit word count was not captured for this file, so growth is not measured here. Current whole-file wc -w: 16920 (HEAD 13150; the earlier uncommitted rewrite of the rest of the chapter accounts for most of the difference).
- Span check: missing {} . Added: `gdsio` (1). The added span comes from the earlier uncommitted rewrite of another section, not from the Exercises edit. Left untouched (outside this job's scope).
- rewrite_guard: 0 hard failures, new numbers 0, lost numbers 0, new code spans 0, lost 0.
- chain_gate: 0.0 per 1000 words (exit 0).

## docs/part-13-ai-storage/09-storage-troubleshooting.md (job A: full voice rewrite)

- Words (wc -w, whole file): 12797 -> 16652 (+30.1%). Guard prose-only count: 9396 -> 13251.
- Method: every prose paragraph and list item was rewritten or expanded in place; tables, Mermaid, code blocks, the input-data blocks, front matter, headings, the 20 checkpoint blocks and the Sources section were not touched. Replacements were applied by unique-prefix location with an assert on each target.
- Every section now opens with a concrete situation (2 a.m. page, a job that stalls, a node on a good day, a parcel moving through depots, a checkpoint pause, the on-call shift).
- Outcomes list under "Prerequisites and outcomes" converted to one plain paragraph (no "you will be able to"). Numbered list markers removed; all numbers and terms kept (guard: lost numbers 0).
- Exercises 1-6: nested (a)/(b) sub-bullets converted to plain sentences under each header. Count stays 6. Commands, function names and facts unchanged. Input blocks untouched.
- Common first mistakes (items 1-5): same five items, same spans, each given a why.
- Interview angles: question lines untouched; four strong answers expanded; numbers unchanged (33.3 percent kept, not 33.33).

### Gates (run and read)
- span check (HEAD vs worktree, prose spans): missing {} , added {} .
- rewrite_guard HEAD WORKTREE: 0 hard failures; new numbers 0; lost numbers 0; new code spans 0; lost 0; residue 0 -> 0.
- chain_gate: 0.0 per 1000 words (target 0.2 or lower met; exit 0).
- Residue grep: no "you will be able", no "should be able", no "you will learn", no exclamation marks in prose, no raw "<" or "{" in prose outside tables, Mermaid, code and checkpoint markup.
- Remaining "untested" / "not run" words: `(untested here)` only inside code-block comments (locked); one prose status sentence in Lab section ("These steps were not run on a live cluster."); checkpoint 8 wording (locked).
- Math `$...$` spans: none in prose (the `$` hits are shell variables inside a code block).

### Honest-status handling
- Removed three duplicate "not run on live hardware" sentences (4.1 walkthrough, 4.2 profile, section 6 intro) so the status appears once in prose, above the lab, as rule 7 asks. Checkpoint 8 (locked) still says "a command that was not run on live hardware".

## Needs source (general explanations added, no new facts)

These are general technical glosses or teaching remarks added in 13.9. None cites a book or vendor page. Verify or cut before publication.

1. PCIe and NVMe expansions (Peripheral Component Interconnect Express; non-volatile memory express), and "local NVMe drives sit inside the server".
2. NVLink described as NVIDIA's faster link between GPUs inside one server.
3. NCCL described as NVIDIA's library for collective communication; "a rank is one process, usually one GPU".
4. Collective communication glossed as group exchanges between GPUs, such as gradient averaging.
5. "A kernel is the small program a GPU runs for one operation"; matrix kernel glossed as the small program for matrix math.
6. Data-parallel job described as copying the model onto every GPU, each with a slice of data.
7. Scaling efficiency defined as achieved speedup divided by hoped-for speedup.
8. NIC expanded as network interface card; "network adapter in the server".
9. Micro-batch size defined as examples per GPU per step.
10. Ring buffer described as the NIC's receive queue; RX ring buffer glossed.
11. Uninterruptible kernel sleep described as a thread waiting in the kernel that a signal cannot wake.
12. cProfile described as Python's built-in profiler; cumulative time defined.
13. SM expanded as streaming multiprocessor; "the unit inside the GPU that runs the work".
14. DALI described as a GPU-accelerated data loading library.
15. Prefetch queue described as a shelf of ready batches (analogy, no numbers).
16. Page cache described as where Linux keeps recently read file data; "--direct=1 bypasses the page cache" (general Linux I/O behavior, not from a cited source).
17. Profiler overhead ("a profiler slows the job while it records").
18. HBM expanded as high-bandwidth memory; latency and throughput defined.
19. Staging defined as writing to fast local drives first, then copying to shared storage in the background.
20. Bounce buffer defined as a staging area in host memory; "six locks on one door" analogy (no numbers).
21. Striping defined as spreading one file across storage targets.
22. Oversubscribed defined as uplinks carrying more traffic than they can handle.
23. RAPIDS described as NVIDIA's GPU data science library family; kvikio as its file I/O package.
24. MiB defined as mebibytes; "100 MiB is roughly the size of a short video clip" (informal size comparison, no numbers).
25. POSIX glossed as the ordinary Linux file path; DMA glossed as direct memory access.
26. GCP and GKE expanded (Google Cloud Platform; Google Kubernetes Engine).
27. SMART expanded (self-monitoring, analysis, and reporting technology) as a drive health report.
28. RPC expanded (remote procedure call) with a one-line gloss; MDS expanded with its role.
29. Epoch defined as one full pass over the dataset.
30. Falsifiable signal defined as a measurement that can prove a guess wrong.
31. Teaching remarks (not facts): "The tree has eight layers because each one is a place where production incidents have hidden before"; "Opening the kernel view first often shows a healthy kernel"; "Interviewers usually care more about how you reason..."; "a fix you cannot explain is a fix you cannot trust".
32. Wording of the Lab section: "GCP is Google Cloud Platform..." and the note that the suite checks rules, not hardware (the lab proves internal consistency only).

## Unresolved items
- None blocking. The gdsio span that shows as "added" in chapter 08 belongs to an earlier uncommitted edit; flag to the owner.
- Mermaid/build not run (instructions said no npm build for this job); Mermaid blocks in 09 are byte-identical to HEAD.
- Changes are uncommitted in the worktree, per instructions.
