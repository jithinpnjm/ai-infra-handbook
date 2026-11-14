# Voice rewrite ledger: Part 12 chapters 12.7 to 12.9

Scope: body prose only. Front matter, the metadata table, headings, tables, code fences, Mermaid, display math lines, checkpoints and the Sources tail are byte-identical to HEAD. Working tree only, nothing committed. EXTERNAL_EDITS.md not touched (per run instructions).

Method: each chapter body was rewritten in a scratch draft with placeholders for every locked block (fence, table, display math). The locked blocks were copied from HEAD by script in original order, and the checkpoint and Sources tail was copied from HEAD by script. The script asserts that the placeholder count equals the locked block count (07: 36, 08: 39, 09: 33).

## Words (wc -w, whole file)

| File | Before | After | Growth |
|---|---|---|---|
| 07-infiniband-subnet-manager-routing-topologies-and-rails.md | 14430 | 18415 | +27.6% |
| 08-infiniband-adaptive-routing-and-congestion-control.md | 13547 | 17619 | +30.1% |
| 09-infiniband-diagnostics-ufm-and-operations.md | 15144 | 19252 | +27.1% |

## Gates (run, output seen)

- `tools/rewrite_guard.py HEAD WORKTREE <file>`: 0 hard failures for all three.
  - 07: new numbers 0, lost numbers 0, new code spans 0, lost 0.
  - 08: new numbers 0, lost numbers 0, new code spans 0, lost 0.
  - 09: new numbers 0, lost numbers 0, new code spans 0, lost 0 (after one fix; see Process notes).
- `tools/restore/chain_gate.py <file>`: 07 = 0.0 per 1000 words; 08 = 0.0; 09 = 0.1.
- Mandatory span check (HEAD vs worktree, fences removed): `{}` for 07, 08 and 09.
- Fence and table blocks: identical to HEAD by construction (copied from HEAD).
- `node tools/check_mermaid.mjs`: not run. Mermaid blocks are byte-identical to HEAD.
- `npm run build`: not run (instructed no npm build).

## Structure checks (done by hand against each chapter)

- Headings, heading order and front matter unchanged.
- Checkpoint and Sources tails unchanged (copied from HEAD).
- Exercises: 6 per chapter, same as original. Lab: one bash command per chapter, same as original. Exercise sub-parts (Part A/B) were turned into plain single-question sentences.
- Outcomes lists ("you will be able to") were rewritten as plain paragraphs in all three chapters. No "you will be able" or "should be able to" remains in body prose.
- Every H2 and H3 opens with a situation or a plain statement of the problem.
- Honest status: each chapter keeps one "not run" sentence above its lab or commands (07 lab, 08 expected output, 09 commands and lab).
- No exclamation marks in prose. No "my", "I read", "the book says" in prose.

## Process notes (what was fixed during the run)

- 07: first assembly came out at +21.7%; added explanation to reach +27.6%. Restored code spans `sminfo`, `ibtracert`, `smpquery`, `saquery`, `perfquery` dropped from the original prose.
- 08: first assembly +15.5%; added explanation to reach +30.1%. Restored span `perfquery`. Removed a "Volume 08" attribution from prose (it remains in a locked code comment).
- 09: first assembly +13.1%; added explanation to reach +27.1%. Restored the original multi-rail tip block (`-C` and `-P` spans). Removed two new numbers introduced in added prose ("99th", "twenty minutes" wording). Guard then showed 0 new numbers.
- Original 09 prose "from our operational archives" was reworded to "Three production incidents show why..." so no archive attribution is invented.

## Needs source (general explanations added in prose, not in the original)

07:
- Control plane vs data plane definitions.
- LID definition as a port address inside one subnet.
- GUID definition as a sixty-four-bit hardware identifier that does not change when a cable moves.
- Routing engine and radix definitions.
- Oversubscription plain-language definition.
- Deadlock definition as packets waiting on each other in a loop.
- Activity count as a counter that rises with each sweep.
- Linear Pluggable Optics description (simpler modules, short reach).
- Chassis switch description.
- NVSwitch, PCIe, DGX, NIC, rail and hop definitions in section 4.
- Single-rail and blast-radius plain-language explanations.
- Scalable Unit, Partition Key and Multi-Instance GPU (MIG) short definitions in section 5.
- RoCEv2 expansion (RDMA over routed Ethernet and UDP).
- Weighted packet spraying explanation.

08:
- Head-of-Line blocking plain-language definition.
- AllToAll description.
- PSN (Packet Sequence Number) role as a counter for one connection.
- Elephant flow description.
- ASIC definition.
- Arbitration definition.
- Scalable Unit definition (repeated from 07 wording).
- SHARP as an in-network reduction feature.
- Oscillation explanation for the asymmetric CCTI recovery.
- Microsecond explanation.
- NUMA expansion (non-uniform memory access).
- Window/deltas definition.

09:
- OpenFabrics Enterprise Distribution (OFED) and rdma-core and Mellanox Firmware Tools (MFT) short definitions in the intro (expansions are in the original Why section, but the rdma-core description is new).
- Forward Error Correction (FEC) definition.
- SERDES expansion (serializer and deserializer).
- Digital Diagnostic Monitoring (DDM) expansion and EEPROM description.
- Bit error rate (BER) plain-language definition.
- Performance Management Agent snapshot definition.
- GSI (General Services Interface) expansion used in the saquery paragraph.
- DRBD, Pacemaker, Corosync and floating Virtual IP descriptions in section 4.2.
- Gate definition as a yes-or-no check.
- Percentile plain-language definition.
- Fencing as a deliberate port-disable action.
- Stage definition for ibdiagnet.

All of the above are general explanations of standard terms. None adds a fact about a specific product, version or measurement. Each should be checked against the owner's preferred glossary before the next release.

## Unresolved

1. Locked headings and code-block comments still carry "(tested here)" or "(untested here)" text, and attributions such as "V8", "Volume 08", "ADC", "SCL Ch.", "Supercomputers for Linux Sysadmins", "Lab 02" and "Volume 08" in code, tables and headings. These are locked by the rewrite rules and were not removed. Needs an owner decision on heading and table text. Examples: 07 code comments and the Volume 08 comment in the oversubscription block; 08 heading "### Run the lab (tested here)"; 09 table headers and the Gate 2 and Gate 5 cells.
2. Math residue in locked tables: some `$...$` spans in table cells appear to pair across a backtick boundary. Found in 09 at the "Rate & Acceleration" row (`$\Delta C$` form), at the LID/LMC row (`$2^{\text{LMC}}$` form) and at the Port 1 SM LID row (`$3 \times 256$` form). Left exactly as written, not repaired. The rule applies to chapters 12.5 to 12.13.
3. Display math: 07 has one `$$` oversubscription formula, 08 has three `$$` formulas (C_avail, EgressPort, R_inj). They are byte-identical to HEAD. No stray backticks found in them.
4. 09 inline math `$\Delta t = t_1 - t_0$` in the 1.2 prose is kept as written, per the math rule.
5. 07 exercise 4 keeps the original numbers and parameters as written in the locked list text. The exercise list itself is rewritten in plain sentences.
6. 08 exercise and interview anchor block and 09 exercise reference table are locked. 09 exercises use the locked table as their input source, so the exercise prose is short but the table stays in its original (table) form.
7. Checkpoint tails (20 questions per chapter) and Sources sections were not edited. They keep the original "Volume" and "Author notes" text, per the locked-tail rule.
8. 08 "Common first mistakes" and the Interview answers are rewritten prose with the same claims and numbers as HEAD. Their numbers were checked by the guard (0 new numbers).
9. The `(untested here)` inline span in 07's lab paragraph and 09's commands intro is kept because the span check requires it. It sits in prose and is a status word, not drafting residue.
