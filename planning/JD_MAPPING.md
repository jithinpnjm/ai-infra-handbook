# Job-description mapping: roles the book must prepare for

Source: the author's job-description review (2026-10). Roles: Platform, MLOps Platform, LLM Inference, NIM Factory (Kubernetes-and-inference family: strong fit, modest gap on inference engines) and HPC-style GPU-cloud roles at CoreWeave, Nebius, Gcore, AMAX, DGX Cloud (hard requirements: **Slurm, InfiniBand, NCCL**; the biggest gap).

## Requirement → where the book teaches it

| Requirement from the JDs | Chapters (see CURRICULUM_MAP) | Hands-on lab / portfolio item | Priority |
|---|---|---|---|
| Slurm (partitions, accounting, sbatch/srun, GPU gres, multi-node) | 6.3a-f | Run a small Slurm cluster (GCP/Nebius), multi-node `torchrun` job | **Tier 1 (biggest gap)** |
| Slurm on Kubernetes (Slinky, Soperator) | 6.3g Slurm on Kubernetes | Deploy Slinky or Soperator on a test cluster | Tier 1 |
| InfiniBand, RoCE vs IB, GPUDirect RDMA | 8.2, 8.3a-e, 7.6e | Rent a 2-node IB cluster for a weekend; `ib_write_bw`, `ibdiagnet` | **Tier 1** |
| NCCL (algorithms, env, topology, debugging) and nccl-tests | 8.6a-e | Run `nccl-tests` on multi-GPU/multi-node instances | **Tier 1** |
| Kubernetes GPU platform (GPU Operator, DCGM, node health automation; close to Mission Control / DGX Cloud) | 7.6a-h, 7.7, 11.4 | Node-health automation: DCGM health + taint/drain controller | Tier 1 |
| Multi-node GPU jobs on K8s (gang scheduling, Kueue/Volcano/JobSet/LWS) | 7.6c |
| **KAI Scheduler and Run:ai** (queues, fair share, gang scheduling, GPU fractions, preemption) | **7.7a-i (dedicated series)** | Multi-tenant GPU queues on GKE with a PyTorchJob gang and preemption demo | **Tier 1** |
| (multi-node jobs lab continues) | | Multi-node PyTorchJob with Kueue on GKE | Multi-node PyTorchJob with Kueue on GKE | Tier 1 |
| Inference engines: vLLM, SGLang, TensorRT-LLM, Triton, NIM, Dynamo | 9.7, 9.8a-f | Deploy vLLM, then Triton/TRT-LLM, then NIM on GKE; benchmark latency and throughput | Tier 1 (modest gap) |
| KServe and model serving platforms | 10.7 | KServe InferenceService with autoscaling on GKE | Tier 1 |
| NIM Factory / NIM Operator, NeMo, NGC | 10.12 | Deploy NIM via NIM Operator | Tier 1b |
| MLOps platform (pipelines, registry, tracking, feature store, orchestration) | 10.1-10.13 | End-to-end pipeline on GKE (see MLOps tools series) | Tier 1 |
| GPU virtualization and sharing (MIG, vGPU, SR-IOV, time-slicing) | 7.10-7.14 | MIG partitioning lab; compare sharing models | Tier 1 |
| DGX BasePOD / SuperPOD architecture, BCM, Mission Control | SP-1..8, BCM-1..8 | Read-only architecture study plus BCM install walkthrough | Tier 1b |
| Redfish, BMC, firmware, fleet automation | RF-1..8 | Query a BMC or Redfish mock server with Python | Tier 1b |
| Lustre, Weka, parallel storage | 6.6a-e | Lustre basics lab on cloud VMs | Tier 2 |
| Go operators with kubebuilder | 5.10a-d Operators and controllers in Go | Build a small GPU-node-health operator | Tier 2 |
| Observability, SLOs, incident response | 11.4, 11.1, 11.2 | DCGM exporter + Prometheus + Grafana + Loki stack | Tier 2 |
| Terraform, Ansible, GitOps for clusters | 4.2-4.7 | Provision a GPU cluster with Terraform + Ansible | Tier 2 |

## Portfolio projects (also the capstones in Part 12)
1. **Inference on GKE:** vLLM → Triton/TensorRT-LLM → NIM, add KServe and KAI/Run:ai scheduler, benchmark latency and throughput, publish the numbers.
2. **Node health automation:** GPU Operator + DCGM health checks + automated cordon/drain/repair (a mini Mission Control).
3. **Slurm, then Slurm on Kubernetes:** small cluster, `sbatch`/`srun`, partitions and accounting, then Slinky or Soperator.
4. **RDMA/IB/NCCL weekend lab:** rent a multi-node fabric, run `nccl-tests`, document bus bandwidth, failure injection.
5. **Storage and architecture study:** Lustre/Weka basics, BasePOD/SuperPOD design exercises, and a kubebuilder operator.
