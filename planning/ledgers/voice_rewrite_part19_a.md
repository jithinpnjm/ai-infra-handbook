# Voice rewrite ledger: Part 19 chapters 19.1, 19.2, 19.3 (pass a, 2026-11-14)

Scope: `docs/part-19-capstone/01-*.md`, `02-*.md`, `03-*.md`. Not committed. Other chapters untouched.

## Method

- Prose was rewritten by hand in scratch templates. Code fences, tables, the top matter (front matter, H1, Field table), and everything from `## Checkpoint questions` to the end (checkpoints, Sources, Verification log) were then inserted byte-identically from `git HEAD` by an assembly step. Verified: tail identical True, top identical True, fence and table counts equal to HEAD.
- Headings: H2 and H3 text checked equal to HEAD in the body.
- Honest status: each chapter has one plain status sentence above the lab. Per-step "Run here" and "Not run" tags were folded into that sentence (no facts removed).

## Gates (run 2026-11-14, output copied)

| File | Words before | Words after | Growth (wc) | rewrite_guard | chain_gate | span check |
|---|---|---|---|---|---|---|
| 01 Slurm GPU cluster | 8590 | 11336 | +32.0% | ok, 0 hard, new numbers 0, lost numbers 0, new code spans 1, lost 0, residue 0 to 0 | 0.0 per 1000 words | {} |
| 02 Kubernetes GPU platform, KAI and Kueue | 8734 | 11411 | +30.7% | ok, 0 hard, new numbers 0, lost numbers 0, new code spans 2, lost 0, residue 1 to 0 | 0.0 per 1000 words | {} |
| 03 Inference on GKE | 10031 | 13095 | +30.5% | ok, 0 hard, new numbers 0, lost numbers 0, new code spans 0, lost 0, residue 11 to 7 | 0.0 per 1000 words | {} |

Checkpoint count: 20, 20, 20 (unchanged). Mermaid: `node tools/check_mermaid.mjs` on the three files: "checked 776 diagrams, 0 failed" (whole repo run; the three chapters' Mermaid blocks are byte-identical to HEAD).
`npm run build` not run (the task said no npm build). `planning/EXTERNAL_EDITS.md` not edited (per instruction).

## Needs source (general explanations added in this pass, not from the original)

Chapter 19.1
- Munge as the authentication service that signs Slurm daemon messages, and the credential being time-stamped (the original stated the time-stamp point only).
- cgroup definition; NUMA definition; NFS definition; NVML definition; PMIx definition.
- Xid as NVIDIA's error-code name; "code 79 means the GPU has fallen off the bus" (the catalog wording is cited in 19.2 and 19.3; confirm 19.1 wording).
- Kernel ring buffer and `dmesg`; ECC definition.
- Drain keeps already-running jobs running (Slurm DRAIN behaviour).
- Fairshare balance decaying back toward its share over time (describes behaviour, not a parameter).
- DCGM definition; SM (streaming multiprocessor) definition; NCCL definition; game-day definition.

Chapter 19.2
- Reconciler definition; kubelet definition; device plugin definition; CDI definition.
- Container-Optimized OS definition; taint and toleration definition.
- Secure Boot signing explanation for the driver crash example (the original gave the error, not the cause).
- CRD definition; PCI vendor ID `10de` is NVIDIA; SLO definition.
- Cordon definition; Workload Identity definition.
- The Kueue flavor-as-shelf analogy and the shared-kitchen analogy (no numbers; analogies only).
- GPU time-slicing gives no isolation and whole-GPU keeps failures contained (the isolation point is from the original README claim; the containment reading is an added inference).

Chapter 19.3
- p95 definition (the phrase "most requests beat" replaces "95 percent" to avoid a new number).
- Time to first token and tokens per second definitions; HPA and KEDA definitions; Little's law definition.
- Goodput definition (original cites the DistServe paper via the vLLM source; kept).
- Node Problem Detector and auto-repair wording kept from the original; no GKE claim added.
- ECC definition; kubelet startup-probe kill-and-repeat behaviour (explanation of the original failure mode).

## Unresolved (not changed)

- Chapter 19.1 checkpoint 5 (default Slurm ports) and checkpoint 4 (what `slurmdbd.conf` configures) are close to bare definitions. Left byte-identical per rule 5.
- Chapter 19.2 checkpoint 13 (what the three Kueue objects do) and 3 are near-definitions. Left as is.
- Chapter 19.3 checkpoint 3 (three kinds of tool) is near a definition. Left as is.
- Chapter 19.1 Exercise 2 solution sketch uses `StartTime=2026-11-09T08:00:00`, which is before today (2026-11-14). It is code text in a sketch, left unchanged. The owner should decide whether to update the date.
- Chapter 19.1 Sources (locked, unchanged) contain first-person residue: "The weight 10000 is my example value" and "This light pass did not re-read them chapter by chapter." Not in reader body; flagged for the owner.
- Chapter 19.2 body keeps the original attribution "*Generative AI on Kubernetes* ch. 7" and the sentence "The book calls this combination common and recommended" was rewritten to name that book. The claim itself is the original's.
- Chapter 19.3 body keeps several unnamed attributions from the original ("The book frames three kinds of tool", "The book calls direct download...", "The book says it integrates with Triton and Dynamo", "The book says the cache means...", "The book says that in explicit mode...", "The book's own example..."). These were not named in the original, so they were not named here. The residue count stays at 7 for this reason. Owner should check which book each refers to.
- Chapter 19.3 `$oauthtoken` is a literal registry user name inside a code span, not math. No `$...$` math found in any of the three files.
- Chapter 19.3 lab numbers from the mock sweep (the 472 ms and 1,293 ms second run) are kept as in the original and marked as noise in prose.
- Chapter 19.1 "Verification log" and "Not verified on live hardware" are in the locked tail and were not touched.
- Lab steps in all three chapters are not run on live hardware. This is stated once in each lab intro.
