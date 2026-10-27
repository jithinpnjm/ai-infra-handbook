# Status tracker (regenerate the skeleton with tools/scaffold/generate.py; update Status by hand or script)

Legend: scaffold · outline · drafted (labs untested) · reviewed · done

Legacy pilot drafts (superseded, kept as reference for the rewrite): `planning/pilots/` (2.5 Linux networking toolbox, 7.1 GPU architecture, 8.3 InfiniBand). Rebuild as series 2.17-2.21, 10.01-10.10 and 12.06-12.09.

## Tier 0: foundations (write first, everything builds on these): 69 chapters

| # | Chapter | Status | Words | Notes |
|---|---|---|---|---|
| 1.1 | The Linux big picture: kernel, userspace, distributions | drafted | 9933 |  |
| 1.2 | The command line: shells, commands, pipes and redirection | drafted | 12134 |  |
| 1.3 | Files and the directory hierarchy: paths, links, inodes | drafted | 8328 |  |
| 1.4 | Text-processing essentials: grep, sed, awk, find, xargs, sort | drafted | 6636 |  |
| 1.5 | Working remotely: SSH keys, file transfer, tmux and editors | drafted | 7823 |  |
| 1.6 | Users, groups, permissions, ACLs, sudo and user environments | drafted | 11924 |  |
| 1.7 | Packages, repositories and software installation | drafted | 15590 |  |
| 1.8 | Processes, signals and job control | drafted | 13885 |  |
| 1.9 | Shell scripting that survives production | drafted | 11237 |  |
| 1.10 | Devices, udev, sysfs and procfs | drafted | 9935 |  |
| 1.11 | How a program runs: system calls, libraries, ELF, strace and ldd | drafted | 10549 |  |
| 1.12 | Disks, partitions and filesystems | drafted | 14589 |  |
| 1.13 | LVM, RAID and NVMe | drafted | 11253 |  |
| 1.14 | Boot: firmware, GRUB, kernel, initramfs | drafted | 11008 |  |
| 1.15 | systemd: units, targets, timers, journald | drafted | 10524 |  |
| 1.16 | Logging, time synchronisation, cron and batch jobs | drafted | 8141 |  |
| 1.17 | Memory management: virtual memory, NUMA, huge pages, OOM | drafted | 9936 |  |
| 1.18 | CPU scheduling and cgroups v1 and v2 | drafted | 9468 |  |
| 1.19 | Namespaces: the kernel feature behind containers | drafted | 8485 |  |
| 1.20 | Lab: build a container by hand with unshare, chroot, cgroups and overlayfs | drafted | 3678 |  |
| 1.29 | Remote administration reference: SSH server and client options, host-based authentication, parallel shells, screen and tmux, IPMI and console managers | drafted | 8876 |  |
| 1.30 | Network file sharing and remote graphical access: rsync in depth, Samba, SSHFS, NFS clients, cloud storage, X11, VNC and alternatives | drafted | 8639 |  |
| 2.1 | What happens when you curl a URL: a packet's journey end to end | drafted | 7180 |  |
| 2.2 | How networks work: layers, encapsulation, the TCP/IP model | drafted | 7845 |  |
| 2.3 | Ethernet and L2: frames, MAC addresses, switching, ARP and NDP | drafted | 9045 |  |
| 2.4 | IP addressing, subnetting and CIDR (IPv4 and IPv6), with practice | drafted | 7595 |  |
| 2.5 | Routing on a host: routing tables, default gateways and forwarding | drafted | 7159 |  |
| 2.6 | TCP in depth: handshake, windows, congestion control, retransmission | drafted | 8688 |  |
| 2.7 | UDP, ICMP and the diagnostic tools: ping, traceroute, mtr | drafted | 6000 |  |
| 2.8 | DNS in depth: resolution, records, resolvers and caching | drafted | 6368 |  |
| 2.9 | DHCP, NAT and PAT | drafted | 6118 |  |
| 2.10 | HTTP, TLS and PKI basics | drafted | 6575 |  |
| 2.11 | VLANs, trunking and spanning tree | drafted | 7035 |  |
| 2.12 | Link aggregation: LACP and MLAG | drafted | 6475 |  |
| 2.13 | IP routing: static routes, dynamic routing and convergence | drafted | 7425 |  |
| 2.22 | Linux networking: inspecting state with ip, ss and counters | drafted | 5475 |  |
| 2.23 | Linux networking: netfilter, nftables, conntrack and NAT | drafted | 5216 |  |
| 2.25 | Linux networking: namespaces, veth, bridges and container networking | drafted | 4804 |  |
| 2.26 | Packet capture from scratch: tcpdump, tshark and Wireshark | drafted | 5053 |  |
| 2.27 | Lab: build network topologies with namespaces, FRR and Containerlab | drafted | 4058 |  |
| 4.1 | Git from scratch for infrastructure engineers | drafted | 5237 |  |
| 4.3 | Ansible from zero: what it is, how it works, installation and ad hoc commands | drafted | 3944 |  |
| 4.4 | YAML and Jinja2 for infrastructure code | drafted | 3886 |  |
| 4.5 | Ansible inventory: hosts, groups, dynamic inventory and variables | drafted | 3316 |  |
| 4.6 | Ansible playbooks: tasks, modules, idempotency and check mode | drafted | 3671 |  |
| 4.7 | Ansible variables, facts, templates and filters | drafted | 3651 |  |
| 4.8 | Ansible handlers, conditionals, loops, blocks and error handling | drafted | 3576 |  |
| 4.9 | A real playbook end to end: deploying an application | drafted | 3604 |  |
| 4.10 | Debugging Ansible playbooks | drafted | 3380 |  |
| 4.11 | Ansible roles and collections | drafted | 3072 |  |
| 4.12 | Ansible Vault and secrets management | drafted | 3425 |  |
| 5.1 | Containers from first principles: images, layers, registries | drafted | 5034 |  |
| 5.2 | Container runtimes: containerd, runc, CRI and OCI | drafted | 3992 |  |
| 5.3 | Kubernetes architecture overview: components and what talks to what | drafted | 4098 |  |
| 5.4 | Bare-metal Kubernetes from scratch with kubeadm (lab) | drafted | 4448 |  |
| 5.5 | The API server and etcd: how a request becomes cluster state | drafted | 4733 |  |
| 5.6 | Controllers and the reconcile loop: how Kubernetes thinks | drafted | 3712 |  |
| 5.7 | Pods and workloads: Deployments, StatefulSets, DaemonSets and Jobs | drafted | 5026 |  |
| 5.8 | The life of a pod, end to end, including what the kernel does | drafted | 4012 |  |
| 5.9 | The kubelet and the node: CRI, cgroups, QoS classes, probes and eviction | drafted | 4735 |  |
| 5.10 | Services, endpoints and kube-proxy: the life of a Service | drafted | 4533 |  |
| 5.11 | DNS and service discovery with CoreDNS | drafted | 3684 |  |
| 5.12 | Ingress, load balancers and the Gateway API | drafted | 4370 |  |
| 5.13 | Pod networking under the hood: veth, bridges, routes and CNI plugins | drafted | 3951 |  |
| 5.15 | NetworkPolicy and the kernel: netfilter, conntrack and eBPF | drafted | 4332 |  |
| 5.16 | Configuration, secrets and RBAC | drafted | 4849 |  |
| 5.17 | Storage internals: volumes, PV and PVC, CSI and mounts | drafted | 4125 |  |
| 5.25 | Troubleshooting Kubernetes from the node: crictl, nsenter, tcpdump and iptables | drafted | 4265 |  |
| 5.26 | How Kubernetes uses the Linux kernel: a complete map | drafted | 5146 |  |

## Tier 1: interview- and job-critical: 116 chapters

| # | Chapter | Status | Words | Notes |
|---|---|---|---|---|
| 1.22 | Kernel modules, DKMS and sysctl tuning for GPU nodes | drafted | 7596 |  |
| 1.28 | Putting it together: tuning a Linux node for GPU and HPC work | drafted | 9701 |  |
| 2.24 | Linux networking: policy routing, bonding, MTU, NIC and stack tuning | drafted | 5554 |  |
| 2.30 | Network troubleshooting method and case studies | drafted | 5501 |  |
| 2.32 | Cloud networking: VPC, peering, load balancers and GCP specifics | drafted | 5457 |  |
| 4.17 | Ansible for GPU nodes and clusters | drafted | 4715 |  |
| 4.24 | Terraform on GCP and Nebius: networks, GPU VMs and GKE | drafted | 4211 |  |
| 4.27 | Lab: provision a GPU cluster with Terraform and Ansible | drafted | 3405 |  |
| 5.14 | Overlay versus routed pod networking: VXLAN, BGP with Calico, eBPF with Cilium | drafted | 4086 |  |
| 5.18 | Scheduling in depth: kube-scheduler, affinity, taints, priority and preemption | drafted | 5030 |  |
| 5.22 | Multitenancy and platform services | drafted | 4167 |  |
| 5.23 | Autoscaling: HPA, VPA, KEDA and the cluster autoscaler | drafted | 4193 |  |
| 5.34 | GKE for GPU workloads: setup, node pools and quotas | drafted | 3576 |  |
| 6.7 | Slurm architecture and installation | drafted | 8600 | First full chapter; coverage file done; verify HA, sackd/auth-slurm, upgrade window, NVIDIA/SchedMD reports. Labs untested. |
| 6.8 | Slurm configuration: nodes, partitions and cgroups | drafted | 4058 |  |
| 6.9 | Slurm accounting and scheduling policy: QoS, fairshare, backfill, preemption | drafted | 4369 |  |
| 6.10 | Slurm GPU scheduling: gres, NVML autodetect, MIG and device constraints | drafted | 3519 |  |
| 6.11 | Submitting and launching jobs: sbatch, srun, salloc, arrays, dependencies | drafted | 3758 |  |
| 6.12 | Multi-node training on Slurm: PMIx, torchrun, NCCL environment, binding, topology | drafted | 3934 |  |
| 6.13 | Containers on Slurm: enroot and pyxis | drafted | 3379 |  |
| 6.14 | Slurm operations: prolog, epilog, health checks, drain, reason codes, troubleshooting | drafted | 3999 |  |
| 6.15 | Slurm high availability, upgrades and scaling | drafted | 3019 |  |
| 6.16 | Slurm on Kubernetes: Slinky and Soperator | drafted | 2725 |  |
| 6.31 | Capstone: build and operate a small Slurm GPU cluster | drafted | 3186 |  |
| 10.8 | Operating GPU nodes: nvidia-smi, topology, clocks and throttling | drafted | 10110 |  |
| 10.9 | The NVIDIA software stack: driver, CUDA toolkit, container toolkit, compatibility | drafted | 9332 |  |
| 10.10 | Fabric Manager, NVSM and NVLink domains | drafted | 9528 |  |
| 10.21 | GPU health: DCGM, ECC, row remapping and Xid | drafted | 9187 |  |
| 10.22 | GPU troubleshooting scenarios | drafted | 8618 |  |
| 11.1 | Why Kubernetes needs a GPU platform layer | drafted | 8217 |  |
| 11.2 | Device plugin, container toolkit, CDI and runtime classes | draft | 8598 |  |
| 11.3 | Node Feature Discovery and GPU Feature Discovery | draft | 7065 |  |
| 11.4 | GPU Operator architecture and operands | draft | 7096 |  |
| 11.5 | GPU Operator installation, configuration and upgrades | draft | 7162 |  |
| 11.6 | Scheduling GPUs: requests, Topology Manager, CPU and NUMA alignment | draft | 7830 |  |
| 11.7 | Multi-node jobs: why a pod cannot span nodes, and gang scheduling concepts | draft | 7451 |  |
| 11.8 | Kueue, Volcano and scheduler plugins | draft | 6998 |  |
| 11.9 | JobSet, LeaderWorkerSet, PyTorchJob and the MPI Operator | draft | 6948 |  |
| 11.10 | Secondary networks: Multus, SR-IOV device plugin and RDMA device plugin | draft | 6915 |  |
| 11.11 | NVIDIA Network Operator | draft | 6907 |  |
| 11.12 | Dynamic Resource Allocation (DRA) | draft | 6769 |  |
| 11.13 | KAI Scheduler: why default scheduling is not enough | draft | 7022 |  |
| 11.14 | KAI Scheduler architecture and resources | draft | 7131 |  |
| 11.15 | KAI queues, quotas and fair sharing | draft | 6936 |  |
| 11.16 | KAI gang scheduling and topology-aware placement | draft | 6911 |  |
| 11.17 | KAI GPU sharing and fractions | draft | 7458 |  |
| 11.18 | KAI operations and troubleshooting | draft | 7248 |  |
| 11.19 | The Run:ai platform view | draft | 7492 |  |
| 11.20 | Scheduler comparison guide: KAI, Kueue, Volcano, YuniKorn and Slurm | draft | 7252 |  |
| 11.21 | PCIe, IOMMU, VFIO and device passthrough | draft | 7483 |  |
| 11.22 | SR-IOV for NICs and GPUs | draft | 7056 |  |
| 11.23 | NVIDIA vGPU: architecture, profiles and licensing | draft | 7051 |  |
| 11.24 | MIG in depth | draft | 7321 |  |
| 11.25 | Time-slicing, MPS and oversubscription | draft | 6791 |  |
| 11.26 | Choosing a GPU sharing model | draft | 6781 |  |
| 11.27 | Virtual machines on Kubernetes: KubeVirt, Kata and GPU passthrough | draft | 7006 |  |
| 11.29 | Multi-tenancy, quotas, fault tolerance and health on GPU clusters | draft | 7768 |  |
| 11.30 | Lab: multi-node GPU Kubernetes on GKE and Nebius | draft | 7328 |  |
| 12.1 | AI traffic: collectives, incast and elephant flows | drafted | 13113 |  |
| 12.2 | RDMA fundamentals: verbs, queue pairs and memory registration | drafted | 13829 |  |
| 12.3 | RoCEv2 transport and congestion management | drafted | 11891 |  |
| 12.4 | PFC, ECN and DCQCN in depth | drafted | 11118 |  |
| 12.5 | Data center bridging and QoS for AI | drafted | 12620 |  |
| 12.6 | InfiniBand fundamentals and addressing | drafted | 12556 |  |
| 12.7 | InfiniBand subnet manager, routing, topologies and rails | drafted | 12583 |  |
| 12.8 | InfiniBand adaptive routing and congestion control | drafted | 11731 |  |
| 12.9 | InfiniBand diagnostics, UFM and operations | drafted | 13535 |  |
| 12.13 | Fabric design: topology, oversubscription and scale | drafted | 13647 |  |
| 12.14 | Load balancing and routing for AI fabrics | drafted | 14534 |  |
| 12.15 | NCCL: collectives and algorithms | drafted | 11717 |  |
| 12.16 | NCCL: topology, channels, transports and environment variables | drafted | 10427 |  |
| 12.17 | nccl-tests and fabric benchmarking | drafted | 11591 |  |
| 12.18 | NCCL debugging: hangs, timeouts and errors | drafted | 14468 |  |
| 12.19 | GPUDirect RDMA and GPUDirect Storage | drafted | 10651 |  |
| 12.24 | AI networking troubleshooting playbook | drafted | 12285 |  |
| 14.13 | Fine-tuning: SFT, LoRA and QLoRA, preference alignment | scaffold |  |  |
| 14.14 | Dataset engineering for fine-tuning | scaffold |  |  |
| 14.15 | Fine-tuning infrastructure and cost | scaffold |  |  |
| 15.1 | The anatomy of an inference request | scaffold |  |  |
| 15.2 | Batching, the KV cache and quantization fundamentals | scaffold |  |  |
| 15.3 | vLLM in depth | scaffold |  |  |
| 15.4 | SGLang and cross-request optimisation | scaffold |  |  |
| 15.5 | TensorRT and TensorRT-LLM | scaffold |  |  |
| 15.6 | Triton Inference Server | scaffold |  |  |
| 15.7 | NVIDIA NIM and the NIM Operator | scaffold |  |  |
| 15.8 | NVIDIA Dynamo, llm-d and disaggregated serving | scaffold |  |  |
| 15.9 | Multinode inference: parallelism, decoding and routing | scaffold |  |  |
| 15.10 | Prefill and decode disaggregation | scaffold |  |  |
| 15.11 | Advanced prefill-decode and KV cache tuning | scaffold |  |  |
| 15.12 | Dynamic and adaptive inference engine optimisations | scaffold |  |  |
| 15.13 | Profiling, debugging and tuning inference at scale | scaffold |  |  |
| 15.14 | Benchmarking: genai-perf, latency percentiles and goodput | scaffold |  |  |
| 15.15 | Autoscaling inference: HPA, KEDA and scale-to-zero | scaffold |  |  |
| 15.16 | Production serving stack and reliability | scaffold |  |  |
| 15.17 | Lab: serve and benchmark on GKE and Nebius | scaffold |  |  |
| 16.1 | MLOps foundations and lifecycle | scaffold |  |  |
| 16.2 | Data versioning and experiment tracking: DVC, MLflow, Weights and Biases | scaffold |  |  |
| 16.3 | Data pipelines and feature stores | scaffold |  |  |
| 16.4 | Pipeline orchestration: Kubeflow Pipelines, Argo, Flyte, Airflow | scaffold |  |  |
| 16.5 | Distributed compute for ML: Ray, KubeRay, Training Operator and Katib | scaffold |  |  |
| 16.6 | Model registry, CI/CD and GitOps for models | scaffold |  |  |
| 16.7 | Model serving platforms: KServe, Seldon and BentoML | scaffold |  |  |
| 16.8 | LLMOps: RAG, vector databases and agents | scaffold |  |  |
| 16.9 | LLM evaluation and guardrails | scaffold |  |  |
| 16.10 | Monitoring, drift and continual learning | scaffold |  |  |
| 16.14 | Platform design: multi-tenant AI factory, quotas and chargeback | scaffold |  |  |
| 16.15 | Lab: end-to-end MLOps on GKE | scaffold |  |  |
| 17.9 | The AI systems performance checklist (master) | scaffold |  |  |
| 19.1 | Capstone: a Slurm GPU cluster | scaffold |  |  |
| 19.2 | Capstone: a Kubernetes GPU platform with KAI and Kueue | scaffold |  |  |
| 19.3 | Capstone: inference on GKE with vLLM, Triton, TensorRT-LLM, NIM and KServe | scaffold |  |  |
| 19.4 | Capstone: multi-node training with fault tolerance | scaffold |  |  |
| 19.5 | Capstone: an nccl-tests fabric lab | scaffold |  |  |
| 19.6 | Capstone: node-health automation with DCGM and an operator | scaffold |  |  |
| 19.14 | Interview question bank by topic | scaffold |  |  |
| 19.15 | Interview cheat sheet | scaffold |  |  |

## Tier 1b: NVIDIA platform operations: 47 chapters

| # | Chapter | Status | Words | Notes |
|---|---|---|---|---|
| 6.22 | Provisioning with PXE, iPXE, DHCP, TFTP and image management | drafted | 3754 |  |
| 7.1 | BMCs, IPMI and out-of-band management | drafted | 3445 |  |
| 7.2 | Redfish concepts: service root, resources, collections, OData | drafted | 2801 |  |
| 7.3 | The Redfish protocol: HTTP methods, headers, status codes, query parameters | drafted | 3134 |  |
| 7.4 | Redfish authentication, sessions and security | drafted | 2897 |  |
| 7.5 | Redfish actions, tasks, events and subscriptions | drafted | 3106 |  |
| 7.6 | The Redfish schema: reading CSDL, JSON schema and the resource guide | drafted | 3246 |  |
| 7.7 | Systems, Chassis and Managers: the core resource model | drafted | 2984 |  |
| 7.8 | Power, thermal, sensors and environment | drafted | 2874 |  |
| 7.9 | Storage, network adapters and PCIe devices | drafted | 2528 |  |
| 7.10 | Firmware inventory and the UpdateService | drafted | 3806 |  |
| 7.11 | Log services, event logs and diagnostics | drafted | 2843 |  |
| 7.12 | Automating Redfish with Python, Ansible and Go | drafted | 2694 |  |
| 7.13 | Redfish on NVIDIA DGX and HGX: BMC, GPU baseboard and management | drafted | 3011 |  |
| 7.14 | Fleet-scale hardware management and node lifecycle automation | drafted | 3156 |  |
| 7.15 | BMC security hardening and attestation | drafted | 3662 |  |
| 8.1 | BCM architecture and concepts | drafted | 4137 |  |
| 8.2 | Planning and installing BCM | drafted | 3059 |  |
| 8.3 | Cluster configuration: networks, nodes and categories | drafted | 5418 |  |
| 8.4 | Node provisioning: images, kernels, categories and the PXE flow | drafted | 5586 |  |
| 8.5 | cmsh and Base View: administering the cluster | drafted | 3038 |  |
| 8.6 | Users, authentication and security in BCM | drafted | 2780 |  |
| 8.7 | Power, BMC and hardware management in BCM | drafted | 3287 |  |
| 8.8 | Workload managers under BCM: Slurm setup | drafted | 4206 |  |
| 8.9 | Kubernetes under BCM: deployment and GPU enablement | drafted | 5519 |  |
| 8.10 | Containerization in BCM: Docker, Apptainer and enroot | drafted | 2535 |  |
| 8.11 | Monitoring, health checks and alerts in BCM | drafted | 3939 |  |
| 8.12 | High availability and head-node failover | drafted | 3853 |  |
| 8.13 | Day-2 operations: updates, scaling, hardware replacement, disaster recovery | drafted | 3014 |  |
| 8.14 | Air-gapped installation and upgrades | drafted | 3145 |  |
| 8.15 | BCM in an AI factory: DGX SuperPOD integration | drafted | 2604 |  |
| 8.16 | Mission Control, DGX Cloud and autonomous recovery concepts | drafted | 7324 |  |
| 9.1 | DGX system families and what they are for | drafted | 10032 |  |
| 9.2 | Inside a DGX H100 and H200 system | drafted | 8283 |  |
| 9.3 | HGX platforms and OEM integration | drafted | 9620 |  |
| 9.4 | Grace CPU, GH200 and GB200 superchips | drafted | 7455 |  |
| 9.5 | GB200 and GB300 NVL72 rack-scale systems | drafted | 7745 |  |
| 9.6 | DGX SuperPOD concepts: scalable units, fabrics and tiers | drafted | 8201 |  |
| 9.7 | DGX B200 SuperPOD data center design: power, cooling, cabling and layout | drafted | 7516 |  |
| 9.8 | GB300 SuperPOD reference architecture | drafted | 6695 |  |
| 9.9 | Compute, storage, in-band and out-of-band networks in a SuperPOD | drafted | 7512 |  |
| 9.10 | BasePOD and smaller deployments | drafted | 7489 |  |
| 9.11 | Power delivery, thermal design and liquid cooling | drafted | 7272 |  |
| 9.12 | Software stack and management in an AI factory | drafted | 6626 |  |
| 9.13 | Sizing and capacity-planning exercises | drafted | 6854 |  |
| 9.14 | Cloud GPU platforms: DGX Cloud, CoreWeave, Nebius and GCP A3 and A4 | drafted | 6372 |  |
| 16.12 | NVIDIA enterprise stack: AI Enterprise, NGC and licensing | scaffold |  |  |

## Tier 2: senior-loop depth: 146 chapters

| # | Chapter | Status | Words | Notes |
|---|---|---|---|---|
| 0.1 | The AI factory landscape and the roles in it | scaffold |  |  |
| 0.2 | How to use this book and set up your labs (Mac, GCP/GKE, Nebius) | scaffold |  |  |
| 0.3 | Learning paths by role: Platform, MLOps, LLM inference, HPC GPU cloud | scaffold |  |  |
| 1.21 | Linux security: capabilities, SELinux, AppArmor, seccomp, PAM, SSH hardening | drafted | 8978 |  |
| 1.23 | Performance methodology: USE, workload characterisation, drill-down | drafted | 10953 |  |
| 1.24 | Observability tools: perf, ftrace, BPF and bpftrace | drafted | 11835 |  |
| 1.25 | Benchmarking correctly | drafted | 9875 |  |
| 1.26 | KVM, QEMU and libvirt basics | drafted | 8425 |  |
| 1.27 | Cloud computing and virtualization internals for Linux engineers | drafted | 8630 |  |
| 2.15 | BGP fundamentals | drafted | 6650 |  |
| 2.16 | BGP in the data center: eBGP Clos, unnumbered, ECMP, anycast | drafted | 8410 |  |
| 2.17 | Overlays: VXLAN and EVPN | drafted | 7215 |  |
| 2.18 | Data center topologies: Clos, leaf-spine, oversubscription, failure domains | drafted | 6130 |  |
| 2.19 | Queuing, QoS, ECN, PFC and DCB basics | drafted | 5635 |  |
| 2.20 | Load balancing: L4, L7, ECMP hashing and proxies | drafted | 5396 |  |
| 2.21 | Network security: firewalls, TLS and zero trust | drafted | 5329 |  |
| 2.28 | Network automation fundamentals: APIs, YANG, NETCONF, gNMI, SDN, templates | drafted | 5893 |  |
| 2.29 | Network automation in practice: Ansible, Nornir and CI/CD for networks | drafted | 5628 |  |
| 2.31 | Network monitoring and telemetry | drafted | 5333 |  |
| 3.1 | Python core: types, control flow, functions | drafted | 7429 |  |
| 3.2 | Modules, packages, virtual environments and packaging | drafted | 5536 |  |
| 3.3 | Idiomatic Python: the data model, comprehensions, generators | drafted | 5259 |  |
| 3.4 | Classes, dataclasses, typing and protocols | drafted | 4965 |  |
| 3.5 | Errors, files, text and bytes, subprocess and system scripting | drafted | 5381 |  |
| 3.6 | Concurrency: threads, processes and asyncio | drafted | 4909 |  |
| 3.7 | Building APIs and microservices with FastAPI | drafted | 5053 |  |
| 3.8 | Building CLIs, agents and exporters (Prometheus exporters, Redfish clients) | drafted | 5618 |  |
| 3.9 | Testing, quality and CI for Python tooling | drafted | 4147 |  |
| 3.10 | Python for data and ML infrastructure: NumPy, pandas, PyTorch essentials | drafted | 4429 |  |
| 3.11 | Python under the hood: decorators, descriptors and metaprogramming (how frameworks work) | drafted | 4372 |  |
| 4.2 | CI/CD pipelines: concepts and design | drafted | 4536 |  |
| 4.13 | Testing Ansible: ansible-lint, Molecule and CI | drafted | 3460 |  |
| 4.14 | Ansible at scale: performance, strategies and callbacks | drafted | 3543 |  |
| 4.15 | Custom modules, plug-ins and Ansible Automation Platform | drafted | 4140 |  |
| 4.16 | Ansible for containers, cloud and network devices | drafted | 3642 |  |
| 4.18 | Terraform refresher: why, providers, resources and the workflow | drafted | 3965 |  |
| 4.19 | Terraform state in depth: backends, locking and drift | drafted | 3903 |  |
| 4.20 | Terraform modules and reusable infrastructure | drafted | 3438 |  |
| 4.21 | Terraform loops, conditionals, lifecycle and gotchas | drafted | 3365 |  |
| 4.22 | Terraform secrets and multiple providers | drafted | 3388 |  |
| 4.23 | Production-grade Terraform: structure, testing and team workflows | drafted | 3615 |  |
| 4.25 | Terraform with Kubernetes and Helm providers; OpenTofu | drafted | 3600 |  |
| 4.26 | GitOps with Argo CD and Flux | drafted | 3798 |  |
| 5.19 | Cluster deployment models and day-2 operations | drafted | 3864 |  |
| 5.20 | Upgrades, etcd backup and restore, and disaster recovery | drafted | 4703 |  |
| 5.21 | Certificates, identity, admission control and policy | drafted | 5081 |  |
| 5.24 | Observability for Kubernetes | drafted | 3717 |  |
| 5.27 | Software supply chain security | drafted | 5014 |  |
| 5.29 | Extending Kubernetes: CRDs and operators | drafted | 4239 |  |
| 5.30 | Go for Kubernetes engineers | drafted | 4307 |  |
| 5.31 | Operators in Go: controller-runtime and kubebuilder | drafted | 3743 |  |
| 5.32 | Project: a GPU-node-health operator | drafted | 2662 |  |
| 5.33 | Reading the GPU Operator and Network Operator source | drafted | 4360 |  |
| 6.1 | What a supercomputer is: TOP500, Linpack, HPC versus AI factory | drafted | 4253 |  |
| 6.2 | Cluster anatomy: head, login, compute, storage and management nodes | drafted | 4719 |  |
| 6.3 | Parallel computing concepts: Amdahl, scaling, shared memory versus message passing | drafted | 4392 |  |
| 6.4 | MPI in practice: Open MPI, ranks, collectives and tuning | drafted | 4489 |  |
| 6.6 | Environment modules, Spack and EasyBuild | drafted | 3727 |  |
| 6.18 | Parallel storage concepts and the limits of NFS | drafted | 4188 |  |
| 6.19 | Lustre architecture and operation | drafted | 4181 |  |
| 6.20 | BeeGFS, GPFS, WekaFS and VAST | drafted | 2647 |  |
| 6.21 | Parallel I/O and checkpoint patterns | drafted | 3917 |  |
| 6.23 | xCAT, Warewulf and cluster managers compared with BCM | drafted | 3992 |  |
| 6.24 | Users, LDAP, SSSD, quotas and accounting at scale | drafted | 4648 |  |
| 6.26 | Cluster monitoring and health at scale | drafted | 4367 |  |
| 6.28 | HPC benchmarking: HPL, HPCG, IOR, OSU and NCCL tests | drafted | 4168 |  |
| 6.29 | Containers and reproducibility in HPC: Apptainer and enroot | drafted | 3132 |  |
| 6.30 | Facility basics: power, cooling, racks and liquid cooling | drafted | 5273 |  |
| 10.1 | Why GPUs: CPU versus GPU and throughput design | drafted | 13317 |  |
| 10.2 | The execution model: threads, warps, blocks and SMs | drafted | 11312 |  |
| 10.3 | The GPU memory hierarchy | drafted | 10882 |  |
| 10.4 | Tensor cores and numerical precision | drafted | 8008 |  |
| 10.5 | The roofline model and performance modelling | drafted | 8534 |  |
| 10.6 | GPU interconnects: PCIe, NVLink, NVSwitch and NVLink-C2C | draft | 8795 |  |
| 10.7 | GPU generations and product line: Ampere, Hopper, Blackwell; PCIe versus SXM | draft | 10197 |  |
| 10.11 | CUDA programming basics: kernels, indexing and memory | drafted | 9900 |  |
| 10.12 | Streams, events, asynchronous copies and pinned memory | drafted | 7627 |  |
| 10.13 | Memory access patterns and profiling | drafted | 9244 |  |
| 10.14 | Occupancy, warp efficiency and instruction-level parallelism | drafted | 8262 |  |
| 10.15 | Kernel efficiency and arithmetic intensity | drafted | 8876 |  |
| 10.16 | Intra-kernel pipelining, warp specialization and thread block clusters | drafted | 11321 |  |
| 10.17 | Inter-kernel pipelining, synchronization and stream-ordered allocation | drafted | 9328 |  |
| 10.18 | Dynamic scheduling, CUDA graphs and device-initiated orchestration | drafted | 9062 |  |
| 10.19 | Triton language and compilers: OpenAI Triton, torch.compile, XLA | drafted | 8258 |  |
| 10.20 | Profiling tools: Nsight Systems, Nsight Compute, PyTorch profiler | drafted | 8851 |  |
| 11.28 | DPUs, BlueField and DOCA | draft | 6694 |  |
| 12.10 | HDR, NDR, XDR, optics and cabling | drafted | 14200 |  |
| 12.11 | NVIDIA Spectrum-X and Spectrum switches | drafted | 13410 |  |
| 12.12 | Ethernet versus InfiniBand: a design decision guide | drafted | 13650 |  |
| 12.20 | SHARP and in-network computing | drafted | 11636 |  |
| 12.21 | Storage networks, Ultra Ethernet and scale-up fabrics | drafted | 13263 |  |
| 12.22 | AI network telemetry and KPIs | drafted | 13944 |  |
| 12.23 | Fabric validation and capacity planning | drafted | 9348 |  |
| 13.1 | The AI data path: from storage to GPU | drafted | 10537 |  |
| 13.2 | Local NVMe and data staging | drafted | 11572 |  |
| 13.3 | GPUDirect Storage architecture | drafted | 10860 |  |
| 13.4 | Lustre for AI | drafted | 11477 |  |
| 13.5 | BeeGFS, Weka, VAST and object storage | drafted | 10847 |  |
| 13.6 | Data loading, small files and metadata | drafted | 11070 |  |
| 13.7 | Checkpoint architecture and recovery | drafted | 12037 |  |
| 13.8 | Capacity, performance and cost planning | drafted | 12552 |  |
| 13.9 | Storage troubleshooting | drafted | 12017 |  |
| 14.1 | ML and deep learning fundamentals for infrastructure engineers | scaffold |  |  |
| 14.2 | Transformers and LLM architecture | scaffold |  |  |
| 14.3 | Training memory and compute anatomy | scaffold |  |  |
| 14.4 | Data parallelism and DDP | scaffold |  |  |
| 14.5 | FSDP and parameter sharding | scaffold |  |  |
| 14.6 | DeepSpeed and ZeRO | scaffold |  |  |
| 14.7 | Tensor, pipeline and expert parallelism; Megatron | scaffold |  |  |
| 14.8 | PyTorch performance: profiling, tuning and scaling | scaffold |  |  |
| 14.9 | PyTorch compilers and kernels: torch.compile | scaffold |  |  |
| 14.10 | Multi-node training architecture | scaffold |  |  |
| 14.11 | Checkpointing, fault tolerance and elastic training | scaffold |  |  |
| 14.12 | Training performance engineering and troubleshooting | scaffold |  |  |
| 14.16 | NeMo framework and customisation | scaffold |  |  |
| 15.18 | Inference cost, capacity and cost per token | scaffold |  |  |
| 16.11 | Cloud MLOps platforms: Vertex AI, SageMaker and Azure ML | scaffold |  |  |
| 16.13 | Governance, privacy and compliance for ML platforms | scaffold |  |  |
| 17.1 | Observability foundations: metrics, logs and traces | scaffold |  |  |
| 17.2 | Prometheus and Grafana | scaffold |  |  |
| 17.3 | Logging with Loki and tracing with OpenTelemetry | scaffold |  |  |
| 17.4 | DCGM exporter and interpreting GPU metrics | scaffold |  |  |
| 17.5 | Distributed observability and profiling | scaffold |  |  |
| 17.6 | Alerting, SLOs and health checks for GPU clusters | scaffold |  |  |
| 17.7 | Failure modes and detection | scaffold |  |  |
| 17.8 | Performance engineering methodology and decision trees | scaffold |  |  |
| 17.10 | Cluster lifecycle, upgrades and change management | scaffold |  |  |
| 17.11 | Incident response and game days | scaffold |  |  |
| 17.12 | Capacity planning and cost optimisation | scaffold |  |  |
| 17.13 | Reliability engineering for AI infrastructure | scaffold |  |  |
| 17.14 | Disaster recovery and data resilience | scaffold |  |  |
| 17.15 | On-call runbooks | scaffold |  |  |
| 17.16 | AI-assisted operations and scaling toward very large clusters | scaffold |  |  |
| 18.1 | Threat modeling for AI infrastructure | scaffold |  |  |
| 18.2 | Hardware and firmware trust | scaffold |  |  |
| 18.3 | Containers and the software supply chain | scaffold |  |  |
| 18.4 | Kubernetes access control and pod security | scaffold |  |  |
| 18.5 | GPU sharing security, DMA, IOMMU and SR-IOV | scaffold |  |  |
| 18.6 | BlueField, DOCA and confidential computing | scaffold |  |  |
| 18.7 | Data and model protection, audit and compliance | scaffold |  |  |
| 19.7 | Capstone: an observability platform | scaffold |  |  |
| 19.8 | Capstone: MIG multi-tenancy | scaffold |  |  |
| 19.9 | Capstone: capacity planning | scaffold |  |  |
| 19.11 | System design: a training cluster | scaffold |  |  |
| 19.12 | System design: inference serving | scaffold |  |  |
| 19.13 | System design: research infrastructure | scaffold |  |  |

## Tier 3: breadth: 8 chapters

| # | Chapter | Status | Words | Notes |
|---|---|---|---|---|
| 2.14 | OSPF and IS-IS | drafted | 6812 |  |
| 5.28 | Service mesh | drafted | 3248 |  |
| 5.35 | Multicluster and fleet management | drafted | 3699 |  |
| 6.5 | OpenMP, compilers and optimisation flags | drafted | 4172 |  |
| 6.17 | Other schedulers: PBS, Torque, LSF and Flux | drafted | 3596 |  |
| 6.25 | Remote access, bastions, Open OnDemand and user environments | drafted | 3380 |  |
| 6.27 | Backup and data protection | drafted | 4375 |  |
| 19.10 | Customer workshops and the consulting method | scaffold |  |  |
