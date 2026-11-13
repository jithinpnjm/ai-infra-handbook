# Voice rewrite ledger: Part 9, chapters 9.4 to 9.6 (batch b)

Scope: `docs/part-09-nvidia-systems/04-grace-cpu-gh200-and-gb200-superchips.md`, `05-gb200-and-gb300-nvl72-rack-scale-systems.md`, `06-dgx-superpod-concepts-scalable-units-fabrics-and-tiers.md`. Rulebook: `planning/HAIKU_REWRITE_INSTRUCTIONS.md` sections 0 to 3 (step 6 on EXTERNAL_EDITS.md skipped by instruction). Not committed.

## Results per chapter

| Chapter | Words before (wc) | Words after (wc) | Growth | rewrite_guard (hard fails / new numbers / new spans / lost) | chain_gate | Span check (`{}`) | Mermaid |
|---|---|---|---|---|---|---|---|
| 9.4 Grace CPU, GH200, GB200 | 8220 | 11360 | +38.2% | 0 / 0 / 0 / 0 | 0.0 | `{}` | part of repo-wide run, see below |
| 9.5 GB200 and GB300 NVL72 | 9349 | 12463 | +33.3% | 0 / 0 / 0 / 0 | 0.2 | `{}` | part of repo-wide run |
| 9.6 DGX SuperPOD concepts | 8049 | 11232 | +39.5% | 0 / 0 / 0 / 0 | 0.0 | `{}` | part of repo-wide run |

Guard word column (its own base, code and front matter excluded): 7320 to 10460, 8186 to 11300, 6699 to 9882.

`node tools/check_mermaid.mjs`: checked 776 diagrams, 0 failed (repo-wide, run after the three rewrites).
`npm run build` was not run (lead instruction: no npm build).

## Structural checks (all three chapters)

- Headings: identical to HEAD (same text and order).
- Front matter: identical.
- Code blocks (including Mermaid): identical, 12 / 13 / 12 blocks.
- Table rows: identical, 77 / 93 / 50 rows.
- Checkpoint block: identical tail from `## Checkpoint questions (20)` to end of file, 20 `<details>` each. Sources and review notes identical.
- Exercises: 6 each, same count as original. Each item split into short sentences; no (a)(b) nesting.
- Outcomes lists rewritten as one plain paragraph (no "you will be able to").
- Honest status: status row keeps **untested** (table, locked). One "were not run" sentence above each lab/commands block.

## Changes of substance

- Each `##` section and most `###` sections open with a situation (an engineer, a crew, a technician, a planner).
- Terms defined once at first use (HBM, PCIe, DIMM, ECC, TLB, ATS, NVMe, SKU, MIG, DPU, BMC, TDP, FSDP, AllGather/ReduceScatter, LACP, DAC, ToR, PUE, POSIX, and others).
- Corpus wording in the ch04 info box rewritten in plain words ("the books cited in the Sources section").
- ch05 Exercise 6 pointed to "Section 4 table" in the original; the comparison table is in Section 5, so the cross-reference now says Section 5. This is a cross-reference fix, no spec changed.
- ch04 `wait` (shell keyword) kept as plain prose, not a new code span.
- No hardware number, spec, flag or command was changed or added. Guard "new numbers" was 1 in ch04 (a "99th" percentile phrase) and 1 in ch06 (a "section 4.2" reference); both were removed.

## Needs source (general explanations added in prose, not in the original sources)

Add or verify before publishing; these are definitions and general mechanics, not new specifications.

ch04 (9.4):
- Arm Neoverse V2 described as a CPU core design from Arm; LPDDR5X as a low-power server memory standard.
- NVLink-C2C expanded as "chip-to-chip"; die-to-die and coherence meaning; single virtual address space meaning.
- HBM, PCIe, DDR5, x86 (instruction set family shared by Intel and AMD), DIMM, ECC, pinned buffer, picojoule, NVMe, SKU, CUDA graph, CUDA kernel, CUDA stream, page table, TLB, DMA, ATS.
- Tokenizer and data loader roles; Arm SVE register meaning (vector and predicate).
- "A mixture-of-experts model activates only a few experts for each token, so the rest of its weights wait in host memory."
- Prefetching as copying data before the kernel runs; NUMA expanded as non-uniform memory access.
- Nsight Systems described as NVIDIA's profiler; P99 ITL as a tail-latency measure; THP compaction as background merging that can pause a process.
- ZeRO-Offload as a method that moves optimizer work to host memory; gradient reduction and NaN/Inf check meanings; first and second Adam moments as running averages; type cast meaning.
- "Speculate" and "roll back" meanings in STV.

ch05 (9.5):
- SRE expanded as site reliability engineer; rack unit (RU) as standard height measure; 1U tray as one unit tall.
- MGX as a modular server architecture; retimer as a signal-cleaning chip; copper run; passive backplane.
- Blind-mate connector; quick-disconnect coupling; cold plate; CDU role; evaporative tower; raised floor and slab meaning; first-pass sizing meaning.
- DPU expanded as data processing unit; RDMA and NVMe over Fabrics expanded; line-rate; multitenancy; clock cap; MIG isolation as hardware separation.
- COMe as a standard module form factor; RJ45 as the common Ethernet jack; out-of-band as a separate management network.
- N-redundant meaning; capacitor role in covering short surges; busbar meaning; three-phase as standard large-building supply; AC and DC roles.
- TDP as the heat and power budget the vendor plans for; allocation versus maximum distinction.
- Crossbar, collective engine, multicast, AllToAll, AllReduce description, NCCL as the collective library, NMX-M analogy to UFM, partition meaning.
- Time to first token and decode throughput definitions; vendor-result caveat.
- East-west traffic definition; failure domain, NVLink plane, IMEX purpose, memory mapping meaning, runbook meaning.
- DCGM as the monitoring tool; goodput and depreciation definitions; plugin as a scheduler add-on.
- Rule of thumb in 8.2 that a clock cap lowers speed and power draw.

ch06 (9.6):
- MTTR and active-active definitions; blocking ratio and non-blocking definitions; policy routing; link training; attenuation; symmetric routing; heartbeat and why a missed one marks a node failed.
- FSDP expanded; AllGather and ReduceScatter meanings; rank; gradient bucket; asynchronous call.
- RoCEv2 as RDMA over Ethernet; lossless meaning; pause storm; credit-based flow control; SHARP as in-network reduction; ECN and PFC expanded; POSIX; GPUDirect Storage as direct-to-GPU storage path; parallel file system meaning.
- LACP as the bonding protocol; ToR and DAC expanded; ISL meaning; oversubscription meaning.
- Metadata storm; atomic rename; SHA-256 as a checksum; fragmentation; bare metal; eBGP as the cluster-to-building routing protocol; cordon as "mark unschedulable".
- "Chatty" traffic as frequent small exchanges.
- Scaling of the NVL72 two-layer design: traffic between two leaves climbs to the spine and returns (rewritten to avoid a stage count).
- The statement that the Nth GPU or NIC of every node connects to the same leaf family (rail-aligned meaning).
- PUE expanded as power usage effectiveness.
- The checkpoint "two-stage" meaning and the rule that gradients are not saved in the checkpoint (this follows from the source arithmetic, but the rule itself is a general mechanism).

## Residue left on purpose (locked by rules)

- Code blocks and tables still contain "(my inference ...)" and "Volume 04 Chapter 7" (ch04 code block), and "V21 Ch 1-4", "V4 Ch 7", "V5/V6" attributions in table cells (ch04, ch05, ch06). These are inside locked code blocks or table rows, so they were not changed. Owner decision needed.
- Table cells in ch04 and ch06 name the "nvidia-devops" volumes and "Distributed AI Systems" as source columns (locked).
- Sources and review notes sections still contain "my own choices", "Run here", "authoring environment" phrasing (locked tail).

## Unresolved

1. GB300 Grace memory figure: ch05 still states 17 TB (36 x 480 GB) and notes the 18 TB alternative. Open factual issue per lead; no figure changed.
2. The ch04 "Grace CPU Superchip" and "GH200" memory tables keep the original figures; no re-verification done.
3. Word growth on ch04 (+38.2%) and ch06 (+39.5%) is close to the 40 percent ceiling, ch05 is at +33.3%.
4. `npm run build` not run (lead instruction).
5. EXTERNAL_EDITS.md not edited (lead instruction).
6. Subsection openers that were table intros got one situational sentence each; a reviewer may want to read them in context.
