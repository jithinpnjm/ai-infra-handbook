---
id: "c02-19"
title: "2.19 Queuing, QoS, ECN, PFC and DCB: congestion management for AI fabrics"
sidebar_label: "2.19 Queuing, QoS, ECN, PFC and DCB: congestion management for AI fabrics"
sidebar_position: 19
description: "QoS fundamentals, queueing, AQM, ECN, PFC, DCQCN, SFC, CSIG and RoCEv2 congestion management"
status: "drafted"
tier: "2"
level: "A"
lab_venue: "GCP / GKE"
---

# 2.19 Queuing, QoS, ECN, PFC and DCB: congestion management for AI fabrics

| | |
|---|---|
| Level | Advanced |
| Priority tier | 0 |
| Lab venue | Linux VM (`tc`, netem); RoCE parts need hardware (untested here) |
| Part | Part 2: Networking, from first principles to AI fabrics |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

Distributed training sends synchronized bursts at line rate between thousands of NICs. Even in a 1:1 non-oversubscribed fabric, several senders target one receiver port at the same instant (incast), hash collisions put two elephant flows on one link, and a single dropped RoCE packet can stall a whole collective. RoCEv2 relies on a nearly lossless Ethernet, so the discipline of **queueing, classification, ECN marking, Priority Flow Control and DCQCN** is the difference between 95% and 40% of line-rate all-reduce. These are also the topics where interview questions get specific: why PFC can cause head-of-line blocking and storms, why ECN thresholds sit below PFC thresholds, what a PFC watchdog does, and what DSCP/priority a RoCE class should use. This chapter starts with general QoS (why not just add bandwidth, classification, marking, queueing disciplines, AQM) and then covers the data-centre/RoCE congestion toolkit and its configuration.

## Prerequisites and outcomes

You should know TCP congestion control and ECN (2.6), switching internals and buffers (2.11), ECMP/LAG hashing (2.12) and AI-fabric topologies (2.18).

After this chapter you can:

- Explain why QoS is needed even when links are large, the four problems it solves (delay, jitter, loss, bandwidth share), and the difference between classification, marking, policing/shaping and queue scheduling.
- Describe DSCP/IP precedence/802.1p marking, trust boundaries, preserving markings across tunnels, and the "unmarked Internet" problem.
- Explain FIFO, strict priority/low-latency queueing, CBWFQ/DRR/WFQ, overcongestion, policers vs shapers, and Linux `tc` equivalents (`prio`, `htb`, `fq_codel`, `cake`).
- Explain buffer management: tail drop, RED/WRED, bufferbloat, CoDel/PIE, ECN-based AQM.
- Describe congestion points in a Clos fabric and why they arise even at 1:1.
- Explain ECN (bits, marking thresholds, CNP), PFC (pause frames, XON/XOFF, headroom, storms, deadlocks, watchdog), ETS/DCBX, DCQCN, and newer proposals (SFC, CSIG), and how they interact.
- Design and verify a lossless RoCEv2 class (DSCP/priority, buffers, thresholds, trust mode) and troubleshoot PFC/ECN issues with counters.
- Decide when to use ECN-only versus ECN+PFC versus adaptive routing.

## 1. Why QoS exists

If links were infinitely fast, there would be no queues and no QoS. Real networks have bottlenecks: speed changes (100G to 10G), many-to-one fan-in, bursts, and shared uplinks. Queues absorb bursts but add delay; when queues overflow, packets drop. Applications differ: voice and RPC need low delay and jitter, bulk transfers need throughput, RDMA needs (nearly) zero loss, control traffic must always get through. **Quality of Service** is the set of mechanisms that treat traffic classes differently under contention.

**"Why not just buy bigger links?"** Because (1) bursts and fan-in make congestion a statistical certainty even at low average utilisation; (2) bandwidth costs money and takes time, whereas needs change in milliseconds; (3) latency-sensitive packets stuck behind large packets suffer serialization delay no matter how fast the average is (a 9000-byte packet on a 100 Mb/s link occupies it for 0.72 ms; a 64-byte packet queued behind it waits 14 times its own serialization time, which shows up as jitter); (4) *adding capacity moves the bottleneck*, it doesn't remove contention. Overprovisioning reduces the need for QoS but never eliminates it, and some paths (WAN, interconnects, host NICs) cannot be overprovisioned economically. In AI fabrics, overprovisioning (1:1) is the baseline, and the residual contention (incast, hash collisions, microbursts) is handled by congestion control.

## 2. The QoS toolbox

```mermaid
flowchart LR
  A["Classify\n(match fields: DSCP, 802.1p, 5-tuple, interface)"] --> B["Mark\n(set DSCP/PCP/ECN, internal class)"]
  B --> C["Police / shape\n(rate limit; drop/remark vs delay)"]
  C --> D["Queue\n(per-class queues, buffers)"]
  D --> E["Schedule\n(strict priority, WFQ/DRR, shaping)"]
  D --> F["Manage queue length\n(tail drop, WRED, ECN, CoDel)"]
  E --> G["Transmit"]
```

### Classification and marking

**Classification** decides which class a packet belongs to; **marking** records that decision in the packet so downstream devices don't need to repeat deep inspection. Fields:

- **IPv4/IPv6 header**: the 8-bit ToS / Traffic Class byte = **DSCP** (6 bits, 64 values: CS0..CS7, AF11..AF43, EF=46, DF=0) + **ECN** (2 bits). Legacy IP precedence uses the top 3 bits.
- **Ethernet 802.1Q tag**: 3-bit **PCP** (802.1p class of service, 0 to 7) and DEI.
- **MPLS** traffic-class bits (3), **VXLAN/GENEVE** inherit from inner/outer by configuration.
- **Layer 4/application**: ports, protocol (RoCEv2 = UDP 4791), or deep inspection.

Common DSCP behaviours: **EF (46)** low-latency expedited forwarding (voice); **AF** classes (assured forwarding, 4 classes × 3 drop precedences); **CS6/CS7** network control; **CS3/CS4** signalling and streaming; **DF/CS0** best effort. AI fabrics typically define their own plan: e.g. a lossless RoCE data class (commonly DSCP 26 mapped to priority 3), a CNP class (DSCP 48 mapped to a strict-priority or high-weight queue), a control/management class, and best-effort for everything else; the specific numbers are conventions, not standards, and must match on NICs and switches (verify with vendor guides).

**Trust boundaries.** Hosts can mark any DSCP they like, so a network must decide where to *trust* markings (from known servers/switches) and where to *re-mark* (from untrusted tenants, the Internet). **Preserving classification** across tunnels and hops requires explicit mapping: copy inner DSCP to the outer header on encapsulation (VXLAN/GRE/IPsec/MPLS "uniform" vs "pipe" modes), map DSCP ↔ 802.1p at L2/L3 boundaries, and ensure marking survives NAT, proxies and DPUs. **The unmarked Internet:** ISPs usually ignore or rewrite DSCP, so end-to-end QoS across the public Internet is not available; QoS is a *domain* tool, and applications that need quality across the Internet use different means (CDNs, SD-WAN path selection, adaptive codecs, QUIC).

### Policing and shaping

- A **policer** measures a traffic rate (token bucket: committed rate CIR, burst CBS/EBS) and drops or re-marks excess immediately. No buffering; protects a downstream resource or enforces a contract; can cause TCP sawtooth because drops are abrupt.
- A **shaper** buffers excess and releases it at the configured rate: smooths bursts, adds delay, needs buffer. Use to match a slower downstream link or provider rate.
- Both use token buckets; the burst size (bucket depth) matters as much as the rate.

### Queueing and scheduling

Each egress port has several queues (per class), a scheduler that decides which queue sends next, and a buffer-management policy that decides who loses when buffers fill.

- **FIFO / tail drop**: one queue, drops when full; no differentiation; causes global synchronization of TCP flows and unfair loss.
- **Strict priority / low-latency queueing (LLQ)**: a priority queue is always served first; ideal for latency-sensitive classes (voice, CNP, control), but must be **policed** (rate-limited) or it starves all else; used sparingly.
- **Weighted fair queueing** and its class-based variants (**CBWFQ**, **DRR** deficit round robin, WRR): classes get a guaranteed share of the link in proportion to weights; unused share is redistributed (work-conserving). This is the *fairness* tool. In DCB it is standardised as **ETS** (Enhanced Transmission Selection, 802.1Qaz): assign each priority group a bandwidth percentage.
- **Overcongestion**: when more traffic than capacity arrives in *every* class, scheduling alone can't help; guarantee only what you can deliver, and use admission control, policing, and capacity planning.
- **Other tools**: hierarchical QoS (parent shaper with child policies per tenant), per-flow fair queueing (fq_codel, CAKE) for host-level fairness, traffic engineering to move flows, rate limiting of control-plane traffic (CoPP), and application back-off.

### Queue management (AQM)

Dropping only when a buffer is completely full ("tail drop") has two defects: the buffer stays full (high latency) and many TCP flows lose packets simultaneously and back off together. **Active queue management** acts earlier:

- **RED / WRED** (Random Early Detection, weighted): once average queue length exceeds a minimum threshold, drop (or ECN-mark) packets with increasing probability up to a maximum threshold, beyond which all packets are dropped; weights give different thresholds per class or drop precedence. Spreads losses over time and across flows, keeps queues short.
- **Bufferbloat**: oversized buffers combined with loss-based congestion control produce queues of hundreds of milliseconds ("latency under load"). Cure: smaller/adaptive buffers and AQM. **CoDel** (controlled delay) measures packet sojourn time in the queue and starts dropping when the minimum delay over an interval stays above a target (5 ms over 100 ms), self-tuning without per-link parameters; **PIE** is a similar controller; **fq_codel** combines flow queueing with CoDel (Linux default qdisc on many distributions); **CAKE** adds shaping, per-host fairness and DSCP handling.
- **ECN-based AQM**: instead of dropping, mark the packet's ECN bits (CE) at the same thresholds; ECN-capable transports slow down without loss (section 5).

### Linux `tc` quick reference

```bash
tc qdisc show dev eth0 ; tc -s qdisc show dev eth0 ; tc -s class show dev eth0       # state + counters (drops, overlimits, backlog)
tc qdisc replace dev eth0 root fq_codel                       # per-flow fair queueing + CoDel (good default)
tc qdisc replace dev eth0 root cake bandwidth 900mbit         # shaper + AQM (home/edge)
tc qdisc add dev eth0 root handle 1: htb default 30
tc class add dev eth0 parent 1: classid 1:1 htb rate 10gbit
tc class add dev eth0 parent 1:1 classid 1:10 htb rate 2gbit ceil 10gbit prio 0       # priority class
tc class add dev eth0 parent 1:1 classid 1:30 htb rate 8gbit ceil 10gbit prio 1
tc filter add dev eth0 parent 1: protocol ip prio 1 u32 match ip dscp 0x2e 0xfc flowid 1:10   # EF -> class 1:10
tc qdisc add dev eth0 parent 1:30 fq_codel
tc qdisc add dev eth0 root tbf rate 100mbit burst 32kbit latency 50ms                 # shaper (token bucket)
tc qdisc add dev eth0 root netem delay 20ms 5ms loss 0.1% rate 1gbit                 # emulate a bad link
tc qdisc add dev eth0 root red limit 400000 min 30000 max 90000 avpkt 1000 burst 55 ecn bandwidth 10gbit   # RED with ECN marking
```

Linux NICs also have hardware queues (`ethtool -l`), driver rings (`ethtool -g`), BQL (byte queue limits) and DCB/PFC controls on supported NICs (`dcb` tool in iproute2, `lldptool`, vendor tools such as `mlnx_qos`).

## 3. Data-centre congestion points

In a Clos with line-rate servers, congestion can occur at several places even at 1:1:

| Point | Cause |
|---|---|
| **Leaf downlink (leaf → server)** | Incast: many senders to one receiver exceed the receiver's NIC bandwidth |
| **Local leaf switching** | Two servers on one leaf sending to a third on the same leaf (no load balancing involved) |
| **Leaf → spine uplink** | Hash collisions put several elephant flows on one uplink while others are idle |
| **Spine → leaf downlink** | Flows from several leaves hash to the same spine, which sends them to one destination leaf over one link |
| **Spine ↔ super-spine** | Same effects one tier up, plus oversubscription |
| **Microbursts** | Sub-millisecond bursts exceed buffer; invisible to average counters |

Load balancing improvements (packet spraying, dynamic and global load balancing, adaptive routing, chapter 2.12, 2.16) reduce hash-collision congestion but do not remove incast or local congestion, so congestion *control* is still needed. Congestion control choices differ by transport: TCP uses window/rate-based algorithms (chapter 2.6); RoCEv2 (RDMA over UDP, destination port 4791) has no TCP; it needs the network and NIC to provide near-lossless delivery. Ethernet by default is lossy, hence the combination of ECN, PFC and DCQCN.

## 4. RoCEv2 and why it needs lossless behaviour

RoCEv2 encapsulates InfiniBand transport (BTH header, queue pairs, opcodes) in UDP/IP/Ethernet. The NIC implements reliability: sequence numbers, ACK/NAK, retransmission. Classic RoCE NICs use **go-back-N** recovery: one lost packet forces retransmission of everything after it, which is catastrophic at 400 Gb/s (and stalls the QP). Newer NICs add selective repeat and out-of-order handling, but vendors still recommend (near-)lossless fabrics for performance. RoCEv2 does not engage the host CPU, which is why it scales far better than TCP for collectives, but its flows have poor ECMP entropy (few long-lived flows with one UDP source port per QP) and bursty, synchronized behaviour. Net effect: the fabric must (a) avoid loss, via PFC or very reliable congestion control; (b) signal congestion early (ECN) so senders slow down before buffers overflow; (c) load balance well.

## 5. ECN and CNPs

**ECN (Explicit Congestion Notification)** lets a congested switch *mark* a packet instead of dropping it. It uses the low two bits of the IP ToS byte:

| ECT | CE | Meaning |
|---|---|---|
| 0 | 0 | Not ECN-capable; congestion causes a drop |
| 0 | 1 | ECT(1): ECN-capable (treated like 10 by most) |
| 1 | 0 | ECT(0): ECN-capable transport; set by the sender |
| 1 | 1 | **CE**: Congestion Experienced (set by a switch) |

Operation in RoCEv2 (end-to-end, sender-switch-receiver):

1. The sender marks packets ECT(0).
2. A switch whose egress queue exceeds the **ECN threshold** marks packets CE (the path doesn't change; no packet lost). Between a minimum and maximum threshold the marking probability ramps up (WRED-style: Kmin, Kmax, Pmax); above Kmax all packets are marked.
3. The receiver sees CE-marked packets and sends a **Congestion Notification Packet (CNP)** back to the sender: a RoCEv2 packet (BTH opcode 0x81 = 129) carrying the QP to identify the flow, typically sent in a high-priority class and rate-limited (e.g. at most one per N microseconds per flow).
4. On receiving CNPs the sender **reduces its rate** for that QP; absence of CNPs makes it recover rate (additive/multiplicative increase).

ECN must be enabled end to end: on the sending NIC, every transit switch, and the receiving NIC; any device that doesn't mark or drops ECN bits breaks the loop. ECN is *flow-granular* (only the QPs causing congestion are slowed) but **slow**: the marked packet has to reach the receiver and the CNP return before the sender reacts (a round trip plus NIC processing); in the meantime, queues can keep growing and overflow. So an ECN-only queue is **lossy** (packets can still drop if the burst outruns the control loop).

Threshold tuning: thresholds are in bytes or cells of queue occupancy (per queue, per port, or shared-buffer based). Too low: needless throttling; too high: ECN reacts too late and the buffer overflows (or PFC fires). Dynamic thresholds exist in some products.

## 6. PFC: lossless links by backpressure

**Priority Flow Control** (IEEE 802.1Qbb) is per-priority pause. A congested receiver sends a **PFC pause frame** (MAC control frame, EtherType 0x8808, opcode 0x0101, destination 01:80:C2:00:00:01) upstream; it carries a *class-enable vector* (which of the 8 priorities) and a 16-bit pause time per priority (units of 512 bit-times; 65535 is the maximum; 0 means resume). The upstream sender stops transmitting that **priority** (not the whole link) for the pause time.

```mermaid
sequenceDiagram
  participant S as Sender / upstream switch
  participant R as Receiving switch (ingress buffer)
  Note over R: queue for priority 3 fills past XOFF threshold
  R->>S: PFC pause (priority 3, time=65535 quanta)
  Note over S: stops sending priority 3, other priorities continue
  Note over R: buffer drains below XON threshold
  R->>S: PFC pause with time=0 (resume)
  Note over S: resumes sending priority 3
```

- **XOFF** is the occupancy at which a pause is sent; **XON** (lower) is where resume is sent (hysteresis avoids oscillation). Between XOFF being crossed and the sender actually stopping, packets keep arriving (propagation delay + the time to process the frame + packets already in flight), so the switch must reserve **headroom** above XOFF to absorb them: headroom ≈ 2 × (propagation delay × bandwidth) + MTU-sized packets in flight at each end + pause processing time. Longer cables (500 m optics) need much more headroom; buffer budgeting per lossless priority and per port is a core design step.
- A queue with PFC enabled is a **lossless queue**; the rest remain lossy. Only one or two classes should be lossless (RoCE data, sometimes storage) so that buffers aren't exhausted.
- The pause propagates hop by hop toward the source: switch → upstream switch → … → the sending NIC, which stops the flows in that priority.

### The problems with PFC

1. **Class-level, not flow-level**: pausing a priority stops *every* flow in it, including innocent ones sharing the link: **head-of-line blocking and unfairness**. A victim flow to an idle destination stalls because it shares a class with congested flows.
2. **PFC storms**: a faulty NIC/port that continuously sends pauses (stuck receiver, firmware bug, broken endpoint) pushes backpressure upstream; every upstream queue fills and pauses its own upstream; congestion spreads across the entire fabric (**congestion spreading**) and the network can freeze.
3. **PFC deadlock**: in topologies with cyclic buffer dependencies (loops caused by failures, routing misconfiguration, or non-up-down paths), switches pause each other in a cycle and none can drain; traffic stops even though no link is actually congested. Prevent with loop-free (Clos up-down) routing, avoiding PFC over rerouted paths, TTL/lossless-class rules, and watchdogs.
4. **Operational fragility**: misconfigured priorities (a mismatch between NIC and switch) make traffic fall into a lossy queue unexpectedly (silent drops), or make pause frames useless.

### PFC watchdog

The **PFC watchdog** (also called PFC storm prevention) has three steps:

1. **Detection**: monitor each port/queue; if a lossless queue stays paused (or keeps receiving pause frames) beyond a configured interval (e.g. 100 ms to 200 ms), declare a storm.
2. **Mitigation**: either **drop** (flush the queue, discard new packets for that queue and ignore/drop incoming pause frames so the stall doesn't propagate) or **forward** (ignore pause frames and keep transmitting). Dropping is the most common.
3. **Restoration**: when pause frames fall below a threshold for a restoration interval, re-enable normal lossless behaviour.

The watchdog trades losing some packets for keeping the rest of the fabric alive; the application (RoCE retransmission or job restart) sees the loss. Alert on watchdog triggers: each one is a fabric-level incident marker.

## 7. DCQCN: ECN and PFC together

**DCQCN** (Data Center Quantized Congestion Notification; Microsoft/Mellanox, SIGCOMM 2015) is the standard congestion control for RoCEv2. It combines:

- **ECN** as the primary, early, flow-level signal (switch marking → receiver CNP → sender rate reduction, using a quantized, QCN-style rate decrease and multi-stage rate recovery on the NIC), and
- **PFC** as the last-resort safety net to prevent loss if queues rise further.

The thresholds are ordered in the queue: **XON < ECN (Kmin/Kmax) < XOFF**. ECN marking starts well before PFC so that senders slow down first; only when congestion worsens faster than ECN can respond does the buffer cross XOFF and PFC pauses the priority. If ECN resolves the congestion, other flows in the queue are unaffected; PFC fires rarely, so its side effects stay rare. If PFC triggers frequently, it harms throughput; in some fabrics it is configured only on leaves and NICs, in others on all nodes; some deployments run **ECN-only** (no PFC) with excellent load balancing and rely on NIC loss recovery, especially with newer NICs that tolerate loss. The right answer depends on the SLA, hardware and measurements.

NIC-side parameters (vendor-specific): initial rate, rate-increase timers and steps, alpha update gain, rate-decrease factor, CNP generation interval (e.g. 50 µs), minimum time between CNPs, ECN marking trust (DSCP), CNP priority/DSCP. Misconfigured NIC parameters are a classic reason for poor performance with a correct switch configuration.

## 8. Newer mechanisms: SFC and CSIG

- **Source Flow Control (SFC)**, being specified as an IETF/IEEE-style standard (802.1Qdw "source PFC"): instead of pausing hop by hop, a congested switch sends the signal **directly to the source** by trimming the packet payload and reversing the source/destination addresses; the first-hop leaf can pause the flow's queue, forward the signal to the NIC if supported, or translate it into PFC. Advantages: no ECN's long loop (the signal does not travel to the receiver and back), and **flow-level** rather than class-level action, avoiding head-of-line blocking.
- **Congestion Signaling (CSIG)**: an emerging in-band mechanism where each hop updates a small tag in the data packet (signal type such as minimum available bandwidth ratio or maximum path delay, a quantized value, and locator metadata: capacity of the bottleneck, stage, device ID, uplink/downlink), the receiver reflects the aggregated signal to the sender, and senders get path-aware, multi-bit congestion information rather than the single ECN bit. It can feed rate control and adaptive routing decisions.
- **Related**: Ultra Ethernet Consortium transport (packet spraying, selective retransmission, new congestion control), in-band network telemetry (INT) and trimming, credit-based or receiver-driven schemes (NDP, HPCC using INT), switch-level adaptive routing/packet spraying, and fabric-wide VOQ (scheduled fabrics, chapter 2.18).

Treat SFC and CSIG as in-progress standards; know the ideas and the problem each solves.

## 9. DCB: the Ethernet toolbox

**Data Center Bridging** is the IEEE bundle that makes Ethernet suitable for storage and RDMA:

| Standard | Name | Purpose |
|---|---|---|
| 802.1Qbb | PFC | Per-priority pause (lossless classes) |
| 802.1Qaz | ETS | Bandwidth allocation per priority group |
| 802.1Qaz | DCBX | Exchange and negotiation of DCB settings (PFC, ETS, application priority) over LLDP |
| 802.1Qau | QCN | Layer-2 congestion notification (rarely deployed; DCQCN uses ECN instead) |
| 802.1Qdw | SFC/source PFC | See above |

Apply as: define 8 priorities; assign traffic types to priorities by DSCP/PCP/port; mark which priorities are lossless (PFC enabled); set ETS weights; enable DCBX willing/non-willing modes consistently, or disable DCBX and push configuration explicitly via automation (common in AI clusters to avoid surprises).

## 10. Configuring a lossless RoCE class (conceptual, verify per vendor)

Pieces to configure and keep consistent from NIC to NIC across all switches:

1. **Classification**: trust DSCP at the host-facing and switch-to-switch ports; map DSCP 26 (RoCE data) → internal class / priority 3; map CNP DSCP (e.g. 48) → priority 6 (strict priority or high weight); everything else → default.
2. **Queues and scheduling**: a lossless queue for priority 3 with ETS weight (e.g. 50 to 90%); CNP queue strict priority with a small rate cap; default queue for the rest.
3. **PFC**: enabled only on priority 3, with correct headroom, XOFF and XON for the port speed and cable length; PFC watchdog on with sensible intervals.
4. **ECN**: ECN marking on priority 3's queue with Kmin/Kmax/Pmax (for example, Kmin = a few hundred KB, Kmax = a few MB at 400G; tune with measurements); ensure the switch preserves the ECN bits.
5. **NIC**: trust DSCP; set the RoCE traffic class/ToS for the QP (e.g. `NCCL_IB_TC`/`NCCL_IB_SL` environment, `cma_roce_tos` or `rdma_cm` settings); enable DCQCN and set parameters; enable PFC for the same priority; keep MTU and RoCE MTU consistent (e.g. 9000 Ethernet, RoCE MTU 4096).
6. **Verification**: send traffic with `ib_write_bw`, `nccl-tests all_reduce_perf`, watch counters: PFC pause frames sent/received per priority, ECN-marked packets, CNPs sent/handled, buffer watermarks, queue drops (must be 0 on the lossless class), out-of-sequence/retransmit counters on the NIC (`ethtool -S`, `rdma statistic`, `mlnx_qos`, vendor telemetry).

```bash
# Host side (NVIDIA ConnectX example; verify tool names and versions in the NIC documentation)
mlnx_qos -i eth2                                   # show trust mode, PFC, ETS
sudo mlnx_qos -i eth2 --trust dscp --pfc 0,0,0,1,0,0,0,0      # lossless on priority 3
ethtool -S eth2 | egrep 'prio3_pause|rx_prio3_pause|tx_prio3_pause|ecn_marked|np_cnp_sent|rp_cnp_handled|out_of_sequence|rx_discards'
rdma statistic show                                # per-device counters (NP/RP CNP, retransmissions)
dcb pfc show dev eth2 ; dcb ets show dev eth2 ; dcb app show dev eth2    # iproute2 dcb tool
ip -s link show eth2 ; ethtool -g eth2             # drops, ring sizes
# Fabric side (SONiC-style examples)
show pfc counters ; show queue counters ; show priority-group watermark headroom ; show pfcwd stats
```

Treat these as pointers; the exact commands, DSCP values and threshold numbers vary by vendor, ASIC and firmware, and must be taken from the validated design guide for your hardware.

## 11. Troubleshooting congestion in AI fabrics

```mermaid
flowchart TD
  S["Low collective bandwidth / long step time"] --> A{"Any drops on lossless class?"}
  A -- "yes" --> A1["PFC/headroom/ECN mismatch; priority mismatch NIC↔switch; watchdog fired; wrong DSCP mapping"]
  A -- "no" --> B{"PFC pause counters high?"}
  B -- "yes" --> B1["Congestion → PFC: lower ECN thresholds, check load balancing, find the incast victim; storm? find the source port; deadlock?"]
  B -- "no" --> C{"ECN marks / CNPs high?"}
  C -- "yes" --> C1["Congestion handled by DCQCN but constant: hot links, hash collisions, oversubscription; improve LB, check ECMP imbalance"]
  C -- "no" --> D{"Link/NIC errors, MTU, speed?"}
  D -- "yes" --> D1["Optics/CRC errors, degraded link speed, MTU mismatch, wrong lane count"]
  D -- "no" --> E["Software/topology: NCCL config (HCA, GID, TC), CPU/NUMA/PCIe, rail mismatch, slow node (stragglers)"]
```

Practical hints: look for the *straggler* (one slow node or link can slow the whole job); compare per-port counters across identical ports (outlier = bad cable/optic); correlate PFC bursts with job phases; confirm ECN is actually marking (counter increments) before tuning thresholds; check that **CNP packets are not themselves queued behind data**; verify DSCP end to end with a capture on the NIC and switch (`tcpdump` shows DSCP/ECN bits; Wireshark decodes BTH opcodes); run `nccl-tests` per rail and across rails to localise; verify `rp_filter`/routing for the RoCE subnets (chapter 2.5).

## 12. Hands-on lab: queueing, AQM, and ECN with Linux

First, run the self-checking Python lab (`code/part02/qos_ecn_pfc_dcqcn_lab.py`) locally. It verifies IP ToS byte (`6`-bit `DSCP` + `2`-bit `ECN`) encoding/decoding (`0x6a` -> `0x6b` on `CE`), DCQCN threshold ordering (`XON < Kmin < Kmax < XOFF`) and linear WRED/ECN marking probability, and PFC headroom buffer growth on `500 m` vs `10 m` `400G` optical links.

```bash
python3 code/part02/qos_ecn_pfc_dcqcn_lab.py
```

Next, on a disposable Linux VM (and optional RoCE NIC/switch hardware for Step 8; all interactive VM commands below are `untested here`), work through these steps:

1. **Bufferbloat**: two namespaces joined by a veth pair; limit rate with `tbf`/`netem rate 50mbit`; run a bulk `iperf3` and a `ping` simultaneously; record latency; replace the qdisc with `fq_codel` or `cake` and compare.
2. **Priority and fairness**: `htb` with a high-priority class for DSCP EF and a bulk class; show a latency flow staying low during saturation; remove the policing on the priority class and show starvation; try `drr`/`wrr` weights.
3. **Policer vs shaper**: `tc filter ... police rate 10mbit burst 10k drop` vs `tbf`; observe TCP throughput sawtooth and drops vs delay.
4. **RED/ECN**: `tc qdisc add ... red ecn` with thresholds; run `iperf3` with `sysctl net.ipv4.tcp_ecn=1`; read `tc -s qdisc` marks vs drops; compare ECN on/off for latency and throughput; try DCTCP (`sysctl net.ipv4.tcp_congestion_control=dctcp`, ECN threshold marking with a very low K) as the TCP analogue of DCQCN.
5. **Incast**: N sender namespaces sending synchronized bursts to one receiver through a small-buffer bridge; measure goodput versus N; add ECN and DCTCP; observe collapse and recovery.
6. **Microburst visibility**: sample queue depth at 1 ms intervals with `tc -s` in a loop or an eBPF tool (`bpftrace` on `qdisc` tracepoints) while sending a burst; show that the 1 s average hides it.
7. **DSCP preservation**: create a VXLAN tunnel (chapter 2.17) and show DSCP copying (`tos inherit`) and the effect on the underlay queue assignment.
8. **Hardware lab (optional)**: with two RoCE-capable NICs and an Ethernet switch (or a SONiC-VS/virtual switch for config practice), configure trust-DSCP, a lossless priority, PFC and ECN; run `ib_write_bw` with competing traffic; read PFC/ECN/CNP counters; trigger a PFC watchdog event by pausing a receiver.
9. **Clean up.**

## 13. Design guidance for AI back-ends

- Prefer **1:1** with good load balancing (adaptive/dynamic/global LB or packet spraying) so congestion is rare; treat congestion control as the safety net.
- Use **ECN with DCQCN as the primary control**; add **PFC** on the RoCE class only where the NIC/transport needs it; always run the **PFC watchdog**; keep the lossless class count at one or two.
- Size **headroom** and buffers for the longest cable; keep ECN thresholds below XOFF; validate with incast tests at the target scale.
- Give **CNPs** a high-priority path so feedback isn't delayed by the congestion it reports.
- Monitor continuously: PFC pause durations/rates, ECN marks, CNPs, queue watermarks, drops on lossless classes (should be zero), watchdog events, link errors; set alerts on trends, not only thresholds.
- Document the DSCP/priority plan and enforce it by automation (NIC and switch templates generated from one source of truth) with continuous compliance checks (chapters 2.28, 2.29).
- When PFC fires often in a given design, prefer fixing the cause (load balancing, topology, incast shaping at the job level) over adding more PFC tuning; in some designs an ECN-only fabric with better LB and loss-tolerant NICs outperforms an ECN+PFC fabric.

## 14. Common mistakes

- Treating QoS as bandwidth guarantees without admission control; strict priority without a policer.
- Trusting host-set DSCP from untrusted tenants; DSCP lost on tunnels/NAT; DSCP/priority mismatch NIC vs switch.
- Enabling PFC on many classes or across the whole cluster without headroom/watchdog; no deadlock analysis for rerouted paths.
- ECN thresholds above PFC thresholds (ECN never fires first); thresholds copied from another speed/cable length.
- Judging fabric health from average utilisation (microbursts hidden).
- Forgetting CNP handling and NIC DCQCN parameters.
- Not testing failure cases (link down → rerouted loops → PFC deadlock).

## 15. Interview angles

- "Why can't you fix congestion by just adding bandwidth?"
- "Explain classification, marking, policing, shaping, queueing and scheduling."
- "LLQ vs CBWFQ; when does strict priority starve others?"
- "What is bufferbloat and how does CoDel work?"
- "How does ECN work end to end in RoCEv2? What is a CNP?"
- "Explain PFC. What are XON/XOFF and headroom? What problems does PFC cause? What is a PFC storm / deadlock / watchdog?"
- "What is DCQCN? Why must ECN threshold be lower than PFC threshold?"
- "How do SFC and CSIG improve on ECN and PFC?"
- "A training job is slow; how would you tell whether it's congestion, a bad link or software?"
- "Where do you enable PFC in a leaf-spine fabric and why?"

## Exercises

1. **Why More Bandwidth Does Not Eliminate QoS, Classification/Marking, Trust Boundaries, and the Unmarked Internet (`CN` Chapter 8):** (a) Give four reasons why simply buying faster links does not eliminate the need for QoS; (b) using `encode_decode_ip_tos_byte()` in `code/part02/qos_ecn_pfc_dcqcn.py`, encode `DSCP = 26` (RoCE data) with `ECN = 2` (`ECT(0)`) and `ECN = 3` (`CE`), plus `DSCP = 48` (`CS6` for CNPs), and explain trust boundaries, tunnel DSCP preservation, and why the public Internet is "unmarked".
2. **Policing vs. Shaping, `LLQ` vs. `CBWFQ`/`ETS`, and Active Queue Management (`WRED` and `CoDel`):** (a) Contrast a token-bucket **policer** with a **shaper**, and contrast **Strict Priority (`LLQ`)** with **Weighted Fair Queueing (`CBWFQ` / `DRR` / `ETS` `802.1Qaz`)**; (b) explain why tail drop causes global TCP synchronization and bufferbloat, and compare **WRED** with **CoDel** (`RFC 8290`, `5 ms` target sojourn delay over `100 ms`).
3. **Clos Congestion Points and End-to-End `ECN` + `CNP` in RoCEv2 (`ADC` Chapter 7):** List the six congestion points in a 3-/5-stage Clos fabric (even at `1:1` non-oversubscribed), and trace the 4-step end-to-end **ECN + CNP** feedback loop in RoCEv2 (`UDP 4791`, `ECT(0)` -> switch `CE` mark -> receiver **CNP** `BTH opcode 0x81` -> sender QP rate cut). Why is an ECN-only queue still considered lossy?
4. **`PFC` (`802.1Qbb`), `XON`/`XOFF`, Headroom Math, and `PFC` Storms / Deadlocks / Watchdog:** (a) Describe the IEEE `802.1Qbb` PFC pause frame (`EtherType 0x8808`, opcode `0x0101`, destination `01:80:C2:00:00:01`, `65535` quanta of `512` bit-times), and use `compute_pfc_headroom_bytes()` to compare the headroom buffer required at `400 Gb/s` for a `10 m` DAC/AOC cable versus a `500 m` optical cable; (b) explain the three hazards of PFC (**class-level Head-of-Line blocking**, **PFC pause storms**, and **cyclic PFC deadlocks**) and the three stages of the **PFC watchdog** (`100–200 ms`).
5. **`DCQCN` Threshold Ordering (`XON < ECN < XOFF`), `SFC` (`802.1Qdw`), and `CSIG`:** (a) Using `evaluate_dcqcn_queue_action()` with `XON = 50 KB, Kmin = 100 KB, Kmax = 500 KB, Pmax = 0.20, XOFF = 1000 KB`, compute the ECN marking probability and PFC state at queue depths `30 KB`, `300 KB`, `600 KB`, and `1100 KB`, and explain why `ECN` thresholds must sit strictly below `XOFF`; (b) explain how **Source Flow Control (`SFC`, `802.1Qdw`)** and **Congestion Signaling (`CSIG`)** improve on ECN and PFC.
6. **Configuring and Troubleshooting a Lossless RoCEv2 Class (`mlnx_qos`, `ethtool -S`, and SONiC):** Write the 6-step end-to-end checklist for configuring a lossless RoCEv2 priority (`DSCP 26 -> priority 3`, `CNP DSCP 48 -> priority 6`) across ConnectX NICs and switches, and walk through the Section 11 diagnostic flowchart when a distributed training job suffers low collective bandwidth.

## Checkpoint questions (20)

<details>
<summary>1. Give four reasons why \"just adding more bandwidth\" does not eliminate the need for QoS (`CN` Chapter 8).</summary>

(1) **Synchronized fan-in and microbursts** make momentary queue build-up a statistical certainty even when 1-minute average link utilization is low;\n(2) **Serialization delay and jitter**: a `9,000`-byte jumbo packet on a `100 Mb/s` link occupies the wire for `0.72 ms`, forcing a `64`-byte (`0.05 ms`) latency-sensitive packet behind it to wait `14x` its own transmission time;\n(3) **Adding bandwidth at one link simply shifts the bottleneck** to the next downstream hop or receiver NIC; and\n(4) **Economic/physical limits** on WAN, inter-pod, and host PCIe/NIC links.
</details>

<details>
<summary>2. How are the 8 bits of the IPv4 `ToS` / IPv6 `Traffic Class` byte divided between `DSCP` and `ECN`, and how does `DSCP` relate to Ethernet `802.1p` `PCP`?</summary>

The **upper 6 bits** are the **DSCP (*Differentiated Services Code Point*, `RFC 2474`)** (`0..63`, including Class Selectors `CS0`–`CS7`, Assured Forwarding `AF11`–`AF43`, and Expedited Forwarding **`EF = 46`** `RFC 3246`), and the **lower 2 bits** are **ECN (*Explicit Congestion Notification*, `RFC 3168`)**. At Layer 2 inside an `802.1Q` VLAN tag, **`PCP` (*Priority Code Point*, `802.1p`)** is **3 bits (`0..7`)**. Switches and NICs map 6-bit L3 DSCP values to 3-bit L2 priorities (for example, mapping RoCE data **`DSCP 26` -> Priority `3`** and RoCE CNPs **`DSCP 48` -> Priority `6`**).
</details>

<details>
<summary>3. What is a QoS \"trust boundary\", how are markings preserved across VXLAN tunnels, and why is the public Internet called \"the unmarked Internet\" (`CN` Chapter 8)?</summary>

Because any host or container can set arbitrary DSCP bits, a **trust boundary** is the first trusted switch/DPU port that either accepts DSCP markings (from managed cluster nodes) or **re-marks/classifiers** packets from untrusted tenants. Across VXLAN/GRE/IPsec tunnels, the encapsulating VTEP must copy the inner DSCP (and ECN) bits to the outer IP header (`uniform` / `tos inherit` mode) so underlay switches schedule the packet into the right queue. On the **public Internet**, ISPs bleach (`0`) or rewrite DSCP at peering boundaries because there is no cross-provider settlement for QoS classes.
</details>

<details>
<summary>4. Contrast Traffic Policing and Traffic Shaping.</summary>

Both measure traffic against a **token bucket (`CIR` rate + `CBS` burst size)**:\n- A **Policer** has **no buffer**: packets exceeding the token bucket are **immediately dropped** (or remarked down), which adds zero queueing delay but can cause sharp TCP retransmission sawtooths.\n- A **Shaper** **buffers** excess packets in a queue and clocks them out smoothly at the target rate—smoothing bursts and avoiding drops at the cost of added queueing latency and memory.
</details>

<details>
<summary>5. Compare Strict Priority (`LLQ`) with Weighted Fair Queueing (`CBWFQ`, `DRR`, and DCB `ETS` `802.1Qaz`), and state the danger of unpoliced Strict Priority.</summary>

**Strict Priority (`LLQ`)** always services the high-priority queue first as long as it has a single packet—minimizing latency and jitter for critical traffic (voice, routing keepalives, RoCE **CNPs**), but if the strict-priority class is not **policed/rate-capped**, a burst in that class **completely starves all lower-priority queues**. **Weighted Fair Queueing (`CBWFQ` / `DRR` / IEEE `802.1Qaz` `ETS` *Enhanced Transmission Selection*)** divides link bandwidth proportionally across priority groups according to configured percentage weights while redistributing unused bandwidth (work-conserving).
</details>

<details>
<summary>6. What is \"tail drop\", how does `WRED` improve on it, and how does `CoDel` (`RFC 8290`) solve bufferbloat?</summary>

Under **tail drop**, a queue accepts packets until 100% full and then drops all arriving packets—keeping buffers permanently full (**bufferbloat**, adding hundreds of milliseconds of latency) and causing all competing TCP flows to drop and back off simultaneously (**global synchronization**). **WRED (*Weighted Random Early Detection*)** drops (or ECN-marks) packets probabilistically with linearly increasing probability between a minimum queue depth (`Kmin`) and maximum depth (`Kmax`). **CoDel (*Controlled Delay*, `RFC 8290`)** measures each packet's **sojourn time** (time spent waiting in the queue) rather than byte count and begins dropping/marking when the minimum sojourn delay over a `100 ms` window exceeds a **`5 ms` target** (`fq_codel` pairs this with per-flow fair queues).
</details>

<details>
<summary>7. Name the six congestion points in a 3-stage or 5-stage leaf-spine AI fabric (`ADC` Chapter 7).</summary>

Even when leaf-to-spine bandwidth is provisioned at `1:1`:\n(1) **Leaf downlink (`leaf -> server`)**: many-to-one **incast** (several senders transmitting to one receiver NIC simultaneously);\n(2) **Local intra-leaf switching**: two servers on Leaf A sending to a third server on Leaf A;\n(3) **Leaf-to-spine uplink (`leaf -> spine`)**: ECMP hash collisions placing two 400G elephant flows onto the same uplink;\n(4) **Spine-to-leaf downlink (`spine -> leaf`)**: flows from different leaves hashing through the same spine toward the same destination leaf;\n(5) **Spine-to-super-spine links** (compounded by `2:1` or `4:1` oversubscription); and\n(6) **Sub-millisecond microbursts** at collective barriers.
</details>

<details>
<summary>8. Why does classic `RoCEv2` (`UDP port 4791`) suffer severe throughput collapse on packet loss?</summary>

RoCEv2 implements transport reliability directly in NIC hardware (`Queue Pairs`) without host CPU involvement. Classic RoCE NICs use a tiny reorder window and **go-back-N recovery**: a single dropped packet out of a multi-megabyte burst forces the sending NIC to rewind and retransmit the lost packet **plus every subsequent packet already sent in flight**, stalling the entire collective barrier across all GPUs.
</details>

<details>
<summary>9. Trace the four steps of `ECN` + `CNP` congestion notification in `RoCEv2` (`ADC` Chapter 7).</summary>

(1) The sending RoCE NIC marks outgoing IP headers with **`ECT(0)` (`ECN = 10b`)**;\n(2) When a transit switch's egress queue depth crosses its **`ECN` threshold (`Kmin..Kmax`)**, the switch rewrites the packet's ECN bits to **`CE` (*Congestion Experienced*, `11b`)** and forwards it without dropping;\n(3) The receiving RoCE NIC detects the `CE` mark and generates a **Congestion Notification Packet (`CNP`, RoCEv2 `BTH opcode 0x81 = 129`)** addressed back to the sender, identifying the congested Queue Pair (`QP`) and marked with high priority (`DSCP 48`);\n(4) Upon receiving the `CNP`, the sending NIC **throttles the injection rate of that specific `QP`** (and gradually recovers rate via timers/byte counters once CNPs stop).
</details>

<details>
<summary>10. Why is an `ECN`-only queue still considered \"lossy\", and why must `CNP` packets be placed in a strict-priority / high-weight queue?</summary>

Because ECN is an **end-to-end feedback loop**: a `CE`-marked packet must travel all the way from the congested switch to the receiver, and the resulting `CNP` must travel all the way back to the sender before the sender slows down (`>= 1 RTT` delay). During a sudden many-to-one incast burst at `400 Gb/s`, the switch buffer can overflow and drop packets before the sender ever receives the `CNP`. If `CNP` packets themselves were queued behind congested bulk data on the return path, the feedback signal would be delayed even further—so `CNP`s (`DSCP 48`) are mapped to a dedicated high-priority queue (`Priority 6`).
</details>

<details>
<summary>11. How does IEEE `802.1Qbb` Priority Flow Control (`PFC`) work on the wire (`EtherType`, `opcode`, destination MAC, quanta, `XOFF`/`XON`)?</summary>

When a receiving switch's (or NIC's) ingress buffer for lossless priority `P` (`0..7`, typically `P = 3`) fills past its **`XOFF` threshold**, it transmits an L2 **PFC Pause Frame** (**`EtherType 0x8808`**, **`opcode 0x0101`**, link-local multicast destination **`01:80:C2:00:00:01`**) directly to the upstream neighbor on that link. The frame contains an 8-bit class-enable vector and eight 16-bit pause timers in units of **`512` bit-times** (`65535` = max pause). The upstream neighbor immediately stops transmitting **only Priority `P`** while other priorities (`0..2, 4..7`) continue flowing; when the receiver's buffer drains below **`XON`**, it sends a PFC frame with `time = 0` to resume.
</details>

<details>
<summary>12. What is `PFC Headroom`, and why does a `500 m` optical link at `400 Gb/s` require much more headroom buffer than a `10 m` link?</summary>

Between the instant a receiver crosses `XOFF` and the instant the upstream sender actually stops transmitting, packets are still in flight on the fiber in both directions: the `XOFF` pause frame takes 1 one-way propagation delay (`~5 ns/m`) to reach the sender, the sender takes reaction time + 1 MTU serialization to stop, and the data bits already put on the wire take another 1 one-way propagation delay to arrive. **PFC Headroom** is the dedicated buffer space reserved **above `XOFF`** to absorb all of those in-flight bytes without dropping (`headroom >= 2 * propagation_delay * bandwidth + 2 * MTU + reaction_bytes`). At `400 Gb/s` (`50 bytes/ns`), `500 m` of fiber (`5,000 ns` RTT) has `250 KB` of data in flight on the glass alone.
</details>

<details>
<summary>13. Explain the three major failure modes of `PFC`: Head-of-Line Blocking, `PFC` Storms (Congestion Spreading), and `PFC` Deadlocks.</summary>

(1) **Class-level Head-of-Line (`HOL`) blocking**: PFC pauses an entire **priority class (`0..7`)** on a link, not an individual flow/QP—so an innocent flow on Priority 3 heading to an idle destination is stalled simply because it shares a link with a flow heading to a congested port.\n(2) **PFC Storms & Congestion Spreading**: a wedged NIC or firmware bug that continuously emits `XOFF` pause frames freezes the leaf port, which fills the leaf's ingress buffer and causes the leaf to pause all spines, spreading backpressure across the entire cluster.\n(3) **PFC Deadlock**: if routing transients, link failures, or non-Clos topologies create a **cyclic buffer dependency** (`Switch A pauses B -> B pauses C -> C pauses A`), every switch in the cycle waits on the next and traffic halts permanently.
</details>

<details>
<summary>14. What are the three stages of a `PFC Watchdog`?</summary>

(1) **Detection**: monitors each lossless queue; if a queue remains paused (unable to drain or continuously receiving `XOFF` frames) for longer than the watchdog timer (typically **`100` to `200 ms`**), it declares a PFC storm/hang;\n(2) **Mitigation**: switches the stuck queue into **drop mode** (flushing queued packets, dropping new arrivals for that queue, and ignoring incoming PFC pauses on that port) so backpressure cannot spread upstream across the fabric; and\n(3) **Restoration**: once pause frames cease for a clean recovery interval, restores normal lossless operation and fires a high-priority operator alert.
</details>

<details>
<summary>15. How does `DCQCN` (`SIGCOMM 2015`) combine `ECN` and `PFC`, and what is the mandatory ordering of queue thresholds?</summary>

**DCQCN** (*Data Center Quantized Congestion Notification*) uses **ECN/CNP** as the primary, fine-grained, per-QP rate controller and uses **PFC** only as the last-resort safety net against buffer overflow. Therefore, queue thresholds must be strictly ordered as:\n**`XON < ECN Kmin < ECN Kmax < PFC XOFF`** (+ headroom).\nAs a queue grows, it crosses `ECN Kmin..Kmax` **first**, marking packets `CE` so senders throttle their QPs smoothly; **PFC (`XOFF`)** only triggers if an abrupt incast burst outruns the 1-RTT ECN control loop.
</details>

<details>
<summary>16. How does `Source Flow Control` (`SFC`, IEEE `802.1Qdw`) improve on both `ECN` and `PFC` (`ADC` Chapter 7)?</summary>

When a switch detects congestion on an egress link (e.g., `Spine A -> Leaf D`), **SFC** trims the congested packet's payload, reverses its source/destination addresses, and sends an **SFC notification packet directly back upstream toward the source (`Leaf A` / sending NIC)**.\n- Unlike **ECN**, the signal does not have to travel forward to the receiver and wait for a `CNP` to come back (cutting reaction latency in half).\n- Unlike **PFC**, SFC identifies the specific **flow** (5-tuple/QP), so the ingress leaf/NIC pauses or throttles **only the culprit flow** rather than pausing the entire priority class.
</details>

<details>
<summary>17. How does `Congestion Signaling` (`CSIG`) improve on ECN's single 2-bit flag (`ADC` Chapter 7)?</summary>

Instead of a binary 1-bit `CE` mark that says only "some hop was congested", **CSIG** carries a small **in-band telemetry tag** in the packet header that each transit switch updates with **quantized multi-bit bottleneck metrics** (such as minimum available bandwidth ratio or maximum queue delay) plus **bottleneck locator metadata** (tier/stage, switch ID, uplink vs downlink). The receiver reflects the CSIG summary back to the sender, allowing the NIC to adjust its sending rate and path selection in a single step proportional to the exact bottleneck severity.
</details>

<details>
<summary>18. Name the IEEE standards that make up the Data Center Bridging (`DCB`) suite.</summary>

- **IEEE `802.1Qbb`**: **PFC** (*Priority-based Flow Control*)\n- **IEEE `802.1Qaz`**: **ETS** (*Enhanced Transmission Selection* bandwidth sharing) and **DCBX** (*Data Center Bridging Capability Exchange Protocol* over LLDP)\n- **IEEE `802.1Qau`**: **QCN** (*Quantized Congestion Notification*, L2 predecessor to DCQCN)\n- **IEEE `802.1Qdw`**: **SFC** (*Source Flow Control*).
</details>

<details>
<summary>19. Which host and switch commands verify `DSCP` trust, `PFC` pause counts, `ECN` marks, `CNP` packets, and lossless queue drops on an NVIDIA ConnectX + SONiC fabric?</summary>

- **On the GPU host**: `mlnx_qos -i eth2` (verifies `--trust dscp` and `--pfc 0,0,0,1,0,0,0,0`), `dcb pfc show dev eth2`, `rdma statistic show` (`np_cnp_sent`, `rp_cnp_handled`, retransmissions), and `ethtool -S eth2 | egrep 'prio3_pause|ecn_marked|cnp|out_of_sequence|discards'`.\n- **On the SONiC switch**: `show pfc counters`, `show queue counters` (verifying **`0` drops** on lossless queue 3), `show priority-group watermark headroom`, and `show pfcwd stats`.
</details>

<details>
<summary>20. Walk through the Section 11 diagnostic flow when an AI training job shows low `AllReduce` bandwidth.</summary>

(1) **Check lossless queue drops on switches and NICs**: if `> 0`, fix DSCP trust/mapping, PFC priority mismatch, or insufficient headroom (or investigate why the PFC watchdog fired);\n(2) **If drops = 0, check PFC pause counters**: if high, congestion is outrunning ECN—lower `ECN Kmin/Kmax` thresholds, check load balancing (`ECMP` / adaptive routing), or locate the incast receiver / stuck NIC;\n(3) **If PFC pauses = 0, check ECN marks and CNPs**: if constantly high, DCQCN is preventing PFC but flows are colliding on hot links (fix ECMP entropy, QP count, or oversubscription);\n(4) **If ECN/PFC = 0, check physical link health** (`FEC`/CRC errors, downtrained speed/width, MTU) and **host/NCCL software** (`NCCL_IB_TC`, NUMA/PCIe locality, CPU stragglers).
</details>

## Sources and review notes

- **Sources read in full:**
  - `computer-networking-problems-and-solutions` — Russ White and Ethan Banks, *Computer Networking Problems and Solutions*, **Chapter 8: Quality of Service** (why not just size links large enough, `9000`-byte `0.72 ms` vs `64`-byte `0.05 ms` serialization jitter on `100 Mb/s`, classification and DSCP Class Selectors `CS0`–`CS7` RFC `2474` and `EF` `46` RFC `3246`, preserving classification across tunnels, the unmarked Internet, congestion management with Low-Latency Queueing `LLQ` and Class-Based Weighted Fair Queueing `CBWFQ`, overcongestion, policing vs shaping, WRED, bufferbloat, and CoDel RFC `8290`).
  - `ai-data-center-network-design-and-technologies` — Dinakaran Setty et al., *AI Data Center Network Design and Technologies*, **Chapter 7: RoCEv2 Transport and Congestion Management** (Clos congestion points, RoCEv2 go-back-N loss sensitivity, ECN RFC `3168` `ECT(0)`/`CE` and CNP BTH opcode `0x81` = `129`, PFC IEEE `802.1Qbb` `XOFF`/`XON` and headroom, PFC HOL blocking / storms / deadlocks / watchdog `100–200 ms`, DCQCN SIGCOMM `2015`, Source Flow Control `SFC` `802.1Qdw`, and Congestion Signaling `CSIG`).
- **Run here:** `python3 code/part02/qos_ecn_pfc_dcqcn_lab.py` (13 passed, 0 failed).
- **Explicitly labelled inferences:** The Linux `tc` (`fq_codel`, `cake`, `htb`, `tbf`, `red ecn`) and ConnectX/SONiC RoCEv2 verification commands (`mlnx_qos`, `rdma statistic`, `dcb pfc`, `show pfcwd stats`) and the Section 11 troubleshooting flowchart synthesize RFCs 2474, 3168, 3246, 7567, 8289, and 8290, IEEE 802.1Qbb/Qaz/Qau/Qdw, and the DCQCN paper (SIGCOMM 2015) (cross-referenced with Chapters 2.5, 2.6, 2.11, 2.12, 2.16–2.18, and 2.28–2.29, plus original study items 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, and 40).
- **Not verified on live hardware:** All interactive VM, `tc`, `mlnx_qos`, `dcb`, and SONiC commands are marked (untested here) and must be executed on a disposable Linux VM or lab switch/NIC testbed.
