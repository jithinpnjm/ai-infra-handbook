# Voice rewrite ledger: Part 12 chapters 04, 05, 06

Scope: docs/part-12-ai-networking/04-pfc-ecn-and-dcqcn-in-depth.md, 05-data-center-bridging-and-qos-for-ai.md, 06-infiniband-fundamentals-and-addressing.md. Not committed. EXTERNAL_EDITS.md not edited (per run instructions). Other chapters in the directory were edited by other agents and were not touched.

## Results (wc -w, git HEAD vs worktree)

| Chapter | Before | After | Growth | Guard (rewrite_guard.py) | Chain gate | Span check |
|---|---|---|---|---|---|---|
| 04 PFC, ECN and DCQCN | 12506 | 15957 | +27.6% | 0 hard failures, new numbers 0, lost numbers 0, new code spans 0 | 0.0 | {} |
| 05 DCB and QoS | 12901 | 16421 | +27.3% | 0 hard failures, new numbers 0, lost numbers 0, new code spans 0 | 0.0 | {} |
| 06 InfiniBand fundamentals | 14444 | 18513 | +28.2% | 0 hard failures, new numbers 0, lost numbers 0, new code spans 0 | 0.1 per 1000 words | {} |

Mermaid: `node tools/check_mermaid.mjs` on each file reports "checked 3 diagrams, 0 failed". npm build not run (run instructions say no build).

## Method notes

- Rewrites were applied as paragraph-level replacements against HEAD. Code fences, tables, headings, front matter, checkpoints, exercise code blocks and Sources were left unchanged.
- Exercises keep their count (6 per chapter). Each exercise was split into single-question sentences. Commands and function names were kept.
- Outcomes lists were rewritten as one plain paragraph in each chapter. No "you will be able to" or "should be able to" lines remain.
- Every section opens with a situation (a port, a job, a checkpoint, a ticket), apart from locked headings, which are followed by a situation sentence.
- Analogies used with no new numbers: PFC as a pause-on-red light per lane, ECN as a road warning sign, WRED as a shop discount sign, the Subnet Manager as a traffic authority, the partition as a guest list, the DCB contract as house rules, the relay race for synchronized collectives.

## Needs source (general explanations added, no attribution made)

- 04: Go-Back-N resends from the lost packet onward. Incast definition. The Clos "layered leaf and spine" description. The DSCP definition. The BGP keepalive definition. Hysteresis as a thermostat dead band. The relay-race picture of CP/NP/RP. Exponential weighted moving average description. The claim that a link trained to one lane gets one quarter of design speed is from the original; the wording around it is new.
- 05: Deficit Weighted Round Robin description. Work-conserving explanation. ACL and VTEP definitions. BlueField DPU as a network card with its own processor. NUMA locality definition. Credit-based flow control as proactive permission. The statement that a drain takes a link out of service without dropping traffic. The claim that the RoCE lane never drops for buffer overflow is original and not re-verified.
- 06: OFED expansion (OpenFabrics Enterprise Distribution). CRC as a checksum for detecting corrupted bits. Definition of a Global Identifier as a mailing address. Passive Subnet Manager failover description. Benefit of connected mode is kept from the original. The "switch with no forwarding table" analogy.

No book was named in any new sentence. The gem book title appears only where the original already attributed the claim.

## Unresolved

1. Honest-status conflict. Rule 7 asks for one "untested" or "not run" word per chapter, and it asks that "(untested here)" be removed from body text. The mandatory span check also requires every backticked span to be kept. In 04 and 05 I kept the body spans. In 06 the span appears in locked headings (for example "### 1. Local HCA ... `(untested here)`") and in body text. The guard reports residue 2->2 for 04 and 05, and 8->8 for 06. The span check cannot be satisfied with a different count, so these spans remain. Owner decision needed.
2. Locked labels that still read "tested here" or "not verified". 05 body label "Expected output (tested here)" was changed to "Expected output from the simulator". 06 heading "Run the lab (tested here)" is locked and was left unchanged. 04 keeps "Not verified on live hardware" inside the locked Sources section.
3. Math formulas. A grep for `$...$` spans that contain a backtick found no matches inside formulas in these three chapters. Table rows that contain `$` and separate code spans on the same line were left unchanged, as the instructions require. The open 12.5 to 12.13 formula issue does not apply to these files.
4. Facts in the original that were not re-verified in this run. Examples: the 04 PFC pause and headroom figures, the 05 ETS table numbers, and the 06 LID and GID examples. They are unchanged. The lab outputs in the chapters are simulator results, and the live-hardware commands were not run (marked untested).
5. Interview angles in 04, 05 and 06 keep their original "Strong answer" bullets. Only the intro was rewritten.
