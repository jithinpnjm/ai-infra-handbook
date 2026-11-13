# Voice rewrite ledger: Part 11 chapters 11.4, 11.5, 11.6

Scope: `docs/part-11-gpu-kubernetes/04-*.md`, `05-*.md`, `06-*.md` only. Not committed. `planning/EXTERNAL_EDITS.md` not edited (per run instructions, step 6 ignored).

## Words, gates

| File | Words before | Words after | Growth | rewrite_guard | chain_gate | Span check | Mermaid |
|---|---|---|---|---|---|---|---|
| 04-gpu-operator-architecture-and-operands.md | 8258 | 10692 | +29.5% | 0 hard failures, new numbers 0, lost numbers 0, new code spans 9, lost 0, residue 1 to 0 | 0.0 | `{}` | `tools/check_mermaid.mjs`: 776 diagrams, 0 failed (repo-wide run) |
| 05-gpu-operator-installation-configuration-and-upgrades.md | 7825 | 10261 | +31.1% | 0 hard failures, new numbers 0, lost numbers 0, new code spans 2, lost 0, residue 2 to 1 | 0.0 | `{}` | same run |
| 06-scheduling-gpus-requests-topology-manager-cpu-and-numa-alignment.md | 9046 | 11761 | +30.0% | 0 hard failures, new numbers 0, lost numbers 0, new code spans 3, lost 0, residue 3 to 2 | 0.0 | `{}` | same run |

Word counts are `wc -w` on the whole file, before (HEAD) and after. The guard's own word column (body without code) shows 7197 to 9631, 6266 to 8702, and 7233 to 9948.

`npm run build` was not run (the run instructions say no npm build for this batch).

## Method

- Each body was rewritten section by section, with headings, the title table, front matter, all code blocks, Mermaid blocks and data tables kept exactly.
- The checkpoint questions and Sources and review notes were restored byte-for-byte from HEAD after the rewrite (splice at the first `<details>` block). They are locked.
- Every section opens with a situation, except the two "Outcomes" paragraphs, which open with a plain summary of what the chapter covers (see Unresolved item 3).
- The Outcomes lists in 11.5 and 11.6, and the Prerequisites bullets in 11.5 and 11.6, were rewritten as plain paragraphs without "you will be able to".
- The "(untested here)" tags were removed from prose. They remain only inside code-block comments, which are locked.
- The one honest status sentence per chapter: 11.4 "The cluster Helm and kubectl commands in this chapter were not run on a live cluster"; 11.5 "The cluster commands in this chapter were not run on a live cluster"; 11.6 "The commands that target a real cluster in this chapter were not run on one."
- "Captured output from this repository" lines (11.4, 11.5, 11.6) became "The block below shows what a passing run prints," because the capture claim could not be checked.
- Exercises: 6 per chapter, same counts and same function names and inputs. Multi-part asks were split into single-question sentences. No nested (a)(b).
- Lab commands are unchanged: `python3 code/part11/gpu_operator_and_operands_lab.py`, `gpu_operator_upgrades_lab.py`, `gpu_scheduling_and_topology_lab.py`.

## Needs source (general explanations added in prose, no new facts)

11.4
- Kubernetes Operator as a controller that watches a custom resource; reconciliation as compare-and-correct; node selector; DaemonSet and CRD as general terms.
- Canary pool, SLO (service level objective), headroom, and maxUnavailable as the number of Pods a rolling update may take down at once.
- Init container as a container that finishes before the main container starts; crash loop; privileged container; bind mount; trap as a shell hook on termination signals.
- Kernel headers as the definitions a module must match; file descriptor as an open handle; the `nvidia_uvm` module depends on the core `nvidia` module, so it unloads first.
- Drop-in config as a small extra file that containerd reads on top of its main file; NVML and the device plugin socket described in one sentence each.
- Secure Boot, MOK and driver DaemonSet sleep loop explained in one sentence each.
- Golden image as the reference OS image; BCM 11 described as a cluster manager.
- NVIDIA DGX as a named host type; RDMA, GPUDirect RDMA, InfiniBand, RoCE, ConnectX, MOFED, SR-IOV, NCCL described in one sentence each.

11.5
- Sandbox as the isolated environment built per container; NAT gateway as a network device.
- Git as version history for values; GitOps as cluster state taken from Git.
- Prometheus as the metrics store; PodDisruptionBudget as a limit on voluntary evictions; uncordon as making a node schedulable again.
- Xid as the numbered driver error code in the kernel log.
- Checkpoint as saved training progress; MIG-partitioned as a card split into slices with their own identity.
- Observation window; procurement batch; the reason for doubling waves (bugs that appear in only one batch).
- Secure Boot as a firmware signature check; MOK as the list of enrolled signing keys (one paragraph in the Concepts section).
- `helm template` as rendering to plain YAML; the `|| true` note explaining diff's non-zero exit.

11.6
- Taint as a node mark that repels Pods without a toleration; socket and PCIe switch as hardware terms; root complex; hint providers as kubelet components reporting NUMA hints.
- Tensor and gradient as the data that moves between GPUs; NCCL as the collective library; peer-to-peer DMA as a device-to-device transfer without a host copy.
- TLB and pageable memory; `numactl` role; closure and `functools.partial`; CUDA context as per-process driver state.
- SM as the GPU compute unit; mixture-of-experts expert-parallel inference as a split model with inter-GPU token traffic.
- Fragmentation and jitter as scheduling terms; service-class catalog explained as a menu of tiers.
- Two-door framing (scheduler door and kubelet door) is an analogy, no new facts.

## Unresolved items

1. Headings and code-block comments keep "(tested here)" and "(untested here)", because heading text and code blocks are locked.
2. Locked tails keep their original attributions ("Volume 10 Chapter 6", "Chapter 7", "Volume 10 Chapter 8", "Volume 10 Chapter 11", "Lab 04" in checkpoints and Sources). Body text does not use them.
3. "Outcomes" sections (11.4, 11.5, 11.6) open with a plain chapter summary rather than a situation, because the heading is locked and the section is only a list of what the chapter covers. The situation comes in the Prerequisites paragraph above it.
4. The dcgm-exporter 4.9.0 blockquote in 11.5 is unchanged (a blockquote atom with a link and numbers). The mapping it points to is in 17.4 and was not edited here.
5. 11.4 checkpoint 11 says "defined Chapter 7" and 11.4 Sources cite `GPU Operator v26.7.2 ClusterPolicy`; both are original locked text and were not checked against the upstream CRD in this run.
6. 11.4 "Explicit Inferences" and 11.5 "Not verified on live hardware" sections are locked, so the untested scope for their CRD and API version names remains as written.
7. Fact fixes required for this batch (dcgm-exporter 4.9.0 renames, Kueue v1beta2, KAI quota units, vLLM `--swap-space`) were checked: the dcgm-exporter note in 11.5 is present and unchanged; no Kueue, KAI or vLLM text appears in these three chapters.
8. No new numbers were introduced (guard: new numbers 0 in all three). Word-form counts like "three" existed in the originals; no new digits were added.
