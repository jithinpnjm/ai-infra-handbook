# Voice rewrite, Part 20 chapters 20.1 to 20.3 (batch a)

Scope: `docs/part-20-nebius-sre-interview/01-the-nebius-loop-and-how-to-use-this-volume.md`, `02-the-role-in-one-page-the-job-posting-line-by-line.md`, `03-triage-method-for-a-sick-linux-box.md`. Nothing committed. `planning/EXTERNAL_EDITS.md` not edited (per owner instruction).

## Word counts (`wc -w`, HEAD vs worktree)

| File | Before | After | Growth |
| --- | --- | --- | --- |
| 20.1 | 4926 | 6627 | +34.5% |
| 20.2 | 5437 | 7026 | +29.2% |
| 20.3 | 8175 | 10601 | +29.7% |

## Gates (run on the final files)

- `python3 tools/rewrite_guard.py HEAD WORKTREE <file>`: 0 hard failures in all three. Output lines:
  - 20.1: `words 4787 -> 6488, new numbers 0, lost numbers 0, new code spans 0 lost 0, residue 5->5`
  - 20.2: `words 4020 -> 5609, new numbers 0, lost numbers 0, new code spans 0 lost 0, residue 14->14`
  - 20.3: `words 7371 -> 9797, new numbers 0, lost numbers 0, new code spans 0 lost 0, residue 51->52`
- `python3 tools/restore/chain_gate.py <file>`: 0.0 per 1000 words for all three (target 0.2 or lower).
- Mandatory span check (inline code spans, HEAD vs worktree, fenced blocks excluded): `{}` for all three.
- Extra integrity checks, all identical to HEAD: fenced code blocks, headings, Markdown tables (20.3 table separator restored to `|---|---|---|` after one slip), front matter, the 10 `<details>` checkpoint blocks per chapter, and the Sources and review notes sections. No `!` in prose, no "will be able to", no "you will learn".
- `node tools/check_mermaid.mjs`: `checked 776 diagrams, 0 failed`.
- `npm run build` not run, per the instruction for this batch ("No npm build").

## Rule and gate notes

- Rule 13 (test-log language to Verification log): these chapters have no Verification log heading, and headings are locked, so nothing was moved. The test-log sentences were kept in natural voice inside the existing status paragraph (20.3), the lab intros and steps, and "What the container run showed" (20.3). The lab sentences "I ran this step" and "I did not run it for you" (20.2) and "I did not run these steps" (20.1) stay as the one honest status line per lab.
- 20.3 residue count moved 51 to 52. The only new-looking hit is the legacy "I have not checked" wording, which was already in the original sentence. Soft, not a hard gate.
- Checkpoint blocks and Drill questions kept byte-identical (count 10 per chapter), per the batch instruction.
- Lab steps keep their count and commands. Step text received light plain-language rewording. Output blocks are unchanged.
- "Picture" openers were varied (Imagine, Suppose, Think of, Consider) so the chapters do not open every section the same way. Two or three remain in 20.1 and 20.2.
- Numbers: the guard reports 0 new numbers. A raw counter showed one extra mention of p50/p90/p99 in 20.2 and one "section 6" cross-reference in 20.3. Both were removed.

## Needs source (general explanations added, no Nebius or book facts added)

These are general teaching explanations written for this rewrite. None is a claim about Nebius internals. Each should be checked before publication.

- 20.1: "loop" and "talent specialist" roles; "take-home task"; "hotspot" as a backup connection; LeetCode and HackerRank as practice sites; "quadratic" growth wording; "off-by-one error"; "KV cache" as attention memory; "distributed system" meaning; two pointers in a sorted list.
- 20.2: "label" and series cost in metrics; "vLLM" as a serving server; Triton and Ray as serving and compute tools; "SLO" definition; "multi-tenancy"; "inference" vs training; "foundation model" and "multimodal"; "OpenAI-compatible API"; "endpoint"; "data residency"; "batch" and "speculative decoding" (small model proposes, larger model checks); "p50/p90/p99" as percentile labels; "time to first token"; "prefill" and "decode"; "backpressure"; "liveness probe"; "SLA" meaning; "runbook"; "replica"; "zone"; "module" in infrastructure code; "required vs preference" in a posting; "being paged".
- 20.3: "uninterruptible state" explanation (the book attribution for 1993 and the load count stays as in the original); "file descriptor" and per-process limit; "OOM killer" as last resort; "swapping" and "thrashing" definitions; "major fault" meaning; "resident set"; "hyperthreading" and two threads on one core; "steal" time; "merged I/O" in the kernel; "namespace" and sharing a namespace for a debug container; "cgroup" as a group with resource limits; "etcd" as the cluster state store; "BCC and bpftrace built on eBPF"; "strace" and "perf" one-line descriptions; "off-CPU" meaning; "cache hit" meaning; "instrumentation" in the diagnosis cycle; supermarket checkout analogy for utilisation, saturation and await (no numbers used); "mitigation before root cause" explanation (points to 17.11, which the original cited).

## Gem books

No new book references were added. Short forms already in the original ("Systems Performance", "How Linux Works", "Production Kubernetes") were kept exactly as written, because they are attributed in the original text. Unresolved: the rule asks for full titles, so a later pass could expand "Systems Performance" to "Systems Performance: Enterprise and the Cloud" in 20.3 if the owner wants it. Not changed here because the heading and span lock makes the edit a wording-only change.

## Unresolved

- Nothing failed a gate.
- 20.3 "Not verified" and "Not run" lines kept as in the original (they are the honest status for the container run).
- Check in review: the "Systems Performance" short form (see Gem books).
- Check in review: Nebius-facing sentences in 20.2 section 6 keep the original vendor facts; the new explanations around them are general and listed above.
- `planning/EXTERNAL_EDITS.md` not updated (owner instruction to skip step 6).
