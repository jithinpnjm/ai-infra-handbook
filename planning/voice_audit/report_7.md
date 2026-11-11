# Voice audit report 7 (parts 06 and 15)

Strict grading. No file got a 5. Common patterns: exercise lists and numbered lists packed with backticked names and stacked numbers; "Explain why X. Then explain Y. Finally..." chains; bold-label bullets where the label is a term stack; table-lookup sentences with six or more parenthetical items. Part 15 prose uses "we", "Notice that", and stock verbs (cripple, unlocks, delivers, slashes). Two samples (15/02, 15/03) include a raw "corrected 2026-11-11" maintenance note that is not prose.

| file | grade | main problem (one phrase) |
|---|---|---|
| 06/01 what-a-supercomputer-is | 3 | opening good; exercises are stacked numbers and acronyms |
| 06/02 cluster-anatomy | 3 | login-node paragraph is a tool and acronym list |
| 06/03 parallel-computing-concepts | 3 | one tangled SHMEM/PGAS paragraph; "(untested here)" marker mid-prose |
| 06/04 mpi-in-practice | 2 | opener is a term stack; env-var and flag dumps in backticks |
| 06/05 openmp-compilers | 3 | exercises are number-heavy command chains |
| 06/06 environment-modules-spack | 3 | list items mix many backticked terms; good opening picture |
| 06/07 slurm-architecture | 4 | munge explanation reads like a person; minor stiffness |
| 06/08 slurm-configuration | 3 | config-lookup sentences; table-intro prose flat |
| 06/09 slurm-accounting-policy | 3 | numbered plan is parameter dump; first paragraph good |
| 06/10 slurm-gpu-scheduling | 3 | one 200-word paragraph of code and flags |
| 06/11 submitting-launching-jobs | 3 | srun option list reads like a man page |
| 06/12 multi-node-training | 3 | opener lacks referent; variable names stacked |
| 06/13 containers-enroot-pyxis | 3 | lab paragraph is a list of checks in backticks |
| 06/14 slurm-operations | 4 | health-check explanation is clear; some stacked options |
| 06/15 slurm-high-availability | 3 | numbered steps dense with commands and paths |
| 06/16 slurm-on-kubernetes | 2 | term stacks, parentheses and backticks in every item |
| 06/17 other-schedulers | 3 | flat inventory lists; "so is" fragments |
| 06/18 parallel-storage-concepts | 2 | exercises stack 6+ numbers per sentence |
| 06/19 lustre-architecture | 3 | procedural, thin human voice |
| 06/20 beegfs-gpfs-weka-vast | 3 | feature-list sentences, quote-heavy |
| 06/21 parallel-io-checkpoint | 3 | abrupt jumps (ROMIO, GDS, Curator) with no thread |
| 06/22 provisioning-pxe | 4 | opening problem-first; slightly list-like |
| 06/23 xcat-warewulf | 3 | command lists inline; "(untested here)" in backticks |
| 06/24 users-ldap-sssd | 4 | plain, concrete, short |
| 06/25 remote-access | 3 | security paragraph is a checklist run-on |
| 06/26 cluster-monitoring | 2 | 150-word DCGM field dump; SNMP term stack |
| 06/27 backup-data-protection | 4 | plain and concrete; minor stiffness |
| 06/28 hpc-benchmarking | 2 | citation-key list; stat-term dump |
| 06/29 containers-reproducibility | 4 | clear, plain definition and story |
| 06/30 facility-basics | 3 | config-file narration, number stacking |
| 06/31 capstone | 2 | source list is pure code-formatted spec dump |
| 15/01 anatomy-of-inference | 3 | bullets are product and flag stacks |
| 15/02 batching-kv-cache-quantization | 3 | bold-label list prose; raw correction note in sample |
| 15/03 vllm-in-depth | 3 | "unlocks", dash-heavy; raw correction note in sample |
| 15/04 sglang | 3 | nine-stage list long-winded; jargon-dense |
| 15/05 tensorrt | 3 | stock phrases ("severe", "strict"); dense lists |
| 15/06 triton-inference-server | 3 | exercises stack 5+ numbers per item |
| 15/07 nim-and-nim-operator | 2 | broken sentences and stray commas ("**, a,**") |
| 15/08 dynamo-llm-d | 2 | fragment sentences; stray punctuation; unreadable exercise |
| 15/09 multinode-inference | 3 | abstract claims; list of options |
| 15/10 prefill-decode-disaggregation | 3 | "Notice the architectural leverage"; stacked ratios |
| 15/11 advanced-prefill-decode | 3 | acceptable but flat |
| 15/12 dynamic-adaptive-optimisations | 3 | good traffic-jam picture; others dense |
| 15/13 profiling-debugging | 3 | abstract verbs, "slashes", "delivers" |
| 15/14 benchmarking-genai-perf | 3 | opener has stacked claims; ending good |
| 15/15 autoscaling-inference | 3 | stacked numbers in opening paragraph |
| 15/16 production-serving-stack | 3 | sentence run-ons; metric-name stacks |
| 15/17 lab-serve-and-benchmark | 2 | opener is a stack of product and SKU names |
| 15/18 inference-cost-capacity | 3 | first-principles filler; "decisively" |

## Suspicious claims (note only)
- 06/26: SNMP sysUpTime OID given as 1.3.6.1.2.1.1.1.3; sysUpTime is 1.3.6.1.2.1.1.3.
- 06/01: "The line between a cluster and a non-cluster is clear" followed by "However"; likely meant blurry.
- 06/05: racy++ "lost 70-80%" but 3,487,814 of 20M is about 83% lost.
- 15/02: H100 "1,979 to 3,958 TFLOPS" are sparsity figures; dense BF16 is about 989. Also "64 to 210 sessions" on four GPUs looks odd.
- 15/08: "70 GB of weights on a 180 GB GPU leaves roughly 122 GB" does not subtract correctly (110 GB); B300 is 288 GB.
- 15/10: "another 4.66x relative to GQA-8" for MLA is unverified.
- 15/16: Nagle plus delayed ACK stall "up to 200 ms"; Linux default is about 40 ms.
- 06/30: B200 "internal N+1" with 6 PSUs needing 5; check against the user guide.

## Other flags
- Semicolon-free, but heavy parenthesis stacking in 06/18, 06/31, 06/16, 15/17.
- Code formatting on ordinary words/metrics in 06/04, 06/16, 06/26.
- Undefined acronyms at first use: HA, HTC, COTS (06/01), PMIx/OOM (06/04), DTNs ok, WQE/TTFT/TPOT (15/01, 15/08).
- Unfinished or garbled items: 06/23 "(untested here)" in backticks; 15/07 and 15/08 exercises.

## Worst 15 files with one example sentence each

1. **15/07**: "Every time a pod restarts, reschedules onto a new node. Scales out from 1 to 10 replicas, the container must download..." Human: "Every time a pod restarts, moves to a new node, or scales from one replica to ten, the container must download the whole model."
2. **15/08**: "NIC work queue element. WQE, setup and doorbell overhead choke the link." Human: "Each write needs its own setup work on the network card, and with 470 small writes that overhead chokes the link."
3. **06/26**: "`DCGM_FI_DEV_SM_CLOCK`, `DCGM_FI_DEV_MEM_CLOCK`, `DCGM_FI_DEV_GPU_TEMP`..." Human: name the four fields that explain a slow job, put the rest in a table.
4. **06/16**: "Unlimited locked memory (`ulimit -l unlimited` / `RLIMIT_MEMLOCK`)." Human: "RDMA needs to pin memory. A default container limit stops that, so jobs fail at start."
5. **06/04**: "When you understand communicators, eager versus rendezvous deadlocks, Open MPI's Modular Component Architecture, HCOLL and UCX transports..." Human: "A multi-node job hangs. This chapter shows how to find out why."
6. **06/31**: "specifies the four fabrics (`MQM9700-NS2F` storage IB at `> 40 GB/s`/node with `1:1`..." Human: one sentence per fabric, specs in a table.
7. **06/28**: "`[Joy 81]`, `[Anon 85]`, `[Jain 91]`, `[Gunther 97]`, `[Shanley 98]`..." Human: cite two key sources in a sentence; move the list to references.
8. **06/18**: "`create` (`4,585 files/s`) is roughly $80\times$ slower than cached `stat` (`378,127/s`)." Human: "Creating a file is about eighty times slower than reading its metadata from cache."
9. **15/17**: "GKE g2-standard-48 with four NVIDIA L4 GPUs and Nebius gpu-l40s-d with four NVIDIA L40S GPUs." Human: "A cheap option is a PCIe server with four small GPUs; table lists the SKUs."
10. **06/10**: "Wrap 5 training steps in `torch.profiler.profile(activities=[...], record_shapes=True...)`." Human: "Profile five training steps, then check whether communication dominates."
11. **15/06**: "A batch of 64 FP32 images totaling 38,535,168 bytes is transferred..." Human: "Compare pageable and pinned copy time for one 38 MB batch."
12. **06/11**: "`-n/--ntasks`, `-N/--nodes`, `--ntasks-per-node`, `-c/--cpus-per-task`, `--cpu-bind`..." Human: show the four options users need; link the man page.
13. **06/09**: "`PriorityWeightFairshare=100000`, `PriorityWeightQOS=50000`, `PriorityWeightAge=1000`..." Human: explain what fair-share dominates, put weights in a table.
14. **15/04**: "Any node with an active request holds a positive reference count (`ref_count > 0`) and cannot be evicted." Human: "A node in use cannot be evicted, because a request still reads it."
15. **15/02**: "Lowering precision delivers three compounding advantages for LLM serving." Human: "Lower precision helps in three ways. The model takes less memory..."
