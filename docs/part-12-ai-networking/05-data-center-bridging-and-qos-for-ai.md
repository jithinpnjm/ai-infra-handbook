---
id: "c12-05"
title: "12.5 Data center bridging and QoS for AI"
sidebar_label: "12.5 Data center bridging and QoS for AI"
sidebar_position: 5
description: "IEEE 802.1Qaz ETS and DCBX, DSCP-to-Priority mapping, QoS trust boundaries, buffer pool carving, and drift detection for AI Ethernet fabrics."
status: "drafted"
tier: "1"
level: "A"
lab_venue: "Nebius GPU"
---

# 12.5 Data center bridging and QoS for AI

| | |
|---|---|
| Level | Advanced |
| Priority tier | 1 |
| Lab venue | Nebius GPU |
| Part | Part 12: Complete AI networking |
| Sources | `nvidia-devops` V9 Ch. 6 & Labs 01–04; `ai-data-center-network-design-and-technologies` Ch. 7 & Ch. 9; `computer-networking-problems-and-solutions` Ch. 8 & Ch. 17; `bcm11-admin` Ch. 3 |
| Code | `code/part12/dcb_qos_ai.py`, `code/part12/dcb_qos_ai_lab.py` |
| Coverage file | `planning/coverage/chapters/12-05.md` |

## Why this matters for AI infrastructure

An AI Ethernet fabric rarely carries pure RoCEv2 collective traffic in isolation. GPU AllReduce and AllToAll collectives on UDP port 4791 share physical network adapters and switch ports with other services. Those services include checkpoint writes, dataset reads, BGP routing keepalives, Kubernetes RPCs, Prometheus scrapes, and operator SSH sessions. If the fabric treats all of those streams as one undifferentiated queue, a checkpoint burst or container image pull can delay Congestion Notification Packets. It can also trigger Priority Flow Control pauses that stall synchronous GPU training steps across the cluster. Conversely, if an operator creates too many lossless traffic classes, switch buffer pools fragment severely. Ordinary TCP and control-plane packets then drop under modest load.

Data Center Bridging and Quality of Service provide the architectural contract that makes link sharing deterministic and observable. First, classification and marking express workload intent in the packet header using DSCP or 802.1p PCP and enforce trust boundaries at ingress ports. Second, Enhanced Transmission Selection under IEEE 802.1Qaz schedules latency-critical CNP feedback with rate-capped Strict Priority. It then shares remaining bandwidth work-conservingly across compute, storage, control, and best-effort queues using Deficit Weighted Round Robin. Third, Data Center Bridging Exchange advertises or audits ETS weights, PFC lossless bitmasks, and Application Priority TLVs over LLDP. Fourth, buffer pool carving partitions finite switch memory between dedicated lossless PFC reservations and the shared lossy pool.

```text
Four Pillars of AI Ethernet Data Center Bridging (DCB) & QoS:
  1. Classification & Trust Boundaries:
     - 6-bit DSCP in 8-bit IP ToS/Traffic Class byte (0..63) or 3-bit 802.1p PCP in 802.1Q VLAN tag (0..7)
     - Ingress trust enforcement (trust: dscp vs trust: pcp vs untrusted rewrite) prevents silent queue drift
  2. Queueing & Enhanced Transmission Selection (ETS, IEEE 802.1Qaz):
     - Maps internal priorities (0..7) to hardware Traffic Classes (TC0..TC7)
     - Rate-capped Strict Priority (TSA 0 / LLQ) for CNPs (TC6, BTH opcode 129 / 0x81)
     - Work-conserving DWRR (TSA 2 / CBWFQ) across RoCE (TC3), Storage (TC4, NVMe-o-TCP port 8009 / NVMe-o-RDMA), Control (TC2), and Best Effort (TC0)
  3. Data Center Bridging Exchange (DCBX, IEEE 802.1Qaz over LLDP EtherType 0x88CC):
     - Uses IEEE 802.1 OUI 00:80:C2 subtypes 9 (ETS Cfg), 10 (ETS Rec), 11 (PFC), and 12 (Application Priority UDP 4791 -> Priority 3)
     - Enforces Willing bit state machine (SWITCH_PEER Willing=1/0 vs BOTH_LOCAL_STATIC Willing=0/0)
  4. Switch Buffer Pool Carving:
     - Balances dedicated lossless PFC headroom (65,536 B / 25% per lossless priority on a 262,144 B port buffer) against shared lossy burst absorption (75%)
```

Chapter 2.19 introduced general QoS primitives, and Chapter 12.4 derived the wire-level mechanics of PFC, ECN, and DCQCN. This chapter focuses on end-to-end QoS system design. We cover IEEE 802.1Qaz ETS and DCBX state machines, buffer pool carving math, hop-by-hop trust-boundary drift detection, and production validation.

## Prerequisites and outcomes

**Prerequisites:** Review queuing, QoS, ECN, PFC, and DCB basics in Chapter 2.19. Review RoCEv2 transport in Chapter 12.3 and PFC, ECN, and DCQCN in Chapter 12.4.

**Outcomes:** After completing this chapter, you will be able to:
- Trace a packet from application socket or RDMA Queue Pair marking through ConnectX egress traffic classes. You will also follow it across switch ingress trust boundaries, internal priority queues, and ETS schedulers.
- Design a five-class AI QoS model. You will encode and decode 8-bit IP ToS bytes across data, storage, control, and CNP traffic.
- Compute IEEE 802.1Qaz ETS work-conserving bandwidth shares, Strict Priority policing caps, and frame serialization jitter. You will also explain why scheduling RoCE data as strict priority starves management traffic.
- Decode IEEE 802.1Qaz DCBX LLDP frames and evaluate Willing bit state machines. You will also carve switch port buffer pools across lossless and lossy classes.
- Diagnose silent hop-by-hop trust-mode drift. You will execute a six-layer production QoS validation plan across host adapters and leaf or spine switches.

---

## 1. End-to-end QoS architecture and the small class model for AI fabrics

### 1.1 The highway lanes mental model and why every control has a single job

In a converged AI Ethernet fabric, physical links carry traffic types with fundamentally incompatible loss and latency requirements. When a massive storage checkpoint or bulk image pull shares a queue with RDMA collectives, training steps stall behind paused or dropped packets.

A helpful mental model compares an eight-priority Ethernet link to a multi-lane highway. Priority 0 on TC0 is the general public lane carrying bulk transfers, container image pulls, and operator traffic. Under congestion, packets wait in a lossy queue or drop so TCP can back off. Priority 2 on TC2 is the dedicated municipal service lane for BGP routing updates, Kubernetes heartbeats, and cluster monitoring. It requires a guaranteed minimum bandwidth share so control-plane sessions never time out during a training burst.

Priority 4 on TC4 is the commercial trucking lane carrying massive storage payloads over NVMe-o-TCP on port 8009. It also carries parallel file systems such as Lustre, GPFS, BeeGFS, and WekaFS. It demands a 30 percent minimum bandwidth share under contention, and TCP recovers cleanly from occasional packet drops without halting the fabric. Priority 3 on TC3 is the emergency convoy express lane for RoCEv2 AI compute on UDP destination port 4791. RDMA Go-Back-N retransmission on a 400 Gbps or 800 Gbps link severely degrades collective completion time. This lane therefore uses ECN for early rate control and narrowly scoped PFC so it never drops a packet due to buffer overflow. Finally, Priority 6 on TC6 is the motorcycle courier lane for CNP feedback frames. It uses rate-capped Strict Priority so backward congestion notifications are never queued behind jumbo data frames.

If a storage flow or an untrusted bulk transfer is accidentally classified into Priority 3, a checkpoint write wanders into the lossless RoCE lane. It fills the Priority 3 buffer, triggers PFC pause frames, and freezes GPU collectives across the switch. Conversely, if a RoCEv2 packet is silently reclassified into Priority 0 at a downstream switch hop, ping and TCP connectivity continue to pass. Meanwhile, RDMA collectives suffer unexplained tail drops and `RETRY_EXC_ERR` completions.

```mermaid
flowchart LR
    A["App / NCCL / Storage\nSets Socket/QP DSCP"] --> N["ConnectX NIC Egress\nMaps DSCP -> Prio & TC"]
    N --> I["Switch Ingress Port\nTrust DSCP or PCP?"]
    I -->|"Trusted DSCP 26/46"| Q3["Lossless Queue TC3\nECN + PFC + ETS 50%"]
    I -->|"Untrusted / PCP Drift"| Q0["Lossy Queue TC0\nBest Effort (WRONG)"]
    Q3 --> S["Egress Scheduler (ETS)\nStrict TC6 + DWRR TCs"]
    Q0 -.->|"Ping/IP works; RDMA\ndrops (rx_prio0_discard)"| DRIFT["Silent Drift:\nNo Alarm Fires"]
    S --> L["Next Fabric Hop\nSpine / Receiver Leaf"]
```

| Control mechanism | Layer / Header / Hardware block | Primary question it answers | What it does NOT provide |
|---|---|---|---|
| **DSCP / 802.1p PCP marking** | L3 IP ToS byte (6-bit DSCP) / L2 802.1Q tag (3-bit PCP) | Which service class *should* this packet use? | Guaranteed end-to-end treatment if a downstream hop rewrites or ignores the tag |
| **Ingress classification & trust** | Switch ingress pipeline (`mlnx_qos --trust dscp` vs `pcp`) | Which internal priority (0..7) and egress queue (TC0..TC7) receives the frame? | Additional link bandwidth or workload authentication |
| **Queue scheduling (Strict vs DWRR)** | Egress port scheduler (TSA 0 Strict Priority vs TSA 2 DWRR) | Which non-empty egress queue is transmitted next on the wire? | Fairness across classes unless weights and strict-priority policers are configured |
| **Enhanced Transmission Selection (ETS)** | IEEE 802.1Qaz bandwidth-sharing controller | What minimum bandwidth share does each Traffic Class receive *under contention*? | A hard, walled-off bandwidth reservation when a class is idle, or a hard ceiling when other classes are idle |
| **Explicit Congestion Notification (ECN)** | RFC 3168 (2-bit IP ECN field `10 -> 11` via WRED `K_min`/`K_max`) | Should the sending RDMA Queue Pair (QP) or TCP socket reduce its injection rate? | Immediate link-local loss protection during a sub-RTT microburst |
| **Priority Flow Control (PFC)** | IEEE 802.1Qbb L2 MAC Control (`0x8808`, opcode `0x0101`) | Can a loss-sensitive queue (Priority 3) pause its immediate upstream link peer before overflowing? | Flow-level isolation (it pauses the entire priority class) or extra fabric capacity |

### 1.2 Designing a small, explainable QoS class model

A common architectural mistake is starting from the hardware maximum of eight priorities and inventing eight distinct policies. Every additional class partitions buffer memory, multiplies `DCBX` and `mlnx_qos` configuration lines across thousands of ports, and complicates incident triage. Start instead from operational workload intents and failure domains. Add a class only when it has a distinct congestion behavior, owner, failure policy, and validation test.

| Workload intent | Typical protocols & ports | Recommended DSCP (Hex ToS with ECT(0) / 00) | `mlnx_qos` 8-value bucket | 802.1p Priority (PCP) | Hardware Traffic Class (TC) | Loss control (PFC / ECN) | IEEE 802.1Qaz TSA & ETS share |
|---|---|---|---|---|---|---|---|
| **Best Effort** | Bulk TCP, image pulls, general traffic | DSCP 0 (CS0/DF, `0x00`) or DSCP 10 (AF11, `0x28`) | `0-7`, `8-15` | Priority 0 | TC0 | Lossy (tail drop / WRED) | `dwrr` (TSA 2), 10% |
| **Infrastructure & Control** | BGP, Kubernetes API, Prometheus, SSH | DSCP 24 (CS3, `0x60`) or DSCP 34 (AF41, `0x88`) | `24-31`, `32-39` | Priority 2 | TC2 | Lossy (protected minimum share) | `dwrr` (TSA 2), 10% |
| **RoCEv2 AI Compute** | NCCL collectives, GPUDirect RDMA (UDP 4791) | DSCP 26 (AF31, `0x6a` w/ ECT(0)) or DSCP 46 (EF, `0xb8` w/ 00) | `24-31` or `40-47` | Priority 3 | TC3 | **Lossless (PFC ON + ECN ON)** | `dwrr` (TSA 2), 50% |
| **Storage & Checkpointing** | NVMe-o-TCP (TCP 8009), parallel FS (NFS, Lustre, WekaFS) | DSCP 18 (AF21, `0x4a` w/ ECT(0)) | `16-23` | Priority 4 | TC4 | Lossy (PFC OFF, TCP ECN ON) | `dwrr` (TSA 2), 30% |
| **CNP & Critical Control** | RoCEv2 CNP (BTH opcode `0x81`), LACP/LLDP | DSCP 48 (CS6, `0xc1` w/ ECT(1)) or DSCP 56 (CS7, `0xe0`) | `48-55`, `56-63` | Priority 6 | TC6 | Lossy (never paused, low occupancy) | `strict` (TSA 0), policed cap 20 Gbps (5% of 400G) |

Three design invariants govern this table. First, the DWRR percentages across TC0, TC2, TC3, and TC4 sum to 100 percent (`10% + 10% + 50% + 30% = 100%`). That sum satisfies the IEEE 802.1Qaz requirement for Enhanced Transmission Selection classes. Second, only TC3 on Priority 3 has PFC enabled. When storage uses NVMe-o-TCP on TCP port 8009 or parallel NFS, keeping TC4 on Priority 4 lossy with TCP ECN preserves 75 percent of the port buffer for shared burst absorption. It also prevents storage congestion from generating PFC pause frames. A second lossless class on Priority 4 is considered only if a deployment runs NVMe-o-RDMA over the same physical switches. Even then, dedicated storage fabrics are preferred at scale.

Third, QoS is neither tenant security nor capacity planning. An endpoint can mark any DSCP value it chooses unless the ingress switch port enforces a trust or ACL policy. QoS classification decides which queue a packet enters and how contention is arbitrated. It does not authenticate a tenant, prevent lateral movement, or manufacture bandwidth when aggregate demand exceeds link capacity.

---

## 2. Packet markings, IP ToS byte math, and QoS trust boundaries

### 2.1 Encoding and decoding the 8-bit IP ToS / Traffic Class byte vs 802.1p PCP

When operators run `tcpdump -v` on a GPU server to verify RoCEv2 markings, `tcpdump` prints the entire 8-bit IP Type of Service byte in hexadecimal. It does not print the 6-bit DSCP integer directly. Misreading the hexadecimal `tos` byte as the decimal DSCP value leads engineers to chase imaginary marking bugs or misconfigure switch buckets.

A packet can carry class-of-service markings at Layer 2, Layer 3, or both. At Layer 2, an IEEE 802.1Q VLAN tag inserts a 4-byte header after the Source MAC (`TPID 0x8100`). That tag contains a 3-bit Priority Code Point from 0 to 7, a 1-bit Drop Eligible Indicator, and a 12-bit VLAN ID from 0 to 4095. Pure routed Layer 3 Ethernet links use untagged frames with no 802.1Q header and therefore carry no PCP bits on the wire. At Layer 3, every IPv4 or IPv6 packet carries an 8-bit ToS or Traffic Class byte. The upper 6 bits hold the DSCP value from 0 to 63, and the lower 2 bits hold the ECN state.

```text
IP ToS / Traffic Class Byte Bit-Shift Equations:
  ToS_byte = (DSCP << 2) | ECN
  DSCP     = ToS_byte >> 2
  ECN      = ToS_byte & 0x03
  mlnx_qos 8-value DSCP buckets: 0-7, 8-15, 16-23, 24-31, 32-39, 40-47, 48-55, 56-63
```

| Traffic type | 6-bit DSCP (decimal & binary) | 2-bit ECN state | 8-bit ToS calculation `(DSCP << 2) \| ECN` | `tcpdump -v` hex output | `mlnx_qos` 8-value DSCP bucket | Mapped 802.1p Priority |
|---|---|---|---|---|---|---|
| **Best Effort (CS0/DF)** | 0 (`000000`) | `00` (0, Not-ECT) | `(0 << 2) \| 0 = 0` | `tos 0x0` (`0x00`) | `0-7` | Priority 0 |
| **Storage (AF21) w/ ECT(0)** | 18 (`010010`) | `10` (2, ECT(0)) | `(18 << 2) \| 2 = 74` | `tos 0x4a` (74) | `16-23` | Priority 4 |
| **Control (CS3)** | 24 (`011000`) | `00` (0, Not-ECT) | `(24 << 2) \| 0 = 96` | `tos 0x60` (96) | `24-31` | Priority 2 |
| **RoCEv2 Data (AF31) w/ ECT(0)** | 26 (`011010`) | `10` (2, ECT(0)) | `(26 << 2) \| 2 = 106` | `tos 0x6a` (106) | `24-31` | Priority 3 |
| **RoCEv2 Data (AF31) w/ CE** | 26 (`011010`) | `11` (3, CE marked) | `(26 << 2) \| 3 = 107` | `tos 0x6b` (107) | `24-31` | Priority 3 |
| **RoCEv2 Data (EF) w/ 00** | 46 (`101110`) | `00` (0, Not-ECT) | `(46 << 2) \| 0 = 184` | `tos 0xb8` (184) | `40-47` | Priority 3 |
| **RoCEv2 CNP (CS6) w/ ECT(1)** | 48 (`110000`) | `01` (1, ECT(1)) | `(48 << 2) \| 1 = 193` | `tos 0xc1` (193) | `48-55` | Priority 6 |
| **Network Control (CS7)** | 56 (`111000`) | `00` (0, Not-ECT) | `(56 << 2) \| 0 = 224` | `tos 0xe0` (224) | `56-63` | Priority 6 |

In NVIDIA `mlnx_qos` output, the 64 DSCP values are displayed in eight buckets of eight consecutive codepoints. Thus DSCP 26 sits in bucket `24-31`, DSCP 46 sits in bucket `40-47`, and DSCP 48 sits in bucket `48-55`.

### 2.2 Trust boundaries, untrusted ingress rewrites, and PCP vs DSCP across L2/L3 hops

Even when a GPU host marks every RoCEv2 packet properly, a single misconfigured switch port along the fabric path breaks the policy. If that port uses the wrong trust mode, it silently dumps RoCEv2 packets into a lossy queue. Every switch ingress port and adapter interface operates in one of three classification trust states.

First, under `trust: dscp`, the ingress port inspects the 6-bit IP DSCP field and maps it through the 64-entry DSCP-to-Priority table. Because IP headers survive Layer 3 routing across leaf, spine, and super-spine switches, `trust: dscp` preserves classification end to end without requiring VLAN tags. Second, under `trust: pcp`, the ingress port ignores the IP DSCP field and inspects only the 3-bit PCP field inside an 802.1Q VLAN header. If a port is left in `trust: pcp` and receives an untagged routed IP packet, there is no 802.1Q header. The switch defaults the frame to Priority 0 Best Effort. That default silently strips lossless PFC and ECN protection even though the IP header still carries DSCP 26 or DSCP 46.

Third, at an untrusted rewrite boundary (`untrusted_rewrite_zero`) facing tenant VMs or external networks, the ingress switch port does not trust host-supplied markings. It either rewrites DSCP to zero or classifies traffic via an explicit ACL policy. Similarly, when traffic traverses VXLAN, GRE, or IPsec overlays, the encapsulating VTEP or DPU must copy the inner DSCP and ECN bits to the outer IP header. Using `uniform` or `tos inherit` mode ensures transit spine switches can classify and ECN-mark packets properly.

In multi-tenant or bare-metal cloud environments using NVIDIA BlueField DPUs in Embedded CPU Function Ownership (`ECPF`) mode, the embedded Arm subsystem and hardware switch sit directly in front of the host PCIe function. The platform administrator can enforce DSCP marking and ACL normalization inside the DPU embedded switch before frames ever reach the leaf switch port. That architecture prevents an untrusted host OS from spoofing DSCP 26 or DSCP 48. However, it introduces a three-layer operational boundary across the host interface, DPU Arm policy service, and external leaf switch port that must be verified after every boot.

---

## 3. IEEE 802.1Qaz Enhanced Transmission Selection, Strict Priority, and CBWFQ scheduling math

### 3.1 How IEEE 802.1Qaz ETS combines Strict Priority (TSA 0) and DWRR (TSA 2)

Once an ingress packet is mapped to an internal priority and placed into its egress Traffic Class queue, the egress port scheduler must decide which non-empty queue transmits next. If all queues share equal priority, 9,000-byte data frames delay urgent CNP feedback frames. Conversely, if data queues use unpoliced strict priority, they starve routing and management traffic completely during collective bursts.

IEEE 802.1Qaz Enhanced Transmission Selection standardizes a two-tier hierarchical scheduler across up to eight Traffic Classes. It assigns each Traffic Class a Transmission Selection Algorithm identifier.

```text
IEEE 802.1Qaz Transmission Selection Algorithm (TSA) Identifiers:
  - TSA 0 (Strict Priority / strict / LLQ):     Serviced ahead of all DWRR queues whenever a packet is present; used for CNPs on TC6
  - TSA 1 (Credit-Based Shaper / cbs):          Used in audio/video bridging (AVB / TSN), not standard AI RoCE fabrics
  - TSA 2 (Enhanced Transmission Selection / ets / dwrr / CBWFQ): Shares bandwidth remaining after TSA 0 in proportion to weights w_i (sum = 100%)
  - TSA 255 (Vendor-Specific):                  Hardware-specific scheduling extensions
```

### 3.2 Work-conserving CBWFQ / DWRR math: minimum guarantees under contention, not hard reservations

Engineers new to ETS often misread a configured weight—such as 30 percent for Storage on TC4 and 50 percent for RoCE on TC3—as either a hard static partition or a hard rate ceiling. They worry that 30 percent of the link sits idle when Storage is quiet or that Storage can never exceed 30 percent when Compute is idle.

In reality, ETS under DWRR or Class-Based Weighted Fair Queueing is work-conserving. When all classes are backlogged under full contention, the scheduler first deducts bandwidth consumed by strict-priority TSA 0 classes ($R_\{\text`{strict}`}$). It then divides the remaining link bandwidth across active DWRR classes in proportion to their weights $w_i$. When some classes are idle or use less than their share, any unused bandwidth is dynamically redistributed across the remaining backlogged DWRR classes in exact proportion to their relative weights.

```text
Work-Conserving ETS Bandwidth Formula & 1,024 Kbps WAN CBWFQ Example (CNPS Ch 8):
  - ETS Allocation Formula: B_i = (R_link - R_strict) * (w_i / sum(w_j for j in active))
  - Guaranteed Shares on 1,024 Kbps WAN Link: AF41 = 256 Kbps, AF31 = 128 Kbps, AF21 = 128 Kbps, Unclassified/Default = 512 Kbps
  - Lowest-Terms Ratio: 256 : 128 : 128 : 512 reduces to 2 : 1 : 1 : 4 across 8 clock cycles
  - All 4 Classes Backlogged: Cycles 1-2 send AF41 (2 pkts), Cycle 3 sends AF31 (1 pkt), Cycle 4 sends AF21 (1 pkt), Cycles 5-8 send Default (4 pkts)
  - Work-Conserving Redistribution (1 AF41 pkt, 0 AF21 pkts, 3 Default pkts):
    * Cycle 1 sends the single AF41 pkt; Cycle 2 immediately serves AF31 (AF31 gets Cycles 2 and 3)
    * Cycle 4 skips empty AF21 and serves Default (Cycles 4-6); when Default runs out after 3 pkts, Cycle 8 serves AF31 again
```

Now apply the exact same work-conserving ETS formula (`simulate_ets_scheduling` in `code/part12/dcb_qos_ai.py`) to a 400.0 Gbps AI Ethernet link running our five-class model.

| Contention scenario on a 400.0 Gbps link | Offered load per TC (Gbps) | TC6 (`strict`, CNP) allocated | TC0 (10% `dwrr`, Best Effort) | TC2 (10% `dwrr`, Control) | TC3 (50% `dwrr`, RoCEv2) | TC4 (30% `dwrr`, Storage) | Operational lesson |
|---|---|---|---|---|---|---|---|
| **1. All 5 classes contending** | `TC6=10, TC0=100, TC2=50, TC3=400, TC4=200` | **10.0 Gbps** | **39.0 Gbps** (10% of 390G) | **39.0 Gbps** (10% of 390G) | **195.0 Gbps** (50% of 390G) | **117.0 Gbps** (30% of 390G) | TC6 takes 10G first; remaining 390G splits `10:10:50:30`; 0 classes starved |
| **2. Only RoCE (TC3) + Storage (TC4) active** | `TC3=400, TC4=400 (TC0=TC2=TC6=0)` | 0.0 Gbps | 0.0 Gbps | 0.0 Gbps | **250.0 Gbps** ($\frac`{50}``{50+30}` \times 400$) | **150.0 Gbps** ($\frac`{30}``{50+30}` \times 400$) | Unused 20% (`TC0+TC2`) is shared in a $50:30 = 5:3$ ratio (250G vs 150G) |
| **3. Only Storage (TC4, 30%) active** | `TC4=400 (TC0=TC2=TC3=TC6=0)` | 0.0 Gbps | 0.0 Gbps | 0.0 Gbps | 0.0 Gbps | **400.0 Gbps** (100% of link) | 30% ETS is a minimum share under contention, **not** a ceiling when the link is idle |
| **4. Misconfigured `strict` RoCE** | `TC1 (Prio 3 RoCE) = 400 (strict), TC0 (Mgmt) = 10 (dwrr weight 5)` | N/A (`TC1 strict` takes **400.0 Gbps**) | **0.0 Gbps (STARVED)** | N/A | **400.0 Gbps** (`TC1 strict`) | N/A | Setting RoCE (`TC1`) to `strict` without a cap completely starves `dwrr` management (`TC0`); `dwrr 95:5` guarantees `TC0` **20.0 Gbps** (`TC1 = 380.0 Gbps`) |

### 3.3 Strict Priority (LLQ) policing math and serialization jitter (9,000 B vs 64 B)

Why must a strict-priority queue always have a strict rate cap or bounded offered load? If a strict-priority queue is allowed to consume 100 percent of the link, every DWRR queue is starved. Conversely, when a strict-priority queue is rate-capped by a policer to protect the rest of the link, exceeding that cap during congestion drops traffic across the entire strict-priority class.

```text
LLQ Strict-Priority Policing & Serialization Jitter Derivations (CNPS Ch 8 & Ch 17, Handbook 2.19):
  1. LLQ Policing on a 1,024 Kbps WAN Link (512 Kbps LLQ Cap, 512 Kbps Remaining):
     - Up to 8 VoIP calls at 64 Kbps (8 * 64 = 512 Kbps) fit inside the cap with 0 drops
     - 9 calls under congestion (9 * 64 = 576 Kbps): policer drops 576 - 512 = 64 Kbps across all 9 calls (class-wide drop)
     - 12 calls under congestion (12 * 64 = 768 Kbps): policer drops 768 - 512 = 256 Kbps (4 * 64 Kbps)
     - Codec change to 16 Kbps: 32 calls (32 * 16 = 512 Kbps) fit with 0 Kbps dropped
     - Uncongested exception: 10 calls at 64 Kbps (640 Kbps) when all other traffic <= 384 Kbps (1,024 - 640 = 384 Kbps, e.g. 300 Kbps) pass with 0 drops
  2. Frame Serialization Delay & Jitter (T_ser = Bits / R_link):
     - At 100 Mbps: 64 B = 512 / 10^8 = 0.00512 ms (.05 ms with framing in CNPS); 1,500 B = 0.12 ms; 9,000 B = 0.72 ms (0.72 / 0.05 = 14.4 -> >14x longer)
     - Mixed 7 elephant + 4 mouse frames at 100 Mbps (Fig 17-4): mouse spacing jitters between .05 ms and .288 ms; elephant spacing between .05 ms and .15 ms
     - At 400 Gbps: 9,000 B (72,000 bits) = 180.0 ns; 64 B (512 bits) = 1.28 ns (180.0 / 1.28 = 140.625x ratio)
```

Giving 64-byte CNPs on TC6 a dedicated strict-priority queue avoids head-of-line delay behind jumbo packets. On a 400 Gbps link, a newly arriving CNP waits at most one in-flight 180.0 ns jumbo frame serialization rather than sitting behind megabytes of queued 9,000-byte RoCE data payloads.

---

## 4. IEEE 802.1Qaz DCBX TLV negotiation and switch buffer pool carving

### 4.1 DCBX over LLDP (`EtherType 0x88CC`, `OUI 00:80:C2`, Subtypes 9..12) and the Willing bit

Configuring PFC on Priority 3 and ETS weights on a switch port is useless if the attached ConnectX adapter transmits RoCEv2 traffic on Priority 0 or enables PFC on Priority 4. When host and switch QoS settings diverge after a reboot, jobs suffer silent drops or pause mismatches.

Data Center Bridging Exchange under IEEE 802.1Qaz is a link-local discovery and capability-exchange protocol carried inside Link Layer Discovery Protocol frames (`EtherType 0x88CC`, destination multicast MAC `01:80:C2:00:00:0E`). It uses Organizationally Specific TLVs with the IEEE 802.1 OUI `00:80:C2`.

| DCBX TLV name | IEEE 802.1 OUI | Subtype | Symmetric vs Asymmetric | Key fields carried on the wire | Purpose on a GPU Host $\leftrightarrow$ Leaf Switch link |
|---|---|---|---|---|---|
| **ETS Configuration TLV** | `00:80:C2` | **9 (`0x09`)** | Asymmetric (uses ETS Recommendation TLV 10) | Willing (1 bit), CBS (1 bit), Max TCs (3 bits), Priority Assignment Table (8 x 4 bits: Prio 0..7 -> TC), TC Bandwidth Table (8 x 8 bits: % weights), TSA Assignment Table (8 x 8 bits: `0=Strict, 2=ETS`) | Advertises operational Prio -> TC map, ETS percentage weights, and `strict`/`dwrr` TSA assignments |
| **ETS Recommendation TLV** | `00:80:C2` | **10 (`0x0A`)** | Asymmetric recommendation from switch to host | Priority Assignment Table (8 x 4 bits), TC Bandwidth Table (8 x 8 bits), TSA Assignment Table (8 x 8 bits) | Recommends the egress ETS scheduling profile that a Willing=1 peer should adopt |
| **PFC Configuration TLV** | `00:80:C2` | **11 (`0x0B`)** | **Symmetric** (both ends of the link must use the identical PFC bitmask) | Willing (1 bit), MBC (1 bit, MACsec Bypass Capability), PFC Cap (4 bits: max simultaneous lossless classes), **PFC Enable bitmask (8 bits: e.g., `00001000` = `0x08` for Priority 3)** | Ensures both the NIC and leaf switch port enable PFC pause (XOFF/XON) on the exact same priority (Priority 3) |
| **Application Priority TLV** | `00:80:C2` | **12 (`0x0C`)** | Symmetric application-to-priority binding | List of 3-octet entries: Priority (3 bits), Selector (3 bits: 1=EtherType, 2=TCP/UDP port, 3=UDP/DCCP), Protocol ID (16 bits: **4791** for RoCEv2) | Tells the endpoint to tag RoCEv2 (UDP port 4791) packets with **Priority 3** |

The Willing bit determines which side wins during DCBX negotiation (`evaluate_dcbx_negotiation` in `code/part12/dcb_qos_ai.py`).

```mermaid
flowchart TB
    LLDP["LLDP Frame (0x88CC, MAC 01:80:C2:00:00:0E)\nIEEE 802.1 OUI 00:80:C2 Subtypes 9, 10, 11, 12"] --> W{"Inspect Host & Switch\nWilling Bits (0 or 1)"}
    W -->|"Host Willing=1\nSwitch Willing=0"| P1["SWITCH_PEER Mode:\nHost adopts Switch PFC & ETS"]
    W -->|"Host Willing=0\nSwitch Willing=0"| P2["BOTH_LOCAL_STATIC Mode:\nAutomation pushes both; audit match"]
    W -->|"Host Willing=0\nSwitch Willing=1"| P3["HOST_LOCAL Mode:\nSwitch adopts Host (rare/unsafe)"]
    W -->|"Host Willing=1\nSwitch Willing=1"| P4["CONFLICT_BOTH_WILLING:\nTie-breaker ambiguity; flag error"]
    P2 --> CHK{"Do PFC, ETS, App 4791,\nand Trust match?"}
    CHK -->|"Yes"| OK["Healthy Link Contract"]
    CHK -->|"No"| ERR["Drift Detected:\nPFC / ETS / Trust Mismatch"]
```

| Host Willing | Switch Willing | Operational state source | Production behavior and AI fabric recommendation |
|---|---|---|---|
| **1 (True)** | **0 (False)** | **`SWITCH_PEER`** | **Classic plug-and-play DCBX:** The leaf switch is authoritative (Willing=0) and the host NIC (`lldpad` / firmware DCBX agent, Willing=1) dynamically adopts the switch PFC bitmask (Priority 3), ETS weights, and UDP 4791 -> Priority 3 Application Priority TLV. |
| **0 (False)** | **0 (False)** | **`BOTH_LOCAL_STATIC`** | **Explicit automation mode (common in large AI clusters):** Neither side accepts dynamic LLDP overrides; automation pushes identical profiles from a single versioned source of truth to both `mlnx_qos` on the host and the switch NOS, while LLDP TLVs audit that zero mismatches exist. |
| **0 (False)** | **1 (True)** | **`HOST_LOCAL`** | Switch accepts whatever the host advertises. **Avoid in production:** a misconfigured or compromised host can alter switch port PFC/ETS behavior. |
| **1 (True)** | **1 (True)** | **`CONFLICT_BOTH_WILLING`** | Both sides claim willingness to be overridden; symmetric tie-breakers vary across implementations and cause unpredictable flips on reboot. **Flag as a configuration error.** |

### 4.2 Switch buffer pool carving across lossless (TC3) and lossy (TC0, TC2, TC4, TC6) classes

Why do NVIDIA Spectrum switches use a Fully Shared Buffer architecture rather than fixed per-port sliced buffers? And why must operators still restrict PFC to one or at most two priorities?

In a switch with a sliced or statically partitioned buffer, each port can access only its tiny dedicated slice of memory. If an 800 Gbps incast microburst hits Port 1, Port 1 overflows or triggers PFC even while 95 percent of total switch memory sits empty on idle ports. A shared-buffer ASIC pools internal memory dynamically so a congested port can borrow burst absorption space. However, every lossless PFC-enabled priority on every port still requires a dedicated minimum reservation and flight-time headroom. Lossy queues cannot borrow that reservation. Once XOFF fires, the switch must guarantee space for the bytes already in flight on the cable, such as 49,064 B for a 2 m DAC cable or 298,064 B for a 500 m optical fiber at 400 Gbps with MTU 9,000.

Using our 262,144-byte port receive buffer profile from `mlnx_qos -i swp12`, each lossless priority reserves 65,536 bytes. That reservation sets XON at 32,768 B or 50 percent, XOFF at 49,152 B or 75 percent, and headroom at 16,384 B or 25 percent. The table below shows what happens as an operator enables PFC on additional classes (`evaluate_buffer_pool_carving` in `code/part12/dcb_qos_ai.py`).

| Number of lossless (PFC) priorities enabled | Lossless priorities | Reserved per lossless priority (XON / XOFF / Headroom) | Total port buffer locked in lossless reservations | Remaining shared buffer for lossy TC0, TC2, TC4, TC6 | Lossless % vs Lossy % | Operational verdict |
|---|---|---|---|---|---|---|
| **1 lossless class (Recommended)** | Priority 3 (RoCEv2 Compute) | 65,536 B (32,768 / 49,152 / 16,384 B) | **65,536 B** (64 KiB) | **196,608 B** (192 KiB) | **25.0% vs 75.0%** | **`HEALTHY_BUFFER_CARVING`:** RoCEv2 has full lossless headroom; 75% of buffer remains for storage (TC4), control (TC2), CNP (TC6), and best effort (TC0). |
| **2 lossless classes (Maximum practical)** | Priority 3 (RoCE) + Priority 4 (NVMe-o-RDMA) | 65,536 B each | **131,072 B** (128 KiB) | **131,072 B** (128 KiB) | **50.0% vs 50.0%** | **`HEALTHY_BUFFER_CARVING` (Tight):** Acceptable only when NVMe-o-RDMA shares the fabric and requires lossless transport alongside RoCE compute. |
| **4 lossless classes (Anti-pattern)** | Priorities 1, 2, 3, 4 | 65,536 B each | **262,144 B** (256 KiB) | **0 B** (0 KiB) | **100.0% vs 0.0%** | **`BUFFER_EXHAUSTED_TOO_MANY_LOSSLESS_CLASSES`:** 100% of port buffer is locked in lossless reservations; lossy TCP, BGP, Kubernetes, and CNP queues have 0 B and drop immediately. |

### 4.3 Comparing Ethernet DCB (PFC + ETS + DCQCN) with InfiniBand Virtual Lanes and Storage Fabrics

When architects evaluate AI compute and storage fabrics, they frequently compare how Ethernet DCB and native InfiniBand implement QoS and lossless transport. Misunderstanding which storage protocols require lossless queues leads teams to over-enable PFC on Ethernet switches.

Native InfiniBand implements QoS via up to 16 Virtual Lanes and link-level Credit-Based Flow Control exchanged in the Link Layer Header. A sender switch or adapter never transmits on a Virtual Lane unless the downstream port has explicitly returned buffer credits. InfiniBand is therefore natively lossless without reactive XOFF pause frames. Over Ethernet and IP, NVMe-o-TCP on TCP port 8009 and Parallel NFS run cleanly on lossy queues on TC4 without PFC. By contrast, RoCEv2 AI training on UDP port 4791 and NVMe-o-RDMA require a lossless queue with tuned PFC, ECN, and DCQCN thresholds.

```text
Storage & Interconnect Latency, Queueing, and Lossless Comparison (ADC Ch 9 & Table 9-2):
  - Local PCIe Gen5 x16 Bus:    32 GT/s x16 delivers ~63 GB/s one-way (~100 ns local NVMe SSD access latency) to drive 400 Gbps NICs at line rate
  - Native InfiniBand Fabric:   ~300 ns switch latency | Up to 16 Virtual Lanes (VLs; 8-12 workload queues) | 1 credit = 64 B in LLH (CBFC) | 16-bit LID = 48,000 nodes
  - AI Ethernet DCB Fabric:     ~800 ns switch latency (700-900 ns port-to-port) | 8 priorities / TCs | Reactive PFC (802.1Qbb) + ETS (802.1Qaz) + DCQCN (ECN)
  - Storage Protocol Matrix:
    * Parallel NFS ((P)NFS):    Runs over TCP/IP on lossy queue (TC4, Priority 4); no PFC required
    * NVMe-o-TCP (TCP 8009):    Uses IC Req PDU, CapsuleCmd (opcode 0x01), CapsuleResp, H2CData (0x03), C2HData (0x04) with 0x01 write & 0x02 read; lossy queue (TC4)
    * NVMe-o-RDMA & RoCEv2 AI:  Uses UDP 4791; requires lossless queue (PFC + ECN/DCQCN) with workload-specific threshold profiles
```

---

## 5. End-to-end consistency, configuration drift detection, and the 6-layer production validation plan

### 5.1 Hop-by-hop drift analysis: how a single `trust: pcp` port breaks RoCE silently

The fastest way to trigger a multi-hour AI training incident is to allow a single port along a multi-hop path to drift from the approved QoS mapping. Ping and basic TCP checks continue to succeed, so no link-down or routing alarm fires while collective throughput collapses.

Consider the three-step diagnostic trace from our production case study (`trace_end_to_end_qos_path` in `code/part12/dcb_qos_ai.py`). First, we verify what the source GPU host puts on the wire at `ens1f0` from `10.20.4.15` to `10.20.8.5`.

```text
# (untested here)
$ tcpdump -i eth0 -c1 -v host 10.20.8.5 and udp port 4791
IP (tos 0xb8, ttl 64, ...) 10.20.4.15.51422 > 10.20.8.5.4791: UDP, length 1200
```

Here `tos 0xb8` decodes to DSCP 46 Expedited Forwarding. The source adapter is marking packets as intended. Second, we verify what the source leaf switch `swp4` believes about this marking.

```text
# (untested here)
$ mlnx_qos -i swp4
Priority trust state: dscp
DSCP to priority mapping:
        dscp    0-7  8-15  ...  40-47  48-55  56-63
        prio     0     0   ...    3      0      0
```

Port `swp4` is in `Priority trust state: dscp` and maps bucket `40-47` to Priority 3, the lossless RoCE class. Third, we inspect the far-side destination leaf switch `swp19` where drift occurred.

```text
# (untested here)
$ mlnx_qos -i swp19
Priority trust state: pcp        <- DRIFT: ignores IP DSCP entirely
PCP to priority mapping:
        pcp      0   1   2   3   4   5   6   7
        prio     0   0   0   0   0   0   0   0    <- untagged L3 frames default to priority 0
```

Port `swp19` is configured with `Priority trust state: pcp`, and the routed IP packet has no 802.1Q VLAN tag. As a result, `swp19` classifies every arriving RoCEv2 frame into Priority 0 Best Effort. Only when we inspect per-priority queue drop and pause counters on `swp19` does the smoking gun appear.

```text
# (untested here)
$ ethtool -S swp19 | egrep "rx_prio0_discard|rx_pfc_prio3"
     rx_prio0_discard:        18420     <- 18,420 RoCE packets dropped in lossy priority 0
     rx_pfc_prio3:            0         <- lossless priority 3 never even sees the traffic
```

```mermaid
flowchart TB
    SoT["Versioned Source of Truth\n(YAML/JSON QoS Schema)"] --> H["Host / ConnectX Profile\n(mlnx_qos, dcb, mlxconfig)"]
    SoT --> L["Leaf Switch Policy\n(Ingress Trust, ETS, PFC)"]
    SoT --> S["Spine Switch Policy\n(DSCP Trust, ECN, PFC)"]
    SoT --> V["Automated Compliance Tests\n(6-Layer Validation Plan)"]
    V --> E["Expected Class, Queue,\nand Counter Deltas"]
    DRIFT["Manual Per-Port Exception\n(e.g. swp19 trust: pcp)"] -.->|"Mismatch Detected:\nrx_prio0_discard = 18,420"| E
```

| Hop / Role in Source-of-Truth Schema | Ingress Trust State | Expected DSCP -> Priority | Expected Egress TC & TSA | Expected PFC / ECN State | Primary Verification Counter |
|---|---|---|---|---|---|
| **GPU Host NIC (`ens1f0` / `mlx5_0`)** | `dscp` | DSCP 26/46 -> Prio 3; DSCP 48 -> Prio 6 | TC3 (`dwrr 50%`), TC6 (`strict`) | PFC ON (Prio 3), DCQCN ON | `tx_prio3_packets`, `np_cnp_sent`, `rp_cnp_handled` |
| **Source Leaf (`leafA_swp4`)** | `dscp` | `24-31` / `40-47` -> Prio 3 | TC3 (`dwrr 50%`), TC0 (`dwrr 10%`) | PFC ON (Prio 3), ECN ON | `rx_prio3_packets`, `tx_pfc_prio3`, `rx_ecn_marked_prio3` |
| **Transit Spine (`spine1_swp1`)** | `dscp` | `24-31` / `40-47` -> Prio 3 | TC3 (`dwrr 50%`), TC6 (`strict`) | ECN ON (PFC per design) | `rx_ecn_marked_prio3`, `tx_prio3_packets` |
| **Destination Leaf (`leafB_swp19`)** | `dscp` (Drifted: `pcp`) | Expected Prio 3 (Drifted: Prio 0) | Expected TC3 (Drifted: TC0) | Expected PFC ON (Drifted: Lossy) | **`rx_prio0_discard` (18,420 drops) vs `rx_pfc_prio3` (0)** |

### 5.2 The 6-layer production QoS validation plan

A QoS configuration that compiles in a switch template but has never been tested under simultaneous multi-class contention is not a production policy. Validate every AI fabric release across six layers before admitting training jobs.

First, verify classification by injecting marked test traffic across RoCE, storage, CNP, and best-effort classes. Assert that per-priority counters increment on the exact intended queue at every hop. Second, verify control-plane isolation under RoCE saturation by driving bounded contention on Priority 3. Prove that management traffic on Priority 0 or Priority 2 experiences zero pause frames and flat SSH or BGP latency. Third, verify simultaneous multi-class ETS service behavior. Run concurrent RoCE, storage, and best-effort generators through a shared bottleneck uplink to confirm DWRR minimum shares without strict-priority starvation.

Fourth, verify closed-loop congestion feedback by confirming that ECN marks on TC3 generate CNPs on TC6 and that sender adapters throttle cleanly. Fifth, verify failure and reroute persistence by simulating a planned uplink drain. Confirm that alternate paths preserve identical trust, ETS, ECN, and PFC profiles. Sixth, correlate switch queue counters with `nccl-tests` or `ib_write_bw`, and audit host PCIe link width, NUMA locality, and cluster manager interface priorities.

```text
Layer 6 Host Topology, PCIe, & Cluster Manager Audit Metrics (V9 Ch 8, Ch 9, Labs 01-04, BCM11 Ch 3):
  - Lab 01-03 Host Baseline & 60 s Contention (ens1f0, 10.20.4.15 -> 10.20.8.5 via 10.20.0.1, MTU 9000, 400000Mb/s):
    * Topology: nvidia-smi topo -m -> GPU0-NIC0 PIX, GPU1-NIC1 PIX, GPU0-GPU1 NV18
    * Baseline Counters (2026-08-07T14:32:15Z): rx_packets = 1,024,567 | rx_bytes = 892,481,382,400 | tx_bytes = 481,029,120,384 | fec_corrected_blocks = 412 | fec_uncorrected_blocks = 0
    * 60 s Contention (2026-08-07T14:35:22Z -> 14:36:30Z): rx_prio3_packets 102,314 -> 51,234,892 (delta 51,132,578) | tx_prio3_packets 89,621 -> 48,901,234 (delta 48,811,613) | rx_ecn_marked_prio3 = 47,829 | rx_pfc_prio3 = 412 | tx_pfc_prio3 = 14 | Sender A (89.2 Gbps) + Sender B (87.1 Gbps) = 176.3 Gbps
  - PCIe Downgrade Trap (V9 Ch 8 lspci -s 41:00.0 -vv):
    * LnkCap: Speed 32GT/s, Width x16 (PCIe Gen5 x16 ~63 GB/s) vs LnkSta: Speed 16GT/s (downgraded), Width x8 (PCIe Gen4 x8 = 16 GB/s < 25 GB/s required for 200 GbE)
  - BlueField DPU Boot Race (V9 Ch 9):
    * Switch port swp14 up 100G full RoCE-compute, but openvswitch-policy-load.service exited status=1/FAILURE at 09:14:02 UTC, leaving host enp1s0f0np0 DOWN/DORMANT
  - NVIDIA Base Command Manager 11 (cmsh) Interface Priority & mlxconfig Precedence (BCM11 Ch 3):
    * onnetworkpriority ladder (0..4294967295): Bridge = 80, Bond = 70, Physical = 60, VLAN = 50, Alias = 40, Tunnel = 30, Netmap = 20, BMC = 10
    * Persistent MLX_ extra_values precedence: category.extra_values < node.extra_values < interface.extra_values
```

---

## Commands and configurations that matter

### 1. Host NIC (ConnectX) QoS, `iproute2 dcb`, `lldptool`, and `mlxconfig` commands

```bash
# (untested here) Inspect and configure DSCP trust, PFC on Priority 3, and ETS weights via mlnx_qos
mlnx_qos -i ens1f0
sudo mlnx_qos -i ens1f0 --trust dscp --pfc 0,0,0,1,0,0,0,0 \
  --tsa dwrr,dwrr,dwrr,dwrr,dwrr,dwrr,strict,dwrr \
  --tcbw 10,0,10,50,30,0,0,0

# (untested here) Set default RoCEv2 ToS/DSCP marking (106 = 0x6a -> DSCP 26 + ECT(0)) via sysfs / cma_roce_tos
cma_roce_tos -d mlx5_0 -t 106
cat /sys/class/infiniband/mlx5_0/tc/1/traffic_class

# (untested here) Standard Linux iproute2 dcb tool: inspect PFC, ETS, and Application Priority TLVs
dcb pfc show dev ens1f0
dcb ets show dev ens1f0
dcb app show dev ens1f0
sudo dcb app add dev ens1f0 dgram-port-prio 4791:3

# (untested here) Inspect IEEE 802.1Qaz DCBX TLVs advertised/received over LLDP (EtherType 0x88CC)
lldptool -t -i ens1f0 -V ETS-CFG
lldptool -t -i ens1f0 -V ETS-REC
lldptool -t -i ens1f0 -V PFC
lldptool -t -i ens1f0 -V APP

# (untested here) Verify PCIe link speed/width (Gen5 32GT/s x16 vs downgraded Gen4 16GT/s x8) & GPU locality
lspci -s 41:00.0 -vv | egrep "LnkCap|LnkSta"
nvidia-smi topo -m
rdma link show
ibv_devinfo -d mlx5_0 -i 1

# (untested here) NVIDIA Base Command Manager (BCM 11) persistent ConnectX policy via cmsh
cmsh -c "device; mlxconfig node001 --adapters"
cmsh -c "category use gpu; set -e MLX_link_type_p1 ETH; commit"
cmsh -c "device; mlxconfig node001 --desired"
```

### 2. Switch port (Cumulus Linux / Spectrum / SONiC) and packet-capture verification commands

```bash
# (untested here) Verify wire DSCP marking (tos 0xb8 -> DSCP 46; tos 0x6a -> DSCP 26 + ECT(0))
sudo tcpdump -i ens1f0 -c 5 -v host 10.20.8.5 and udp port 4791

# (untested here) Check switch port trust state, DSCP-to-priority map, TSA scheduler, and PFC counters
mlnx_qos -i swp4
mlnx_qos -i swp19
mlnx_qos -i swp4 | grep -A5 "tsa"

# (untested here) Capture timestamped per-priority packet, drop, ECN, and PFC deltas (never reset shared counters)
date -u && ethtool -S ens1f0 | egrep "rx_bytes|tx_bytes|fec_corrected|fec_uncorrected|ecn_marked|pfc_prio|prio3_packets|prio0_discard"
ethtool -S swp19 | egrep "rx_prio0_discard|rx_pfc_prio3|rx_ecn_marked_prio3"

# (untested here) SONiC / Cumulus CLI equivalents for queue, PFC, watermark, and watchdog inspection
show qos interface swp4
show pfc counters
show queue counters
show pfcwd stats
```

---

## How it fails

| # | Failure mode | Production symptom | Root cause & counter signature | Definitive fix & prevention |
|---|---|---|---|---|
| **1** | **Silent ingress trust-mode drift (`trust: pcp` on a routed port)** | `ping` and TCP work normally, PFC is enabled on Priority 3 everywhere, yet `nccl-tests` / RDMA jobs suffer high retries (`RETRY_EXC_ERR`) and low throughput. | Source (`ens1f0`, `tos 0xb8` / DSCP 46) and first-hop leaf (`swp4`, `trust: dscp`) map traffic to Priority 3, but destination leaf (`swp19`) is set to `Priority trust state: pcp`. Untagged L3 packets have no 802.1Q PCP and fall into Priority 0: `rx_prio0_discard: 18420` while `rx_pfc_prio3: 0`. | Set `mlnx_qos -i swp19 --trust dscp`; enforce automated source-of-truth compliance checks (`trace_end_to_end_qos_path`) with marked test probes across every hop. |
| **2** | **Management and control-plane starvation by `strict` RoCE scheduling** | SSH hangs, Kubernetes node heartbeats fail, or BGP sessions flap whenever a large multi-node training burst runs, even with `rx_pfc_prio0 = 0`. | `mlnx_qos -i swp4` shows `tc: 1` (carrying Priority 3 RoCE) configured as `tsa: strict` (`ratelimit: unlimited`), while `tc: 0` (Priority 0 management) is `tsa: dwrr, weight: 5`. Sustained 400 Gbps RoCE bursts keep `tc: 1` permanently non-empty, giving `tc: 0` 0.0 Gbps. | Move RoCE (TC3) to `tsa: dwrr` (e.g., 50% or 95% ETS weight) and give Infrastructure/Control (TC2 or TC0) a guaranteed ETS minimum share (5%–10%); reserve `strict` (TSA 0) only for rate-capped CNP/link control (TC6). |
| **3** | **Storage misses its expected bandwidth share under compute load** | Checkpoint writes (NVMe-o-TCP on port 8009 or parallel FS) collapse when GPU collectives start, despite ETS appearing configured. | Either storage packets are unmarked (DSCP 0) and land in TC0 (10%) instead of TC4 (30%), RoCE is scheduled `strict` ahead of `dwrr` storage, or an architect promised 30% ETS on an oversubscribed spine cut without testing simultaneous load. | Verify storage DSCP 18 (`tos 0x4a` -> Priority 4 / TC4) end to end, ensure both TC3 and TC4 run under `dwrr` (TSA 2), and benchmark concurrent RoCE + storage flows under realistic contention. |
| **4** | **DCBX Willing bit conflict or static PFC/Application TLV mismatch** | After a host reboot or `lldpad` restart, the NIC either disables PFC on Priority 3 or moves RoCE (UDP 4791) to Priority 0 or 4. | Both host and switch advertise Willing = 1 (`CONFLICT_BOTH_WILLING`), or both use Willing = 0 (`BOTH_LOCAL_STATIC`) with drifted local profiles (`host PFC=(4,)` vs `switch PFC=(3,)`). | Use either `Host Willing=1 / Switch Willing=0` (`SWITCH_PEER`) or `Host Willing=0 / Switch Willing=0` (`BOTH_LOCAL_STATIC`) generated from one versioned schema, and alert on any `lldptool` / `dcb` mismatch. |
| **5** | **Buffer pool exhaustion from enabling PFC on too many priorities** | TCP storage, Prometheus scrapes, and CNP packets suffer heavy tail drops even at moderate link utilization (40–60%). | Enabling PFC on 4 priorities (`4 x 65,536 B = 262,144 B`) locks 100.0% of the port receive buffer in dedicated lossless headroom reservations, leaving 0 B (0.0%) for shared lossy queues (`BUFFER_EXHAUSTED_TOO_MANY_LOSSLESS_CLASSES`). | Restrict PFC to **one** lossless class (Priority 3 for RoCEv2 compute, 25.0% = 65,536 B), leaving 75.0% (196,608 B) in the shared lossy pool (or at most two classes if NVMe-o-RDMA shares the fabric). |
| **6** | **BlueField DPU boot-policy race or ConnectX PCIe/rail misselection** | Switch port (`swp14`) reports UP 100G/400G with zero errors, yet host interface (`enp1s0f0np0`) stays DOWN/DORMANT, or `ib_write_bw` drops from 392 Gbps (2.1 s) to 156 Gbps (8.2 s, 24 `RETRY_EXC_ERR`s). | On a BlueField DPU in ECPF mode, `openvswitch-policy-load.service` on the Arm subsystem failed during boot. Alternatively, on a dual-rail host (Lab 04), selecting `-d mlx5_1` (`ens1f1`, wrong NUMA/GID) or seating a NIC in a downgraded PCIe Gen4 x8 slot (`16 GB/s < 25 GB/s` for 200 GbE) bottlenecks the host path. | Audit all three DPU layers (switch uplink, Arm policy service, host representor) before admitting jobs, and run preflight checks for `lspci` (`LnkCap == LnkSta`), `nvidia-smi topo -m` (`PIX`), and `rdma link show`. |

---

## Hands-on lab

### Venue and scope

- **Venue:** Any Linux environment with Python 3.10 or newer. It runs deterministically on a laptop, CPU VM, or Nebius GPU node using the standard library only. No switch hardware is required for the simulator, while hardware CLI commands above are marked `(untested here)`.
- **Code files:** `code/part12/dcb_qos_ai.py` for the core model and `code/part12/dcb_qos_ai_lab.py` for the 30 automated self-checks.

### Step 1 — Run the 30-check DCB and QoS verification suite

Execute `code/part12/dcb_qos_ai_lab.py` to validate IP ToS byte encoding and decoding and the five-class AI fabric QoS model. The script also verifies IEEE 802.1Qaz ETS bandwidth allocation, DCBX TLV negotiation over LLDP, switch port buffer pool carving, and hop-by-hop trust-boundary drift detection.

```bash
python3 -B code/part12/dcb_qos_ai_lab.py
```

**Expected output (tested here):**

```text
=== Chapter 12.5 Lab: Data Center Bridging and QoS for AI ===
  [PASS] V9 Ch 6 tcpdump decode: tos 0xb8 (184) -> DSCP 46 (EF, 0xb8 >> 2 == 46), ECN 00, mlnx_qos bucket 40-47
  [PASS] RoCEv2 DSCP 26 + ECT(0) (10): (26 << 2) | 2 == 106 (0x6a), decodes to DSCP 26 in bucket 24-31
  [PASS] RoCEv2 CE-marked ToS 0x6b (107) and CNP DSCP 48 + ECT(1) ToS 0xc1 (193) in bucket 48-55
  [PASS] Storage DSCP 18 (AF21) + ECT(0): (18 << 2) | 2 == 74 (0x4a), mlnx_qos bucket 16-23
  [PASS] AI fabric QoS class model: DWRR weights sum to 100% (10+10+50+30), exactly 1 lossless class (TC3), and 1 strict-priority CNP class (TC6 capped at 20 Gbps)
  [PASS] 64-entry DSCP-to-Priority table: DSCP 0/10 -> Prio 0, DSCP 18 -> Prio 4 (Storage), DSCP 24/34 -> Prio 2 (Control), DSCP 26/46 -> Prio 3 (RoCE), DSCP 48/56 -> Prio 6 (CNP)
  [PASS] IEEE 802.1Qaz Transmission Selection Algorithm (TSA) IDs: Strict=0, CBShaper=1, ETS/DWRR=2, Vendor=255
  [PASS] ETS 400G full contention (10G CNP strict + 390G DWRR split 10:10:50:30): TC6=10G, TC0=39G, TC2=39G, TC3=195G, TC4=117G, 0 starved
  [PASS] ETS work-conserving 2-class contention (TC3 50% vs TC4 30% on 400G): unused 20% redistributed in 5:3 ratio -> TC3=250.0 Gbps, TC4=150.0 Gbps
  [PASS] ETS work-conserving single-class burst: TC4 (30% ETS minimum) gets full 400.0 Gbps when other queues are empty
  [PASS] V9 Ch 6 Scenario 2 starvation: TC1 (Prio 3) on `strict` takes 400.0 Gbps and starves TC0 (`dwrr` weight 5 -> 0.0 Gbps); moving to ETS 95/5 guarantees TC0 20.0 Gbps
  [PASS] CNPS Ch 8 CBWFQ on 1,024 Kbps link (ratio 2:1:1:4 across 8 clock cycles): AF41=256 Kbps, AF31=128 Kbps, AF21=128 Kbps, Default=512 Kbps
  [PASS] CNPS Ch 8 LLQ under congestion (1,024 Kbps link, 512 Kbps LLQ cap): 9x64=576 Kbps drops 64 Kbps; 12x64=768 Kbps drops 256 Kbps; 32x16=512 Kbps drops 0 Kbps
  [PASS] CNPS Ch 8 LLQ uncongested link (640 Kbps LLQ + 300 Kbps other <= 1,024 Kbps, <= 384 Kbps remaining): all 640 Kbps passes without policing drops
  [PASS] CNPS Ch 8/17 & Handbook 2.19 serialization delay: on 100 Mbps, 64B=0.00512 ms (0.05 ms in CNPS), 1500B=0.12 ms, 9000B=0.72 ms (14x 0.05 ms); on 400 Gbps, 9000B=180.0 ns and 64B=1.28 ns
  [PASS] IEEE 802.1Qaz DCBX over LLDP constants: EtherType 0x88CC, MAC 01:80:C2:00:00:0E, OUI 00:80:C2, subtypes 9 (ETS Cfg), 10 (ETS Rec), 11 (PFC), 12 (App Prio), RoCE UDP 4791, NVMe/TCP 8009
  [PASS] DCBX Negotiation (Host Willing=1, Switch Willing=0): Host adopts Switch Priority 3 PFC, ETS weights (10/10/50/30), and UDP 4791 -> Prio 3 cleanly
  [PASS] DCBX Static Automation Mode (Host Willing=0, Switch Willing=0, matching source of truth): BOTH_LOCAL_STATIC healthy
  [PASS] DCBX Static Drift Detection: catches PFC mismatch (Prio 4 vs 3), ETS weight mismatch, App TLV 4791 mismatch, and Trust mode mismatch (pcp vs dscp)
  [PASS] DCBX Willing Conflict: when both Host and Switch set Willing=1, evaluator flags CONFLICT_BOTH_WILLING
  [PASS] Buffer Pool Carving (1 lossless class Prio 3 on 262,144B port): 65,536B (25.0%) lossless (XOFF=49,152B, XON=32,768B, headroom=16,384B), 196,608B (75.0%) lossy
  [PASS] Buffer Pool Carving (2 lossless classes Prio 3 + Prio 4): 131,072B (50.0%) lossless reserved, 131,072B (50.0%) remaining for lossy classes
  [PASS] Buffer Pool Carving Failure (4 lossless classes): 262,144B (100.0%) consumed, 0B (0.0%) left for lossy TCP/control/CNP queues -> BUFFER_EXHAUSTED_TOO_MANY_LOSSLESS_CLASSES
  [PASS] End-to-End QoS Contract Verified: DSCP 46 (tos 0xb8) untagged L3 frame stays in lossless Priority 3 across host_ens1f0, leafA_swp4, spine1_swp1, and leafB_swp19
  [PASS] V9 Ch 6 Scenario 1 Trust-Mode Drift on swp19 (`trust: pcp`): untagged L3 RoCE packet falls to Priority 0 at leafB_swp19 (`rx_prio0_discard=18,420`, `rx_pfc_prio3=0`)
  [PASS] CNPS Ch 8 Fig 8-3 & V9 Ch 6 Fig 9.6.1 Untrusted Ingress Rewrite: leafA_swp4 rewrites DSCP 26 -> 0, forcing all downstream hops into Priority 0
  [PASS] ADC Ch 9 Storage & QoS metrics: PCIe Gen5 32 GT/s x16 (~63 GB/s, 100 ns local SSD), IB ~300 ns (16 VLs, 64B credits, 48,000 LIDs), Ethernet ~800 ns (700-900 ns), NVMe/TCP port 8009
  [PASS] BCM11 Ch 3 interface priority ladder (Bridge=80, Bond=70, Physical=60, VLAN=50, Alias=40, Tunnel=30, Netmap=20, BMC=10) & V9 Ch 8 PCIe Gen4 x8 (16 GB/s < 25 GB/s for 200GbE)
  [PASS] V9 Labs 01-03 Baseline & 60s Contention: MTU 9000, 400000Mb/s, fec_corrected=412, fec_uncorrected=0, rx_prio3 delta=51,132,578, tx_prio3 delta=48,811,613, ECN=47,829, RX PFC=412, TX PFC=14, 89.2+87.1=176.3 Gbps
  [PASS] V9 Lab 04 Evidence Ladder: mlx5_0 (392 Gbps in 2.1s, 0 retries) vs mlx5_1 (156 Gbps in 8.2s, 2.51x slower, 24 RETRY_EXC_ERR, rx_ecn_marked_prio3=142)

Summary: 30 passed, 0 failed out of 30 checks.
```

---

## Common first mistakes

1. **Reading `tcpdump` hex `tos` values as decimal DSCP numbers:** Seeing `tos 0xb8` or `tos 0x6a` in `tcpdump -v` and forgetting to right-shift by 2 bits. Always strip the lower 2 ECN bits before looking up the `mlnx_qos` DSCP bucket.
2. **Leaving switch ports in `Priority trust state: pcp` on a routed Layer 3 fabric:** Routed IP packets carry no 802.1Q VLAN tag. A `trust: pcp` switch port therefore silently maps DSCP 26 or DSCP 46 RoCEv2 packets into lossy Priority 0. That drift causes `rx_prio0_discard` drops while `rx_pfc_prio3` remains zero.
3. **Scheduling RoCEv2 data on TC3 as `tsa: strict` instead of `tsa: dwrr`:** An unpoliced strict RoCE queue consumes 100 percent of a 400 Gbps link during collective bursts and completely starves DWRR management queues. Reserve strict priority for low-volume, rate-capped CNP feedback on TC6.
4. **Treating an ETS weight as a hard static reservation or a hard bandwidth ceiling:** ETS under DWRR is work-conserving. An idle class reserves zero bandwidth, and a single active class can legitimately burst to 100 percent of the link when other queues are empty.
5. **Enabling PFC on three or four priorities "just in case":** Every lossless priority carves out dedicated port buffer and flight-time headroom. Enabling too many lossless classes starves lossy TCP, storage, and control queues of shared burst buffer.
6. **Resetting live switch or NIC counters during an incident instead of computing timestamped deltas:** Clearing shared counters destroys historical evidence for other operators and monitoring collectors. Always capture UTC timestamps and subtract baseline snapshots.

---

## Exercises

1. **IP ToS byte encoding, decoding, and `mlnx_qos` bucket mapping:**
   Using the bit-shift equation from Section 2.1, calculate the decimal and hexadecimal ToS byte for Storage AF21 with ECT(0). Repeat the calculation for RoCEv2 AF31 with ECT(0) and with CE, RoCEv2 EF with Not-ECT, and a RoCEv2 CNP on CS6 with ECT(1). Then state which `mlnx_qos` 8-value DSCP bucket and 802.1p priority each packet maps to in our five-class model.

2. **IEEE 802.1Qaz ETS work-conserving bandwidth allocation and `strict` starvation:**
   Consider a 400.0 Gbps switch egress port configured with TC6 strict and four DWRR classes: TC0 at 10%, TC2 at 10%, TC3 at 50%, and TC4 at 30%. Compute the exact bandwidth allocated to each class under full five-class contention, two-class contention between TC3 and TC4, and single-class load on TC4. Then explain what happens to `tc: 0` when `tc: 1` is set to `tsa: strict` versus `tsa: dwrr` at a 95:5 weight ratio.

3. **CBWFQ clock-cycle scheduling, LLQ policing math, and serialization jitter:**
   On a 1,024 Kbps WAN link with CBWFQ minimums of 256, 128, 128, and 512 Kbps, reduce the bandwidth ratio across 8 clock cycles. Trace which classes transmit on Cycles 2, 4, and 8 when AF41 has 1 packet, AF21 has 0 packets, and unclassified traffic has 3 packets. Next, calculate the LLQ policer drops for 9, 12, 32, and 10 VoIP calls under the 512 Kbps cap. Finally, compute the serialization delay of a 9,000-byte frame versus a 64-byte frame at 100 Mbps and 400 Gbps.

4. **IEEE 802.1Qaz DCBX TLV negotiation and Willing bit state machine:**
   State the LLDP EtherType, destination multicast MAC address, IEEE 802.1 OUI, and the four DCBX TLV subtype numbers. Identify which TLVs are symmetric versus asymmetric. Then determine the operational state source and mismatch list across the four Willing bit combinations in `evaluate_dcbx_negotiation`.

5. **Switch port buffer pool carving across lossless and lossy classes:**
   A leaf switch port has 262,144 bytes of port receive buffer, and each lossless priority requires 65,536 bytes. Compute the total lossless bytes reserved, remaining lossy bytes, percentage split, and `evaluate_buffer_pool_carving` verdict for 1, 2, and 4 lossless priorities.

6. **End-to-end hop-by-hop drift diagnosis and the evidence ladder:**
   Trace an untagged routed RoCEv2 packet across `host_ens1f0`, `leafA_swp4`, `spine1_swp1`, and `leafB_swp19` when `leafB_swp19` is configured with `Priority trust state: pcp` instead of `dscp`. Explain why `ethtool -S swp19` shows 18,420 discards on Priority 0 and 0 pauses on Priority 3. Then contrast Lab 03 bounded contention against Lab 04 rail misselection.

---

## Interview angles

1. **"Why can a DSCP value be 100% correct in `tcpdump` at the sending GPU host and still land in a lossy best-effort queue at the far-side leaf switch?"**
   - *Strong answer:* `tcpdump` at the sender only proves the source adapter marked the IP header. Classification is an end-to-end hop-by-hop contract where every switch ingress port independently decides whether to trust DSCP, trust 802.1p PCP, or rewrite markings to zero. If the destination leaf port `swp19` drifted to `Priority trust state: pcp` on a routed L3 link, frames carry no 802.1Q VLAN tag and have no PCP value. Port `swp19` ignores DSCP and drops the packet into Priority 0 lossy best effort. Consequently, `rx_prio0_discard` climbs while `rx_pfc_prio3` stays zero.

2. **"What is the exact operational difference between an IEEE 802.1Qaz ETS bandwidth percentage and a hard bandwidth reservation?"**
   - *Strong answer:* An ETS percentage under TSA 2 DWRR is a work-conserving minimum share objective under contention, not a static partition or rate cap. When multiple classes contend simultaneously, the scheduler divides bandwidth remaining after strict-priority queues in proportion to configured weights. When other classes are idle, a 30 percent storage class can burst to the full 400 Gbps link rate.

3. **"How do you prove empirically—not just by reading config files—that PFC on the RoCE class will not stall cluster management or BGP during a collective burst?"**
   - *Strong answer:* Run a controlled contention test that deliberately saturates Priority 3 enough to generate sustained ECN marks and PFC pauses. While `rx_pfc_prio3` increments, assert two pieces of evidence simultaneously. First, `rx_pfc_prio0` and `rx_pfc_prio2` must stay at zero, proving PFC is scoped only to Priority 3. Second, management-plane RTT and throughput must remain flat, proving that Priority 3 is scheduled via DWRR rather than `tsa: strict`.

4. **"Why is QoS not a substitute for tenant security isolation or fabric capacity planning?"**
   - *Strong answer:* QoS answers which queue a frame enters and how queues share a congested link. Tenant isolation answers who is authorized to send traffic or reach a peer. An untrusted host can forge DSCP 26 unless an ingress trust boundary or BlueField DPU embedded switch normalizes markings. Capacity planning answers whether there is enough bisection bandwidth for aggregate demand, since QoS cannot manufacture bandwidth on an oversubscribed cut.

---

## Checkpoint questions (20)

<details><summary>`&lt;strong>`1. Why do AI Ethernet fabrics avoid creating eight separate lossless QoS classes even though IEEE 802.1p and IEEE 802.1Qbb support Priorities 0..7?`&lt;/strong>`</summary>

Every lossless PFC-enabled priority requires a dedicated per-port buffer reservation and XOFF flight-time headroom. On a 262,144 B port buffer where each lossless class reserves 65,536 B, enabling PFC on 4 priorities consumes 100.0 percent of the buffer. That leaves 0 B for lossy TCP, storage, control, and CNP queues while multiplying configuration drift and head-of-line blocking risks.
</details>

<details><summary>`&lt;strong>`2. In `tcpdump -i eth0 -c1 -v`, an IP packet displays `tos 0xb8`. How do you decode the 6-bit DSCP value and 2-bit ECN codepoint, and which `mlnx_qos` bucket does it match?`&lt;/strong>`</summary>

Hexadecimal `0xb8` equals 184 in decimal or `10111000` in binary. Right-shifting by 2 bits gives DSCP 46 for Expedited Forwarding, and masking the low 2 bits gives ECN 0 for Not-ECT. In `mlnx_qos`, DSCP 46 falls in the `40-47` bucket.
</details>

<details><summary>`&lt;strong>`3. What hexadecimal ToS byte values appear on the wire for a RoCEv2 data packet marked DSCP 26 with ECT(0), the same packet after a switch marks CE, and a CNP marked DSCP 48 with ECT(1)?`&lt;/strong>`</summary>

```text
RoCEv2 DSCP 26 + ECT(0) (2): (26 << 2) | 2 = 104 + 2 = 106 = 0x6a (bucket 24-31)
RoCEv2 DSCP 26 + CE (3):     (26 << 2) | 3 = 104 + 3 = 107 = 0x6b (bucket 24-31)
RoCEv2 CNP DSCP 48 + ECT(1): (48 << 2) | 1 = 192 + 1 = 193 = 0xc1 (bucket 48-55)
```
</details>

<details><summary>`&lt;strong>`4. What are the five traffic classes in our standard AI Ethernet fabric QoS model, including their DSCP markings, 802.1p priorities, TSA scheduling modes, and ETS weights?`&lt;/strong>`</summary>

```text
1. TC0 (Best Effort, Priority 0):              DSCP 0 / 10, lossy, dwrr (TSA 2), 10%
2. TC2 (Infrastructure & Control, Priority 2): DSCP 24 / 34, lossy, dwrr (TSA 2), 10%
3. TC3 (RoCEv2 AI Compute, Priority 3):        DSCP 26 / 46 (UDP 4791), lossless (PFC + ECN), dwrr (TSA 2), 50%
4. TC4 (Storage & Checkpointing, Priority 4):  DSCP 18 (AF21, tos 0x4a w/ ECT(0), NVMe-o-TCP port 8009), lossy (ECN ON), dwrr (TSA 2), 30%
5. TC6 (CNP Feedback & Control, Priority 6):   DSCP 48 / 56 (CNP opcode 0x81), lossy, strict (TSA 0) policed at 20.0 Gbps on 400 Gbps
```
</details>

<details><summary>`&lt;strong>`5. What are the four IEEE 802.1Qaz Transmission Selection Algorithm (TSA) identifiers?`&lt;/strong>`</summary>

- **0:** Strict Priority (`strict` / LLQ).
- **1:** Credit-Based Shaper (`cbs`).
- **2:** Enhanced Transmission Selection (`ets` / `dwrr` / CBWFQ).
- **255:** Vendor-Specific.
</details>

<details><summary>`&lt;strong>`6. On a 400.0 Gbps link with TC6 (strict, 10.0 Gbps offered) and DWRR weights TC0 = 10%, TC2 = 10%, TC3 = 50%, TC4 = 30%, how much bandwidth does each class receive under full contention versus two-class contention?`&lt;/strong>`</summary>

```text
All 5 classes contending:       TC6 = 10.0 Gbps; remaining 390.0 Gbps splits 10:10:50:30 -> TC0 = 39.0 Gbps, TC2 = 39.0 Gbps, TC3 = 195.0 Gbps, TC4 = 117.0 Gbps
Only TC3 (50%) & TC4 (30%) on:  Unused 20% redistributed in 50:30 = 5:3 ratio -> TC3 = 250.0 Gbps, TC4 = 150.0 Gbps
```
</details>

<details><summary>`&lt;strong>`7. Why did cluster management (`tc: 0`, Priority 0) stall during training bursts when `mlnx_qos -i swp4` showed `tc: 1` (Priority 3, RoCE) set to `tsa: strict` and `tc: 0` set to `tsa: dwrr, weight: 5`?`&lt;/strong>`</summary>

In strict-priority scheduling with no rate limit, the scheduler always services `tc: 1` before any DWRR queue. During a sustained 400.0 Gbps RoCE burst, `tc: 1` never empties, starving `tc: 0` at 0.0 Gbps regardless of its DWRR weight. Moving `tc: 1` to DWRR with weight 95 guarantees `tc: 0` with weight 5 at least 20.0 Gbps under contention.
</details>

<details><summary>`&lt;strong>`8. On a 1,024 Kbps WAN link with an LLQ cap of 512 Kbps, what happens when a 9th or 12th 64 Kbps VoIP call joins under congestion, and when can 10 calls pass with zero drops?`&lt;/strong>`</summary>

Under congestion, the LLQ policer treats the class as one aggregate stream. It drops 64 Kbps when 9 calls offer 576 Kbps and drops 256 Kbps when 12 calls offer 768 Kbps. Switching to a 16 Kbps codec lets 32 calls fit inside 512 Kbps with zero drops. If all other traffic stays at or below the remaining 384 Kbps when 10 calls offer 640 Kbps, the link is uncongested and all 640 Kbps passes without loss.
</details>

<details><summary>`&lt;strong>`9. Compare the wire serialization delay of a 9,000-byte jumbo frame and a 64-byte control/CNP frame at 100 Mbps versus 400 Gbps.`&lt;/strong>`</summary>

```text
At 100 Mbps:  9,000 B = 0.72 ms | 1,500 B = 0.12 ms | 64 B = 0.00512 ms (.05 ms with framing overhead in textbook models, 14x ratio)
At 400 Gbps:  9,000 B = 180.0 ns | 64 B = 1.28 ns (140.625x shorter)
```
</details>

<details><summary>`&lt;strong>`10. What EtherType, destination MAC, IEEE OUI, and TLV subtypes does IEEE 802.1Qaz DCBX use over LLDP?`&lt;/strong>`</summary>

```text
LLDP EtherType:       0x88CC | Destination MAC: 01:80:C2:00:00:0E | IEEE 802.1 OUI: 00:80:C2
Four DCBX Subtypes:   9 (ETS Configuration, asymmetric), 10 (ETS Recommendation, asymmetric), 11 (PFC Configuration, symmetric), 12 (Application Priority, e.g., UDP 4791 -> Priority 3)
```
</details>

<details><summary>`&lt;strong>`11. How do the Host Willing and Switch Willing bits interact in DCBX, and which two combinations are valid in production AI fabrics?`&lt;/strong>`</summary>

When Host Willing is 1 and Switch Willing is 0 (`SWITCH_PEER`), the host adapter adopts the authoritative switch port settings. When both are 0 (`BOTH_LOCAL_STATIC`), both sides are configured identically from a versioned source of truth and LLDP audits zero drift. Setting Host Willing to 0 with Switch Willing at 1 (`HOST_LOCAL`) or setting both to 1 (`CONFLICT_BOTH_WILLING`) is unsafe in production.
</details>

<details><summary>`&lt;strong>`12. On `swp12` (262,144 B total receive buffer, 65,536 B per lossless priority), compare the buffer split for 1, 2, and 4 lossless priorities.`&lt;/strong>`</summary>

```text
1 lossless priority (Priority 3):      65,536 B (25.0%) lossless (16,384 B headroom), 196,608 B (75.0%) lossy -> HEALTHY_BUFFER_CARVING
2 lossless priorities (Prio 3, 4):     131,072 B (50.0%) lossless, 131,072 B (50.0%) lossy -> HEALTHY_BUFFER_CARVING
4 lossless priorities (Prio 1..4):     262,144 B (100.0%) lossless, 0 B (0.0%) lossy -> BUFFER_EXHAUSTED_TOO_MANY_LOSSLESS_CLASSES
```
</details>

<details><summary>`&lt;strong>`13. Why does a Spectrum switch with a Fully Shared Buffer outperform a sliced-buffer switch during AI incast microbursts, and why can't a buffer solve sustained link oversubscription?`&lt;/strong>`</summary>

A Fully Shared Buffer pools internal switch memory dynamically. An overloaded port can borrow burst space from idle ports rather than dropping packets as soon as a fixed per-port slice fills. However, a buffer only absorbs transient arrival-rate mismatches during microbursts. If offered load structurally exceeds egress capacity over milliseconds or seconds, the buffer inevitably fills and triggers ECN, PFC, or drops.
</details>

<details><summary>`&lt;strong>`14. Why did `ethtool -S swp19` show `rx_prio0_discard: 18420` and `rx_pfc_prio3: 0` even though PFC was enabled on Priority 3 on every switch?`&lt;/strong>`</summary>

Running `mlnx_qos -i swp19` revealed `Priority trust state: pcp` while `swp4` used `Priority trust state: dscp`. Because the routed RoCEv2 IP packets had no 802.1Q VLAN tag, `swp19` ignored DSCP 46 and classified every RoCEv2 frame into Priority 0. PFC was disabled on Priority 0, so 18,420 packets were discarded.
</details>

<details><summary>`&lt;strong>`15. How do InfiniBand Virtual Lanes and Credit-Based Flow Control differ from Ethernet DCB, and what are the typical switch and PCIe latencies?`&lt;/strong>`</summary>

```text
InfiniBand:   Up to 16 VLs (8-12 workload queues), 48,000 LIDs (16-bit), proactive link-level CBFC (64 B per credit in LLH), ~300 ns switch latency
Ethernet DCB: 8 priorities/TCs, reactive PFC (802.1Qbb) + ETS (802.1Qaz) + DCQCN (ECN), ~800 ns (700-900 ns) switch latency
Local PCIe:   PCIe Gen5 32 GT/s x16 delivers ~63 GB/s one-way with ~100 ns local SSD latency
```
</details>

<details><summary>`&lt;strong>`16. Which AI storage protocols require a lossless Ethernet class (PFC + DCQCN) and which run over a lossy class (TC4)?`&lt;/strong>`</summary>

NVMe-o-RDMA over RoCEv2 on UDP port 4791 requires a lossless queue with PFC, ECN, and DCQCN. NVMe-o-TCP on TCP port 8009 and Parallel NFS use TCP reliability and run over a lossy queue on TC4 with 30 percent ETS and TCP ECN.
</details>

<details><summary>`&lt;strong>`17. What are the six layers of a production AI fabric QoS validation plan?`&lt;/strong>`</summary>

The six validation layers are Classification, Isolation, Service behavior, Feedback, Failure behavior, and Application plus host correlation. Together they verify hop-by-hop queue counters, management isolation under PFC, multi-class ETS shares, ECN-to-CNP sender throttling, failover persistence, and collective throughput.
</details>

<details><summary>`&lt;strong>`18. Why did a 200 GbE ConnectX adapter fail to reach line rate even though the switch fabric had zero ECN marks and zero PFC pauses?`&lt;/strong>`</summary>

Inspecting `lspci -s 41:00.0 -vv` showed `LnkCap: Speed 32GT/s, Width x16` for PCIe Gen5 x16. However, the slot negotiated `LnkSta: Speed 16GT/s (downgraded), Width x8` for PCIe Gen4 x8, topping out around 16 GB/s. Sustaining 200 GbE requires 25 GB/s of PCIe bandwidth, so the host PCIe slot bottlenecked the adapter before packets ever reached the switch.
</details>

<details><summary>`&lt;strong>`19. On a server equipped with a BlueField DPU in ECPF mode, why did the host interface (`enp1s0f0np0`) remain DOWN/DORMANT while the leaf switch port (`swp14`) showed `up 100G full RoCE-compute`?`&lt;/strong>`</summary>

A BlueField DPU introduces three independent layers: the external switch uplink `swp14`, the DPU Arm control plane and embedded switch, and the host-facing function `enp1s0f0np0`. During boot, `openvswitch-policy-load.service` on the BlueField Arm OS exited with `status=1/FAILURE` at `09:14:02 UTC`. That failure left the embedded switch without rules to bring up the host representor despite a healthy physical uplink.
</details>

<details><summary>`&lt;strong>`20. In NVIDIA Base Command Manager (`cmsh`), what is the default `onnetworkpriority` resolution ladder across interface types, and what is the precedence order for persistent `MLX_` `mlxconfig` extra values?`&lt;/strong>`</summary>

```text
onnetworkpriority ladder (0..4294967295): Bridge = 80, Bond = 70, Physical = 60, VLAN = 50, Alias = 40, Tunnel = 30, Netmap = 20, BMC = 10
Persistent MLX_ mlxconfig precedence:     category.extra_values < node.extra_values < interface.extra_values
```
</details>

---

## Sources and review notes

### Primary sources read in full for this chapter

All primary Volume 09 notes, labs, and textbook chapters mapped to Chapter 12.5 were read in full and verified against the 30-check lab suite.

```text
Primary Sources & Mapped Files (brief.py 12.5 & check_coverage.py 12.5):
  1. Author's Volume 09 Notes and Labs (nvidia-devops):
     - nvidia-zero-to-hero/volume-09/chapter-06-data-center-bridging-and-qos.md
       * Highway lanes analogy (Priority 0 Best Effort, Priority 4 Storage, Priority 3 RoCE)
       * Figure 9.6.1 end-to-end classification contract and silent drift; Figure 9.6.2 source-of-truth verification; Figure 9.6.3 DSCP 26 -> Prio 3 vs DSCP 0 -> Prio 0
       * Hop-by-hop drift capture: tcpdump 10.20.4.15.51422 > 10.20.8.5.4791 udp port 4791 length 1200 tos 0xb8 (0xb8 >> 2 = 46 EF), swp4 trust: dscp bucket 40-47 -> prio 3 vs swp19 trust: pcp 0..7 -> prio 0
       * 6-layer production validation plan; Scenario 1 ethtool -S swp19 rx_prio0_discard: 18420 & rx_pfc_prio3: 0; Scenario 2 mlnx_qos -i swp4 tc: 0 dwrr weight 5 starved by tc: 1 strict; Scenario 3 storage ETS contention
     - nvidia-zero-to-hero/volume-09/labs/lab-01-inventory-an-ai-ethernet-path.md
     - nvidia-zero-to-hero/volume-09/labs/lab-02-validate-roce-addressing-and-mtu.md
     - nvidia-zero-to-hero/volume-09/labs/lab-03-observe-pfc-and-ecn-under-load.md
     - nvidia-zero-to-hero/volume-09/labs/lab-04-troubleshoot-a-roce-path.md
     - nvidia-zero-to-hero/volume-09/chapter-04-priority-flow-control.md
     - nvidia-zero-to-hero/volume-09/chapter-07-spectrum-switches-for-ai.md
     - nvidia-zero-to-hero/volume-09/chapter-08-connectx-ethernet-adapters.md
     - nvidia-zero-to-hero/volume-09/chapter-09-bluefield-dpus-and-doca.md
  2. Book Sources from the Local TOON-RAG Corpus:
     - AI Data Center Network Design and Technologies (ai-data-center-network-design-and-technologies):
       * Chapter 7 (7. RoCEv2 Transport and Congestion Management: PFC-DSCP, ECN, DCQCN, UDP 4791, CNP opcode 129 / 0x81)
       * Chapter 9 (9. Storage Network Design and Technologies: PCIe Gen5 32 GT/s x16 ~63 GB/s and ~100 ns local SSD latency, InfiniBand ~300 ns switch latency with 16 VLs, 8-12 workload queues, 64 B CBFC credits, 48,000 LIDs, Ethernet ~800 ns [700-900 ns] switch latency, Table 9-2 comparison of (P)NFS and NVMe-o-TCP on port 8009 [lossy] vs NVMe-o-RDMA and InfiniBand [lossless])
     - Computer Networking Problems and Solutions (computer-networking-problems-and-solutions):
       * Chapter 8 (Quality of Service: Figure 8-3 QoS trust boundary, LLQ policing math on 1,024 Kbps link with 512 Kbps cap and 8, 9 [576 Kbps, 64 Kbps dropped], 10 [640 Kbps uncongested when other <= 384 Kbps], 12 [768 Kbps, 256 Kbps dropped] 64 Kbps calls or 32 x 16 Kbps calls, CBWFQ 256:128:128:512 = 2:1:1:4 across 8 clock cycles)
       * Chapter 17 (Policy in the Control Plane: serialization delay on 100 Mbps for 64 B [.05 ms], 1,500 B [.12 ms], and 9,000 B [.72 ms] frames, Figure 17-4 7 elephant / 4 mouse flow jitter .05 ms to .288 ms)
     - NVIDIA Base Command Manager 11 Administrator Manual (bcm11-admin):
       * Chapter 3 (3.2 Network Settings & 3.6 Configuring InfiniBand Interfaces: onnetworkpriority ladder Bridge=80, Bond=70, Physical=60, VLAN=50, Alias=40, Tunnel=30, Netmap=20, BMC=10, and persistent mlxconfig MLX_ extra_values precedence)
     - Cross-checked: Network Programmability and Automation (2nd Edition) (network-programmability-and-automation-2nd-edition, Chapter 3 Linux networking)
```

### Run here

- `python3 -B code/part12/dcb_qos_ai_lab.py` (30 passed, 0 failed out of 30 checks).

### Explicitly labelled inferences

- The 400.0 Gbps ETS multi-class allocation numbers apply the standard IEEE 802.1Qaz work-conserving ETS formula in `code/part12/dcb_qos_ai.py` to the class model in Volume 09 Chapter 6 and Chapter 2.19.
- The four-class buffer exhaustion calculation extrapolates the single-class `mlnx_qos -i swp12` buffer profile of 262,144 B total and 65,536 B per lossless priority from Volume 09 Chapter 4.

### Not verified on live hardware

- All `mlnx_qos`, `dcb`, `lldptool`, `cma_roce_tos`, `ethtool -S`, `tcpdump`, `lspci`, `nvidia-smi`, `rdma link`, `ibv_devinfo`, `cmsh`, and SONiC or Cumulus CLI commands are marked `(untested here)` and were not executed on live switch or ConnectX and BlueField hardware in this environment.

