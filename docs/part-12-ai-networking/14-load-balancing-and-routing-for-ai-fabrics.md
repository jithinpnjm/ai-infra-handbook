---
id: "c12-14"
title: "12.14 Load balancing and routing for AI fabrics"
sidebar_label: "12.14 Load balancing and routing for AI fabrics"
sidebar_position: 14
description: "Per-flow and per-packet load balancing (SLB, DLB, GLB NNHN, TELB, sDLB) and IP routing protocols (eBGP unnumbered, BGP DPF, RIFT, IS-IS Flex Algo, EVPN-VXLAN multi-tenancy, and SRv6 uSID) for AI/ML data center fabrics."
status: "drafted"
tier: "1"
level: "A"
lab_venue: "Nebius GPU"
---

# 12.14 Load balancing and routing for AI fabrics

| | |
|---|---|
| Level | Advanced |
| Priority tier | 1 |
| Lab venue | Nebius GPU |
| Part | Part 12: Complete AI networking |
| Sources used | `ADC` Ch. 6, Ch. 8; `bcm11-admin` Ch. 3 |
| Coverage file | `planning/coverage/chapters/12-14.md` |
| Claim ledger | `planning/ledgers/12-14.md` |
| Companion code | `code/part12/load_balancing_routing_ai.py`, `code/part12/load_balancing_routing_ai_lab.py` |

## Why this matters for AI infrastructure

An AI training cluster with full non-oversubscribed leaf-to-spine bandwidth can still run at half of its effective fabric capacity. It will also suffer persistent Priority Flow Control stalls if its switches rely on traditional static 5-tuple Equal-Cost Multipathing. Enterprise web and microservice workloads generate thousands of short, high-entropy TCP connections that spread evenly across switch ports. Distributed Large Language Model training with natural language understanding and natural language generation phases behaves very differently. It exchanges massive east-west synchronization bursts across a small, fixed set of GPU pairs over RoCEv2 on UDP port 4791. When two elephant flows hash to the same leaf-to-spine uplink, that link saturates and pauses traffic while adjacent uplinks sit idle.

Eliminating these bottlenecks requires coordinating two layers of the switching stack. Operators must align data-plane load balancing in the switch Packet Forwarding Engine with control-plane IP routing across three-stage, five-stage, or DragonFly topologies. In the data plane, modern AI switch ASICs progress from Static Load Balancing with resilient and weighted hashing to local queue-aware Dynamic Load Balancing. They also support next-next-hop Global Load Balancing, Traffic Engineering Load Balancing, and Selective Packet Spraying that matches RoCEv2 Base Transport Header write opcodes in TCAM. In the control plane, operators deploy eBGP with RFC 5549 BGP unnumbered, shared spine Autonomous System Numbers, Link Bandwidth Extended Communities, or BGP Deterministic Path Forwarding. Alternative control planes include Routing in Fat Trees, IS-IS with distributed flood reduction and Flex Algo, multi-tenant EVPN-VXLAN with NVIDIA Multi-Instance GPU, and Segment Routing over IPv6 compressed micro-SIDs.

| Layer | Technology Family | Key Mechanisms and Standards |
|---|---|---|
| Workload traffic | Distributed LLM (`NLU` and `NLG`) | `1:1` non-oversubscribed `400 Gbps` or `800 Gbps` links, `RoCEv2` (`UDP 4791`), `100 Gbps` and `50 Gbps` flows on `200 Gbps` uplinks (`100%` vs `50%` load) |
| Data-plane load balancing | Switch ASIC `PFE` | `SLB` (`512` or `1,024` resilient buckets, `WCMP`), `DLB` (quality bands `0..7`, flowlets), `GLB` (`20 ms` heartbeats), `TELB`, `sDLB` (`BTH` write opcodes in `TCAM`) |
| Control-plane routing | Clos and DragonFly underlays | `eBGP` (`RFC 5549` Capability Code `5`, spine `ASN 65001`, `BGP DPF`), `RIFT` (`RFC 9692`), `IS-IS` (`RFC 9350` / `RFC 9502` Flex Algo), `EVPN-VXLAN` + `MIG`, `SRv6` `16`-bit `uSID` |

## Prerequisites and outcomes

Prerequisites for this chapter include the fabric and transport foundations from earlier sections. You should understand AI collective traffic patterns, RDMA Queue Pairs, RoCEv2 headers, and congestion control from Chapters 12.1 through 12.5. You should also know switch ASIC buffer architectures, Ethernet versus InfiniBand trade-offs, and rail topologies from Chapters 12.11 through 12.13.

After completing this chapter, you will be able to perform five engineering tasks. First, you will compute the exact 5-tuple CRC32 hash key and modulo indices. You will also build resilient bucket remapping, symmetric XOR normalization, and WCMP indirection tables for SLB. Second, you will compare SLB, DLB, GLB, and TELB across local and remote congestion scenarios. Third, you will architect per-packet spraying and sDLB on NVIDIA ConnectX-6, ConnectX-7, and BlueField DPUs. Fourth, you will design and verify eBGP AI underlays using BGP unnumbered, shared spine ASNs, ADD-PATH, Link Bandwidth Extended Communities, and BGP DPF. Fifth, you will evaluate RIFT, IS-IS Flex Algo, multi-tenant EVPN-VXLAN with H100 MIG, host-level FRR BGP, and SRv6 uSID traffic engineering.

| Outcome Area | Target Numbers, Identifiers, and Mechanisms |
|---|---|
| 1. `SLB` hashing math | `CRC32` key `0x8BDA7C2D` (`2,346,351,661`), `mod 5 = 1`, `mod 8 = 5`, `512` or `1,024` resilient buckets, symmetric `XOR`, `WCMP` |
| 2. `DLB`, `GLB`, and `TELB` | Quality bands `0` to `7`, flowlet inactivity timer (`256 µs`), `draft-wang-idr-next-next-hop-nodes` Code `2`, `20 ms` Tomahawk 5 heartbeats |
| 3. Per-packet spraying | Random Spray, `DLB` Per-Packet Mode, `sDLB` matching `UDP 4791` `BTH` RDMA Write opcodes (`0x06..0x0B`) on `ConnectX-6/7` and `BlueField` |
| 4. `eBGP` AI underlays | `RFC 5549` Capability Code `5`, `MP_REACH_NLRI` Type `14`, shared spine `ASN 65001`, `ADD-PATH`, `WCMP` (`20%/45%/15%/20%`), `BGP DPF` (`draft-wang-idr-dpf`) |
| 5. IGP, multi-tenancy, `SRv6` | `RIFT` (`RFC 9692`), `IS-IS` `Flex Algo` (`128`, `129`, `130`), `512`-GPU/rail `EVPN-VXLAN` + `7`-instance `H100 MIG`, host `FRR` (`4200000001..4200000004`), `16`-bit `uSID` |

---

## 1. Per-flow load balancing: from static hashing to global path awareness

### 1.1 IP ECMP next-hop groups and the low-entropy RoCEv2 problem

When a leaf switch learns multiple equal-cost paths to a remote GPU server, it must forward packets across those uplinks in hardware. It cannot consult the routing CPU on every frame. If the switch created a separate hardware forwarding group for every destination IP prefix across dozens of spines, ASIC next-hop table memory would run out. Instead, the switch control plane groups all remote prefixes that share the same spine next hops into one shared hardware ECMP group identifier.

In a three-stage Leaf-Spine Clos fabric, GPU1 connects to LeafA, GPU2 connects to LeafB, and both leaves connect to SpineA, SpineB, and SpineC. The routing protocol advertises GPU2's IP subnet from LeafB to all three spines. Each spine rewrites the BGP next-hop attribute to itself and advertises the prefix to LeafA. Because all three paths carry identical routing metrics and BGP attributes, LeafA installs one shared hardware ECMP group in its ASIC forwarding table.

```text
ASIC ECMP Group nh-id123 ---> { Unicast_nh1: SpineA, Unicast_nh2: SpineB, Unicast_nh3: SpineC }
Scale in production AI clusters: 32 or 64 spines sharing nh-id123 (or resolving to remote VTEP loopbacks under EVPN-VXLAN MAC-VRF / RT5 overlays)
```

Once the control plane programs `nh-id123`, packet-by-packet path selection happens entirely inside the switch ASIC Packet Forwarding Engine. Neither BGP nor the switch CPU participates in choosing which spine carries a given packet.

```mermaid
flowchart LR
    subgraph PerFlow["Per-Flow Load Balancing (SLB / DLB / GLB / TELB)"]
        PF1["SLB: Static 5-Tuple CRC32\n+ Resilient 512/1024 Buckets"] --> PF2["DLB: Local Link BW + Queue\nQuality Bands (0..7) & Flowlets"]
        PF2 --> PF3["GLB: BGP NNHN (Code 2)\n+ 20 ms ASIC Heartbeats"]
        PF3 --> PF4["TELB: BGP-DPF / PBR Pinning\nper QPAIR or Tenant Color"]
    end
    subgraph PerPkt["Per-Packet Load Balancing (Random / DLB-PP / sDLB)"]
        PP1["Random Spray: Round-Robin\nAcross ECMP Ports"] --> PP2["DLB Per-Packet: Weighted by\nLocal Link Quality Table"]
        PP2 --> PP3["sDLB: TCAM ACL Matches\nUDP 4791 BTH Write Opcodes"]
    end
    PerFlow --> PerPkt
```

| Load-Balancing Family | Specific Mechanism | Primary Input Signals | Reordering Exposure and Target Hardware |
|---|---|---|---|
| **Per-Flow (`SLB`)** | Raw Modulo, Resilient (`512`/`1,024` buckets), Symmetric `XOR`, Weighted (`WCMP`) | Packet 5-tuple (`SRC/DST IP`, `Proto 17`, `SRC/DST UDP`) + optional `BTH QPair` | Zero intra-flow reordering; vulnerable to low-entropy elephant collisions (`100%` vs `50%` link load). |
| **Per-Flow (`DLB`)** | Assigned-Flow Mode, Flowlet Mode (inactivity timer), Reactive Rebalancing | 5-tuple + local port bandwidth utilization and egress buffer queue depth (quality bands `0..7`) | Zero reordering if paused longer than inactivity timer; brief reordering during reactive rebalancing. |
| **Per-Flow (`GLB`)** | Broadcom Cognitive Routing / `Tomahawk 5` `GLB` App | Local `DLB` quality + remote spine-to-egress-leaf quality via `BGP NNHN` (`Code 2`) and `20 ms` ASIC heartbeats | Prevents downstream spine collisions (`Link X` on `SpineA -> LeafD`); lowers `DCQCN` and `PFC` triggers. |
| **Per-Flow (`TELB`)** | Filter-Based Forwarding (`FBF`/`PBR`), `BGP DPF`, or Out-of-Band `TELB` Controller | Source `UDP` port range, `RoCEv2 BTH QPair`, ingress GPU port, or fabric telemetry | Deterministic in-order delivery per colored fabric plane with pre-installed ASIC backup path ID. |
| **Per-Packet** | Random Spray, `DLB` Per-Packet Mode, Selective Packet Spraying (`sDLB`) | Per-datagram spraying (`1,500 B` packets `A, B, C`) + `TCAM ACL` on `BTH` RDMA `Write` opcodes (`0x06..0x0B`) | Requires NIC hardware reorder buffer (`NVIDIA ConnectX-6/7` or `BlueField` DPU for RDMA Write opcodes). |

### 1.2 Static load balancing (`SLB`): worked CRC32 5-tuple math, resilient buckets, symmetric XOR, and WCMP

Static Load Balancing hashes packet headers without knowing whether the selected outgoing link is idle or congested. When two elephant flows produce the same hash index, they collide on one spine link while parallel links sit underutilized. Worse, if a link flaps and changes the number of active uplinks, naive modulo arithmetic remaps almost every active flow in the switch at once.

When a packet enters a switch port under SLB, the PFE extracts the 5-tuple header fields and optional fields from the RoCEv2 BTH header. It passes those bits through a hardware hash polynomial such as CRC32 or CRC16. Raw modulo arithmetic then divides the hash key by the active ECMP member count to pick the outgoing interface index.

```text
Worked 5-Tuple CRC32 Calculation (ADC Ch. 6):
- Simple modulo examples (N = 5): hash_key = 10 -> 10 mod 5 = 0; hash_key = 11 -> 11 mod 5 = 1
- Source IP address:      192.168.1.20 -> hex C0A80114
- Destination IP address: 192.168.2.10 -> hex C0A8020A
- IP Protocol:            17 (UDP)     -> hex 11
- Source UDP port:        1024         -> hex 0400
- Destination UDP port:   4791 (RoCEv2)-> hex 12B7
- Concatenated 13-byte (104-bit) string: C0A80114 C0A8020A 11040012 B7
- Hardware CRC32 output:  0x8BDA7C2D = 2,346,351,661 (base 10)
- Active links N = 5:     2,346,351,661 mod 5 = 1 (outgoing interface index 1)
- Active links N = 8:     2,346,351,661 mod 8 = 5 (outgoing interface index 5)
- Naive modulo churn:     dropping from 5 to 4 links remaps 75% of active flows
```

To prevent global flow churn when a link state changes, switches implement resilient hashing. Resilient hashing replaces the variable divisor with a fixed hardware indirection table of 512 or 1,024 buckets. When a single interface fails, the ASIC rewrites only the buckets that pointed to the failed link and leaves all other buckets untouched.

| Bucket Index (`hash_key mod 8`) | Initial Mapped Interface (`5` Active Links) | Remapped Interface After `interface_2` Fails | Status on `interface_2` Failure |
|---|---|---|---|
| `Bucket 0` | `interface_0` | `interface_0` | Unchanged |
| `Bucket 1` | `interface_1` | `interface_1` | Unchanged |
| `Bucket 2` (`10 mod 8 = 2`) | `interface_2` | `interface_0` (reassigned) | **Affected (`2 / 8 = 25%` remapped)** |
| `Bucket 3` | `interface_3` | `interface_3` | Unchanged |
| `Bucket 4` | `interface_4` | `interface_4` | Unchanged |
| `Bucket 5` | `interface_0` | `interface_0` | Unchanged |
| `Bucket 6` | `interface_1` | `interface_1` | Unchanged |
| `Bucket 7` | `interface_2` | `interface_1` (reassigned) | **Affected (`2 / 8 = 25%` remapped)** |

Switches often combine two additional SLB enhancements with resilient buckets. First, symmetric hashing sorts or applies a bitwise XOR over the source and destination IP addresses and UDP ports before evaluating CRC32. Both directions of a bidirectional flow then land on the exact same bucket and interface. That symmetry is required for stateful firewalls or inline inspection engines. Second, Weighted ECMP populates the bucket indirection table in proportion to configured next-hop weights rather than evenly. This weighting biases flow distribution toward higher-capacity spines.

Even with resilient, symmetric, and weighted enhancements, SLB remains blind to actual flow rates and queue occupancy. An equal number of flows on each port can still produce severe bandwidth imbalance when elephant and mice flows mix.

| Metric / Scenario | `LeafA -> SpineA` (`200 Gbps` Uplink) | `LeafA -> SpineB` (`200 Gbps` Uplink) | Operational Outcome |
|---|---|---|---|
| **`SLB` (`2` flows per link: `Flow1=50G, Flow2=100G, Flow3=50G, Flow4=100G`)** | `Flow1 + Flow3 = 100 Gbps` (`50%` utilization) | `Flow2 + Flow4 = 200 Gbps` (`100%` utilization) | `SpineB` saturates at `100%` while `SpineA` sits at `50%`. |
| **`SLB` low-entropy collision (`2 × 200 Gbps` elephant flows)** | `0 Gbps` (`0%` utilization) | `2 × 200 Gbps` (`100%` saturated) | Mice flows drop or pause behind colliding elephant flows. |
| **`DLB` bandwidth-aware assignment (`Flow1..Flow4`)** | `Flow1 + Flow4 = 150 Gbps` (`75%` utilization) | `Flow2 + Flow3 = 150 Gbps` (`75%` utilization) | Both `200 Gbps` uplinks balance at `150 Gbps` (`75%`). |

### 1.3 Dynamic load balancing (`DLB`): quality bands, flowlet inactivity timers, and reactive rebalancing

Static hashing cannot see that one uplink is carrying twice as many bytes per second as its neighbor. When collective phases shift traffic patterns every few milliseconds, static hash assignments leave some uplinks congested and others half empty. Dynamic Load Balancing solves this local collision problem by incorporating real-time link utilization and egress queue depth into forwarding decisions.

Pioneered in Broadcom switch silicon and also known as Adaptive Load Balancing on other platforms, DLB runs an embedded microkernel inside the switch ASIC. It continuously samples local port bandwidth utilization and egress buffer queue occupancy in the PFE. Each ECMP member interface is mapped to an integer link quality band from 0 for lowest quality to 7 for highest quality. Because DLB tracks port state in the PFE in real time, it detects local link failures in microseconds. It does not wait for control-plane routing convergence.

| `DLB` Operational Mode | Forwarding Mechanism | Suitability for AI Training Fabrics |
|---|---|---|
| **1. `DLB` Assigned-Flow Mode** | Assigns each new flow to the highest-quality local egress port when its first packet arrives and pins it there for life. | Unsuitable for AI backend fabrics because RDMA Queue Pairs stay open for hours while link quality changes. |
| **2. `DLB` Flowlet Mode (Inactivity Timer)** | Tracks flows in hardware flowset tables and starts a per-flow inactivity timer (`256 µs`). Pauses shorter than the timer keep the current spine (`SpineB`); gaps exceeding the timer reassign the next burst (flowlet) to a higher-quality spine (`SpineA`). Ties (e.g., all at band `7`) fall back to flow hash. | Ideal for bursty GPU tasks that reuse the same outer 5-tuple (differing only inside `IB BTH`) with natural inter-task gaps. |
| **3. `DLB` Reactive Path Rebalancing** | Monitors active links for continuous elephant flows (`Flow1`, `Flow2`, `Flow3`) that never pause longer than the inactivity timer. Migrates flows from degraded `LeafA -> SpineA` to `LeafA -> SpineC` mid-stream. | Useful when destination NICs can tolerate brief transient packet reordering during the path switchover. |

### 1.4 Global load balancing (`GLB`): BGP NNHN (`draft-wang-idr-next-next-hop-nodes`) and `20 ms` ASIC heartbeats

Local DLB balances leaf-to-spine uplinks, but it cannot see congestion one hop further downstream on the spine-to-egress-leaf link. Suppose servers on LeafA and LeafB simultaneously send line-rate elephant flows to a destination server on LeafD. LeafA sees that its uplink to SpineA is uncongested, and LeafB independently sees that its own uplink to SpineA is uncongested. Both leaves forward their elephant flows to SpineA, where they collide on the single downlink to LeafD while SpineB's downlink to LeafD sits idle. That remote spine collision triggers ECN marking, DCQCN rate cuts, and PFC pause cascades back into the fabric.

Global Load Balancing, introduced under Broadcom's cognitive routing architecture starting with the Tomahawk 5 ASIC, eliminates remote spine collisions. It combines control-plane topology discovery via BGP Next-Next-Hop Nodes with fast data-plane hardware heartbeats.

```text
Global Load Balancing (GLB) Architecture on Broadcom Tomahawk 5 (ADC Ch. 6):
1. Control-Plane Topology Discovery (draft-wang-idr-next-next-hop-nodes / BGP NNHN):
   - Carried inside BGP Next-Hop Dependent Capabilities attribute
   - Bits 0..15:  Characteristic Code = 2
   - Bits 16..31: Characteristic Length = variable
   - Row 2 (Bits 0..31):  32-bit Next-hop BGP ID (immediate spine next hop)
   - Row 3+ (Bits 0..31): 32-bit Next-next-hop BGP IDs (downstream egress leaves reachable via ECMP for the NLRI)
2. Data-Plane PFE Heartbeats (20 ms interval):
   - BGP sends a path-monitor message instructing the PFE GLB app to flood heartbeats ONLY on active BGP underlay interfaces
   - Change-based hardware heartbeats exchanged every 20 ms
3. Path Quality Profiles & Avoidance:
   - Simple path quality profile:   3-stage Clos (single next-next-hop leaf per spine for a prefix)
   - Compound path quality profile: 5-stage Clos (groups 2+ simple profiles across pod spines and super-spines)
   - Path correlation: combines local Link A (LeafA->SpineA) & Link B (LeafA->SpineB) with remote Link X (SpineA->LeafD) & Link Y (SpineB->LeafD)
   - Result: LeafA sees remote Link X is congested and steers new flows over Link B -> SpineB -> Link Y
```

In five-stage Clos clusters, operators can deploy GLB in four scopes depending on hardware table scale. They can enable it across a three-stage Clos fabric on all switches. They can also enable it within individual pods of a five-stage Clos by treating each pod as a three-stage GLB domain. Alternatively, they can run GLB exclusively between the spine and super-spine layers when oversubscription exists there. Finally, they can run it across all five stages when ASIC profile table capacity permits.

### 1.5 Traffic engineering–based load balancing (`TELB`)

Dynamic schemes like DLB and GLB react after queue occupancy begins to change. Multi-tenant LLM training clusters often require strict deterministic path pinning. That way, one tenant's bursty AllReduce or AllToAll job never shares spine links or buffers with another tenant. Traditional MPLS Traffic Engineering and Segment Routing MPLS require expensive software licenses on high-radix switches and add label overhead. They also lack full telemetry and lossless DCQCN compatibility compared to native IP fabrics.

Traffic Engineering–Based Load Balancing achieves deterministic path diversity in a pure Ethernet and IP fabric. It uses filter-based forwarding rules, ingress-port coloring, or an out-of-band telemetry controller synchronized with the GPU job scheduler.

| `TELB` Mechanism | Topology and Configuration Details | Operational Guarantee |
|---|---|---|
| **1. Multi-tenant spine slicing and `FBF` / `PBR`** | In an `8`-spine, two-stripe `ROD` (`Leaf1..Leaf8` in Stripe 1, `Leaf9..Leaf16` in Stripe 2) with `7` tenants (`Tenant 1..7`), pin `Tenant 1` to `1` spine or split `4` and `4` spines. Host splits collectives across multiple `RoCEv2` `QPAIRs`; leaf `FBF`/`PBR` maps `QPAIR` or source UDP port ranges onto colored path IDs (`BGP DPF`). | Strict in-order delivery per pinned spine or `QPAIR` group with pre-installed ASIC backup path IDs. |
| **2. Ingress-port coloring in `RUD`** | All `8` GPUs (`GPU 1..8`) of a server connect to the same leaf complex (`Leaf1..Leaf16` with `3 × 400G` uplinks to `Spine1..Spine8`). `TELB` classifies traffic by ingress switch interface, assigning each GPU ID to a dedicated logical fabric color. | A bandwidth spike on `GPU 1` cannot contend with jobs running on `GPU 2..8`. |
| **3. Out-of-band (`OOB`) `TELB` controller** | External controller on the `OOB` management network collects streaming telemetry (queue buffers, `DCQCN`/`PFC` counters, active probe latencies) and coordinates with the GPU job scheduler. | Dynamically updates deterministic path placements before job launch or between training phases. |

---

## 2. Per-packet load balancing and selective packet spraying (`sDLB`)

### 2.1 Random spray, DLB per-packet mode, and the receiver reordering challenge

Per-flow load balancing can never split a single massive GPU-to-GPU flow across multiple spine links simultaneously. Per-packet load balancing solves this by ignoring flow tables at the ingress leaf and spraying every arriving packet of an elephant flow across all available ECMP uplinks. This achieves nearly perfect link utilization even when a single pair of GPUs communicates at line rate.

However, parallel spine switches experience slightly different instantaneous queue depths. Packets sprayed across three spines therefore arrive at the egress leaf and destination NIC out of sequence. Traditional RDMA NICs without hardware reorder buffers treat out-of-order Packet Sequence Numbers as packet loss and emit Go-Back-N NAK storms that collapse goodput.

```text
Per-Packet Spraying and Selective Packet Spraying (sDLB) Mechanics (ADC Ch. 6):
- Spraying example: 100 Gbps flow of 3 x 1,500-byte datagrams (Datagram A, Datagram B, Datagram C) into Leaf1
  * Datagram A -> Port 1 (100 Gbps to Spine1)
  * Datagram B -> Port 2 (100 Gbps to Spine2)
  * Datagram C -> Port 3 (100 Gbps to Spine3)
- Out-of-order arrival at Leaf2 and server 192.168.1.1:
  * Time T1: Datagram B arrives first
  * Time T2: Datagram C arrives second
  * Time T3: Datagram A arrives last
- Switch Per-Packet Modes:
  1. Random Spray: blind random/round-robin across ECMP ports (can overload a link if 64 B control frames mix with 4,096 B or 9,000 B payloads)
  2. DLB Per-Packet Mode: weights per-packet spraying using the real-time DLB hardware link quality table (bands 0..7)
  3. Selective Packet Spraying (sDLB): ingress TCAM ACL inspects UDP 4791 + 8-bit RoCEv2 BTH opcode for ConnectX-6 (CX6), ConnectX-7 (CX7), and BlueField DPUs:
     - Flow1 (non-matching: RDMA Read Request 0x0C, RDMA Send Only 0x04) -> per-flow SLB/DLB (strictly in order)
     - Flow2 (matching: RDMA Write First 0x06, Write Middle 0x07, Write Last 0x08, Write Only 0x0A, 0x06..0x0B) -> DLB per-packet spray (NIC DDP engine places payloads out of order and defers CQE until all PSNs arrive)
```

### 2.2 Complete load-balancing mechanism comparison (`ADC` Table 6-1)

Choosing the right load-balancing mechanism depends on whether your switch silicon supports remote quality heartbeats and whether your NICs support out-of-order RDMA Write placement. The table below summarizes the seven capability dimensions across all four per-flow families.

| Feature / Capability | `SLB` (Static) | `DLB` (Dynamic) | `GLB` (Global) | `TELB` (Traffic Engineering) |
|---|---|---|---|---|
| **Load balancing based on packet characteristics** | Yes (`5`-tuple) | Yes (`5`-tuple + flowlets) | Yes (`5`-tuple + flowlets) | No (explicit path/color policy) |
| **Includes local link bandwidth** | No | Yes | Yes | Yes |
| **Uses queue size information** | No | Yes | Yes | No |
| **Can use remote link quality** | No | No | Yes (`BGP NNHN` + `20 ms` heartbeats) | Yes |
| **May include `RoCEv2 BTH` header for load balancing** | Yes | Yes | Yes | Yes |
| **Can use fabric telemetry for load balancing** | No | No | No | Yes |
| **Industry adoption level** | **High** | **Medium** | **Low** | **Low** |

---

## 3. IP routing for AI fabrics: eBGP unnumbered, ASN design, WCMP, and BGP DPF

### 3.1 Dynamic IP routing options: OSPF vs IS-IS vs eBGP across backend and frontend networks

An AI data center comprises two distinct routing domains with different traffic and multi-tenancy demands. The backend training fabric connects high-speed GPU compute nodes over lossless RoCEv2 and DCQCN. The frontend inference and storage fabric connects inference servers, client gateways, and storage clusters over RoCEv2, NVMe-o-TCP, iSCSI, or iWARP. Even when an operator chooses eBGP for both domains, the feature profiles diverge. The backend typically runs a pure native IP underlay optimized with GLB or BGP Link Bandwidth Extended Communities. By contrast, the frontend layers EVPN-VXLAN multi-tenant overlays on top of standard equal-weight ECMP.

| Routing Protocol Family | Core Mechanism and Strengths | Operational Trade-Offs in AI Fabrics |
|---|---|---|
| **`OSPFv2` / `OSPFv3`** | Link-state flooding and Dijkstra `SPF` algorithm for fast convergence. | Requires separate instances for IPv4 (`OSPFv2`) and IPv6 (`OSPFv3`), lacks per-prefix policy traffic engineering, and risks transient micro-loops during topology changes. |
| **`IS-IS`** | Encapsulates directly over Layer 2 (immune to TCP spoofing), carries IPv4 and IPv6 in one instance via extensible `TLVs`, and scales to `2,500` switches with `Flex Algo`. | Enterprise data center teams often have less operational familiarity with `IS-IS` than with `BGP`. |
| **`eBGP` (`RFC 7938`)** | Deterministic path-vector loop prevention (`AS_PATH`), rich route-policy engine, native `EVPN` multi-tenancy, and multi-vendor maturity. | Requires `BGP` unnumbered (`RFC 5549`), shared spine `ASN` allocation, `ADD-PATH`, and link-bandwidth or `DPF` communities for optimal AI fabric behavior. |

### 3.2 eBGP underlay and BGP unnumbered (`RFC 5549` / `Capability Code 5`)

In a non-oversubscribed AI Clos fabric with dozens of high-speed links per switch, assigning and tracking `/30` or `/31` point-to-point IPv4 subnets on every cable is tedious and error-prone. A single mistyped subnet mask or swapped cable silently breaks ECMP symmetry. BGP Unnumbered, standardized in RFC 5549 and updated by RFC 8950, eliminates interface IPv4 address configuration altogether.

Under BGP unnumbered, switches establish eBGP sessions over automatic IPv6 Link-Local Addresses derived from each port's burned-in MAC address. They then advertise IPv4 server prefixes with an IPv6 link-local Next Hop using Extended Next Hop Encoding. Operators only need to assign private BGP Autonomous System Numbers and redistribute local GPU server interfaces via a route policy.

```text
RFC 5549 / RFC 8950 BGP Unnumbered Wire Sequence (ADC Ch. 8 Figs. 8-1, 8-2, 8-3):
- Private ASN ranges: 16-bit (64512 to 65535), 32-bit (4200000000 to 4294967294)
- Peers on interface Eth11:
  * spine1: MAC 0c:59:9c:f1:00:32, IPv6 LLA fe80::e59:9cff:fef1:32, AS 65001, Router ID 172.16.7.101
  * leaf1:  MAC 0c:59:9c:22:5d:d7, IPv6 LLA fe80::e59:9cff:fe22:5dd7
- Step 1 (ICMPv6 ND & RD): Exchange NS/NA (Router flag R set) and RS/RA carrying Source Link-Layer Address option (learns LLA + MAC without ARP)
- Step 2 (TCP Handshake):  spine1 fe80::e59:9cff:fef1:32 (port 52659) -> leaf1 fe80::e59:9cff:fe22:5dd7 (port 179) SYN, SYN-ACK, ACK
- Step 3 (Frame 22 - BGP OPEN, 189 bytes / 1,512 bits on wire):
  * Type = 1 (OPEN), Length = 81 bytes, Version = 4, My AS = 65001, Hold Time = 90 s, BGP ID = 172.16.7.101, Opt Params Len = 52 bytes
  * Capability: Extended Next Hop Encoding (Capability Code = 5, Length = 6 bytes)
    -> AFI = 1 (IPv4), SAFI = 1 (Unicast), Next Hop AFI = 2 (IPv6)
- Step 4 (Frame 28 - BGP UPDATE, 358 bytes / 2,864 bits on wire):
  * Type = 2 (UPDATE), Length = 82 bytes, Withdrawn Routes Len = 0, Total Path Attr Len = 46 bytes
  * ORIGIN = IGP, AS_PATH = 65001 (Flags = 0x40, Type = 2, Length = 6)
  * MP_REACH_NLRI (Flags = 0x90, Type Code = 14, Length = 42 bytes):
    -> AFI = 1 (IPv4), SAFI = 1 (Unicast), Next Hop = fe80::9:0a:2f:c1:f1:32, NLRI = 172.16.7.181/32
```

### 3.3 BGP ASN allocation, ADD-PATH, AS-PATH normalization, Link Bandwidth WCMP, and minimum peers

How an architect assigns BGP Autonomous System Numbers to spines and leaves governs how the fabric behaves during multi-link failures. If every spine switch receives a different ASN, simultaneous link failures can cause BGP to route traffic down from one spine to a transit leaf and back up to another spine. On 400 Gbps or 800 Gbps AI links, this valley tromboning saturates the transit leaf and stalls every GPU job connected to it.

Assigning a single shared ASN to all spines in the same tier while giving each leaf its own unique ASN prevents valley routing automatically. Standard BGP `AS_PATH` loop detection on the second spine sees its own shared ASN already in the path and rejects the bounced route immediately. Four additional BGP features handle external multipath reflection, WAN ASN normalization, unequal spine bandwidths, and degraded downlink withdrawal.

| Control-Plane Feature | Topology and Configuration Parameters (`ADC` Ch. 8) | Operational Behavior |
|---|---|---|
| **1. Shared Spine `ASN` (`Fig. 8-4` vs `Fig. 8-5`)** | `spine1..spine4` share `ASN 65001`; `leaf1..leaf4` use unique `ASNs 65101..65104`. Anti-pattern uses unique spine `ASNs 65001..65004`. | When `leaf1 -> spine2..4` and `leaf2 -> spine3` fail between `server1` (`10.10.1.1/24` on `leaf1`, `AS 65101`) and `server5` (`10.10.5.1/24` on `leaf3`, `AS 65103`), shared `ASN 65001` rejects the valley trombone `leaf1 (65101) -> spine1 (65001) -> leaf2 (65102) -> spine1/2 -> leaf3 (65103)` because `65001` is already in `AS_PATH (65001, 65102, 65101)`. |
| **2. `BGP ADD-PATH` (`Fig. 8-6`)** | External `DC GW` (`AS 65503`) advertises `server2` (`10.10.108.0/24`) via `border-leaf1` (`AS 65501`, `NH1`) and `border-leaf2` (`AS 65502`, `NH2`) to `spine2` (`AS 65001`). | Enabling `ADD-PATH send/receive` on `spine2` advertises both `NH1` and `NH2` for `10.10.108.0/24` to `leaf2` (`AS 65102`, hosting `server1` `10.10.101.0/24`) instead of only a single best path. |
| **3. `AS-PATH` Strip and Replace (`Fig. 8-7`)** | Ingress policy on border spines (`AS 65001`) or ToR leaves for routes from `server101` (private WAN core or host BGP daemons). | Strips private ASNs and replaces `AS_PATH` with a uniform-length operator ASN sequence so all border paths remain equal-cost `ECMP` candidates. |
| **4. Link Bandwidth Extended Community (`WCMP` / `WPS`, `Fig. 8-8`)** | `spine1..spine4` (`AS 65001`) connect northbound with `400 Gbps`, `800 Gbps`, `100 Gbps`, and `400 Gbps` (`1,700 Gbps` total). | Programs `WCMP` buckets on `leaf1..leaf4` (`AS 65101..65104`) as `20%` (`spine1`), `45%` (`spine2`), `15%` (`spine3`), and `20%` (`spine4`), or `13, 28, 10, 13` of `64` buckets. Dynamically lowers weights on 5-stage super-spine link failure (`Weighted Packet Spraying`, `WPS`). |
| **5. Minimum BGP Peers per Prefix** | Conditional advertisement policy on a spine reaching `10.10.101.0/24` across `4`-way `ECMP` downlinks. | If `1` downlink fails (active peers drop from `4` to `3`), the spine withdraws `10.10.101.0/24` northbound so upstream leaves use only the remaining `3` full-capacity spines instead of sending `25%` of traffic into a degraded spine. |

### 3.4 BGP Deterministic Path Forwarding (`BGP DPF`, `draft-wang-idr-dpf`) and traffic-to-fabric color mapping

Standard eBGP treats the entire Clos fabric as one shared pool of bandwidth where every tenant competes for the same spine queues. BGP Deterministic Path Forwarding, specified in `draft-wang-idr-dpf`, partitions a physical three-stage or five-stage Clos into multiple isolated logical colored fabrics such as black and gray. It accomplishes this by coloring underlay eBGP peering sessions as well as routes.

An underlay eBGP session between a leaf and spine can be configured with a single color, multiple colors over the same physical link, excluding colors, or uncolored. Under the color pruning rule, only routes carrying at least one color that matches the eBGP session color are advertised over that session. Any unmatched colors on the route are pruned out upon advertisement, giving ingress leaves a deterministic active path and a pre-programmed ASIC backup path.

```mermaid
flowchart LR
    subgraph Egress["Egress Leaf4 (Originates 10.10.1.4/32)"]
        L4["Uncolored Route 10.10.1.4/32\n(Matches All Colors)"]
    end
    subgraph Spines["Colored eBGP Sessions & Route Pruning"]
        S1["Spine1 (Black Session)\nPrunes Route to BLACK"]
        S2["Spine2 (Gray Session)\nPrunes Route to GRAY"]
    end
    subgraph Ingress["Ingress Leaf1 (Deterministic Path Table)"]
        L1["Active Path: BLACK via Spine1\nBackup Path: GRAY via Spine2"]
    end
    L4 -->|Black eBGP| S1
    L4 -->|Gray eBGP| S2
    S1 -->|Black eBGP| L1
    S2 -->|Gray eBGP| L1
```

| BGP DPF Stage / Deployment Mode | Mechanism and Route / Forwarding Behavior | Quantitative Example from `ADC` Ch. 8 |
|---|---|---|
| **1. Route Origination and Pruning (`Fig. 8-13`)** | Egress `leaf4` originates `10.10.1.4/32` uncolored (matching all colors). Advertising over `black` session to `spine1` prunes color to `black`; advertising over `gray` session to `spine2` prunes color to `gray`. | Ingress `leaf1` installs `black` via `spine1` as **Active** and `gray` via `spine2` as pre-programmed ASIC **Backup**. |
| **2. Rail-Optimized Design (`ROD`, `Fig. 8-10`)** | Two stripes (`Leaf1..8` and `Leaf9..16`, `8` GPUs/server) share `Spine1..8`. High-priority `black` tenant LLM is pinned to `fab-id black` for deterministic low `JCT`; other tenants (`Tenant 2..7`) use `DLB` / packet spraying. | Note resiliency trade-off: in `RUD`, losing `1` leaf takes down `4` whole `H100` servers (`32` GPUs); in `ROD`, losing `1` leaf impacts `1` rail across the stripe. |
| **3. Rail-Unified Design (`RUD`, `Fig. 8-11`)** | All `8` GPUs of a server connect to the same ToR leaf complex. Specific `GPU ID` (`GPU-id 0`) or `RoCEv2 QPair` is pinned to `fab-id black` across `128` servers. | `128 × GPU-id 0` across `128` servers allocated **`3 × 400 Gbps = 1.2 Tbps`** per leaf on logical fabric `black`. |
| **4. Traffic-to-Fabric Color Mapping (`4` Options)** | (a) **Filter-Based Forwarding (`FBF`)** on ingress ports, source UDP ports, or `BTH QPairs`; (b) **On-box agent** with active probes; (c) **Central controller (`CPCE`)**; (d) **`EVPN-VXLAN` underlay-to-overlay correlation (`Fig. 8-14`)**. | `MAC-VRF-black` / `RT5-VRF-black` maps to `black` IP path (`spine1`); `MAC-VRF-gray` / `RT5-VRF-gray` maps to `gray` IP path (`spine2`). |

---

## 4. Interior gateway protocols (`RIFT` and `IS-IS Flex Algo`), multi-tenancy, host BGP, and `SRv6 uSID`

### 4.1 RIFT (`RFC 9692`) for Fat-Tree and DragonFly Sparse topologies

When an AI backend scales to tens of thousands of GPUs or adopts low-diameter DragonFly topologies, standard eBGP becomes complex to automate. It requires intricate per-link policies and external failure detection. Routing in Fat Trees, standardized in IETF RFC 9692, is a specialized hybrid Interior Gateway Protocol purpose-built for dense data center fabrics.

RIFT floods full topology link-state advertisements northbound toward the Top-of-Fabric spines so the spines maintain complete fabric visibility. At the same time, it advertises only a default route southbound via distance-vector to ToR leaves. This asymmetric design keeps leaf forwarding tables minimal and enables Zero-Touch Provisioning without manual ASN assignments. If a spine-to-leaf link fails, default routing could blackhole traffic. RIFT prevents this through automatic route disaggregation, pushing specific `/32` or `/24` southbound prefixes so leaves route around the severed spine link.

```text
RIFT (RFC 9692) and DragonFly Sparse Architecture (ADC Ch. 8 Figs. 8-15..8-18):
- Target scale: 16,000 to 32,000 GPUs (>= 1,000 switch nodes)
- Hybrid routing: Northbound link-state to Top-of-Fabric (ToF) spines; Southbound distance-vector default route to ToR leaves
- Adjacencies & Multipathing: Lightweight UDP "hello" messages + IPv6 Neighbor Discovery (ND); automatic route disaggregation on failure; wide ECMP and northbound UCMP
- Canonical DragonFly: 7 switch groups (Group 1..7), each with 8 internally meshed switches and inter-group global links connecting every group to every other group
- DragonFly Sparse (draft-przygienda-rift-dragonfly):
  * Simplifies each group (Group A, Group B, Group C) into a standard two-tier Leaf-Spine Clos (LA1/LA2 -> SA1/SA2, LB1/LB2 -> SB1/SB2, LC1/LC2 -> SC1/SC2)
  * Interconnects only the T2 Top-of-Fabric (ToF) spines across groups (SA1/SA2 <-> SB1/SB2 <-> SC1/SC2)
  * Uses RIFT Key-Value Store (K-store) advertisements to distribute inter-group global links and link-quality telemetry for non-shortest-path UCMP with split-horizon loop prevention
```

### 4.2 IS-IS for AI IP fabrics: Optimal Distributed Flooding and Flex Algo (`RFC 9350` / `RFC 9502`)

In a dense AI fabric with 32 or 64 spines and multiple parallel links per leaf-spine pair, standard link-state flooding causes every spine to replicate every new server prefix Link State PDU back to every leaf. That flooding storm wastes control-plane CPU cycles and slows convergence. Modernized IS-IS solves this problem and adds native IP traffic engineering planes without MPLS or SRv6 header overhead.

Under Optimal Distributed Flooding, each leaf elects a single designated spine to flood new server prefix updates rather than replicating across all spines. Furthermore, RFC 9350 and RFC 9502 standardize IS-IS Flexible Algorithm for native IPv4 and IPv6 prefix forwarding. Switches advertise a Flexible Algorithm Definition specifying calculation type, metric type, and bandwidth or delay constraints. One physical fabric can then host isolated logical planes for storage, inference, and training.

| `IS-IS` AI Fabric Capability | IETF Specification and Mechanism | Target Scale and Plane Mapping (`ADC` Ch. 8) |
|---|---|---|
| **1. Optimal Distributed Flooding** | `draft-white-lsr-distoptflood`: `leaf1` elects a single designated spine (`spine2`) to flood new server prefix `LSPs` across `T1/T2/T3/T4` Clos topologies. | Scales up to `2,500` switch nodes across `32` or `64` spines (`400G`/`800G` links) with minimal `LSP` fragment churn. |
| **2. `IS-IS` Flexible Algorithm (`Flex Algo`)** | `RFC 9350` (`FAD` tuple: Calculation Type, Metric Type, Constraints), `RFC 9502` (native IP Flex Algo via `IS-IS IPv4 Algorithm Prefix Reachability TLV` with `MTID`), and `draft-ietf-lsr-flex-algo-bw-con` (`min-bandwidth`, `max-link-delay`). | **`Flex Algorithm 128`** (`spine1/2`): Storage; **`Flex Algorithm 129`** (`spine3/4`): Inference; **`Flex Algorithm 130`** (`spine5/6`): Training elephant flows; **`Algorithm 0`**: default `SPF` fallback. |

### 4.3 Protocol comparison: eBGP vs RIFT vs IS-IS (`ADC` Table 8-1)

Architects must weigh topology support, frontend multi-tenancy, convergence speed, and operational complexity when selecting an AI underlay routing protocol. The table below compares eBGP, RIFT, and IS-IS across nine fabric design criteria.

| Characteristic | `eBGP` | `RIFT` (`RFC 9692`) | `IS-IS` (`RFC 9350` / `9502`) |
|---|---|---|---|
| **IP Clos `ECMP` topology support** | Yes | Yes | Yes |
| **DragonFly topology support** | No | **Yes** (`draft-przygienda-rift-dragonfly`) | No |
| **Multi-tenancy options for the frontend** | **Many** (`EVPN-VXLAN` `MAC-VRF` and `RT5`) | Limited | Limited |
| **Convergence speed** | Medium | **Fast** | **Fast** |
| **Link awareness** | Low (requires `BFD`/OAM/extensions) | **High** | **High** |
| **Full topology awareness** | Medium | **High** (northbound link-state) | Medium (`2,500`-node area scale) |
| **Automatic disaggregation on failure** | No | **Yes** | No |
| **Advertising fabric configuration data** | No | **Yes** (`K-store` metadata) | No |
| **Wide `ECMP` or `UCMP` (Unequal-Cost Multipathing)** | **Yes** (via Link Bandwidth Community) | **Yes** (native northbound `UCMP`) | No |

### 4.4 Network- and server-level multi-tenancy (`512` GPUs/rail, `H100 MIG`, `EVPN RT5`, and `VXLAN-GBP`)

Cloud GPU-as-a-Service providers and enterprise private AI clouds cannot allow one tenant's collective traffic or security boundary to bleed into another tenant's workspace. Isolation must hold at both the network rail layer for bare-metal tenants and the sub-GPU slice layer when single servers are shared.

At the network layer, EVPN Route Type 5 IP-VRFs and MAC-VRFs partition a 512-GPU rail into isolated tenant routing domains while allowing tenants to reuse overlapping IP subnets across rails. At the server layer, NVIDIA Multi-Instance GPU hardware-partitions each H100 GPU into up to seven isolated instances. Mapping each MIG instance to its own IEEE 802.1Q VLAN, MAC-VRF, and EVPN Type-5 IP-VRF delivers end-to-end CUDA-to-wire isolation without exhausting switch TCAM space.

| Multi-Tenancy Tier | Hardware and Protocol Architecture (`ADC` Ch. 8 Figs. 8-21..8-24) | Capacity and Isolation Numbers |
|---|---|---|
| **1. Bare-Metal (`BMSaaS`) Rail Multi-Tenancy** | `8` leaf switches $\times$ `8` spine switches built with `64 × 800 Gbps` radix switches. Each leaf allocates `32 × 800 Gbps` ports to spines (`4 × 800G` per spine = `25.6 Tbps`/leaf) and breaks out `32 × 800 Gbps` ports into `64 × 400 Gbps` server ports (`2 × 400G` breakout $\times 32$). | `8 × 64 = 512` GPUs per rail (`64` servers of `8` GPUs, `204.8 Tbps` `1:1` rail bisection). Partitioned into `4` bare-metal tenants of `128` GPUs/tenant using `EVPN RT5` (`RT5 IPVRF1..7`) + `MAC-VRF` (`RT2` symmetric IRB), reusing `8` IP subnets per tenant. |
| **2. Server + Network `H100 MIG` Multi-Tenancy** | NVIDIA `H100 MIG` partitions each GPU into `7` isolated instances (`GPU Instance 1..7`). Server-to-leaf links trunk `7` IEEE `802.1Q` tags (`VLAN 1..7`) into ToR leaves. | Each leaf maps `VLAN 1..7` `1:1` into `7` `MAC-VRF` instances (`MAC-VRF 1..7`) and `7` `EVPN Type-5 IP-VRFs` (`RT5 IPVRF 1..7`) for `Tenant 1..Tenant 7` without dynamic RADIUS `TCAM` exhaustion. |
| **3. Intra-Subnet Microsegmentation (`VXLAN-GBP`)** | Stamps a `16`-bit Group Policy ID (`GBP tag`) inside the VXLAN header on ingress when tenants or tiers share a subnet and `VNI`. | Egress ToR enforces microsegmentation rules in hardware without requiring additional `VRFs`. |

### 4.5 Extending BGP to the GPU server (`FRR`) and SRv6 compressed `16`-bit `uSID` traffic engineering

When GPU servers have multiple NICs or host containerized inference endpoints that migrate across racks, static default gateway routes on the host become a bottleneck. Running an open-source routing daemon such as FRRouting directly on the Linux GPU host or BlueField DPU extends BGP all the way to the endpoint. Each server peers with ToR leaves using 32-bit private ASNs and advertises an IP anycast service prefix for automatic leaf selection and host-level VRF isolation.

For centralized path steering without per-flow switch state, Segment Routing over IPv6 allows an ingress leaf to push a stack of Segment Identifiers onto each packet. Standard 128-bit SRv6 SIDs add significant header overhead when four hops are stacked inside a Segment Routing Header. Micro-segment SRv6 solves this by compressing each hop instruction into a 16-bit micro-SID inside a single 128-bit IPv6 Destination Address.

```text
Host-Level FRR BGP and SRv6 16-Bit uSID Carrier Math (ADC Ch. 8 Figs. 8-25..8-30):
1. Extending BGP to the GPU Server (FRR 32-bit Private ASNs):
   - Spines (spine1..spine4):   ASN 4294967100
   - Leaves (leaf1..leaf4):     ASN 4224967001, 4224967002, 4224967003, 4224967004 (or 4294967100 in iBGP RR mode)
   - Servers (server1..server4): ASN 4200000001, 4200000002, 4200000003, 4200000004
   - Advertised prefix: IP anycast inference/training service 192.168.10.10/32 with next hops NH1..NH4
2. Segment Routing over IPv6 (SRv6, RFC 8754 / RFC 8986) & Compressed 16-Bit uSID:
   - Controller discovery & programming: IGP or BGP-LS topology -> PCEP path placement (e.g., SID 5 transit spine -> SID 1 egress leaf)
   - Uncompressed SRH (RFC 8754): Next Header (0..7), Hdr Ext Len (8..15), Routing Type (16..23), Segments Left (24..31), Last Entry (0..7), Flags (8..15), Tag (16..31) + 128-bit SIDs formatted as Locator : Function (End / End.X) : Argument (RFC 8986)
   - Uncompressed 4-SID SRH overhead: 8-byte SRH base + 4 x 16-byte (128-bit) SIDs = 72 bytes (plus 40-byte outer IPv6 header = 112 bytes total)
   - Compressed SRv6 uSID (draft-filsfils-spring-net-pgm-extension-srv6-usid-16 & draft-filsfils-srv6ops-srv6-ai-backend):
     * Shared 32-bit locator block: fc00:0a10::/32
     * Remaining bits in 128-bit IPv6 Destination Address: (128 - 32) / 16 = 6 micro-SIDs (16-bit each), saving 72 bytes of SRH overhead
     * Carrier shift sequence: fc00:0a10:0005:0001:0000:: (ingress) -> fc00:0a10:0001:0000:0000:: (spine pops 0005) -> fc00:0a10:0000:0000:0000:: (egress leaf pops 0001)
```

---

## 5. End-to-end packet and control-plane walkthroughs

### 5.1 Walkthrough A: Ingress RoCEv2 flowlet vs GLB NNHN vs sDLB BTH opcode path selection

To see how SLB, DLB, GLB, and sDLB interact inside a single leaf switch, we can trace two concurrent transfers originating from a GPU server on LeafA toward a remote GPU server on LeafD. First, a control transfer uses an RDMA Read Request that requires strict in-order arrival. Immediately afterward, an AllReduce ring step sends bulk gradient payloads using RDMA Write Only frames toward a ConnectX-7 NIC.

| Walkthrough Stage | Packet / Control-Plane Attributes | Switch ASIC `PFE` Action on `LeafA` |
|---|---|---|
| **1. Control-plane table installation** | `SpineA` (`BGP ID 172.16.7.101`, `AS 65001`) and `SpineB` (`BGP ID 172.16.7.102`, `AS 65001`) peer with `LeafA` (`AS 65101`) over `RFC 5549` (`Capability Code 5`) and advertise `LeafD` with `BGP NNHN` (`Characteristic Code = 2`, `LeafD` `32-bit BGP ID`). | `Tomahawk 5` `GLB` app installs a 3-stage **simple path quality profile** combining local `Link A`/`Link B` quality with remote `Link X` (`SpineA -> LeafD`) and `Link Y` (`SpineB -> LeafD`) quality from `20 ms` `PFE` heartbeats. |
| **2. Control/Read flow (`RDMA Read Request 0x0C`)** | 5-tuple `192.168.1.20 -> 192.168.2.10, Proto 17, UDP 1024 -> 4791` (`CRC32 = 0x8BDA7C2D = 2,346,351,661`), `BTH Opcode = 0x0C`. | `0x0C` does not match the `sDLB` RDMA Write `TCAM` set (`0x06..0x0B`), so it uses per-flow `GLB`/`DLB` flowlet mode. Because `SpineA`'s `20 ms` heartbeat reports remote `Link X` degraded to band `1` (despite local `Link A` at band `7`), `LeafA` pins the flowlet to `Link B -> SpineB -> Link Y` (combined band `7`). |
| **3. Bulk gradient flow (`RDMA Write Only 0x0A`)** | `1,500-byte` (or `4,096-byte`) `RoCEv2` packets with `UDP 4791` and `BTH Opcode = 0x0A` (`RDMA Write Only`) to `ConnectX-7` / `BlueField-3`. | Matches ingress `TCAM` filter and invokes **`sDLB` per-packet spraying** across uncongested spines; destination NIC hardware reorder engine reassembles out-of-order datagrams (`B` at `T1`, `C` at `T2`, `A` at `T3`) directly in GPU memory. |

### 5.2 Walkthrough B: Multi-tenant `512`-GPU rail with `H100 MIG`, `EVPN RT5`, and `BGP DPF`

When a cloud provider commissions a 512-GPU rail, it must support both large bare-metal training tenants and smaller fractional-GPU inference tenants on the same physical switches. Combining EVPN Route Type 5 overlays with NVIDIA H100 MIG and BGP DPF underlay coloring satisfies both requirements cleanly.

| Tenant Layer | Configuration on the `512`-GPU Rail (`8` Leaves $\times$ `8` Spines of `64 × 800G` Switches = `204.8 Tbps`) | Isolation Result |
|---|---|---|
| **1. Bare-Metal (`BMSaaS`) Tenants** | `4` bare-metal tenants each lease `128` GPUs (`16` servers $\times 8$ GPUs) across `64 × 400G` server breakout ports and `32 × 800G` spine uplinks per leaf. | Segmented via `EVPN RT5` IP-VRFs (`RT5 IPVRF1..4`) or combined `MAC-VRF` (`RT2`) + `RT5`, reusing `8` rail subnets per tenant. |
| **2. Shared `H100 MIG` Tenants** | Shared nodes partitioned into `7` `MIG` instances (`MIG 1..7`) trunk `7` VLANs (`VLAN 1..7`) into ToR leaves. | Mapped `1:1` into `7` `MAC-VRF` instances (`MAC-VRF 1..7`) and `7` `EVPN RT5` IP-VRFs (`RT5 IPVRF 1..7`). |
| **3. `BGP DPF` Underlay Correlation** | `spine1` underlay `eBGP` session colored `black`; `spine2` session colored `gray`. `leaf4` originates `10.10.1.4/32` uncolored. | Ingress `leaf1` maps `Tenant 1` (`MAC-VRF-black` / `RT5-VRF-black`) to active underlay path `black` (`spine1`) with pre-installed ASIC backup path `gray` (`spine2`). |

---

## Commands and configurations that matter

### 1. Cumulus Linux `NVUE` and BCM `cmsh`: eBGP unnumbered, shared spine ASN, and RoCEv2 adaptive routing

On NVIDIA Spectrum switches running Cumulus Linux, operators configure routing and QoS through NVUE and NVIDIA Base Command Manager. You can enable RFC 5549 BGP unnumbered with a shared spine ASN, lossless RoCEv2 QoS, and hardware adaptive routing in a single configuration commit.

```bash
# (untested here) On leaf1 (ASN 65101): enable BGP unnumbered toward spine1..spine4 (shared ASN 65001)
nv set router bgp autonomous-system 65101
nv set router bgp router-id 172.16.7.181
nv set vrf default router bgp neighbor swp1-32 remote-as external
nv set vrf default router bgp neighbor swp1-32 type unnumbered
nv set vrf default router bgp address-family ipv4-unicast enable on
nv set vrf default router bgp address-family ipv4-unicast redistribute connected enable on
nv set vrf default router bgp address-family l2vpn-evpn enable on

# (untested here) Enable lossless RoCEv2 QoS (PFC prio 3 + ECN) and hardware adaptive routing / DLB
nv set qos roce enable on
nv set interface swp1-64 link mtu 9216
nv set router adaptive-routing enable on
nv config apply
```

From the BCM head node, administrators use `cmsh` to audit the switch's NVUE management mode, uplink port assignments, hardware inventory, and NetQ telemetry port.

```text
BCM 11 Cumulus Linux Switch Management Reference (bcm11-admin Ch. 3 §3.8-3.12):
- NVUE REST API port: 8765 (nv CLI and REST management)
- nvconfigurationmode options: auto, manual, or file (pushes /etc/nvue.d/startup.yaml and cm-startup.yaml)
- SN2201 OOB/management switch specs: 8,048,771,072 B RAM, 115,923,419,136 B NVMe disk, uplink ports 15 16
- NetQ telemetry streaming port: HTTPS port 443
```

```bash
# (untested here) Inspect Cumulus NVUE switch management and port mapping in BCM 11 cmsh
cmsh -c "device; use switch01; get nvconfigurationmode; get uplinks; sysinfo"
cmsh -c "device; use switch01; accesssettings; get port"
cmsh -c "device; switchoverview"
```

### 2. Inspecting BGP unnumbered `Capability Code 5` (`Extended Next Hop`) and `MP_REACH_NLRI` (`Code 14`)

When an unnumbered session fails to install IPv4 routes, you should verify that both switches negotiated RFC 5549 Extended Next Hop Encoding and exchanged IPv6 link-local next hops. The commands below inspect the neighbor capabilities in `vtysh` and capture the BGP OPEN and UPDATE frames on the wire.

```bash
# (untested here) Verify BGP unnumbered neighbor capabilities and IPv4 routes over IPv6 LLA next hops
vtysh -c "show bgp ipv4 unicast summary"
vtysh -c "show bgp neighbors swp11" | grep -E "Extended Next Hop|fe80::|Hold time"
vtysh -c "show bgp ipv4 unicast 172.16.7.181/32"

# (untested here) Packet capture on Eth11 / swp11 matching ADC Ch 8 Fig 8-2 (OPEN) & Fig 8-3 (UPDATE)
tcpdump -ni swp11 -vvv "ip6 and tcp port 179"
```

The decoded packet capture confirms Capability Code 5 in Frame 22 and Multiprotocol Reachable NLRI Type Code 14 in Frame 28.

```text
Frame 22: 189 bytes on wire (1512 bits), IPv6 fe80::e59:9cff:fef1:32.52659 > fe80::e59:9cff:fe22:5dd7.179
  Border Gateway Protocol - OPEN Message (Type 1, Length 81, My AS: 65001, Hold Time: 90s, BGP ID: 172.16.7.101)
    Optional Parameters Length: 52
    Capability: Extended Next Hop Encoding (Code 5, Length 6)
      AFI: IPv4 (1), SAFI: Unicast (1), Next Hop AFI: IPv6 (2)

Frame 28: 358 bytes on wire (2864 bits)
  Border Gateway Protocol - UPDATE Message (Type 2, Length 82, Path Attributes Length: 46)
    ORIGIN: IGP, AS_PATH: 65001 (Flags 0x40, Type 2, Length 6)
    MP_REACH_NLRI (Flags 0x90, Type Code 14, Length 42):
      AFI: IPv4 (1), SAFI: Unicast (1), Next Hop: fe80::9:0a:2f:c1:f1:32
      NLRI: 172.16.7.181/32
```

### 3. Configuring `DLB`, `GLB NNHN`, `sDLB` `BTH` opcode filters, and `BGP DPF` colored sessions

On switches supporting Broadcom DLB and GLB or Juniper Junos Evo BGP DPF and RoCEv2 BTH TCAM classification, the configuration stanzas map directly to the hardware forwarding pipelines.

```text
# (untested here) Conceptual Junos Evo / Broadcom Tomahawk 5 DLB + GLB + sDLB + BGP DPF stanza
forwarding-options {
    enhanced-hash-key {
        ecmp-dlb {
            mode flowlet;
            inactivity-interval 256;          # Flowlet pause threshold in microseconds
            glb {
                enable;                       # Enable Tomahawk 5 GLB app (20 ms PFE heartbeats)
            }
        }
        rocev2-bth-opcode-spray {
            udp-destination-port 4791;
            bth-opcode [ 0x06 0x07 0x08 0x09 0x0a 0x0b ]; # RDMA Write opcodes -> per-packet spray
        }
    }
}
protocols bgp {
    group underlay-spines {
        family inet { unicast { extended-nexthop; add-path { send; receive; } } }
        capability next-next-hop-nodes;       # draft-wang-idr-next-next-hop-nodes (Code 2)
        neighbor fe80::e59:9cff:fef1:32 {
            peer-as 65001;
            dpf-session-color black;          # draft-wang-idr-dpf active plane color
        }
    }
}
```

### 4. Host-level `FRR` eBGP (`32`-bit ASNs) and `EVPN-VXLAN` `MIG` multi-tenancy

On a multi-tenant GPU compute node partitioned with H100 MIG, the host administrator creates seven VLAN subinterfaces corresponding to the seven GPU instances and advertises the anycast service address via FRR BGP.

```bash
# (untested here) Verify 7 H100 MIG instances on the GPU server and bind VLAN 1..7 subinterfaces
nvidia-smi mig -lgi
for id in 1 2 3 4 5 6 7; do
  ip link add link ens1f0 name ens1f0.${id} type vlan id ${id}
  ip link set dev ens1f0.${id} mtu 9000 up
done

# (untested here) Host FRR BGP configuration (server1 AS 4200000001 -> leaf1 AS 4224967001 -> spine1 AS 4294967100)
vtysh -c "show running-config bgp"
# router bgp 4200000001
#  neighbor ens1f0 interface remote-as 4224967001
#  address-family ipv4 unicast
#   network 192.168.10.10/32
```

---

## How it fails

When load-balancing modes or routing policies are misconfigured in an AI cluster, symptoms appear as asymmetric link saturation, PFC pause cascades, or RDMA sequence number errors. The table below maps six production failure modes to their root causes and deterministic fixes.

| Failure Mode | Observable Symptom in Production | Root Cause in Data or Control Plane | Deterministic Fix |
|---|---|---|---|
| **1. Low-entropy `SLB` hash collision on `UDP 4791`** | One leaf-to-spine `200 Gbps` (or `400G`/`800G`) uplink runs at **`100%` utilization** with rising `tx_ecn_marked_prio3` and `rx_pfc_prio3`, while a parallel spine uplink sits at **`50%` or `0%`**. | Static 5-tuple `CRC32` hashing maps two `100 Gbps` elephant flows (`Flow2 + Flow4`) to `SpineB` and two `50 Gbps` flows (`Flow1 + Flow3`) to `SpineA` without checking port load or queue depth. | Enable **`DLB` flowlet mode** (settling both links at **`75%` / `150 Gbps`**) or include `RoCEv2 BTH QPair` fields in the hash seed; use **`sDLB`** for RDMA Write flows. |
| **2. Downstream spine collision (`Link X` congestion) under local-only `DLB`** | Ingress leaves `LeafA` and `LeafB` show balanced local uplinks, yet `SpineA`'s downlink `Link X` (`SpineA -> LeafD`) suffers heavy `DCQCN` rate cuts and `PFC` pause propagation while `SpineB -> LeafD` (`Link Y`) is idle. | Local `DLB` evaluates only the immediate `Leaf -> Spine` link quality band (`0..7`) and is blind to downstream `Spine -> Egress Leaf` congestion when multiple leaves target `LeafD`. | Enable **Global Load Balancing (`GLB`)** with `BGP NNHN` (`draft-wang-idr-next-next-hop-nodes` `Code 2`) and **`20 ms`** `PFE` heartbeats so `LeafA` steers new flows via `SpineB -> Link Y`. |
| **3. Blind per-packet spraying (`Random Spray`) onto NICs without Read/Send reorder support** | Pairwise throughput collapses, `ib_read_bw` / `rccl` / `nccl` logs `RETRY_EXC_ERR` or `PSN` gap NAKs, and host CPU spikes reassembling out-of-order packets (`Datagram B` at `T1`, `C` at `T2`, `A` at `T3`). | Per-packet spraying was enabled globally on all traffic rather than restricted to RDMA operations supported by the NIC's hardware reorder engine. | Deploy **Selective Packet Spraying (`sDLB`)** via ingress `TCAM ACLs` matching `UDP 4791` + `BTH` **RDMA Write opcodes (`0x06..0x0B`)** on `ConnectX-6/7` or `BlueField` DPUs; keep Read/Send per-flow. |
| **4. Suboptimal valley tromboning (`leaf1 -> spine1 -> leaf2 -> spine2 -> leaf3`) on link failures** | After multiple spine-link failures, transit `leaf2` (`400G`/`800G`) unexpectedly saturates and jobs local to `leaf2` stall, even though `server1` (`leaf1`) is communicating with `server5` (`leaf3`). | Spines were assigned **distinct BGP ASNs (`65001..65004`)** instead of a shared spine ASN; `spine2` accepted a route bounced through transit `leaf2` (`AS_PATH 65001, 65102, 65101`). | Assign the **same BGP ASN (`65001`) to all spines in a tier** (`RFC 7938` / `Fig. 8-4`) so default `AS_PATH` loop detection rejects any path that traverses two spines via a transit leaf. |
| **5. `BGP DPF` color pruning mismatch or missing backup path ID** | High-priority tenant traffic pinned to `fab-id black` drops completely (`No route to host`) when `spine1` goes down, or leaks onto shared best-effort spines during normal operation. | Either the `eBGP` session on `spine2` was colored `black` instead of `gray`, or ingress `leaf1` lacked the pre-installed `gray` backup path (`10.10.1.4/32` via `spine2`). | Audit `BGP DPF` session colors (`black` on `spine1`, `gray` on `spine2`), verify uncolored route origination on egress `leaf4`, and confirm both active (`black`) and backup (`gray`) next hops in `leaf1` `FIB`. |
| **6. Unequal border/super-spine link speeds overloaded under equal-weight `ECMP`** | On a border pod with `400G`, `800G`, `100G`, and `400G` uplinks (`spine1..4`), `spine3`'s `100 Gbps` link saturates at `100%` and drops packets as soon as total northbound traffic exceeds `400 Gbps`. | Standard `ECMP` splits flows `25%/25%/25%/25%` regardless of northbound link capacity, or keeps advertising a prefix from a spine that lost `1` of `4` downlinks. | Enable **BGP Link Bandwidth Extended Community (`WCMP` / `WPS`)** to weight buckets **`20% / 45% / 15% / 20%`**, and configure **minimum BGP peers per prefix (`min-peers 4`)** to withdraw degraded spines. |

---

## Hands-on lab

This lab runs on a local workstation or a Nebius GPU node using the Python 3 standard library. No root privileges or physical switch hardware are required.

### Step 1: Run the self-checking load-balancing and AI routing lab suite

Execute the companion lab script `code/part12/load_balancing_routing_ai_lab.py` to run 25 automated verification checks covering every calculation and protocol table in this chapter.

```bash
python3 -B code/part12/load_balancing_routing_ai_lab.py
```

Expected output verified locally:

```text
=== Chapter 12.14 Lab: Load Balancing and Routing for AI Fabrics ===
  [PASS] ADC Ch 6 simple ECMP modulo: hash_key=10 -> 10 mod 5 = 0, hash_key=11 -> 11 mod 5 = 1
  [PASS] ADC Ch 6 5-tuple hex packing: C0A80114 C0A8020A 11 0400 12B7
  [PASS] ADC Ch 6 CRC32 key 0x8BDA7C2D (2,346,351,661): mod 5 = 1 and mod 8 = 5
  [PASS] ADC Ch 6 resilient hashing: 512/1024 buckets; 8-bucket example (0,1,2,3,4,0,1,2) maps key=10 -> bucket 2 -> iface 2, only buckets (2,7) remapped on failure (25% vs 75% modulo churn)
  [PASS] ADC Ch 6 symmetric hashing: normalized XOR 5-tuple produces identical key for A->B and B->A
  [PASS] ADC Ch 6 Figs 6-2 & 6-4: Flows (50, 100, 50, 100) Gbps on 200G links yield SLB (100G=50%, 200G=100%) vs DLB (150G=75%, 150G=75%)
  [PASS] ADC Ch 6 DLB quality bands (0..7), flowlet inactivity timer reassignment (SpineB -> SpineA), and reactive path rebalancing (SpineA -> SpineC)
  [PASS] ADC Ch 6 GLB NNHN (Characteristic Code=2, 32-bit BGP IDs, 20 ms Tomahawk 5 heartbeats, simple vs compound profile) avoids remote Link X congestion on SpineA->LeafD
  [PASS] ADC Ch 6 Figs 6-14 & 6-15 per-packet spraying: 3 x 1500B datagrams (A, B, C) over 3 x 100G ports arrive out of order (T1=B, T2=C, T3=A) at 192.168.1.1
  [PASS] ADC Ch 6 sDLB TCAM ACL: RoCEv2 UDP 4791 BTH RDMA Write opcodes (0x06..0x0B) trigger PER_PACKET_SPRAY while Read/Send stay PER_FLOW_DEFAULT
  [PASS] ADC Ch 6 Table 6-1 capability matrix: SLB (High), DLB (Medium, local BW+queue), GLB (Low, +remote link quality), TELB (Low, local+remote+BTH+telemetry)
  [PASS] ADC Ch 8 BGP Unnumbered (RFC 5549): 16-bit private ASNs 64512..65535, 32-bit private ASNs 4200000000..4294967294, spine1 fe80::e59:9cff:fef1:32 <-> leaf1 fe80::e59:9cff:fe22:5dd7 TCP 52659->179
  [PASS] ADC Ch 8 Figs 8-2 & 8-3 packet captures: Frame 22 OPEN (189B/1512b, Cap Code 5 len 6, AFI=1 SAFI=1 NH_AFI=2, AS 65001, hold 90s, ID 172.16.7.101) & Frame 28 UPDATE (358B/2864b, MP_REACH_NLRI type 14 len 42, 172.16.7.181/32)
  [PASS] ADC Ch 8 Figs 8-4 & 8-5: Shared spine ASN 65001 with leaf ASNs 65101..65104 rejects leaf-spine-leaf-spine valley paths whereas distinct spine ASNs 65001..65004 allow suboptimal tromboning
  [PASS] ADC Ch 8 Fig 8-6 BGP ADD-PATH: DC GW (65503) -> border-leaf1 (65501) & border-leaf2 (65502) -> spine2 (65001) advertises both NH1 and NH2 for 10.10.108.0/24 to leaf2 (65102)
  [PASS] ADC Ch 8 Fig 8-8 WCMP & Link Bandwidth Extended Community: spine1..4 (400G, 800G, 100G, 400G = 1,700G) configured as 20%/45%/15%/20% (sum=100%), and spine withdraws 10.10.101.0/24 when active peers drop from 4 to 3
  [PASS] ADC Ch 8 BGP DPF (draft-wang-idr-dpf): 10.10.1.4/32 pruned to black (active via spine1) and gray (backup via spine2); 128x GPU-0 on 3x400G = 1.2 Tbps/leaf; 4 color mapping modes
  [PASS] ADC Ch 8 RIFT (RFC 9692): >=1,000 switch nodes, link-state northbound + distance-vector southbound, UDP hello + IPv6 ND, 7 canonical DragonFly groups x 8 switches/group + DragonFly Sparse ToF K-store
  [PASS] ADC Ch 8 IS-IS Flood Reduction & Flex Algo: 2,500 switch nodes, 32/64 spines, RFC 9350 FAD + RFC 9502 IP Flex Algo planes 128 (storage), 129 (inference), 130 (training)
  [PASS] ADC Ch 8 Table 8-1 routing protocol matrix: eBGP (Many frontend multi-tenancy, Wide ECMP/UCMP) vs RIFT (DragonFly=Yes, auto-disaggregation=Yes, K-store config=Yes) vs IS-IS (Fast convergence, High link awareness)
  [PASS] ADC Ch 8 Figs 8-21..8-24 multi-tenancy: 8 leafs x 8 spines (64x800G switch: 64x400G server breakout + 32x800G spine) = 512 GPUs/rail, 4 tenants x 128 GPUs BMS, 7 H100 MIG instances x 7 VLANs/MAC-VRFs/RT5-IP-VRFs + VXLAN-GBP
  [PASS] ADC Ch 8 Figs 8-25 & 8-26 BGP to the server: spine AS 4294967100, leaf ASNs 4224967001..4224967004, host ASNs 4200000001..4200000004, anycast service 192.168.10.10/32
  [PASS] ADC Ch 8 SRv6 (RFC 8754 / RFC 8986) & 16-bit uSID carrier math: 128-bit SID holds 6 x 16-bit uSIDs after 32-bit locator, saving 72B on a 4-hop SRH and shifting SID 5 -> SID 1
  [PASS] BCM 11 Cumulus Linux NVUE & NetQ management: REST API port 8765, NetQ port 443, SN2201 8,048,771,072 B RAM / 115,923,419,136 B disk, uplinks (15, 16)
  [PASS] 1:1 non-oversubscribed 512-GPU rail bandwidth invariant: 8 leafs x 64x400G server ports = 204.8 Tbps == 8 leafs x 32x800G spine ports = 204.8 Tbps

Summary: 25 passed, 0 failed
```

### Step 2: Inspect the reference simulator outputs directly

Run `code/part12/load_balancing_routing_ai.py` to print the 5-tuple hex and CRC32 breakdown, SLB versus DLB link utilization, WCMP 64-bucket allocation, and SRv6 16-bit uSID carrier shift.

```bash
python3 -B code/part12/load_balancing_routing_ai.py
```

Expected output:

```text
ADC Ch 6 5-tuple C0A80114C0A8020A11040012B7 -> CRC32 0x8BDA7C2D (2346351661), mod 5 = 1, mod 8 = 5
SLB spine util: (50%, 100%) vs DLB spine util: (75%, 75%)
ADC Ch 8 WCMP 64-bucket counts: {'spine1': 13, 'spine2': 28, 'spine3': 10, 'spine4': 13}
ADC Ch 8 SRv6 uSID carrier: fc00:0a10:0005:0001:0000:: -> fc00:0a10:0001:0000:0000::
```

---

## Common first mistakes

1. **Assuming DLB assigned-flow mode is sufficient for AI training clusters:** In assigned-flow mode, a flow is placed on the highest-quality local link at creation time and never rebalanced. Because RoCEv2 Queue Pairs between GPU peers persist across entire training runs, assigned-flow mode locks elephant flows onto links whose quality later degrades. Always use DLB flowlet mode with an inactivity timer and optional reactive rebalancing, or enable GLB and sDLB.
2. **Enabling GLB without verifying BGP NNHN and underlay peering scope:** GLB requires control-plane next-next-hop-nodes capability to map which spine interface reaches which egress leaf, along with data-plane heartbeats restricted to links with active eBGP underlay peering. Without BGP NNHN, the leaf receives spine link quality numbers but cannot correlate them to the destination prefix's egress leaf.
3. **Assigning unique BGP ASNs to every spine switch in a tier:** Giving spines distinct ASNs disables BGP's built-in `AS_PATH` valley-loop prevention between spines. Failed leaf-to-spine topologies can then bounce elephant flows through a transit leaf. Always share a single ASN across all spines in the same Clos stage.
4. **Deploying uncompressed SRv6 SRH stacks on jumbo RoCEv2 frames without checking MTU and DCQCN support:** A four-segment uncompressed SRH adds 72 bytes on top of the 40-byte outer IPv6 header for 112 bytes total. That extra header will fragment or drop RoCEv2 frames unless switch interfaces are raised to 9,216 bytes and compressed 16-bit uSID carriers are used.

---

## Exercises

1. **5-Tuple CRC32 Static Load Balancing, Resilient Buckets, and SLB vs DLB Link Utilization:**
   Use `compute_adc_ch6_five_tuple_slb` and `compare_slb_vs_dlb_spine_utilization` to verify static and dynamic hashing. Convert the 5-tuple into its 13-byte hex string, state its CRC32 key, and compute the outgoing interface index for 5 and 8 active links. Then determine which resilient buckets remap when `interface_2` fails and compare SLB versus DLB link utilization.

   ```text
   Exercise 1 Reference Parameters:
   - 5-tuple: SRC_IP = 192.168.1.20 (C0A80114), DST_IP = 192.168.2.10 (C0A8020A), IP_PROTO = 17 (11), SRC_PORT = 1024 (0400), DST_PORT = 4791 (12B7)
   - CRC32 key: 0x8BDA7C2D = 2,346,351,661 (N = 5 -> mod 5 = 1; N = 8 -> mod 8 = 5; simple keys 10 mod 5 = 0, 11 mod 5 = 1)
   - 8-bucket resilient table (0, 1, 2, 3, 4, 0, 1, 2): hash_key = 10 -> Bucket 2 -> interface_2; interface_2 failure remaps buckets (2, 7) = 25% churn vs 75% modulo churn
   - Flows (50, 100, 50, 100 Gbps) on 2 x 200 Gbps uplinks: SLB = (50%, 100%) vs DLB = (75%, 75%)
   ```

2. **DLB Flowlet Timers, GLB NNHN, and Selective Packet Spraying:**
   Use `simulate_dlb_flowlet_and_glb_nnhn`, `classify_sdlb_rocev2_packet`, and `build_adc_table_6_1` to analyze path selection. Explain how DLB quality bands, flowlet inactivity timers, and reactive path rebalancing operate, and why local-only DLB suffers downstream collisions. Then detail Tomahawk 5 GLB and sDLB TCAM opcode classification.

   ```text
   Exercise 2 Reference Parameters:
   - DLB: quality bands 0..7, flowlet reassignment SpineB -> SpineA after pause > inactivity timer, reactive rebalancing SpineA -> SpineC, downstream collision on Link X (SpineA -> LeafD)
   - GLB (Tomahawk 5): draft-wang-idr-next-next-hop-nodes (Characteristic Code = 2, 32-bit Next-hop and Next-next-hop BGP IDs), simple vs compound profiles, 20 ms PFE heartbeats
   - Per-packet & sDLB: 3 x 1,500 B datagrams (A, B, C) across 3 x 100 Gbps ports to 192.168.1.1 arrive B (T1), C (T2), A (T3); TCAM ACL on UDP 4791 BTH RDMA Write opcodes (0x06..0x0B) on ConnectX-6/7 and BlueField
   ```

3. **BGP Unnumbered Packet Capture and Spine ASN Loop-Prevention Analysis:**
   Use `evaluate_bgp_spine_asn_allocation` to inspect control-plane peering. Trace the BGP unnumbered session setup between `spine1` and `leaf1`, including all fields of Frame 22 and Frame 28. Then compare `AS_PATH` loop prevention under distinct versus shared spine ASNs, and explain ADD-PATH and ingress `AS-PATH` strip-and-replace.

   ```text
   Exercise 3 Reference Parameters:
   - Peers on Eth11: spine1 (0c:59:9c:f1:00:32, fe80::e59:9cff:fef1:32, AS 65001, BGP ID 172.16.7.101) <-> leaf1 (0c:59:9c:22:5d:d7, fe80::e59:9cff:fe22:5dd7, TCP 52659 -> 179)
   - Frame 22 (OPEN, 189 B / 1,512 b, Len 81, Hold 90 s, Opt Params 52, Capability Code 5 Len 6 with AFI=1, SAFI=1, NH_AFI=2) & Frame 28 (UPDATE, 358 B / 2,864 b, Len 82, Path Attr 46, MP_REACH_NLRI Type 14 Len 42, 172.16.7.181/32)
   - ASN loop check: server1 (10.10.1.1/24, leaf1 AS 65101) -> server5 (10.10.5.1/24, leaf3 AS 65103) under distinct spine ASNs (65001..65004) vs shared spine ASN (65001)
   - ADD-PATH: DC GW 65503 -> border-leaf1 65501 (NH1) & border-leaf2 65502 (NH2) -> spine2 65001 -> leaf2 65102 for 10.10.108.0/24; server101 AS-PATH strip-and-replace
   ```

4. **WCMP Link Bandwidth Extended Community, Minimum Peers, and BGP DPF:**
   Use `compute_wcmp_link_bandwidth_distribution` and `build_bgp_dpf_plane_plan` to model weighted and deterministic routing. Verify the WCMP traffic split and 64-bucket counts across four heterogeneous spines, and determine when a spine withdraws a prefix under a minimum-peers policy. Then trace BGP DPF color pruning and RUD capacity allocation.

   ```text
   Exercise 4 Reference Parameters:
   - WCMP & WPS: spine1..4 (AS 65001) with 400G, 800G, 100G, 400G (1,700 Gbps total) -> 20%, 45%, 15%, 20% (13, 28, 10, 13 of 64 buckets); 10.10.101.0/24 withdrawn when peers drop from 4 to 3
   - BGP DPF (draft-wang-idr-dpf): 10.10.1.4/32 from leaf4 pruned to active black (spine1) and backup gray (spine2) on leaf1; 128 x GPU-id 0 allocated 3 x 400 Gbps = 1.2 Tbps/leaf in RUD; 4 color mapping modes
   ```

5. **RIFT, DragonFly Sparse, and IS-IS Optimal Distributed Flooding and Flex Algo:**
   Use `build_adc_table_8_1` to compare interior gateway protocols. Explain how RIFT combines northbound link-state flooding with southbound distance-vector default routing and how DragonFly Sparse simplifies cabling. Then explain IS-IS designated-spine flood reduction and Flex Algo plane slicing.

   ```text
   Exercise 5 Reference Parameters:
   - RIFT (RFC 9692, >= 1,000 switches): UDP hello + IPv6 ND, automatic disaggregation, canonical DragonFly (7 groups x 8 switches) vs DragonFly Sparse (Group A/B/C Clos interconnected at T2 ToF spines SA1/2, SB1/2, SC1/2 with K-store in draft-przygienda-rift-dragonfly)
   - IS-IS (2,500 switches, 32/64 spines): draft-white-lsr-distoptflood (leaf1 elects spine2); RFC 9350 (FAD) + RFC 9502 (MTID) planes 128 (spine1/2 Storage), 129 (spine3/4 Inference), 130 (spine5/6 Training); Table 8-1 (9 rows)
   ```

6. **Multi-Tenant 512-GPU Rail, Server-Level BGP, and SRv6 16-Bit uSID Math:**
   Use `compute_multitenant_rail_plan` and `compute_srv6_usid_carrier_shift` to verify multi-tenancy and segment routing. Confirm the port and bandwidth math for a 512-GPU rail, its four-tenant bare-metal split, its seven-instance H100 MIG mapping, and server-level FRR BGP. Finally, show how six 16-bit micro-SIDs fit inside an IPv6 Destination Address and shift left at each hop.

   ```text
   Exercise 6 Reference Parameters:
   - 512-GPU rail: 8 leaves x 8 spines of 64 x 800G switches (64 x 400G server breakout + 32 x 800G spine uplinks/leaf = 25.6 Tbps/leaf, 204.8 Tbps rail), 4 x 128-GPU BMS tenants (EVPN RT5), 7 H100 MIG instances (VLAN 1..7 -> MAC-VRF 1..7 -> RT5 IPVRF 1..7), VXLAN-GBP
   - Host FRR BGP: spine 4294967100, leaf 4224967001..4, server 4200000001..4 advertising anycast 192.168.10.10/32
   - SRv6 uSID: 72-byte 4-hop SRH savings; 6 x 16-bit uSIDs after 32-bit locator fc00:0a10::/32 (fc00:0a10:0005:0001:0000:: -> fc00:0a10:0001:0000:0000:: -> fc00:0a10:0000:0000:0000::)
   ```

---

## Interview angles

1. **"Walk me through why traditional 5-tuple ECMP fails in a RoCEv2 AI training cluster, and how SLB, DLB, GLB, and sDLB differ in hardware."**
   RoCEv2 uses fixed UDP destination port 4791 and a small number of persistent elephant Queue Pair flows. Even with resilient bucket tables, SLB ignores link load. It can hash two 100 Gbps flows onto one 200 Gbps spine link while placing two 50 Gbps flows on another. DLB samples local port bandwidth and queue depth in the PFE across quality bands 0 to 7. It rebalances across inter-burst pauses via the flowlet inactivity timer so both spines run at 75% utilization. GLB on Tomahawk 5 adds BGP NNHN and 20 ms PFE heartbeats so ingress leaves see downstream spine-to-egress-leaf congestion. Finally, sDLB uses ingress TCAM ACLs to match BTH RDMA Write opcodes and spray packets across all spines. The target ConnectX-6, ConnectX-7, or BlueField NIC then reorders those RDMA Write payloads in hardware.
2. **"Should we assign unique BGP ASNs or a shared ASN to the spine switches in our AI Clos underlay?"**
   Always assign a shared BGP ASN such as 65001 to all spines in the same tier and unique ASNs to each ToR leaf, following RFC 7938. Suppose spines have unique ASNs and multiple uplinks fail. A route from one leaf can bounce through a first spine down to a transit leaf, up to a second spine, and down to the destination leaf. Because no ASN repeats in `AS_PATH`, BGP accepts the path. In an AI cluster with 400 Gbps or 800 Gbps elephant flows, that valley trombone saturates the transit leaf and stalls innocent training jobs. With a shared spine ASN, the second spine immediately drops the route bounced from the transit leaf via standard `AS_PATH` loop detection.
3. **"When would you choose eBGP with BGP DPF versus RIFT or IS-IS Flex Algo for an AI backend fabric?"**
   Choose eBGP with RFC 5549 unnumbered peering, Link Bandwidth WCMP, and BGP DPF session coloring when you want multi-vendor familiarity and rich policy control. It also integrates directly with unified EVPN-VXLAN multi-tenancy. Choose RIFT under RFC 9692 for thousand-switch Fat-Tree or DragonFly Sparse topologies that need sub-second UDP hello convergence and tiny leaf FIBs. RIFT also provides automatic disaggregation on failure and K-store fabric configuration distribution. Choose IS-IS with Optimal Distributed Flooding and RFC 9502 native IP Flex Algo when you want pure Layer-2 link-state security up to 2,500 switches. It isolates storage, inference, and training onto constraint-based logical planes without SR-MPLS or SRv6 headers.

---

## Checkpoint questions (20)

<details><summary>`&lt;strong>`1. In a three-stage Clos fabric, how does an ingress leaf switch install ECMP routes learned from multiple spines, and why do multiple destination prefixes share a single ASIC `nh-id`?`&lt;/strong>`</summary>

When LeafB advertises GPU2's IP prefix to SpineA, SpineB, and SpineC, each spine rewrites the BGP next hop to itself. Each spine then advertises the prefix with identical attributes to LeafA. LeafA's control plane installs a single shared hardware ECMP group (`ASIC ECMP nh-id123 -> Unicast_nh1..3`) in the PFE. Sharing the same `nh-id` across all remote prefixes reachable through the same 32 or 64 spines conserves hardware next-hop table memory in the switch ASIC.
</details>

<details><summary>`&lt;strong>`2. Walk through the exact 5-tuple hexadecimal packing and CRC32 modulo result for `192.168.1.20 -> 192.168.2.10, UDP 17, 1024 -> 4791`.`&lt;/strong>`</summary>

The fields pack into 13 bytes as `192.168.1.20 = C0A80114`, `192.168.2.10 = C0A8020A`, `Proto 17 = 11`, `UDP 1024 = 0400`, and `UDP 4791 = 12B7`. Concatenating them forms `C0A80114 C0A8020A 11040012 B7`. The hardware CRC32 result is `0x8BDA7C2D` (`2,346,351,661` decimal). Raw modulo selects interface index 1 for 5 active links (`0x8BDA7C2D % 5 = 1`) and interface index 5 for 8 active links (`0x8BDA7C2D % 8 = 5`).
</details>

<details><summary>`&lt;strong>`3. How does resilient hashing with `512` or `1,024` buckets reduce flow churn compared to raw `hash_key mod N` when a link fails?`&lt;/strong>`</summary>

Under raw `hash_key mod N`, changing the active link count from 5 to 4 alters the modulo divisor and remaps 75% of active flows. Resilient hashing maps `hash_key mod B` into a fixed table of 512 or 1,024 buckets. In our simplified 8-bucket example, `hash_key = 10` maps to `Bucket 2 -> interface_2`. When `interface_2` fails, the ASIC reassigns only Bucket 2 and Bucket 7 (25% of buckets) and leaves all other flows untouched.
</details>

<details><summary>`&lt;strong>`4. What is symmetric hashing in Static Load Balancing (SLB), and when is it required in a data center fabric?`&lt;/strong>`</summary>

Symmetric hashing applies a sorting normalization or bitwise XOR operation over the source and destination IP pair and UDP port pair before computing CRC32 or CRC16. Both forward and reverse packets of a bidirectional flow then produce the exact same hash key and egress interface. It is required when steering flows through stateful firewalls or inline inspection appliances.
</details>

<details><summary>`&lt;strong>`5. Using the four-flow example (`50, 100, 50, 100 Gbps` over two `200 Gbps` uplinks), explain why `DLB` outperforms `SLB`.`&lt;/strong>`</summary>

SLB assigns an equal number of flows to each link without checking bandwidth. It can place the two 50 Gbps flows (100 Gbps or 50% utilization) on SpineA and the two 100 Gbps flows (200 Gbps or 100% utilization) on SpineB. DLB tracks real-time port bandwidth and queue depth via hardware link quality bands 0 to 7. It pairs one 50 Gbps flow and one 100 Gbps flow on each spine so both 200 Gbps uplinks run at 150 Gbps or 75% utilization.
</details>

<details><summary>`&lt;strong>`6. Compare `DLB` assigned-flow mode, flowlet mode (inactivity timer), and reactive path rebalancing.`&lt;/strong>`</summary>

Assigned-flow mode pins a flow to its initial interface for its entire lifetime. That is unsuitable for long-lived AI Queue Pairs because link quality changes later. Flowlet mode monitors inter-packet gaps against a configured inactivity timer. When a GPU flow pauses longer than the timer between tasks, the next burst is reassigned to a higher-quality spine without reordering packets. Reactive path rebalancing migrates continuous elephant flows that never pause when their current link's quality degrades relative to other ECMP paths.
</details>

<details><summary>`&lt;strong>`7. Why can congestion still occur at the spine under local `DLB`, and how does `GLB` (`draft-wang-idr-next-next-hop-nodes`) prevent it?`&lt;/strong>`</summary>

Local DLB checks only the immediate leaf-to-spine uplink quality. When LeafA and LeafB both send elephant flows to LeafD via SpineA, they collide on the single downstream downlink `Link X` from SpineA to LeafD. GLB on Tomahawk 5 learns which spine interfaces reach LeafD via BGP NNHN (`Characteristic Code = 2`). It also exchanges hardware PFE link-quality heartbeats every 20 ms on BGP-peered links. LeafA combines local and remote quality into a simple or compound profile and steers around `Link X` via SpineB and `Link Y`.
</details>

<details><summary>`&lt;strong>`8. What happens when three `1,500-byte` datagrams (`A, B, C`) of a `100 Gbps` flow are sprayed per-packet across three `100 Gbps` spine paths, and how does `sDLB` handle this safely?`&lt;/strong>`</summary>

Because Spine1, Spine2, and Spine3 have different instantaneous queue depths, the three datagrams arrive at destination server `192.168.1.1` out of order. Datagram B arrives at `T1`, Datagram C at `T2`, and Datagram A at `T3`. Selective Packet Spraying uses ingress switch TCAM ACLs to match UDP port 4791 and RoCEv2 BTH RDMA Write opcodes (`0x06..0x0B`). It sprays only RDMA Write elephant flows that NVIDIA ConnectX-6, ConnectX-7, and BlueField DPUs can reorder in hardware while keeping Read and Send flows on per-flow ECMP.
</details>

<details><summary>`&lt;strong>`9. Compare `SLB`, `DLB`, `GLB`, and `TELB` across the seven rows of `ADC` Table 6-1.`&lt;/strong>`</summary>

All four mechanisms can include RoCEv2 BTH header fields. SLB, DLB, and GLB load-balance based on packet characteristics, whereas TELB uses explicit path and color rules. DLB, GLB, and TELB include local link bandwidth, while only DLB and GLB use queue size information. Only GLB and TELB use remote link quality, and only TELB uses external fabric telemetry. Industry adoption is High for SLB, Medium for DLB, and Low for GLB and TELB.
</details>

<details><summary>`&lt;strong>`10. How does BGP unnumbered (`RFC 5549`) establish an `eBGP` session without IPv4 interface addresses, and what exact capability is carried in the BGP `OPEN` message (`Frame 22`)?`&lt;/strong>`</summary>

Switches derive unique IPv6 Link-Local Addresses (`fe80::e59:9cff:fef1:32` on `spine1` and `fe80::e59:9cff:fe22:5dd7` on `leaf1`). They discover each other via ICMPv6 NS, NA, RS, and RA messages, and open TCP port 179. In Frame 22 (`189 B` OPEN, `AS 65001`, `Hold Time 90 s`, `BGP ID 172.16.7.101`), they negotiate Extended Next Hop Encoding (`Capability Code = 5`, `Length = 6`) with `AFI = 1`, `SAFI = 1`, and `Next Hop AFI = 2`. That capability allows Frame 28 (`358 B` UPDATE, `MP_REACH_NLRI` `Type 14`) to advertise `172.16.7.181/32` over an IPv6 link-local next hop.
</details>

<details><summary>`&lt;strong>`11. What are the 16-bit and 32-bit private BGP ASN ranges, and why must all spines in a Clos stage share the same ASN (`65001`)?`&lt;/strong>`</summary>

The 16-bit private ASN range is `64512` to `65535`, and the 32-bit private ASN range is `4200000000` to `4294967294`. Assigning the same ASN (`65001`) to all spines while giving each leaf a unique ASN (`65101..65104`) activates BGP's default `AS_PATH` loop check between spines. A second spine immediately rejects any route bounced from a first spine down to a transit leaf and back up. This prevents valley tromboning during multi-link failures.
</details>

<details><summary>`&lt;strong>`12. What problems do BGP `ADD-PATH` and `AS-PATH` strip-and-replace solve in an AI data center fabric?`&lt;/strong>`</summary>

Suppose `spine2` (`AS 65001`) or an iBGP Route Reflector receives multiple paths for external prefix `10.10.108.0/24` via `border-leaf1` (`NH1`) and `border-leaf2` (`NH2`) from `DC GW 65503`. ADD-PATH allows `spine2` to advertise both paths rather than only a single best path to `leaf2` (`AS 65102`). Ingress `AS-PATH` strip-and-replace normalizes routes arriving from a private WAN core (`server101`) or host BGP daemons. It replaces variable private ASNs with a uniform-length operator ASN sequence so ECMP treats all border paths equally.
</details>

<details><summary>`&lt;strong>`13. How do BGP Link Bandwidth Extended Community (`WCMP` / `WPS`) and Minimum BGP Peers per Prefix work (`ADC` Fig. 8-8)?`&lt;/strong>`</summary>

When `spine1..spine4` have unequal northbound bandwidths of 400G, 800G, 100G, and 400G, advertising the BGP Link Bandwidth Extended Community programs WCMP weights of 20%, 45%, 15%, and 20% on `leaf1..leaf4`. In a five-stage Clos, Weighted Packet Spraying dynamically lowers a spine's weight when a spine-to-super-spine link fails. Minimum BGP peers per prefix forces a spine to withdraw a prefix (`10.10.101.0/24`) if its active downlink peers drop from 4 to 3, keeping traffic on full-capacity spines.
</details>

<details><summary>`&lt;strong>`14. How does BGP Deterministic Path Forwarding (`BGP DPF`, `draft-wang-idr-dpf`) partition a Clos fabric into colored planes, and what are the four traffic-to-fabric color mapping methods?`&lt;/strong>`</summary>

BGP DPF colors underlay eBGP sessions, such as black on `spine1` and gray on `spine2`. When egress `leaf4` originates an uncolored route (`10.10.1.4/32`), advertising it over a colored session prunes unmatched colors. Ingress `leaf1` then installs a deterministic black active path and a pre-installed gray backup path. Traffic maps to colors via Filter-Based Forwarding on ingress or UDP ports and BTH QPairs, on-box active probe agents, a central controller (`CPCE`), or EVPN-VXLAN `MAC-VRF` and `RT5` IP-VRF correlation.
</details>

<details><summary>`&lt;strong>`15. How does `RIFT` (`RFC 9692`) work, and how does DragonFly Sparse (`draft-przygienda-rift-dragonfly`) simplify canonical DragonFly cabling?`&lt;/strong>`</summary>

RIFT floods link-state topology northbound to spines while advertising only a default route southbound via distance-vector. It features automatic disaggregation on link failure, UDP hello and IPv6 ND peering, wide ECMP/UCMP, and K-store configuration metadata. While a canonical DragonFly requires internal and external meshes across 7 groups of 8 switches, DragonFly Sparse turns each group into a simple Leaf-Spine Clos. It then meshes only the T2 Top-of-Fabric spines and advertises horizontal global links in RIFT K-store attributes.
</details>

<details><summary>`&lt;strong>`16. What two enhancements make `IS-IS` suitable for dense AI backend fabrics (`draft-white-lsr-distoptflood` and `RFC 9350` / `RFC 9502` Flex Algo)?`&lt;/strong>`</summary>

First, Optimal Distributed Flooding (`draft-white-lsr-distoptflood`) elects a single designated spine (`spine2`) to flood new leaf prefix LSPs across dense 32- or 64-spine topologies up to 2,500 switches. Second, IS-IS Flex Algo (`RFC 9350` FAD and `RFC 9502` native IP Flex Algo) uses the IPv4 Algorithm Prefix Reachability TLV. It isolates Storage (`Flex Algo 128`), Inference (`Flex Algo 129`), and Training (`Flex Algo 130`) onto separate spines without SRv6 or MPLS encapsulation.
</details>

<details><summary>`&lt;strong>`17. Walk through the port and tenant math for a `512`-GPU non-oversubscribed rail (`ADC` Fig. 8-21) and its `H100 MIG` + `EVPN-VXLAN` multi-tenant mapping (`Fig. 8-24`).`&lt;/strong>`</summary>

Using 8 leaf switches and 8 spine switches of `64 × 800 Gbps` radix, each leaf dedicates `32 × 800 Gbps` ports to spines (`25.6 Tbps`) and breaks out `32 × 800 Gbps` ports into `64 × 400 Gbps` server ports (`25.6 Tbps`). Across 8 leaves, the rail connects 512 GPUs (`204.8 Tbps` 1:1 rail) split across 4 bare-metal tenants of 128 GPUs each. With NVIDIA H100 MIG (`7` GPU instances), each server link trunks 7 VLANs mapped 1:1 into 7 `MAC-VRF` instances and 7 EVPN Route Type 5 IP-VRFs on every leaf. VXLAN-GBP tags provide intra-subnet microsegmentation.
</details>

<details><summary>`&lt;strong>`18. How is BGP extended directly to the GPU server (`ADC` Figs. 8-25 and 8-26), and what 32-bit ASNs and prefixes are used?`&lt;/strong>`</summary>

By running FRR on the Linux GPU server, `server1..server4` (`AS 4200000001..4200000004`) peer directly via eBGP with `leaf1..leaf4` (`AS 4224967001..4224967004` below spines `AS 4294967100`) or via iBGP with a Route Reflector. Each server advertises an IP anycast service prefix (`192.168.10.10/32`) with next hops `NH1..NH4` and enforces host-level `IP-VRF` and `MAC-VRF` multi-tenancy.
</details>

<details><summary>`&lt;strong>`19. How does Segment Routing over IPv6 (`SRv6`, `RFC 8754` / `RFC 8986`) steer GPU flows, and how much header overhead does `16-bit` compressed `uSID` save?`&lt;/strong>`</summary>

An ingress leaf encapsulates packets with an IPv6 Segment Routing Header (`RFC 8754`) carrying 128-bit SIDs (`Locator : Function : Argument`, `RFC 8986`). For example, it pushes `SID 5` for the transit spine and `SID 1` for the egress leaf. Because 4 uncompressed 128-bit SIDs plus the 8-byte SRH base add 72 bytes, Compressed SRv6 uSID encodes up to 6 16-bit micro-SIDs after a 32-bit locator directly inside the 128-bit IPv6 Destination Address (`fc00:0a10:0005:0001:0000::`). That encoding saves all 72 bytes of SRH overhead.
</details>

<details><summary>`&lt;strong>`20. How does NVIDIA Base Command Manager (`bcm11-admin`) manage Cumulus Linux switches via `NVUE` and `NetQ`?`&lt;/strong>`</summary>

In BCM 11 (`cmsh`), each Cumulus Linux switch (`SN5600` or `SN2201` OOB switch with `8,048,771,072` B RAM, `115,923,419,136` B NVMe, and uplinks `15 16`) is configured over the NVUE REST API on TCP port 8765. Operators set `nvconfigurationmode` to `auto`, `manual`, or `file`, which renders `/etc/nvue.d/startup.yaml` and `cm-startup.yaml`. Fleet-wide telemetry and BGP or QoS validation stream to NetQ over HTTPS port 443.
</details>

---

## Sources and review notes

The primary book sources and technical references used in this chapter are cataloged in the block below.

```text
1. Primary book sources read in full from the local corpus:
   - AI Data Center Network Design and Technologies (ai-data-center-network-design-and-technologies):
     * Chapter 6 (Efficient Load Balancing): Read in full and incorporated (DONE in planning/gem_books/DEFERRED.md). Covers LLM (NLU/NLG) low-entropy RoCEv2 east-west flows (UDP 4791, IB BTH), ECMP hardware group ASIC ECMP nh-id123 (Unicast_nh1..3 across 32 or 64 spines and EVPN-VXLAN MAC-VRF / RT5 loopback next hops, Figure 6-1), Static Load Balancing (SLB) with Flow1..Flow4 (50, 100, 50, 100 Gbps on 200 Gbps links yielding 50% and 100% utilization, Figure 6-2, Figure 6-3), worked CRC32 5-tuple calculation (192.168.1.20 C0A80114, 192.168.2.10 C0A8020A, Proto 17 11, UDP 1024 0400, UDP 4791 12B7 -> C0A80114 C0A8020A 11040012 B7 -> 0x8BDA7C2D = 2,346,351,661, mod 5 = 1, mod 8 = 5, plus 10 mod 5 = 0 and 11 mod 5 = 1), resilient hashing (512 or 1,024 buckets, 8-bucket example mapping hash_key = 10 -> bucket 2 -> interface_2 where only buckets 2 and 7 remap on failure = 25% vs 75% modulo churn), symmetric XOR hashing, weighted ECMP (WCMP), Dynamic Load Balancing (DLB) quality bands (0..7), 75% (150 Gbps) balanced spine utilization (Figure 6-4), DLB assigned-flow mode, flowlet mode with inactivity timer and flowset tables (Figure 6-5), reactive path rebalancing (Figure 6-6), Global Load Balancing (GLB) on Broadcom Tomahawk 5 avoiding remote spine congestion on Link X (SpineA -> LeafD, Figure 6-7, Figure 6-8), BGP NNHN (draft-wang-idr-next-next-hop-nodes, Characteristic Code = 2, 32-bit Next-hop and Next-next-hop BGP IDs, simple vs compound path quality profiles, 20 ms change-based PFE heartbeats, Figure 6-9), Traffic Engineering-Based Load Balancing (TELB across ROD, RUD with 3 x 400G links, FBF/PBR per QPAIR, and OOB TELB controller, Figures 6-10..6-13), Per-Packet Load Balancing (3 x 1,500 B datagrams A, B, C over 3 x 100 Gbps ports arriving out of order B at T1, C at T2, A at T3 at 192.168.1.1, Figures 6-14, 6-15), Random Spray, DLB Per-Packet Mode, Selective Packet Spraying (sDLB matching UDP 4791 BTH RDMA Write opcodes 0x06..0x0B in TCAM ACLs for ConnectX-6/7 and BlueField DPUs, Figure 6-16), and Table 6-1.
     * Chapter 8 (IP Routing for AI/ML Fabrics): Read in full and incorporated (DONE in planning/gem_books/DEFERRED.md). Covers OSPFv2/v3 vs IS-IS vs eBGP (RFC 7938), backend vs frontend routing domains, eBGP unnumbered (RFC 5549 / RFC 8950) with 16-bit (64512..65535) and 32-bit (4200000000..4294967294) private ASNs, ICMPv6 NS/NA/RS/RA and TCP 52659 -> 179 handshake between spine1 (0c:59:9c:f1:00:32, fe80::e59:9cff:fef1:32) and leaf1 (0c:59:9c:22:5d:d7, fe80::e59:9cff:fe22:5dd7, Figure 8-1), packet capture Frame 22 (189 B / 1,512 bits BGP OPEN, Length 81, AS 65001, Hold Time 90 s, BGP ID 172.16.7.101, Opt Params 52 B, Extended Next Hop Encoding Capability Code 5 Length 6 with AFI=1, SAFI=1, NH_AFI=2, Figure 8-2) and Frame 28 (358 B / 2,864 bits BGP UPDATE, Length 82, Path Attr 46, MP_REACH_NLRI Type 14 Length 42, prefix 172.16.7.181/32, Figure 8-3), shared spine ASN (65001 with leaves 65101..65104, Figure 8-4) vs distinct spine ASNs (65001..65004 valley tromboning server1 10.10.1.1/24 -> leaf1 -> spine1 -> leaf2 -> spine1/2 -> leaf3 -> server5 10.10.5.1/24, Figure 8-5), BGP ADD-PATH (DC GW 65503, border-leaf1 65501, border-leaf2 65502, spine2 65001, leaf2 65102, 10.10.108.0/24 & 10.10.101.0/24, Figure 8-6), ingress AS-PATH strip-and-replace (server101, Figure 8-7), BGP Link Bandwidth Extended Community & WCMP / WPS (spine1..4 400G/800G/100G/400G -> 20%/45%/15%/20%, Figure 8-8), minimum BGP peers per prefix (10.10.101.0/24 withdrawn when peers drop from 4 to 3), BGP DPF (draft-wang-idr-dpf, ROD vs RUD where 1 leaf failure impacts 4 H100 servers in RUD, 128 x GPU-id 0 on 3 x 400G = 1.2 Tbps, 10.10.1.4/32 active black / backup gray pruning, and 4 color mapping modes including CPCE and EVPN-VXLAN, Figures 8-9..8-14), RIFT (RFC 9692, >= 1,000 switches, canonical 7 x 8 DragonFly vs DragonFly Sparse ToF K-store in draft-przygienda-rift-dragonfly, Figures 8-15..8-18), IS-IS Optimal Distributed Flooding (draft-white-lsr-distoptflood, 2,500 switches, 32/64 spines, Figure 8-19) & Flex Algo (RFC 9350 FAD, RFC 9502 IP Flex Algo planes 128/129/130, Figure 8-20, Table 8-1), Multi-tenancy (8 x 8 rail of 64 x 800G switches = 512 GPUs/rail, 204.8 Tbps, 4 x 128 GPUs BMS, 8 subnets/tenant, 7-instance H100 MIG VLAN 1..7 / MAC-VRF 1..7 / RT5 IPVRF 1..7, VXLAN-GBP, Figures 8-21..8-24), Host FRR BGP (spine 4294967100, leaf 4224967001..4, server 4200000001..4, anycast 192.168.10.10/32, Figures 8-25, 8-26), and SRv6 (RFC 8754 SRH, RFC 8986, SID 5 -> SID 1, 16-bit uSID packing 6 micro-SIDs after fc00:0a10::/32 saving 72 B, Figures 8-27..8-30).
   - NVIDIA Base Command Manager 11 Administrator Manual (bcm11-admin, Chapter 3 §3.8-3.12): Read and cited for Cumulus Linux switch management via NVUE (nv CLI and REST port 8765), nvconfigurationmode (auto/manual/file with startup.yaml and cm-startup.yaml), SN2201 (8,048,771,072 B RAM, 115,923,419,136 B NVMe, uplinks 15 16), and NetQ (port 443).
```

The companion reference module (`code/part12/load_balancing_routing_ai.py`) and its 25-check lab (`code/part12/load_balancing_routing_ai_lab.py`) were executed and verified locally (`Summary: 25 passed, 0 failed`). Switch CLI and NOS configuration snippets (`nv set`, `cmsh`, `vtysh`, `tcpdump`, `ALB`, `ZTP`, `ToF-to-ToF`, `spine6` ASNs `65002` and `65003`, `LLAs` in `fe80::/10`, `NEXT_HOP`, `MPLS-TE`, `Locator:Function:Argument`, `GPUaaS`, Junos Evo and Broadcom stanzas, and `nvidia-smi mig`) are derived from the cited references. They are marked `(untested here)` where not executed on live switch hardware in this build environment.

