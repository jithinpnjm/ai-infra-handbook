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
| 2.22 | Linux networking: inspecting state with ip, ss and counters | drafted | 7850 |  |
| 2.23 | Linux networking: netfilter, nftables, conntrack and NAT | drafted | 7235 |  |
| 2.25 | Linux networking: namespaces, veth, bridges and container networking | drafted | 6880 |  |
| 2.26 | Packet capture from scratch: tcpdump, tshark and Wireshark | drafted | 7161 |  |
| 2.27 | Lab: build network topologies with namespaces, FRR and Containerlab | drafted | 6218 |  |
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
| 2.24 | Linux networking: policy routing, bonding, MTU, NIC and stack tuning | drafted | 7835 |  |
| 2.30 | Network troubleshooting method and case studies | drafted | 7632 |  |
| 2.32 | Cloud networking: VPC, peering, load balancers and GCP specifics | drafted | 7790 |  |
| 4.17 | Ansible for GPU nodes and clusters | drafted | 4715 |  |
| 4.24 | Terraform on GCP and Nebius: networks, GPU VMs and GKE | drafted | 4211 |  |
| 4.27 | Lab: provision a GPU cluster with Terraform and Ansible | drafted | 3405 |  |
| 5.14 | Overlay versus routed pod networking: VXLAN, BGP with Calico, eBPF with Cilium | drafted | 4086 |  |
| 5.18 | Scheduling in depth: kube-scheduler, affinity, taints, priority and preemption | drafted | 5030 |  |
| 5.22 | Multitenancy and platform services | drafted | 4167 |  |
| 5.23 | Autoscaling: HPA, VPA, KEDA and the cluster autoscaler | drafted | 4193 |  |
| 5.34 | GKE for GPU workloads: setup, node pools and quotas | drafted | 3576 |  |
| 6.7 | Slurm architecture and installation | drafted | 9470 | `slurm_arch_lab.py` (3/3 pass); `validate_chapter.py` 12/12 PASS |
| 6.8 | Slurm configuration: nodes, partitions and cgroups | drafted | 5042 | `slurmconf_lint_lab.py` (3/3 pass); `validate_chapter.py` 12/12 PASS |
| 6.9 | Slurm accounting and scheduling policy: QoS, fairshare, backfill, preemption | reviewed | 6109 | `fairtree_sim_lab.py` (3/3 pass), `SCL 15` |
| 6.10 | Slurm GPU scheduling: gres, NVML autodetect, MIG and device constraints | reviewed | 5789 | `gpu_env_check_lab.py` (3/3 pass), `DAI 8`, `SCL 15` |
| 6.11 | Submitting and launching jobs: sbatch, srun, salloc, arrays, dependencies | reviewed | 6237 | `sbatch_lint_lab.py` (3/3 pass), `SCL 15`, `DAI 8` |
| 6.12 | Multi-node training on Slurm: PMIx, torchrun, NCCL environment, binding, topology | reviewed | 6065 | `slurm_dist_init_lab.py` (3/3 pass), `DAI 8`, `ASP 4` |
| 6.13 | Containers on Slurm: enroot and pyxis | reviewed | 5267 | `enroot_pyxis_lab.py` (3/3 pass), `SCL 16`, `DAI 8` |
| 6.14 | Slurm operations: prolog, epilog, health checks, drain, reason codes, troubleshooting | reviewed | 6357 | `node_health_lab.py` (3/3 pass), `SCL 15`, `V20` |
| 6.15 | Slurm high availability, upgrades and scaling | reviewed | 5241 | `slurm_upgrade_path_lab.py` (3/3 pass), `SCL 15` |
| 6.16 | Slurm on Kubernetes: Slinky and Soperator | reviewed | 5083 | `slinky_soperator_lab.py` (3/3 pass), Slinky & Soperator |
| 6.31 | Capstone: build and operate a small Slurm GPU cluster | reviewed | 7870 | `capstone_demo_lab.py` (3/3 pass), `volume-10/00c-slurm-bcm-interview-lab.md` |
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
| 14.13 | Fine-tuning: SFT, LoRA and QLoRA, preference alignment | drafted | 13639 |  |
| 14.14 | Dataset engineering for fine-tuning | drafted | 10131 |  |
| 14.15 | Fine-tuning infrastructure and cost | drafted | 14694 |  |
| 15.1 | The anatomy of an inference request | drafted | 12275 |  |
| 15.2 | Batching, the KV cache and quantization fundamentals | drafted | 12493 |  |
| 15.3 | vLLM in depth | drafted | 13817 |  |
| 15.4 | SGLang and cross-request optimisation | drafted | 11200 |  |
| 15.5 | TensorRT and TensorRT-LLM | drafted | 10394 |  |
| 15.6 | Triton Inference Server | drafted | 10126 |  |
| 15.7 | NVIDIA NIM and the NIM Operator | drafted | 9706 |  |
| 15.8 | NVIDIA Dynamo, llm-d and disaggregated serving | drafted | 10897 |  |
| 15.9 | Multinode inference: parallelism, decoding and routing | drafted | 12360 |  |
| 15.10 | Prefill and decode disaggregation | drafted | 12209 |  |
| 15.11 | Advanced prefill-decode and KV cache tuning | drafted | 11378 |  |
| 15.12 | Dynamic and adaptive inference engine optimisations | drafted | 12458 |  |
| 15.13 | Profiling, debugging and tuning inference at scale | drafted | 11054 |  |
| 15.14 | Benchmarking: genai-perf, latency percentiles and goodput | drafted | 13802 |  |
| 15.15 | Autoscaling inference: HPA, KEDA and scale-to-zero | drafted | 10507 |  |
| 15.16 | Production serving stack and reliability | drafted | 13403 |  |
| 15.17 | Lab: serve and benchmark on GKE and Nebius | drafted | 9440 |  |
| 16.1 | MLOps foundations and lifecycle | drafted | 12470 | Tier 1 (job- and interview-critical). Validator: 12/12 PASS. Lab: pipeline_lab.py (158/0). Ledger: planning/ledgers/16-01.md. Coverage: planning/coverage/chapters/16-01.md. Lab untested. |
| 16.2 | Data versioning and experiment tracking: DVC, MLflow, Weights and Biases | drafted | 8641 | Validator: 12/12 PASS. Lab: pipeline_lab.py (158/0). Ledger: planning/ledgers/16-02.md. Coverage: planning/coverage/chapters/16-02.md. Lab untested. |
| 16.3 | Data pipelines and feature stores | drafted | 9993 | Validator: 12/12 PASS. Lab: pipeline_lab.py (158/0). Ledger: planning/ledgers/16-03.md. Coverage: planning/coverage/chapters/16-03.md. Lab untested. |
| 16.4 | Pipeline orchestration: Kubeflow Pipelines, Argo, Flyte, Airflow | drafted | 7063 | Validator: 12/12 PASS. Lab: pipeline_lab.py (158/0). Ledger: planning/ledgers/16-04.md. Coverage: planning/coverage/chapters/16-04.md. Lab untested. |
| 16.5 | Distributed compute for ML: Ray, KubeRay, Training Operator and Katib | drafted | 6513 | Validator: 12/12 PASS. Lab: pipeline_lab.py (158/0). Ledger: planning/ledgers/16-05.md. Coverage: planning/coverage/chapters/16-05.md. Lab untested. |
| 16.6 | Model registry, CI/CD and GitOps for models | drafted | 7645 | Tier 1. Validator: 12/12 PASS. Lab: pipeline_lab.py (158/0). Ledger: planning/ledgers/16-06.md. Coverage: planning/coverage/chapters/16-06.md. Lab untested. |
| 16.7 | Model serving platforms: KServe, Seldon and BentoML | drafted | 6359 | Tier 1. Validator: 12/12 PASS. Lab: pipeline_lab.py (158/0). Ledger: planning/ledgers/16-07.md. Coverage: planning/coverage/chapters/16-07.md. Lab untested. |
| 16.8 | LLMOps: RAG, vector databases and agents | drafted | 5975 | Tier 1. Validator: 12/12 PASS. Lab: pipeline_lab.py (158/0). Ledger: planning/ledgers/16-08.md. Coverage: planning/coverage/chapters/16-08.md. Lab untested. |
| 16.9 | LLM evaluation and guardrails | drafted | 6581 | Tier 1. Validator: 12/12 PASS. Lab: pipeline_lab.py (158/0). Ledger: planning/ledgers/16-09.md. Coverage: planning/coverage/chapters/16-09.md. Lab untested. |
| 16.10 | Monitoring, drift and continual learning | drafted | 6449 | Validator: 12/12 PASS. Lab: pipeline_lab.py (158/0). Ledger: planning/ledgers/16-10.md. Coverage: planning/coverage/chapters/16-10.md. Lab untested. |
| 16.14 | Platform design: multi-tenant AI factory, quotas and chargeback | drafted | 6135 | Tier 1. Validator: 12/12 PASS. Lab: pipeline_lab.py (158/0). Ledger: planning/ledgers/16-14.md. Coverage: planning/coverage/chapters/16-14.md. Lab untested. |
| 16.15 | Lab: end-to-end MLOps on GKE | drafted | 5408 | Tier 1 (capstone). Validator: 12/12 PASS. Lab: pipeline_lab.py (158/0). Ledger: planning/ledgers/16-15.md. Coverage: planning/coverage/chapters/16-15.md. Lab untested. |
| 17.9 | The AI systems performance checklist (master) | drafted | 6409 | Tier 1 (master reference). Validator: 12/12 PASS. Lab: operations_lab.py (168/0). Ledger: planning/ledgers/17-09.md. Coverage: planning/coverage/chapters/17-09.md. Lab untested. |
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
| 6.22 | Provisioning with PXE, iPXE, DHCP, TFTP and image management | reviewed | 5609 | `gen_provision_lab.py` (3/3 pass), `SCL 23-26`, `VL10 ch1,3` |
| 7.1 | BMCs, IPMI and out-of-band management | reviewed | 7338 | `oob_cred_lab.py` (3/3 pass), `RF-S`, `SCL 10`, `V5 ch3`, `VL10 ch1` |
| 7.2 | Redfish concepts: service root, resources, collections, OData | reviewed | 5666 | `crawl_concepts_lab.py` (3/3 pass), `RF-S 5,6,9,12`, `RF-G` |
| 7.3 | The Redfish protocol: HTTP methods, headers, status codes, query parameters | reviewed | 5731 | `protocol_lab.py` (36/36 pass), `RF-S 6,7,8` |
| 7.4 | Redfish authentication, sessions and security | reviewed | 5469 | `auth_lab.py` (44/44 pass), `RF-S 13`, `RF-G` |
| 7.5 | Redfish actions, tasks, events and subscriptions | reviewed | 5236 | `actions_lab.py` (34/34 pass), `RF-S 7.11,12`, `RF-G` |
| 7.6 | The Redfish schema: reading CSDL, JSON schema and the resource guide | reviewed | 5133 | `schema_lab.py` (11/11 pass), `RF-SC`, `RF-G`, `RF-S 9,11` |
| 7.7 | Systems, Chassis and Managers: the core resource model | reviewed | 5067 | `model_inventory_lab.py` (3/3 pass), `RF-G`, `RF-S 9.11` |
| 7.8 | Power, thermal, sensors and environment | reviewed | 5029 | `sensors_lab.py` pass, `RF-G` |
| 7.9 | Storage, network adapters and PCIe devices | reviewed | 5060 | `hardware_lab.py` pass, `RF-G` |
| 7.10 | Firmware inventory and the UpdateService | reviewed | 5415 | `firmware_lab.py` pass, `RF-G`, `BCM 14.5`, `VL10 ch16` |
| 7.11 | Log services, event logs and diagnostics | reviewed | 5025 | `logs_lab.py` pass, `RF-G` |
| 7.12 | Automating Redfish with Python, Ansible and Go | reviewed | 5018 | `fleet_lab.py` (14/14 pass), `RF-S`, `AUR` |
| 7.13 | Redfish on NVIDIA DGX and HGX: BMC, GPU baseboard and management | reviewed | 5173 | `dgx_record_lab.py` (3/3 pass), `V5 ch3`, `V6`, `SPGB300`, `BCM` |
| 7.14 | Fleet-scale hardware management and node lifecycle automation | reviewed | 5066 | `lifecycle_lab.py` (24/24 pass), `BCM 14.5`, `VL10 ch1` |
| 7.15 | BMC security hardening and attestation | reviewed | 5292 | `hardening_lab.py` (28/28 pass), `V18 ch2`, `RF-S 13`, `RF-G` |
| 8.1 | BCM architecture and concepts | reviewed | 5033 | `bcm_model_lab.py` (35/35 pass), `BCM-A 1,2,8.1`, `VL10 ch2` |
| 8.2 | Planning and installing BCM | reviewed | 5176 | `install_lab.py` (32/32 pass), `BCM-I` |
| 8.3 | Cluster configuration: networks, nodes and categories | reviewed | 6418 | `netconf_lab.py` (67/67 pass), `BCM-A 3`, `VL10 ch2` |
| 8.4 | Node provisioning: images, kernels, categories and the PXE flow | reviewed | 6650 | `provision_lab.py` (82/82 pass), `BCM-A 5,9`, `VL10 ch2` |
| 8.5 | cmsh and Base View: administering the cluster | reviewed | 5016 | `cmsh_lab.py` (55/55 pass), `BCM-A 2` |
| 8.6 | Users, authentication and security in BCM | reviewed | 5039 | `security_lab.py` (51/51 pass), `BCM-A 2.3,6` |
| 8.7 | Power, BMC and hardware management in BCM | reviewed | 5142 | `hardware_lab.py` (45/45 pass), `BCM-A 3.7,4,14.5,14.7` |
| 8.8 | Workload managers under BCM: Slurm setup | reviewed | 5017 | `slurm_lab.py` (60/60 pass), `BCM-A 7` |
| 8.9 | Kubernetes under BCM: deployment and GPU enablement | reviewed | 6292 | `k8s_lab.py` (64/64 pass), `BCM-C 4,5,6,7,8` |
| 8.10 | Containerization in BCM: Docker, Apptainer and enroot | reviewed | 5086 | `containers_lab.py` (35/35 pass), `BCM-C 2,3`, `SCL 16` |
| 8.11 | Monitoring, health checks and alerts in BCM | reviewed | 5171 | `monitoring_lab.py` (46/46 pass), `BCM-A 10,G` |
| 8.12 | High availability and head-node failover | reviewed | 5188 | `ha_lab.py` (50/50 pass), `BCM-A 15`, `VL10 ch13` |
| 8.13 | Day-2 operations: updates, scaling, hardware replacement, disaster recovery | reviewed | 5134 | `ops_lab.py` (45/45 pass), `BCM-A 9,14`, `VL10 ch13` |
| 8.14 | Air-gapped installation and upgrades | reviewed | 5104 | `airgap_lab.py` (34/34 pass), `BCM-C A,B,C` |
| 8.15 | BCM in an AI factory: DGX SuperPOD integration | reviewed | 5124 | `superpod_lab.py` (29/29 pass), `SPGB300`, `SPB200`, `BCM-A` |
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
| 16.12 | NVIDIA enterprise stack: AI Enterprise, NGC and licensing | drafted | 5381 | Tier 1b (NVIDIA-specific). Validator: 12/12 PASS. Lab: pipeline_lab.py (158/0). Ledger: planning/ledgers/16-12.md. Coverage: planning/coverage/chapters/16-12.md. Lab untested. |

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
| 2.18 | Data center topologies: Clos, leaf-spine, oversubscription, failure domains | drafted | 8315 |  |
| 2.19 | Queuing, QoS, ECN, PFC and DCB basics | drafted | 7945 |  |
| 2.20 | Load balancing: L4, L7, ECMP hashing and proxies | drafted | 7749 |  |
| 2.21 | Network security: firewalls, TLS and zero trust | drafted | 7593 |  |
| 2.28 | Network automation fundamentals: APIs, YANG, NETCONF, gNMI, SDN, templates | drafted | 7963 |  |
| 2.29 | Network automation in practice: Ansible, Nornir and CI/CD for networks | drafted | 7805 |  |
| 2.31 | Network monitoring and telemetry | drafted | 7440 |  |
| 3.1 | Python core: types, control flow, functions | drafted | 9295 |  |
| 3.2 | Modules, packages, virtual environments and packaging | drafted | 11314 |  |
| 3.3 | Idiomatic Python: the data model, comprehensions, generators | drafted | 10864 |  |
| 3.4 | Classes, dataclasses, typing and protocols | drafted | 9999 |  |
| 3.5 | Errors, files, text and bytes, subprocess and system scripting | drafted | 9087 |  |
| 3.6 | Concurrency: threads, processes and asyncio | drafted | 8154 |  |
| 3.7 | Building APIs and microservices with FastAPI | drafted | 7936 |  |
| 3.8 | Building CLIs, agents and exporters (Prometheus exporters, Redfish clients) | drafted | 7994 |  |
| 3.9 | Testing, quality and CI for Python tooling | drafted | 7051 |  |
| 3.10 | Python for data and ML infrastructure: NumPy, pandas, PyTorch essentials | drafted | 6787 |  |
| 3.11 | Python under the hood: decorators, descriptors and metaprogramming (how frameworks work) | drafted | 7884 |  |
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
| 6.1 | What a supercomputer is: TOP500, Linpack, HPC versus AI factory | drafted | 9505 | `flops_lab.py` (3/3 pass); `validate_chapter.py` 12/12 PASS |
| 6.2 | Cluster anatomy: head, login, compute, storage and management nodes | drafted | 9848 | `cluster_anatomy_lab.py` (3/3 pass); `loss_check.py` PASS; `validate_chapter.py` 12/12 PASS |
| 6.3 | Parallel computing concepts: Amdahl, scaling, shared memory versus message passing | drafted | 8371 | `scaling_lab.py` (3/3 pass); `validate_chapter.py` 12/12 PASS |
| 6.4 | MPI in practice: Open MPI, ranks, collectives and tuning | drafted | 8186 | `mpi_tuning_lab.py` (3/3 pass); `validate_chapter.py` 12/12 PASS |
| 6.6 | Environment modules, Spack and EasyBuild | drafted | 5846 | `modules_spack_lab.py` (3/3 pass); `validate_chapter.py` 12/12 PASS |
| 6.18 | Parallel storage concepts and the limits of NFS | reviewed | 5912 | `iomix_lab.py` (3/3 pass), `SCL 9`, `SCL 28` |
| 6.19 | Lustre architecture and operation | reviewed | 5745 | `lustre_stripe_lab.py` (3/3 pass), `SCL 9`, `SCL 28`, `V15 ch5` |
| 6.20 | BeeGFS, GPFS, WekaFS and VAST | reviewed | 5347 | `parallel_fs_compare_lab.py` (3/3 pass), `SCL 9`, `V15` |
| 6.21 | Parallel I/O and checkpoint patterns | reviewed | 6217 | `ckpt_atomic_lab.py` (3/3 pass), `ASP 5`, `PHPC 16`, `V15` |
| 6.23 | xCAT, Warewulf and cluster managers compared with BCM | reviewed | 5541 | `cluster_mgr_lab.py` (3/3 pass), `SCL 26`, `SCL 28` |
| 6.24 | Users, LDAP, SSSD, quotas and accounting at scale | reviewed | 6221 | `identity_gen_lab.py` (3/3 pass), `SCL 11, 12, 28` |
| 6.26 | Cluster monitoring and health at scale | reviewed | 6459 | `slurm_exporter_lab.py` (3/3 pass), `SCL 19` |
| 6.28 | HPC benchmarking: HPL, HPCG, IOR, OSU and NCCL tests | reviewed | 7648 | `bench_stats_lab.py` (3/3 pass), `SP 12`, `ASP 5` |
| 6.29 | Containers and reproducibility in HPC: Apptainer and enroot | reviewed | 5382 | `container_lint_lab.py` (3/3 pass), `SCL 16` |
| 6.30 | Facility basics: power, cooling, racks and liquid cooling | reviewed | 6693 | `facility_calc_lab.py` (3/3 pass), `ADC 5`, `SCL 28`, `SPB200` |
| 6.31 | Capstone: build and operate a small Slurm GPU cluster | reviewed | 7870 | `capstone_demo_lab.py` (3/3 pass), `volume-10/00c-slurm-bcm-interview-lab.md` |
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
| 14.1 | ML and deep learning fundamentals for infrastructure engineers | drafted | 15438 |  |
| 14.2 | Transformers and LLM architecture | drafted | 15288 |  |
| 14.3 | Training memory and compute anatomy | drafted | 12788 |  |
| 14.4 | Data parallelism and DDP | drafted | 11778 |  |
| 14.5 | FSDP and parameter sharding | drafted | 12585 |  |
| 14.6 | DeepSpeed and ZeRO | drafted | 12654 |  |
| 14.7 | Tensor, pipeline and expert parallelism; Megatron | drafted | 13472 |  |
| 14.8 | PyTorch performance: profiling, tuning and scaling | drafted | 11038 |  |
| 14.9 | PyTorch compilers and kernels: torch.compile | drafted | 10758 |  |
| 14.10 | Multi-node training architecture | drafted | 11722 |  |
| 14.11 | Checkpointing, fault tolerance and elastic training | drafted | 9735 |  |
| 14.12 | Training performance engineering and troubleshooting | drafted | 10771 |  |
| 14.16 | NeMo framework and customisation | drafted | 9151 |  |
| 15.18 | Inference cost, capacity and cost per token | drafted | 14117 |  |
| 16.11 | Cloud MLOps platforms: Vertex AI, SageMaker and Azure ML | drafted | 5819 | Tier 2. Validator: 12/12 PASS. Lab: pipeline_lab.py (158/0). Ledger: planning/ledgers/16-11.md. Coverage: planning/coverage/chapters/16-11.md. Lab untested. |
| 16.13 | Governance, privacy and compliance for ML platforms | drafted | 6226 | Tier 2. Validator: 12/12 PASS. Lab: pipeline_lab.py (158/0). Ledger: planning/ledgers/16-13.md. Coverage: planning/coverage/chapters/16-13.md. Lab untested. |
| 17.1 | Observability foundations: metrics, logs and traces | drafted | 5851 | Tier 2. Validator: 12/12 PASS. Lab: operations_lab.py (168/0). Ledger: planning/ledgers/17-01.md. Coverage: planning/coverage/chapters/17-01.md. Lab untested. |
| 17.2 | Prometheus and Grafana | drafted | 5033 | Tier 2. Validator: 12/12 PASS. Lab: operations_lab.py (168/0). Ledger: planning/ledgers/17-02.md. Coverage: planning/coverage/chapters/17-02.md. Lab untested. |
| 17.3 | Logging with Loki and tracing with OpenTelemetry | drafted | 4991 | Tier 2. Validator: 12/12 PASS. Lab: operations_lab.py (168/0). Ledger: planning/ledgers/17-03.md. Coverage: planning/coverage/chapters/17-03.md. Lab untested. |
| 17.4 | DCGM exporter and interpreting GPU metrics | drafted | 4961 | Tier 2. Validator: 12/12 PASS. Lab: operations_lab.py (168/0). Ledger: planning/ledgers/17-04.md. Coverage: planning/coverage/chapters/17-04.md. Lab untested. |
| 17.5 | Distributed observability and profiling | drafted | 5293 | Tier 2. Validator: 12/12 PASS. Lab: operations_lab.py (168/0). Ledger: planning/ledgers/17-05.md. Coverage: planning/coverage/chapters/17-05.md. Lab untested. |
| 17.6 | Alerting, SLOs and health checks for GPU clusters | drafted | 5220 | Tier 2. Validator: 12/12 PASS. Lab: operations_lab.py (168/0). Ledger: planning/ledgers/17-06.md. Coverage: planning/coverage/chapters/17-06.md. Lab untested. |
| 17.7 | Failure modes and detection | drafted | 6211 | Tier 2. Validator: 12/12 PASS. Lab: operations_lab.py (168/0). Ledger: planning/ledgers/17-07.md. Coverage: planning/coverage/chapters/17-07.md. Lab untested. |
| 17.8 | Performance engineering methodology and decision trees | drafted | 5663 | Tier 2. Validator: 12/12 PASS. Lab: operations_lab.py (168/0). Ledger: planning/ledgers/17-08.md. Coverage: planning/coverage/chapters/17-08.md. Lab untested. |
| 17.10 | Cluster lifecycle, upgrades and change management | drafted | 5399 | Tier 2. Validator: 12/12 PASS. Lab: operations_lab.py (168/0). Ledger: planning/ledgers/17-10.md. Coverage: planning/coverage/chapters/17-10.md. Lab untested. |
| 17.11 | Incident response and game days | drafted | 5711 | Tier 2. Validator: 12/12 PASS. Lab: operations_lab.py (168/0). Ledger: planning/ledgers/17-11.md. Coverage: planning/coverage/chapters/17-11.md. Lab untested. |
| 17.12 | Capacity planning and cost optimisation | drafted | 4772 | Tier 2. Validator: 12/12 PASS. Lab: operations_lab.py (168/0). Ledger: planning/ledgers/17-12.md. Coverage: planning/coverage/chapters/17-12.md. Lab untested. |
| 17.13 | Reliability engineering for AI infrastructure | drafted | 4684 | Tier 2. Validator: 12/12 PASS. Lab: operations_lab.py (168/0). Ledger: planning/ledgers/17-13.md. Coverage: planning/coverage/chapters/17-13.md. Lab untested. |
| 17.14 | Disaster recovery and data resilience | drafted | 4914 | Tier 2. Validator: 12/12 PASS. Lab: operations_lab.py (168/0). Ledger: planning/ledgers/17-14.md. Coverage: planning/coverage/chapters/17-14.md. Lab untested. |
| 17.15 | On-call runbooks | drafted | 5040 | Tier 2. Validator: 12/12 PASS. Lab: operations_lab.py (168/0). Ledger: planning/ledgers/17-15.md. Coverage: planning/coverage/chapters/17-15.md. Lab untested. |
| 17.16 | AI-assisted operations and scaling toward very large clusters | drafted | 5180 | Tier 2. Validator: 12/12 PASS. Lab: operations_lab.py (168/0). Ledger: planning/ledgers/17-16.md. Coverage: planning/coverage/chapters/17-16.md. Lab untested. |
| 18.1 | Threat modeling for AI infrastructure | drafted | 5756 | Tier 2. Validator: 12/12 PASS. Lab: security_lab.py (73/0). Ledger: planning/ledgers/18-01.md. Coverage: planning/coverage/chapters/18-01.md. Lab untested. |
| 18.2 | Hardware and firmware trust | drafted | 4962 | Tier 2. Validator: 12/12 PASS. Lab: security_lab.py (73/0). Ledger: planning/ledgers/18-02.md. Coverage: planning/coverage/chapters/18-02.md. Lab untested. |
| 18.3 | Containers and the software supply chain | drafted | 4523 | Tier 2. Validator: 12/12 PASS. Lab: security_lab.py (73/0). Ledger: planning/ledgers/18-03.md. Coverage: planning/coverage/chapters/18-03.md. Lab untested. |
| 18.4 | Kubernetes access control and pod security | drafted | 4520 | Tier 2. Validator: 12/12 PASS. Lab: security_lab.py (73/0). Ledger: planning/ledgers/18-04.md. Coverage: planning/coverage/chapters/18-04.md. Lab untested. |
| 18.5 | GPU sharing security, DMA, IOMMU and SR-IOV | drafted | 4739 | Tier 2. Validator: 12/12 PASS. Lab: security_lab.py (73/0). Ledger: planning/ledgers/18-05.md. Coverage: planning/coverage/chapters/18-05.md. Lab untested. |
| 18.6 | BlueField, DOCA and confidential computing | drafted | 4544 | Tier 2. Validator: 12/12 PASS. Lab: security_lab.py (73/0). Ledger: planning/ledgers/18-06.md. Coverage: planning/coverage/chapters/18-06.md. Lab untested. |
| 18.7 | Data and model protection, audit and compliance | drafted | 4686 | Tier 2. Validator: 12/12 PASS. Lab: security_lab.py (73/0). Ledger: planning/ledgers/18-07.md. Coverage: planning/coverage/chapters/18-07.md. Lab untested. |
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
| 6.5 | OpenMP, compilers and optimisation flags | drafted | 7252 | `omp_compilers_lab.py` (3/3 pass); `validate_chapter.py` 12/12 PASS |
| 6.17 | Other schedulers: PBS, Torque, LSF and Flux | reviewed | 5211 | `pbs2slurm_lab.py` (3/3 pass), `loss_check.py` PASS, `SCL 14` |
| 6.25 | Remote access, bastions, Open OnDemand and user environments | reviewed | 5859 | `sshd_audit_lab.py` (3/3 pass), `SCL 18`, `SCL 27` |
| 6.27 | Backup and data protection | reviewed | 5986 | `backup_protection_lab.py` (3/3 pass), `SCL 20` (0% missing) |
| 19.10 | Customer workshops and the consulting method | scaffold |  |  |
