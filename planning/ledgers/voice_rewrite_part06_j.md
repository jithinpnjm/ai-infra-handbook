# Voice rewrite, Part 6 chapters 6.26, 6.27, 6.28 (batch j)

Scope: docs/part-06-hpc-slurm/26-cluster-monitoring-and-health-at-scale.md, 27-backup-and-data-protection.md, 28-hpc-benchmarking-hpl-hpcg-ior-osu-and-nccl-tests.md. Uncommitted. Only these three files and this ledger were written. EXTERNAL_EDITS.md was not edited (lead instruction, step 6 of the rulebook ignored).

## Word counts (`wc -w`)

| Chapter | Before | After | Growth |
|---|---|---|---|
| 6.26 Cluster monitoring and health at scale | 8348 | 10695 | +28.1% |
| 6.27 Backup and data protection | 8245 | 10420 | +26.4% |
| 6.28 HPC benchmarking | 9465 | 11930 | +26.0% |

The locked tails (Checkpoint and Sources and review notes) were spliced back from HEAD byte for byte by a script, so their words are unchanged: 26 has 2186, 27 has 2193, 28 has 2420 words. Prose-only growth from the guard: 26 +30.2%, 27 +28.9%, 28 +26.8%.

## Gates (run from the repo root, output seen)

`python3 tools/rewrite_guard.py HEAD WORKTREE <file>`:
- 26: 0 hard failures. new numbers 0, lost numbers 0, residue 4 to 0. Guard reports "new code spans 9, lost 5". Checked by hand (inline spans from HEAD and WORKTREE, fenced blocks removed): the only real loss was the `sinfo` span in section 4, which was restored. Remaining guard "lost 5" are regex pairing artifacts from backticks next to each other in prose, not lost spans. New spans are plain-word names now typed in backticks (`gmond`, `gmetad`, `public`, `/tmp`, `authCommunity`, `STATUS`, `TIMELEFT`, `upsc`, `ups.conf`, `upsmon.conf`, `for:`).
- 27: 0 hard failures. new numbers 0, lost numbers 0, new code spans 2, lost 0, residue 3 to 0.
- 28: 0 hard failures. new numbers 0, lost numbers 0, new code spans 0 (manual check adds `/proc`, a plain path), lost 0, residue 6 to 0. Note from guard: "H2 headings changed: -1 +1" was caused by my italicising a heading; reverted, and the heading list now matches HEAD exactly (diffed).

`python3 tools/restore/chain_gate.py <file>`:
- 26: 0.3 per 1000 words. The hits are inside the status row and one table cell, which are data and were kept verbatim.
- 27: 0.0 per 1000 words.
- 28: 0.1 per 1000 words.

`node tools/check_mermaid.mjs` and `npm run build`: not run (lead instruction: "No npm build or full Mermaid").

Other self-checks run:
- Code fences: guard reports code blocks unchanged in all three chapters (no hard failure).
- Checkpoint count: 20 `<details>` blocks in 28 and in HEAD; 26 and 27 unchanged by splice. Checkpoint and Sources text is byte-identical to HEAD.
- Headings: 28 heading list diffed against HEAD, identical. 26 and 27 headings untouched.
- No exclamation marks in prose. No raw `<` or `{` outside code. Semicolon chains "; the/every/each/a/an": 0 in 27 and 28, 3 in 26 (all inside the locked status row and one table cell).
- Honest status: each chapter keeps "not run" or "not verified" in the status row, and one plain sentence above its lab steps.
- Residue: no "(untested here)", "the book", "Volume N", "my tool" or "earlier draft" in reader text. The only remaining "book" words are inside the locked Checkpoint and Sources sections.

## What changed

Every chapter:
- Each section opens with a situation (an on-call page, a purchase report, a head node that dies on a Monday, a backup that reports success for a year, and so on).
- The "By the end you will be able to" outcomes list (26, 27, 28) became one plain paragraph. Headings kept.
- Acronyms and terms are defined at first use in plain words (MIB, OID, RRD, TSDB, DCGM, NVLink, WORM, RPO, RTO, HSM, MFU, NVSwitch, DGEMM, IOPS, SM, MPI, NCCL, and others).
- Book attributions were changed from "the book" to the full title of the book the original text already named. Where the original did not name the book, the sentence was rewritten without attribution (see Needs source).

26 (cluster monitoring):
- Lab steps paragraph turned into a numbered list of the same nine steps, same commands. One honest sentence sits above the list: the steps were not run on a live cluster, and the first three ran locally.
- Exercises: still 14. Several multi-part exercises (6, 7, 9, 10, 11, 13) split into shorter sentences, no new numbers. Exercise 6's original "snmpget and snmpwalk ... that read sysUpTime" became "snmpget that reads sysUpTime" plus "snmpwalk that reads the same branch". The original snmpwalk used the `system` branch, which holds sysUpTime, so this matches; flagged for review.
- Removed the reader-text sentence "the levels are described from general knowledge of DCGM, not from a cited source" (moved to Needs source below). The Sources section still records "live DCGM diag levels" as not verified.
- Removed the repeated "were not run" sentence in section 4. Its limit is now described as canned rows versus real `sinfo` output.

27 (backup):
- Lab: numbered list of ten steps, same commands and facts. Single honest sentence above the list: steps 1 to 5 ran on a laptop, steps 6 to 10 were not run.
- Exercises: kept at 6 (an intermediate 25-item version was caught and replaced before the gates). Each of the six keeps the original content, split into one-question sentences.
- Stray ":" after the Bacula `Archive Device = /dev/nst0` sentence was a typo in the original and was replaced by a full stop.
- "Supercomputers for Linux Sysadmins book" in the status row now reads "*Supercomputers for Linux Sysadmins* and general knowledge". The status row is data; only the word "book" changed.

28 (benchmarking):
- Lab: numbered list of eleven tasks, same content. Sentence "The first four tasks run on your laptop. The tasks after them need a cluster, and none of them was run for this handbook."
- Exercises: kept at 14. Exercises 1, 3, 6, 11 and 13 extended with one short sentence of framing each. No new numbers.
- "$< 16.0$" changed to "below 16.0" (raw `<` and math in prose). Same meaning.
- "Table 12.1 in the book", "Table 12.2" and "Table 5-1" removed from reader text. These are borrowed table labels (residue rule). Their numbers (12.1, 12.2, 5-1) are no longer in the prose. The data they referred to is kept as written.
- Heading "## 1. Methodology (Systems Performance, chapter 12)" kept exactly.
- "In the book's example" (60 GB/s DDP gradient example) rewritten as "Suppose ..." because the source named in Sources does not say which book this example comes from.
- "The book covers this in its PyTorch chapter" removed, because no source in Sources names that chapter. Replaced with the general statement in Needs source.

## Needs source (explanation added, not in the original text)

26:
- Xid errors described as codes the NVIDIA driver writes when a GPU hits a fault. ECC and remapped rows described in plain words.
- BMC described as a small computer on the server board that reports sensors while the OS is down. IPMI described as its query protocol.
- SEL described as the BMC's record of hardware events. Redfish described as a web interface to hardware data.
- RRD described as a fixed-size file for one metric. Multicast and unicast explained as one packet to a group, and one to one server.
- Loki and Elasticsearch described as log stores. MCE described as a CPU hardware error report.
- SLO described as the availability target for a service. Dead man's switch explained as an always-firing heartbeat.
- Entropy and fragmentation explained where they appear in the alert text.
- Prolog and textfile collector explained.

27:
- Explanation of how each number in 3-2-1-1-0 answers one kind of disaster (section 2). This is an interpretation of the rule.
- WORM, append-only credentials, canary files, entropy-based detection, clean-room rebuild, and the reason DNS/DHCP files are rebuilt from their source.
- Content-defined chunking, why an edit does not shift later chunks, and why "content hashes" verify chunks.
- SHA-256 described as a fingerprint function.
- Lineage, ACL and xattr, catalog, HSM, cold data, DVC and lakeFS, lifecycle policies, and the purpose of a transfer node.
- The sentence "the offline copy should be small enough to carry" (section 7) is our advice, not sourced.
- Choosing restic, borg or kopia by team type (section 4) is our advice.

28:
- The sentence that the PyTorch chapter covers the sync problem was replaced with "Framework guides, including PyTorch's own profiling notes, describe the same problem." This is a general claim, not checked against a specific source.
- The "60 GB/s over 100 GB/s NIC" DDP example: original named "the book", source unclear. Confirm which book before publishing.
- Explanations added: benchmark as a repeatable question; cloud versus on-premises for a quick answer versus a long-lived purchase; infant mortality; burn-in; warm cache; NUMA domain; DMA; pinned memory; PyTorch DDP; NVSwitch; DGEMM; golden run; MFU; ping-pong; switch hop; downtrained link; HPCG sparse matrix and preconditioner; the knee of a curve; dead loop optimised away by a compiler.
- "a vendor will often push to accept a cluster with a few weak nodes" and "a cloud instance can answer a question in an afternoon" are general advice.
- "The laptop was also running other work" is a restatement of the original "shared with other processes", not a new fact.
- The four-types paragraph ("Micro-benchmarks tell you whether one part works at its limit ...") is our framing of Gregg's four types.
- The sentence about the blocked NIC and downtrained link explains the existing text.

## Unresolved

1. Bacula configuration in 27 (code blocks, unchanged, per rule 5): names do not match across blocks. `Job` uses `Client = client1` but the Client stanza is `client-1`. The Director's `Storage` is `dir-storage1`, but the Pool points to `Storage = Dir-Storage1`. The Job's `Pool = example-pool` does not match the `stor1-pool` stanza. Left as written. Owner should decide whether the example is meant to be consistent before a reader copies it.
2. The Sources and review notes sections of all three chapters still contain drafting words that are out of scope for this run ("untested here" and "Run here" in 26's Sources, "Not verified" lines, "section 12.6 of the book" in 28, and "Table 12.1" in 28's Sources). They are locked and were not touched.
3. Checkpoint 16 in 28 (locked) names "AI Systems Performance Engineering"; the body now refers to the same title. No change needed.
4. 28 checkpoint and Sources text still says "the book" in places (locked, out of scope).
5. The status rows in all three chapters keep their original "Drafted" and bold "Run" / "Not run" wording (table data). The rule asks only for one honest status sentence above the lab, which is present.
6. 26: the `sinfo` span restored in section 4. The guard's "lost 5" for code spans is a pairing artifact, confirmed by hand.
7. Mermaid and npm build not run (lead instruction).
8. The DDP "60 GB/s" example and the "PyTorch chapter" sentence need a source check before publication (see Needs source).
