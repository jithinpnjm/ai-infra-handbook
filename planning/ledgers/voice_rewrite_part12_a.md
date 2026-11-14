# Voice rewrite ledger: Part 12 chapters 12.1 to 12.3

Scope: body prose only. Front matter, headings, tables, code fences, Mermaid, checkpoints and the Sources tail are kept byte-identical to HEAD. Working tree only, nothing committed.

## Words (wc -w, whole file)

| File | Before | After | Growth |
|---|---|---|---|
| 01-ai-traffic-collectives-incast-and-elephant-flows.md | 16434 | 21211 | +29.1% |
| 02-rdma-fundamentals-verbs-queue-pairs-and-memory-registration.md | 15477 | 19881 | +28.5% |
| 03-rocev2-transport-and-congestion-management.md | 13510 | 17209 | +27.4% |

## Gates (run, output seen)

- `tools/rewrite_guard.py HEAD WORKTREE`: 0 hard failures for all three. New numbers 0, lost numbers 0, new code spans 0, lost spans 0.
- `tools/restore/chain_gate.py`: 12.1 = 0.1 per 1000 words; 12.2 = 0.1; 12.3 = 0.0.
- Mandatory span check (`git show HEAD` vs worktree, code fences removed): `{}` for all three.
- Fence check: fenced code blocks identical to HEAD for all three (26, 29, 19 blocks).
- `node tools/check_mermaid.mjs` and `npm run build`: not run (instructed no npm build; Mermaid blocks are unchanged from HEAD).

## Residue scan (prose lines only, outside code and headings)

- No "you will be able", "should be able to", "the book says", "my summary", "I read", or exclamation marks in body prose.
- One honest status sentence per chapter above the lab or commands ("were not run on a live cluster" / "were not run here").
- Remaining "untested here" and "tested here" strings sit in headings and code-block comments only (locked). See Unresolved.

## Needs source (general explanations added in prose, not in the original)

- 12.1: SHARP expansion (Scalable Hierarchical Aggregation and Reduction Protocol); Global Interpreter Lock behaviour; DPU definition; "logarithmic growth roughly one step per doubling"; mixture-of-experts routing description; "measure with nccl-tests at a few message sizes" advice.
- 12.2: NUMA expansion; OFED expansion (OpenFabrics Enterprise Distribution); MSI-X description; OpenSM and UFM roles; Partition Key as a grouping tag; ICRC behaviour (receiver discards a packet that fails the check without acknowledging it); "a deregistered MR revokes its keys" statement; per-lane explanation of 4x and 12x links; "Virtual Lanes" description; Interconnect Context Memory explanation.
- 12.3: IEEE 802.1Q expansion and VLAN-tag explanation; rdma-core description; SR-IOV Virtual Function description; BER definition; hash polarization definition; NIC buffer memory requirement for Selective Repeat; "don't-fragment ping" MTU test; statement that CSIG is a draft and details may change.

## Unresolved

1. `(untested here)` and `(tested here)` remain in headings and code-block comments in all three chapters. Headings and code blocks are locked by the rewrite rules, so these were not removed. Needs an owner decision on heading text.
2. Formula residue: 12.1 has `$...$` formulas (ring AllReduce steps, volume ratio, SHARP table cells and the JCT and serial/ideal overlap formulas). Left exactly as written per instruction; not repaired.
3. Table residue kept (tables locked): 12.1 Transmission-speed row has "The book rates it as slower than Ethernet." and the Pipeline row says "book also notes ring-style layer passing". 12.1 code block headings cite "ADC" and "ASP". 12.3 code block cites "Volume 09" and "Volume 06" labels. These are attributions inside locked tables and code, not prose.
4. Exercise 6 in 12.1 keeps the written input `size_two_tier_nonblocking_fattree(128. 8, 64)` exactly as in the original (possible typo, not changed).
5. Chapter 12.1 checkpoint and Sources tails are unchanged, including any "Volume" text there.
6. 12.2 Sources section still lists "Corrections to the author's notes" (locked tail).
7. The planning/EXTERNAL_EDITS.md line was intentionally not added (instruction step 6 excluded).
