# Voice rewrite, Part 9 chapters 10, 11, 12 (ledger)

Scope: docs/part-09-nvidia-systems/10-basepod-and-smaller-deployments.md, 11-power-delivery-thermal-design-and-liquid-cooling.md, 12-software-stack-and-management-in-an-ai-factory.md. Not committed. EXTERNAL_EDITS.md not edited (per run instructions).

## Words (wc, full file incl. locked tail)
| File | Before | After | Growth |
|---|---|---|---|
| 10-basepod-and-smaller-deployments.md | 7403 | 11539 | +56% (over the 25-40% band; no text removed) |
| 11-power-delivery-thermal-design-and-liquid-cooling.md | 8904 | 12501 | +40% |
| 12-software-stack-and-management-in-an-ai-factory.md | 6454 | 9144 | +42% (slightly over band) |

## Gates
- Span check (`git show HEAD:` vs worktree, code spans outside fences): `{}` for all three (after restoring one lost `torchrun` span in ch12).
- `tools/rewrite_guard.py HEAD WORKTREE <file>`: 0 hard failures on all three. Ch10: new numbers 0, lost numbers 0. Ch11: new numbers 0 after removing a restated "22.5 kW" from prose. Ch12: new numbers 0 after rewording a "Section 3.2" cross-reference. The "lost code spans" lines are the pairing artifact the owner warned about; the span check is the authority.
- `tools/restore/chain_gate.py`: ch10 0.1, ch11 0.1, ch12 0.0 (target <=0.2 met).
- `node tools/check_mermaid.mjs`: 776 diagrams, 0 failed. `npm run build` not run (task said no npm build).
- Locked tail verified identical to HEAD (from "## Checkpoint questions" to end) for all three: 20 checkpoints each.
- Code blocks identical to HEAD for all three (count matches).
- Tables: no table row removed. One separator row in ch11 optics table restored to original.
- Exercises: 6 numbered items per chapter (same as HEAD). Multi-part items split into one-question sentences inside the same item.

## Structure checks
- Every section opens with a situation (picture a team / a researcher / an executive).
- Outcomes lists rewritten as plain paragraphs in ch10, ch11, ch12. No "you will be able to" or "should be able to" in body.
- Honest status: status row kept; one sentence above commands/lab per chapter ("These steps were not run on a live ..."; ch11: "The hardware commands were not run on live DGX hardware").
- Residue removed from body: "Expected output verified" (now "when the lab passes in this repository"), "(untested here)"-style lines, "authoring environment" wording in body (kept in Sources only). No first-person claims in body. No "the book says" or "Volume N" in body.
- No new redundancy claims in ch11 (PSU section explains 3+3 and 5-of-6 only; no N+1 wording added).
- Typo fixed in ch11 ("immediately,.").

## Needs source (general explanations added, not in the original text)
Ch10:
- Token is roughly a word or part of a word.
- NVSwitch is the switch chip on the node baseboard linking GPUs.
- Slurm and Kubernetes are the schedulers that place jobs.
- Blanking panel, spine/leaf/fat-tree roles, rail definition, NIC meaning.
- Redfish as the standard remote hardware-management interface.
- LLDP, PFC pause storm, QoS, ib_write_bw style terms.
- Fine-tuning, pre-training, adapters, LoRA meaning; Series B meaning.
- MFU, exposed communication overhead, MTTR, checkpoint meaning; FP8 as 8-bit format.
- Persistence of MIG/MPS fault-isolation reasoning (explained from table, not new facts).
Ch11:
- C19/C20 plug types; locking outlets; SNMP as older monitoring protocol.
- Power factor meaning; whip meaning; sqrt(3) three-phase reasoning.
- Substation role; colocation facility meaning; raised floor; reinforced slab; rigging rating.
- Volumetric heat capacity, latent heat, dielectric meaning, single/two-phase definitions, evaporative tower behavior.
- Static pressure; OEM and HGX meanings; manifold and dripless quick-disconnect meanings.
- Heat flux; E1.S and M.2 meaning; drip pan and manifold trench.
- Glycol and biocide roles.
- GPUDirect Storage explanation; parallel file system explanation.
- Concurrent maintainability meaning; Uptime Institute reference is the original text.
- Heat balance formula meaning; warm-water design explanation.
Ch12:
- NCCL as the NVIDIA collective communication library.
- Pod and Job definitions; bare-metal definition.
- Subnet manager and NVLink switch manager roles; rank and gang scheduling definitions.
- SHARP and SHIELD explanations; CMDaemon definition; draining/cordoning definitions.
- NGC container definition; digest meaning; communicator meaning.
- Forward-compatibility package behavior; PIX meaning; MoE and fragmentation definitions.
- Memory_reserved vs allocated explanation; CUDA Graph and pipelining definitions.
- DLPack open-standard description; FSDP as PyTorch's sharding; ZeRO naming.
- Headless Service per-pod DNS behavior; anti-affinity meaning; Pending state.
- DCGM, Tensor Core and warp definitions; P99, KV cache, TTFT/ITL meaning.
- Runbook annotation and for: meaning; playbook cordon/drain meaning.

## Unresolved
1. Word growth: ch10 is +56% (band is 25-40%). Growth is explanation only; I did not trim because the rule says never trim. Owner decision whether to accept or trim explanations.
2. Ch12 is +42%, ch11 +40%: at or slightly above band.
3. (Resolved) An unsourced "thinner than a human hair" comparison was removed from ch11.
4. Ch11 and ch12 contain existing internal inconsistencies from the original, left unchanged because they are locked facts: GB200 power is "about 130 kW" in some places and "120 to 130 kW" range was dropped in Sources notes; ch11 Sources notes mention "6 to make 5" style; ch12 `dcgm-exporter` 4.8.x vs 4.9.0 note retained with its cross-chapter link (../part-17-operations/04-dcgm-exporter-and-interpreting-gpu-metrics.md) not verified in this run.
5. Ch12 exercise and body reference "Section 5.2" and "section 6.1" of Chapter 9.8 as in original.
6. ch11 checkpoint 18 still names "the author's illustrative estimate" (locked checkpoint answer). Left as is.
7. Ch10 "Expected output" block contains "V21 Ch13" etc. labels: locked lab output, left as is.
