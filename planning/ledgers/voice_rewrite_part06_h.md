# Voice rewrite, Part 6 chapters 6.20, 6.21, 6.22 (batch h)

Scope: docs/part-06-hpc-slurm/20-beegfs-gpfs-wekafs-and-vast.md, 21-parallel-i-o-and-checkpoint-patterns.md, 22-provisioning-with-pxe-ipxe-dhcp-tftp-and-image-management.md. Uncommitted. Only these three files were edited. EXTERNAL_EDITS.md was not edited (lead instruction overrides rule 3.6). Front matter, the title, the level/status table, all headings, all fenced code blocks (including Mermaid), the checkpoint block and the Sources and review notes section are byte-identical to HEAD (checked by script: front, tail, fenced blocks, 20/20, 20/20, 20/20 details).

## Word counts (`wc -w`, HEAD baseline taken before any edit)

| Chapter | Before | After | Growth |
|---|---|---|---|
| 6.20 BeeGFS, GPFS, WekaFS and VAST | 6630 | 8659 | +30.6% |
| 6.21 Parallel I/O and checkpoint patterns | 10903 | 14221 | +30.4% |
| 6.22 Provisioning with PXE, iPXE, DHCP, TFTP and image management | 8312 | 10705 | +28.8% |

## Gates (run from the repo root, output seen)

`python3 tools/rewrite_guard.py HEAD WORKTREE <file>`, final run:
- 20: 0 hard failures; new numbers 0; lost numbers 0; prose words 6487 to 8516; residue 3 to 2. Code spans: 0 lost, 0 new (set diff of inline spans against HEAD).
- 21: 0 hard failures; new numbers 0; lost numbers 0; prose words 10575 to 13893; residue 17 to 11. Code spans: 0 lost. New spans (4): `MPI_File_open`, `MPI_File_set_view`, `state_dict`, `noatime`, `pread()`, `io_uring`, `fsync`, `Get`, `wait_stream` (plain words previously, now typed identifiers).
- 22: 0 hard failures; new numbers 0; lost numbers 0; prose words 8052 to 10445; residue 15 to 9. Code spans: 6 lost, all six are the "(untested here)" tags that were inline code in HEAD and are removed on purpose (rule 7). 0 other spans lost. New spans: `dhcp`, `kernel`, `initrd`, `boot`, `dhcp-host`.

`python3 tools/restore/chain_gate.py <file>`, final run:
- 20: 0.2 per 1000 words (target 0.2 or lower: met)
- 21: 0.1 per 1000 words
- 22: 0.1 per 1000 words

`node tools/check_mermaid.mjs` and `npm run build`: NOT RUN (lead instruction: no npm build or full Mermaid). Mermaid blocks are byte-identical to HEAD, so no new Mermaid risk was introduced.

Other checks run:
- No "will be able", "should be able", "you can:", "In this chapter", "By the end", "my tool", "earlier draft" in prose.
- No exclamation marks in prose; no raw `<` or `{` outside code.
- "Volume 15" remains only in the 6.20 section 8.1 heading (heading text is kept by rule 5) and in the source line naming `nvidia-zero-to-hero/volume-15` (original attribution, unchanged).
- One honest "not run" or "untested" sentence is present in each chapter's body (6.20 lab heading and section 9 "not run" sentence; 6.21 section 6 heading and "Three more steps have not been run"; 6.22 section 9 "The VM steps have not been run yet"). Status rows are unchanged.

## What changed

- Every section that was a framing sentence got a situation first where it was missing (for example "Picture a small team ..." before Comparison, "Picture a GPU dashboard ..." before Data loading, "Imagine someone edits the commit code on a Friday afternoon" before the Lab).
- "Prerequisites and outcomes" in all three chapters: bullet lists of "you will be able to" or "you can" items became one plain paragraph per chapter. Heading kept.
- Walkthroughs added with the same numbers and commands: the write path through BeeGFS services, the DHCP and iPXE conversation for a UEFI node, a sequential-versus-random read example, the Friday-style rollout order for an image wave, a board swap that keeps identity through the switch port.
- Bold reduced to one idea per section (the original had bold on every boot-chain step, every node state and every cluster-manager name). Table bold kept.
- Exercises rewritten in all three chapters: same count (6 each), same commands, same facts. Nested (a)(b)(c) lists removed. 6.20 exercise 6 uses Stage 1 to Stage 5. 6.22 exercise 5 names four nodes with first, second, third and fourth.
- Lab step lists kept in count and command text: 6.20 has 6 steps, 6.21 has 3 tested plus 3 not-run items, 6.22 has 7 VM steps.
- 6.22 "(untested here)" tags removed from the ROCKS and PelicanHPC walkthroughs. The steps still come from the book and were not run here (see Unresolved).
- 6.22 attribution "the book says" in the PelicanHPC paragraph rewritten as "The book's figures for that case are ...". Same claim, same numbers.

## Needs source (explanations added that a reviewer should check; no new numbers were added)

- 6.20: "Soft-RoCE is a software version of RDMA" (lab step 4 explainer). General knowledge.
- 6.20: "neocloud" definition; "TLS is the encryption layer that web sites use"; "data egress" definition; DNE described as "the Lustre feature that spreads metadata over several servers" (matches original's "DNE to scale out", explanation only).
- 6.20: "similarity-based reduction removes repeated or similar data across the whole system"; "wide erasure coding spreads each stripe across many pieces". Explanation of the original "global similarity-based reduction and wide erasure coding" bullet. Check against VAST documentation.
- 6.21: "Blackwell Decompression Engine is on-die" and "nvJPEG handles GPU image decoding" stay as in original; the new explanation "an on-die engine is built into the GPU chip itself" is general.
- 6.21: "a few thousand files per checkpoint" (describes file-per-rank at scale; no digit added). Check against DCP docs if quoted.
- 6.21: "CRAQ ... write-all, read-any" and "FUSE or native USRBIO client" kept from original; explanations of FUSE and USRBIO are general.
- 6.22: "statelite sits between stateless and stateful, with a few paths kept writable" (xCAT section). Check against xCAT docs before reuse.
- 6.22: "Commissioning means MAAS powers on a new machine and checks its hardware before it is ever deployed" (MAAS). Check against Canonical MAAS docs.
- 6.22: "Katello handles content and patch management, and Puppet keeps configuration in line" (Foreman). General knowledge.
- 6.22: "Redfish is the standard web API for managing servers through their BMCs"; "SR-IOV lets one network card share itself across several virtual functions"; "the shim is the small signed program that lets the firmware trust the rest of the boot chain". General knowledge; check against the Redfish and UEFI shim docs.
- 6.22: "LLDP (Link Layer Discovery Protocol) is how a switch learns what is plugged into each of its ports". General knowledge.

## Unresolved

1. Mermaid check and `npm run build` not run (lead instruction). Mermaid blocks unchanged, so no new risk expected.
2. EXTERNAL_EDITS.md not edited, per the lead instruction that overrides the procedure's step 6. Owner or Claude must add the row if the review step needs it.
3. 6.22 section 7 ROCKS and PelicanHPC walkthroughs: the old "(untested here)" tags were removed (rule 7). These steps come from the book and were not run here. Only the section 9 VM steps say "not run" in the body. Consider one more sentence above section 7 if the owner wants that status visible.
4. Residue counts are not zero: 6.20 has 2 (Sources section, unchanged by rule 5), 6.21 has 11 and 6.22 has 9 by the guard's own pattern count. Most are in Sources and checkpoint text kept by rule 5, or in the status rows. Not inspected line by line.
5. Some reader-facing explanations are longer than the original claims and go beyond the book text (see Needs source). Nothing new is numeric.
6. Section 10 (Interview angles) in 6.20 and 6.21 and the question list in 6.22 keep their original question wording. The openers were changed to a situation, but the questions themselves are not rewritten.
7. Section 3 of 6.22 ("A tested generator"): the rejection example and dnsmasq block are verbatim; the surrounding prose was expanded. The generator limit list ("naive" discovery pool arithmetic) is unchanged from the original.
8. No commit. Working tree shows the three chapter files modified and this ledger new.
