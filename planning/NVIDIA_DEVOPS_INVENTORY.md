# nvidia-devops inventory: every existing topic must be present in the handbook

The author's repo `nvidia-devops` (26 zero-to-hero volumes ≈ 0.95M words, legacy 9 volumes ≈ 0.14M, core interview ≈ 43k) is indexed in the study corpus as `nvidia-devops-zth-vNN`, `nvidia-devops-legacy-vNN`, `nvidia-devops-core-interview` (search with `tools/study_rag/query.py --book nvidia-devops`). Outlines: `planning/source-outlines/nvidia-devops-*.md`.

Rule: the handbook re-teaches each topic in the book's own structure and at the depth of the strongest source (book, vendor PDF, or the author's own volume, whichever is deepest), then adds what is missing. Nothing in this table may be dropped; if a topic is merged, its coverage file says where.

## Volume → handbook mapping

| nvidia-devops volume | Handbook home | Extra sources to deepen | Known thin spots to fill |
|---|---|---|---|
| ZTH V01 Architecture of accelerated computing (AI infra, CPU vs GPU, inference request, K8s vs Slurm, AI factory power/cooling, NVIDIA ecosystem) | Part 0, 7.1, 10.5 | AF, ASP ch.1-2, SuperPOD PDFs | power/cooling depth |
| V02 GPU architecture (warps, memory hierarchy, occupancy, topology, perf model) | 7.1a-d | ASP ch.6-9 | profiling workflow |
| V03 CUDA (stack, execution model, memory, streams, graphs, compilation, profiling) | 7.2 series | ASP ch.6-12 | none major |
| V04 Hardware portfolio (families, PCIe vs SXM, T4/L4/L40S, training accelerators, Grace) | 7.4a-b | ASP ch.2, SuperPOD PDFs | latest generations |
| V05 DGX (H100 internals, management plane + Redfish, power/cooling, storage paths, networking, GH200/GB200 NVL72) | 7.4c, 6.x BCM/Redfish, SuperPOD series | SuperPOD PDFs, BCM, Redfish PDFs | Redfish practice, BMC ops |
| V06 HGX and OEM integration | 7.4d | | OEM support boundaries |
| V07 GPU networking and data paths (PCIe/NUMA, NVLink/NVSwitch, RDMA, GPUDirect RDMA/Storage, ConnectX, placement, NCCL) | 7.x, 8.x | ADC, ASP ch.4, DAI | Fabric Manager, NVSM |
| V08 InfiniBand (12 chapters) | 8.3a-e | SCL ch.5, ADC | UFM, SHARP |
| V09 Ethernet for AI (RoCEv2, PFC, ECN/DCQCN, DCB/QoS, Spectrum, ConnectX, BlueField/DOCA) | 8.2, 8.4-8.7 | ADC ch.3-8 | Spectrum-X, SONiC/Cumulus, UEC |
| V10 Kubernetes GPU platform (toolkit/CDI, device plugin, NFD/GFD, GPU Operator, scheduling, DCGM, upgrades) | 7.6a-h | GAK ch.3,7 | JobSet, LeaderWorkerSet, Kueue, Topology Manager |
| V11 GPU sharing (MIG, time-slicing, vGPU, comparison, scheduling, security, chargeback, SLOs) | 7.12-7.14 | GAK ch.3 | **VFIO, SR-IOV mechanics, vGPU licensing internals** |
| V12 Inference (Triton, TensorRT, TRT-LLM, vLLM/TGI/SGLang, batching, KV cache, scaling, benchmarking) | 9.7-9.10 | HLS, DAI ch.6-7, ASP ch.15-19 | Dynamo, NIXL |
| V13 Distributed training (memory anatomy, DDP, FSDP, ZeRO, TP/PP/EP, Megatron, NCCL, checkpointing) | 9.4-9.5 | DAI ch.3-5, ASP ch.13 | fault tolerance |
| V14 NVIDIA AI Enterprise (NIM, NeMo, guardrails, NGC, licensing, lifecycle) | 10.4 | | NIM ops |
| V15 AI storage (NVMe, GDS, Lustre, BeeGFS, object, checkpoints, small files) | 6.6a-d | SCL ch.9, ADC ch.9 | GPFS/Weka, tuning |
| V16 GPU observability (signals, DCGM, Prometheus/Grafana, distributed, tracing, failures, SLOs) | 11.4 | PK ch.9, SCL ch.19 | **Loki, alerting design** |
| V17 Performance engineering (profilers, roofline, bottlenecks, comm optimisation, system tuning) | 11.3, 1.8-1.10 | SP, ASP | none major |
| V18 Security (threat model, firmware trust, supply chain, RBAC, pod security, GPU sharing security, DMA/IOMMU/SR-IOV security, BlueField, confidential computing) | 10.6 | PK ch.8,10,15 | attestation practice |
| V19 Production operations (lifecycle, game days, capacity, cost, multi-tenancy, DR, runbooks) | 11.1 | EAS | |
| V20 Troubleshooting encyclopedia (Xid, NCCL, NVLink, ECC, thermal, DMA, power, clocks, stragglers) | 11.2 | | keep every scenario |
| V21 AI Factory (design, compute/net/storage, power/thermal, software stack, training, inference, multi-region, capacity, cost, reference architectures) | 10.5, 12.x | SuperPOD PDFs, AF | |
| V22 Customer workshops (consulting method, industries) | 12.4 | | |
| V23 Interview masterclass | 12.5 | | |
| V24 Capstones (12 projects) | 12.1-12.3 | | |
| V25 MLOps engineering (DVC, MLflow, data pipelines, promotion gate, case study) | 10.1-10.3 | PM, DMLS | |
| V26 Consolidated interview questions | 12.5 | | |
| Legacy V01 Linux (compute/memory, storage I/O, networking, systemd/containers) | Part 1, 2.5 | HLW, SP | netfilter, cgroups depth |
| Legacy V02 Python | Part 3 | LP, FP, FA | |
| Legacy V03 Kubernetes (control plane, scheduling, DRA; node/storage; networking/security) | Part 5 | KUR, PK, NK | |
| Legacy V04-V09 GPU, AI workloads, networking/RDMA, observability, architecture/TCO, gauntlets | Parts 7-12 | | |
| Core interview questions | 12.5 | | |

## Gaps identified in the author's own content (must be filled)

Absent or near-absent: VFIO and PCIe passthrough, JobSet and LeaderWorkerSet, OSPF, xCAT, PXE and network provisioning, VXLAN/EVPN, netfilter/nftables, Fabric Manager/NVSM details, systemd and cgroups depth, Terraform and Ansible depth, Redfish API practice, BCM administration, Slurm administration depth, HPC cluster building and parallel programming stack.
