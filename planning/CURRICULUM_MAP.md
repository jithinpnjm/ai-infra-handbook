# AI Infrastructure Handbook: Curriculum Map (DRAFT v1, for review)

Goal: one self-contained book, basics to advanced, for a DevOps engineer moving into AI infrastructure / AI factory platform roles. Original prose only. Books are research inputs and are credited in each chapter's "Sources" line. Nothing is copied.

Level key: **B** basics refresh, **I** intermediate, **A** advanced. Every chapter climbs B → I → A where the topic allows it.
Lab venue: **M** Mac, **G** GCP, **N** Nebius GPU.
"Reuse" = your existing `nvidia-devops` volume (V#) to mine for structure and material.

## Source codes

HLW How Linux Works 3e · SP Systems Performance 2e · SCL Supercomputers for Linux SysAdmins · CN Computer Networking Problems & Solutions · NPA Network Programmability & Automation 2e · NK Networking and Kubernetes · KUR Kubernetes Up & Running 3e · PK Production Kubernetes · GAK Generative AI on Kubernetes · AUR Ansible Up & Running 3e · TUR Terraform Up & Running 3e · LP Learning Python 6e · FP Fluent Python 2e · FA Building Python Web APIs with FastAPI · ASP AI Systems Performance Engineering · ADC AI Data Center Network Design · ANC AI Networking Cookbook · DAI Distributed AI Systems · HLS Hands-On LLM Serving & Optimization · AIE AI Engineering · DMLS Designing ML Systems · EAS Engineering AI Systems · LEH LLM Engineer's Handbook · LLO LLMOps · PM Practical MLOps · AF AI Factory (limited fit: Distributed Computing, Software Engineering, Roadmap chapters only).

## Continuity

`planning/HANDOFF_PROMPT.md` is the prompt to paste into any new session or different model so depth, scope and rules stay identical. `planning/STATUS.md` tracks progress and `planning/BACKLOG.md` collects ideas that are out of scope for the current chapter.

## Chapter template (every chapter)

1. Why this matters for AI infra (a paragraph, role-specific)
2. Prerequisites and what you will be able to do afterwards
3. Concepts: basics → intermediate → advanced, with an original Mermaid diagram of the mental model
4. Commands and configs that matter (annotated, runnable)
5. How it fails: 4–6 failure modes with symptoms, diagnosis, fix
6. Hands-on lab (venue tagged, with expected output)
7. Checkpoint questions (8–12, with answers)
8. Sources and further reading

## Parts and chapters

### Part 0: Orientation
| # | Chapter | Level | Notes |
|---|---|---|---|
| 0.1 | The AI factory landscape and the roles in it | B | AF ch.11, V21 |
| 0.2 | How to use this book, lab setup (Mac, GCP, Nebius) | B | new |

### Part 1: Linux, from first principles to performance
| # | Chapter | Level | Sources | Reuse |
|---|---|---|---|---|
| 1.1 | The Linux big picture: kernel, userspace, boot | B | HLW 1,5,6 | V1 |
| 1.2 | Files, permissions, users, devices | B | HLW 2,3,7; SCL 7,11,12 | V1 |
| 1.3 | Processes, scheduling, signals, resource use | B→I | HLW 8; SP 3 | V1 |
| 1.4 | Disks, filesystems, LVM, RAID | I | HLW 4; SP 8,9 | V15 |
| 1.5 | systemd, logging, time, cron | I | HLW 6,7; SCL 30 | V1 |
| 1.6 | Shell scripting that survives production | B→I | HLW 11; SCL 28,29 | V1 |
| 1.7 | Containers' kernel foundations: namespaces, cgroups | I→A | HLW 17; SP 11 | V1 |
| 1.8 | Performance methodology: USE, workload, drill-down | I→A | SP 1,2,4 | V17 |
| 1.9 | CPU, memory, NUMA and the cost of getting them wrong | I→A | SP 6,7 | V17 |
| 1.10 | Tracing: perf, ftrace, BPF | A | SP 13,14,15 | V17 |

### Part 2: Networking, from packets to data centers
| # | Chapter | Level | Sources | Reuse |
|---|---|---|---|---|
| 2.1 | Models and addressing: layers, IP, subnets | B | CN 1,2; HLW 9 | V1 |
| 2.2 | TCP, UDP, congestion and loss | B→I | CN 2,3,5 | |
| 2.3 | Switching, VLANs, ARP/ND, STP | I | CN 4,6,7,11 | |
| 2.4 | Routing: static, OSPF, BGP | I | CN 12–17; ADC 8 | V9 |
| 2.5 | Linux networking toolbox: ip, ss, tc, netfilter, bonding | I | HLW 9,10; NK 2; SP 10 | V1 |
| 2.6 | Overlays, VXLAN, virtualization, tunnels | I→A | CN 9; NK 3 | |
| 2.7 | QoS, queuing, ECN/PFC fundamentals | I→A | CN 8; ADC 7 | V9 |
| 2.8 | Data center topologies: leaf-spine, Clos, failure domains | A | CN 19,20,22,23; ADC 3 | V9 |
| 2.9 | Network automation: APIs, YANG, templates, CI | I | NPA 2,8,9,10,13,14; CN 26 | |
| 2.10 | Network security and troubleshooting method | I | CN 10,21,24 | V18,V20 |

### Part 3: Python for infrastructure engineers
| # | Chapter | Level | Sources |
|---|---|---|---|
| 3.1 | Python core: types, control flow, functions, modules | B | LP 4–25 |
| 3.2 | Idiomatic Python: data model, comprehensions, generators | I | FP 1–3,17; LP 14,20 |
| 3.3 | Classes, typing, dataclasses, protocols | I | FP 5,8,13,15; LP 26–32 |
| 3.4 | Errors, files, text and bytes, packaging | I | LP 33–37; FP 4 |
| 3.5 | Concurrency: threads, processes, asyncio | I→A | FP 19–21 |
| 3.6 | Building APIs and CLIs (FastAPI, Typer) | I | FA 1–9; PM 11 |

### Part 4: Automation and infrastructure as code
| # | Chapter | Level | Sources | Reuse |
|---|---|---|---|---|
| 4.1 | Git workflows and CI/CD pipelines | B→I | NPA 11,13; AUR 22 | V19 |
| 4.2 | Ansible fundamentals: inventory, playbooks, variables | B | AUR 1–5 | |
| 4.3 | Ansible at scale: roles, collections, testing, performance | I→A | AUR 9–11,14,15,20,24 | |
| 4.4 | Ansible for hosts, GPU nodes and networks | I→A | AUR 17,21; NPA 12 | V10 |
| 4.5 | Terraform fundamentals: providers, state, modules | B→I | TUR 1–4 | |
| 4.6 | Terraform in production: loops, secrets, multi-provider | I→A | TUR 5–8 | |
| 4.7 | Testing and team workflows for IaC; GitOps | A | TUR 9,10; PK 11 | V19 |

### Part 5: Containers and Kubernetes
| # | Chapter | Level | Sources | Reuse |
|---|---|---|---|---|
| 5.1 | Container images and runtimes | B→I | KUR 2; PK 3 | V1 |
| 5.2 | Kubernetes core: pods, services, deployments | B | KUR 3–12 | V10 |
| 5.3 | Config, secrets, RBAC, storage | I | KUR 13,14,16; PK 4,7 | V10 |
| 5.4 | Kubernetes networking: CNI, services, ingress, mesh | I→A | NK 4–6; PK 5,6; KUR 7,8,15 | V10 |
| 5.5 | Cluster deployment models and day-2 operations | I→A | PK 1,2; KUR 3,A | V19 |
| 5.6 | Identity, admission control, multitenancy, supply chain | A | PK 8,10,12,15; KUR 19,20 | V18 |
| 5.7 | Observability and autoscaling | I→A | PK 9,13 | V16 |
| 5.8 | Platform services and abstractions; extending K8s | A | PK 11,16; KUR 17,22 | V19 |
| 5.9 | Multicluster and fleet management | A | KUR 21; GAK 4 | |

### Part 6: HPC and job scheduling
| # | Chapter | Level | Sources | Reuse |
|---|---|---|---|---|
| 6.1 | What an HPC/GPU cluster is: anatomy and roles | B | SCL 1–4,6 | V4 |
| 6.2 | Provisioning: boot, node images, xCAT, BCM-style management | I | SCL 3,23–26 | V5 |
| 6.3 | Slurm: concepts, config, partitions, QoS, fairshare | I→A | SCL 13–15; DAI 8 | V10 |
| 6.4 | Running GPU and multi-node jobs on Slurm, containers (enroot/pyxis) | A | DAI 8; SCL 16 | V13 |
| 6.5 | Parallel programming stack: MPI, compilers, modules | I | SCL 21,22 | |
| 6.6 | Cluster file systems: NFS, Lustre, parallel I/O | I→A | SCL 9; ASP 5; ADC 9 | V15 |
| 6.7 | Cluster monitoring, accounting, quotas, backup | I | SCL 12,19,20 | V16 |

### Part 7: GPU and the NVIDIA stack
| # | Chapter | Level | Sources | Reuse |
|---|---|---|---|---|
| 7.1 | GPU architecture: SMs, memory hierarchy, tensor cores | B→I | ASP 2,6; DAI 2 | V2 |
| 7.2 | CUDA programming for infra engineers: kernels, streams, memory | I | ASP 6–9 | V3 |
| 7.3 | NVIDIA software stack: drivers, CUDA toolkit, container toolkit | I | ASP 3 | V3,V14 |
| 7.4 | DGX and HGX systems, NVLink, NVSwitch, topology | I→A | ASP 2; ADC 13 | V4–V6 |
| 7.5 | GPU sharing: MIG, MPS, time slicing | I→A | GAK 3,7 | V11 |
| 7.6 | GPUs on Kubernetes: Device Plugin, GPU Operator, scheduling | A | GAK 3,7; ASP 3 | V10 |
| 7.7 | GPU observability: DCGM, metrics, Xid errors, health | A | GAK 5; ASP 13,16 | V16 |
| 7.8 | Profiling GPU workloads: Nsight, PyTorch profiler, occupancy | A | ASP 7–9,13 | V17 |
| 7.9 | Tuning the host: OS, NUMA, IOMMU, huge pages for GPU nodes | A | ASP 3 | V17 |

### Part 8: AI networking
| # | Chapter | Level | Sources | Reuse |
|---|---|---|---|---|
| 8.1 | AI workload traffic: collectives, incast, elephant flows | I | ADC 1,2; ASP 4 | V7 |
| 8.2 | RDMA and RoCEv2: transport, PFC, ECN, DCQCN | I→A | ADC 7; CN 8 | V9 |
| 8.3 | InfiniBand: subnet manager, routing, congestion control | I→A | SCL 5; ADC 8 | V8 |
| 8.4 | Fabric design: topologies, oversubscription, optics, power | A | ADC 3–6 | V7 |
| 8.5 | Load balancing and routing for AI fabrics | A | ADC 6,8 | V9 |
| 8.6 | NCCL: collectives, algorithms, tuning, debugging | A | ASP 4; DAI 2,10 | V13 |
| 8.7 | Storage networks, UEC, scale-up fabrics, telemetry | A | ADC 9–13 | V15 |

### Part 9: ML for infrastructure engineers
| # | Chapter | Level | Sources | Reuse |
|---|---|---|---|---|
| 9.1 | ML and deep learning fundamentals (just enough math) | B | DMLS 1,2,6; EAS 3 | V13 |
| 9.2 | Foundation models and LLM architecture | I | AIE 2; EAS 4; LEH 1 | V12 |
| 9.3 | Data pipelines and dataset engineering | I | DMLS 3–5; AIE 8; LEH 3 | V25 |
| 9.4 | Distributed training: DDP, FSDP, tensor/pipeline parallel | A | DAI 3,4,5; ASP 13 | V13 |
| 9.5 | Training jobs on Slurm and Kubernetes at scale; failure and checkpointing | A | DAI 8; GAK 7 | V13 |
| 9.6 | Fine-tuning: SFT, LoRA, preference alignment, infra cost | I→A | AIE 7; LEH 5,6; GAK 6; LLO 5 | V25 |
| 9.7 | Inference fundamentals: batching, KV cache, quantization | I | HLS 1–7; AIE 9 | V12 |
| 9.8 | Serving stacks: vLLM, SGLang, Triton, TensorRT-LLM | A | DAI 6,7,9; HLS 8,9; ASP 15–19 | V12 |
| 9.9 | Multi-node and disaggregated inference | A | ASP 15,17,18; DAI 6 | V12 |
| 9.10 | Benchmarking, capacity planning, cost per token | A | DAI 10; HLS 9; ASP 16 | V17 |
| 9.11 | Evaluation: models, systems, regressions | I | AIE 3,4; LEH 7; LLO 7 | |

### Part 10: MLOps, LLMOps and the AI factory
| # | Chapter | Level | Sources | Reuse |
|---|---|---|---|---|
| 10.1 | MLOps foundations: lifecycle, versioning, experiment tracking | B→I | PM 1,2,4; DMLS 10 | V25 |
| 10.2 | ML pipelines and CI/CD for models; serving on K8s | I→A | PM 3,4,6; DMLS 7,9; GAK 1,2 | V25 |
| 10.3 | Monitoring, drift, continual learning | I | DMLS 8,9; GAK 5; PM 6 | V16 |
| 10.4 | LLMOps: RAG, agents, API-first deployment | I→A | LLO 3,6; AIE 6; LEH 9,10,11; GAK 8,9 | V12 |
| 10.5 | Platform design: multi-tenant AI factory, quotas, chargeback | A | PK 12,16; GAK 7; AF 11 | V21 |
| 10.6 | Governance, security, privacy, compliance for AI platforms | A | LLO 8; EAS 9,10 | V18 |

### Part 11: Operations excellence
| # | Chapter | Level | Sources | Reuse |
|---|---|---|---|---|
| 11.1 | Reliability engineering for AI infrastructure | A | EAS 7; PK 14 | V19 |
| 11.2 | Systematic troubleshooting playbooks (GPU, fabric, scheduler, K8s) | A | SP 2; CN 24 | V20 |
| 11.3 | Performance checklist and tuning catalogue | A | ASP appendix; SP 12 | V17 |
| 11.4 | Observability stack: Prometheus, Grafana, Loki, DCGM | I→A | PK 9; SCL 19 | V16 |

### Part 12: Capstones and interview readiness
| # | Chapter | Level | Reuse |
|---|---|---|---|
| 12.1 | Capstone A: build a Slurm + Kubernetes GPU cluster on Nebius | A | V24 |
| 12.2 | Capstone B: serve and benchmark an LLM; optimise cost per token | A | V12,V24 |
| 12.3 | Capstone C: multi-node training with failure recovery | A | V13,V24 |
| 12.4 | Architecture and system-design scenarios | A | V22,V23 |
| 12.5 | Interview question bank by topic | all | V23,V26 |

## Totals and effort

93 chapters across 13 parts (Parts 0–12), 5–8k words each, so roughly 450k words and about 80 labs. This is a multi-week effort done in waves; each wave ends with a review gate.

## Waves

1. **Pilot (3 chapters):** 2.5 Linux networking toolbox, 7.1 GPU architecture, 8.3 InfiniBand. You review depth, tone and the lab format.
2. **Wave 1: Foundations** (Parts 1–4): Linux, networking, Python, automation.
3. **Wave 2: Platform** (Parts 5–7): Kubernetes, HPC, GPU stack.
4. **Wave 3: AI** (Parts 8–10): AI networking, ML, MLOps.
5. **Wave 4: Operations and capstones** (Parts 11–12), then a consistency and accuracy pass over the whole book.

## Rules

- Original wording and original diagrams. No verbatim passages, no copied figures or code beyond tiny API fragments.
- Each technical claim is cross-checked across at least two sources, or marked "single source".
- Commands are run on the lab venue where possible, and results are noted.
- Where the books are thin (Network Operator, Lustre, Grafana/Loki, executive framing), I note it and use NVIDIA's public documentation as the reference.
- Content in your existing `nvidia-devops` volumes is rewritten into the book's template, not copied wholesale, and deduplicated against these new chapters.

---

# Revision 2 (after pilot review): deeper, interview-driven

Author feedback: pilot depth was too thin versus the source books (about 10% of the material), diagrams must be larger, and real-interview topics (Slurm, multi-node GPU pods on Kubernetes, SR-IOV, virtualization, vGPU) must not be missed. See `INTERVIEW_TOPICS.md` and `COVERAGE_PROCESS.md`.

## Principles
- Chapters are split rather than compressed. Target 6–10k words per file; a topic that needs more becomes a series (a, b, c...).
- Coverage files (`planning/coverage/`) are created before writing; every source heading gets a status.
- Writing order follows tiers from `INTERVIEW_TOPICS.md`, not part numbers.

## Slurm becomes a six-chapter series (Part 6)
6.3a Architecture and installation (slurmctld, slurmd, slurmdbd, munge, HA) · 6.3b Scheduling policy (partitions, QoS, accounting, multifactor priority, fairshare, backfill, preemption, reservations) · 6.3c GPU scheduling (gres, NVML autodetect, cgroup device constraints, MIG) · 6.3d Submitting and launching multi-node jobs (sbatch/srun/salloc, PMIx, torchrun, NCCL env, CPU/GPU binding, topology-aware placement) · 6.3e Containers on Slurm (enroot, pyxis) · 6.3f Operations and troubleshooting (prolog/epilog, health checks, drain, reason codes, upgrades, failure drills)

## GPUs on Kubernetes becomes an eight-chapter series (Part 7)
7.6a Device plugin, container toolkit, CDI, runtime classes · 7.6b GPU Operator in depth · 7.6c Multi-node jobs: why a pod cannot span nodes; gang scheduling with Kueue, Volcano, JobSet, LeaderWorkerSet, Kubeflow Training/MPI operators · 7.6d Topology Manager, CPU Manager, NUMA and PCIe alignment · 7.6e Secondary networks for RDMA: Multus, SR-IOV device plugin, RDMA device plugin, NVIDIA Network Operator · 7.6f Dynamic Resource Allocation (DRA) · 7.6g GPU sharing on Kubernetes: time-slicing, MPS, MIG strategies · 7.6h Multi-tenancy, quotas, preemption, fault tolerance and health

## New: virtualization and sharing series (Part 7)
7.10 PCIe, IOMMU, VFIO and device passthrough · 7.11 SR-IOV for NICs and GPUs (PF/VF, switchdev, representors) · 7.12 NVIDIA vGPU (architecture, profiles, time-sliced vs MIG-backed, licensing) · 7.13 MIG in depth · 7.14 Choosing a GPU sharing model: comparison matrix · 7.15 VMs on Kubernetes (KubeVirt, Kata), DPUs and BlueField

## Pilot chapters to be rebuilt in depth
- 2.5 → 2.5a Inspecting Linux networking (ip, ss, counters) · 2.5b Netfilter, nftables, conntrack and NAT · 2.5c Routing policy, bonding, NIC and stack tuning · 2.5d Namespaces, veth, bridges and container wiring · 2.5e Packet capture and tracing (tcpdump, BPF)
- 7.1 → 7.1a Execution model and memory hierarchy · 7.1b Tensor cores, precision and the roofline · 7.1c GPU interconnects and system architectures (PCIe, NVLink, NVSwitch, Grace, NVL72) · 7.1d Operating GPU nodes (nvidia-smi, topology, throttling, ECC, Xid)
- 8.3 → 8.3a InfiniBand fundamentals and addressing · 8.3b Subnet manager, routing, topologies and rails · 8.3c Diagnostics and operations (ibdiagnet, counters, UFM) · 8.3d GPUDirect RDMA and NCCL on InfiniBand (including SHARP)

## Realistic size
About 150 chapter files at 6–10k words, roughly 1.0–1.2 million words, written in tier order. Tier 1 (Slurm, K8s GPU, virtualization) is about 20 files and is written first.

---

# Revision 3: HPC and supercomputer track, BMC/Redfish, BCM, SuperPOD, complete Linux and networking

New author requirements (2026-10): prepare for all HPC and supercomputer topics in the light of the AI-infra role; Linux basics to advanced; networking basics to advanced; the complete networking story for AI; Redfish; BCM; NVIDIA solutions; every topic already in `nvidia-devops` (see `NVIDIA_DEVOPS_INVENTORY.md`); fill all gaps from books, the added vendor PDFs and public documentation. Added corpus: `bcm11-admin`, `bcm11-containerization`, `bcm11-install`, `redfish-resource-guide`, `redfish-schema`, `redfish-spec`, `superpod-b200-dc`, `superpod-gb300-ra` (private PDFs, indexed; outlines in `source-outlines/`).

## New or expanded series

**Part 6 HPC and supercomputers (expanded to about 24 chapters).** 6.1 What a supercomputer is: history, TOP500, Linpack, HPC versus AI factory · 6.2 Cluster anatomy: head/login/compute/storage/management nodes, networks · 6.3a-f Slurm series · 6.4 Alternative schedulers (PBS/Torque, LSF) · 6.5a-c Parallel programming stack: MPI, OpenMP, compilers, environment modules, Spack/EasyBuild · 6.6a-e Parallel storage: NFS, Lustre, BeeGFS, GPFS/Weka, tuning, checkpoint patterns · 6.7a-c Provisioning and cluster management: PXE/iPXE, image management, xCAT, Warewulf, Ansible at scale · 6.8 Users, accounting, quotas, access (LDAP, SSSD) · 6.9 Monitoring and health at scale · 6.10 Performance benchmarking (HPL, HPCG, IOR, OSU, NCCL tests) · 6.11 Reproducible software and containers in HPC (Apptainer, enroot) · 6.12 Facility: power, cooling, racks, liquid cooling.

**Part 6B BCM and node lifecycle (new).** BCM-1 Architecture and concepts (head node, categories, node images, provisioning) · BCM-2 Installation walkthrough · BCM-3 Administration (cmsh/Base View, users, networks, power control, HA) · BCM-4 Software images and provisioning · BCM-5 Workload managers and Kubernetes under BCM (Slurm, K8s deployment) · BCM-6 Containerization in BCM (Docker, Singularity/Apptainer, enroot) · BCM-7 Monitoring and health checks · BCM-8 Day-2 operations: updates, scaling, failures. Source: the three BCM PDFs, supplemented by public docs.

**Part 6C Out-of-band management and Redfish (new).** RF-1 BMC and IPMI fundamentals · RF-2 Redfish concepts: service root, resources, collections, OData, schemas · RF-3 Redfish protocol (spec): HTTP methods, sessions and authentication, query parameters, actions, events and subscriptions, tasks · RF-4 Resource model walkthrough: Systems, Chassis, Managers, Power/Thermal, Storage, NetworkAdapters, UpdateService, LogServices · RF-5 Automating Redfish with Python and Ansible · RF-6 Firmware updates and inventory at fleet scale · RF-7 Redfish on NVIDIA DGX/HGX (management plane, BMC, GPU baseboard) · RF-8 Security hardening of BMCs. Source: the Redfish spec, schema and resource-guide PDFs, plus the author's V05 ch.3.

**Part 6D NVIDIA reference architectures (new).** SP-1 SuperPOD concepts (scalable units, fabrics, storage tiers) · SP-2 DGX B200 SuperPOD data-centre design · SP-3 GB300 NVL72 reference architecture · SP-4 BasePOD and DGX deployments · SP-5 Power, cooling, rack and liquid-cooling design · SP-6 Compute, storage, in-band and out-of-band network design · SP-7 Software stack and management (BCM, Slurm/K8s, observability) · SP-8 Sizing and capacity exercises. Source: the two SuperPOD PDFs, V05/V06/V21 of nvidia-devops.

**Part 1 Linux (expanded to about 20 chapters).** Basics: filesystem, shell, permissions, packages, users · processes, signals, scheduling · systemd in depth · storage stack (block, LVM, RAID, filesystems, NVMe, I/O scheduler) · memory management (virtual memory, NUMA, huge pages, cgroups memory, OOM) · cgroups v1/v2 and namespaces · security (SELinux/AppArmor, capabilities, seccomp, PAM, SSH hardening) · kernel and modules (DKMS, kernel parameters, boot, GRUB, initramfs) · performance tools and methodology (USE, perf, ftrace, BPF) · virtualization (KVM/QEMU, libvirt, VFIO) · shell scripting and automation. Sources: HLW, SP, SCL, legacy V01.

**Part 2 Networking (expanded to about 30 chapters, basics → advanced → AI).** Fundamentals: OSI/TCP-IP, Ethernet, ARP/ND, IP addressing, subnetting, TCP, UDP, DNS, DHCP, NAT, ICMP · switching: VLAN, STP, LACP/MLAG · routing: static, OSPF, IS-IS, BGP in depth · data-centre fabrics: Clos, leaf-spine, VXLAN/EVPN, ECMP, anycast, BGP unnumbered · QoS and congestion: queuing, ECN, PFC, DCB · Linux networking toolbox series (2.5a-e) · network virtualization and container networking · load balancing and proxies · network automation (Netconf/gNMI, Ansible, Nornir, CI) · security · observability and troubleshooting. Then **Part 8 Complete AI networking**: AI traffic characterisation, RoCEv2, PFC/ECN/DCQCN deep dives, InfiniBand series, Spectrum-X and adaptive routing, UEC, scale-up fabrics (NVLink, NVL72, SUE), optics and cabling, NCCL and collectives, storage networks, telemetry, fabric validation, design exercises. Sources: CN, NPA, ADC, SCL, NK, V07-V09, plus public docs for Cumulus/SONiC where the books are silent.

## Gap policy
Where books, PDFs and the author's volumes are all thin (VFIO and SR-IOV mechanics, JobSet and LeaderWorkerSet, xCAT/PXE, Fabric Manager, OSPF/IS-IS, EVPN), fill from public documentation. Each such chapter says which parts rest on public documentation and has a "verify against your version" box. Public lookups are part of the plan (author approved: "refer internet").

## Revised scale
About 220 chapter files at 6–10k words: roughly 1.5 million words. Writing order stays tier-driven (INTERVIEW_TOPICS.md): Tier 1 first (Slurm, K8s multi-node GPU, virtualization/SR-IOV/vGPU), then BCM/Redfish/SuperPOD (new Tier 1b, because they are NVIDIA-specific and the author supplied the source PDFs), then Tier 2, Tier 3.


---

# Revision 4: MLOps tools, inference engines and platforms, schedulers, operators, ASP capture

## AI Systems Performance Engineering (ASP) is the primary source: capture it all
ASP is the author's top-rated source. Its 20 chapters and 175+ item checklist are mapped at section level in `planning/coverage/ai-systems-performance-engineering.md` (550 rows, each mapped to target handbook chapters via `planning/coverage/asp-mapping.json`). Rules: every ASP section must end as `covered`, `moved` or `skipped` with a reason; the master checklist (appendix) becomes chapter 11.3, and each related chapter ends with a short "ASP checklist" section; ASP is the first source consulted for GPU, CUDA, NCCL, PyTorch performance and inference tuning chapters, and its depth is the minimum bar for those chapters (cross-check, do not copy).

## MLOps tools series (Part 10, expanded; this was missing as a named series)
10.1 MLOps foundations and lifecycle · 10.2 Data versioning and experiment tracking: DVC, MLflow, Weights & Biases · 10.3 Data pipelines and feature stores: Airflow, Dagster, Spark, Ray Data, Feast · 10.4 Pipeline orchestration: Kubeflow Pipelines, Argo Workflows, Flyte, Metaflow, Tekton · 10.5 Distributed compute for ML: Ray (Train, Tune, Serve), KubeRay, Kubeflow Training Operator, Katib · 10.6 Model registry, CI/CD and GitOps for models: MLflow registry, Argo CD, GitHub Actions, promotion gates · 10.7 Model serving platforms: KServe, Seldon, BentoML, ModelMesh, Triton · 10.8 LLMOps tooling: LangChain/LlamaIndex, vector databases (Milvus, Qdrant, pgvector), prompt management, guardrails, evaluation (Ragas, DeepEval), tracing (Langfuse, OpenTelemetry) · 10.9 Monitoring and drift: Evidently, Prometheus/Grafana, data and concept drift · 10.10 Cloud MLOps platforms mapped to the open-source stack: Vertex AI, SageMaker, Azure ML · 10.11 GPU-aware schedulers: NVIDIA Run:ai and KAI Scheduler, Kueue, Volcano, YuniKorn · 10.12 NVIDIA enterprise stack: NIM and NIM Operator, NeMo, Triton, Dynamo, NGC, DGX Cloud and Mission Control concepts · 10.13 End-to-end MLOps lab on GKE.

## Inference engines and serving (Part 9, expanded)
9.8a vLLM in depth (PagedAttention, scheduler, parallelism, config) · 9.8b SGLang · 9.8c TensorRT-LLM (engine build, in-flight batching, quantization) · 9.8d Triton Inference Server (model repository, backends, ensembles, dynamic batching) · 9.8e NVIDIA NIM and NIM Operator · 9.8f NVIDIA Dynamo, llm-d and disaggregated serving · 9.8g Benchmarking tools and methodology (genai-perf, vLLM benchmarks, latency percentiles, goodput) · 9.8h Autoscaling inference (HPA, KEDA, custom metrics, scale-to-zero) · 9.8i Serving on GKE with GPUs (lab).

## Slurm on Kubernetes and schedulers
6.3g Slurm on Kubernetes: Slinky and Soperator architectures, when to run Slurm on K8s, trade-offs.

## Kubernetes operators and Go
5.10a Kubernetes API machinery and controllers · 5.10b CRDs and kubebuilder · 5.10c Writing and testing an operator (a GPU-node-health operator as the running example) · 5.10d Reading the GPU Operator and Network Operator source.

## NCCL series (HPC-GPU cloud roles list it as a hard requirement)
8.6a Collectives and algorithms (ring, tree, NVLS) · 8.6b Topology, channels, transports and environment variables · 8.6c nccl-tests and benchmarking methodology · 8.6d Debugging hangs, timeouts and errors · 8.6e RDMA verbs basics for NCCL users, SHARP.

## Elevated priorities from the JD review
Slurm, InfiniBand and NCCL move into Tier 1 together with the interview topics. See `JD_MAPPING.md`.

---

# Revision 5: NVIDIA KAI Scheduler and Run:ai get a dedicated series

Author requirement: KAI Scheduler is needed (job descriptions for Platform, MLOps Platform, LLM Inference and DGX Cloud roles). It was only a name inside chapter 10.11; it now has its own series, placed in Part 7 after the multi-node scheduling chapters, with Kueue, Volcano and YuniKorn covered as comparison points.

**7.7 series: GPU-aware scheduling on Kubernetes**
- 7.7a Why the default kube-scheduler is not enough for AI: gang scheduling, queueing, fairness, bin-packing versus spreading, preemption, GPU fractions, topology awareness
- 7.7b KAI Scheduler architecture: components, how it runs next to or instead of the default scheduler, the PodGroup and Queue resources, how workloads (PyTorchJob, JobSet, Ray, plain pods) reach it
- 7.7c Queues, quotas and fair sharing: hierarchical queues, guaranteed and over-quota resources, reclaim and preemption, priority classes
- 7.7d Gang scheduling and placement: all-or-nothing PodGroups, topology-aware scheduling (NVLink domains, racks, NICs), bin-pack versus spread policies
- 7.7e GPU sharing and fractions under KAI; interaction with MIG, MPS and time-slicing
- 7.7f Operations: installation (Helm), upgrades, observability (metrics, events), debugging unschedulable gangs, failure modes
- 7.7g Run:ai platform view: control plane, projects and departments, workload types, how it relates to the open-source KAI Scheduler (verify current product and licensing status in public docs)
- 7.7h Comparison and decision guide: KAI vs Kueue vs Volcano vs YuniKorn vs Slurm; when to use which; combining Kueue with JobSet/LWS
- 7.7i Lab on GKE/Nebius: multi-tenant GPU queues, a gang of PyTorchJob pods, preemption demo, fair-share measurements

**Sources and gap policy.** Primary: NVIDIA's KAI Scheduler repository and documentation, Kubernetes scheduling docs; supporting: Generative AI on Kubernetes ch.7, nvidia-devops V01/V11/V23, BCM containerization PDF (Run:ai install under BCM). Mark in each chapter which statements rest on public docs and need a version check (the project is evolving quickly).

Chapter 10.11 now only cross-references this series.


---

# Revision 6: foundations track (Tier 0)

Author feedback: strong DevOps experience but weak basics in Linux, networking and Kubernetes internals; new to Ansible; has used Terraform. Parts 1, 2, 4 and 5 were expanded and made Tier 0 (written first, from zero): Linux grows to 28 chapters (command line, text tools, SSH, system calls, building a container by hand), Networking to 32 (what happens when you curl a URL, subnetting practice, DNS, HTTP/TLS, tcpdump from scratch, labs with namespaces, FRR and Containerlab), Ansible from zero in 17 chapters plus a Terraform refresher in 10, and Kubernetes to 35 chapters including bare-metal kubeadm, API server and etcd, controllers, the life of a pod and of a Service, pod networking under the hood, and a kernel-actions map. Part 3 gained a Python internals chapter. See `STRUCTURE.md` for numbering; `planning/coverage/MASTER_MAP.md` audits that every chapter of the gem foundation books is used.
