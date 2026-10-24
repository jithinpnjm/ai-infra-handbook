# Book structure (generated from planning/structure.txt; do not edit by hand)

386 chapters in 20 parts. Chapter ids are part.chapter (for example 6.12 = Part 6, chapter 12). This file supersedes the numbering used in earlier CURRICULUM_MAP revisions.

## Part 0: Orientation  (tier 2, 3 chapters)

| # | Chapter | Level | Tier | Sources |
|---|---|---|---|---|
| 0.1 | The AI factory landscape and the roles in it | B | 2 | AF 11; V1; V21; EAS 1,15; NPA 1; V1; VINTRO |
| 0.2 | How to use this book and set up your labs (Mac, GCP/GKE, Nebius) | B | 2 | PUB; VINTRO |
| 0.3 | Learning paths by role: Platform, MLOps, LLM inference, HPC GPU cloud | B | 2 | JD_MAPPING; VINTRO |

## Part 1: Linux, from the command line to the kernel and performance  (tier 0, 30 chapters)

| # | Chapter | Level | Tier | Sources |
|---|---|---|---|---|
| 1.1 | The Linux big picture: kernel, userspace, distributions | B | 0 | HLW 1; SCL 7; NPA 3 |
| 1.2 | The command line: shells, commands, pipes and redirection | B | 0 | HLW 2; SCL 7,8 |
| 1.3 | Files and the directory hierarchy: paths, links, inodes | B | 0 | HLW 2; SCL 7,8 |
| 1.4 | Text-processing essentials: grep, sed, awk, find, xargs, sort | B | 0 | HLW 2; PUB; SCL 7,8 |
| 1.5 | Working remotely: SSH keys, file transfer, tmux and editors | B | 0 | HLW 12; SCL 10,18; PUB |
| 1.6 | Users, groups, permissions, ACLs, sudo and user environments | B | 0 | HLW 7,13; SCL 11,12 |
| 1.7 | Packages, repositories and software installation | B | 0 | HLW 15,16; SCL 24; SCL 7 |
| 1.8 | Processes, signals and job control | B | 0 | HLW 8; SP 3; SCL 7 |
| 1.9 | Shell scripting that survives production | B | 0 | HLW 11; SCL 28,29; SCL 7,8 |
| 1.10 | Devices, udev, sysfs and procfs | I | 0 | HLW 3; SCL 7,8 |
| 1.11 | How a program runs: system calls, libraries, ELF, strace and ldd | I | 0 | HLW 8,15,16; SP 5; PUB; VL1 ch1 |
| 1.12 | Disks, partitions and filesystems | I | 0 | HLW 4; SP 8,9; VL1 ch2 |
| 1.13 | LVM, RAID and NVMe | I | 0 | HLW 4; SP 9; V15; VL1 ch2 |
| 1.14 | Boot: firmware, GRUB, kernel, initramfs | I | 0 | HLW 5; SCL 23 |
| 1.15 | systemd: units, targets, timers, journald | I | 0 | HLW 6,7; SCL 30; VL1; VL1 ch4; SCL 7 |
| 1.16 | Logging, time synchronisation, cron and batch jobs | I | 0 | HLW 7; SCL 7; SCL 28 |
| 1.17 | Memory management: virtual memory, NUMA, huge pages, OOM | A | 0 | SP 7; VL1 |
| 1.18 | CPU scheduling and cgroups v1 and v2 | A | 0 | SP 6; HLW 8; VL1 |
| 1.19 | Namespaces: the kernel feature behind containers | I | 0 | HLW 17; SP 11; VL1 ch4 |
| 1.20 | Lab: build a container by hand with unshare, chroot, cgroups and overlayfs | I | 0 | HLW 17; PUB; VL1 ch4 |
| 1.21 | Linux security: capabilities, SELinux, AppArmor, seccomp, PAM, SSH hardening | A | 2 | HLW; PK 8; PUB; VL10 ch3 |
| 1.22 | Kernel modules, DKMS and sysctl tuning for GPU nodes | A | 1 | HLW 5; ASP 3; VL10 ch3 |
| 1.23 | Performance methodology: USE, workload characterisation, drill-down | I | 2 | SP 1,2,4 |
| 1.24 | Observability tools: perf, ftrace, BPF and bpftrace | A | 2 | SP 4,13,14,15 |
| 1.25 | Benchmarking correctly | A | 2 | SP 12 |
| 1.26 | KVM, QEMU and libvirt basics | I | 2 | HLW 17; SP 11 |
| 1.27 | Cloud computing and virtualization internals for Linux engineers | I | 2 | SP 11 |
| 1.28 | Putting it together: tuning a Linux node for GPU and HPC work | A | 1 | SP 16; ASP 3; SCL |
| 1.29 | Remote administration reference: SSH server and client options, host-based authentication, parallel shells, screen and tmux, IPMI and console managers | I | 0 | SCL 10; PUB |
| 1.30 | Network file sharing and remote graphical access: rsync in depth, Samba, SSHFS, NFS clients, cloud storage, X11, VNC and alternatives | I | 0 | HLW 12; SCL 18; PUB; SCL 28 |

## Part 2: Networking, from packets to data centers  (tier 0, 32 chapters)

| # | Chapter | Level | Tier | Sources |
|---|---|---|---|---|
| 2.1 | What happens when you curl a URL: a packet's journey end to end | B | 0 | CN 1; NK 1; HLW 9,10 |
| 2.2 | How networks work: layers, encapsulation, the TCP/IP model | B | 0 | CN 1 |
| 2.3 | Ethernet and L2: frames, MAC addresses, switching, ARP and NDP | B | 0 | CN 4,6,7 |
| 2.4 | IP addressing, subnetting and CIDR (IPv4 and IPv6), with practice | B | 0 | CN 4,5; HLW 9 |
| 2.5 | Routing on a host: routing tables, default gateways and forwarding | B | 0 | HLW 9; NK 2 |
| 2.6 | TCP in depth: handshake, windows, congestion control, retransmission | I | 0 | CN 2,3,5 |
| 2.7 | UDP, ICMP and the diagnostic tools: ping, traceroute, mtr | B | 0 | CN 5; HLW 9 |
| 2.8 | DNS in depth: resolution, records, resolvers and caching | B | 0 | HLW 10; CN 5; PUB |
| 2.9 | DHCP, NAT and PAT | B | 0 | CN 5; HLW 9,10 |
| 2.10 | HTTP, TLS and PKI basics | B | 0 | CN 10; HLW 10; PUB |
| 2.11 | VLANs, trunking and spanning tree | I | 0 | CN 7,11 |
| 2.12 | Link aggregation: LACP and MLAG | I | 0 | CN 7; SCL 4 |
| 2.13 | IP routing: static routes, dynamic routing and convergence | I | 0 | CN 12,13,14 |
| 2.14 | OSPF and IS-IS | I | 3 | CN 15,16 |
| 2.15 | BGP fundamentals | I | 2 | CN 16,17 |
| 2.16 | BGP in the data center: eBGP Clos, unnumbered, ECMP, anycast | A | 2 | CN 17,19; ADC 8 |
| 2.17 | Overlays: VXLAN and EVPN | A | 2 | CN 9; NK 3; PUB |
| 2.18 | Data center topologies: Clos, leaf-spine, oversubscription, failure domains | A | 2 | CN 19,20,22,23,25; ADC 3 |
| 2.19 | Queuing, QoS, ECN, PFC and DCB basics | A | 2 | CN 8; ADC 7 |
| 2.20 | Load balancing: L4, L7, ECMP hashing and proxies | I | 2 | CN; PK 6 |
| 2.21 | Network security: firewalls, TLS and zero trust | I | 2 | CN 10,21 |
| 2.22 | Linux networking: inspecting state with ip, ss and counters | B | 0 | HLW 9; SP 10; NK 2 |
| 2.23 | Linux networking: netfilter, nftables, conntrack and NAT | I | 0 | NK 2; VL1 |
| 2.24 | Linux networking: policy routing, bonding, MTU, NIC and stack tuning | A | 1 | SP 10; ASP 4 |
| 2.25 | Linux networking: namespaces, veth, bridges and container networking | I | 0 | NK 2,3 |
| 2.26 | Packet capture from scratch: tcpdump, tshark and Wireshark | I | 0 | SP 10,15; NK 1 |
| 2.27 | Lab: build network topologies with namespaces, FRR and Containerlab | I | 0 | NK 2; CN; PUB |
| 2.28 | Network automation fundamentals: APIs, YANG, NETCONF, gNMI, SDN, templates | I | 2 | NPA 2,8,9,10; CN 18 |
| 2.29 | Network automation in practice: Ansible, Nornir and CI/CD for networks | A | 2 | NPA 12,13,14; CN 26,27 |
| 2.30 | Network troubleshooting method and case studies | A | 1 | CN 24; SP 10 |
| 2.31 | Network monitoring and telemetry | I | 2 | ADC 11; NPA |
| 2.32 | Cloud networking: VPC, peering, load balancers and GCP specifics | I | 1 | NK 6; CN 28; PUB; NPA 4 |

## Part 3: Python for infrastructure engineers  (tier 2, 11 chapters)

| # | Chapter | Level | Tier | Sources |
|---|---|---|---|---|
| 3.1 | Python core: types, control flow, functions | B | 2 | LP 4-19; LP 1,2,3; NPA 6; VL2 ch0 |
| 3.2 | Modules, packages, virtual environments and packaging | B | 2 | LP 22-25; PUB |
| 3.3 | Idiomatic Python: the data model, comprehensions, generators | I | 2 | FP 1-3,17; LP 14,20; FP 6,7,9,10; VL2 ch1 |
| 3.4 | Classes, dataclasses, typing and protocols | I | 2 | FP 5,8,13,15; LP 26-32; FP 11,12,14,16; VL2 ch1,5 |
| 3.5 | Errors, files, text and bytes, subprocess and system scripting | I | 2 | LP 33-37; FP 4,18 |
| 3.6 | Concurrency: threads, processes and asyncio | A | 2 | FP 19-21; VL2 ch2 |
| 3.7 | Building APIs and microservices with FastAPI | I | 2 | FA 1-9; VL2 ch4 |
| 3.8 | Building CLIs, agents and exporters (Prometheus exporters, Redfish clients) | I | 2 | PM 11; PUB; VL2 ch3 |
| 3.9 | Testing, quality and CI for Python tooling | I | 2 | FA 8; AUR 14; LP 21; EAS 2; VL2 ch3 |
| 3.10 | Python for data and ML infrastructure: NumPy, pandas, PyTorch essentials | I | 2 | AIE; DMLS |
| 3.11 | Python under the hood: decorators, descriptors and metaprogramming (how frameworks work) | A | 2 | FP 22,23,24; LP 38,39,40,41; VL2 ch5 |

## Part 4: Automation and infrastructure as code (Ansible from zero, Terraform)  (tier 0, 27 chapters)

| # | Chapter | Level | Tier | Sources |
|---|---|---|---|---|
| 4.1 | Git from scratch for infrastructure engineers | B | 0 | NPA 11; NPA 5; VL10 ch17 |
| 4.2 | CI/CD pipelines: concepts and design | I | 2 | NPA 13; AUR 22; VL10 ch11 |
| 4.3 | Ansible from zero: what it is, how it works, installation and ad hoc commands | B | 0 | AUR 1,2 |
| 4.4 | YAML and Jinja2 for infrastructure code | B | 0 | AUR 3; PUB |
| 4.5 | Ansible inventory: hosts, groups, dynamic inventory and variables | B | 0 | AUR 4 |
| 4.6 | Ansible playbooks: tasks, modules, idempotency and check mode | B | 0 | AUR 3 |
| 4.7 | Ansible variables, facts, templates and filters | B | 0 | AUR 5 |
| 4.8 | Ansible handlers, conditionals, loops, blocks and error handling | I | 0 | AUR 10,11 |
| 4.9 | A real playbook end to end: deploying an application | I | 0 | AUR 6,7 |
| 4.10 | Debugging Ansible playbooks | I | 0 | AUR 8 |
| 4.11 | Ansible roles and collections | I | 0 | AUR 9,15 |
| 4.12 | Ansible Vault and secrets management | I | 0 | AUR; PUB |
| 4.13 | Testing Ansible: ansible-lint, Molecule and CI | I | 2 | AUR 14,22 |
| 4.14 | Ansible at scale: performance, strategies and callbacks | A | 2 | AUR 18,20 |
| 4.15 | Custom modules, plug-ins and Ansible Automation Platform | A | 2 | AUR 19,23,24 |
| 4.16 | Ansible for containers, cloud and network devices | I | 2 | AUR 12,13,16,17,21; NPA 12; VL10 ch4 |
| 4.17 | Ansible for GPU nodes and clusters | A | 1 | AUR; ASP 3; PUB; VL10 ch4 |
| 4.18 | Terraform refresher: why, providers, resources and the workflow | B | 2 | TUR 1,2; VL10 ch5 |
| 4.19 | Terraform state in depth: backends, locking and drift | I | 2 | TUR 3; VL10 ch5 |
| 4.20 | Terraform modules and reusable infrastructure | I | 2 | TUR 4; VL10 ch5 |
| 4.21 | Terraform loops, conditionals, lifecycle and gotchas | I | 2 | TUR 5; VL10 ch5 |
| 4.22 | Terraform secrets and multiple providers | I | 2 | TUR 6,7; VL10 ch5 |
| 4.23 | Production-grade Terraform: structure, testing and team workflows | A | 2 | TUR 8,9,10; VL10 ch5 |
| 4.24 | Terraform on GCP and Nebius: networks, GPU VMs and GKE | I | 1 | PUB |
| 4.25 | Terraform with Kubernetes and Helm providers; OpenTofu | I | 2 | PUB |
| 4.26 | GitOps with Argo CD and Flux | I | 2 | PK 11; PUB; VL10 ch11 |
| 4.27 | Lab: provision a GPU cluster with Terraform and Ansible | A | 1 | TUR; AUR; PUB |

## Part 5: Containers and Kubernetes, from internals to operators  (tier 0, 35 chapters)

| # | Chapter | Level | Tier | Sources |
|---|---|---|---|---|
| 5.1 | Containers from first principles: images, layers, registries | B | 0 | KUR 2; PK 3 |
| 5.2 | Container runtimes: containerd, runc, CRI and OCI | I | 0 | PK 3 |
| 5.3 | Kubernetes architecture overview: components and what talks to what | B | 0 | KUR 1,3; VL3 |
| 5.4 | Bare-metal Kubernetes from scratch with kubeadm (lab) | I | 0 | KUR 3,4,A; PK 1,2; PUB |
| 5.5 | The API server and etcd: how a request becomes cluster state | I | 0 | PK 1,2; KUR 17; PUB; VL3 ch1 |
| 5.6 | Controllers and the reconcile loop: how Kubernetes thinks | I | 0 | KUR 9-12,17; KPG |
| 5.7 | Pods and workloads: Deployments, StatefulSets, DaemonSets and Jobs | B | 0 | KUR 4-6,9-12,22; PK 14 |
| 5.8 | The life of a pod, end to end, including what the kernel does | I | 0 | KUR 5; PK 3,5; HLW 17; NK 3,4 |
| 5.9 | The kubelet and the node: CRI, cgroups, QoS classes, probes and eviction | I | 0 | PK 3; KUR 5; VL3 ch2 |
| 5.10 | Services, endpoints and kube-proxy: the life of a Service | I | 0 | KUR 7; NK 5; PK 6 |
| 5.11 | DNS and service discovery with CoreDNS | I | 0 | KUR 7; NK 5 |
| 5.12 | Ingress, load balancers and the Gateway API | I | 0 | KUR 8; PK 6; NK 6 |
| 5.13 | Pod networking under the hood: veth, bridges, routes and CNI plugins | I | 0 | NK 3,4,6; PK 5 |
| 5.14 | Overlay versus routed pod networking: VXLAN, BGP with Calico, eBPF with Cilium | A | 1 | PK 5; NK 4-6 |
| 5.15 | NetworkPolicy and the kernel: netfilter, conntrack and eBPF | I | 0 | NK 4,5; PK 5; VL3 ch3 |
| 5.16 | Configuration, secrets and RBAC | I | 0 | KUR 13,14; PK 7 |
| 5.17 | Storage internals: volumes, PV and PVC, CSI and mounts | I | 0 | KUR 16; PK 4; VL3 ch2 |
| 5.18 | Scheduling in depth: kube-scheduler, affinity, taints, priority and preemption | A | 1 | KUR; VL3; VL3 ch1 |
| 5.19 | Cluster deployment models and day-2 operations | A | 2 | PK 1,2; KUR 3 |
| 5.20 | Upgrades, etcd backup and restore, and disaster recovery | A | 2 | PK; PUB |
| 5.21 | Certificates, identity, admission control and policy | A | 2 | PK 8,10; KUR 19,20; VL3 ch3 |
| 5.22 | Multitenancy and platform services | A | 1 | PK 11,12,16 |
| 5.23 | Autoscaling: HPA, VPA, KEDA and the cluster autoscaler | A | 1 | PK 13 |
| 5.24 | Observability for Kubernetes | A | 2 | PK 9 |
| 5.25 | Troubleshooting Kubernetes from the node: crictl, nsenter, tcpdump and iptables | I | 0 | PK; NK; PUB |
| 5.26 | How Kubernetes uses the Linux kernel: a complete map | I | 0 | HLW 17; NK 2-5; PK 3-5 |
| 5.27 | Software supply chain security | A | 2 | PK 15 |
| 5.28 | Service mesh | I | 3 | KUR 15 |
| 5.29 | Extending Kubernetes: CRDs and operators | A | 2 | KUR 17,18; BCM-C 6; KPG |
| 5.30 | Go for Kubernetes engineers | I | 2 | KPG; PUB; NPA 7 |
| 5.31 | Operators in Go: controller-runtime and kubebuilder | A | 2 | KPG; PUB |
| 5.32 | Project: a GPU-node-health operator | A | 2 | KPG; PUB; V10 |
| 5.33 | Reading the GPU Operator and Network Operator source | A | 2 | KPG; PUB |
| 5.34 | GKE for GPU workloads: setup, node pools and quotas | I | 1 | PUB; GAK; K8GS; SKI |
| 5.35 | Multicluster and fleet management | A | 3 | KUR 21 |

## Part 6: HPC, supercomputers and Slurm  (tier 1, 31 chapters)

| # | Chapter | Level | Tier | Sources |
|---|---|---|---|---|
| 6.1 | What a supercomputer is: TOP500, Linpack, HPC versus AI factory | B | 2 | SCL 1,2; AF 9 |
| 6.2 | Cluster anatomy: head, login, compute, storage and management nodes | B | 2 | SCL 3,4,6; SCL 17 |
| 6.3 | Parallel computing concepts: Amdahl, scaling, shared memory versus message passing | I | 2 | SCL 21,22; PUB; PHPC |
| 6.4 | MPI in practice: Open MPI, ranks, collectives and tuning | I | 2 | SCL 21,22; PHPC; VL10 ch7 |
| 6.5 | OpenMP, compilers and optimisation flags | I | 3 | SCL 21; PHPC |
| 6.6 | Environment modules, Spack and EasyBuild | I | 2 | SCL 21,24 |
| 6.7 | Slurm architecture and installation | I | 1 | SCL 13-15; DAI 8; VL6 ch4; VL10 ch6,14 |
| 6.8 | Slurm configuration: nodes, partitions and cgroups | I | 1 | SCL 15 |
| 6.9 | Slurm accounting and scheduling policy: QoS, fairshare, backfill, preemption | A | 1 | SCL 15; VL10 ch6,14 |
| 6.10 | Slurm GPU scheduling: gres, NVML autodetect, MIG and device constraints | A | 1 | DAI 8; SCL 15; PUB |
| 6.11 | Submitting and launching jobs: sbatch, srun, salloc, arrays, dependencies | I | 1 | SCL 15; DAI 8 |
| 6.12 | Multi-node training on Slurm: PMIx, torchrun, NCCL environment, binding, topology | A | 1 | DAI 8; ASP 4 |
| 6.13 | Containers on Slurm: enroot and pyxis | A | 1 | SCL 16; DAI 8; PUB; VL10 ch8 |
| 6.14 | Slurm operations: prolog, epilog, health checks, drain, reason codes, troubleshooting | A | 1 | SCL 15; V20; VL10 ch9 |
| 6.15 | Slurm high availability, upgrades and scaling | A | 1 | SCL; PUB; VL10 ch6,14 |
| 6.16 | Slurm on Kubernetes: Slinky and Soperator | A | 1 | PUB |
| 6.17 | Other schedulers: PBS, Torque, LSF and Flux | I | 3 | SCL 14 |
| 6.18 | Parallel storage concepts and the limits of NFS | I | 2 | SCL 9 |
| 6.19 | Lustre architecture and operation | A | 2 | V15 ch5; PUB; SCL 28 |
| 6.20 | BeeGFS, GPFS, WekaFS and VAST | I | 2 | V15; PUB |
| 6.21 | Parallel I/O and checkpoint patterns | A | 2 | ASP 5; V15 |
| 6.22 | Provisioning with PXE, iPXE, DHCP, TFTP and image management | A | 1b | SCL 23-26; VL10 ch1,3 |
| 6.23 | xCAT, Warewulf and cluster managers compared with BCM | I | 2 | SCL 26; PUB; SCL 28 |
| 6.24 | Users, LDAP, SSSD, quotas and accounting at scale | I | 2 | SCL 11,12; SCL 28 |
| 6.25 | Remote access, bastions, Open OnDemand and user environments | I | 3 | SCL 18; SCL 27 |
| 6.26 | Cluster monitoring and health at scale | A | 2 | SCL 19 |
| 6.27 | Backup and data protection | I | 3 | SCL 20 |
| 6.28 | HPC benchmarking: HPL, HPCG, IOR, OSU and NCCL tests | A | 2 | SP 12; ASP; PHPC |
| 6.29 | Containers and reproducibility in HPC: Apptainer and enroot | I | 2 | SCL 16 |
| 6.30 | Facility basics: power, cooling, racks and liquid cooling | I | 2 | V1; AF; SPB200; SCL 28 |
| 6.31 | Capstone: build and operate a small Slurm GPU cluster | A | 1 | all of Part 6; VL10 ch0 |

## Part 7: Out-of-band management and Redfish  (tier 1b, 15 chapters)

| # | Chapter | Level | Tier | Sources |
|---|---|---|---|---|
| 7.1 | BMCs, IPMI and out-of-band management | B | 1b | RF-S; V5 ch3; VL10 ch1 |
| 7.2 | Redfish concepts: service root, resources, collections, OData | B | 1b | RF-S 5,6; RF-G |
| 7.3 | The Redfish protocol: HTTP methods, headers, status codes, query parameters | I | 1b | RF-S 7-9 |
| 7.4 | Redfish authentication, sessions and security | I | 1b | RF-S 13 |
| 7.5 | Redfish actions, tasks, events and subscriptions | A | 1b | RF-S |
| 7.6 | The Redfish schema: reading CSDL, JSON schema and the resource guide | I | 1b | RF-SC; RF-G |
| 7.7 | Systems, Chassis and Managers: the core resource model | I | 1b | RF-G |
| 7.8 | Power, thermal, sensors and environment | I | 1b | RF-G |
| 7.9 | Storage, network adapters and PCIe devices | I | 1b | RF-G |
| 7.10 | Firmware inventory and the UpdateService | A | 1b | RF-G; VL10 ch16 |
| 7.11 | Log services, event logs and diagnostics | I | 1b | RF-G |
| 7.12 | Automating Redfish with Python, Ansible and Go | A | 1b | RF-S; PUB |
| 7.13 | Redfish on NVIDIA DGX and HGX: BMC, GPU baseboard and management | A | 1b | V5 ch3; VL; V6; PUB |
| 7.14 | Fleet-scale hardware management and node lifecycle automation | A | 1b | PUB; BCM-A; VL10 ch1 |
| 7.15 | BMC security hardening and attestation | A | 1b | V18 ch2; RF-S 13 |

## Part 8: NVIDIA Base Command Manager (BCM)  (tier 1b, 16 chapters)

| # | Chapter | Level | Tier | Sources |
|---|---|---|---|---|
| 8.1 | BCM architecture and concepts | B | 1b | BCM-A 1,2; BCM-I 1; VL10 ch2 |
| 8.2 | Planning and installing BCM | I | 1b | BCM-I |
| 8.3 | Cluster configuration: networks, nodes and categories | I | 1b | BCM-A 3; VL10 ch2 |
| 8.4 | Node provisioning: images, kernels, categories and the PXE flow | A | 1b | BCM-A 5; VL10 ch2 |
| 8.5 | cmsh and Base View: administering the cluster | I | 1b | BCM-A 2 |
| 8.6 | Users, authentication and security in BCM | I | 1b | BCM-A |
| 8.7 | Power, BMC and hardware management in BCM | I | 1b | BCM-A; RF-S |
| 8.8 | Workload managers under BCM: Slurm setup | A | 1b | BCM-A |
| 8.9 | Kubernetes under BCM: deployment and GPU enablement | A | 1b | BCM-C |
| 8.10 | Containerization in BCM: Docker, Apptainer and enroot | I | 1b | BCM-C |
| 8.11 | Monitoring, health checks and alerts in BCM | A | 1b | BCM-A |
| 8.12 | High availability and head-node failover | A | 1b | BCM-A; VL10 ch13 |
| 8.13 | Day-2 operations: updates, scaling, hardware replacement, disaster recovery | A | 1b | BCM-A; VL10 ch13 |
| 8.14 | Air-gapped installation and upgrades | A | 1b | BCM-C B,C |
| 8.15 | BCM in an AI factory: DGX SuperPOD integration | A | 1b | BCM-A; SPB200; SPGB300 |
| 8.16 | Mission Control, DGX Cloud and autonomous recovery concepts | I | 1b | PUB; V21 |

## Part 9: NVIDIA systems and reference architectures  (tier 1b, 14 chapters)

| # | Chapter | Level | Tier | Sources |
|---|---|---|---|---|
| 9.1 | DGX system families and what they are for | B | 1b | V4; V5; ASP 2 |
| 9.2 | Inside a DGX H100 and H200 system | I | 1b | V5 ch2; ASP 2 |
| 9.3 | HGX platforms and OEM integration | I | 1b | V6 |
| 9.4 | Grace CPU, GH200 and GB200 superchips | I | 1b | V4 ch7; ASP 2 |
| 9.5 | GB200 and GB300 NVL72 rack-scale systems | A | 1b | V5 ch7; V6 ch7; SPGB300; ASP 2 |
| 9.6 | DGX SuperPOD concepts: scalable units, fabrics and tiers | A | 1b | SPB200; SPGB300; V21 |
| 9.7 | DGX B200 SuperPOD data center design: power, cooling, cabling and layout | A | 1b | SPB200 |
| 9.8 | GB300 SuperPOD reference architecture | A | 1b | SPGB300 |
| 9.9 | Compute, storage, in-band and out-of-band networks in a SuperPOD | A | 1b | SPGB300; SPB200 |
| 9.10 | BasePOD and smaller deployments | I | 1b | PUB; V21 |
| 9.11 | Power delivery, thermal design and liquid cooling | A | 1b | V5 ch4; V1 ch6; SPB200 |
| 9.12 | Software stack and management in an AI factory | I | 1b | V21 ch6; BCM-A |
| 9.13 | Sizing and capacity-planning exercises | A | 1b | V21; V19; VL8 ch1,2 |
| 9.14 | Cloud GPU platforms: DGX Cloud, CoreWeave, Nebius and GCP A3 and A4 | I | 1b | PUB |

## Part 10: The GPU and CUDA  (tier 2, 22 chapters)

| # | Chapter | Level | Tier | Sources |
|---|---|---|---|---|
| 10.1 | Why GPUs: CPU versus GPU and throughput design | B | 2 | V1; V2 ch1; ASP 1 |
| 10.2 | The execution model: threads, warps, blocks and SMs | I | 2 | V2; ASP 6; VL4 ch1 |
| 10.3 | The GPU memory hierarchy | I | 2 | V2; ASP 6,7; VL4 ch1 |
| 10.4 | Tensor cores and numerical precision | I | 2 | ASP 2,9; V2 |
| 10.5 | The roofline model and performance modelling | A | 2 | ASP 9; V17 ch3 |
| 10.6 | GPU interconnects: PCIe, NVLink, NVSwitch and NVLink-C2C | I | 2 | ASP 2; V7 ch2,3 |
| 10.7 | GPU generations and product line: Ampere, Hopper, Blackwell; PCIe versus SXM | I | 2 | V4 |
| 10.8 | Operating GPU nodes: nvidia-smi, topology, clocks and throttling | I | 1 | V2; V16 |
| 10.9 | The NVIDIA software stack: driver, CUDA toolkit, container toolkit, compatibility | I | 1 | V3 ch2; ASP 3; VL4 ch2 |
| 10.10 | Fabric Manager, NVSM and NVLink domains | A | 1 | PUB; V7 |
| 10.11 | CUDA programming basics: kernels, indexing and memory | I | 2 | V3; ASP 6 |
| 10.12 | Streams, events, asynchronous copies and pinned memory | I | 2 | V3; ASP 11 |
| 10.13 | Memory access patterns and profiling | A | 2 | ASP 7 |
| 10.14 | Occupancy, warp efficiency and instruction-level parallelism | A | 2 | ASP 8 |
| 10.15 | Kernel efficiency and arithmetic intensity | A | 2 | ASP 9 |
| 10.16 | Intra-kernel pipelining, warp specialization and thread block clusters | A | 2 | ASP 10 |
| 10.17 | Inter-kernel pipelining, synchronization and stream-ordered allocation | A | 2 | ASP 11 |
| 10.18 | Dynamic scheduling, CUDA graphs and device-initiated orchestration | A | 2 | ASP 12; V3 |
| 10.19 | Triton language and compilers: OpenAI Triton, torch.compile, XLA | A | 2 | ASP 14 |
| 10.20 | Profiling tools: Nsight Systems, Nsight Compute, PyTorch profiler | A | 2 | ASP 13; V17 ch2 |
| 10.21 | GPU health: DCGM, ECC, row remapping and Xid | A | 1 | V16; V20; VL4 ch3 |
| 10.22 | GPU troubleshooting scenarios | A | 1 | V20 |

## Part 11: GPUs on Kubernetes, scheduling and virtualization  (tier 1, 30 chapters)

| # | Chapter | Level | Tier | Sources |
|---|---|---|---|---|
| 11.1 | Why Kubernetes needs a GPU platform layer | B | 1 | V10 ch1 |
| 11.2 | Device plugin, container toolkit, CDI and runtime classes | I | 1 | V10; GAK 3; K8GS |
| 11.3 | Node Feature Discovery and GPU Feature Discovery | I | 1 | V10 ch5 |
| 11.4 | GPU Operator architecture and operands | I | 1 | V10 ch6,7; K8GS; VL4 ch2 |
| 11.5 | GPU Operator installation, configuration and upgrades | A | 1 | V10 ch10,11 |
| 11.6 | Scheduling GPUs: requests, Topology Manager, CPU and NUMA alignment | A | 1 | V10 ch8; ASP 3; K8GS; SKI |
| 11.7 | Multi-node jobs: why a pod cannot span nodes, and gang scheduling concepts | A | 1 | GAK 7; PUB; K8GS; VL6 ch4 |
| 11.8 | Kueue, Volcano and scheduler plugins | A | 1 | GAK 7; PUB; K8GS |
| 11.9 | JobSet, LeaderWorkerSet, PyTorchJob and the MPI Operator | A | 1 | GAK 6,7; PUB; K8GS |
| 11.10 | Secondary networks: Multus, SR-IOV device plugin and RDMA device plugin | A | 1 | PK 5; PUB |
| 11.11 | NVIDIA Network Operator | A | 1 | VL6; PUB |
| 11.12 | Dynamic Resource Allocation (DRA) | A | 1 | GAK 3; VL3; PUB |
| 11.13 | KAI Scheduler: why default scheduling is not enough | I | 1 | PUB; GAK 7 |
| 11.14 | KAI Scheduler architecture and resources | A | 1 | PUB |
| 11.15 | KAI queues, quotas and fair sharing | A | 1 | PUB |
| 11.16 | KAI gang scheduling and topology-aware placement | A | 1 | PUB |
| 11.17 | KAI GPU sharing and fractions | A | 1 | PUB |
| 11.18 | KAI operations and troubleshooting | A | 1 | PUB |
| 11.19 | The Run:ai platform view | I | 1 | PUB |
| 11.20 | Scheduler comparison guide: KAI, Kueue, Volcano, YuniKorn and Slurm | I | 1 | PUB |
| 11.21 | PCIe, IOMMU, VFIO and device passthrough | A | 1 | SP 11; PUB |
| 11.22 | SR-IOV for NICs and GPUs | A | 1 | SP 11; V18 ch7; PUB |
| 11.23 | NVIDIA vGPU: architecture, profiles and licensing | A | 1 | V11 ch5; GAK 3; PUB |
| 11.24 | MIG in depth | A | 1 | V11 ch2,3; GAK 3; VL4 ch3 |
| 11.25 | Time-slicing, MPS and oversubscription | A | 1 | V11 ch4; GAK 3; VL4 ch3 |
| 11.26 | Choosing a GPU sharing model | I | 1 | V11 ch6; VL4 ch3 |
| 11.27 | Virtual machines on Kubernetes: KubeVirt, Kata and GPU passthrough | A | 1 | PUB |
| 11.28 | DPUs, BlueField and DOCA | A | 2 | V9 ch9; V18 ch8 |
| 11.29 | Multi-tenancy, quotas, fault tolerance and health on GPU clusters | A | 1 | V11 ch8-10; V19; SKI |
| 11.30 | Lab: multi-node GPU Kubernetes on GKE and Nebius | A | 1 | PUB; K8GS |

## Part 12: Complete AI networking  (tier 1, 24 chapters)

| # | Chapter | Level | Tier | Sources |
|---|---|---|---|---|
| 12.1 | AI traffic: collectives, incast and elephant flows | I | 1 | ADC 1,2; ASP 4; V7 |
| 12.2 | RDMA fundamentals: verbs, queue pairs and memory registration | I | 1 | V8 ch3; ADC 7; SCL 5; VL6 ch1 |
| 12.3 | RoCEv2 transport and congestion management | A | 1 | ADC 7; V9 ch3; VL6 ch1 |
| 12.4 | PFC, ECN and DCQCN in depth | A | 1 | V9 ch4,5; ADC 7 |
| 12.5 | Data center bridging and QoS for AI | A | 1 | V9 ch6 |
| 12.6 | InfiniBand fundamentals and addressing | I | 1 | SCL 5; V8 ch1-4 |
| 12.7 | InfiniBand subnet manager, routing, topologies and rails | A | 1 | V8 ch5,6; ADC 8 |
| 12.8 | InfiniBand adaptive routing and congestion control | A | 1 | V8 ch7 |
| 12.9 | InfiniBand diagnostics, UFM and operations | A | 1 | V8 ch9,10; SCL 5 |
| 12.10 | HDR, NDR, XDR, optics and cabling | I | 2 | V8 ch8; ADC 4 |
| 12.11 | NVIDIA Spectrum-X and Spectrum switches | A | 2 | V9 ch7; PUB |
| 12.12 | Ethernet versus InfiniBand: a design decision guide | I | 2 | ADC; V9 |
| 12.13 | Fabric design: topology, oversubscription and scale | A | 1 | ADC 3,5; V7 ch11 |
| 12.14 | Load balancing and routing for AI fabrics | A | 1 | ADC 6,8 |
| 12.15 | NCCL: collectives and algorithms | A | 1 | ASP 4; V7 ch9; DAI 2; VL6 ch2 |
| 12.16 | NCCL: topology, channels, transports and environment variables | A | 1 | ASP 4 |
| 12.17 | nccl-tests and fabric benchmarking | A | 1 | ASP 4; DAI 10 |
| 12.18 | NCCL debugging: hangs, timeouts and errors | A | 1 | V20; ASP 4; VL10 ch15 |
| 12.19 | GPUDirect RDMA and GPUDirect Storage | A | 1 | V7 ch5,6; VL6 ch2 |
| 12.20 | SHARP and in-network computing | A | 2 | ASP 4; PUB |
| 12.21 | Storage networks, Ultra Ethernet and scale-up fabrics | A | 2 | ADC 9,12,13 |
| 12.22 | AI network telemetry and KPIs | A | 2 | ADC 10,11; V8 ch9 |
| 12.23 | Fabric validation and capacity planning | A | 2 | V9 ch10; V8 ch11 |
| 12.24 | AI networking troubleshooting playbook | A | 1 | V8 ch10; V9 ch11; V20 |

## Part 13: AI storage  (tier 2, 9 chapters)

| # | Chapter | Level | Tier | Sources |
|---|---|---|---|---|
| 13.1 | The AI data path: from storage to GPU | B | 2 | V15 ch1,2; VL6 ch3 |
| 13.2 | Local NVMe and data staging | I | 2 | V15 ch3 |
| 13.3 | GPUDirect Storage architecture | A | 2 | V15 ch4; ASP 5 |
| 13.4 | Lustre for AI | A | 2 | V15 ch5 |
| 13.5 | BeeGFS, Weka, VAST and object storage | I | 2 | V15 ch6,7 |
| 13.6 | Data loading, small files and metadata | A | 2 | V15 ch9; ASP 5; VL6 ch3 |
| 13.7 | Checkpoint architecture and recovery | A | 2 | V15 ch8; V13 ch9 |
| 13.8 | Capacity, performance and cost planning | A | 2 | V15 ch10 |
| 13.9 | Storage troubleshooting | A | 2 | V15 ch11 |

## Part 14: Distributed training and fine-tuning  (tier 2, 16 chapters)

| # | Chapter | Level | Tier | Sources |
|---|---|---|---|---|
| 14.1 | ML and deep learning fundamentals for infrastructure engineers | B | 2 | DMLS 1,2,6; EAS 3 |
| 14.2 | Transformers and LLM architecture | I | 2 | AIE 2; EAS 4 |
| 14.3 | Training memory and compute anatomy | I | 2 | V13 ch2; DAI 1; VL5 ch1 |
| 14.4 | Data parallelism and DDP | I | 2 | DAI 3; V13 ch3; VL5 ch1 |
| 14.5 | FSDP and parameter sharding | A | 2 | DAI 4; V13 ch4 |
| 14.6 | DeepSpeed and ZeRO | A | 2 | DAI 5; V13 ch5 |
| 14.7 | Tensor, pipeline and expert parallelism; Megatron | A | 2 | DAI 5; V13 ch6,7 |
| 14.8 | PyTorch performance: profiling, tuning and scaling | A | 2 | ASP 13 |
| 14.9 | PyTorch compilers and kernels: torch.compile | A | 2 | ASP 14 |
| 14.10 | Multi-node training architecture | A | 2 | V13 ch10; DAI 8 |
| 14.11 | Checkpointing, fault tolerance and elastic training | A | 2 | V13 ch9 |
| 14.12 | Training performance engineering and troubleshooting | A | 2 | V13 ch11; ASP 13 |
| 14.13 | Fine-tuning: SFT, LoRA and QLoRA, preference alignment | A | 1 | AIE 7; LEH 5,6; LLO 5 |
| 14.14 | Dataset engineering for fine-tuning | I | 1 | AIE 8; LEH 3; LLO 4 |
| 14.15 | Fine-tuning infrastructure and cost | A | 1 | GAK 6; PUB; K8GS |
| 14.16 | NeMo framework and customisation | I | 2 | V14 ch5; PUB |

## Part 15: LLM inference and serving  (tier 1, 18 chapters)

| # | Chapter | Level | Tier | Sources |
|---|---|---|---|---|
| 15.1 | The anatomy of an inference request | B | 1 | V12 ch1,2; V1 ch4; VL5 ch2 |
| 15.2 | Batching, the KV cache and quantization fundamentals | I | 1 | HLS 1-7; AIE 9; LLP; VL5 ch2 |
| 15.3 | vLLM in depth | A | 1 | DAI 6; HLS 8; V12 ch6; LLP |
| 15.4 | SGLang and cross-request optimisation | A | 1 | DAI 7 |
| 15.5 | TensorRT and TensorRT-LLM | A | 1 | V12 ch4,5 |
| 15.6 | Triton Inference Server | A | 1 | V12 ch3 |
| 15.7 | NVIDIA NIM and the NIM Operator | A | 1 | V14 ch3,4 |
| 15.8 | NVIDIA Dynamo, llm-d and disaggregated serving | A | 1 | ASP 17; PUB |
| 15.9 | Multinode inference: parallelism, decoding and routing | A | 1 | ASP 15 |
| 15.10 | Prefill and decode disaggregation | A | 1 | ASP 17 |
| 15.11 | Advanced prefill-decode and KV cache tuning | A | 1 | ASP 18 |
| 15.12 | Dynamic and adaptive inference engine optimisations | A | 1 | ASP 19; HLS 10 |
| 15.13 | Profiling, debugging and tuning inference at scale | A | 1 | ASP 16 |
| 15.14 | Benchmarking: genai-perf, latency percentiles and goodput | A | 1 | HLS 9; DAI 10; V12 ch10; LLP |
| 15.15 | Autoscaling inference: HPA, KEDA and scale-to-zero | A | 1 | GAK 4; PUB; K8GS; LLP; VL5 ch3 |
| 15.16 | Production serving stack and reliability | A | 1 | DAI 9; V12 ch11; LLP; DMLS 7 |
| 15.17 | Lab: serve and benchmark on GKE and Nebius | A | 1 | GAK; PUB; K8GS |
| 15.18 | Inference cost, capacity and cost per token | A | 2 | V12; V19 |

## Part 16: MLOps and LLMOps tools and platforms  (tier 1, 15 chapters)

| # | Chapter | Level | Tier | Sources |
|---|---|---|---|---|
| 16.1 | MLOps foundations and lifecycle | B | 1 | PM 1,2; DMLS 1; MLPE; AIE 1; LLO 1,2; EAS 5 |
| 16.2 | Data versioning and experiment tracking: DVC, MLflow, Weights and Biases | I | 1 | PM; V25; MLPE |
| 16.3 | Data pipelines and feature stores | I | 1 | DMLS 3-5; PUB; MLPE; GAK 2 |
| 16.4 | Pipeline orchestration: Kubeflow Pipelines, Argo, Flyte, Airflow | A | 1 | DMLS 10; PUB; MLPE; PM 5 |
| 16.5 | Distributed compute for ML: Ray, KubeRay, Training Operator and Katib | A | 1 | PUB |
| 16.6 | Model registry, CI/CD and GitOps for models | A | 1 | PM 4; DMLS 9; MLPE; PM 3 |
| 16.7 | Model serving platforms: KServe, Seldon and BentoML | A | 1 | PUB; GAK 1; MLPE; K8GS; DMLS 7; PM 10 |
| 16.8 | LLMOps: RAG, vector databases and agents | A | 1 | LLO 3,6; AIE 6; GAK 8,9; LLP; AIE 5; VL5 ch3 |
| 16.9 | LLM evaluation and guardrails | I | 1 | AIE 3,4; LEH 7; LLO 7 |
| 16.10 | Monitoring, drift and continual learning | I | 1 | DMLS 8,9; PM 6 |
| 16.11 | Cloud MLOps platforms: Vertex AI, SageMaker and Azure ML | I | 2 | PM 7-9 |
| 16.12 | NVIDIA enterprise stack: AI Enterprise, NGC and licensing | I | 1b | V14 |
| 16.13 | Governance, privacy and compliance for ML platforms | A | 2 | LLO 8; EAS 9,10; DMLS 11 |
| 16.14 | Platform design: multi-tenant AI factory, quotas and chargeback | A | 1 | V21; PK 12; MLPE; SKI; AIE 10; LLO 9 |
| 16.15 | Lab: end-to-end MLOps on GKE | A | 1 | V25; PUB; MLPE; PM 12 |

## Part 17: Observability, performance and operations  (tier 2, 16 chapters)

| # | Chapter | Level | Tier | Sources |
|---|---|---|---|---|
| 17.1 | Observability foundations: metrics, logs and traces | B | 2 | V16 ch1,2; PK 9; EAS 11; VL7 ch1 |
| 17.2 | Prometheus and Grafana | I | 2 | V16 ch5; VL7 ch1 |
| 17.3 | Logging with Loki and tracing with OpenTelemetry | I | 2 | PUB |
| 17.4 | DCGM exporter and interpreting GPU metrics | A | 2 | V16 ch3,4; GAK 5; VL7 ch2 |
| 17.5 | Distributed observability and profiling | A | 2 | V16 ch6,7; VL7 ch2 |
| 17.6 | Alerting, SLOs and health checks for GPU clusters | A | 2 | V16 ch9; VL10 ch9 |
| 17.7 | Failure modes and detection | A | 2 | V16 ch8; V20 |
| 17.8 | Performance engineering methodology and decision trees | A | 2 | V17; ASP 1; EAS 8 |
| 17.9 | The AI systems performance checklist (master) | A | 1 | ASP app |
| 17.10 | Cluster lifecycle, upgrades and change management | A | 2 | V19 ch1; EAS 6; AF 8; VL10 ch10,16 |
| 17.11 | Incident response and game days | A | 2 | V19 ch2; V16 ch12; VL7 ch3 |
| 17.12 | Capacity planning and cost optimisation | A | 2 | V19 ch3,6; V21; SKI; VL8 ch2 |
| 17.13 | Reliability engineering for AI infrastructure | A | 2 | EAS 7; V19 |
| 17.14 | Disaster recovery and data resilience | A | 2 | V19 ch10 |
| 17.15 | On-call runbooks | A | 2 | V19 ch12; VL10 ch12 |
| 17.16 | AI-assisted operations and scaling toward very large clusters | A | 2 | ASP 20; DAI 11; LLO 10 |

## Part 18: Security  (tier 2, 7 chapters)

| # | Chapter | Level | Tier | Sources |
|---|---|---|---|---|
| 18.1 | Threat modeling for AI infrastructure | I | 2 | V18 ch1; VL8 ch3 |
| 18.2 | Hardware and firmware trust | A | 2 | V18 ch2 |
| 18.3 | Containers and the software supply chain | A | 2 | V18 ch3; PK 15 |
| 18.4 | Kubernetes access control and pod security | A | 2 | V18 ch4,5; PK 8,10 |
| 18.5 | GPU sharing security, DMA, IOMMU and SR-IOV | A | 2 | V18 ch6,7 |
| 18.6 | BlueField, DOCA and confidential computing | A | 2 | V18 ch8,9 |
| 18.7 | Data and model protection, audit and compliance | A | 2 | V18 ch10,11; EAS 9,10; VL8 ch3 |

## Part 19: Capstones, design and interview readiness  (tier 2, 15 chapters)

| # | Chapter | Level | Tier | Sources |
|---|---|---|---|---|
| 19.1 | Capstone: a Slurm GPU cluster | A | 1 | V24; Part 6 |
| 19.2 | Capstone: a Kubernetes GPU platform with KAI and Kueue | A | 1 | V24 P7 |
| 19.3 | Capstone: inference on GKE with vLLM, Triton, TensorRT-LLM, NIM and KServe | A | 1 | V24 P11 |
| 19.4 | Capstone: multi-node training with fault tolerance | A | 1 | V24 P3 |
| 19.5 | Capstone: an nccl-tests fabric lab | A | 1 | V24 P2 |
| 19.6 | Capstone: node-health automation with DCGM and an operator | A | 1 | V24 P5 |
| 19.7 | Capstone: an observability platform | A | 2 | V24 P4 |
| 19.8 | Capstone: MIG multi-tenancy | A | 2 | V24 P6 |
| 19.9 | Capstone: capacity planning | A | 2 | V24 P9 |
| 19.10 | Customer workshops and the consulting method | I | 3 | V22; EAS 12,13,14; VL8 ch4; VL10 ch12 |
| 19.11 | System design: a training cluster | A | 2 | V23 ch10; VL8 ch1 |
| 19.12 | System design: inference serving | A | 2 | V23 ch11 |
| 19.13 | System design: research infrastructure | A | 2 | V23 ch12 |
| 19.14 | Interview question bank by topic | all | 1 | V23; V26; VCORE; VL9 |
| 19.15 | Interview cheat sheet | all | 1 | V23 ch13; V26; VL9 |
