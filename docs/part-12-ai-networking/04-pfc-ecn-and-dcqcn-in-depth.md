---
id: "c12-04"
title: "12.4 PFC, ECN and DCQCN in depth"
sidebar_label: "12.4 PFC, ECN and DCQCN in depth"
sidebar_position: 4
description: "IEEE 802.1Qbb Priority Flow Control, RFC 3168 ECN marking, DCQCN closed-loop rate control, buffer headroom math, PFC Watchdog, SFC, and CSIG."
status: "drafted"
tier: "1"
level: "A"
lab_venue: "Nebius GPU"
---

# 12.4 PFC, ECN and DCQCN in depth

| | |
|---|---|
| Level | Advanced |
| Priority tier | 1 |
| Lab venue | Nebius GPU |
| Part | Part 12: Complete AI networking |
| Sources | `ai-data-center-network-design-and-technologies` Ch. 7; `nvidia-devops` V9 Ch. 4–5 & Labs 01–04 |
| Code | `code/part12/pfc_ecn_dcqcn.py`, `code/part12/pfc_ecn_dcqcn_lab.py` |
| Coverage file | `planning/coverage/chapters/12-04.md` |

## Why this matters for AI infrastructure

Picture an AI cluster that looks healthy on every dashboard. Every optical link is up, and every packet-drop counter reads zero. Yet a training run slows to a crawl during an AllReduce or all-to-all collective. You need to understand this failure before you change any switch setting.

The stall often starts in one place. One receiver-facing leaf egress port fills its queue and keeps sending Priority Flow Control pause frames. Within microseconds, the upstream switch ingress buffers fill too, and they pass pause frames further upstream, one hop at a time. That chain freezes unrelated GPU workers that happen to share the same traffic class.

The opposite failure is just as damaging. If PFC is absent when microbursts converge on one egress port, RoCEv2 packets drop. Those drops trigger hardware Go-Back-N retransmission storms across 400 Gbps or 800 Gbps rails.

Preventing both failures means coordinating two mechanisms on every network adapter and switch hop. The first is the closed loop formed by Explicit Congestion Notification and Data Center Quantized Congestion Notification. It works early and end to end. A congested switch marks the IP ECN field to Congestion Experienced. The destination adapter returns a RoCEv2 Congestion Notification Packet, and the sender's hardware Reaction Point throttles that specific Queue Pair before the buffers fill.

The second mechanism is Priority Flow Control, a link-local, hop-by-hop Layer 2 circuit breaker. It pauses one priority class at a time. It also reserves enough headroom buffer to absorb the bytes already in flight along the cable and transceiver pipeline.

```text
Coordinated RoCEv2 Congestion Control Architecture:
  1. ECN + DCQCN (RFC 3168 / RoCEv2):
     - Switch marks 2-bit IP ECN field to 11 (Congestion Experienced, CE)
     - Destination NIC returns CNP (InfiniBand BTH opcode 129 / 0x81, UDP port 4791)
     - Sender NIC Reaction Point (RP) throttles only the offending Queue Pair (QP)
  2. Priority Flow Control (PFC, IEEE 802.1Qbb):
     - Link-local Layer 2 MAC Control frame (EtherType 0x8808, opcode 0x0101, dst MAC 01:80:C2:00:00:01)
     - Pauses a single 802.1p priority class (0..7) for 0..65,535 quanta (512 bit-times per quantum)
     - Reserves flight-time headroom buffer for cable + transceiver + ASIC pipeline delay
```

This chapter builds on the QoS concepts from Chapter 2.19 and the RoCEv2 transport architecture from Chapter 12.3. If you already know the ECN and PFC basics, you can go straight to the math. The chapter derives the PFC frame format, the pause timing, and the buffer headroom a cable needs. It then follows the ECN marking curve and the DCQCN rate-cut and recovery steps, and ends with the PFC Watchdog, the newer signaling standards, and a production diagnostic workflow.

Keep both mechanisms in mind as you read, since the rest of the chapter treats them as one design.

## Prerequisites and outcomes

**Prerequisites:** Before you start, review the queuing, QoS, ECN, PFC and DCB basics in Chapter 2.19. Then review the RDMA fundamentals in Chapter 12.2 and the RoCEv2 transport in Chapter 12.3.

**Outcomes:** When you finish this chapter, you will be able to:
- Identify all six Clos fabric congestion points. You will also explain why RoCEv2 over UDP port 4791 needs coordinated congestion management.
- Decode every field of an IEEE 802.1Qbb PFC pause and un-pause frame. Then compute the exact pause durations on links from 100 Gbps to 800 Gbps.
- Size per-priority lossless buffers from cable length, the speed of light in glass, transceiver delay and MTU. You will also audit the output of `mlnx_qos`.
- Trace the ECN and DCQCN closed loop across the IP ToS byte, WRED probability zones and CNP generation. You will also trace the three-stage Reaction Point recovery state machine.
- Configure the three-stage PFC Watchdog, and compare hop-by-hop PFC with Source Flow Control and Congestion Signaling. You will also isolate production pause trees using `ethtool -S` and `mlx5_cnp_stats`.

---

## 1. The six Clos congestion points and why RoCEv2 needs two loops

Suppose several GPU servers transmit at line rate, anywhere from 100 Gbps to 800 Gbps, at the same moment. Short microbursts and Equal-Cost Multi-Path hash collisions then overload switch egress queues. Engineers feel this first as a spike in collective latency, even on a Clos topology that is not oversubscribed.

RoCEv2 wraps InfiniBand transport headers inside connectionless UDP packets on destination port 4791. Standard Ethernet provides no built-in windowing or retransmission. So congestion can build at six distinct points across both two-tier and three-tier fabrics.

```mermaid
flowchart TB
    subgraph SuperSpine["Super-Spine Tier"]
        SSA["SuperSpineA"]
        SSB["SuperSpineB"]
    end
    subgraph Spine["Spine Tier"]
        SA["SpineA"]
        SC["SpineC"]
    end
    subgraph Leaf["Leaf Tier"]
        LA["LeafA"]
        LB["LeafB"]
        LD["LeafD"]
    end
    S1["GPU Server 1"] -->|"100-800G"| LA
    S2["GPU Server 2"] -->|"100-800G"| LA
    LA -->|"CP1: Local Leaf Link"| ST["Local Storage / Peer"]
    LA -->|"CP2: Leaf-to-Spine"| SA
    LB -->|"Line Rate"| SA
    SA -->|"CP3: Spine-to-Leaf"| LD
    LD -->|"CP4: Leaf-to-Server"| S4["Receiver GPU Server"]
    SA -->|"CP5: Spine-to-SuperSpine"| SSA
    SSA -->|"CP6: SuperSpine-to-Spine"| SC
```

The table below lists each congestion point, the path that leads to it, and what the queue shows once it fills.

| Congestion point | Topology path | How congestion arises | Immediate symptom on queue |
|---|---|---|---|
| **1. Local leaf link congestion (CP1)** | Two servers on LeafA -> south-facing storage/compute link on LeafA | Local switching bypasses spine load balancing; two line-rate flows converge on 1 south-facing port | South-facing egress queue on LeafA fills rapidly in an N:1 local incast |
| **2. Leaf-to-spine link congestion (CP2)** | Two servers on LeafA -> same uplink from LeafA to SpineA | ECMP hash collision places multiple high-entropy elephant flows onto the same LeafA -> SpineA uplink | Northbound uplink queue on LeafA builds occupancy while parallel uplinks to SpineB sit idle |
| **3. Spine-to-leaf link congestion (CP3)** | Server on LeafA + Server on LeafB -> SpineA -> single downlink to LeafD | Flows arrive on separate spine ingress ports without contention, then collide on the single SpineA -> LeafD downlink | Southbound transit spine queue on SpineA -> LeafD crosses ECN and PFC thresholds |
| **4. Leaf-to-server link congestion (CP4)** | Server on LeafA via SpineA + Server on LeafB via SpineB -> LeafD -> receiver server | Perfect spine load balancing delivers 2x line rate cleanly to LeafD, exceeding the single receiver NIC link capacity | Final egress leaf queue on LeafD -> Server saturates in a classic destination incast |
| **5. Spine-to-super-spine link congestion (CP5)** | Servers on LeafA and LeafB -> SpineA -> single uplink to SuperSpineA | Multi-pod traffic in a 3-tier fabric hashes onto the same SpineA -> SuperSpineA link while SuperSpineB is underutilized | Northbound spine-to-super-spine queue builds backpressure toward the lower pod |
| **6. Super-spine-to-spine link congestion (CP6)** | Servers across LeafA, LeafB, LeafE -> SpineA/SpineB -> SuperSpineA -> SpineC | Traffic spreads cleanly upward to SuperSpineA, then converges onto a single SuperSpineA -> SpineC downlink | Core-to-pod downlink queue on SuperSpineA becomes the fabric bottleneck |

Notice that most of these points come down to many flows converging on one port. If you see a queue fill that way, look at how many flows converge on it.

### Why neither ECN alone nor PFC alone suffices

A common architecture question is why AI Ethernet fabrics run both ECN and PFC rather than picking one. If you rely on ECN alone, the fabric stays open to packet drops during fast microbursts. If you rely on PFC alone, you get head-of-line blocking and fabric-wide pause trees that freeze unrelated GPU jobs.

ECN is an end-to-end control loop, and that loop takes time. When SpineA marks a packet on its congested link to LeafD, the packet must first finish the forward path through LeafD to the destination server. The destination adapter then generates a CNP, and that CNP must travel the reverse path back to the sender before transmission slows down. During that round trip, a sudden incast burst can fill the rest of the switch buffer and drop packets. A queue with only ECN enabled can still drop packets during fast transients, so it counts as a lossy queue.

PFC acts at once, but only across one link at a time. You can think of it as a local brake. It pauses transmission hop by hop before a queue overflows, which keeps the queue lossless. However, PFC has no concept of an individual flow or Queue Pair. It stops all traffic mapped to the congested priority class on that link. If one congested flow triggers PFC on Priority 3, every unrelated flow sharing Priority 3 on that link is blocked through head-of-line blocking. Sustained pauses then spread backward into a fabric-wide PFC pause tree.

DCQCN resolves this tension by combining both mechanisms over DSCP. ECN acts first, at a lower buffer threshold, to throttle only the offending sender Queue Pairs end to end. PFC sits higher in the buffer as a last-resort safety net. It absorbs microbursts before any packet drop occurs.

Keep both mechanisms enabled on the lossless priority, and treat PFC as the backstop rather than the first response.

---

## 2. Priority Flow Control frame format, quanta math, and buffer headroom

### 2.1 From Global Pause to Per-Priority Pause

Consider what happens when a receiver buffer fills on a legacy Ethernet link. Stopping the entire physical wire also stops SSH management, BGP keepalives, storage traffic and RDMA collectives. Cluster operators lose control-plane visibility at exactly the moment congestion hits.

Original Ethernet flow control, IEEE 802.3x Global Pause, works like one red traffic light across the whole physical link. IEEE 802.1Qbb Priority Flow Control replaces that link-wide pause with eight independent virtual lanes. These lanes match the 3-bit IEEE 802.1p Priority Code Point, or the DSCP classes mapped to them. When Queue 3 crosses its XOFF threshold on a receiving switch port, the receiver sends a Layer 2 MAC Control frame upstream. That frame tells its link partner to pause only Priority 3. The other seven priorities keep transmitting at full line rate.

### 2.2 Wire-level anatomy of an 802.1Qbb PFC XOFF and XON frame

Suppose a switch port emits malformed pause frames or enables the wrong class bitmask. The upstream peer then misbehaves. It either ignores the pause and drops RoCEv2 packets, or it halts the wrong priority queue. If you capture packets to debug this, you need to read the exact byte layout on the wire.

A PFC frame is a 64-byte Layer 2 Ethernet MAC Control frame. It goes directly to the link-local peer. Switches never forward PFC frames across Layer 2 bridges or Layer 3 routers.

The table below breaks the frame into its fields, so you can match each byte in a capture to its meaning.

| Field | Size | Wire value (Hex / Binary) | Operational meaning |
|---|---|---|---|
| **Destination MAC** | 6 octets | `01:80:C2:00:00:01` | IEEE 802.1 reserved non-forwardable link-local MAC control multicast address |
| **Source MAC** | 6 octets | e.g., `10:0e:7e:b7:a7:1b` | MAC address of the congested port generating the pause frame |
| **EtherType** | 2 octets | `0x8808` | Identifies an Ethernet MAC Control frame |
| **Control Opcode** | 2 octets | `0x0101` | Identifies Class-Based Flow Control (CBFC / PFC, IEEE 802.1Qbb) |
| **Priority Control Vector (Class Enable Vector)** | 2 octets | `0x0008` (C3 = True, C0..C2, C4..C7 = False) | 16-bit field (8 upper reserved bits = 0, 8 lower bits = e[7]..e[0]); `1 << 3 = 0x0008` enables Class 3 |
| **Time (`time[0]..time[7]`)** | 16 octets (8 x 2 octets) | C3 = 65535 (`0xFFFF`) for XOFF; C3 = 0 (`0x0000`) for XON | Pause duration in 512-bit quanta (0..65,535) for each of the 8 classes (C0..C7) |
| **Padding + FCS (CRC-32)** | 26 + 4 octets | Zero-padded to 60 B + 4 B CRC | Brings total wire frame length to 64 bytes |

A congested port sends a pause in two steps. First comes the XOFF pause. It fires when the Priority 3 ingress buffer crosses the XOFF threshold, and it tells the upstream neighbor to stop Priority 3 and nothing else. In the frame, the Class Enable Vector is `0x0008` and the Class 3 pause time is 65,535 quanta. The other seven class timers stay at zero. While congestion lasts, every packet that crosses XOFF sends a fresh XOFF frame and resets the upstream pause timer.

Then comes the XON un-pause. It fires once the queue drains below the XON threshold, before the pause timer expires. The receiver sends an identical frame with the Class 3 pause time set to 0, and the upstream neighbor resumes Priority 3 at once.

### 2.3 Exact PFC pause duration math across 100G, 200G, 400G, and 800G

As you move AI fabrics from 100 Gbps to 400 Gbps and 800 Gbps rails, single-frame pause times shrink in proportion. If you assume a fixed microsecond pause window, you will misread pause storm telemetry on the faster links.

In IEEE 802.1Qbb, each pause quantum equals 512 bit-times at the negotiated link speed. Because 1 Gbps equals 1 bit per nanosecond, the pause duration for a 16-bit quanta value $Q$ depends on the link rate $R_{\text{Gbps}}$.

```text
IEEE 802.1Qbb Quanta Pause Duration Equations:
  Total Bit-Times      = Q * 512
  Pause Duration (ns)  = (Q * 512) / R_Gbps
  Pause Duration (us)  = (Q * 512) / (R_Gbps * 1000)
```

The table divides the maximum pause of 65,535 quanta by the link speed of each generation.

| Link speed ($R_{\text{Gbps}}$) | Quanta ($Q$) | Total bit-times ($Q \times 512$) | Pause duration (ns) | Pause duration (µs) | Operational note |
|---|---|---|---|---|---|
| **100 Gbps** | 65,535 | 33,553,920 | 335,539.2 ns | **335.5392 µs** | Legacy 100G RoCEv2 leaf-server link |
| **200 Gbps** | 65,535 | 33,553,920 | 167,769.6 ns | **167.7696 µs** | ConnectX-6 / HDR-era Ethernet rail |
| **400 Gbps** | 65,535 | 33,553,920 | 83,884.8 ns | **83.8848 µs** | ConnectX-7 / Spectrum-4 400G rail |
| **800 Gbps** | 65,535 | 33,553,920 | 41,942.4 ns | **41.9424 µs** | ConnectX-8 / Spectrum-X 800G rail |
| **Any rate (XON)** | 0 | 0 | 0.0 ns | **0.0 µs** | Explicit XON un-pause frame resumes TX immediately |

A quantum is measured in bit-times, not in wall-clock microseconds. So doubling the link speed cuts the maximum pause of a single XOFF frame in half. Moving from 400 Gbps to 800 Gbps cuts the longest pause in half. The maximum single-frame pause falls from 83.8848 microseconds to 41.9424 microseconds.

### 2.4 Cable flight-time headroom math and `mlnx_qos` buffer thresholds

When a receiving switch port crosses XOFF and sends a pause frame, bytes already on the wire keep arriving. They keep arriving until the pause reaches the upstream sender and the sender's MAC stops transmitting. If the priority buffer above XOFF cannot absorb those in-flight bytes, the lossless queue suffers tail-drop packet loss.

To prevent drops in this reaction window, the headroom above XOFF must absorb three things. First, it must absorb the round-trip cable propagation delay. Light in glass travels at 5 nanoseconds per meter one way, or 10 nanoseconds per meter round trip. Second, it must absorb the transceiver, PHY and ASIC reaction pipeline delay, which is typically 600 nanoseconds. Third, it must absorb the in-flight serialization of up to two jumbo MTU packets, plus the 64-byte PFC control frame. One jumbo frame may have just started serializing at the sender when XOFF arrived. Another may be finishing at the receiver when XOFF triggered.

```text
Minimum Lossless Flight-Time Headroom Formula:
  Headroom_min (bytes) = ((2 * L_m * 5 ns/m + t_pipeline_ns) * R_Gbps) / 8 + (2 * MTU) + 64
```

Compare a short in-rack copper cable with a long campus optical fiber at 400 Gbps. The table shows why long links need a much larger headroom buffer.

| Link scenario (400 Gbps, MTU = 9,000 B) | Cable RTT (2 * L * 5 ns/m) | Total reaction time (RTT + 600 ns) | In-flight wire bytes (t * 400 / 8) | Serialization bytes (2 * 9,000 + 64) | Required flight headroom (B) |
|---|---|---|---|---|---|
| **Short in-rack DAC (L = 2 m)** | 20 ns | 620 ns | 31,000 B | 18,064 B | **49,064 B** |
| **Long optical fiber (L = 500 m)** | 5,000 ns | 5,600 ns | 280,000 B | 18,064 B | **298,064 B** (+249,000 B delta) |

On a switch or host interface, `mlnx_qos -i swp12` shows the deployed buffer partitioning, XOFF, XON, headroom and hysteresis.

```text
# (untested here)
$ mlnx_qos -i swp12
Priority trust state: pcp
Receive buffer size (bytes): 262144, 262144, 262144, ...
PFC configuration:
        priority    0   1   2   3   4   5   6   7
        enabled     0   0   0   1   0   0   0   0
        buffer      0   0   0   1   0   0   0   0

Buffer size assigned to priority 3: 65536 bytes
Xoff threshold: 49152 bytes   (75% of buffer)
Xon threshold:  32768 bytes   (50% of buffer)
```

```text
mlnx_qos -i swp12 Lossless Buffer Invariants:
  - Narrow Lossless Scope:  enabled = 0 0 0 1 0 0 0 0 -> Only Priority 3 (buffer 1) is lossless; Priorities 0..2 and 4..7 remain lossy
  - Port & Priority Pool:   262,144 B port receive buffer; 65,536 B assigned to Priority 3
  - Flight Headroom:        65,536 - 49,152 = 16,384 bytes (25.0% above XOFF at 75.0%) absorbs in-flight bytes after XOFF fires
  - Drain Hysteresis:       49,152 - 32,768 = 16,384 bytes (25.0% gap between 75.0% XOFF and 50.0% XON) prevents rapid XOFF/XON oscillation
```

Each number in that output enforces a hardware rule. Only Priority 3 is lossless, so management on Priority 0 and storage never enter a pause domain. Setting XOFF at 75 percent leaves 16,384 bytes of headroom above it. Setting XOFF equal to the full buffer leaves zero headroom, so tail-drop loss happens before the upstream sender can halt. The queue must also drain down to 50 percent before XON lifts the pause. If XON equaled XOFF with zero hysteresis, one draining packet would trigger XON, and the next arriving packet would trigger XOFF again. That loop shows up as micro-oscillations and spikes in `tx_pfc_prio3`. Setting XON to zero bytes does the opposite. It starves the link, because resumption waits until the queue is completely empty.

When you read that output, check the headroom and hysteresis figures before you trust the buffer profile.

---

## 3. Explicit Congestion Notification and DCQCN closed-loop rate control

### 3.1 IP header DSCP + ECN bits and CNP packet format

If a congested switch drops packets to signal congestion, RoCEv2 performance collapses under Go-Back-N retransmissions. If the switch uses PFC alone, unrelated flows freeze behind class-wide pauses. So the fabric needs a way to mark individual congested flows in flight. It also has to carry that signal back to the exact sending Queue Pair without being delayed by the congestion itself.

In the IPv4 Type of Service byte, or the IPv6 Traffic Class byte, the upper 6 bits hold the Differentiated Services Code Point. QoS uses that code point to classify traffic into queues. The lower 2 bits hold the ECN field, which RFC 3168 defines. The two ECN bits form four codepoints, and the table shows how each one is treated under congestion.

| ECT bit (Bit 6) | CE bit (Bit 7) | 2-bit ECN codepoint | Standard name | Switch & endpoint behavior under congestion |
|---|---|---|---|---|
| `0` | `0` | **`00`** | Not-ECT (Not ECN-Capable Transport) | Transport does not support ECN; congested switches **drop** the packet instead of marking it |
| `0` | `1` | **`01`** | ECT(1) (ECN-Capable Transport 1) | Marks packet as ECN-capable; set by sender on RoCEv2 data packets and by receiver on returning CNP frames (`01` and `10` are treated identically by transit switches) |
| `1` | `0` | **`10`** | ECT(0) (ECN-Capable Transport 0) | Marks packet as ECN-capable; congested switches rewrite `10` (or `01`) to `11` (CE) instead of dropping |
| `1` | `1` | **`11`** | CE (Congestion Experienced) | Set by a congested transit switch when queue occupancy crosses its WRED ECN threshold; triggers the receiver NIC to generate a CNP |

Notice that `00` is the only codepoint that gets dropped. The ECN-capable codepoints are marked instead.

When an ECN-marked RoCEv2 packet reaches the destination, the receiving adapter's Notification Point hardware generates a Congestion Notification Packet back toward the source IP. The CNP is a RoCEv2 frame on UDP port 4791, and it carries InfiniBand Base Transport Header opcode 129. It names the congested destination Queue Pair, so the sender throttles that one Queue Pair rather than the entire priority class. When you read a capture, the CNP tells you which Queue Pair to slow. If you look at the sender's counters, you can confirm that it slowed. The receiver maps the CNP to a high-priority control class, such as DSCP 48 on strict-priority Queue 6. Carrying CNPs on Priority 6 means backward notifications are never delayed by, or paused behind, Priority 3 data congestion.

The wire profiles below compare a data packet with a CNP.

```text
RoCEv2 Data vs Congestion Notification Packet (CNP) Wire Profile:
  - RoCEv2 Data Packet:  UDP dst port 4791 | DSCP 26 (AF31, Queue 3) or DSCP 46 (EF, tcpdump tos 0xb8 where 0xb8 >> 2 = 46) | ECN 01/10 -> 11 (CE)
  - RoCEv2 CNP Frame:    UDP dst port 4791 | IB BTH opcode 129 (0x81, binary 10000001) | Carries congested QP ID | ECN 01 (ECT(1)) | DSCP 48 (CS6, Queue 6)
```

The CNP travels on Queue 6, which is why it stays clear of the congested Queue 3 data.

### 3.2 WRED `K_min` / `K_max` probabilistic marking curve and `XON < K_min < K_max < XOFF`

Consider a switch that waits for one static buffer cutoff before it marks ECN. Every active sender then receives the congestion signal at the same moment, and every sender cuts its rate in lockstep. That synchronized sawtooth oscillation leaves the link underutilized. Furthermore, if the ECN thresholds sit above the PFC XOFF threshold, PFC fires first, and ECN never prevents pause storms.

Production AI switches apply Weighted Random Early Detection, or WRED, to mark ECN bits with a probability. The marking probability rises linearly as queue occupancy $q$ climbs between a minimum threshold $K_{\min}$ and a maximum threshold $K_{\max}$. The maximum marking probability is $P_{\max}$.

```text
WRED Probabilistic ECN Marking Function P_mark(q):
  - Green Zone (q < K_min):          P_mark(q) = 0.0 (Free Flow)
  - Yellow Zone (K_min <= q < K_max): P_mark(q) = P_max * (q - K_min) / (K_max - K_min) (Linear WRED Ramp)
  - Red Zone (q >= K_max):           P_mark(q) = 1.0 (100% ECN Marking)
```

Take a standard high-speed switch profile with $K_{\min}$ at 150 KB and $K_{\max}$ at 1,500 KB. The table shows the marking probability at five queue levels.

| Queue occupancy ($q$) | Queue zone | WRED calculation | Marking probability ($P_{\text{mark}}$) | Switch action |
|---|---|---|---|---|
| **100 KB** (`< 150 KB`) | **Green Zone** | $q < K_{\min}$ | **0.0 (0%)** | Forward packets unmarked at full line rate |
| **487.5 KB** (25% of span) | **Yellow Zone** | $(487.5 - 150) / (1500 - 150) = 337.5 / 1350$ | **0.25 (25%)** | Mark 1 in 4 packets with ECN = 11 (CE) |
| **825 KB** (midpoint) | **Yellow Zone** | $(825 - 150) / (1500 - 150) = 675 / 1350$ | **0.50 (50%)** | Mark 1 in 2 packets with ECN = 11 (CE) |
| **1,600 KB** (`>= 1,500 KB`) | **Red Zone** | $q \ge K_{\max}$ | **1.0 (100%)** | Mark 100% of packets with CE (`< XOFF`, no PFC yet) |
| **`>= 2,000 KB`** (`>= XOFF`) | **PFC Safety Net** | $q \ge \text{XOFF}$ | **1.0 + PFC XOFF** | Emit 802.1Qbb pause frame to upstream hop |

Read the table as a gradual ramp rather than a switch. Marking stays at zero below 150 KB, then rises in a straight line until it reaches 1.0 at 1,500 KB. At 487.5 KB, the queue sits 337.5 KB above $K_{\min}$. That is a quarter of the 1,350 KB span, so one packet in four gets marked.

For DCQCN to prevent PFC storms, the thresholds on every lossless queue must strictly satisfy the ordering rule below.

```text
DCQCN Threshold Ordering Invariant (ADC Ch 7 Fig 7-16):
  - Ordering Rule:    0 < XON < K_min < K_max < XOFF < BufferMax
  - Valid Profile:    XON (32,768 B) < K_min (150,000 B) < K_max (1,500,000 B) < XOFF (2,000,000 B) < BufferMax (2,500,000 B)
  - Broken Profile:   Setting K_max = 55,000 B above XOFF = 49,152 B violates K_max < XOFF, firing PFC pauses before ECN reaches 100%
```

If $K_{\max}$ is set at or above XOFF, the switch fires hop-by-hop PFC pauses before ECN marking reaches 100 percent. That misconfiguration makes PFC the primary congestion mechanism, and it starves unrelated flows.

### 3.3 The DCQCN three-actor state machine (CP, NP, RP)

Suppose a switch has marked ECN and a receiver has sent a CNP. The sending adapter then has to decide how hard to cut its injection rate. It also has to decide how quickly to recover once congestion clears. Cut too weakly, and PFC pauses keep firing. Cut and recover too aggressively, and throughput swings wildly.

DCQCN coordinates three hardware state machines across the fabric. The Congestion Point on a transit switch egress queue monitors queue depth against $K_min$ and $K_max$, and it rewrites the ECN bits to CE. The Notification Point on the receiver adapter inspects arriving RoCEv2 packets. When CE is present, it sends at most one CNP per coalesce timer window, typically 50 microseconds, back to the sender. The Reaction Point on the sender adapter keeps three state variables per active Queue Pair. They are the current transmission rate $R_c$, the target rate $R_t$ saved before a cut, and the congestion estimate $\alpha$, which is updated by an exponential weighted moving average with weight $g$.

Because $\alpha$ never exceeds 1.0, a single rate cut reduces $R_c$ by at most 50 percent. When no CNP arrives, the sender decays $\alpha$ toward zero as each rate-increase timer or byte counter expires. Recovery then runs in three stages, governed by the Fast Recovery threshold $F$: Fast Recovery, Additive Increase and Hyper-Additive Increase.

```text
DCQCN Reaction Point (RP) Equations & Numerical Walkthrough (g = 1/16 = 0.0625, F = 5, R_AI = 10.0 Gbps, R_HAI = 40.0 Gbps):
  - Multiplicative Rate Cut on CNP Arrival:
    * Equations: R_t <- R_c | R_c <- R_c * (1 - alpha / 2) | alpha <- (1 - g) * alpha + g * 1.0
    * At alpha = 1.0 on 400.0 Gbps link: R_t = 400.0 Gbps, R_c = 400.0 * (1 - 1.0/2) = 200.0 Gbps (maximum 50% single cut)
    * At alpha = 0.5 on 400.0 Gbps link: R_t = 400.0 Gbps, R_c = 400.0 * (1 - 0.5/2) = 300.0 Gbps, alpha -> (1 - 0.0625)*0.5 + 0.0625 = 0.53125
  - Three-Stage Rate Recovery When No CNP Arrives (alpha <- (1 - g) * alpha; starting from R_c = 200.0 Gbps, R_t = 300.0 Gbps, alpha = 0.8):
    1. Fast Recovery (step <= F, step 1):            Keeps R_t = 300.0 Gbps; binary-searches R_c = (200.0 + 300.0) / 2 = 250.0 Gbps
    2. Additive Increase (step > F, step 6):         R_t = min(LineRate, 300.0 + 10.0) = 310.0 Gbps; R_c = (250.0 + 310.0) / 2 = 280.0 Gbps
    3. Hyper-Additive Increase (both > F, step 9):   With i = 2, R_t = min(LineRate, 310.0 + 2 * 40.0) = 390.0 Gbps; R_c = (280.0 + 390.0) / 2 = 335.0 Gbps
```

You can walk the first cut with plain numbers. On a 400.0 Gbps link with alpha at 1.0, the rate halves to 200.0 Gbps. With alpha at 0.5, the same link drops only to 300.0 Gbps, and alpha moves to 0.53125. The code block above has the full equations.

The diagram below traces the same loop from sender to switch and back.

```mermaid
flowchart LR
    S["Sender NIC (RP)<br/>Rc, Rt, alpha"] -->|"1. RoCEv2 UDP 4791<br/>DSCP 26, ECN 01/10"| SW["Switch Queue 3 (CP)<br/>XON < Kmin < Kmax < XOFF"]
    SW -->|"2a. q >= Kmin:<br/>Mark ECN = 11 (CE)"| R["Receiver NIC (NP)<br/>Inspects CE bit"]
    R -->|"3. CNP Opcode 129 (0x81)<br/>DSCP 48 (Prio 6), ECN 01"| S
    SW -.->|"2b. If q >= XOFF:<br/>802.1Qbb 0x8808 Pause"| S
```

You can follow one congestion event through the five-step loop in the table. Each row names the counter you check to confirm that step.

| Loop component | Actor & hardware location | Trigger condition | Action taken | Key verification counter |
|---|---|---|---|---|
| **1. Forward data** | Sender NIC (RP) | Application posts RDMA verb | Emits UDP 4791 packet with DSCP 26 (Prio 3) and ECN = 01 or 10 | `tx_prio3_packets` |
| **2a. ECN marking** | Switch egress queue (CP) | Queue depth $q \ge K_{\min}$ (WRED) | Rewrites IP ECN bits to 11 (CE) and forwards packet normally | `rx_ecn_marked_prio3` |
| **2b. PFC backstop** | Switch ingress/egress (CP) | Ingress buffer crosses XOFF (49,152 B) | Sends 64 B `0x8808` XOFF (65,535 quanta) to link partner | `tx_pfc_prio3` / `rx_pfc_prio3` |
| **3. CNP feedback** | Receiver NIC (NP) | Receives RoCEv2 packet with ECN = 11 | Sends CNP (BTH opcode 129 / `0x81`, ECN 01, DSCP 48) to sender | `np_ecn_marked_roce_packets` |
| **4. Rate cut & recovery** | Sender NIC (RP) | Receives CNP or recovery timer fires | Cuts $R_c \leftarrow R_c(1 - \alpha/2)$, then runs Fast / AI / HAI recovery | `np_cnp_handled`, `rp_current_rate`, `rp_byte_reset` |

Before you change any marking threshold, check that the sender's counters show it responding to the marks.

---

## 4. Hop-by-hop PFC propagation, pause trees, and the PFC Watchdog

### 4.1 The 5-step hop-by-hop PFC propagation chain

When DCQCN cannot drain a congested downstream link fast enough, or when a receiver adapter hangs, PFC propagates backward across the fabric. That backpressure builds a pause tree. The tree freezes upstream spine and leaf queues, and it halts unrelated GPU jobs that share those transit links.

PFC moves backward through a strict five-step hardware chain. First, a transit switch such as SpineA receives a PFC XOFF frame on its egress interface facing LeafC or LeafD. Second, SpineA pauses transmission on that egress Queue 3 for the requested quanta duration. Third, packets from LeafA and LeafB keep arriving at SpineA for that paused queue. So SpineA's own ingress buffer for Priority 3 fills and breaches its XOFF threshold. Fourth, that ingress port sends a new PFC XOFF frame upstream toward LeafA and LeafB. Fifth, the chain repeats hop by hop until LeafA pauses the source server GPU101. That pause freezes all Priority 3 traffic on the affected branch, including unrelated flows from GPU103 on LeafB.

When you trace a pause tree, follow the chain one hop at a time, since the freeze spreads along that same path. Suppose you see a pause on one hop. The next step is to check the hop upstream of it.

### 4.2 The 3-stage PFC Watchdog (Detection, Mitigation, Restoration)

Picture a broken adapter driver or a PCIe credit loop that makes a downstream node, such as GPU102 on LeafC, emit XOFF frames continuously. The resulting PFC storm can lock up the entire fabric. Operators need an automated circuit breaker on every switch, one that isolates the broken sink before the upstream spine buffers freeze.

The PFC Watchdog on each switch monitors per-port pause duration. It breaks the storm in three stages: Detection, Mitigation and Restoration.

```mermaid
flowchart LR
    N["Normal Lossless<br/>paused_ms < 100 ms"] -->|"1. Detection:<br/>paused_ms >= 100 ms"| M{"2. Mitigation Mode<br/>(Drop vs Forward)"}
    M -->|"Drop Mode (Default)"| D["Flush existing queue,<br/>drop new pkts & XOFF"]
    M -->|"Forward Mode"| F["Ignore RX PFC frames,<br/>forward all queue pkts"]
    D -->|"3. Restoration:<br/>quiet_ms >= 200 ms"| R["Resume Lossless<br/>Un-pause Priority 3"]
    F -->|"3. Restoration:<br/>quiet_ms >= 200 ms"| R
```

The table lists what triggers each stage and what it does to the rest of the fabric.

| Watchdog stage | Trigger condition | Switch hardware actions | Impact on upstream fabric (LeafA, LeafB, GPU101, GPU103) |
|---|---|---|---|
| **1. Detection** | Port/queue remains paused by incoming XOFF frames for $\ge T_{\text{detect}}$ (e.g., 100 ms; storm tested at 150 ms) | Marks the port on SpineA facing LeafC as experiencing an abnormal PFC storm and increments watchdog storm counters | Identifies the stuck branch before upstream ingress buffers lock the entire spine tier |
| **2a. Mitigation (Drop mode — most common)** | Watchdog storm state active on queue | **(1)** Discards all packets already queued in the output queue; **(2)** discards new packets arriving for that output queue; **(3)** discards incoming pause frames from the same priority group | **Stops upstream pause propagation:** SpineA clears its buffer and never sends XOFF to LeafA or LeafB, isolating the blast radius to the broken LeafC -> GPU102 sink |
| **2b. Mitigation (Forward mode)** | Watchdog storm state active when configured for forward | Ignores received PFC frames on the port and forcefully forwards both queued and newly arriving packets downstream | Drains SpineA's buffer without pausing upstream hops, pushing packets toward LeafC |
| **3. Restoration** | Received PFC pause frames remain below threshold for $\ge T_{\text{restore}}$ (e.g., 200 ms quiet window; tested at 250 ms) | Lifts mitigation drops, un-pauses the queue, and restores normal IEEE 802.1Qbb lossless behavior | Fabric seamlessly returns to lossless RoCEv2 operation once the downstream fault clears |

You can read the table row by row, and each stage hands off to the next. Drop mode is the most common mitigation. It contains the damage, because SpineA never sends XOFF to LeafA or LeafB. Forward mode works differently. It keeps packets moving toward LeafC and never pauses the upstream hops.

Choose the mode with that trade-off in mind: Drop mode isolates the broken branch, while Forward mode keeps the buffer draining toward the receiver.

---

## 5. Next-generation congestion signaling: Source Flow Control and CSIG

ECN adds a forward trip and a return trip to every signal. PFC pauses a whole traffic class at once. Under extreme incast, large AI clusters still see microburst stalls because of these two trade-offs. Two newer standards aim to give direct, low-latency, flow-aware feedback that avoids them.

### 5.1 Source Flow Control (SFC, IEEE 802.1Qdw / Source PFC)

Consider what happens to a transit spine queue under ECN. The congestion mark has to reach the destination receiver and come back as a CNP before the sender reacts. Source Flow Control in IEEE 802.1Qdw removes both costs: the forward-trip delay of ECN and the class-wide blast radius of hop-by-hop PFC.

Follow the sequence, and you can see where the signal changes hands. A server on LeafA transmits a flow through SpineA toward LeafD. When the SpineA to LeafD queue crosses its SFC threshold, SpineA acts at once rather than waiting for the packet to reach the destination server. It trims the data packet payload and reverses the source and destination IP addresses in the header. Then it sends a flow-specific SFC congestion signal straight back toward the source, through SpineA to LeafA. When LeafA receives that signal, it can pause the specific queue locally, or it can forward the signal to an SFC-capable server adapter. For legacy adapters, LeafA translates the signal into a standard 802.1Qbb PFC pause frame. Because SFC triggers at the congested switch in half a round-trip time and identifies the specific flow, it avoids both the forward-path delay of ECN and the unfairness of class-wide PFC.

### 5.2 Congestion Signaling (CSIG, `draft-ravi-ippm-csig-01`)

A single ECN bit tells a sender that some hop crossed a threshold. It hides how much bandwidth remains and which switch tier is the bottleneck. Congestion Signaling, or CSIG, uses In-Band Network Telemetry to embed fixed-length, multi-bit bottleneck summaries directly inside live data packets.

The CSIG tag sits at Layer 2.5, between the Layer 2 Ethernet header and the Layer 3 IP header. It requires an IEEE-allocated Ethernet tag. As sender GPU1 transmits packets across hops to receiver GPU2, each switch updates the CSIG tag with its local bottleneck state. Receiver GPU2 reflects the accumulated CSIG summary back to GPU1 through CSIG reflection headers. That reflection lets the sender adjust both its injection rate and its multipath selection in real time. As you read the CSIG tag layout, notice that it carries four locator fields for each bottleneck.

```text
CSIG Tag Layout and Metadata Fields (draft-ravi-ippm-csig-01, ADC Ch 7 Figs 7-19..7-21):
  - Wire Header Placement:  Ethernet (L2) -> CSIG Tag (L2.5) -> IP (L3) -> UDP (L4) across CSIG1 -> CSIG2 -> CSIG3/CSIG4 -> CSIG5 -> CSIG6
  - Three CSIG Tag Sections:
    1. Signal Type:         Selects congestion metric requested by server (minimum ABW / C, minimum ABW [available bandwidth], or maximum PD [packet delay])
    2. Signal Value:        Carries the quantized multi-bit congestion measurement along the path
    3. Locator Metadata:    Static per-port identifier encoding 4 bottleneck fields:
                            (1) Capacity of bottleneck link, (2) Stage in Clos topology, (3) Device ID, (4) Link identification (uplink or downlink)
```

The table compares the five mechanisms on granularity, feedback path and lossless behavior.

| Mechanism | Standard / Draft | Granularity | Feedback path | Lossless guarantee | Primary advantage & trade-off |
|---|---|---|---|---|---|
| **ECN** | RFC 3168 | Per-flow (QP) | Switch -> Receiver -> CNP -> Sender (full RTT) | No (**lossy queue** if used alone) | Zero pause unfairness, but forward+reverse RTT is too slow for microbursts |
| **PFC** | IEEE 802.1Qbb | Per-priority class (0..7) | Congested Port -> Upstream Neighbor (1 hop) | Yes (**lossless queue**) | Immediate microburst protection, but causes head-of-line blocking & pause trees |
| **DCQCN** | SIGCOMM 2015 / RoCEv2 | ECN per-QP + PFC per-class | CNP end-to-end (XON < ECN < XOFF) | Yes (when PFC backstop enabled) | Production standard: ECN handles steady contention; PFC catches bursts |
| **SFC** | IEEE 802.1Qdw | Per-flow | Congested Switch -> Leaf / Source (direct reverse) | Yes (with leaf PFC translation) | Avoids ECN forward-path delay and avoids class-wide PFC blocking |
| **CSIG** | `draft-ravi-ippm-csig-01` | Per-packet / Per-flow INT | L2.5 tag -> Receiver CSIG Reflection -> Sender | Complements rate & path control | Exposes exact bottleneck (capacity, stage, device ID, uplink/downlink) |

ECN is lossy when used alone, and DCQCN stays lossless only with its PFC backstop enabled. DCQCN remains the production standard in the table. If you compare the rows, you can see which gap each newer standard targets. SFC and CSIG are the newer standards that aim at the gaps DCQCN leaves.

---

## Commands and configurations that matter

Every operational command below is marked `(untested here)`. They reproduce the exact verification sequence from our production runbooks, and none of them ran in this chapter's environment.

### 1. Inspecting PFC enablement, buffer allocation, XOFF, XON, and DSCP trust (`mlnx_qos`)

Start with the switch port. The first command shows per-priority PFC, buffer sizes, XOFF and XON. The second confirms that PFC is enabled on Priority 3 alone, the lossless class.

```bash
# (untested here) Inspect per-priority PFC, buffer sizes, XOFF, and XON on switch port swp12
mlnx_qos -i swp12

# (untested here) Verify PFC is enabled ONLY on Priority 3 (0 0 0 1 0 0 0 0), never on Priority 0 (management)
mlnx_qos -i swp12 | grep -A3 "PFC configuration"
```

### 2. Walking a PFC pause tree and correlating ECN marks (`ethtool -S`)

Compare the downstream receiver-facing port with the upstream relay port. The final command samples the ECN mark counter twice, five seconds apart, so you can see how fast marking is moving.

```bash
# (untested here) Check downstream receiver-facing leaf port (swp7) vs upstream relay port (swp3)
ethtool -S swp7 | egrep "tx_pfc_prio3|rx_pfc_prio3|rx_ecn_marked_prio3"
ethtool -S swp3 | egrep "tx_pfc_prio3|rx_pfc_prio3|rx_ecn_marked_prio3|queue3_occupancy"

# (untested here) Capture two consecutive 5-second windows on swp9 to measure active ECN marking delta
ethtool -S swp9 | grep rx_ecn_marked_prio3 && sleep 5 && ethtool -S swp9 | grep rx_ecn_marked_prio3
```

### 3. Auditing NIC DCQCN Notification Point and Reaction Point counters (`mlx5_cnp_stats`)

The first command confirms that the sender's Reaction Point receives CNPs and adjusts its rate in response to the switch ECN marks. The second samples the current rate and CNP count every second, which helps you catch synchronized oscillation.

```bash
# (untested here) Verify sender RP is receiving CNPs and adjusting rate in response to switch ECN marks
mlx5_cnp_stats -d mlx5_0

# (untested here) Sample RP current rate and CNP count at 1-second intervals to detect synchronized oscillation
mlx5_cnp_stats -d mlx5_0 --interval 1
```

### 4. End-to-end 4-lab RoCEv2 path inventory, contention test, and GID evidence ladder

The first block walks the path for Labs 01 and 02. It checks the route, MTU 9000, the 400G link speed, the RDMA device mapping and that uncorrected FEC errors stay at zero. The second block compares the healthy rail with the misaligned rail for Lab 04.

```bash
# (untested here) Lab 01 & 02: Verify route, MTU 9000, 400G link speed, RDMA netdev mapping, and zero uncorrected FEC
ip route get 10.20.8.5
ip link show dev ens1f0
ethtool ens1f0 | egrep "Speed|Duplex|Link"
rdma link show
date -u && ethtool -S ens1f0 | egrep "ecn_marked|pfc_prio|rx_prio3_packets|tx_prio3_packets|fec_uncorrected"

# (untested here) Lab 04: Compare healthy rail (mlx5_0, 392 Gbps in 2.1s) vs misaligned rail (mlx5_1, 156 Gbps in 8.2s)
ibv_devinfo -d mlx5_0 -i 1 | grep GID
ibv_devinfo -d mlx5_1 -i 1 | grep GID
ib_write_bw -d mlx5_0 -i 1 10.20.8.5
```

Compare the counters on both ends of each path before you draw a conclusion about the fabric.

---

## How it fails

When congestion control misbehaves on a production AI fabric, the counters on switches and network adapters tell you which failure you are looking at. They separate an upstream pause relay from a broken feedback loop, and both from an endpoint rail bug.

```text
Production Counter Signatures Across Volume 09 Scenarios & Labs 01-04:
  - Ch 4 Scenario 1 (Pause Tree Relay vs Root):
    * Relay hop swp3: rx_pfc_prio3 = 41,823 | tx_pfc_prio3 = 41,810 | rx_ecn_marked_prio3 = 190 | queue3_occupancy = 98%
    * Receiver port swp7: tx_pfc_prio3 = 0 | rx_ecn_marked_prio3 = 2,200 (11.58x higher than swp3's 190)
  - Ch 5 Healthy Loop vs Broken Feedback (swp9 & mlx5_0):
    * Healthy swp9: rx_ecn_marked_prio3 climbs 84,200 -> 84,512 (delta 312) | NP = 305 | RP np_cnp_handled = 298 | rp_byte_reset = 1
    * Scenario 1 (Weak RP / Oversubscription): rx_ecn_marked_prio3 = 412,880 | rx_pfc_prio3 = 93,100 | np_cnp_handled = 409,500 (99.18%) | rp_current_rate = 98 Gbps on 100G
    * Scenario 2 (Oscillation): t=0s (40 CNPs, 100 Gbps) -> t=1s (380 CNPs, 12 Gbps) -> t=2s (2 CNPs, 95 Gbps) -> t=3s (410 CNPs, 11 Gbps) -> t=4s (3 CNPs, 96 Gbps)
    * Scenario 3 (Broken Return Path): rx_ecn_marked_prio3 +15,000, rx_pfc_prio3 +4,200, but sender np_cnp_handled = 0 and rp_current_rate = 100 Gbps
  - Lab 01-04 Evidence Ladder:
    * Lab 01 Baseline: fec_corrected_blocks = 412, fec_uncorrected_blocks = 0
    * Lab 03 Contention (60 s): rx_ecn_marked_prio3 = 47,829 | rx_pfc_prio3 = 412 | tx_pfc_prio3 = 14 | rx_prio3_packets 102,314 -> 51,234,892 (delta 51,132,578) | tx_prio3_packets 89,621 -> 48,901,234 (delta 48,811,613) | Sender A (89.2 Gbps) + Sender B (87.1 Gbps) = 176.3 Gbps
    * Lab 04 Misaligned Rail: mlx5_0 / ens1f0 (GID[3] fe80::0c42:a1ff:fec8:d79b/64) achieves 392 Gbps in 2.1 s (0 retries) vs mlx5_1 / ens1f1 (GID[3] fe80::0c42:a1ff:fec8:d79d/64) dropping to 156 Gbps in 8.2 s (2.51x slower, 3.90x longer, 24 RETRY_EXC_ERR, rx_ecn_marked_prio3 = 142)
```

The table maps each failure mode to its symptoms, root cause and fix, so you can match your own counters to a row.

| Failure mode | Observable symptoms & counter signature | Root cause | Diagnostic commands & remediation |
|---|---|---|---|
| **1. Upstream PFC pause tree from a downstream receiver bottleneck (`swp3` vs `swp7`)** | Collective latency spikes with 0 link errors and 0 drops. Upstream port `swp3` shows `rx_pfc_prio3: 41823`, `tx_pfc_prio3: 41810`, `rx_ecn_marked_prio3: 190`, and `queue3_occupancy: 98%`, while downstream receiver port `swp7` shows `tx_pfc_prio3: 0` and `rx_ecn_marked_prio3: 2200`. | `swp3` is a **relay hop** caught in the middle of a pause chain, whereas `swp7` (`rx_ecn_marked = 2,200`, 11.58x higher than `swp3`) is marking heavily at the receiver edge. | Walk in the `rx_pfc` direction until `tx_pfc == 0` (`trace_pause_tree_origin`). Relieve the destination bottleneck via job placement, adaptive routing, or validated ECN tuning; never blindly disable PFC. |
| **2. Management SSH freeze from accidental `prio0` PFC leak** | SSH sessions and Kubernetes heartbeats stall specifically during AllReduce bursts. `mlnx_qos -i swp12` shows `enabled: 1 0 0 1 0 0 0 0`. | PFC was accidentally enabled on **Priority 0** alongside Priority 3, allowing congestion or shared buffer pressure to pause management traffic. | Reconfigure `mlnx_qos` so `enabled` is set strictly to `0 0 0 1 0 0 0 0` (Priority 3 only) and verify `rx_pfc_prio0 == 0` under load. |
| **3. Heavy ECN marking + heavy PFC with weak RP throttling (98 Gbps on 100G)** | Switch `swp9` shows `rx_ecn_marked_prio3: 412880` and `rx_pfc_prio3: 93100`; sender `mlx5_0` shows `np_cnp_handled: 409500` (99.18% of marks), yet `rp_current_rate: 98 Gbps` on a 100 Gbps link. | The ECN/CNP feedback loop is intact (`409,500 / 412,880 = 99.18%` delivered), but the endpoint RP rate-cut profile is too weak or the destination cut is structurally oversubscribed to drain the queue before XOFF. | Apply the vendor-qualified DCQCN RP profile and fix destination oversubscription or job placement before altering switch thresholds. |
| **4. Synchronized sender rate oscillation (`100 -> 12 -> 95 -> 11 -> 96 Gbps`)** | Fabric utilization pulses in 1-second waves as `rp_current_rate` collapses by 88 Gbps and rebounds every second. | DCQCN rate-decrease factor is overly aggressive and recovery (`R_AI`/`R_HAI`) is too fast, causing all synchronized senders sharing the bottleneck to cut and overshoot in lockstep. | Restore the qualified DCQCN endpoint profile so `rp_current_rate` converges into a stable band (`70–90%` of line rate) instead of swinging `11%..96%`. |
| **5. Broken CNP return path or asymmetric sender response (`np_cnp_handled == 0`)** | Switch `rx_ecn_marked_prio3` climbs by `15,000+` and `rx_pfc_prio3` climbs by `4,200+`, but sender `np_cnp_handled` stays at 0 and `rp_current_rate` stays pinned at 100 Gbps. | Reverse-path ACL/routing drops CNP frames (UDP 4791, opcode 129), CNPs on Priority 6 are misclassified into a congested queue, or ECN/DCQCN is disabled on the receiver/sender NIC. | Audit bidirectional CNP reachability (DSCP 48 -> Queue 6) and verify `np_ecn_marked_roce_packets` on the receiver and `np_cnp_handled` on the sender track switch `rx_ecn_marked_prio3`. |
| **6. Misaligned RDMA device / GID selection masquerading as fabric congestion (`mlx5_1` vs `mlx5_0`)** | `ib_write_bw -d mlx5_1 -i 1 10.20.8.5` degrades from **392 Gbps (2.1 s, 0 retries)** on `mlx5_0` to **156 Gbps (8.2 s, 2.51x slower, 3.90x longer)** with **24 `RETRY_EXC_ERR`** completions and `rx_ecn_marked_prio3: 142` on `ens1f1`. | Process bound to the wrong RDMA device/rail (`mlx5_1` / `ens1f1` instead of `mlx5_0` / `ens1f0`), forcing cross-rail routing and ECN marks. | Walk the 4-layer evidence ladder (1. Physical `rdma link show` -> 2. Route/MTU 9000 -> 3. RoCE GID/device -> 4. QoS counters). Fix the process `-d mlx5_0` binding; never tune switch PFC/ECN for an endpoint selection bug. |

If you see the PFC leak or the wrong-device case, remember that neither one is fabric congestion. One is a PFC leak onto management traffic, and the other is a process bound to the wrong RDMA device.

Each remedy points at one layer, so you can fix that layer and leave the others alone.

---

## Hands-on lab

You can run this lab on a local workstation or on a Nebius GPU node. It uses our self-checking Python simulator, so no live switch hardware is required. The commands for live switches and adapters in the previous section are marked `(untested here)`.

Run the Chapter 12.4 verification lab, `code/part12/pfc_ecn_dcqcn_lab.py`. It executes 28 checks against the protocol model in `code/part12/pfc_ecn_dcqcn.py`.

```bash
python3 code/part12/pfc_ecn_dcqcn_lab.py
```

When the lab passes, the output looks like the block below, and it ends with 28 passed and 0 failed.

```text
=== Chapter 12.4 Lab: PFC, ECN and DCQCN in Depth ===
  [PASS] ADC Ch 7 Table 7-1 IP Header & ECN bits: 8-bit ToS = 6-bit DSCP + 2-bit ECN (00 Not-ECT drop, 01 ECT(1), 10 ECT(0), 11 CE)
  [PASS] ADC Ch 7 RoCEv2 & CNP frame: UDP destination port 4791; CNP carries IB BTH opcode 129 (0x81, binary 10000001) and ECN 01
  [PASS] V9 Ch 4/6 & Handbook 2.19 DSCP markings: RoCE data DSCP 26 -> Prio 3, CNP DSCP 48 -> Prio 6, and tcpdump tos 0xb8 >> 2 == DSCP 46 (EF)
  [PASS] ADC Ch 7 Fig 7-10..7-12 IEEE 802.1Qbb PFC frame: 64B wire frame, Dst MAC 01:80:C2:00:00:01, Src 10:0e:7e:b7:a7:1b, EtherType 0x8808, Opcode 0x0101, Class 3 enable vector 0x0008, 16-octet Time field
  [PASS] IEEE 802.1Qbb Quanta math (100 Gbps): 65,535 quanta * 512 bit-times = 33,553,920 bit-times = 335,539.2 ns (335.5392 us)
  [PASS] IEEE 802.1Qbb Quanta math (200 Gbps & 400 Gbps): 200G max pause = 167.7696 us; 400G max pause = 83,884.8 ns (83.8848 us)
  [PASS] IEEE 802.1Qbb Quanta math (800 Gbps & XON=0): 800G max pause = 41,942.4 ns (41.9424 us); quanta=0 is explicit XON un-pause (0.0 us)
  [PASS] V9 Ch 4 mlnx_qos -i swp12 buffer profile: port rx buffer = 262,144 B, prio3 buffer = 65,536 B, XOFF = 49,152 B (75.0%), XON = 32,768 B (50.0%)
  [PASS] V9 Ch 4 mlnx_qos -i swp12 headroom & hysteresis: headroom = 65,536 - 49,152 = 16,384 B (25.0%); hysteresis = 49,152 - 32,768 = 16,384 B (25.0%)
  [PASS] Flight-time headroom sizing (400 Gbps, MTU 9000): 2m DAC needs 49,064 B (31,000 B wire + 18,064 B serialization); 500m fiber (5,000 ns RTT) needs 298,064 B (280,000 B wire + 18,064 B serialization)
  [PASS] WRED ECN Green & Red Zones (K_min=150 KB, K_max=1,500 KB from V6 Ch 1): 100 KB -> 0.0 (GREEN_ZONE_FREE_FLOW); 1,600 KB -> 1.0 (RED_ZONE_100PCT_ECN_MARKING)
  [PASS] WRED ECN Yellow Zone linear ramp: at 487.5 KB (25% of [150, 1500]), p = 0.25; at midpoint 825 KB, p = 0.50 (YELLOW_ZONE_PROBABILISTIC_ECN)
  [PASS] ADC Ch 7 Fig 7-16 DCQCN threshold ordering: valid ordering satisfies XON (32,768) < K_min (150,000) < K_max (1,500,000) < XOFF (2,000,000) < BufferMax (2,500,000)
  [PASS] ADC Ch 7 Fig 7-14 & 7-16 invalid threshold ordering detection: catches K_min >= K_max, K_max >= XOFF (PFC fires before ECN saturates), and XOFF == BufferMax (zero headroom)
  [PASS] DCQCN RP Rate Cut (V9 Ch 5 sequence diagram 400 -> 200 Gbps): at alpha=1.0, R_c = 400 * (1 - 1.0/2) = 200.0 Gbps (max 50% cut, R_t=400.0 Gbps); at alpha=0.5, R_c = 300.0 Gbps
  [PASS] DCQCN RP 3-Stage Recovery: Fast Recovery step 1 raises 200 -> 250.0 Gbps (R_t=300); Additive Increase step 6 raises R_t to 310 -> R_c=280.0 Gbps; Hyper-Increase step 9 raises R_t to 390 -> R_c=335.0 Gbps while alpha decays
  [PASS] ADC Ch 7 Fig 7-15 PFC Watchdog Stage 1 (Detection) & Stage 2 (Drop Mitigation): at 150 ms >= 100 ms threshold, Drop mode flushes existing queue packets, drops new packets, and discards incoming pause frames to stop upstream propagation
  [PASS] ADC Ch 7 Fig 7-15 PFC Watchdog Forward Mode & Stage 3 (Restoration): Forward mode ignores PFC and forwards queue packets; after 250 ms >= 200 ms quiet interval, Restoration resumes lossless Ethernet
  [PASS] V9 Ch 4 Scenario 1 Pause Tree Walk: swp3 (rx_pfc=41,823, tx_pfc=41,810, rx_ecn_marked=190, queue3_occupancy=98%) is a middle relay hop; swp7 (tx_pfc=0, rx_ecn_marked=2,200) is the downstream receiver-facing port
  [PASS] V9 Ch 4 Scenario 2 Management Priority Leak: mlnx_qos enabled=[1,0,0,1,0,0,0,0] enables PFC on prio0 (management) alongside prio3 (RoCE), stalling SSH during training bursts; fix sets enabled=[0,0,0,1,0,0,0,0]
  [PASS] V9 Ch 5 Healthy ECN/CNP Tracking (swp9): rx_ecn_marked_prio3 climbs 84,200 -> 84,512 (delta 312), mlx5_0 np_ecn_marked_roce_packets=305, np_cnp_handled=298, rp_byte_reset=1 -> HEALTHY_CLOSED_LOOP_CONTAINED
  [PASS] V9 Ch 5 Scenario 1 (Weak RP Response / Capacity Bottleneck): rx_ecn_marked_prio3=412,880, rx_pfc_prio3=93,100, np_cnp_handled=409,500 (99.18% of marks), but rp_current_rate=98 Gbps on 100G link
  [PASS] V9 Ch 5 Scenario 2 (Synchronized Rate Oscillation) & Scenario 3 (Broken Return Path): rp_current_rate swinging 100 -> 12 -> 95 -> 11 -> 96 Gbps (88 Gbps drop) diagnoses oscillation; np_cnp_handled=0 diagnoses broken reverse path
  [PASS] V9 Lab 03 Bounded Contention (60s, 2 senders on 400G uplink): rx_ecn_marked_prio3=47,829, rx_pfc_prio3=412, tx_pfc_prio3=14, rx_prio3_packets delta=51,132,578, tx_prio3_packets delta=48,811,613; Sender A (89.2 Gbps) + Sender B (87.1 Gbps) = 176.3 Gbps
  [PASS] V9 Lab 01/02/04 Evidence Ladder: Lab 01 clean baseline fec_corrected_blocks=412, fec_uncorrected_blocks=0; Lab 04 healthy mlx5_0 (392 Gbps in 2.1s, 0 retries) vs misaligned mlx5_1 (156 Gbps in 8.2s, 2.51x slower, 24 RETRY_EXC_ERR, rx_ecn_marked_prio3=142)
  [PASS] Edge-case validation: compute_pfc_pause_duration rejects quanta > 65,535; evaluate_pfc_buffer_profile enforces 0 < XON < XOFF < PriorityBuffer
  [PASS] Hysteresis validation: XON == XOFF (49,152 B) is rejected as XON_GE_XOFF_NO_HYSTERESIS to prevent rapid pause/unpause oscillation
  [PASS] ADC Ch 7 Source Flow Control (SFC, IEEE 802.1Qdw) & Congestion Signaling (CSIG, draft-ravi-ippm-csig-01): CSIG locator metadata has 4 fields (capacity, stage, device ID, link direction)

Summary: 28 passed, 0 failed (total 28)
```

Each PASS line names the rule it checks, so you can find the matching section of this chapter.

---

## Common first mistakes

1. **Reading rising PFC counters as proof that the fabric is healthy.** PFC is a reactive, last-resort safety net. Sustained `rx_pfc_prio3` or `tx_pfc_prio3` activity means something failed to drain the queue before XOFF. That failure may sit in the ECN and DCQCN loop, in the routing, or in the destination capacity.
2. **Enabling PFC on several priorities, or on Priority 0.** When PFC is enabled on Priority 0, SSH, BGP and Kubernetes control traffic sits inside a pause domain. Keep PFC restricted to the dedicated lossless RoCE priority, Priority 3, and you keep management traffic out of the pause domain.
3. **Setting $K_{\max}$ at or above XOFF, or setting XOFF equal to BufferMax.** If $K_{\max}$ is at or above XOFF, PFC pauses fire before WRED ECN marking reaches 100 percent. If XOFF equals the priority buffer size, there is zero headroom. In-flight cable bytes then overflow the queue after XOFF is sent.
4. **Assuming switch ECN marks prove that senders are slowing down.** A switch that increments `rx_ecn_marked_prio3` has only proven that the Congestion Point marked the packet. To confirm the reverse CNP loop, verify `np_ecn_marked_roce_packets` on the receiver. Then check `np_cnp_handled` and `rp_current_rate` on the sender.
5. **Tuning ECN or PFC thresholds after ECN marks drop to zero, or after one job slows down.** A drop of ECN marks to zero often means a QoS classification bug moved RoCEv2 traffic into a lossy best-effort queue. A single-process throughput drop with `RETRY_EXC_ERR` completions is frequently a wrong local RDMA device or GID binding.

Before you touch a threshold, confirm that traffic lands in the right queue and binds to the right device. If you skip that check, you may tune a threshold that was never the problem.

---

## Exercises

Each exercise covers one part of the chapter, and you can check your work against the matching section. Keep your units straight, because bytes, bit-times, and nanoseconds all appear. Exercises 1 through 4 are arithmetic, so the tables and equations in Sections 2 and 3 let you check each answer.

1. Read a maximum-pause XOFF frame. A congested switch port sends an 802.1Qbb XOFF frame for Priority 3 with a pause value of 65,535 quanta. Give the destination MAC, the EtherType, and the control opcode. Give the Class Enable Vector in hex. Then calculate the pause duration in microseconds at 100 Gbps and at 800 Gbps, and say what pause value an XON frame carries.
2. Size the headroom. Use `calculate_flight_headroom_bytes` to compute the minimum flight-time headroom at 400 Gbps for a 2 m DAC cable. Do the same for a 500 m fiber. Then read the output of `mlnx_qos -i swp12` and work out the headroom and hysteresis, first in bytes and then as percentages. Finally, say what fails when either one is zero.
3. Check the WRED marking curve. A switch queue has K_min at 150 KB, K_max at 1,500 KB, P_max at 1.0, and XOFF at 2,000 KB. Calculate the marking probability and the zone at 100 KB, 487.5 KB, 825 KB, and 1,600 KB. Then explain why a K_max of 55,000 B breaks DCQCN on a queue whose XOFF is 49,152 B.
4. Trace a DCQCN rate cut. A 400.0 Gbps RoCEv2 sender receives a CNP on UDP port 4791. Compute the new current rate R_c, the target rate R_t, and the updated alpha, starting from an alpha of 1.0. Repeat with an alpha of 0.5. Then trace Fast Recovery at step 1, Additive Increase at step 6, and Hyper-Additive Increase at step 9.
5. Trace the PFC Watchdog. A downstream host floods SpineA with XOFF frames. Trace the three stages of the PFC Watchdog on SpineA. Then contrast the three Drop-mode actions with Forward mode, and say how Source Flow Control and Congestion Signaling improve on hop-by-hop PFC.
6. Read the production telemetry. Compare the two switch ports `swp3` and `swp7` in the failure table. Then compare `swp9`, where the Reaction Point throttles weakly and the rate oscillates in sync. Finish with the bounded contention in Lab 03 and the wrong rail in Lab 04.

---

## Interview angles

1. **"What does PFC pause: an application, a flow, a priority, or an entire link?"**
   - **Trap to avoid:** Saying that PFC pauses a congested RoCE flow, or that it pauses the entire physical link. The second answer describes IEEE 802.3x Global Pause.
   - **Strong answer:** PFC under IEEE 802.1Qbb pauses one 802.1p priority class, on one link, in one direction. It has no visibility into individual flows or Queue Pairs. So every flow mapped to Priority 3 on that link halts together through head-of-line blocking. That is why strict QoS classification matters: Priority 0 management and storage must stay out of Priority 3.
2. **"How do you find the root of a PFC pause tree using switch counters?"**
   - **Strong answer:** Start by reading the per-port `rx_pfc_prio3`, `tx_pfc_prio3`, `queue3_occupancy` and `rx_ecn_marked_prio3` counters on every hop. A port where both `rx_pfc` and `tx_pfc` increment at high occupancy is a middle relay hop, passing backpressure upstream. Walk downstream in the direction of `rx_pfc` until you reach the egress port where `tx_pfc == 0` and `rx_ecn_marked_prio3` is high. That downstream bottleneck is the root of the pause tree.
3. **"Draw the end-to-end DCQCN feedback loop and identify the four places it can fail."**
   - **Strong answer:** Picture the loop as four stages. First, the forward RoCEv2 packet on UDP port 4791 must be classified into lossless Queue 3 and marked CE by the switch Congestion Point. Second, the CE-marked packet must reach the receiver Notification Point. Third, the receiver adapter must generate a CNP on Priority 6 that survives the reverse path. Fourth, the sender Reaction Point must process the CNP and apply a properly tuned rate cut. If any stage breaks, the switch keeps marking until the queue hits XOFF and triggers PFC.
4. **"After a configuration change, switch ECN marks drop to zero. Why is that not automatically a win?"**
   - **Strong answer:** Zero ECN marks is ambiguous until you prove two things. First, confirm that traffic still lands in Queue 3 by checking that `tx_prio3_packets` and `rx_prio3_packets` grow at the expected rate. A trust bug often sends RoCEv2 into best-effort Queue 0, where ECN is disabled. Second, confirm that packet drops and `RETRY_EXC_ERR` completions stay at zero while job completion time improves.

---

## Checkpoint questions (20)

Suppose you map a 2-tier or 3-tier Clos fabric. These are the six congestion points you would find.

<details><summary>**1. What are the six congestion points in a 2-tier or 3-tier Clos AI Ethernet fabric?**</summary>

1. **Local leaf link (CP1):** Two servers on LeafA send line-rate traffic to a single south-facing port on LeafA.
2. **Leaf-to-spine link (CP2):** Two servers on LeafA hash onto the same northbound uplink, from LeafA to SpineA.
3. **Spine-to-leaf link (CP3):** Servers on LeafA and LeafB converge at SpineA onto a single southbound downlink to LeafD.
4. **Leaf-to-server link (CP4):** Traffic spread across SpineA and SpineB converges at LeafD onto one receiver server link.
5. **Spine-to-super-spine link (CP5):** Flows at SpineA hash onto a single northbound uplink to SuperSpineA.
6. **Super-spine-to-spine link (CP6):** Multi-pod flows at SuperSpineA converge onto a single southbound downlink to SpineC.
</details>

<details><summary>**2. Why is a switch queue with only ECN enabled called a "lossy queue", whereas a queue with PFC enabled is called a "lossless queue"?**</summary>

ECN signals congestion end to end. The marked packet has to travel forward to the receiver, and the receiver has to send a CNP back before the sender slows. If traffic bursts faster than that round trip, the buffer overflows and drops packets, which makes it a lossy queue. PFC works differently. When XOFF is crossed, it sends an 802.1Qbb XOFF frame straight to the immediate upstream neighbor, across one hop. That pause stops transmission before the headroom buffer overflows, so the queue stays lossless.
</details>

<details><summary>**3. How are the 8 bits of the IP ToS / Traffic Class byte partitioned between DSCP and ECN, and what do the four 2-bit ECN codepoints (`00`, `01`, `10`, `11`) mean?**</summary>

The upper 6 bits hold a DSCP value from 0 to 63, which QoS uses to mark the traffic class. The lower 2 bits hold the ECN field.
- **`00` (Not-ECT):** The transport is not ECN-capable, so a congested switch drops the packet.
- **`01` (ECT(1))** and **`10` (ECT(0)):** These are ECN-capable codepoints, and switches treat them the same. `01` is also set on returning CNP frames.
- **`11` (CE, Congestion Experienced):** A congested switch sets this when queue depth crosses the ECN threshold.
</details>

<details><summary>**4. What UDP port, InfiniBand BTH opcode, ECN codepoint, and DSCP value identify a RoCEv2 Congestion Notification Packet (CNP)?**</summary>

A CNP is a RoCEv2 packet on UDP destination port 4791. The destination adapter generates it with InfiniBand Base Transport Header opcode 129. It carries IP ECN bits set to `01`, and it typically carries DSCP 48, which maps to high-priority control Queue 6. That mapping keeps CNPs from waiting behind congested Priority 3 data. The CNP also carries the number of the congested destination Queue Pair. If you capture one, you can read that Queue Pair number straight from it.
</details>

<details><summary>**5. What are the exact Layer 2 header fields of an IEEE 802.1Qbb PFC XOFF frame for Priority 3?**</summary>

Here are the fields of a Priority 3 XOFF frame, as they appear on the wire.

```text
Wire size:            64 bytes
Destination MAC:      01:80:C2:00:00:01 (link-local MAC control multicast)
Source MAC:           Sending switch port MAC (e.g., 10:0e:7e:b7:a7:1b)
EtherType:            0x8808
Control Opcode:       0x0101 (Class-Based Flow Control)
Class Enable Vector:  0x0008 (1 << 3, enabling Class 3 while C0..C2, C4..C7 are 0)
Time field:           16 octets (8 classes x 2 octets), Class 3 = 65535 (0xFFFF) for XOFF or 0 (0x0000) for XON
```
</details>

<details><summary>**6. How many bit-times are in one IEEE 802.1Qbb pause quantum, and what is the maximum pause duration (65,535 quanta) at 100 Gbps, 200 Gbps, 400 Gbps, and 800 Gbps?**</summary>

One quantum is 512 bit-times, so the maximum of 65,535 quanta is 33,553,920 bit-times. Divide that by each link speed to get the pause duration.

```text
100 Gbps:  33,553,920 / 100 = 335,539.2 ns = 335.5392 us
200 Gbps:  33,553,920 / 200 = 167,769.6 ns = 167.7696 us
400 Gbps:  33,553,920 / 400 =  83,884.8 ns =  83.8848 us
800 Gbps:  33,553,920 / 800 =  41,942.4 ns =  41.9424 us
```
</details>

<details><summary>**7. How do you calculate the minimum PFC headroom buffer for a 2 m DAC cable versus a 500 m optical fiber at 400 Gbps with MTU = 9,000 bytes and 600 ns transceiver/ASIC delay?**</summary>

Use the flight-time headroom equation from Section 2.4, and apply it to both links:

```text
2 m DAC:      RTT_cable = 20 ns    | total = 620 ns   | wire = 31,000 B  | + 18,064 B serialization = 49,064 bytes
500 m fiber:  RTT_cable = 5,000 ns | total = 5,600 ns | wire = 280,000 B | + 18,064 B serialization = 298,064 bytes (+249,000 B delta)
```
</details>

<details><summary>**8. In `mlnx_qos -i swp12`, Priority 3 has a 65,536-byte buffer out of a 262,144-byte port buffer, XOFF = 49,152 bytes, and XON = 32,768 bytes. What are the headroom and hysteresis, and why are both required?**</summary>

The headroom is 16,384 bytes, or 25.0 percent above XOFF. It absorbs packets that are still in flight after XOFF is sent. The hysteresis is also 16,384 bytes. It is the 25.0 percent gap between XOFF at 75.0 percent and XON at 50.0 percent, and it stops XOFF and XON from oscillating around a single queue fill level. You need both, because headroom prevents loss and hysteresis prevents rapid toggling.
</details>

<details><summary>**9. How does WRED compute ECN marking probability across the Green, Yellow, and Red zones (`K_min = 150 KB`, `K_max = 1,500 KB`, `P_max = 1.0`)?**</summary>

Suppose you walk a queue from empty into the Red Zone. The probability stays at zero in the Green Zone, rises in a straight line through the Yellow Zone, and reaches 1.0 in the Red Zone.

```text
Green Zone (q < 150 KB, e.g., 100 KB):       P_mark = 0.0 (0%, free flow)
Yellow Zone (150 KB <= q < 1,500 KB):        P_mark = (q - 150) / (1500 - 150) -> 0.25 (25%) at 487.5 KB; 0.50 (50%) at 825 KB
Red Zone (q >= 1,500 KB, e.g., 1,600 KB):    P_mark = 1.0 (100% of packets marked with CE)
```
</details>

<details><summary>**10. Why must DCQCN thresholds strictly obey `XON < K_min < K_max < XOFF < BufferMax`?**</summary>

Keeping $K_{\min} < K_{\max} < \text{XOFF}$ lets WRED ECN marking start early and reach 100 percent before the buffer hits XOFF. That gives the DCQCN loop time to slow the offending Queue Pairs without firing class-wide PFC pauses. Keeping $\text{XOFF} < \text{BufferMax}$ preserves lossless flight-time headroom, and $\text{XON} < \text{XOFF}$ provides drain hysteresis.
</details>

<details><summary>**11. How does a DCQCN Reaction Point cut its transmission rate upon receiving a CNP, and what is the maximum single-step cut?**</summary>

When a CNP arrives, the sender saves $R_t$ from $R_c$, then cuts its current rate using the congestion estimate $\alpha$. Alpha stays between 0 and 1, so a single cut can remove at most half of the rate. At $\alpha = 1.0$, the largest single-step cut is 50 percent. A 400.0 Gbps sender therefore cuts to at least 200.0 Gbps in one step.
</details>

<details><summary>**12. How do the three stages of DCQCN rate recovery (Fast Recovery, Additive Increase, Hyper-Additive Increase) work when CNPs stop arriving?**</summary>

While $\alpha$ decays toward zero, the sender moves through three recovery phases:

```text
1. Fast Recovery (step <= F):               Keeps R_t fixed; R_c = (R_c + R_t) / 2 (e.g., 200.0 and 300.0 -> 250.0 Gbps)
2. Additive Increase (step > F, 1 counter): R_t = min(LineRate, R_t + R_AI); R_c = (R_c + R_t) / 2 (e.g., R_t = 310.0 -> R_c = 280.0 Gbps)
3. Hyper-Additive Increase (both > F):      R_t = min(LineRate, R_t + i * R_HAI); R_c = (R_c + R_t) / 2 (e.g., R_t = 390.0 -> R_c = 335.0 Gbps)
```
</details>

<details><summary>**13. List the five steps by which a PFC pause frame propagates hop by hop from an egress port to an upstream switch.**</summary>

Suppose a transit switch receives a PFC XOFF frame on an egress port. You can follow the chain in five steps.

1. The PFC XOFF frame arrives on an egress interface.
2. The switch pauses transmission on the matching egress queue.
3. Packets headed for that paused queue pile up in the ingress lossless buffer, which breaches the ingress XOFF threshold.
4. The ingress port generates a new PFC XOFF frame toward its upstream neighbor.
5. The cycle repeats hop by hop back to the sender network adapters.
</details>

<details><summary>**14. What are the three stages of the PFC Watchdog, and what three actions does Drop mitigation perform?**</summary>

1. **Detection:** The Watchdog monitors the pause duration per port. If the port stays paused for at least $T_{\text{detect}}$, such as 100 ms, it flags a PFC storm.
2. **Mitigation:** In Drop mode, the switch discards all packets already in the output queue, and it discards new packets arriving for that queue. It also discards incoming pause frames for that priority group, so pauses do not propagate upstream. In Forward mode, the switch ignores received PFC frames and forwards packets.
3. **Restoration:** Once received PFC frames stay below the threshold for at least $T_{\text{restore}}$, such as 200 ms, the queue is un-paused and lossless Ethernet resumes.
</details>

<details><summary>**15. How does Source Flow Control (SFC, IEEE 802.1Qdw) differ from both ECN and traditional hop-by-hop PFC?**</summary>

When a transit switch queue crosses its SFC threshold, SpineA trims the packet payload and reverses the source and destination IP headers. It then sends a flow-specific SFC signal straight back to the source leaf. Unlike ECN, it skips the forward trip to the destination and back. Unlike PFC, it targets one flow instead of pausing the whole traffic class. The ingress leaf can then forward the signal, or translate it to PFC for the server.
</details>

<details><summary>**16. Where is a Congestion Signaling (CSIG, `draft-ravi-ippm-csig-01`) tag placed in a packet, what are its three sections, and what four fields are in its locator metadata?**</summary>

The CSIG tag sits between the Layer 2 Ethernet header and the Layer 3 IP header. Its three sections are Signal Type, Signal Value and Locator Metadata. The Locator Metadata encodes four fields: the capacity of the bottleneck, its stage, its device ID, and whether the link is an uplink or a downlink.
</details>

<details><summary>**17. On a leaf switch, `swp3` shows `rx_pfc_prio3 = 41,823`, `tx_pfc_prio3 = 41,810`, `rx_ecn_marked_prio3 = 190`, and `queue3_occupancy = 98%`, while `swp7` shows `tx_pfc_prio3 = 0` and `rx_ecn_marked_prio3 = 2,200`. Which port is the relay hop and where does the fix belong?**</summary>

Port `swp3` is a middle relay hop. It receives pause from downstream and passes it upstream. Port `swp7` sits nearest the receiver. It shows heavy receiver-edge congestion, with 2,200 ECN marks and zero transmitted PFC frames. So the fix belongs at the downstream destination bottleneck, not at the middle relay hops.
</details>

<details><summary>**18. Why did SSH management sessions stall during training bursts when `mlnx_qos -i swp12` showed `enabled: 1 0 0 1 0 0 0 0`, and how do you verify the fix?**</summary>

That configuration enabled PFC on Priority 0, which carries default management traffic, alongside Priority 3 for RoCE. Training backpressure could therefore pause management traffic. To fix it, you set `enabled: 0 0 0 1 0 0 0 0`, then run a repeat congestion test. You verify that `rx_pfc_prio0` stays at zero and that SSH latency stays flat.
</details>

<details><summary>**19. Contrast the counter signatures of a healthy DCQCN loop (`swp9` delta 312), a weak RP response (412,880 marks, 98 Gbps), and synchronized oscillation (`100 -> 12 -> 95 -> 11 -> 96 Gbps`).**</summary>

On the healthy contained loop, `swp9` shows `rx_ecn_marked_prio3` rising by 312. The endpoint counters track it, with `np_ecn_marked_roce_packets` at 305 and `np_cnp_handled` at 298, and there is zero PFC. In a weak RP response, `rx_ecn_marked_prio3` reaches 412,880 and `np_cnp_handled` reaches 409,500. Yet `rp_current_rate` stays at 98 Gbps on a 100G link, and PFC forces 93,100 frames. In synchronized oscillation, `rp_current_rate` swings from 100 Gbps down to 12 Gbps and back every second, because the rate cuts are too aggressive and the recovery is too fast.
</details>

<details><summary>**20. In Lab 04, why did `ib_write_bw -d mlx5_1 -i 1 10.20.8.5` drop from 392 Gbps to 156 Gbps with 24 `RETRY_EXC_ERR` completions, and which layer of the evidence ladder caught it?**</summary>

The Layer 1 physical link state and the Layer 2 route and MTU 9000 checks were clean. The Layer 3 RoCE device and GID selection caught the first divergence. Selecting `-d mlx5_1` forced traffic onto the nonpreferred rail `ens1f1`, instead of `mlx5_0` on `ens1f0`. Restoring `-d mlx5_0` returned throughput to 392 Gbps in 2.1 seconds, without touching switch QoS.
</details>

---

## Sources and review notes

### Primary sources read in full for this chapter

All primary textbook and Volume 09 sources mapped to Chapter 12.4 were read in full and verified against the protocol simulator.

```text
Primary Sources & Mapped Files (brief.py 12.4 & check_coverage.py 12.4):
  1. Book Sources (TOON-RAG Corpus):
     - AI Data Center Network Design and Technologies (ai-data-center-network-design-and-technologies), Chapter 7 (ADC 7):
       * 7. RoCEv2 Transport and Congestion Management
       * Figures 7-1..7-6: All 6 Clos congestion points (CP1..CP6)
       * Table 7-1 & Figures 7-7..7-9: ECN bits 00/01/10/11, RoCEv2 UDP port 4791, CNP frame with ECN 01 and IB BTH opcode 129 / 10000001 / 0x81
       * Figures 7-10..7-14: IEEE 802.1Qbb PFC 64 B frame, dst 01:80:c2:00:00:01, src 10:0e:7e:b7:a7:1b, EtherType 0x8808, opcode 0x0101, Class 3 vector 0x0008, 65535 XOFF vs 0 XON
       * Figure 7-15: 3-stage PFC Watchdog (Detection, Mitigation, Restoration)
       * Figures 7-16..7-17: DCQCN threshold ordering XON < ECN < XOFF and 5-step hop-by-hop PFC propagation
       * Figure 7-18: Source Flow Control (SFC, IEEE 802.1Qdw)
       * Figures 7-19..7-21: Congestion Signaling (CSIG, draft-ravi-ippm-csig-01)
     - Cross-checked: bcm11-admin and computer-networking-problems-and-solutions (Chapter 8 QoS/WRED)
  2. Author's Volume 09 Notes and Labs (nvidia-devops):
     - nvidia-zero-to-hero/volume-09/chapter-04-priority-flow-control.md
     - nvidia-zero-to-hero/volume-09/chapter-05-ecn-and-dcqcn.md
     - nvidia-zero-to-hero/volume-09/labs/lab-01-inventory-an-ai-ethernet-path.md
     - nvidia-zero-to-hero/volume-09/labs/lab-02-validate-roce-addressing-and-mtu.md
     - nvidia-zero-to-hero/volume-09/labs/lab-03-observe-pfc-and-ecn-under-load.md
     - nvidia-zero-to-hero/volume-09/labs/lab-04-troubleshoot-a-roce-path.md
     - Also indexed in MIGRATION_MAP.md as:
       * 01-rocev2-and-infiniband-architecture.md
       * lab-01-inspect-and-validate-roce-interfaces.md
       * lab-02-validate-pfc-ecn-and-qos-queues.md
       * lab-03-benchmark-rocev2-and-compare-to-tcp.md
       * lab-04-troubleshoot-a-congested-roce-path.md
```

### Run here

- `python3 code/part12/pfc_ecn_dcqcn_lab.py` (28 passed, 0 failed out of 28 checks).

### Explicitly labelled inferences

- The flight-time headroom comparison of 49,064 B for a 2 m DAC cable versus 298,064 B for a 500 m optical fiber at 400 Gbps applies the standard IEEE 802.1Qbb propagation formula from Chapter 2.19 and `code/part12/pfc_ecn_dcqcn.py`.
- The WRED numerical example with $K_{\min}$ at 150 KB and $K_{\max}$ at 1,500 KB uses the Spectrum-X and ConnectX threshold pair from Volume 06 Chapter 1 to make the Green, Yellow, and Red zones concrete.

### Not verified on live hardware

- None of the `mlnx_qos`, `ethtool -S`, `mlx5_cnp_stats`, `rdma link`, `ibv_devinfo`, or `ib_write_bw` commands in this chapter were executed on live switch or ConnectX hardware. They are marked `(untested here)`. The counter values shown, such as `rx_pfc_prio3=41823` and `rp_current_rate=98Gbps`, are sample figures from the source notes.
