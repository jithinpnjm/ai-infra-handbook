# Voice rewrite ledger: Part 12, chapters 22-24 (run h)

Scope: docs/part-12-ai-networking/22-ai-network-telemetry-and-kpis.md, 23-fabric-validation-and-capacity-planning.md, 24-ai-networking-troubleshooting-playbook.md. Not committed. EXTERNAL_EDITS.md not touched (per run instructions).

## Word counts (wc -w, whole file)

| Chapter | Before | After | Growth |
|---|---|---|---|
| 22 AI network telemetry and KPIs | 13969 | 17919 | +28.3% |
| 23 Fabric validation and capacity planning | 11446 | 14719 | +28.6% |
| 24 AI networking troubleshooting playbook | 13893 | 17814 | +28.2% |

Locked tail (checkpoints and Sources) kept byte-identical. Code fences, tables, Mermaid blocks and front matter kept verbatim (assembled from HEAD units).

## Gates (run after the final edit)

- rewrite_guard HEAD WORKTREE: 0 hard failures on all three. New numbers 0, lost numbers 0, new code spans 0, lost 0.
- chain_gate: 0.0 per 1000 words on all three (target 0.2 or lower).
- Inline code span check (HEAD vs worktree, prose only): empty dict on all three.
- Headings: identical sequence to HEAD on all three.
- check_mermaid.mjs on the three files: 4 diagrams, 0 failed. npm build not run (per run instructions).
- Residue scan: no "you will be able", "should be able", "the book says", "Volume N" in prose. Status sentence kept once above the lab in ch22 ("These steps were not run on a live cluster") and once in ch23 Commands intro ("not run on live hardware"). ch24 lab paragraph says the hardware commands were not run.

## Needs source (general explanations added in prose, not from the original text)

Ch22:
- Mirror-on-Drop copies packets the switch discards; DCGM as NVIDIA's data center GPU manager.
- Streaming gNMI and TWAMP definitions; NUMA definition; flow entropy meaning; incast tree wording.
- Bisection bandwidth definition; Clos and oversubscription explanations (downlinks versus uplinks).
- Continuous-benchmark rhythm advice and the "telemetry is a camera, capacity is the road" analogy (analogy only).

Ch23:
- GUID versus LID explanation; breakout-port definition; LFT (linear forwarding table) definition.
- Slurm topology-file behaviour (keeps communicating ranks close); UFM and OpenSM roles; BGP, EVPN and NetQ roles.
- DPU, HCA, out-of-band management, field spare, reach derating, blast radius, SLA and canary definitions.
- Bus bandwidth as the NCCL figure that compares a collective to link speed.

Ch24:
- NDR as the 400 Gb/s InfiniBand generation; GID as the RoCE port address; RTR as the Queue Pair state before sending.
- DAC (direct-attach copper) definition; IOMMU and DMAR wording; LnkCap versus LnkSta reading.
- Xid as the numbered NVIDIA driver error code; RMA definition; "single-bit ECC" as corrected memory errors.
- MIG intent for disabling peer-to-peer; the "profiler Heisenbug" naming; RDMA Write definition.

## Unresolved (left as written, not repaired)

- Ch22, checkpoint answers (locked tail): four prose lines use `$...$` math with stray backticks in the answers (scaling, residence time). Left exactly as written, per rule for math formulas. Not edited.
- Ch22 and ch23 Sources (locked tail) keep "Volume 08" and similar residue labels in the source notes. Not body prose, left as written.
- Ch24 table row "Conditional Python bug (`if rank != 0`)" contains `!=`. Table kept verbatim, so the exclamation-mark rule is not applied to table cells.
- Ch24 dcgm-exporter 4.9.0 blockquote kept verbatim (original text and link to Part 17).
- Tables and fenced blocks are unchanged, so their dense jargon remains. Growth comes from prose around them.
- Interview "Strong answer" wording was rewritten; the questions are unchanged.
