# Voice rewrite, Part 9 batch E (chapters 9.13 and 9.14)

Scope: `docs/part-09-nvidia-systems/13-sizing-and-capacity-planning-exercises.md` and `docs/part-09-nvidia-systems/14-cloud-gpu-platforms-dgx-cloud-coreweave-nebius-and-gcp-a3-and-a4.md`. Nothing committed. EXTERNAL_EDITS.md not edited (per instruction).

## Word counts (wc -w)

| Chapter | Before | After | Growth |
|---|---|---|---|
| 9.13 sizing and capacity planning | 6473 | 9820 | +51.7 percent (above the 25 to 40 aim; not trimmed, rule 1 forbids trimming; owner call) |
| 9.14 cloud GPU platforms | 6099 | 8332 | +36.6 percent |

## Gates

Run from the repo root.

- `python3 tools/rewrite_guard.py HEAD WORKTREE <file>`
  - 9.13: 0 hard failures. words 4495 -> 7842 (guard's own count). new numbers 52, lost numbers 0, new code spans 2, lost 0.
  - 9.14: 0 hard failures. words 5364 -> 7597. new numbers 1, lost numbers 0, new code spans 4, lost 0.
- `python3 tools/restore/chain_gate.py <file>`
  - 9.13: 0.0 per 1000 words (7901 words)
  - 9.14: 0.0 per 1000 words (7682 words)
- Span check (inline backtick spans, code blocks excluded): `{}` for both files.
- `node tools/check_mermaid.mjs`: checked 776 diagrams, 0 failed (repo-wide run).
- `npm run build` not run (instruction for this batch: no npm build).

## New numbers (guard list), explained

All of these are restated from code blocks or tables that already existed in the chapter, or are simple arithmetic on them. No new facts.

- 9.13 prose restates block values: 0.12, 0.2667, 0.40, 0.7, 0.72, 0.80, 0.989, 1,000, 1,095, 1,392, 1.35, 11,178, 11,400, 115.1, 115.2, 120, 128, 13.9, 135.8, 15.2, 150,000, 164, 17,866, 172.8, 18,007.
- 9.13 "8/30" training ratio and "one 118th GPU" restated from the block (118 is the first GPU past 117).
- 9.14 8868: restated from the existing `ping -M do -s 8868` line.
- 9.14 8-byte ICMP header and 20-byte IP header in the ping walkthrough: standard header sizes that make 8868 + 8 + 20 = 8896. Listed under Needs source.

## Needs source (general explanations added, not chapter facts)

9.13
- Definitions of MIG, FinOps, SM, KV cache, QPS, PUE, FTE, PFLOPS, BF16, TTFT, P95.
- The walkthroughs explaining why fixed costs raise cost per token at low load (the chapter's own numbers; the reasoning is general).
- The statement that asynchronous checkpoints run in the background so the loop does not stop.
- The statement that fifteen-minute checkpoints bound lost work to fifteen minutes.
- Explanation of `-B` (no bytecode cache) in the commands section.
- Explanation of `max_over_time` as the highest reading in the window.

9.14
- Definitions: hypervisor, bare metal, multi-tenant, DPU, DMA, PCIe passthrough, NCCL, AllReduce, GPUDirect RDMA, NVMe SSD, NVLink domain, leaf and spine switches, oversubscription, lossless fabric, line rate.
- Definitions of operating expense, data hall, Kueue, Volcano, gang scheduling, namespace, RBAC, Helm, node labels, IMDS, live migration, draining, the NVIDIA kernel driver module, Terraform, service account, workload federation, project, tenant.
- "S3-compatible storage speaks the same API as Amazon S3."
- The Friday change-window scenario in 4.2 is illustrative only, not a reported incident.
- Step-1 package manager note (APT on Debian-based, yum on RHEL-based) matches the commands already in the chapter.

No new vendor claims were added. Nebius statements are unchanged in fact (the table, the fabric membership paragraph and the resource names are the original text, only with explanation around them).

## Structure and rule checks

- Every section opens with a situation or concrete scene (9.13: planning meeting, hotel wing, room power; 9.14: deadline and slow multi-node job, team with the same GPU slower in cloud, Friday change window).
- Outcomes lists in both chapters rewritten as one plain paragraph (no "you will be able to").
- Exercises: 9.13 has 6 exercises, 9.14 has 6 exercises, same counts and same commands. Multi-part asks split into one-question lines.
- Bold lead-ins converted to plain text in 9.14 sections 1.2, 2.2 and 4.2 and in 9.13 exercises (at most one bold idea per section).
- Residue removed from body text: 9.14 "untested in this authoring environment" sentence in the commands section (the honest status moved to the lab paragraph and the status row). 9.13 had no "(untested here)" residue in the body.
- Honest status sentence kept once per chapter in the lab section ("not run"): 9.13 "The Prometheus queries ... were not run against a live cluster"; 9.14 "These steps were not run on a live cloud account".
- Checkpoint questions and answers unchanged (20 each).
- Sources and review notes sections unchanged (locked).

## Unresolved

1. 9.13 body growth is +51.7 percent, above the +25 to 40 percent aim. Rule 1 forbids trimming, so it was left. Owner can decide whether to thin the added walkthroughs.
2. Locked text in Sources and review notes of 9.14 still contains first-person residue ("as I recall it", "this handbook's own"). Rule 5 keeps the Sources section unchanged, so it was not touched. Owner should decide.
3. 9.14 "Update, November 2026" blockquote (Run:ai open source, Apache 2.0, 13 October 2026) kept verbatim as a fact-bearing line. Not verified in this run.
4. 9.14 Google Cloud A3 row (`a3-highgpu-8g` TCPX vs `a3-megagpu-8g` TCPXO) is unchanged and still flagged in its own Sources notes as unresolved.
5. 9.13 Exercise 5 prompt refers to "the room power cap in the table", and the table states 120 kW while the block says 150 kW. Kept as in the original; a source-data question for the owner.
