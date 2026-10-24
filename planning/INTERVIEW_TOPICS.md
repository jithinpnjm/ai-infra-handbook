# NVIDIA AI-infrastructure interview checklist (must-cover topics)

Source: the author's real interview experience (asked: Slurm, Kubernetes pods using GPUs across multiple nodes, SR-IOV, virtualization, vGPU) plus the standard scope of senior AI-infra / solutions-architect loops. Every item below must be covered in the book to interview depth: *explain it, draw it, configure it, debug it*. Tier 1 is written first.

Book coverage legend: **S** strong in the O'Reilly books · **P** partial · **T** thin or absent (needs NVIDIA public docs, kernel/K8s docs, and hands-on verification; flag in the chapter).

## Tier 1: asked in the real interview, so highest priority

### Slurm (books: S; SCL ch.13–15, DAI ch.8)
- Architecture: slurmctld, slurmd, slurmdbd, munge, HA controllers, accounting database
- Partitions, nodes, QoS, associations, accounts; priority (multifactor), fairshare, backfill, preemption, reservations
- GPU scheduling: `gres.conf`, `AutoDetect=nvml`, `--gpus`, `--gpus-per-node`, `--gres=gpu:N`, GPU types, MIG with Slurm, cgroups device constraints (`ConstrainDevices`)
- Job life cycle: `sbatch`/`srun`/`salloc`, steps, arrays, dependencies, heterogeneous jobs, requeue and checkpoint hooks
- Multi-node launch: `srun`, PMIx/PMI2, `torchrun` under Slurm, rendezvous, NCCL env, `--ntasks-per-node`, CPU/GPU binding, topology-aware placement (`topology.conf`, block/tree)
- Containers: enroot and pyxis (`--container-image`), mounts, GPU visibility
- Prolog/epilog, node health checks, drain/resume/down, `scontrol`, `sinfo`, `squeue`, `sacct`, `sreport`, pending reason codes
- Operations: slurm.conf tuning, cloud/power-saving nodes, upgrades, failure scenarios (controller loss, node flapping, stuck jobs)

### Kubernetes with GPUs, including multi-node (books: P; GAK ch.3,7; ASP ch.3)
- Why one pod can never span nodes; multi-node jobs = a gang of pods with identical lifetime
- Device plugin model, `nvidia.com/gpu` as integer extended resource (requests must equal limits, no overcommit), NVIDIA container toolkit and runtime class, CDI
- GPU Operator components: driver container, toolkit, device plugin, GPU Feature Discovery, NFD, DCGM exporter, MIG manager, validator, vGPU manager
- Gang scheduling and queueing: Kueue, Volcano, scheduler-plugins coscheduling, JobSet, LeaderWorkerSet, Kubeflow Training Operator (PyTorchJob), MPI Operator, **NVIDIA KAI Scheduler and Run:ai (own series 7.7a-i)**
- Topology: Topology Manager, CPU Manager, NUMA/PCIe alignment, topology-aware scheduling of GPUs and NICs
- Networking for multi-node training: secondary networks with Multus, SR-IOV device plugin, RDMA shared device plugin, NVIDIA Network Operator, host networking versus secondary NIC, GPUDirect RDMA, `/dev/shm`, `IPC_LOCK`, NCCL in pods
- Dynamic Resource Allocation (DRA): ResourceClaim/ResourceClaimTemplate, DeviceClass, structured parameters, how it replaces the device-plugin model (note feature maturity per Kubernetes version)
- Sharing: time-slicing, MPS, MIG (single vs mixed strategy), what each isolates
- Failure handling: node drain on Xid, checkpointing, elastic training, preemption, pod disruption, health checks (DCGM, node-problem-detector)
- Multi-tenancy: namespaces, quotas, priority classes, fair share across teams

### SR-IOV, virtualization, vGPU (books: T; SPE ch.11 for virtualization basics, GAK ch.3 for sharing; rest from NVIDIA docs)
- PCIe, IOMMU, VFIO, device passthrough, ACS, interrupt remapping
- SR-IOV: physical function vs virtual functions, creating VFs (`sriov_numvfs`), VF drivers, switchdev/eswitch and representors, SR-IOV for NICs in Kubernetes pods
- NVIDIA vGPU: architecture (host manager, guest driver, licensing), vGPU profiles, time-sliced vs MIG-backed vGPU, SR-IOV-based vGPU on newer architectures, live-migration limits
- MIG details: profiles (e.g. 1g.10gb), GPU instances vs compute instances, reconfiguration constraints, what is shared (L2, memory bandwidth partitions) and what is isolated
- Comparison table of GPU sharing: whole-GPU passthrough, MIG, vGPU, MPS, time-slicing, containers on bare metal: isolation, performance, memory limits, fault isolation, operations cost
- Virtualized Kubernetes: Kata, KubeVirt, GPU passthrough into VMs; overhead and trade-offs
- DPUs/BlueField and SmartNICs: offload, isolation, DOCA overview

## Tier 1c: from the job-description review
HPC-style GPU-cloud roles (CoreWeave, Nebius, Gcore, AMAX, DGX Cloud) treat **Slurm, InfiniBand and NCCL** as hard requirements. Kubernetes/inference roles (Platform, MLOps Platform, LLM Inference, NIM Factory) need vLLM, Triton/TensorRT-LLM, NIM, KServe, Run:ai/KAI scheduler, GPU Operator/DCGM and node-health automation. Full mapping in `JD_MAPPING.md`.

## Tier 1b: NVIDIA platform operations (author supplied vendor PDFs)

- Base Command Manager (BCM): architecture, head node and categories, software images and provisioning, cmsh/Base View, Slurm and Kubernetes under BCM, containerization, monitoring, HA, installation (sources: bcm11-admin, bcm11-install, bcm11-containerization)
- Redfish and out-of-band management: BMC/IPMI, Redfish resource model, sessions and auth, actions, events, firmware update, fleet inventory (sources: redfish-spec, redfish-schema, redfish-resource-guide)
- SuperPOD and reference architectures: DGX B200 SuperPOD, GB300 NVL72 reference architecture, scalable units, network and storage tiers, power and cooling (sources: superpod-b200-dc, superpod-gb300-ra)

## Tier 2: expected in a senior AI-infra loop

- DGX/HGX/BasePOD/SuperPOD reference architectures; NVLink, NVSwitch, Fabric Manager; NVL72 domain; Base Command Manager
- NCCL: algorithms (ring, tree, NVLS), channels, env vars, nccl-tests, debugging hangs, topology files
- InfiniBand and RoCE: SM, routing, congestion control, PFC/ECN, rail design, UFM, diagnostics
- Linux: boot, systemd, cgroups v1/v2, namespaces, NUMA, huge pages, IRQ affinity, kernel params for GPU nodes, eBPF/perf, storage stack
- GPU health: DCGM (diag levels, health, profiling), Xid catalogue, ECC and row remapping, thermal and power capping, firmware management
- Provisioning at scale: PXE/network boot, image management, BMC/Redfish/IPMI, Ansible, Terraform, GitOps
- Storage for AI: Lustre, GPFS, WekaFS, NFS pitfalls, object storage, GPUDirect Storage, checkpointing patterns, data-loading bottlenecks
- Observability: Prometheus, Grafana, Loki, DCGM exporter, alerting design, SLOs for AI platforms
- Distributed training: DDP, FSDP, ZeRO, tensor/pipeline/expert parallelism, mixed precision, checkpoint/restart
- Inference: batching, KV cache, quantization, vLLM/TensorRT-LLM/Triton/Dynamo, disaggregated prefill/decode, autoscaling and cost per token
- MLOps/LLMOps platform design

## Tier 3: breadth and soft skills

- Security (multi-tenant GPU hosts, container hardening, secrets), compliance
- Capacity planning and cost, procurement trade-offs (HBM vs compute vs network)
- Customer-facing and executive framing; design interviews; incident post-mortems
- Python and automation for infrastructure, CI/CD for platform changes
