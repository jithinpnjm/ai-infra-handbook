# Voice rewrite ledger: Part 12, chapters 12.13, 12.14, 12.15

Scope: `docs/part-12-ai-networking/13-*.md`, `14-*.md`, `15-*.md` only. Nothing committed. `planning/EXTERNAL_EDITS.md` not edited (per run instructions).

## Summary table

| Chapter | Words before | Words after | Growth | Guard (`rewrite_guard.py`) | Chain gate | Span check | Build |
|---|---|---|---|---|---|---|---|
| 12.13 fabric design (file 13) | 15068 | 19246 | +27.7% | 0 hard failures; new numbers 0; lost numbers 0; new spans 0; lost spans 0 | 0.0 | `{}` | not run (no npm build per run instructions) |
| 12.14 load balancing and routing (file 14) | 17223 | 21951 | +27.4% | 0 hard failures; new numbers 0; lost numbers 0; new spans 0; lost spans 0 | 0.0 | `{}` | not run |
| 12.15 NCCL collectives (file 15) | 13428 | 17111 | +27.4% | 0 hard failures; new numbers 0; lost numbers 0; new spans 0; lost spans 0 | 0.1 | `{}` | not run |

Guard residue: file 15 keeps `(untested here)` only inside locked headings (`### 1.` and `### 2.` in Commands, and `### Step 2`). These are headings, not prose, so the guard counts them unchanged (4 -> 4). File 13 and 14 residue went to 0 (14 went 3 -> 0).

Honest status sentence per chapter (one per chapter, placed above the lab):
- 13: "These steps were not run on a live cluster."
- 14: "The switch commands in this chapter were not run on live switch hardware."
- 15: "This step needs live GPUs, so it has not been run in this build." (Step 2, original line kept.)

## Method notes

- Body rewritten section by section. Tables, code blocks, Mermaid, `:::info` admonition, front matter, headings, checkpoint blocks, and the Sources section are unchanged. The checkpoint and Sources tails (from `## Checkpoint questions` to end of file) were appended byte-for-byte from `git show HEAD`.
- Outcome lists ("you will be able to ...") were rewritten as short plain paragraphs. The outcome tables were kept.
- Exercises were kept at the original counts (13: 6, 14: 6, 15: 6). Multi-part asks were split into short single-question sentences. `(a)`/`(b)` nesting was removed.
- Lab steps were kept at the original counts and commands. Step lists were turned into prose ("First", "Next", "Finally") so no new numbered items were added.
- Figure references kept as in the original (for example "Figure 8-9" in 14 section 3.5). They are source labels, not `Volume N`, and changing them would drop number tokens. See Unresolved.
- Chain gate: no `; the/every/each/a/an` chains were introduced.
- Numbers: no new digit tokens in any of the three files (guard `new numbers 0`). A stray "section 5.1" introduced in file 15 was removed.
- Residue: "the book" attributions in 14 section 4.6 were replaced ("The design pairs...", "The example here uses..."). "I" and "we" appear only in locked table or question text.

## Needs source (general explanations added in prose)

These are explanations of general networking or ML terms added to the body. None introduces a new fact or number, but each should be checked against a primary source before publication.

Chapter 12.13:
- Bisection cut: definition as "links crossed to split the cluster into two equal halves".
- Oversubscription as the ratio of server-facing to spine-facing capacity.
- Clos as "every leaf links to every spine" (common name for layered leaf-spine).
- Virtual Lanes as logical lanes sharing one physical link.
- Direct Attach Copper (DAC) and Active Electrical Cable (AEC) short definitions.
- Head-of-line blocking definition; cell spraying and reassembly description.
- Serialization latency; network diameter as longest shortest path in hops.
- Adversarial traffic and non-minimal path wording (Dragonfly).
- Torus deadlock as a standstill loop.
- Ceiling-function explanation for cell padding.
- Multi-Planar: queue pair meaning for the application view; completion signal wording.
- Bridging loop; underlay and ACL definitions.
- DSP as the module's signal processor.
- Prefill and decode definitions (5.1); KV cache and point of presence.
- Service level agreement and multi-tenancy boundary definitions (5.2); scaling-efficiency curve; OpenSM and out-of-band management definitions.
- Recable definition; PDU definition; link flap definition.
- Hot-pocket / airflow analogy; cold aisle and ASIC definitions.

Chapter 12.14:
- Entropy as header variety; elephant and mice flow explanation; microburst definition.
- Next-hop group explanation; control plane vs data plane analogy.
- XOR symmetry explanation; CRC as checksum-style hash; Weighted ECMP explanation.
- Flowlet timer threshold explanation; microkernel description.
- Convergence definition; blackhole definition.
- Adversarial pattern and Dragonfly non-minimal path explanation.
- Goodput definition; PSN and Go-Back-N explanation; ASN and draft/IETF working document wording.
- K-store as a key-value table; longest prefix match; IRB definition; VNI definition.
- Anycast definition; SRH and SID definitions; train analogy for uSID shift.
- Link State PDU definition; Flex Algo planes wording.
- Overlay and equal-weight ECMP wording; route reflector multipath reflection wording.

Chapter 12.15:
- Pronunciation and MFU definition; MFU caveat (slow kernels, batch size).
- SIMT / warp / thread definitions; SM definition; HBM definition.
- Critical-path definition.
- Ring "each GPU passes data to its right-hand neighbor".
- In-place versus out-of-place buffers explanation; AllToAll separate buffer reason.
- Full-duplex and leaf idle explanation for binary tree.
- GEMM definition; caching allocator and fragmentation explanation.
- Atomic store explanation; framing efficiency definition; flag polling wording.
- Autograd and hook definitions; wait-free backpropagation ordering reason.
- Oversubscription at ingress ports; hot spot definition; multicast replication wording.
- Time-to-first-token definition; KV cache definition; UCX wording; NIXL busy-wait comment.
- Watchdog timer definition.
- Silent NCCL fallback statement ("the run still finishes").

## Unresolved

1. Math with `$...$`, `$$...$$` and `$\times$` / `$\rightarrow$` in table cells (12.13 sections 1.3, 6.1; 12.14 section 4.4 table; 12.15 section 2.2 formula line and the Ring and Tree tables). Left exactly as written per instructions. No stray backticks inside math spans were found, so nothing was repaired.
2. Source inconsistencies kept, not fixed (the source is the owner's): 12.13 maximum cable span MoR "To span `6` racks (`5`–`6` racks)"; 12.14 interview answer 3 describes IS-IS as "pure Layer-2 link-state security" while the 4.2 table says it runs over Layer 2 and carries IP; 12.14 "Sprayed liquid cooling 25.8%" is kept without a source check.
3. Figure labels (`Figure 8-9`..`8-24`, `Figure 6-x`) remain in 12.14 prose, since they are source references, and removing them would drop number tokens. Owner to decide whether to keep them as borrowed labels.
4. "Meta's 54-day pretraining study" and vendor attributions (Microsoft, Google, NVIDIA Dynamo speedups) in the original are kept as written. They were not verified in this run.
5. Lab counts were not re-run in this run (companion code not executed). The 28-check (13), 25-check (14), and 29-check (15) summary lines are the original text.
6. Build (`npm run build`), Mermaid check, and language audit were not run (run instructions specified no npm build).
7. Original Mermaid labels (for example "Cools 12W/15W Optics" in 12.13) were kept unchanged, since Mermaid is locked.
