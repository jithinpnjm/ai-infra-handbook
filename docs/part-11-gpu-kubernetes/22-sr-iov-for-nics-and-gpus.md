---
id: "c11-22"
title: "11.22 SR-IOV for NICs and GPUs"
sidebar_label: "11.22 SR-IOV for NICs and GPUs"
sidebar_position: 22
description: "How Single-Root I/O Virtualization slices ConnectX RDMA NICs and NVIDIA GPUs into hardware-isolated Virtual Functions, and how to secure and forensically operate SR-IOV AI clusters."
status: "drafted"
tier: "1"
level: "A"
lab_venue: "GCP / GKE"
---

# 11.22 SR-IOV for NICs and GPUs

| | |
|---|---|
| Level | Advanced |
| Priority tier | 1 |
| Lab venue | GCP / GKE and local Python simulation lab |
| Part | Part 11: GPUs on Kubernetes, scheduling and virtualization |
| Coverage file | `planning/coverage/chapters/11-22.md` |

## Why this matters for AI infrastructure

Suppose your training job runs slowly, and its network traffic passes through a software proxy in the hypervisor. Routing high-speed guest network or storage traffic that way adds severe latency and CPU overhead. Every packet or block operation takes five to ten extra control and data steps through the host proxy. Giving the whole PCIe card to one virtual machine removes that proxy and fixes the speed problem. It creates a different problem: no other tenant on that server can share the ConnectX-7 network card or the H100 GPU.

Platform teams need both bare-metal passthrough speed and hardware sharing on the same physical card. The PCIe specification handles this trade-off with Single-Root I/O Virtualization, known as SR-IOV. One SR-IOV card can present dozens of independent, hardware-sliced Virtual Functions on the PCIe bus, and each one can be handed to a different tenant.

- **SR-IOV for NICs on ConnectX-6, ConnectX-7, and BlueField-3.** The physical network card acts as a Physical Function and slices itself in silicon into dozens of independent Virtual Functions. Each Virtual Function gets its own PCIe Bus-Device-Function address, hardware transmit and receive queues, and RDMA doorbells. A Pod or virtual machine attaches directly to its own Virtual Function, bypassing the hypervisor and host network stack to reach line-rate GPUDirect RDMA.
- **SR-IOV for GPUs on Ampere A100, Hopper H100, Ada L40S, and Blackwell B200.** Starting with the Ampere architecture, these NVIDIA data-center GPUs also implement hardware SR-IOV. When you deploy NVIDIA vGPU or pass a MIG instance into a KubeVirt or KVM guest VM, the GPU exposes each slice as a dedicated PCIe SR-IOV Virtual Function.

SR-IOV also brings three problems that often catch operations teams off guard.

1. **Keep the IOMMU on.** A Virtual Function is a slice of the card. Without an IOMMU, that slice can still reach any address in host memory by direct memory access. The motherboard IOMMU limits each Virtual Function to its own tenant's memory through per-VF DMA remapping tables.
2. An SRE who runs `iostat` on the host sees almost nothing. Virtual Functions talk straight to PCIe hardware rings, so host block and network tools no longer see the guest traffic.
3. Suppose an attacker compromises a notebook pod or flashes rogue firmware onto a network card or GPU. Deleting the pod or rebooting the host destroys the evidence held in RAM and VRAM. Without that evidence the team may never find the hole the attacker used, and the attacker can return.

The baseline below gathers the identifiers and kernel setting used throughout this chapter.

```text
SR-IOV Reference Baseline:
- Hypervisor software I/O proxy penalty: 5 to 10 extra steps ([Qumranet 06], [Xen 19])
- ConnectX-7 400G NIC Physical Function BDF: 0000:4b:00.0 (VFs: 0000:4b:00.1..N)
- NVIDIA H100 80 GB GPU Physical Function BDF: 0000:8a:00.0 (/usr/lib/nvidia/sriov-manage -e ALL)
- Host IOMMU kernel parameter: intel_iommu=on (Intel VT-d / AMD-Vi DMAR tables)
```

Treat an active IOMMU as a requirement on every SR-IOV node, because the first item above depends on it.

## Prerequisites and outcomes

### Prerequisites

Before you start, finish Chapter 11.10 on Multus and device plugins, Chapter 11.11 on Network Operator, and Chapter 11.21 on PCIe, IOMMU, and VFIO passthrough. You should also be comfortable reading PCIe Bus-Device-Function notation and writing Kubernetes `NetworkPolicy` manifests.

### Outcomes

The outcomes below describe what you should be able to do when you finish this chapter.

- Explain the Physical Function and Virtual Function architecture of SR-IOV and MR-IOV. Then compare SR-IOV for NICs with MIG for GPUs, and configure Virtual Functions for both ConnectX RDMA NICs and NVIDIA GPUs.
- Diagnose SR-IOV performance and observability with Brendan Gregg's methodology from *Systems Performance* Chapter 11. Explain why SR-IOV bypasses host `iostat`, how Calico compares with Cilium eBPF and Hubble, and how Linux cgroups and qdiscs shape traffic.
- Architect the five-layer Zero-Trust AI defense-in-depth stack across supply chain, Kubernetes, network and BlueField DPU, hardware and IOMMU, and confidential computing. Then audit clusters against the fourteen-item production security checklist.
- Execute the six-step security incident response and forensic containment protocol on a breached GPU and SR-IOV node without destroying volatile evidence.

Finish the three prerequisite chapters before you go on.

## Concepts: basics to intermediate to advanced

### 1. Basics: How SR-IOV works on PCIe for ConnectX NICs and NVIDIA GPUs

#### 1. Physical Functions vs Virtual Functions

Picture a standard PCIe setup without virtualization extensions. You would see just one primary PCIe function on that bus. If you bind that function to `vfio-pci` and pass it into one virtual machine, no other virtual machine on that server can touch the card. An eight-tenant node would then need eight separate physical network cards just to give every tenant direct hardware access.

Single-Root I/O Virtualization solves this inside the PCIe endpoint silicon, so one card can serve many tenants. For multi-host fabrics that span several PCIe root complexes, the companion specification is Multi-Root I/O Virtualization, known as MR-IOV. Both specifications split a physical device into two kinds of function.

- **Physical Function.** The Physical Function is the primary PCIe function that the host OS or hypervisor owns and manages exclusively. Its driver controls global hardware configuration, firmware flashing, and eSwitch steering modes such as Legacy mode or SwitchDev mode. It also creates and destroys Virtual Functions through sysfs files.
- **Virtual Functions.** Virtual Functions are lightweight, hardware-sliced PCIe functions. Each one has dedicated transmit and receive queues, DMA channels, and doorbell registers on the silicon, plus its own PCIe Bus-Device-Function Requester ID. Because that ID is distinct, the motherboard IOMMU places every Virtual Function in an isolated IOMMU group with its own DMA Remapping access table.

The diagram shows how one physical device fans out into isolated tenant paths.

```mermaid
flowchart TD
    subgraph Silicon["Physical PCIe Silicon (ConnectX-7 400G NIC or NVIDIA H100 GPU)"]
        PF["Physical Function PF (0000:4b:00.0) - Owned by Host Kernel / Hypervisor"]
        VF1["Virtual Function VF 1 (0000:4b:00.1)"]
        VF2["Virtual Function VF 2 (0000:4b:00.2)"]
        VFN["Virtual Function VF N (0000:4b:00.N)"]
        PF -->|"Hardware Slicing (sriov_numvfs / sriov-manage)"| VF1
        PF --> VF2
        PF --> VFN
    end
    VF1 -->|"Unique BDF Requester ID -> IOMMU DMAR Table 1"| T1["Tenant 1 Pod / VM (Direct DMA to Tenant 1 RAM/VRAM Only)"]
    VF2 -->|"Unique BDF Requester ID -> IOMMU DMAR Table 2"| T2["Tenant 2 Pod / VM (Direct DMA to Tenant 2 RAM/VRAM Only)"]
    VFN -->|"Unique BDF Requester ID -> IOMMU DMAR Table N"| TN["Tenant N Pod / VM (Zero Hypervisor QEMU Proxy Overhead)"]
```

#### 2. Comparing SR-IOV for NICs vs SR-IOV and MIG for GPUs

Engineers often ask how SR-IOV relates to Multi-Instance GPU, known as MIG. You may ask the same question. Both do the same kind of hardware partitioning, but on different silicon. SR-IOV splits the PCIe interface and packet queues of a network card. MIG splits the streaming multiprocessors, memory crossbars, and HBM channels of a GPU.

On Ampere A100, Hopper H100 and H200, Ada L40S, and Blackwell B200 GPUs, SR-IOV and MIG work together when virtual machines are involved. The GPU uses SR-IOV to expose isolated PCIe Virtual Functions to the hypervisor. Behind those Virtual Functions, vGPU or MIG partitions the compute and memory. The table below compares the two cases.

| Hardware Dimension | SR-IOV on ConnectX-6 / ConnectX-7 NICs | SR-IOV + MIG on NVIDIA Data-Center GPUs (`A100` / `H100` / `L40S`) |
|---|---|---|
| **What Silicon Is Sliced?** | **Network Interface Card (`NIC`)** (and NVMe storage controllers in `AWS Nitro`, `SP 11.2.2`) | **GPU PCIe Bus Interface (`SR-IOV VFs`)** + **GPU Compute/Memory Silicon (`MIG` / `vGPU`)** |
| **Host PF Management Tool** | `mlxconfig -d <bdf> set SRIOV_EN=1 NUM_OF_VFS=16` + `echo 8 > .../sriov_numvfs` (or `sriov-network-operator`) | `/usr/lib/nvidia/sriov-manage -e ALL` (enables GPU VFs) + `nvidia-smi -mig 1` / **NVIDIA Virtual GPU Manager** (`nvidia-smi vgpu`) |
| **Two GPU SR-IOV Modes** | Each VF is an independent hardware RDMA/RoCEv2 or InfiniBand virtual HCA (`mlx5_vf`) | **1. Time-Sliced vGPU over SR-IOV VF:** Multiple VFs share the GPU's SMs (`NVIDIA GRID A100-20Q`, `2000MiB / 20000MiB`, `18W / 400W`).<br/>**2. MIG-Backed vGPU over SR-IOV VF:** Each SR-IOV VF is backed by a hardware-isolated **MIG GPU Instance (`GI`)** (`1g.10gb`, `2g.20gb`, `3g.40gb`). |
| **Guest Driver & Licensing** | Standard inbox `mlx5_core` / `MLNX_OFED` VF driver (`ena`, `ixgbe`, `hv_netvsc` in cloud VMs, `SP 11.2`) | Guest VM loads the **NVIDIA Guest vGPU Driver** (must match the Host vGPU Manager compatibility matrix) and acquires an entitlement lease from the **NVIDIA License System (`NLS`)**. |

Notice that each NIC Virtual Function is an independent virtual HCA, while the GPU side offers two modes to choose from.

---

### 2. Intermediate: Operating SR-IOV in Kubernetes and Brendan Gregg's observability and CNI rules

#### 1. Exposing ConnectX NIC VFs and GPU VFs to Kubernetes Pods and KubeVirt VMs

Without automated device discovery, you would write sysfs files and move network interfaces into container namespaces by hand after every node boot. Kubernetes automates that work through the NVIDIA Network Operator and the NVIDIA GPU Operator. Workloads consume SR-IOV Virtual Functions in one of two ways, depending on whether they run as containers or as virtual machines.

1. **Container secondary RDMA networks with Multus and the SR-IOV device plugin.** The Network Operator reconciles a `SriovNetworkNodePolicy` custom resource. That resource names the target Physical Function and the number of Virtual Functions you want. The operator writes that count to `sriov_numvfs` in sysfs. When a training Pod requests an SR-IOV resource, the SR-IOV device plugin and Multus move one Virtual Function into the Pod network namespace, and they mount its InfiniBand character devices under the Linux `rdma` cgroup.
2. **Virtual machine VF passthrough with VFIO and KubeVirt.** When a tenant runs inside a KubeVirt virtual machine or a Kata container, the policy binds each Virtual Function to the `vfio-pci` kernel driver instead of a host network driver. For GPUs, running `/usr/lib/nvidia/sriov-manage -e ALL` on the host creates the GPU Virtual Functions. The hypervisor can then pass a time-sliced vGPU or a MIG-backed vGPU straight into the guest virtual machine.

```text
Kubernetes SR-IOV Resource & Cgroup Summary:
- SriovNetworkNodePolicy fields: deviceType: netdevice (or vfio-pci), isRdma: true, numVfs: 8
- Sysfs activation path: /sys/class/net/<pf>/device/sriov_numvfs (bounded by sriov_totalvfs)
- Pod resource request examples: nvidia.com/hostdev: 1 or openshift.io/mlnx_connectx7: 1
- Pod secondary interface & device mount: net1 + /dev/infiniband/uverbs* (bounded by Table 11.2 rdma cgroup)
```

If a Virtual Function count does not take, check the sysfs path first. The `sriov_totalvfs` value sets the ceiling.

#### 2. The SR-IOV Observability Blind Spot and Kubernetes Network Controls

Turning on SR-IOV fixes network throughput, but it breaks standard host-level monitoring. Picture an SRE who logs into a worker node during a large distributed training run and runs `iostat` or `sar`. That SRE sees almost no disk or network activity on the host. Brendan Gregg explains this blind spot, along with two container networking rules, in *Systems Performance* Chapter 11.

1. **Why SR-IOV makes traffic invisible to host `iostat` and `sar`.** In a traditional virtualized system without SR-IOV, every guest packet or storage command goes through the host kernel and the hypervisor proxy. With SR-IOV or VFIO passthrough, the guest driver talks to the hardware rings directly through DMA and skips the host kernel. So you must query hardware Performance Monitoring Counters, physical NIC port counters, or DCGM telemetry instead. Alternatively, you can run eBPF tools inside the guest kernel.
2. **Primary CNI overhead between Calico iptables and Cilium eBPF.** While SR-IOV secondary networks carry east-west NCCL RDMA traffic, the primary container network on `eth0` carries control-plane and inference API traffic. Calico in iptables mode and the standard `kube-proxy` both evaluate long sequential lists of netfilter rules. That sequential walk adds CPU latency once a cluster grows to thousands of Kubernetes Services. Cilium replaces iptables and `kube-proxy` with in-kernel eBPF programs attached at the XDP, traffic control, and cgroup hooks, and it pairs with Cilium Hubble for flow visibility.
3. **Software bandwidth shaping with cgroups and Token Bucket Filter qdiscs.** When containers share a non-SR-IOV host interface, Linux prioritizes and throttles their traffic with the `net_prio` and `net_cls` cgroups. Linux also offers more than fifty queueing disciplines. Kubernetes enforces pod bandwidth annotations by attaching a Token Bucket Filter qdisc to the container's virtual interface.

| Observability / Control Dimension | Exact Drivers, Counters, & Kernel Mechanisms (`Systems Performance` Ch. 11) |
|---|---|
| **SR-IOV / Hardware-Virtualized Drivers (`SP 11.2`)** | `ixgbe` (Intel `10GbE`), `ena` (AWS Elastic Network Adapter in `AWS Nitro`), `hv_netvsc` (Microsoft Hyper-V), and `nvme` (NVMe storage controllers) |
| **SR-IOV Observability Blind Spot (`SP 11.2.4`)** | Bypassing `QEMU` / `dom0` makes I/O invisible to host `iostat(1)` and `sar -n DEV`; use NIC `port_xmit_data`, `port_rcv_data`, `PortXmitWait`, hardware `PMCs`, `DCGM-Exporter`, or guest eBPF (`biosnoop(8)`, `tcplife`) |
| **Primary CNI: Calico vs Cilium (`SP 11.1.6` & `11.3.2`)** | `Calico` (`netfilter` / `iptables`) + `kube-proxy` sequential rule overhead vs `Cilium` (`[Borkmann 19]`, `[Borkmann 20]`, `[Cilium 20a]`) in-kernel `eBPF` (`BPF` at `XDP`, `tc` `qdisc`, `cgroup`) + `Cilium Hubble` (`[Cilium 19]`) |
| **Linux Traffic Control & Cgroups (`SP 11.3.1` & `11.3.3`)** | `rdma` cgroup (`Table 11.2`), `net_prio` (`SO_PRIORITY`), `net_cls` class ID tagging, and `> 50` Linux `qdiscs` where `tbf` (Token Bucket Filter, `[CNI 18]`) implements `kubernetes.io/ingress-bandwidth` and `kubernetes.io/egress-bandwidth` |

Read the table as a list of what you should monitor, since host tools will not show SR-IOV traffic.

---

### 3. Advanced: Zero-trust AI defense-in-depth and forensic incident response on SR-IOV and GPU nodes

#### 1. The 5-Layer Zero-Trust AI Defense-in-Depth Stack

When tenants share network cards and GPUs through SR-IOV, relying on one perimeter firewall is a recipe for a cluster-wide breach. Say a researcher downloads a poisoned model checkpoint from a public hub. That payload then runs inside the cluster perimeter right away. Without layered hardware and software isolation, an attacker can pivot from a compromised container into host memory or neighboring tenant workloads.

A zero-trust AI architecture assumes that any single layer can be breached. It therefore surrounds workloads with five concentric defense rings. Even if a malicious model gets past the supply-chain checks and spawns a reverse shell, Kubernetes policies, DPU firewalls, motherboard IOMMU tables, and hardware memory encryption contain the blast radius.

```mermaid
flowchart TD
    L1["1. Supply Chain Defense: Trivy CVE Scan + Cosign Image Signatures + .safetensors (Block Malicious Pickle)"] -->|"If poisoned dependency enters pod"| L2["2. Kubernetes Defense: Least-Privilege RBAC + Locked gpu-operator NS + Pod Security Admission (Restricted, Non-Root)"]
    L2 -->|"If attacker gets reverse shell in container"| L3["3. Network Defense: Default-Deny NetworkPolicies + BlueField DPU Isolated ARM Firewall (No Host Shared Fate)"]
    L3 -->|"If attacker attempts rogue PCIe/VF memory read"| L4["4. Hardware Defense: UEFI Secure Boot + Signed GPU/NIC Drivers & Firmware + Motherboard IOMMU (DMAR Blocks DMA)"]
    L4 -->|"If attacker dumps physical RAM or VRAM"| L5["5. Data Defense: NVIDIA Hopper Confidential Computing + CPU TEE (AMD SEV-SNP / Intel TDX) -> Reads Only Ciphertext"]
```

Each of the five layers enforces a specific hardware or software boundary on an SR-IOV and GPU worker node. You can check each boundary on its own.

1. **Supply Chain Defense at Layer 1.** Ban mutable image tags and reject Python pickle model checkpoints. A pickle file can run arbitrary shell commands while the model loads. Scan every container image with Trivy and sign approved digests with Cosign. Enforce signature checks in a Kubernetes Admission Controller, and store model weights in the non-executable `.safetensors` format.
2. **Kubernetes Defense at Layer 2.** Lock down the operator namespaces with least-privilege RBAC, and enforce Pod Security Admission in Restricted mode across all tenant namespaces. That keeps containers from running as root or gaining the privileged access needed to modify sysfs SR-IOV files or host kernel drivers.
3. **Network and DPU Micro-Segmentation at Layer 3.** Host-based software firewalls suffer from the shared-fate problem. If an attacker compromises the x86 host kernel, they can simply flush the local iptables rules. Offloading network policy and encryption to an NVIDIA BlueField DPU moves the firewall onto physically isolated ARM cores. That hardware boundary blocks lateral movement even when the host OS is compromised.
4. **Hardware Trust and IOMMU at Layer 4.** Enforce UEFI Secure Boot, signed kernel modules, and vendor-signed GPU and ConnectX NIC firmware on every server. Keep the motherboard IOMMU enabled. Its per-VF DMA Remapping tables then block any rogue Virtual Function from reading host management RAM.
5. **Confidential Computing at Layer 5.** Suppose an attacker, or a malicious administrator, dumps physical RAM or snoops the PCIe bus. NVIDIA Hopper Confidential Computing still protects the workload. Paired with a CPU Trusted Execution Environment, it encrypts GPU VRAM and PCIe bounce buffers in hardware, so any memory dump captures only unusable ciphertext.

Audit each layer on its own, since the design assumes any one of them can be breached.

#### 2. Security Incident Response: Isolate, Do Not Terminate

Suppose your intrusion detection system or DCGM telemetry alerts that a notebook pod on a GPU node is scanning internal corporate SSH ports, or running an unauthorized crypto-miner. A flat power trace at maximum TDP on a node that normally serves bursty inference suggests unauthorized mining. What you do in the first five minutes decides whether you keep the evidence you need to close the hole.

- **Deleting the pod or rebooting the node.** In a postmortem from the author's field notes, a platform engineer saw a notebook pod scanning internal port 22 and immediately ran `kubectl delete pod` to stop the alert. Deleting the pod wiped volatile system RAM and GPU VRAM, which destroyed the bash history, active network sockets, and in-memory payload of the attacker. With the forensic evidence gone, the team never found the unpatched Jupyter CVE. One week later, the attacker came back through the same hole and encrypted the cluster with ransomware.
- **The six-step containment protocol.** On a GPU cluster, isolate the pod instead of terminating it. First cordon the node and cage the pod with a deny-all network policy. Then capture RAM and VRAM. After that, patch the root CVE across the cluster, wipe the hardware and reflash the firmware, and only then rotate credentials.

| Step | Phase | Exact Action / Command | Why This Ordering Is Mandatory |
|---|---|---|---|
| **1** | **Cordon the Crime Scene** | `kubectl cordon gpu-node-42` | Prevents the scheduler from placing new clean pods onto the compromised node while keeping existing pods alive. |
| **2** | **Network Quarantine (*"Isolate, Don't Terminate"*)** | Apply a **Deny-All Quarantine `NetworkPolicy`** (or ToR switch / DPU ACL) dropping all ingress/egress except the forensic workstation IP. | Traps the attacker inside the running container (`air-gapped cage`) without clearing volatile RAM or GPU VRAM. |
| **3** | **Capture Volatile Forensics** | Snapshot VM/host RAM + GPU VRAM (`kubectl debug`), inspect **Kubernetes API Audit Logs** (compromised `ServiceAccount`?), verify **container image digest** vs registry, and review **DCGM power/thermal traces**. | Identifies the exact entry vector (e.g., unpatched PyTorch/Jupyter CVE or leaked token) before any process is killed. |
| **4** | **Patch Root Vulnerability Globally** | Patch the exploited CVE and admission policy across all namespaces and images. | Guarantees the attacker cannot immediately re-exploit the cluster the moment the pod is removed. |
| **5** | **Scorched-Earth Hardware Wipe & Firmware Reflash** | **Never "clean" a breached node—destroy it:** PXE re-image the bare-metal OS **and reflash both the GPU and ConnectX NIC firmware with vendor-signed images**. | Eradicates persistent rootkits hidden in the Linux kernel or flashed into the ConnectX NIC / GPU silicon firmware. |
| **6** | **Credential Rotation & Rejoin** | Rotate all **Kubernetes Secrets, Registry tokens, and S3 API keys** that ever resided on `gpu-node-42`, then `kubectl uncordon gpu-node-42`. | Invalidates any credentials the attacker read from memory before quarantine took effect. |

If you follow the rows in order, you will see why each step sits where it does.

#### 3. The 14-Item Production Security Checklist for SR-IOV and GPU Clusters

Before a multi-tenant SR-IOV and GPU cluster goes into production, security architects need an objective audit gate, not verbal assurances. The security guidance here rests on five core principles: defense in depth, trust verification, evidence over assertions, explicit trade-offs, and insider threat awareness. Those five principles translate directly into the fourteen-item checklist below.

| Security Domain | Production Verification Gate | How to Audit on a Live GPU / SR-IOV Node |
|---|---|---|
| **1. Hardware & Firmware Root of Trust** | 1. **UEFI Secure Boot** enabled on all nodes with audited boot logs.<br/>2. **Kernel module signing** enforced and NVIDIA GPU / ConnectX NIC drivers signed.<br/>8. **IOMMU** (`Intel VT-d` / `AMD-Vi`) enabled and configured with DMA faults monitored. | Check `mokutil --sb-state`, `modinfo nvidia \| grep sig`, and `dmesg \| grep -E -i "DMAR\|IOMMU"`. |
| **2. Container & Model Supply Chain** | 3. **Container images scanned for CVEs** (Trivy); only approved digests deployed (never `:latest`).<br/>11. **Model artifacts signed and verified** (Cosign + `.safetensors`, never untrusted Python `pickle`) before deployment. | Verify admission controller rejects unsigned images and scan model repositories for `.bin`/`.pt` pickle files. |
| **3. Kubernetes RBAC & Pod Security** | 4. **Least-privilege RBAC** deployed and verified for all tenant workloads (`gpu-operator` locked down).<br/>5. **Pod Security Standards (`Restricted`)** enforced at admission time (no `root` or `privileged` containers). | Inspect namespace labels `pod-security.kubernetes.io/enforce: restricted` and test admission with a root pod spec. |
| **4. Network, DPU & GPU Isolation** | 6. **Default-deny `NetworkPolicies`** deployed with explicit allow rules.<br/>7. **GPU isolation verified** (`MIG` or dedicated GPUs for sensitive/zero-trust workloads; never time-slicing across untrusted tenants).<br/>9. **BlueField DPU** deployed with isolated ARM security policy enforcement (where applicable). | Verify `nvidia-smi mig -lgi`, test cross-namespace packet drops, and confirm DPU OVS/firewall offload state. |
| **5. Confidential Compute & Data Protection** | 10. **Confidential Computing** (`NVIDIA Hopper H100 CC` + `AMD SEV-SNP` / `Intel TDX`) enabled for high-value models (where available), with KMS encryption at rest and model watermarking. | Verify CPU TEE state and GPU Confidential Computing mode (`nvidia-smi conf-compute -f`). |
| **6. Audit Logging & Quarterly IR Drills** | 12. **Centralized audit logging** enabled with compliance retention.<br/>13. **Incident response playbooks** (`Cordon -> Quarantine NetworkPolicy -> RAM/VRAM dump -> PXE + Firmware reflash`) written and **tested quarterly**.<br/>14. **Security assessments** completed with compliance evidence collected. | Review quarterly Game Day / IR drill reports and verify Kubernetes audit logs stream to immutable storage. |

Use the right-hand column as your audit list, since each item names a command or test to run on a live node.

## Commands and configurations that matter

### 1. Enabling SR-IOV Virtual Functions on a ConnectX-7 NIC and an NVIDIA H100 GPU

Before you write a Virtual Function count to sysfs on a bare-metal worker node, check the kernel boot logs for an active motherboard IOMMU. Then enable the network Virtual Functions with `sriov_numvfs`, and activate the GPU Virtual Functions with `/usr/lib/nvidia/sriov-manage`.

```bash
# 1. Enable 8 SR-IOV VFs on a ConnectX-7 PF (0000:4b:00.0 / ens1f0np0) after verifying IOMMU
dmesg | grep -E -i "DMAR|IOMMU"
echo 8 | sudo tee /sys/class/net/ens1f0np0/device/sriov_numvfs
lspci | grep -i "Mellanox"

# 2. Enable SR-IOV Virtual Functions on NVIDIA GPUs for vGPU / MIG-backed VM passthrough
sudo /usr/lib/nvidia/sriov-manage -e ALL
nvidia-smi vgpu -s
nvidia-smi vgpu
```

Notice that the IOMMU check comes first. Only after it passes should you change the Virtual Function count.

### 2. Forensic Containment Quarantine NetworkPolicy

When an intrusion alert fires on a GPU pod, cordon the node first and then apply a quarantine `NetworkPolicy` right away. This manifest drops all outbound traffic and allows inbound connections only from the forensic collector workstation IP.

```yaml
# quarantine-compromised-gpu-pod.yaml ("Isolate, don't terminate")
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: quarantine-jupyter-research-1
  namespace: research
spec:
  podSelector:
    matchLabels:
      app: jupyter-research-1
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - ipBlock:
            cidr: 10.250.99.10/32   # Allow ONLY the Security Forensics collector IP
  egress: []                        # Drop 100% of outbound traffic (cages the attacker)
```

Read the `ingress` and `egress` blocks together. The empty `egress` list is what cages the attacker.

### 3. Checking Host vs Guest vGPU State

When a vGPU inside a virtual machine misbehaves, check both sides of the hypervisor boundary. Start on the host with the Virtual GPU Manager. Then move into the guest to verify PCIe enumeration, virtual device UUIDs, and license lease status.

```bash
# 1. Host-side vGPU Manager check (before entering guest VM)
nvidia-smi vgpu
nvidia-smi vgpu -q

# 2. Guest-side vGPU & license verification inside the VM
lspci | grep -i nvidia
nvidia-smi --query-gpu=driver_version,vbios_version,gpu_uuid --format=csv
nvidia-smi -q | grep -A 5 "vGPU Software Licensed Product"
```

Finish the host checks before you open the guest, so you know which side of the boundary the fault sits on.

## How it fails

Even when your SR-IOV hardware is healthy, configuration ceilings, kernel bypass behavior, and security mistakes can cause serious failures. The table below lists five common failure modes, so you can match each symptom to its cause and fix.

| Failure mode | Exact symptom & command evidence | Root cause boundary | Remediation |
|---|---|---|---|
| **1. Responder runs `kubectl delete pod` on a compromised GPU notebook scanning `port 22`, and ransomware hits the cluster a week later** | IDS alerts on outbound `port 22` scan or crypto-mining pool; deleting the pod stops the alert immediately, but the attacker returns days later via the same unpatched CVE. | **Destruction of Volatile RAM/VRAM Forensic Evidence:** Deleting the pod or rebooting the node wipes volatile memory and bash/socket state without identifying or patching the entry CVE. | Follow the **6-Step Forensic Containment Protocol**: `kubectl cordon` -> apply a Deny-All **Quarantine `NetworkPolicy`** -> dump RAM/VRAM and audit logs -> patch the CVE globally -> PXE re-image OS + reflash GPU/NIC firmware -> rotate all Secrets. |
| **2. Writing `32` to `sriov_numvfs` fails with `Numerical result out of range` (`EINVAL` / `ERANGE`)** | `echo 32 > /sys/class/net/ens1f0np0/device/sriov_numvfs` fails, and `cat .../sriov_totalvfs` prints `16`. | **Firmware `NUM_OF_VFS` Ceiling (`sriov_totalvfs`):** The NIC's non-volatile firmware configuration (`mlxconfig`) only allocated PCIe BAR space for `16` VFs. | Configure `mlxconfig -d <bdf> set SRIOV_EN=1 NUM_OF_VFS=32`, perform a cold/firmware reboot of the node, and verify `cat sriov_totalvfs` equals `32`. |
| **3. Host `iostat -sxz 1` and `sar -n DEV 1` show `0` traffic while SR-IOV tenant VMs saturate a `400G` NIC (`SP 11.2.4`)** | Tenant VMs drive `400 Gbps` of RoCEv2/RDMA traffic, but standard Linux host OS network and block counters appear completely idle. | **SR-IOV Host Kernel Bypass (`SP 11.2.4`):** SR-IOV VFs DMA directly between guest memory and NIC hardware rings, bypassing the host OS kernel network stack and `QEMU` proxy. | Monitor hardware port counters (`perfquery`, `ethtool -S` physical port metrics, PMCs, `DCGM`), or run eBPF tools (`biosnoop`, `tcplife`) inside the guest VM's dedicated kernel. |
| **4. Compromised x86 host OS flushes its local `iptables` firewall rules and moves laterally across the AI cluster** | Attacker escapes a container onto the host kernel and runs `iptables -F`, disabling host software micro-segmentation. | **Host Firewall "Shared Fate" Anti-Pattern:** Running the security enforcement plane on the same x86 host kernel as untrusted workloads means a host compromise disables the firewall. | Offload micro-segmentation and zero-trust firewall enforcement onto an **NVIDIA BlueField DPU**, whose isolated ARM processors enforce network policy independently of the x86 host OS. |
| **5. Guest VM with NVIDIA vGPU (`GRID A100-20Q`) boots and runs `nvidia-smi`, but CUDA throughput throttles after a grace period** | `nvidia-smi` inside the guest shows `Memory: 2000MiB / 20000MiB` and `Temp: 45C`, but `nvidia-smi -q` reports `vGPU Software Licensed Product: Unlicensed`. | **Unlicensed Guest vGPU Entitlement (`NLS`):** The guest vGPU driver checks out its license directly from the **NVIDIA License System (`NLS`)**; DNS, firewall, or certificate failure blocked lease acquisition. | Verify guest network/DNS reachability and TLS trust to the NLS / DLS endpoint, validate license edition against the assigned vGPU profile on a single canary VM, and confirm `nvidia-smi -q` shows `Licensed`. |

If you get an alert about a compromised pod, start with the first row, because the fix there is to contain the pod rather than delete it. If a VM's GPU throttles, check the license state before you blame the hardware.

## Hands-on lab

### Venue and scope

This lab runs on your own machine with the Python standard library. It simulates Physical Function to Virtual Function allocation and security checks for ConnectX-7 NICs and NVIDIA H100 and A100 GPUs. It also checks Brendan Gregg's SR-IOV observability and CNI rules, the five-layer Zero-Trust AI defense-in-depth stack, and the six-step forensic incident response playbook. The host and cluster commands in this chapter were not run on live hardware.

The inventory below lists the files and simulated targets you will see.

```text
Lab Script Inventory:
- Implementation module: code/part11/sriov_for_nics_and_gpus.py
- Self-checking test runner: code/part11/sriov_for_nics_and_gpus_lab.py
- Simulated hardware targets: ConnectX-7 400G NIC (0000:4b:00.0) and H100/A100 GPU (0000:8a:00.0)
- Incident scenario targets: gpu-node-42 and pod jupyter-research-1
```

### Step 1: Run the self-checking SR-IOV for NICs and GPUs lab

Run the lab verification script from the root of the repository. It executes all twenty-five assertions, so one command tells you whether the whole simulation holds.

```bash
python3 code/part11/sriov_for_nics_and_gpus_lab.py
```

The captured output from this repository looks like the block below.

```text
=== Chapter 11.22 Lab: SR-IOV for NICs & GPUs, Zero-Trust Defense & Forensic IR ===
  [PASS] ConnectX-7 SR-IOV VF allocation is rejected when IOMMU (Intel VT-d / AMD-Vi) is disabled
  [PASS] ConnectX-7 SR-IOV VF allocation is rejected when NIC firmware signature is unverified
  [PASS] Requesting numVfs=32 above hardware sriov_totalvfs=16 is rejected
  [PASS] ConnectX-7 PF (0000:4b:00.0) with IOMMU enabled activates 8 VFs via sriov_numvfs
  [PASS] SP 11.2.4: SR-IOV VFs bypass hypervisor I/O proxy so host iostat/sar visibility is False
  [PASS] NVIDIA H100 GPU enables 16 SR-IOV VFs via /usr/lib/nvidia/sriov-manage -e for time-sliced vGPU
  [PASS] NVIDIA A100 GPU with MIG enabled exposes 7 MIG-backed SR-IOV VFs for hardware-isolated VMs
  [PASS] Volume 18 Summary defines 5 Zero-Trust layers (Supply Chain, Kubernetes, Network, Hardware, Data)
  [PASS] Layer 1 Supply Chain mandates Trivy CVE scans, Cosign signatures, and .safetensors instead of pickle
  [PASS] Layer 2 Kubernetes mandates least-privilege RBAC and Pod Security Admission (PSA) set to Restricted
  [PASS] Layer 3 Network pairs NetworkPolicies with BlueField DPU isolated ARM firewalls to eliminate Shared Fate
  [PASS] Layer 4 Hardware mandates UEFI Secure Boot, signed drivers/firmware, and motherboard IOMMU
  [PASS] Layer 5 Data mandates NVIDIA Hopper Confidential Computing paired with CPU TEEs (AMD SEV-SNP / Intel TDX)
  [PASS] Volume 18 Ch 12: Running kubectl delete pod on jupyter-research-1 destroys RAM/VRAM evidence and leaves HIGH ransomware risk
  [PASS] Volume 18 Ch 12: Rebooting compromised gpu-node-42 wipes volatile RAM and GPU VRAM forensics
  [PASS] Volume 18 Ch 12: 6-step Forensic Containment Protocol preserves evidence, patches CVE, and sets reinfection risk to LOW
  [PASS] Forensic IR Step 1 cordons gpu-node-42 and Step 2 applies a Deny-All Quarantine NetworkPolicy ('Isolate, don't terminate')
  [PASS] Forensic IR Step 3 captures RAM/VRAM snapshots, K8s API audit logs, container image digest, and DCGM power/thermal traces
  [PASS] Forensic IR Step 5 executes scorched-earth PXE OS re-image + reflashes GPU and ConnectX NIC firmware with vendor-signed images
  [PASS] Forensic IR Step 6 rotates all Kubernetes Secrets, Registry tokens, and S3 API keys present on gpu-node-42
  [PASS] SP 11.2 lists SR-IOV and MR-IOV hardware virtualization drivers (ixgbe, ena, hv_netvsc, nvme)
  [PASS] SP 11.1.6 & 11.3.3 contrast Calico (netfilter/iptables) with Cilium (eBPF kube-proxy replacement & Hubble) and tbf qdiscs
  [PASS] SP 11.3.1 Table 11.2 includes the Linux rdma cgroup controller for limiting RDMA and InfiniBand resource usage
  [PASS] Volume 11 Ch 5 NVIDIA vGPU uses SR-IOV VFs (GRID A100-20Q: 45C, 18W/400W, 2000MiB/20000MiB) + NVIDIA License System (NLS)
  [PASS] Volume 18 Index defines a 14-item Production Security Checklist spanning Secure Boot, IOMMU, PSA, DPUs, and quarterly IR drills

Summary: 25 passed, 0 failed out of 25 checks.
```

The summary line should read `Summary: 25 passed, 0 failed out of 25 checks.` Any failure at this point means the simulation no longer matches the chapter's claims.

### Exercises

Work through the six exercises below. Each one uses the simulation module or the material from this chapter.

1. You must enable Virtual Functions on a ConnectX-7 NIC and on an H100 GPU. Use the lab simulation module to find the sysfs path or helper script for each. Then say how time-sliced vGPU Virtual Functions differ from MIG-backed ones.
2. The allocation helper refuses to create Virtual Functions when the IOMMU is disabled or the firmware signature is unverified. Why? What happens at the hardware level when a Virtual Function tries an unauthorized DMA read while the IOMMU is active?
3. Host `iostat` shows no traffic for an SR-IOV device. Why? Name the four guest drivers Brendan Gregg cites. Then say which Linux qdisc implements Kubernetes bandwidth annotations.
4. List the five defense layers in order and the controls at each. Then explain why a BlueField DPU solves the shared-fate problem of a host firewall.
5. A platform engineer ran `kubectl delete pod` on a pod that was scanning port 22. Why did that lead to a later ransomware outage? List the six containment steps in order.
6. Group the fourteen checklist items under hardware and boot, supply chain and models, Kubernetes and network isolation, confidential compute, and audit and incident response.

## Checkpoint questions

<details>
<summary>**1. What is the difference between a Physical Function and a Virtual Function in PCIe Single-Root I/O Virtualization?**</summary>

- **Physical Function.** The primary PCIe function that the host OS or hypervisor manages. It owns global device configuration and firmware updates, and it creates or removes Virtual Functions through `sriov_numvfs`.
- **Virtual Function.** A lightweight, hardware-sliced PCIe function with its own unique PCIe Bus-Device-Function Requester ID, DMA channels, and hardware queues. You can pass a Virtual Function straight into a container or guest VM and get bare-metal I/O speed without hypervisor proxy overhead.
</details>

<details>
<summary>**2. Why do architect interviews compare SR-IOV and MIG as philosophically the same thing for different pieces of silicon?**</summary>

SR-IOV slices a network card at the PCIe silicon level into isolated Virtual Functions that skip the software hypervisor. MIG does the same kind of slicing on a GPU, producing isolated GPU Instances with their own streaming multiprocessors, HBM memory channels, and L2 cache banks. The two split different silicon, but you can think of them as one idea applied twice.
</details>

<details>
<summary>**3. How does an NVIDIA Ampere, Hopper, Ada, or Blackwell GPU use SR-IOV when running NVIDIA vGPU or MIG-backed VMs?**</summary>

Running `/usr/lib/nvidia/sriov-manage -e ALL` exposes hardware PCIe Virtual Functions on the GPU. Time-sliced vGPUs or MIG-backed vGPUs then map onto those Virtual Functions. The hypervisor and NVIDIA Virtual GPU Manager assign each Virtual Function directly to a guest VM.
</details>

<details>
<summary>**4. What four example SR-IOV or hardware-virtualized device drivers are named in Brendan Gregg's Systems Performance Chapter 11, and what is the difference between SR-IOV and MR-IOV?**</summary>

- **Example drivers.** The four drivers are `ixgbe` for Intel networks, `ena` for AWS Elastic Network Adapter, `hv_netvsc` for Microsoft Hyper-V network VSC, and `nvme` for NVMe storage.
- **SR-IOV vs MR-IOV.** Single-Root I/O Virtualization exposes Virtual Functions across one PCIe Root Complex inside a single physical server. Multi-Root I/O Virtualization exposes them across several PCIe Root Complexes that multiple servers share over a PCIe fabric.
</details>

<details>
<summary>**5. Why does SR-IOV make guest disk and network I/O invisible to host OS tools like iostat and sar, and how should operators observe SR-IOV I/O instead?**</summary>

With SR-IOV, the guest driver talks to the NIC or storage hardware directly through DMA. That path skips the host kernel stack and any hypervisor proxy, so host tools miss the traffic. To observe it, you read the hardware Performance Monitoring Counters, the physical NIC port counters, or DCGM metrics. You can also run kernel tracing tools inside the dedicated kernel of the guest VM.
</details>

<details>
<summary>**6. In Systems Performance Chapter 11, why can Calico and kube-proxy incur CPU overhead at scale, and how does Cilium eliminate that overhead?**</summary>

At thousands of Services, Calico in netfilter iptables mode and `kube-proxy` must walk long sequential rule lists. That adds first-packet and per-packet CPU overhead. Cilium removes the cost by replacing both iptables and `kube-proxy` with in-kernel eBPF programs attached to XDP, traffic control qdisc, and cgroup hooks.
</details>

<details>
<summary>**7. How does Linux implement the Kubernetes pod bandwidth annotations, and which cgroup limits RDMA resources?**</summary>

- **Bandwidth annotations.** Kubernetes implements `kubernetes.io/ingress-bandwidth` and `kubernetes.io/egress-bandwidth` by attaching a Linux Token Bucket Filter queueing discipline to the Pod's virtual network interface. Linux also shapes traffic with the `net_prio` and `net_cls` cgroups.
- **RDMA cgroup.** The Linux `rdma` cgroup controller limits RDMA and InfiniBand HCA resource usage per container.
</details>

<details>
<summary>**8. Why is SR-IOV alone insufficient to stop a malicious tenant from reading host memory, and what hardware control completes the boundary?**</summary>

SR-IOV splits the NIC into separate Virtual Functions, but each one is still a PCIe bus master. Unless it is restricted, it can issue Direct Memory Access requests to any physical address. You must enable the motherboard IOMMU with `intel_iommu=on` in the kernel boot parameters. The IOMMU then checks every Virtual Function Requester ID against its DMA Remapping access table, and blocks unauthorized host memory reads with a DMAR fault.
</details>

<details>
<summary>**9. What are the four checks to run in order when a guest VM with an NVIDIA vGPU boots but sees no usable GPU or suffers throttled performance?**</summary>

1. **Check the Host.** Run `nvidia-smi vgpu` on the host to confirm that the physical GPU is healthy, the Virtual GPU Manager is loaded, and the VM has an active vGPU assignment.
2. **Check Guest PCIe Enumeration.** Run `lspci` inside the guest to confirm that the guest OS sees the virtual NVIDIA PCIe device.
3. **Check Guest License State.** Run `nvidia-smi -q` inside the guest to confirm that the vGPU Software Licensed Product field reports Licensed from the NVIDIA License System.
4. **Check Hypervisor VM XML.** Inspect the hypervisor domain XML to confirm that the vGPU profile attachment exists in the VM definition.
</details>

<details>
<summary>**10. Why does a guest VM running NVIDIA vGPU see a different GPU UUID in nvidia-smi than the physical GPU UUID on the host?**</summary>

The guest does not see the physical GPU hardware. If you run nvidia-smi inside it, you see the virtual GPU that the NVIDIA Virtual GPU Manager presents, and that virtual device has its own UUID and lifecycle.
</details>

<details>
<summary>**11. List the five layers of the Zero-Trust AI Defense-in-Depth Architecture.**</summary>

1. **Supply Chain Defense.** Trivy CVE scanning, Cosign image signatures, Admission Controller enforcement, and `.safetensors` model format.
2. **Kubernetes Defense.** Least-privilege RBAC, locked-down operator namespaces, and Pod Security Admission set to Restricted.
3. **Network Defense.** Default-deny `NetworkPolicy` manifests and BlueField DPU hardware-isolated firewalls.
4. **Hardware Defense.** UEFI Secure Boot, signed drivers and firmware, and motherboard IOMMU enforcement.
5. **Data Defense.** NVIDIA Hopper Confidential Computing paired with CPU Trusted Execution Environments so VRAM dumps yield only ciphertext.
</details>

<details>
<summary>**12. Why must enterprise AI supply chains convert model weights from Python pickle files to .safetensors?**</summary>

Python's pickle format is executable, so loading a malicious file with `torch.load` can run arbitrary attacker code inside the GPU container. The `.safetensors` format stores only tensor buffers and metadata, with no executable code paths, which removes model-deserialization remote code execution.
</details>

<details>
<summary>**13. What is the Shared Fate firewall problem on a GPU worker node, and how does an NVIDIA BlueField DPU solve it?**</summary>

If you run firewall and encryption rules on the x86 host kernel through iptables, they share the host OS's fate. An attacker who escapes a container and gains host root can disable the firewall at once. A BlueField DPU moves firewall, zero-trust micro-segmentation, and encryption onto physically isolated ARM cores on the DPU card. A compromised x86 host OS cannot disable enforcement on the DPU.
</details>

<details>
<summary>**14. How does NVIDIA Hopper Confidential Computing protect proprietary model weights against a compromised hypervisor or host administrator?**</summary>

Hopper GPU Confidential Computing mode works with a CPU Trusted Execution Environment, such as AMD SEV-SNP or Intel TDX, and with remote attestation. Model weights and inference prompts stay encrypted in memory and across PCIe transfers from CPU to GPU. A host memory or VRAM dump therefore reads only ciphertext.
</details>

<details>
<summary>**15. What is the Golden Rule of Security Incident Response when an IDS alerts on a compromised GPU Pod or Node?**</summary>

Suppose an IDS alert fires on a compromised GPU pod. The golden rule is to isolate rather than terminate. Do not run `kubectl delete pod` or reboot the server right away. Doing so wipes volatile system RAM and GPU VRAM, which destroys the attacker's forensic footprint and leaves the root vulnerability open to re-exploitation.
</details>

<details>
<summary>**16. Walk through the three containment steps a Senior SRE executes immediately when a GPU node alerts for outbound crypto-mining.**</summary>

Consider the three steps a senior SRE takes first.

1. **Cordon the node.** Run `kubectl cordon` on the compromised node so Kubernetes schedules no new workloads onto it.
2. **Network Quarantine.** Apply a `NetworkPolicy`, or a switch or DPU ACL, that drops all inbound and outbound traffic to the pod or node. Allow connections only from the forensic management IP of the security team.
3. **Volatile Snapshot.** Capture a snapshot of VM or host RAM, GPU VRAM, and disk state before you terminate any process.
</details>

<details>
<summary>**17. What three AI-specific forensic artifacts should responders inspect during a GPU cluster breach investigation?**</summary>

1. **Kubernetes API Audit Logs.** They show which ServiceAccount or user identity deployed the malicious pod.
2. **Container Image Digest.** Compare the running image hash on the node against the signed registry to see whether the Admission Controller was bypassed.
3. **DCGM Telemetry.** Inspect GPU power draw, utilization, and thermal curves. Sustained flat max-TDP power draw on an inference or idle node points to unauthorized cryptocurrency mining.
</details>

<details>
<summary>**18. Why should you destroy a compromised server instead of cleaning it, and what four eradication steps are required before the node can rejoin the cluster?**</summary>

If an attacker gained root on a GPU node, they may have installed kernel rootkits or flashed malicious firmware into the GPU or ConnectX NIC silicon. That is why you destroy the node rather than clean it. Four steps must be finished before it can rejoin.

1. **Re-image the bare-metal server OS.** Provision a clean OS through an automated PXE boot pipeline from an immutable image.
2. **Reflash both the GPU and ConnectX NIC firmware.** Install vendor-signed firmware images and verify their versions.
3. **Rotate all credentials.** Invalidate and reissue every Kubernetes Secret, container registry token, and S3 API key that was present on that node.
4. **Rejoin the cluster.** Run `kubectl uncordon` only after the exploited CVE is patched across the entire cluster.
</details>

<details>
<summary>**19. In the customer scenario, trace the exact chain of events from the initial port 22 network scan to the cluster-wide ransomware outage one week later.**</summary>

1. **Initial compromise.** An attacker exploited an unpatched vulnerability in the research notebook pod and began scanning internal port 22.
2. **Destructive response.** The platform engineer ran `kubectl delete pod`. That stopped the scan but destroyed all volatile memory and process evidence.
3. **Unpatched root cause.** With the forensics destroyed, the security team never identified or patched the entry CVE.
4. **Ransomware re-entry.** Days later, the attacker used the same CVE to compromise a new pod, moved laterally across the cluster, and deployed ransomware.
</details>

<details>
<summary>**20. Name the 14 items in the Production Security Checklist.**</summary>

1. **Secure Boot.** Enable UEFI Secure Boot on all nodes with audited boot logs.
2. **Driver signing.** Enforce kernel module signing and ensure GPU drivers are signed.
3. **Image CVE scanning.** Scan container images for CVEs and deploy only approved versions.
4. **Least-privilege RBAC.** Deploy and verify least-privilege RBAC policies across all namespaces.
5. **Pod Security Standards.** Enforce the Restricted Pod Security profile at admission time.
6. **Network segmentation.** Deploy default-deny `NetworkPolicy` manifests with explicit allow rules.
7. **GPU hardware isolation.** Verify MIG or dedicated GPU isolation for sensitive workloads.
8. **IOMMU DMA protection.** Enable and configure the motherboard IOMMU and monitor DMA faults.
9. **DPU offload.** Deploy BlueField DPUs with isolated security policy enforcement where applicable.
10. **Confidential Computing.** Enable Confidential Computing for high-value models where available.
11. **Model signing.** Sign and verify model artifacts using Cosign and `.safetensors` before deployment.
12. **Audit logging.** Enable centralized audit logging with compliance retention.
13. **Incident response drills.** Write incident response playbooks and test them quarterly.
14. **Compliance assessments.** Complete security assessments and collect compliance evidence.
</details>

## Sources and review notes

### Primary sources read in full for this chapter

The chapter draws on the primary book and field-note sources listed below.

```text
Primary Corpus & Field-Note Sources:
1. Brendan Gregg, Systems Performance: Enterprise and the Cloud, 2nd Edition (systems-performance-2nd-edition, Addison-Wesley, 2020), Chapter 11 (Cloud Computing, Sections 11.1 through 11.8: SR-IOV and MR-IOV hardware virtualization drivers ixgbe, ena, hv_netvsc, nvme; eliminating QEMU / dom0 I/O proxies 5 vs 10 steps in [Qumranet 06] and [Xen 19]; SP 11.2.4 SR-IOV host iostat observability blind spot; Calico iptables vs Cilium eBPF [Borkmann 19] [Borkmann 20] [Cilium 20a] + Hubble [Cilium 19]; Linux rdma, net_prio, and net_cls cgroups in Table 11.2; and tbf token-bucket filter qdiscs > 50 types in [CNI 18] for kubernetes.io/ingress-bandwidth and egress-bandwidth).
2. nvidia-zero-to-hero/volume-18/chapter-07-dma-iommu-and-sriov-security.md (SR-IOV 400G ConnectX-7 VF slicing, IOMMU Intel VT-d / AMD-Vi intel_iommu=on DMAR tables, ConnectX-6 bare-metal SR-IOV penetration test without IOMMU, and iommu=pt trade-offs).
3. nvidia-zero-to-hero/volume-18/chapter-12-incident-response-and-troubleshooting.md (Security IR "Isolate, don't terminate", gpu-node-42 crypto-miner & jupyter-research-1 port 22 scan -> ransomware postmortem, kubectl cordon -> Quarantine NetworkPolicy -> RAM/VRAM snapshot + API audit + image digest + DCGM power review -> PXE OS re-image + GPU & ConnectX NIC vendor-signed firmware reflash + Secret rotation).
4. nvidia-zero-to-hero/volume-18/chapter-12-volume-18-summary.md (5-Layer Zero-Trust AI Defense-in-Depth: Supply Chain .safetensors + Cosign + Trivy -> Kubernetes RBAC + PSA Restricted -> Network NetworkPolicies + BlueField DPU ARM firewall -> Hardware Secure Boot + IOMMU -> Data Hopper Confidential Computing + AMD SEV-SNP / Intel TDX).
5. nvidia-zero-to-hero/volume-18/index.md (12-chapter security overview, 5 key principles, and the 14-item Production Security Checklist).
6. nvidia-zero-to-hero/volume-11/chapter-05-vgpu-architecture-and-enterprise-virtualization.md (Time-sliced vs MIG-backed vGPU over SR-IOV VFs, NVIDIA GRID A100-20Q 45C 18W / 400W 2000MiB / 20000MiB, nvidia-smi vgpu -s/-c/-q, virsh dumpxml, and NVIDIA License System NLS).
7. nvidia-zero-to-hero/volume-23/chapter-13-ai-factory-architect-interview-cheatsheet.md (Section 4 comparing SR-IOV for NICs with MIG for GPUs).
```

### Related source files mapped in MIGRATION_MAP.md

Every Volume 18 file mapped for Chapter 11.22 is cited and migrated in full in the source inventory above.

### Run here

We ran the local verification script `code/part11/sriov_for_nics_and_gpus_lab.py`, and it passed all checks.

### Explicitly labelled inferences

The device allocation model in `code/part11/sriov_for_nics_and_gpus.py` is a deterministic software simulation of sysfs `sriov_numvfs` and `/usr/lib/nvidia/sriov-manage`.

### Not verified on live hardware

The following items were not checked on live hardware, so treat them as untested. The sysfs items are `sriov_numvfs` (`/sys/class/net/.../sriov_numvfs`, `PFs`, `Bus:Device.Function`, `SriovDeviceSpec` in `allocate_sriov_virtual_functions`, `sriov-network-device-plugin`). The helper and device items are `/usr/lib/nvidia/sriov-manage` (64 VFs) and `nvidia-smi vgpu` (`host_iostat_visible`). The `kubectl` items are `FIVE_ZERO_TRUST_AI_LAYERS` with `iommu_enabled=False` and `firmware_signed_and_verified=False`, and `FORENSIC_IR_PLAYBOOK_STEPS` from nvidia-devops `chapter-12-volume-18-summary.md`. They also include `kueue.x-k8s.io/v1beta1` and `resource.k8s.io/v1` in 2026.

### Not in the corpus

Vendor-specific Mellanox BlueField-3 DPU OVS-DOCA hardware steering rule syntax is covered in Chapter 11.28 on DPUs, BlueField, and DOCA.

### Corrections to the author's notes

- The YAML manifests and commands are marked untested and were not applied to a cluster. Custom resource API versions change between releases, so check them against the version you install. Console outputs quoted from the Volume notes are illustrative unless the chapter says otherwise.
- Earlier author note: all security controls, incident response steps, vGPU outputs, and *Systems Performance* Chapter 11 metrics are preserved accurately.
