# Opus review report, set 2: Parts 10 to 20 (214 chapters)

Reviewer scope: digest_2.md for all 214 chapters, readability metrics computed on the live files, pattern counts across all 214 files, and full reads of 12 chapters (10.8, 11.24, 12.23, 13.6, 14.11, 15.3, 16.7, 17.4, 18.5, 19.5, 19.14, 20.18), with 13.7, 15.16 and 19.4 opened where a question came up. Some digest observations are already stale because rewrite workers are active: 17.1 and 11.13 no longer open with "Read the diagram" or a meta table, and the 15.7/15.8 exercise garbling in the digest is not in the current files. Everything marked ERR below was checked against the current file.

Size context. Parts 10 to 20 hold about 2.14 million words: Part 12 alone is 352k words in 24 chapters (14.6k average), Part 15 248k, Part 11 282k, Part 20 286k. Part 18 is 44k words for all of security. Length is now a reader problem in its own right: 25 chapters exceed 12k words, and four exceed 19k (12.21, 15.12, 15.13, 17.9 plus 12.14 at 17k).

---

## 1. Verdict per part

**Part 10, GPU and CUDA (22 chapters).** Technically the deepest part of the set and the one closest to the gem book it leans on, but it reads like a migration of source notes, not a book. Every chapter carries the provenance apparatus in reader text: "(untested here)" on almost every command (896 occurrences across Parts 10 to 15 and 19), "V16 Ch 3" inside tables, lab output and checkpoint answers, a "Corrections to the author's notes" section, a MIGRATION_MAP file list, and section 5.5 of 10.8 that compares disagreements between source notes. Correctness risk is real: 10.8 states two wrong mechanisms (persistence mode, PyTorch preallocation) that a Senior SRE interviewer would catch at once. The ramp is poor for a DevOps reader: 10.11 to 10.18 are eight chapters of CUDA kernel programming (warp specialisation, thread block clusters, device-initiated graphs) that an SRE will rarely need, while operational chapters (10.8, 10.9, 10.21, 10.22) are where the interview is. Redundancy: occupancy math in 10.2 and 10.14; streams in 10.12 and 10.17; profiling in 10.20, 14.8, 15.13 and 17.5; DCGM/Xid in 10.8, 10.21, 11.24, 17.4 and 19.6; torch.compile in 10.19 and 14.9. Gaps: NCCL-hang-looks-like-100%-util, SM_ACTIVE vs GPU_UTIL as the right utilisation metric, GPU reset and driver reload procedure, clock-event-reason naming change.

**Part 11, GPUs on Kubernetes (34 chapters).** The most readable of the deep parts: short sentences (asl 14 to 16), few parentheses, scenario openings. Its voice problem is the formula: 100 files across the set open with "Picture ...", and Part 11 is where it is densest; "Read each row from left to right" and "Work through the six exercises below" recur as boilerplate. Depth is solid on device plugin, CDI, GPU Operator, DRA and scheduling. Correctness risk is moderate: 11.24 (MIG) has an impossible profile combination and a wrong driver/CUDA pairing. Off-topic paragraphs survive from source migration (11.9 has a RAG paragraph in a JobSet chapter; 11.11 has fio storage tests in a Network Operator chapter). Redundancy is the main structural cost: six KAI chapters (11.13 to 11.18) plus Run:ai (11.19) plus the AI-factory stack (11.31) plus three NVKE chapters (11.32 to 11.34) is ten chapters of NVIDIA-specific scheduler and platform material, much of it about products with thin public documentation. Sharing (11.21 to 11.26) duplicates Part 18's 18.5. Gap: GKE-native GPU paths (gpu-partition-size, GKE-managed driver and device plugin) are thin despite GKE being the lab venue.

**Part 12, AI networking (24 chapters).** Deep and mostly correct on RDMA, RoCEv2, PFC/ECN/DCQCN, InfiniBand, NCCL and fabric design; the arithmetic I checked (Clos BOM, bottleneck cut, N-1) is right. It is also the least readable part of the book. Chapters average 14.6k words; explanations live inside ```text blocks crammed with counters; numbers are printed twice by a formatting pass ("4:1 / 4.00:1", "40.0 ms (40 ms)", "rx_packets: 1024567 (1,024,567)"); and 17 files contain LaTeX inside backticks that renders as raw TeX (142 hits, e.g. `\rightarrow` in table cells, `G_{\max} = R^2 / 2`). Code identifiers leak source chapter names (`compute_adc_ch6_five_tuple_slb`, `V8_CH3_MLX5_PROFILE`). 12.23 has a wrong srun invocation. Redundancy: 12.4/12.5 (PFC/ECN vs DCB/QoS), 12.19 vs 13.3 (GPUDirect Storage), 12.17/12.23/19.5 (nccl-tests and acceptance), 12.21 vs Part 13 (storage networks), 12.22 vs Part 17 (telemetry). A beginner cannot enter this part: the first chapter is 16k words and the core concepts (what a collective is, why one slow link stalls everyone) are buried under sizing tables.

**Part 13, AI storage (9 chapters).** Better structured than Part 12: the library-catalogue analogy in 13.6 is the kind of picture the language rule asks for, and the diagnostic method (strace -c, warm-cache trap, mdtest) is right. Still number-stacked and with tables carrying the explanation. Correctness risk is moderate: generalised limits ("MDS limit 50,000 to 100,000 ops/sec") stated as facts, a 400 GiB /dev/shm pod spec for a 4.6 GiB need. The serious structural issue is 13.7 vs 14.11: the same five checkpoint components, the same gather-vs-sharded example, the same Young-Daly worked numbers, the same async OOM and the same 64-to-48 reshard, from the same source, written twice. 13.5 repeats the GDS bounce-buffer table from 13.3 and 12.19.

**Part 14, training and fine-tuning (16 chapters).** Good beginner ramp at the start (14.1, 14.3, 14.11 open with plain stories and analogies). Mid-part chapters (14.4 to 14.9, 14.12) are dense, with parentheses at 0.2 to 0.3 per sentence and book-table references in exercises ("Tables 13-2 and 13-3"). Correctness risk is moderate and concentrated: 14.11 says the NCCL default timeout is 30 minutes (12.18 correctly says 10), counts gradients as checkpoint payload, and calls Xid 63 uncorrectable. Memory arithmetic for ZeRO stages appears in 14.3, 14.5, 14.6 and again in 13.7. Gap: no clear operational chapter on "the training job is slow and it is not the GPU" that joins dataloader (13.6), NCCL (12.18) and stragglers (14.12) into one triage path.

**Part 15, inference (18 chapters).** Rich, current and genuinely expert in places (vLLM internals, disaggregation, KV-cache tuning), but this is where correctness risk is highest. 15.3 contains a 10x arithmetic error that inverts its own swap-vs-recompute conclusion, unlabelled sparse TFLOPS figures, and an invented pipeline-parallel failure mechanism. 15.1 still opens "In today's AI landscape ... In this chapter, we trace", the most template-like opening in the set. Average sentence length is 19 to 21 words with 5 to 7 numbers per 100 words. Two chapters are book-length (15.12 at 25k, 15.13 at 23k) and should be split. Redundancy: 15.9/15.10/15.11 overlap on parallelism and disaggregation; 15.15 vs 20.20 (autoscaling) and 15.16 vs 20.18/20.21 (reliability, probes, circuit breakers) cover the same ground with different defaults. The vLLM default for gpu_memory_utilization is 0.90 in 15.3 and 0.92 in 20.18.

**Part 16, MLOps and LLMOps (15 chapters).** Plain, readable, beginner-friendly (asl 13 to 14, almost no code formatting), with scenario-based checkpoint questions that other parts should copy. But shallow for a Senior SRE: each tool gets a table and a YAML stub, exercises are "Add X. *Solution sketch:*" build tasks that cannot be checked, and every chapter opens with a "background reading ... figures below are examples, not quotations" block (62 occurrences in Parts 16 to 18). Correctness risk is in specifics: 16.7 calls the KServe transformer a sidecar, describes shadow mode as canary at 100 percent, and ships a NetworkPolicy that blocks the model download. Parts of the tool landscape are dated (Seldon Core v1 API, Yatai). Gap: model artifact delivery at LLM scale (OCI modelcar, storage initializer time, Gateway API Inference Extension).

**Part 17, operations (16 chapters).** The part that matters most for an SRE interview and the one that is thinnest. Chapters are 5k to 8k words of generic SRE practice (USE method, runbooks, incident roles) with little that is specific to GPU fleets, and 17.10 imports a software-engineering-textbook passage ("five generic activities: communication, planning, modelling, construction"). The reader-facing text says "the draft" repeatedly (17.4 has 8). 17.4's alert rules are operationally wrong: they page on high utilisation, on memory used above 90 percent (which every vLLM pod does by design), and on clocks below base (which every idle GPU does). Redundancy: 17.4 vs 10.21, 17.5 vs 10.20, 17.8/17.9 vs 15.13, 17.12 vs 13.8/15.18/19.9, 17.6 vs 20.19. Gaps a Senior SRE loop would expose: multi-window burn-rate alerting with worked numbers, GPU fleet health automation (cordon/drain/RMA loop), error budgets for token APIs, toil measurement.

**Part 18, security (7 chapters, 44k words).** The weakest part technically. Short, plain sentences, but the core mechanism in 18.5 is wrong (it says tenants read each other's GPU memory "via DMA" and that the IOMMU stops it), and the commands and configs in 18.5 are partly fabricated (`nvidia-smi -vgpu 1`, a time-slicing ConfigMap with non-existent fields, invented IAM roles). Exercises are all "Add a ... alert" with a sketch. Not one GPU-specific CVE is named, although the NVIDIA Container Toolkit escapes are the real-world tenant-isolation incidents of the last two years. 18.5 and 18.6 duplicate 11.21 to 11.28 at a fraction of the depth. Needs a rebuild, not edits.

**Part 19, capstones and interview readiness (15 chapters).** The best part of the set. 19.5 and 19.14 read like one careful author: real incident openings, sourced numbers, honest thresholds, decision rules, and analysers tested on real fixtures. Faults are process residue in reader text ("The earlier draft of this chapter used eight names", 18 times in 19.6; "Earlier drafts quoted ... so it is removed" in 19.5; "Parts 16, 17, 18 ... have not yet been through the same source check" in 19.14) and some duplicate derivations (Young/Daly is derived in 13.7, 14.11, 19.4 and 20.17). 19.3's front matter title lacks its number.

**Part 20, Nebius SRE interview (38 chapters).** Strong, opinionated, interview-shaped, and the most honest about sources. 20.18 is the best chapter I read and should be the house model for Parts 15 and 17. Its voice problem is the reverse of Part 10's: first-person process notes ("I ran it", "Verification log", "CONFIRMED/CORRECTED", paths to planning/ files) and a boilerplate opener ("This chapter serves the ... round", 30 files). 20.3 opens with "Honest status first" and a Docker image digest. No chapter has an exercises section; drills are in details blocks, which is acceptable for this volume. Risk: many facts are pinned to vLLM v0.32.0, dcgm-exporter 4.9.0, NCCL 2.31/2.32, all released weeks before writing; they are sourced, but the rest of the book disagrees with them in places (15.3 defaults, 17.4 metric names).

---

## 2. Chapter table (all 214)

Scores: voice / depth / accessibility, 1 to 5. Chapters marked * were read in full.

| chapter id | voice | depth | access | action | one-line reason |
|---|---|---|---|---|---|
| 10.1 | 3 | 3 | 3 | split | 16k words mixing role description, DeepSeek case study and host inspection; split into "why GPUs" and "the performance engineer's job" |
| 10.2 | 3 | 4 | 3 | rewrite-sections | Good scenario opening; occupancy math duplicated in 10.14; heavy tables |
| 10.3 | 2 | 4 | 2 | rewrite-sections | "In one minute" admonitions stuffed with numbers; BAR1 detail before the picture |
| 10.4 | 3 | 4 | 3 | light-edit | Clear opening contrast; drop raw tcgen05/wgmma detail to an aside |
| 10.5 | 3 | 4 | 3 | light-edit | Roofline motivated by a cost story; exercises are a parameter dump |
| 10.6 | 3 | 4 | 3 | light-edit | Good "slowest wire" framing; C2C coherence section valuable |
| 10.7 | 2 | 3 | 3 | rewrite-sections | Procurement memo exercises; 14 "untested"; product specs as prose |
| 10.8* | 2 | 3 | 3 | rewrite-sections | Persistence-mode and PyTorch-preallocation mechanisms wrong; source-note apparatus in body |
| 10.9 | 3 | 4 | 3 | light-edit | Core SRE chapter, sound layering; 19 "untested" tags |
| 10.10 | 2 | 4 | 2 | rewrite-sections | Fabric Manager material good; middle drifts into ToR oversubscription |
| 10.11 | 3 | 3 | 3 | light-edit | Fine CUDA basics; keep as the one programming chapter SREs need |
| 10.12 | 2 | 4 | 2 | merge-with 10.17 | "Chris Fregly details", "Volume 03 Chapter 8 parameters" in body; streams split across two chapters |
| 10.13 | 2 | 4 | 2 | merge-with 10.15 | "The book counts" voice; kernel tuning beyond SRE need |
| 10.14 | 2 | 4 | 2 | merge-with 10.2 | Occupancy repeated from 10.2 at 13.5k words |
| 10.15 | 2 | 4 | 2 | merge-with 10.13 | Inline PTX patterns from "Chapter 9" listed; same arithmetic-intensity ground |
| 10.16 | 2 | 4 | 1 | merge-with 10.18 | Warp specialisation and DSMEM: expert kernel-author content, no on-ramp |
| 10.17 | 2 | 4 | 2 | merge-with 10.12 | Stream-ordered allocation belongs with streams |
| 10.18 | 2 | 4 | 2 | merge-with 10.16 | Device-initiated orchestration; optional advanced appendix |
| 10.19 | 2 | 3 | 2 | merge-with 14.9 | torch.compile covered twice; exercise asks for a CPython PEP number |
| 10.20 | 2 | 4 | 2 | rewrite-sections | "Table 13-1" book refs in exercises; overlaps 14.8, 15.13, 17.5 |
| 10.21 | 3 | 4 | 3 | light-edit | Should own DCGM/ECC/Xid for the whole book; 17.4 links here |
| 10.22 | 3 | 4 | 3 | light-edit | Good triage-order framing; keep |
| 11.1 | 3 | 3 | 4 | light-edit | Strong "zero GPUs on a green node" opener |
| 11.2 | 3 | 4 | 3 | light-edit | Device plugin/CDI well layered |
| 11.3 | 3 | 3 | 3 | light-edit | EKS Terraform module detail is noise |
| 11.4 | 3 | 3 | 3 | light-edit | Operator reconciliation explained well |
| 11.5 | 3 | 3 | 3 | light-edit | "Helm deployed means less than it sounds" is a good lesson |
| 11.6 | 3 | 4 | 3 | light-edit | Topology Manager/NUMA solid |
| 11.7 | 3 | 3 | 4 | light-edit | Clear "a Pod cannot span nodes" teaching |
| 11.8 | 3 | 3 | 3 | light-edit | Kueue/Volcano fine; boilerplate fault-table intro |
| 11.9 | 3 | 3 | 3 | rewrite-sections | RAG/vector-DB paragraph in a JobSet chapter (still present) |
| 11.10 | 3 | 3 | 3 | light-edit | Multus/SR-IOV path clear |
| 11.11 | 3 | 3 | 3 | rewrite-sections | fio storage-validation paragraph in Network Operator chapter |
| 11.12 | 3 | 4 | 3 | light-edit | DRA v1 at 1.34 correct and current |
| 11.13 | 3 | 3 | 3 | merge-with 11.14 | Six KAI chapters is too many; motivation + architecture fit in one |
| 11.14 | 3 | 3 | 3 | merge-with 11.13 | Same |
| 11.15 | 3 | 3 | 3 | merge-with 11.16 | Queues, gang and topology form one chapter |
| 11.16 | 3 | 3 | 3 | merge-with 11.15 | Same |
| 11.17 | 3 | 3 | 3 | merge-with 11.18 | Fractions and operations form one chapter |
| 11.18 | 3 | 3 | 3 | merge-with 11.17 | Same |
| 11.19 | 3 | 2 | 3 | merge-with 11.31 | Run:ai view repeats 11.31 platform map |
| 11.20 | 3 | 3 | 3 | light-edit | Comparison guide is useful for interviews |
| 11.21 | 3 | 3 | 3 | rewrite-sections | Off-topic mpstat/dataloader middle; PCIe/IOMMU core is right |
| 11.22 | 3 | 3 | 3 | rewrite-sections | "Compromised pod" triage row out of place |
| 11.23 | 3 | 3 | 3 | light-edit | vGPU licensing clear |
| 11.24* | 2 | 3 | 3 | rewrite-sections | Impossible MIG combo, driver/CUDA mismatch, drain logic wrong under MIG |
| 11.25 | 3 | 3 | 3 | light-edit | Time-slicing/MPS fine |
| 11.26 | 3 | 3 | 4 | keep | Workload-contract-first framing is exactly right |
| 11.27 | 3 | 3 | 3 | light-edit | KubeVirt/Kata fine; CC paragraph overlaps 18.6 |
| 11.28 | 3 | 3 | 3 | light-edit | Should own DPU content; 18.6 links here |
| 11.29 | 3 | 3 | 3 | light-edit | Day-two ops reasonable |
| 11.30 | 3 | 3 | 3 | rewrite-sections | Cloud lab mostly replaced by local Python checks |
| 11.31 | 3 | 3 | 3 | rewrite-sections | 13k words; opens with a link list to 11.32 to 11.34 |
| 11.32 | 2 | 4 | 2 | merge-with 11.33 | Opens with a provenance "Tag legend" and "on this Mac" |
| 11.33 | 3 | 4 | 3 | merge-with 11.32 | Good ten-day pilot framing; three NVKE chapters too many |
| 11.34 | 3 | 3 | 3 | light-edit | 02:10 /readyz opener is good |
| 12.1 | 3 | 4 | 3 | split | 16k words; the beginner entry to Part 12 needs a short concept chapter |
| 12.2 | 2 | 4 | 2 | rewrite-sections | Verbs opcode lists in prose; V8_CH3 identifiers |
| 12.3 | 3 | 4 | 3 | light-edit | Good "why one drop matters" BDP reasoning |
| 12.4 | 3 | 4 | 3 | merge-with 12.5 | PFC/ECN/DCQCN and DCB/QoS are one topic |
| 12.5 | 2 | 4 | 2 | merge-with 12.4 | Buffer threshold arithmetic carries the explanation |
| 12.6 | 3 | 4 | 3 | light-edit | IB addressing fine |
| 12.7 | 3 | 4 | 3 | light-edit | SM/routing fine |
| 12.8 | 2 | 4 | 2 | rewrite-sections | 35 code blocks; credit accounting before intuition |
| 12.9 | 2 | 4 | 2 | rewrite-sections | 26 "untested"; diagnostics as command dumps |
| 12.10 | 2 | 3 | 2 | rewrite-sections | Connector/optics lists; "Giga Data Rate" claim to check |
| 12.11 | 2 | 3 | 2 | rewrite-sections | Vendor product chapter; dense |
| 12.12 | 3 | 4 | 3 | light-edit | Decision guide is interview-relevant |
| 12.13 | 3 | 4 | 3 | light-edit | Topology math right; keep |
| 12.14 | 2 | 4 | 2 | split | 17k words; ECMP/DLB and routing protocols are two chapters |
| 12.15 | 3 | 4 | 3 | light-edit | Collectives explained with rhythm-of-a-step framing |
| 12.16 | 3 | 4 | 3 | light-edit | Env-var chapter, useful |
| 12.17 | 2 | 4 | 2 | rewrite-sections | Inference TPS/RPS paragraph off-topic; overlaps 19.5/12.23 |
| 12.18 | 3 | 4 | 3 | light-edit | Correct 10-min default; good misdiagnosis framing |
| 12.19 | 2 | 4 | 2 | merge-with 13.3 | GDS covered twice |
| 12.20 | 3 | 4 | 3 | light-edit | SHARP fine |
| 12.21 | 2 | 3 | 2 | split | 25k words: storage net, UEC and scale-up fabrics are three topics |
| 12.22 | 3 | 3 | 3 | light-edit | Telemetry KPIs; link to Part 17 |
| 12.23* | 2 | 4 | 2 | rewrite-sections | srun -x bug; raw LaTeX; duplicated numbers; strong ladder idea |
| 12.24 | 3 | 4 | 3 | light-edit | Good blame-the-other-layer opener |
| 13.1 | 3 | 4 | 3 | light-edit | Data path framing good |
| 13.2 | 3 | 3 | 3 | light-edit | Stateless-node contrast good |
| 13.3 | 3 | 4 | 3 | light-edit | Should own GDS for the book |
| 13.4 | 3 | 4 | 3 | light-edit | Lustre for AI; depends on 6.19 |
| 13.5 | 3 | 3 | 3 | rewrite-sections | Vendor survey; repeats GDS table |
| 13.6* | 3 | 3 | 3 | rewrite-sections | Good analogy and method; number stacks; 400 GiB /dev/shm spec |
| 13.7 | 2 | 3 | 3 | merge-with 14.11 | Same checkpoint content as 14.11 from the same source |
| 13.8 | 3 | 3 | 3 | light-edit | Storage cost planning; link 17.12/19.9 instead of repeating |
| 13.9 | 2 | 4 | 3 | light-edit | Troubleshooting ladder useful; gdsio flags dense |
| 14.1 | 3 | 3 | 4 | light-edit | Excellent 64-GPU OOM opener |
| 14.2 | 3 | 4 | 3 | light-edit | GQA/MQA infra consequences well chosen |
| 14.3 | 3 | 4 | 3 | light-edit | Good memory anatomy |
| 14.4 | 2 | 4 | 3 | rewrite-sections | 0.32 parentheses per sentence; code density high |
| 14.5 | 2 | 4 | 3 | merge-with 14.6 | ZeRO/FSDP memory math repeated |
| 14.6 | 2 | 4 | 3 | merge-with 14.5 | Same |
| 14.7 | 3 | 4 | 3 | light-edit | TP/PP/EP fine |
| 14.8 | 2 | 4 | 2 | rewrite-sections | Exercises reference book "Tables 13-2/13-3" |
| 14.9 | 3 | 4 | 3 | light-edit | Should own torch.compile; absorb 10.19 |
| 14.10 | 3 | 4 | 3 | light-edit | Multi-node architecture fine |
| 14.11* | 3 | 3 | 4 | rewrite-sections | 30-min NCCL default wrong; gradients in checkpoint; swap advice |
| 14.12 | 2 | 4 | 3 | rewrite-sections | Seven marketing words; exercise block in the middle |
| 14.13 | 3 | 4 | 3 | light-edit | Fine-tuning fine |
| 14.14 | 3 | 3 | 3 | light-edit | Dataset engineering fine |
| 14.15 | 3 | 3 | 3 | rewrite-sections | 59 code blocks |
| 14.16 | 3 | 3 | 3 | light-edit | NeMo fine |
| 15.1 | 1 | 3 | 2 | rewrite-sections | "In today's AI landscape ... In this chapter, we trace" opener |
| 15.2 | 2 | 4 | 3 | rewrite-sections | Exercise list sits mid-chapter; "up to 90 percent" claim unsourced |
| 15.3* | 2 | 4 | 2 | rewrite-sections | 10x recompute error inverts conclusion; sparse TFLOPS unlabelled; V0/V1 mix |
| 15.4 | 3 | 4 | 3 | light-edit | SGLang well contrasted |
| 15.5 | 2 | 3 | 2 | rewrite-sections | Exercises are parameter dumps |
| 15.6 | 2 | 3 | 3 | light-edit | Triton fine |
| 15.7 | 2 | 3 | 2 | rewrite-sections | "Volume 14 Lab 02" leak; being rewritten |
| 15.8 | 2 | 4 | 2 | rewrite-sections | Dense; book derivation blocks |
| 15.9 | 2 | 4 | 2 | rewrite-sections | 16k words; overlaps 15.10 |
| 15.10 | 2 | 4 | 2 | merge-with 15.11 | Disaggregation in two chapters |
| 15.11 | 2 | 4 | 2 | merge-with 15.10 | Same |
| 15.12 | 2 | 4 | 2 | split | 25k words |
| 15.13 | 3 | 4 | 3 | split | 23k words; strong content |
| 15.14 | 2 | 4 | 3 | light-edit | "Yuan Tang demonstrates" book leak |
| 15.15 | 2 | 3 | 3 | merge-with 20.20 | Autoscaling covered twice |
| 15.16 | 2 | 3 | 3 | rewrite-sections | Probe/circuit-breaker content conflicts with 20.18/20.21 |
| 15.17 | 2 | 3 | 3 | rewrite-sections | Lab is mostly local Python |
| 15.18 | 2 | 3 | 3 | rewrite-sections | Cost per token; dedupe with 20.12 |
| 16.1 | 3 | 3 | 4 | light-edit | 12k words; recap opener |
| 16.2 | 3 | 3 | 4 | light-edit | Good 2 a.m. "what changed" opener |
| 16.3 | 3 | 3 | 4 | light-edit | Feature store parity explained |
| 16.4 | 3 | 2 | 4 | expand | Orchestrators listed, not compared under failure |
| 16.5 | 3 | 2 | 4 | expand | Ray/KubeRay shallow |
| 16.6 | 3 | 3 | 4 | light-edit | Promotion gate idea strong |
| 16.7* | 3 | 2 | 4 | rewrite-sections | Transformer "sidecar", shadow mode, NetworkPolicy wrong; dated tools |
| 16.8 | 3 | 2 | 4 | expand | RAG/agents ops shallow |
| 16.9 | 3 | 2 | 4 | expand | Eval and guardrails shallow |
| 16.10 | 3 | 2 | 4 | expand | Drift without numbers |
| 16.11 | 3 | 2 | 4 | light-edit | Cloud platforms survey |
| 16.12 | 3 | 2 | 3 | light-edit | NVAIE licensing |
| 16.13 | 3 | 2 | 4 | expand | Governance generic |
| 16.14 | 3 | 3 | 4 | light-edit | Remove OOMKilled basics |
| 16.15 | 3 | 2 | 4 | rewrite-sections | Lab exercises unverifiable |
| 17.1 | 3 | 2 | 4 | light-edit | Opener already fixed; generic pillars |
| 17.2 | 3 | 2 | 4 | expand | Prometheus basics; GPU specifics thin |
| 17.3 | 3 | 2 | 4 | expand | Loki/OTel generic |
| 17.4* | 3 | 2 | 3 | rewrite-sections | Alert rules wrong in judgement; "the draft" x8 |
| 17.5 | 3 | 2 | 3 | merge-with 10.20 | Profiling repeated |
| 17.6 | 3 | 2 | 4 | expand | SLOs without burn-rate math |
| 17.7 | 2 | 2 | 3 | rewrite-sections | "Read the diagram" opener; catalogue without numbers |
| 17.8 | 3 | 2 | 4 | merge-with 17.9 | Method and checklist are one chapter |
| 17.9 | 3 | 3 | 3 | merge-with 17.8 | 16k-word checklist |
| 17.10 | 2 | 2 | 3 | rewrite-sections | Textbook "five generic activities" filler |
| 17.11 | 3 | 2 | 4 | expand | Incident roles generic |
| 17.12 | 2 | 2 | 3 | merge-with 19.9 | Capacity covered in four places |
| 17.13 | 3 | 1 | 4 | expand | Reliability with no GPU-fleet numbers |
| 17.14 | 3 | 2 | 4 | expand | DR without RTO/RPO worked cases for checkpoints |
| 17.15 | 3 | 2 | 4 | expand | Runbook template without GPU runbooks |
| 17.16 | 2 | 1 | 3 | rewrite-chapter | Vague "use high-level compilers", "watch AI services" |
| 18.1 | 3 | 2 | 4 | rewrite-sections | Threat model generic; no AI-specific attack trees |
| 18.2 | 3 | 2 | 3 | rewrite-chapter | Firmware trust without SPDM/attestation specifics |
| 18.3 | 3 | 2 | 4 | rewrite-sections | Supply chain checklist filler ("What is the current X rate?") |
| 18.4 | 2 | 2 | 3 | rewrite-sections | "Read the diagram" opener; off-topic patch paragraph |
| 18.5* | 2 | 1 | 3 | rewrite-chapter | Core mechanism wrong; fabricated commands and config |
| 18.6 | 3 | 1 | 3 | rewrite-chapter | Duplicates 11.27/11.28 at lower depth |
| 18.7 | 3 | 1 | 3 | rewrite-chapter | "Add an alert" exercises; no model-weight protection mechanics |
| 19.1 | 3 | 4 | 3 | light-edit | Good fairshare 2 a.m. story |
| 19.2 | 4 | 4 | 3 | light-edit | "Earlier draft" note in body |
| 19.3 | 4 | 4 | 3 | light-edit | Front-matter title lacks "19.3" |
| 19.4 | 3 | 4 | 3 | light-edit | Opens with a numbered list; Young/Daly third derivation |
| 19.5* | 4 | 4 | 4 | light-edit | Model chapter; strip draft history |
| 19.6 | 4 | 4 | 3 | light-edit | "The earlier draft" 18 times |
| 19.7 | 4 | 3 | 3 | light-edit | Repeats 4.9 rename from 17.4 |
| 19.8 | 4 | 3 | 4 | light-edit | Good wrong-shapes opener |
| 19.9 | 3 | 3 | 3 | light-edit | 15 "untested"; should own capacity planning |
| 19.10 | 4 | 2 | 4 | light-edit | Consulting method; "earlier draft cited placeholder files" |
| 19.11 | 4 | 4 | 4 | keep | Workload-first design answer |
| 19.12 | 4 | 4 | 4 | keep | Little's-law sizing done right |
| 19.13 | 4 | 3 | 4 | keep | Lending-rule example good |
| 19.14* | 4 | 3 | 4 | light-edit | Excellent bank; status leak about Parts 16 to 18 |
| 19.15 | 4 | 3 | 4 | light-edit | Trustworthy-sheet framing good |
| 20.1 | 4 | 2 | 4 | keep | Map of the volume |
| 20.2 | 4 | 2 | 4 | keep | Posting line by line |
| 20.3 | 3 | 4 | 3 | light-edit | Opens "Honest status first" with an image digest |
| 20.4 | 4 | 4 | 3 | light-edit | Code density 7/100 words |
| 20.5 | 3 | 4 | 3 | light-edit | "This chapter serves" opener |
| 20.6 | 3 | 4 | 3 | light-edit | Same opener |
| 20.7 | 4 | 4 | 3 | light-edit | Good 5xx-log opener |
| 20.8 | 4 | 3 | 4 | keep | Coding round format |
| 20.9 | 4 | 3 | 4 | keep | Patterns |
| 20.10 | 4 | 3 | 4 | keep | Latency numbers |
| 20.11 | 4 | 3 | 4 | keep | Practice set |
| 20.12 | 3 | 4 | 3 | light-edit | 8.9 numbers/100 words; dedupe with 15.18 |
| 20.13 | 3 | 4 | 3 | light-edit | Book-chapter citation in body |
| 20.14 | 4 | 4 | 3 | light-edit | Good |
| 20.15 | 4 | 4 | 3 | light-edit | Good |
| 20.16 | 4 | 4 | 3 | light-edit | Good |
| 20.17 | 3 | 3 | 2 | rewrite-sections | 12.4 numbers/100 words; drill sheet unreadable as prose |
| 20.18* | 4 | 4 | 4 | light-edit | Best chapter read; strip verification log |
| 20.19 | 4 | 4 | 3 | light-edit | Owns token-API SLOs; 17.6 should link here |
| 20.20 | 4 | 4 | 3 | light-edit | Owns autoscaling; absorb 15.15 |
| 20.21 | 4 | 4 | 3 | light-edit | Envoy panic threshold detail is expert |
| 20.22 | 4 | 4 | 3 | light-edit | vLLM v0.32.0 pins |
| 20.23 | 4 | 4 | 3 | light-edit | Good |
| 20.24 | 4 | 3 | 3 | light-edit | Six marketing words |
| 20.25 | 4 | 4 | 3 | light-edit | PromQL traps good |
| 20.26 | 4 | 3 | 3 | light-edit | Stress round good |
| 20.27 | 4 | 3 | 4 | keep | Post-mortem storytelling |
| 20.28 | 4 | 2 | 4 | keep | Project deep dive |
| 20.29 | 4 | 2 | 4 | keep | Plan |
| 20.30 | 3 | 3 | 3 | light-edit | [official] tags inline |
| 20.31 | 3 | 3 | 3 | light-edit | Same |
| 20.32 | 3 | 3 | 3 | light-edit | Same |
| 20.33 | 3 | 3 | 3 | light-edit | Same |
| 20.34 | 3 | 3 | 3 | light-edit | Leans on third-party ClusterMAX |
| 20.35 | 3 | 3 | 3 | light-edit | "[source-code, my reading of ...]" tags |
| 20.36 | 3 | 4 | 3 | light-edit | Soperator rolling update well explained |
| 20.37 | 3 | 3 | 3 | light-edit | Status-page statistics |
| 20.38 | 3 | 3 | 3 | light-edit | Separates documented vs marketed vs own design |

---

## 3. The 12 full-chapter reviews

### 10.8 Operating GPU nodes: nvidia-smi, topology, clocks and throttling
Strengths: the "three lies" framing (utilisation, memory, clocks) is the right mental model; the throttle bitmask table matches nvml.h; the Xid tiering is a usable triage rule; section 5.2's ordered slowdown check is what an on-call needs.
Five problems:
1. Persistence mode mechanism wrong: "the Linux kernel unloads the `/dev/nvidia*` character devices ... re-enumerate the PCIe bus, reload driver modules" (4.1, repeated in Q9).
2. "This pool often reserves 75% to 95% of total VRAM" upfront (2.2, Q7): PyTorch's caching allocator grows on demand.
3. Invented thermal model: "a chassis providing `3 W/°C` of heat rejection" and exercise 4 built on it.
4. Source-note apparatus throughout: "V16 Ch 1 Compute-Bound Run" as table rows, "(untested here)" on every command, section 5.5 "Source notes comparison", "Corrections to the author's notes", a 25-line MIGRATION_MAP list.
5. Misses the case readers will meet: an NCCL hang shows near 100 percent GPU-Util on every rank because NCCL kernels spin; the chapter says "other ranks sit at 0% waiting".
Factual errors: persistence mode (NVIDIA driver persistence documentation: the module stays loaded; without persistence the driver deinitialises the GPU when the last client closes). PyTorch preallocation (PyTorch CUDA semantics docs; the 75 percent preallocation default belongs to JAX/XLA). Needs checking: `APPLICATIONS_CLOCKS_SETTING` is tied to application clocks (`-ac`), not `-lgc`.
Beginner blocker: no picture of what "a warp is resident" means before the utilisation definition; the bitmask table arrives before the reader knows why clocks move.
Expert disappointment: no DCGM_FI_PROF_SM_ACTIVE/SM_OCCUPANCY as the honest utilisation metric, no row-remapper query, no NVLink error counters, no GPU reset/driver reload procedure, no clock-event-reason naming change.
Rewrite instruction: fix the two mechanisms; delete 5.5, the corrections section and the migration list; strip "(untested here)" and source tags from tables, lab output and answers; replace the W/°C exercise with a throttle-reason decode; add a short section "utilisation you can trust" (SM_ACTIVE, TENSOR_ACTIVE, DRAM_ACTIVE) and an NCCL-hang signature row.

### 11.24 MIG in depth
Strengths: GI vs CI explained by what each owns; the isolated-vs-shared table is exactly what a security reviewer needs; "seven 1g.10gb give 70 GB" explained by memory-slice geometry; sizing from concurrent peak, not weights, is the right lesson.
Five problems:
1. "1 x 4g.40gb + 2 x 2g.20gb also valid at 80 GB" is eight compute slices.
2. Layer 1 output "575.10 (CUDA Version: 12.5)".
3. Drain loop polls DCGM field 203 to prove no workload remains, then `rmmod`s the driver for a MIG change.
4. Checkpoint questions examine the source notes: "In Volume 4 Chapter 3 (Part 1.2), how is CUDA MPS configured".
5. Invented ceremony presented as practice: "10-Item Operational Evidence Package & 7-Field Governance Record", "Silicon Tetris", "Senior Architect Forensics".
Factual errors: profile combination (NVIDIA MIG User Guide, supported profiles; `nvidia-smi mig -lgip`). Driver 575 ships with CUDA 12.9 (CUDA toolkit release notes, driver table). Utilisation is not reported per physical GPU with MIG enabled, and zero utilisation does not mean no open handle.
Beginner blocker: the reader is told to create GIs and CIs before seeing why two layers exist; the heading scheme "### 1. Basics" then "#### 1." confuses.
Expert disappointment: no H200/B200 profiles, no "+me" media profiles, no per-instance DCGM labels (GPU_I_ID), no MIG with time-slicing, no GKE path although GKE is the venue.
Rewrite instruction: fix the combination and driver pairing; replace the drain loop with a process check (`nvidia-smi --query-compute-apps`, `fuser /dev/nvidia*`) and explain that MIG mode toggles need a GPU reset with no clients, while layout changes do not need a module unload; rewrite checkpoint questions as scenarios; add a GKE MIG node-pool subsection.

### 12.23 Fabric validation and capacity planning
Strengths: the five-stage acceptance ladder with "a later stage cannot make up for an earlier one"; bottleneck-cut and N-1 reasoning; four cable-diff categories; the Clos BOM arithmetic is correct.
Five problems:
1. `srun ... -x NCCL_DEBUG=WARN -x NCCL_IB_TC=106` in the Stage L4 commands.
2. Raw TeX shown to the reader: `\rightarrow` in table cells, `G_{\max} = R^2 / 2` in backticks.
3. Numbers printed twice: "12,800 / 3,200 = 4.00:1 (4:1)", "t_1:1 = ... 40.0 ms (40 ms)".
4. Explanations live in ```text blocks of counters ("rx_packets: 1024567 (1,024,567), rx_bytes: 892481382400").
5. Checkpoint Q10/Q11 ask for Topograph fetch timeouts and upgrade package names.
Factual errors: `srun -x` is `--exclude` (srun man page); env must go through `--export`. "Disabling IOMMU (iommu=pt)" mislabels passthrough mode. Needs checking: universal DOM pass threshold "Rx >= -6.0 dBm" (receiver sensitivity is per optic type).
Beginner blocker: the opening dumps two production incidents as counter lists before saying what "acceptance" means.
Expert disappointment: no at-scale L3 tooling (all-pairs perftest harness, per-rail nccl-tests with NCCL_IB_HCA), no SHARP/NVLS A/B, no retention policy for evidence.
Rewrite instruction: fix srun; convert every TeX-in-backticks to $...$ math or plain words; remove all duplicated parenthetical numbers; move each counter block into a short worked example after the prose; replace Q10/Q11 with "which stage would catch X" scenarios.

### 13.6 Data loading, small files and metadata
Strengths: the library-catalogue analogy; strace -c, warm-cache trap and mdtest as three complementary checks; DataLoader settings tied to their failure symptoms; the DALI ping-pong anti-pattern.
Five problems:
1. 31 numbers in the first 25 lines; the ImageNet arithmetic block repeats three times (opening, 1.1 table, 1.1 verification).
2. Inconsistent provenance numbers: openat at "106 us/call" in one table and "8 usecs/call ... 1,234 errors" in the summary.
3. "MDS limit 50,000 to 100,000 ops/sec" stated as a constant.
4. "persistent_workers=False tears down and fork/spawns all num_workers * 8 processes".
5. A 400 GiB memory-backed /dev/shm for a computed 4.6 GiB need.
Factual errors: none I can prove wrong outright; the MDS limit and the `num_workers * 8` claim need checking (MDS rates depend on hardware and DNE; workers are num_workers per rank).
Beginner blocker: "DNE", "OST", "OSS" are used before Part 13's Lustre chapter is read; prerequisites point at it but the chapter does not define them.
Expert disappointment: no discussion of shuffle quality with shard-level shuffling, no object-store streaming (S3 range reads, Mountpoint), no GPU-side decode limits.
Rewrite instruction: keep the analogy and the three checks; state the ImageNet arithmetic once in a short block; make the MDS limit "your MDS's measured mdtest rate"; size /dev/shm to need plus headroom and warn that memory-backed emptyDir counts against the pod limit.

### 14.11 Checkpointing, fault tolerance and elastic training
Strengths: the video-game save opening; the five components; why try/except cannot repair an NCCL communicator; elastic batch preservation; a goodput table whose numbers check out.
Five problems:
1. "By default, PyTorch's NCCL process group timeout is thirty minutes" (4.3, failure row 6, exercise 5b).
2. "Checkpoint payload at 16 bytes/param (4B weights + 4B grads + 8B Adam)".
3. "Uncorrectable ECC error (`Xid 48`/`63`)".
4. The first code block claims "all 5 deterministic state components" but saves no dataloader state and only rank 0's CUDA RNG.
5. "add a `100 GB` swap file" as an async-checkpoint mitigation.
Factual errors: NCCL default timeout is 10 minutes (torch.distributed.init_process_group docs; 12.18 line 232 agrees). Gradients are not saved. Xid 63 is a row-remap record (10.8 itself tiers it as informational). Pinned host memory cannot be swapped.
Beginner blocker: Young-Daly formula appears before an explanation of why the optimum exists.
Expert disappointment: no in-memory/peer checkpointing, no checkpoint validation or corruption detection on load, no torchft/fault-tolerant HSDP mention.
Rewrite instruction: fix the four errors; own fault tolerance and elastic training here; move storage-tier and write-path content to 13.7 and link; delete lab checks 23 and 24 (off-topic).

### 15.3 vLLM in depth
Strengths: PagedAttention block tables, CoW, APC hash chaining, the token-budget scheduler and V1's process split are explained with real mechanism; DP+EP launch commands and the metrics table are what an operator uses.
Five problems:
1. Swap vs recompute: "t_swap = 167.77 ms vs t_recompute = 29.01 ms -> Recompute is 5.78x faster!"
2. "TF32 = 989 TFLOPS | BF16/FP16 = 1,979 TFLOPS | FP8/INT8 = 3,958" without saying these are sparse figures.
3. Failure Mode 4: "Stage 0 KV cache usage to hit 99.2 percent while Stage 1 sits at 38.5 percent" because stage 0 "absorbed heavy prefills".
4. V0 and V1 mixed: `BlockSpaceManager`, `use_beam_search` next to `EngineCore`; multi-node example uses `python -m vllm.entrypoints.api_server`.
5. Out-of-scope content: closed-model API price lists, RLHF rollout share, image-pad token IDs.
Factual errors: the chapter's own formula gives 289 ms recompute for L=80, S=4096, H=8192 at 989 TFLOPS (code/part15/vllm_paged_attention.py computes 289 ms); for the GQA model named, round-trip swap is about 42 ms, so swap is faster by about 7x; and 989 TFLOPS assumes 100 percent MFU. H100 SXM dense BF16 is 989 TFLOPS, TF32 495 (NVIDIA H100 datasheet). PP stages hold KV for their own layers for every request. Needs checking: MQA examples (Falcon-40B uses 8 KV groups), "--swap-space removed in v0.18.0".
Beginner blocker: KV-cache formulas and complexity notation precede any picture of a block.
Expert disappointment: no cache_salt for tenant isolation (20.22 has it), no LMCache/NIXL operational detail beyond numbers.
Rewrite instruction: correct the swap/recompute numbers and restate the recompute rule as "V1 recomputes because swap was removed"; label sparse figures; delete the PP-imbalance failure mode; replace V0 names; cut price lists; split into "PagedAttention and the scheduler" and "operating vLLM".

### 16.7 Model serving platforms: KServe, Seldon and BentoML
Strengths: plain voice; a clear ownership table; failure stories with symptom/diagnosis/fix; scenario checkpoint questions.
Five problems:
1. "The transformer is a sidecar."
2. "Shadow mode works by sending 100% of traffic to the canary and disabling its response path."
3. The NetworkPolicy allows egress only to kube-system, using a `name:` namespace label.
4. BentoML example calls `.predict` on `bentoml.models.BentoModel`.
5. Opening block: "background reading ... the figures below are examples, not quotations".
Factual errors: KServe transformer is a separate component (KServe docs); `canaryTrafficPercent: 100` promotes; shadowing needs request mirroring; the policy blocks the storage initializer's object-store pull. Needs checking: Seldon Core v1 API status and licence change, Yatai deprecation, runtime image registry.
Beginner blocker: none serious; this chapter is readable.
Expert disappointment: no RawDeployment vs Serverless trade-off, no modelcar/OCI model delivery, no ServingRuntime, no Gateway API Inference Extension or llm-d.
Rewrite instruction: fix the four errors; add a section on LLM serving on KServe today (RawDeployment, vLLM runtime, model loading time budget, inference gateway); replace "Add X" exercises with checkable tasks.

### 17.4 DCGM exporter and interpreting GPU metrics
Strengths: plain opening; an honest, row-by-row 4.8-to-4.9 rename table with inferred rows marked.
Five problems:
1. `GPUHighUtilization` (>95 percent for 10 minutes, "over-utilised", fix "reduce batch size").
2. `GPUMemoryPressure` at 90 percent framebuffer used.
3. `GPUClockThrottle` on SM clock below 1400 MHz, and `GPUThermalThrottle` on temperature above 85 C.
4. "The draft treats a single double-bit error as critical", "the service target the draft uses" (8 occurrences).
5. Lab "Step 5: simulate a GPU failure" reads counters and simulates nothing.
Factual or judgement errors: full utilisation is the goal; vLLM preallocates 90 percent by design (15.3) and 10.8 calls high memory "the Memory Lie"; idle GPUs drop to about 300 MHz (10.8), so the clock rule fires on idle nodes; `DCGM_FI_DEV_XID_ERROR > 0` stays true forever. DCGM supports error injection (`dcgmi test --inject`). Needs checking: "H100 base clock is 1.4 GHz"; the 4.9.0 release itself (dated five days before writing).
Beginner blocker: metric families listed before the reader knows which questions they answer.
Expert disappointment: no alerts on row-remap pending/failure, NVLink CRC rate, PCIe replay rate, GPU count mismatch, or exporter absence.
Rewrite instruction: rebuild the rule file around fault signals (row remap, ECC DBE rate, Xid by tier with `changes()`, throttle violation counters, NVLink/PCIe error rates, `absent()`), delete the utilisation and memory-used alerts or make them capacity reports, replace "the draft" with direct statements, fix the lab to use PrometheusRule and error injection.

### 18.5 GPU sharing security, DMA, IOMMU and SR-IOV
Strengths: short sentences; correct instinct that time-slicing is the weakest boundary and hardware boundaries matter.
Five problems:
1. "Tenant A's workload uses DMA to read GPU memory that contains Tenant B's data", defended by the IOMMU.
2. `nvidia-smi -vgpu 1`, `nvidia-smi mig -cgi 0,1,2,3,4,5,6 -C`, `cat /sys/class/iommu/*/devices/*`, `perf stat -e iommu.io_page_walk.cycles`.
3. Time-slicing ConfigMap with `interval: 5` and `timeout: 10`.
4. "Memory isolation: None (processes share GPU memory)" for time-slicing; "SR-IOV (vGPU) ... Spatial (concurrent)".
5. Detection by `nvidia-smi --query-gpu=memory.used` and an alert "GPU memory anomalies > 0" that should page.
Factual errors: GPU processes are isolated by per-context GPU virtual memory; the IOMMU protects host memory from device DMA (Linux IOMMU documentation, NVIDIA CUDA programming guide on contexts). `nvidia-smi -vgpu` does not exist; Ampere+ vGPU VFs are enabled with `sriov-manage` (NVIDIA vGPU user guide). The device plugin time-slicing schema is `sharing.timeSlicing.resources[].replicas` (k8s-device-plugin README). Non-MIG vGPU is time-sliced.
Beginner blocker: DMA, IOMMU, MIG and SR-IOV are introduced as three equal "layers" when they protect different things.
Expert disappointment: no NVIDIA Container Toolkit escape CVEs (CVE-2024-0132, CVE-2025-23266), no NVIDIA_VISIBLE_DEVICES=all risk, no memory scrubbing, no ACS/IOMMU-group vs GPUDirect P2P trade-off.
Rewrite instruction: rebuild from a threat table (cross-tenant read, host escape, noisy neighbour, side channel, remanence) and map each threat to the control that actually stops it; delete all invented commands; link 11.21 to 11.26 for mechanics.

### 19.5 Capstone: an nccl-tests fabric lab
Strengths: real incident openings; algbw vs busbw explained with a derivation and a wrong-ticket story; tier ladder; analyser tested on a real BCM table; "the ranks that print the timeout are the healthy ones".
Five problems:
1. "Earlier drafts quoted a '750 to 800 GB/s' range ... so it is removed."
2. "The exact `nvbandwidth` thresholds in earlier drafts were from memory and are removed."
3. "my reasoning" three times in rule text.
4. Ladder and gates re-derived from 12.17/12.23.
5. No per-rail isolation run.
Factual errors: none found. Needs checking: NCCL 2.31 diagnostics, `NCCL_DEBUG=ATTN` since 2.32.
Beginner blocker: few; prerequisites are clear.
Expert disappointment: no NVLS/SHARP A/B and no alltoall expectation for MoE.
Rewrite instruction: delete draft history; say "a starting threshold; calibrate it" once in a callout; add a per-rail run; replace repeated ladder text with links.

### 19.14 Interview question bank by topic
Strengths: the answer shape; the weak-answer field; arithmetic answers that check out; chapter links as repair paths.
Five problems:
1. "Parts 16, 17, 18 and the earlier drafts of Part 19 have not yet been through the same source check" in reader text.
2. Observability and operations: 9 questions, 0 stretch, for an SRE target.
3. Weighted to Parts 1 to 9.
4. 40 samples make the chapter long.
5. Some answers depend on chapters with known errors (Parts 17 and 18).
Factual errors: none found; its persistence-mode answer is correct and should be the reference for fixing 10.8.
Beginner blocker: none.
Expert disappointment: no burn-rate, toil or fleet-automation questions.
Rewrite instruction: remove the status sentence; add six senior/stretch operations questions; re-run the bank validator after Parts 17/18 are fixed.

### 20.18 How LLM serving fails
Strengths: one model (three places a request waits) carried through every failure; symptom/confirm/mitigate/fix/decide per section; real metric names; the /health and error-after-first-token traps; correct retry and KV arithmetic.
Five problems:
1. "I ran it" four times and a "Verification log (fact-check pass)" with CONFIRMED/CORRECTED items.
2. Drill Q8: "A busy engine answers slowly, so the probe fails" contradicts the corrected section 8.
3. gpu_memory_utilization 0.92 here vs 0.90 in 15.3.
4. vLLM only.
5. Source line points at `planning/VOLUME_20_NEBIUS_SRE_PLAN.md`.
Factual errors: none found.
Beginner blocker: none; terms are defined at first use.
Expert disappointment: no mapping of the three waits to SGLang/TRT-LLM metrics.
Rewrite instruction: move the verification log to the ledger, fix Q8, align the default with 15.3, add one paragraph on other engines.

---

## 4. Cross-cutting patterns and mechanical instructions

1. **Source and process apparatus in reader text.** "(untested here)" 896 times in 98 files; "Volume NN Ch" 1,515 times in 88 files; "Corrections to the author's notes" in 40 files; "my inference / I ran it / my reasoning" 173 times; "the draft / earlier draft" in Parts 17 and 19 (19.6 has 18). Instruction: delete every "(untested here)" from comments and prose; put one admonition at the top of each Commands section ("These commands were not run on hardware for this book; check flags against your version"). Remove "V16 Ch 3" style tags from tables, diagrams, lab output, checkpoint questions and answers; keep source attribution only in the Sources section. Delete "Corrections to the author's notes", MIGRATION_MAP lists, "Verification log" and any sentence about earlier drafts; move them to planning/ledgers.
2. **Book citations as sentence subjects.** 459 hits ("*Production Kubernetes*, chapter 13, warns", "Chris Fregly details"). Instruction: state the fact in the book's own voice; cite in Sources; at most one "as X shows" per chapter when the source is the point.
3. **Openings.** 191 "Picture ..." openers across 100 files; "This chapter serves the ... round" in 30 Part 20 files; "background reading ... figures below are examples" blocks in 36 Part 16 to 18 files; recap openers ("Chapter 16.1 named ..."). Instruction: first paragraph is a specific incident or decision with a time, a system and a consequence, no "Picture"; delete the background-reading blocks; in Part 20 move "serves the X round" to a one-line tag under the title.
4. **Numbers.** Part 12 and 15 average 4 to 7 numbers per 100 words and duplicate them ("4:1 / 4.00:1", "40.0 ms (40 ms)"). Instruction: remove every parenthetical restatement of the same number; keep one unit; move counter dumps after the prose as a short worked example with one sentence saying what it shows.
5. **LaTeX inside code formatting.** 142 hits in 17 Part 12 files. Instruction: replace backticked TeX with $...$ (the site supports it) or plain words; never put `\rightarrow` in a table cell, write "to".
6. **Exercise blocks.** Parts 10 to 15: "Using function X in code/partNN calculate ..." parameter dumps and boilerplate intros ("Work through these six exercises", 21 files); Parts 16 to 18: "Add an X. *Solution sketch:*" build tasks. Instruction: each chapter gets 4 to 6 exercises of three kinds: one diagnosis from evidence, one calculation with a stated answer, one decision with trade-off; no exercise may ask for a source's table or chapter number; Parts 16 to 18 exercises must have a checkable outcome.
7. **Checkpoint questions that test the source, not the concept.** "In Volume 11 Chapter 3, what ...". Instruction: rewrite as scenarios ("A pod requests mig-3g.40gb and stays Pending while 12 1g slices are free. Why?").
8. **Version pins that disagree.** vLLM gpu_memory_utilization default (0.90 vs 0.92), NCCL timeout (10 vs 30 min), dcgm-exporter names (4.8 vs 4.9). Instruction: one "versions this book was checked against" table in Part 0 or 20; chapters say "in vLLM v0.32.0" once and link to it; a worker grepping for each pinned default must make all chapters agree.
9. **Chapter length.** 25 chapters over 12k words. Instruction: a chapter over 12k words is split at its largest second-level section; each half keeps its own opening story and exercises.
10. **Tables carrying explanation.** Five-column tables with bold and backticked numbers in every cell (12.23, 11.24, 15.3). Instruction: any table cell longer than 20 words becomes a paragraph; no bold inside tables.
11. **Off-topic migrated paragraphs.** 11.9 (RAG), 11.11 (fio), 11.21 (mpstat), 11.22 (compromised pod), 12.17 (TPS/RPS), 17.10 (textbook process model). Instruction: a paragraph whose subject is not in the chapter title or outcomes is deleted or moved to the chapter that owns it.

---

## 5. Priority rework list (40, ranked)

1. **18.5** Rebuild from a threat table: cross-tenant GPU memory read, host escape via the container toolkit, noisy neighbour, side channel, data remanence. Map each to the control that stops it (GPU virtual memory per context, MIG, IOMMU for host memory, toolkit patching, CDI). Delete every invented command and config; link 11.21 to 11.26 for mechanics; name CVE-2024-0132 and CVE-2025-23266.
2. **15.3** Correct the swap-vs-recompute numbers (289 ms recompute; ~42 ms GQA round-trip swap) and state that V1 recomputes because swap was removed. Label sparse TFLOPS; delete the PP stage-imbalance failure mode; replace V0 names and the api_server example with `vllm serve`; remove API price lists. Split at section 4.
3. **17.4** Replace the alert file with fault-signal alerts (row remap, ECC DBE rate, Xid by tier, throttle violation counters, NVLink/PCIe error rates, absent exporter). Remove the high-utilisation, memory-used and clock-below-base alerts. Delete every "the draft"; make the lab use PrometheusRule and `dcgmi test --inject`.
4. **10.8** Fix persistence mode and PyTorch allocator mechanisms; add SM_ACTIVE/TENSOR_ACTIVE as the honest utilisation and an NCCL-hang signature row. Delete section 5.5, the corrections section and the migration list; strip source tags from tables, lab output and answers. Replace the W/°C exercise.
5. **14.11** Fix NCCL default timeout (10 min), remove gradients from checkpoint payload, fix Xid 63, fix the code sample to save dataloader and per-rank RNG state, remove the swap-file advice. Own fault tolerance and elastic training; move storage-path content to 13.7.
6. **13.7** Remove the five components, gather-vs-sharded and Young-Daly material duplicated in 14.11; own the storage side (tiers, striping, async write path, atomic publish, retention, cuda-checkpoint). Link 14.11 and 19.4 for the rest.
7. **18.6** Rewrite as a short chapter on what BlueField and confidential computing actually guarantee (attestation flow, CC mode on H100/B200, performance cost, what is still trusted); link 11.27/11.28 for mechanics. Remove "Add an alert" exercises.
8. **18.2** Rewrite around SPDM/device attestation, firmware signing, BMC trust and secure boot with concrete commands and failure stories. Add one GPU firmware incident pattern.
9. **18.7** Rewrite around model-weight protection (encryption at rest, KMS, signed artifacts, safetensors vs pickle, access audit) with checkable exercises.
10. **11.24** Fix the impossible profile combination and driver/CUDA pairing; replace the drain loop; add GKE MIG node pools and per-instance DCGM labels; rewrite checkpoint questions as scenarios.
11. **12.23** Fix srun env passing; convert all TeX-in-backticks; remove duplicated numbers; move counter blocks after prose; replace trivia checkpoint questions.
12. **Part 12 TeX sweep (17 files)** Mechanically replace backticked TeX and `\rightarrow` in all Part 12 files with $...$ or words. Verify in the built site that no backslash commands render.
13. **16.7** Fix transformer, shadow mode, NetworkPolicy and BentoML code; add an LLM-on-KServe section (RawDeployment, vLLM runtime, modelcar, inference gateway). Check Seldon/Yatai status.
14. **15.1** Replace the "In today's AI landscape" opening with a concrete request story; cut sentence length to 15 to 20 words; move stage timing tables after the narrative.
15. **17.16** Rewrite around concrete AI-assisted ops patterns (alert summarisation with guardrails, anomaly detection on DCGM with false-positive budgets, LLM runbook assistants and their failure modes) and scaling limits (Prometheus cardinality, fleet automation). Delete vague advice.
16. **17.10** Remove the software-process textbook passage; build the chapter around a GPU driver and GPU Operator upgrade with canary pools, drain policy and rollback evidence.
17. **17.6** Add multi-window burn-rate alerting with worked numbers for a token API, and link 20.19 as the owner of token SLOs. Keep GPU health checks.
18. **17.7** Turn the failure catalogue into symptom/detect/first-action with real signals; remove the "Read the diagram" opener.
19. **17.13** Add GPU-fleet reliability numbers (failure rates from the Llama 3 405B table, MTBF per node, spare-pool sizing) and an error-budget policy.
20. **18.4** Remove the off-topic patch paragraph; add GPU-specific RBAC risks (device plugin, privileged DaemonSets, hostPath /dev) and Pod Security for GPU pods.
21. **12.21** Split into storage networks, Ultra Ethernet, and scale-up fabrics; each under 9k words with its own opening.
22. **15.12** Split at its largest section; remove repeated KV and graph-bucket arithmetic already in 15.3/15.11.
23. **15.13** Split into "profiling inference" and "debugging inference at scale"; link 20.18 for the failure catalogue.
24. **12.14** Split into load balancing (ECMP, flowlets, DLB, packet spraying) and routing protocols for AI fabrics.
25. **12.19 + 13.3** Merge GDS into 13.3; keep GPUDirect RDMA in 12.19 and cut the duplicated bounce-buffer tables.
26. **12.17** Remove the inference TPS/RPS paragraph; make it the concept chapter for nccl-tests and link 19.5 for the lab and 12.23 for acceptance policy.
27. **11.32 + 11.33** Merge into one NVKE architecture and installation chapter; remove the tag legend and first-person "on this Mac" from the body.
28. **11.13 to 11.18** Merge six KAI chapters into three (why and architecture; queues, gang and topology; sharing and operations). Keep one fault table per chapter.
29. **11.9** Delete the RAG/vector-DB paragraphs; keep JobSet/LWS/PyTorchJob/MPI.
30. **11.11** Delete the fio storage-validation paragraph; replace with Network Operator upgrade and NicClusterPolicy failure cases.
31. **10.12 + 10.17** Merge streams and stream-ordered allocation; remove "Chris Fregly details" and "Volume 03 Chapter 8 parameters".
32. **10.13 + 10.15, 10.16 + 10.18** Merge into two chapters and mark them optional for SRE readers; keep one worked kernel each.
33. **10.19 + 14.9** Merge torch.compile into 14.9; delete PEP-number trivia.
34. **14.8** Replace book-table references in exercises with self-contained data; reduce parentheses and code formatting.
35. **15.16** Align probe, circuit-breaker and preemption advice with 20.18/20.21; remove the swap-space guidance or mark it pre-V1.
36. **15.10 + 15.11** Merge disaggregation chapters; keep one worked DistServe example.
37. **15.15 + 20.20** Merge autoscaling into 20.20 and leave a short KEDA/HPA how-to in 15.15 or cut it.
38. **12.4 + 12.5** Merge PFC/ECN/DCQCN with DCB/QoS into one chapter with one buffer-threshold worked example.
39. **13.5** Remove the repeated GDS table; compare BeeGFS, Weka, VAST and object storage on metadata rate, small-file behaviour and failure modes.
40. **19.6 and Part 19 draft-history sweep** Delete every "earlier draft" sentence in 19.2, 19.4, 19.5, 19.6, 19.8, 19.9, 19.10, 19.12 and the status sentence in 19.14; keep corrections in ledgers.

---

## 6. Technical correctness watch list

Confident errors (with evidence):
- 10.8: persistence mode "kernel unloads /dev/nvidia* ... re-enumerate PCIe, reload modules". Wrong; driver deinitialises GPU state when no client holds it. NVIDIA driver persistence docs; 19.14 states it correctly.
- 10.8: PyTorch caching allocator "reserves 75% to 95% of VRAM upfront". Wrong; grows on demand. PyTorch CUDA semantics docs; JAX docs for the 75 percent default.
- 10.8: cooling capacity "3 W/°C" model and exercise. Not physical; thermal resistance is °C/W relative to inlet temperature.
- 11.24: "1 x 4g.40gb + 2 x 2g.20gb valid at 80 GB" (8 compute slices). NVIDIA MIG User Guide.
- 11.24: "575.10 (CUDA Version: 12.5)". Driver 575 = CUDA 12.9. CUDA release notes.
- 11.24: drain by DCGM field 203 under MIG; layout change does not need rmmod.
- 12.23: `srun -x NCCL_...`; -x is --exclude. srun man page.
- 12.23: "Disabling IOMMU (iommu=pt)"; pt is passthrough, not disabled.
- 14.11: NCCL default timeout 30 min. PyTorch docs: 10 min for NCCL; 12.18 agrees.
- 14.11: checkpoint includes 4 B/param gradients.
- 14.11: Xid 63 called uncorrectable.
- 14.11: swap file for pinned staging buffers.
- 15.3: t_recompute 29.01 ms (actual 289 ms by its own formula and code); conclusion inverted for GQA.
- 15.3: H100 "TF32 989, BF16 1,979, FP8 3,958" unlabelled sparse figures; same chapter uses 989 as dense BF16.
- 15.3: PP stage 0 vs stage 1 KV imbalance mechanism.
- 16.7: transformer as sidecar; shadow via canaryTrafficPercent 100; NetworkPolicy blocks model download; BentoModel.predict.
- 17.4: alert rules (high util, FB used > 90 percent, SM clock < 1400 MHz, temperature as throttle proxy, Xid gauge > 0 never clears).
- 17.4: cardinality row "12 metrics x 8 metrics per GPU x 1000 GPUs".
- 18.5: cross-tenant GPU memory read "via DMA" stopped by IOMMU; time-slicing "no memory isolation"; non-MIG vGPU called spatial.
- 18.5: `nvidia-smi -vgpu 1`; `nvidia-smi mig -cgi 0,1,2,3,4,5,6 -C`; `cat /sys/class/iommu/*/devices/*`; perf iommu events; time-slicing `interval`/`timeout` fields; IAM roles `gpusharing.*`; IOMMU "logs DMA accesses".
- 20.18 vs 15.3: gpu_memory_utilization default (0.92 in v0.32.0 source per 20.18; 0.90 in 15.3).

Needs checking:
- 10.8: APPLICATIONS_CLOCKS_SETTING bit tied to `-lgc` vs `-ac`.
- 10.8 and 17.4: H100 base clock "1.4 GHz" (SXM5 datasheet lists a higher base).
- 12.10: Giga Data Rate positioning and per-lane rates.
- 12.23: DOM thresholds "Rx >= -6.0 dBm, Tx >= -4.0 dBm" as universal pass criteria.
- 13.6: "MDS limit 50,000 to 100,000 ops/sec"; "num_workers * 8 processes".
- 15.2, 15.18: "inference accounts for up to 90 percent" (unsourced in the digest).
- 15.3: Falcon-40B and Command-R as MQA examples; "--swap-space removed in v0.18.0"; `long_prefill_token_threshold` described as chunk size; Claude/GPT/Gemini cache prices.
- 15.3, 19.3, 20.18, 20.22: vLLM v0.32.0 version and defaults (released 2026-10-18 per 20.18; after my knowledge cutoff).
- 16.7: Seldon Core v1 vs v2 and licence; Yatai deprecation; KServe image registry.
- 17.4, 19.7, 10.8, 11.24: dcgm-exporter 4.9.0 rename (dated 2026-11-06).
- 19.5, 20.x: NCCL 2.31 diagnostics, NCCL_DEBUG=ATTN in 2.32, RAS port.
- 11.12: `resource.k8s.io/v1` at Kubernetes 1.34 (I believe correct).

---

## 7. Structural advice

1. **Give each concept one home and link to it.** Owners: GPU health/DCGM/Xid = 10.21 (10.8, 11.24, 17.4, 19.6 link); profiling = 10.20 for GPU, 15.13 for inference, 14.8 for training (17.5 cut); checkpoints = 13.7 storage side, 14.11 training side (19.4 capstone, 20.17 drill link; Young/Daly derived once in 14.11); GDS = 13.3; nccl-tests = 12.17 concept, 12.23 acceptance policy, 19.5 lab; autoscaling inference = 20.20; token SLOs = 20.19; capacity and cost = 19.9 (13.8 storage, 15.18 tokens, 17.12 cut or merge); GPU sharing security = 11.26 decision + rebuilt 18.5 threats.
2. **Add a bridge chapter at the start of Part 12** (about 5k words): what a collective is, why the slowest link sets the step time, the three fabrics, the vocabulary (rail, leaf, spine, oversubscription, RDMA, lossless). 12.1 at 16k words cannot be the on-ramp.
3. **Add a bridge at the start of Part 15**: the request path in plain words (prefill, decode, KV cache, batching) before 15.1's stage timing; 20.18's "three places a request waits" is the right model to introduce here and reuse.
4. **Move CUDA kernel programming (10.13 to 10.18) behind a clearly marked optional track.** Put operational chapters (10.8, 10.9, 10.21, 10.22) earlier in Part 10, right after 10.6, so an SRE reader meets nvidia-smi, the driver stack and Xid before warp specialisation.
5. **Shrink vendor-product clusters.** KAI 6 to 3 chapters, NVKE 3 to 2, Run:ai merged into 11.31.
6. **Rebuild Part 18 and deepen Part 17** using Part 20's method (one model, real signals, symptom/confirm/mitigate/fix). Part 17 should own: GPU fleet health automation loop, burn-rate alerting, change management for drivers/operators, toil and on-call metrics, with links to 20.19 to 20.27 for interview framing.
7. **One version table** (vLLM, NCCL, DCGM/dcgm-exporter, GPU Operator, Kubernetes, CUDA/driver) that all chapters reference, so defaults stop disagreeing across parts.
8. **Use 20.18, 19.5 and 19.14 as the exemplars** in the worker prompt for Parts 10 to 18: incident opener, one mental model, decision rule per section, numbers few and sourced, process notes in the ledger only.
