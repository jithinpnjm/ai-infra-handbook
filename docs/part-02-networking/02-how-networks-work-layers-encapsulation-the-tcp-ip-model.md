---
id: "c02-02"
title: "2.2 How networks work: layers, encapsulation, the TCP/IP model"
sidebar_label: "2.2 How networks work: layers, encapsulation, the TCP/IP model"
sidebar_position: 2
description: "How networks work: layers, encapsulation, the TCP/IP model"
status: "drafted"
tier: "0"
level: "B"
lab_venue: "GCP / GKE"
---

# 2.2 How networks work: layers, encapsulation, the TCP/IP model

| | |
|---|---|
| Level | Beginner |
| Priority tier | 0 |
| Lab venue | Any Linux VM (packet captures and small calculations) |
| Part | Part 2: Networking, from first principles to AI fabrics |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

Every networking term in an AI cluster (RoCE, InfiniBand, VXLAN, EVPN, ECMP, PFC, MTU, MSS, GRE, NAT, CNI) names something at a particular place in a stack, and every performance or reliability problem becomes tractable once you can say *which layer* it lives at and *what that layer is responsible for*. The vocabulary of layers is also the shared language of every network engineer you will work with: when a switch engineer says "that's an L2 problem" and a platform engineer says "the pod can't reach the service", you need to translate between them in your head.

This chapter builds the foundation: why networks are built from packets rather than circuits; what the four jobs of any data-carrying protocol are; how layered models (the DoD/TCP-IP model, the OSI model, and the recursive view) organise those jobs; how **encapsulation** wraps data at each layer and what the overhead costs; why the Internet's **hourglass** shape (many link technologies below, many applications above, one IP in the middle) is the reason it scaled; the difference between the **data plane**, **control plane** and **management plane**; and how the layers map onto the Linux kernel and onto the AI-cluster fabrics you will meet (Ethernet/RoCE and InfiniBand). Later chapters in this Part take each layer in depth.

## Prerequisites and outcomes

You should have read chapter 2.1 (the packet's journey) and know basic Linux commands.

After this chapter you can:

- Explain circuit switching versus packet switching, and the trade-offs that produced today's packet-switched Internet.
- State the four functions every data-carrying protocol performs (transport, multiplexing, error control, flow control) and classify familiar protocols with them.
- Draw and compare the 4-layer TCP/IP (DoD) model and the 7-layer OSI model; explain why both are useful and neither is perfect; explain the recursive (RINA) view.
- Explain encapsulation and decapsulation, name each layer's PDU (bits, frame, packet, segment/datagram), and compute header overhead and goodput for a given MTU.
- Explain demultiplexing keys (EtherType, IP protocol number, port number) and how a received frame reaches the right process.
- Distinguish connection-oriented from connectionless service, hop-by-hop forwarding from end-to-end state, and the three network planes.
- Explain the hourglass/wasp-waist idea and the State/Optimisation/Surface trade-off model of complexity.
- Locate the layers in the Linux networking stack (`sk_buff`, netfilter hooks, qdisc, NIC drivers, offloads, XDP) and in the RDMA/InfiniBand stack that bypasses it.
- Read a packet capture and label each layer.

## 1. Two ways to build a network

### Circuit switching

In a **circuit-switched** network the path (and bandwidth) between two endpoints is reserved before any data flows. The telephone network is the classic example. With **time-division multiplexing (TDM)**, each link is divided into fixed time slots in a repeating frame; a controller assigns, for each call, one slot on each link along the path, and each switch simply copies the contents of an input slot into an output slot without reading any address (the slot position *is* the address). The reserved slots form a **circuit**.

Advantages: forwarding is trivial (no header parsing), delay and jitter are deterministic, bandwidth is guaranteed, and a central controller can engineer the optimal path with complete knowledge of the load. Disadvantages: unused slots are wasted (bandwidth reserved for a circuit cannot be lent to someone else), the controller becomes a complexity and failure bottleneck as the network grows, and reacting to a topology change is slow (the controller must learn of it and reprogram every switch on each affected path). Frame Relay, SONET/SDH, ISDN and X.25 are circuit- or virtual-circuit-style technologies, many now historical.

### Packet switching

In a **packet-switched** network the data is cut into **packets**, each carrying a **header** with at least the destination (and usually the source and handling information). Every device along the path reads the header, looks up the destination in a **forwarding table**, and sends the packet out the chosen interface: **hop-by-hop forwarding**, each device deciding independently for each packet. The network is a shared resource: packets from many sources interleave on the same link (**statistical multiplexing**), so bandwidth is used only when there is data.

Advantages: efficient use of links; resilience (if a link fails, devices can forward around it as soon as their tables change, without asking a controller; with at least two disjoint paths the network keeps working); simple endpoints and cheap, scalable core devices; incremental deployment. Disadvantages: every device must parse headers and do a table lookup (a real cost in early hardware, now solved in silicon); no inherent guarantee of bandwidth, delay or order; **congestion** can occur when more traffic arrives than a link can send, so queues build up and packets are dropped, which requires **flow control** and **congestion control** to be added on top (TCP, from 1974 onwards).

The Internet is packet switched. The packet-versus-circuit debate left permanent legacies: *virtual circuits and label switching* (MPLS), *reserved bandwidth and QoS* for real-time traffic, *centralised control planes* (SDN) returning for hyperscale fabrics, and *lossless Ethernet* for RDMA (priority flow control creates something like circuit-style "no drop" behaviour inside a packet network, with its own risks: chapter 2.19).

### Fixed versus variable length frames

ATM tried to merge the two worlds with **53-byte fixed cells** (a 5-byte header, 48 bytes of payload) and **label switching** (a short fixed-size label instead of a full destination address, looked up in a small table). Fixed-size cells simplified hardware (no fragmentation, easy buffering and queueing) but wasted bandwidth: a 64-byte data packet needed two cells (one full, one nearly empty), so half or more of the link could carry padding. ATM died; its ideas survived: **label switching became MPLS** and the lesson that *fragmentation hurts performance* led to the IPv4 "Don't Fragment" bit, path MTU discovery, and removal of in-network fragmentation in IPv6. In modern AI fabrics, buffers and switching chips again use fixed-size internal cells even though external frames are variable length, and "message size versus MTU" remains a first-order performance variable.

### Flow control and congestion

Circuit-switched networks cannot oversubscribe a circuit (the slots are pre-allocated), so flow control is built in. Packet networks need it explicitly: **TCP** (Cerf and Kahn, 1973/74) provides end-to-end flow control (do not overrun the receiver) and congestion control (do not overrun the network). Link-level flow control exists too (Ethernet PAUSE frames; PFC per priority; InfiniBand credit-based flow control), and its interaction with end-to-end control is a central topic in AI fabrics.

## 2. The four jobs of a protocol

Every protocol that carries data does some combination of four things:

1. **Transport**: move bits from one place to another, including translating between data formats and addressing endpoints.
2. **Multiplexing**: keep data from different senders, applications or flows separate on a shared medium or connection (and demultiplex them at the other end).
3. **Error control**: detect (CRC, checksum) and optionally correct (FEC) or retransmit (ARQ) damaged or lost data.
4. **Flow control**: match the sender's rate to what the receiver and the network can absorb (windows, credits, pause frames, rate control).

These group naturally into two pairs: *transport + multiplexing* and *error control + flow control*. Examples:

| Protocol | Transport | Multiplexing | Error control | Flow/congestion control |
|---|---|---|---|---|
| Ethernet | Link-local frames, MAC addressing | EtherType, VLAN tags | FCS (CRC32) detects errors (drops); FEC at high speed PHYs | None originally; PAUSE/PFC optional |
| IP | Network-wide addressing, routing | Protocol number | Header checksum (IPv4) only | None (ICMP signals) |
| UDP | Datagrams between ports | Ports | Optional checksum | None |
| TCP | Reliable byte stream | Ports | Checksum, sequence numbers, ACK, retransmit | Receive window, congestion window |
| TLS | Secure channel over TCP | (single stream) | MAC/AEAD integrity | None (relies on TCP) |
| HTTP/2 | Requests/responses | Streams | Relies on TCP | Per-stream flow-control windows |
| QUIC | Streams over UDP | Connection IDs, streams | Own ACKs/retransmit | Own congestion control, stream windows |
| InfiniBand (link + transport) | Packets in a lossless fabric | LIDs/QPs | ICRC/VCRC, ACK/NAK retransmit | Credit-based link flow control, CC |
| RoCE v2 | InfiniBand transport over UDP/IP/Ethernet | UDP port 4791, QP numbers | ICRC + retransmit (go-back-N or selective) | Needs PFC/ECN + DCQCN/other CC |

Seeing each protocol as "which of these four does it do, and at what scope (one link, or end to end)?" is a more reliable guide than memorising layer numbers. The **scope** matters: Ethernet's jobs apply on one link; IP's job applies across many links; TCP's apply end to end. This recursive pattern (the same four functions at different scopes) is the insight of the **Recursive InterNetwork Architecture (RINA)** model.

## 3. Layered models

A **protocol stack model** helps classify protocols by purpose, know which questions to ask about a new protocol, and see how the pieces fit together. Layers talk to the layer above and below through well-defined interfaces (for example the *socket API* between application and transport), and to the *peer layer* on the other machine through a protocol.

### The DoD / TCP/IP model (4 layers)

```mermaid
flowchart TB
  subgraph TCPIP["TCP/IP (DoD) model"]
    A["Application: HTTP, DNS, SSH, TLS, NFS, gRPC"]
    T["Transport: TCP, UDP (ports; reliability, flow control)"]
    I["Internet: IPv4, IPv6, ICMP (addresses, routing, fragmentation)"]
    L["Link (network access): Ethernet, Wi-Fi, PPP; physical signalling"]
    A --- T --- I --- L
  end
```

Developed in the 1960s to 1980s under DARPA sponsorship (not to survive nuclear war, but to let incompatible computers at universities and labs communicate). It separated the problem into link (frames on one network), internet (datagrams across networks), transport (end-to-end conversations) and application (user-visible protocols). A key characteristic: **multiple protocols may exist at each layer** (several link types, TCP and UDP, thousands of applications), connected by **one** at the middle (IP). Earlier seven-layer variants of the DoD model (adding utility, network, internetwork) were dropped.

Placement in Linux: application code runs in **user space** (curl, nginx, PyTorch); the transport layer and everything below live in the **kernel** (with exceptions: user-space networking like DPDK, XDP in the driver, QUIC in user space, RDMA verbs bypassing the kernel stack).

### The OSI model (7 layers)

```mermaid
flowchart TB
  L7["7 Application: user-facing protocols"] --- L6["6 Presentation: encoding, encryption, compression"] --- L5["5 Session: dialogue/session management"] --- L4["4 Transport: end-to-end delivery (TCP, UDP)"] --- L3["3 Network: addressing and routing (IP)"] --- L2["2 Data link: frames on one link, MAC addresses (Ethernet)"] --- L1["1 Physical: signals on the medium (cables, optics, radio)"]
```

Proposed by ISO in 1977 as an alternative to the DoD stack (an attempt to blend circuit- and packet-oriented thinking, driven by telecom and database interests). The full OSI protocol suite never won (the specifications were slow, complex and sold in paper form to members, whereas TCP/IP specifications and implementations were free), but the **model** became the universal teaching and troubleshooting vocabulary, and it made lasting contributions: strict modularity, well-defined interfaces, and the idea that intermediate systems (routers and switches) are part of the architecture. Several OSI-era protocols survive, notably **IS-IS** (Intermediate System to Intermediate System, a routing protocol widely used in data centres and ISP backbones: chapter 2.14).

Practical mapping and usage: people say **L1** (cables, optics, signal, link up/down), **L2** (Ethernet, MAC addresses, VLANs, switching, ARP lives between 2 and 3), **L3** (IP, routing), **L4** (TCP/UDP, ports; load balancers, firewalls), **L7** (HTTP and application-aware proxies). Layers 5 and 6 rarely matter in practice (TLS is often described at L6 or "L4.5"). Protocols often straddle layers: Ethernet is L1+L2; TCP covers parts of L4 and L5; TLS is "Transport Layer Security" yet sits above TCP; BGP runs over TCP (an application protocol) but provides the L3 forwarding information; IPsec is arguably L3 or L4; VXLAN is L2 over L3 over UDP; MPLS is "L2.5". Do not waste energy on classification quarrels; use the model to **ask the right questions**.

### Comparison

| TCP/IP (4) | OSI (7) | Typical protocols and devices | PDU name |
|---|---|---|---|
| Application | 7, 6, 5 | HTTP, DNS, SSH, TLS, gRPC, NFS | Message / data |
| Transport | 4 | TCP, UDP, QUIC (over UDP), SCTP | Segment (TCP) / datagram (UDP) |
| Internet | 3 | IPv4, IPv6, ICMP; routers, L3 switches | Packet |
| Link | 2, 1 | Ethernet, Wi-Fi, PPP; switches, NICs, cables | Frame / bits |

### Connection-oriented and connectionless

A **connection-oriented** service establishes state (and often reserves resources and a path) before sending data, then data flows with little per-packet overhead (TCP at the edge, ATM, MPLS LSPs, InfiniBand queue pairs, RDMA reliable connections). A **connectionless** service carries everything needed to deliver each unit in the unit itself (IP datagrams, UDP, Ethernet frames). The Internet is built connectionless in the core and connection-oriented at the edges: "state in the middle" (circuit-style) makes failure recovery expensive, whereas state at the edges and datagrams in the core let the network route around failures without touching the endpoints' connections (the **end-to-end principle**: put intelligence in the endpoints, keep the core simple). QoS and flow control are often layered on top as connection-like state, which can create mismatches with a connectionless forwarding plane when paths change.

## 4. Encapsulation and decapsulation

When an application sends data, each layer wraps what it receives from above in its own **header** (and sometimes a **trailer**), adds it to the unit, and passes it down. This is **encapsulation**. On the receiving side each layer strips its header and hands the payload up: **decapsulation**.

```mermaid
flowchart TB
  APP["Application data: 'GET / HTTP/1.1 ...' (e.g. 1,000 bytes)"] --> TLS["(TLS record: + 5-byte header + 16-byte tag)"]
  TLS --> TCP["TCP segment = TCP header (20-60 B) + payload"]
  TCP --> IP["IP packet = IP header (IPv4 20-60 B / IPv6 40 B) + segment"]
  IP --> ETH["Ethernet frame = dst MAC (6) + src MAC (6) + [802.1Q tag 4] + EtherType (2) + packet + FCS (4)"]
  ETH --> PHY["On the wire: preamble (7) + SFD (1) + frame + inter-frame gap (12 byte times)"]
```

Header sizes (typical): Ethernet header 14 B (+4 B for an 802.1Q VLAN tag) + FCS 4 B; IPv4 header 20 B (IPv6: 40 B); TCP header 20 B (up to 60 B with options; timestamps add 12 B); UDP header 8 B. On the wire add 8 B preamble/SFD and 12 B inter-frame gap = 20 B of fixed per-frame overhead.

### Overhead and goodput (worked examples)

For a 1500-byte MTU (the maximum IP packet size on standard Ethernet), a TCP/IPv4 segment carries at most **MSS = 1500 − 20 − 20 = 1460 bytes** of data (1448 with the TCP timestamp option). Each such segment occupies 1460 + 20 (TCP) + 20 (IP) + 14 (Eth hdr) + 4 (FCS) + 20 (preamble+IFG) = **1538 byte times** on the wire. Goodput fraction = 1460/1538 = **94.9%**. With a 9000-byte MTU (jumbo): MSS 8960; wire = 8960 + 78 = 9038; efficiency = **99.1%**. For small messages the overhead dominates: a 64-byte minimum frame carries as little as 18 bytes of application data (UDP) and occupies 84 byte times, so a 100 Gb/s link can carry at most 148.8 million minimum-size frames per second (100e9 / (84 × 8)). RoCE v2 adds its own headers (UDP 8 B + IB BTH 12 B + extension headers + ICRC 4 B), and with a 4096-byte RDMA MTU on a jumbo-frame Ethernet fabric the efficiency is again about 98% to 99%. These calculations explain why jumbo frames and larger messages help throughput, and why message-rate (packets per second) limits matter for small-message workloads such as allreduce latency phases or key-value traffic.

```bash
# See the layers in a live packet: -e shows the Ethernet header, -v adds IP/TCP details
sudo tcpdump -nn -e -v -c 5 -i any 'tcp port 443'
# Show raw bytes of a frame; match the layers by offset (Ethernet 0-13, IP 14-33, TCP 34-53 ...)
sudo tcpdump -nn -XX -c 1 -i eth0 'tcp'
ip -s link show dev eth0 ; ethtool -k eth0 | egrep 'segmentation|checksum|scatter|gro|gso|tso'      # offloads hide the true on-wire sizes from tcpdump
```

### Demultiplexing: how the right code gets the bytes

Each layer includes a field that tells the receiver which protocol to hand the payload to:

- **Ethernet EtherType** (16 bits): 0x0800 IPv4, 0x86DD IPv6, 0x0806 ARP, 0x8100 VLAN tag (802.1Q), 0x88A8 QinQ, 0x8847/8848 MPLS, 0x8915 RoCE v1, 0x8808 MAC control (PAUSE/PFC), 0x88CC LLDP.
- **IP protocol / next header** (8 bits): 1 ICMP, 6 TCP, 17 UDP, 41 IPv6-in-IPv4, 47 GRE, 50 ESP (IPsec), 58 ICMPv6, 89 OSPF, 132 SCTP.
- **UDP/TCP port numbers** (16 bits each): identify the endpoint application; **well-known ports** below 1024 (22 SSH, 53 DNS, 80/443 HTTP/HTTPS, 4791 RoCE v2), registered ports 1024 to 49151, ephemeral ports above.

So the first bits of a received frame determine the path through the stack: Ethernet → EtherType 0x0800 → IPv4 → protocol 6 → TCP → destination port 443 → the socket bound to that port (or the connection's 5-tuple) → the process. If any key does not match a handler, the packet is dropped or answered with an error (ICMP protocol/port unreachable, TCP RST).

### MTU, MSS and tunnels

The **MTU** (maximum transmission unit) is the largest IP packet a link can carry (1500 on standard Ethernet; commonly 9000 on storage and AI fabrics; 1460 on some cloud networks). The **MSS** is the largest TCP payload per segment, announced in SYN options (MTU − 40 for IPv4). **Tunnels and overlays** add outer headers: VXLAN adds 50 bytes (outer Ethernet 14 + IP 20 + UDP 8 + VXLAN 8), GRE 24 (IPv4), IPsec ESP 50 to 70+, WireGuard 60; Kubernetes overlays and VPNs therefore reduce the effective MTU of the inner traffic. If the inner packets are not reduced (or MSS clamped), large packets exceed the path MTU: either they are fragmented (slow) or dropped with ICMP "fragmentation needed" (if that ICMP is filtered, connections hang on large transfers: a black hole). Always verify end-to-end MTU in AI clusters: a single link at 1500 in a 9000 fabric cripples throughput or breaks RoCE.

## 5. The three planes

Network devices and networks are organised into functional planes:

| Plane | Job | Examples |
|---|---|---|
| **Data (forwarding) plane** | Moves packets: parse headers, look up the forwarding table (FIB), rewrite, queue, transmit; must run at line rate (ASICs in switches, kernel/XDP/eBPF on hosts, SmartNIC/DPU) | Switching, routing lookups, ACL matching, NAT, encapsulation, QoS queueing |
| **Control plane** | Builds the information the data plane needs: routing protocols, spanning tree, ARP/ND, LACP, BGP/EVPN, SDN controllers | OSPF, IS-IS, BGP, STP, LLDP, DHCP |
| **Management plane** | Configures and monitors the device: CLI, SNMP, NETCONF/gNMI, syslog, telemetry | SSH, REST APIs, Prometheus exporters |

In traditional networks, the control plane is **distributed**: every router runs the protocol and computes its own table (a RIB of candidate routes from which the best go into the FIB). In **SDN**, a **centralised controller** computes and installs forwarding state (OpenFlow was the first widely known interface). In practice hybrid designs win: hyperscale data centres run distributed BGP with automation on top; some AI fabric managers (InfiniBand's **Subnet Manager**) are logically centralised controllers computing routes for a lossless fabric. Where exactly a function sits (is manual static route configuration management plane or control plane?) is a matter of definition; the useful question is "what happens to traffic when the control plane fails, the controller is unreachable, or the device reboots?" (fail-open/fail-static behaviour, graceful restart).

### Loop-free paths: the control plane's core problem

Whatever the protocol, the control plane must produce **loop-free** forwarding paths: if traffic can circle, packets eventually die by TTL (IP) or, worse in L2 where there is no TTL, multiply and melt the network (broadcast storms: chapter 2.11). Three families of algorithm are used: **distance vector** (each router tells neighbours its distances; hop-by-hop; RIP, EIGRP), **link state** (every router floods topology and runs Dijkstra shortest path first on an identical database; OSPF, IS-IS), and **path vector** (each announcement carries the list of autonomous systems it traversed to prevent loops and allow policy; BGP). Chapters 2.13 to 2.16 develop them. An important design insight: advances in CPU, memory and bandwidth made the early arguments about protocol overhead less decisive, but *stability, scalability and operability* remain the criteria.

### Quality of service

Real-time traffic (voice, video, now also tightly synchronised distributed training and RDMA) cares about **delay** and **jitter**. Early thinking said such traffic could never share a packet network; the solution became marking, classification and queueing: classify packets (DSCP/IP precedence, 802.1p PCP), give them separate **queues** with scheduling (strict priority, weighted round robin), shape/police rates, and use ECN/early drop to signal congestion. With faster links and better queueing algorithms, four to eight queues usually suffice. In AI fabrics QoS means dedicating a lossless priority to RDMA traffic with PFC + ECN and keeping storage, management and other traffic in different classes (chapter 2.19).

## 6. Taming complexity: the hourglass and the SOS triangle

### The hourglass (wasp waist)

```mermaid
flowchart TB
  subgraph APPS["Many application protocols"]
    HTTP["HTTP"]; DNS["DNS"]; SSH["SSH"]; NFS["NFS"]; GRPC["gRPC"]; NCCL["NCCL (over TCP/RDMA)"]
  end
  TR["TCP / UDP / QUIC (few)"]
  IPN["IP (exactly one, plus its IPv6 version)"]
  subgraph LINKS["Many link technologies"]
    ETH["Ethernet"]; WIFI["Wi-Fi"]; SAT["Satellite"]; PPP["PPP/LTE/5G"]; IB["IPoIB"]
  end
  APPS --> TR --> IPN --> LINKS
```

Protocols are numerous at the top (applications) and at the bottom (physical media) but there is essentially **one** protocol at the narrow waist: IP. This keeps three kinds of complexity bounded: **state** is separated into "information about the network" (lower layers) and "information about the data" (upper layers), so neither needs the other's detail; **interaction surfaces** between components are reduced to a single well-regulated interface (IP) that changes rarely; and some **optimisation** is deliberately given up by hiding network state from applications (TCP infers congestion from loss and delay rather than knowing the network). Layer violations (a transport that peeks at link state, a switch that parses TCP ports for ECMP, a NIC that offloads TCP) buy performance but add interaction surfaces and make evolution harder (ossification: middleboxes that break new TCP options or QUIC). AI fabrics are a deliberate, controlled violation of layering: RDMA transport hardware is tightly integrated with link-layer flow control and a specific fabric design to buy microsecond latency and zero CPU overhead.

### State, Optimisation, Surface

A useful trade-off model for any network design decision:

- **State**: how much information devices must hold (routes, ACLs, MAC tables, flows).
- **Optimisation**: how well the design uses resources (shortest paths, load balance, low latency, cost).
- **Surface**: how many places and ways components interact (protocols, interfaces, configuration touch points, failure interactions).

Increasing optimisation tends to require more state or more interaction surfaces; reducing state tends to reduce optimisation or increase surfaces; reducing surfaces tends to cost optimisation or state. The *plane of the possible* is the region of designs you can actually build. Example: **stretch** is the difference between the shortest physical path and the path traffic actually takes; any policy (traffic engineering, PBR) increases stretch; the extra state and interaction needed to implement it is the price. Similar three-way trade-offs appear everywhere (CAP theorem; quick/cheap/good). "If you have not found the trade-off, you have not looked hard enough." Complexity cannot be "solved", only moved or managed: abstraction (black boxes), moving the problem elsewhere, adding a layer of indirection (overlays), replacing the system, or deferring it. Each has costs; a network that is robust against the predictable can be brittle against the unpredictable ("robust yet fragile"). Keep this in mind when you design clusters: every special case (a rail-optimised topology exception, a custom NCCL topology file, a per-tenant policy) adds state and surface.

## 7. Where the layers live: Linux and AI fabrics

### The Linux stack

```mermaid
flowchart TB
  APP["Application (user space): socket API (socket, bind, listen, connect, send, recv, epoll)"] --> SOCK["Socket layer: struct socket / sock; send and receive buffers (sk_buff queues)"]
  SOCK --> L4["TCP / UDP / SCTP / QUIC-in-userspace: connection state, retransmit timers, congestion control"]
  L4 --> L3["IP: routing (FIB), netfilter hooks (PREROUTING, INPUT, FORWARD, OUTPUT, POSTROUTING), fragmentation, IPsec/XFRM"]
  L3 --> QD["Traffic control: qdisc (fq_codel, fq, mq, htb, tbf), tc filters, eBPF (tc, cgroup, XDP)"]
  QD --> DRV["Device driver / NIC: TX/RX rings (DMA), NAPI polling, interrupts, RSS queues, offloads (checksum, TSO/GSO/GRO, VLAN, VXLAN)"]
  DRV --> WIRE["Wire / fiber / virtual device (virtio, veth, vxlan, bridge, bond, tun)"]
  RDMA["RDMA verbs (libibverbs): memory registration, QPs, CQs - NIC hardware transport"] -. "bypasses sockets, TCP/IP, qdisc" .-> WIRE
```

The unit of data inside the kernel is the **`sk_buff`** (socket buffer): a descriptor with pointers into packet data and metadata (headers, device, timestamps, checksum state). Layers add and remove headers by moving pointers (cheap), not by copying. Software constructs map to the layer model: **`lo`, `eth0`, `ens4`** (L2 devices), **bridge** (software switch, L2), **bond/team** (link aggregation, L2), **VLAN subinterface** (802.1Q, L2), **veth** (virtual cable between namespaces), **VXLAN/GRE/Geneve** devices (L2/L3 overlays), **WireGuard** (L3 tunnel), routing tables and rules (L3), netfilter/nftables and conntrack (L3/L4 filtering and NAT), qdiscs (egress queueing), XDP (programs at the earliest driver point).

```bash
ip -d link show                          # device types: bridge, bond, vlan, veth, vxlan, tun ...
ip -s link show dev eth0                 # RX/TX counters, errors, drops (L1/L2 health)
ss -s ; ss -tanp | head                  # sockets (L4) per state and process
nstat -az | egrep 'TcpRetrans|IpInDiscards|UdpInErrors'      # protocol counters
tc qdisc show ; tc -s qdisc show dev eth0                      # queueing discipline and drops
sudo nft list ruleset | head -50 ; sudo conntrack -L | head    # filtering and NAT state
sudo bpftool net list 2>/dev/null | head                       # XDP / tc eBPF programs
```

### AI fabrics in the model

| Fabric | L1/L2 | L3 | L4 / transport | How it maps |
|---|---|---|---|---|
| **Ethernet with TCP** (front-end, storage, control plane) | Ethernet (25/100/400 GbE) | IP (BGP/ECMP in Clos) | TCP/UDP (kernel) | Standard stack; congestion control CUBIC/BBR |
| **RoCE v2** (RDMA over Converged Ethernet) | Lossless Ethernet (PFC, ECN, DCB) | IP (routable) | UDP (4791) + IB transport (BTH) in the NIC | RDMA verbs bypass the kernel stack; fabric must be engineered for near-zero loss |
| **InfiniBand** | IB link layer (credit-based, virtual lanes) | IB network layer (GIDs; routing via LIDs inside subnets, GRH across) | IB transport (RC/UD/...) in the NIC | Own addressing and a Subnet Manager computing forwarding tables |
| **NVLink / NVSwitch** | Proprietary GPU-to-GPU links | (memory-semantic, no IP) | Load/store and DMA between GPUs | Inside a node (and now rack-scale): collectives use it before leaving via NICs |
| **PCIe** | Serial links, TLPs | (bus) | | GPU-NIC-CPU paths; locality matters (chapter 1.28) |

For NCCL, "the network" is therefore a hierarchy: NVLink inside the node, NIC and fabric between nodes, TCP sockets as the fallback and for bootstrap. Chapters in Part 12 take these in depth.

## 8. Reading a capture: labelling layers

A frame decoded by `tcpdump -nn -e -v` (illustrative):

```text
12:00:01.123456 52:54:00:12:34:56 > 52:54:00:ab:cd:ef, ethertype IPv4 (0x0800), length 74:
    10.0.0.15.51234 > 93.184.216.34.443: Flags [S], seq 1, win 64240, options [mss 1460,sackOK,TS val 1 ecr 0,nop,wscale 7], length 0
    (tos 0x0, ttl 64, id 12345, offset 0, flags [DF], proto TCP (6), length 60)
```

Layer by layer: **L2** source MAC 52:54:00:12:34:56 to destination 52:54:00:ab:cd:ef, EtherType 0x0800 → next header is IPv4; frame length 74 = 14 (Eth) + 60 (IP). **L3** source 10.0.0.15, destination 93.184.216.34, TTL 64, DF set, protocol 6 → TCP; IP total length 60 = 20 (IP) + 40 (TCP with options). **L4** TCP source port 51234 (ephemeral) to destination 443; flag S (SYN); options MSS 1460, SACK, timestamps, window scale 7. No payload yet (length 0): this is the first packet of the handshake. The same frame viewed in Wireshark expands each header's fields as a tree; the OSI/TCP-IP model is the table of contents of that tree.

## 9. Hands-on lab: layers, overhead, and captures

First, run the self-checking Python lab (`code/part02/layers_encapsulation_lab.py`) locally. It verifies Ethernet/IP/TCP goodput efficiency (`94.9%` at `1500` MTU vs `99.1%` at `9000` jumbo MTU), `50`-byte VXLAN MSS reduction (`1410` B), maximum packet rate (`148.8 Mpps` on `100 Gb/s` and `595.2 Mpps` on `400 Gb/s` for `64`-byte frames), and L2 -> L3 -> L4 demultiplexing keys.

```bash
python3 code/part02/layers_encapsulation_lab.py
```

Next, on a disposable Linux VM (all interactive VM commands below are `untested here`), work through these steps:

1. **Capture and label**: run `sudo tcpdump -nn -e -v -w layers.pcap -i any 'host example.com or port 53'` while running `curl -s https://example.com/ >/dev/null`; open in Wireshark (or `tshark -r layers.pcap -V -c 3`). For one DNS packet and one TCP packet, write down each header's key fields and the demultiplexing key that selected the next layer.
2. **Overhead calculator**: write a small script (Python) taking MTU, L3 (IPv4/IPv6), L4 (TCP/UDP, options), VLAN yes/no and returning MSS, bytes on the wire per full segment, and efficiency; test 1500, 9000, 4096-byte RDMA payloads, VXLAN encapsulation; compute max packets/s for a 100 Gb/s and 400 Gb/s link for 64-byte and 1500-byte frames.
3. **MTU experiment**: `ping -M do -s 1472 <host>` (1472 + 28 = 1500) then 1473; observe the "message too long"/"frag needed" behaviour; `tracepath <host>` to discover path MTU; lower an interface MTU in a network namespace pair and watch TCP's MSS and PMTUD adapt (see chapter 2.25 for the namespace setup).
4. **See the stack**: use `ip -d link`, `ss -s`, `nstat`, `tc -s qdisc`, `nft list ruleset` on your VM; classify each output as L1/L2, L3, L4, or "between"; run `ethtool -k` and note which functions are offloaded to the NIC.
5. **Encapsulation by hand**: create a VXLAN device between two namespaces (or two VMs), capture the outer and inner headers, and verify the 50-byte overhead and the MTU reduction.
6. **RDMA contrast** (if hardware available): run `ib_write_bw` and observe with `tcpdump` (nothing appears for IB; RoCE appears only on a mirrored port or with a special capture tool); read `ethtool -S` / `rdma statistic` counters; write down which layers the traffic "skips".
7. **Complexity exercise**: pick a cluster design choice (for example, using a dedicated RDMA VLAN and policy routing for a second NIC) and write down the added state, the optimisation gained and the new interaction surfaces; discuss the trade-off.

## 10. Common mistakes

- Treating the OSI numbers as strict facts; arguing about where a protocol "belongs" instead of asking what it does and at what scope.
- Forgetting overhead: assuming 100 Gb/s of line rate equals 100 Gb/s of application throughput; ignoring per-packet limits for small messages.
- Ignoring MTU in tunnels, VPNs, overlays and clouds.
- Confusing hop-by-hop identifiers (MAC) with end-to-end ones (IP) and with application identifiers (port).
- Assuming a lossless fabric behaves like a normal Ethernet network (PFC deadlocks, head-of-line blocking, pause storms).
- Believing TCP/IP tools see all traffic on a host (RDMA, DPDK, XDP-redirected traffic, and offloaded flows bypass them).
- Adding "just one more" overlay or special case without accounting for state and interaction surfaces.

## 11. Interview angles

- "Explain the OSI model and where TCP, IP, Ethernet, VXLAN and TLS fit." (With the caveats.)
- "What does encapsulation mean? What is the overhead of VXLAN? What happens to MTU?"
- "Circuit versus packet switching: why did packet switching win, and where does circuit-like behaviour reappear?" (MPLS, lossless RDMA fabrics.)
- "What is the difference between the control plane and the data plane? What happens when the control plane fails?"
- "How does a frame find the right process on a server?" (EtherType → IP protocol → port → socket.)
- "Why can't I see RDMA traffic with tcpdump?"
- "What is the hourglass model and why did the Internet scale?"
- "Where does NCCL traffic live in these layers when it uses InfiniBand versus sockets?"

## Exercises

1. **Circuit Switching vs. Packet Switching, Statistical Multiplexing, and ATM's Legacy (`CN` Chapter 1):** (a) Compare circuit switching (TDM time slots) and packet switching (hop-by-hop statistical multiplexing) across link utilization, resilience to link failures, and control-plane complexity; (b) why did ATM's `53`-byte fixed cells (`5`-byte header + `48`-byte payload) lose to variable-length IP/Ethernet packets, and what two ATM concepts survived into modern networks?
2. **The Four Jobs of a Data-Carrying Protocol and the RINA Scope View (`CN` Chapter 3):** State the four functions performed by data-carrying protocols (transport, multiplexing, error control, flow/congestion control), and compare how Ethernet, IPv4, UDP, TCP, QUIC, InfiniBand, and RoCE v2 (`UDP 4791` + IB `BTH` + `ICRC`) implement each of the four.
3. **Encapsulation Overhead, Goodput (`1500` vs. `9000` MTU vs. `VXLAN`), and `Mpps` Limits:** (a) Using `compute_tcp_ethernet_goodput()` in `code/part02/layers_encapsulation.py`, compute the TCP/IPv4 `MSS`, total on-wire byte-times (including `14`B Eth + `4`B FCS + `8`B preamble/SFD + `12`B inter-frame gap), and goodput percentage for `MTU = 1500`, `MTU = 9000` (jumbo), and `MTU = 1500` with a `50`-byte VXLAN overlay; (b) using `compute_max_frame_rate_mpps()`, compute the maximum packet rate in `Mpps` for minimum `64`-byte frames (`84` byte-times on the wire) on a `100 Gb/s` link and a `400 Gb/s` link.
4. **Demultiplexing Keys (`EtherType`, `IP Protocol`, and `TCP/UDP Port`):** Trace how a receiving Linux kernel demultiplexes an incoming frame (`demultiplex_packet()`) for: (a) `EtherType = 0x0800`, `proto = 6`, `dst_port = 443`, (b) `EtherType = 0x0800`, `proto = 17`, `dst_port = 4791`, and (c) `EtherType = 0x86DD`, `next_header = 58`.
5. **The Three Network Planes, the Hourglass Model, and the State/Optimization/Surface (`SOS`) Triangle:** (a) Distinguish the Data Plane (`FIB`), Control Plane (`RIB`, distance vector / link state / path vector, or centralized IB Subnet Manager), and Management Plane; (b) explain the Internet hourglass (*wasp waist*) and use White's **State / Optimization / Surface (`SOS`)** triangle to explain the cost of reducing path *stretch* via traffic-engineering policies or overlays.
6. **Mapping the Layers to the Linux Kernel (`sk_buff`, `netfilter`, `qdisc`, `XDP`) vs. AI Fabrics:** Trace a packet through the Linux kernel stack (`socket` -> `sk_buff` -> TCP/UDP -> IP FIB & `netfilter` hooks -> `tc qdisc` -> NIC ring / `XDP`) and contrast it with how `RoCE v2`, `InfiniBand`, and `NVLink`/`NVSwitch` map onto L1–L4.

## Checkpoint questions (20)

<details>
<summary>1. What is the fundamental difference between circuit switching and packet switching?</summary>
In **circuit switching** (such as TDM telephony), a dedicated path and fixed bandwidth time slots are reserved end-to-end before any data flows—guaranteeing bandwidth and jitter, but wasting capacity whenever the sender is silent. In **packet switching**, data is sliced into self-describing **packets** that share links via **statistical multiplexing** and are forwarded independently **hop-by-hop**.
</details>

<details>
<summary>2. Why did ATM's 53-byte fixed cells fail against variable-length Ethernet/IP, and which ATM ideas survived?</summary>
ATM used `53`-byte cells (`5`-byte header + `48`-byte payload) to make hardware switching deterministic, but slicing variable-length data into 48-byte chunks wasted massive bandwidth on headers and padding ("cell tax"). However, ATM's **label switching** evolved directly into **MPLS**, and its proof that in-network fragmentation hurts router performance led to IPv4 Path MTU Discovery (`DF` bit) and the removal of router fragmentation in IPv6.
</details>

<details>
<summary>3. What are the four functions of any data-carrying protocol (`CN` Chapter 3), and how does the RINA model view them?</summary>
The four functions are: (1) **Transport** (moving bits and addressing), (2) **Multiplexing** (separating multiple flows on a shared channel), (3) **Error control** (CRC, checksums, FEC, ARQ retransmissions), and (4) **Flow/congestion control** (matching sender rate to receiver and network capacity). The **RINA** (*Recursive InterNetwork Architecture*) model observes that these same four functions repeat recursively at different scopes: across one physical link (Ethernet), across an internetwork (IP), and end-to-end between processes (TCP).
</details>

<details>
<summary>4. Compare the 4-layer TCP/IP (DoD) model and the 7-layer ISO OSI model, and name the PDU at each layer.</summary>
The **4-layer TCP/IP model** consists of: **Application** (`Message`/`Data`, covering OSI L7 Application, L6 Presentation, and L5 Session), **Transport** (`Segment` for TCP / `Datagram` for UDP, OSI L4), **Internet** (`Packet`, OSI L3 Network), and **Link** (`Frame` at OSI L2 Data Link / `Bits` at OSI L1 Physical).
</details>

<details>
<summary>5. Why did the TCP/IP protocol suite beat the ISO OSI protocol suite in practice, while the 7-layer OSI numbering survived?</summary>
The DARPA TCP/IP specifications (RFCs) were open, free, and shipped as working C code inside BSD Unix, whereas ISO OSI specifications were slow, committee-heavy, and sold as expensive paper documents. The 7-layer OSI numbering (`L1` physical optics, `L2` Ethernet switching, `L3` IP routing, `L4` TCP/UDP load balancing, `L7` HTTP proxies) survived because it separates physical (`L1`) from data-link (`L2`) and provides a clear troubleshooting vocabulary.
</details>

<details>
<summary>6. Give four examples of protocols that blur or straddle strict OSI layer boundaries.</summary>
(1) **ARP** sits between L2 and L3 (carried in Ethernet frames `0x0806` to resolve L3 IPv4 addresses to L2 MACs); (2) **MPLS** sits at "L2.5" between Ethernet and IP; (3) **BGP** runs over TCP port `179` (an L7 application socket) yet builds the L3 IP routing table; and (4) **VXLAN** encapsulates L2 Ethernet frames inside L4 UDP datagrams (`port 4789`) over L3 IP packets.
</details>

<details>
<summary>7. What is the difference between connection-oriented and connectionless protocols, and how does the End-to-End Principle combine them?</summary>
A **connection-oriented** protocol (`TCP`, `MPLS LSPs`, `InfiniBand RC QPs`) sets up state at the endpoints (or along the path) before transferring data; a **connectionless** protocol (`IP`, `UDP`, `Ethernet`) routes every packet independently using only its header. Under the **End-to-End Principle**, the Internet keeps the core network connectionless (`IP`) so routers can route around link failures instantly without tearing down connections, while placing connection state and reliability at the endpoints (`TCP` or NIC `RDMA` engines).
</details>

<details>
<summary>8. Calculate the on-wire goodput efficiency of a full-size TCP/IPv4 segment at `MTU = 1500` versus `MTU = 9000` (jumbo frames).</summary>
At `MTU = 1500`: `MSS = 1500 - 20 (IPv4) - 20 (TCP) = 1460` bytes of application payload. On the Ethernet wire, the frame consumes `1500 + 14 (Eth hdr) + 4 (FCS) + 8 (Preamble/SFD) + 12 (Inter-Frame Gap) = 1538` byte-times, giving **`1460 / 1538 = 94.9%`** goodput (`1448 / 1538 = 94.1%` with 12-byte TCP timestamps). At `MTU = 9000`: `MSS = 8960` over `9038` wire byte-times = **`99.1%`** goodput.
</details>

<details>
<summary>9. What is the maximum packet rate (`Mpps`) of a `100 Gb/s` link and a `400 Gb/s` link when sending minimum 64-byte Ethernet frames?</summary>
A minimum `64`-byte Ethernet frame (`14`B header + `46`B payload + `4`B FCS) plus `8`B Preamble/SFD and `12`B Inter-Frame Gap occupies **`84` byte-times = `672` bits** on the wire. A `100 Gb/s` link can carry at most `100e9 / 672 = 148.8 million packets per second (Mpps)`, and a `400 Gb/s` link can carry at most **`595.2 Mpps`**.
</details>

<details>
<summary>10. State the exact demultiplexing keys at L2 (`EtherType`), L3 (`IP Protocol`), and L4 (`Port`) for IPv4, IPv6, ARP, VLAN, TCP, UDP, ICMP, HTTPS, and RoCE v2.</summary>
- **L2 `EtherType` (16-bit)**: `0x0800` = IPv4, `0x86DD` = IPv6, `0x0806` = ARP, `0x8100` = 802.1Q VLAN, `0x8915` = RoCE v1, `0x88CC` = LLDP.
- **L3 `Protocol` / `Next Header` (8-bit)**: `1` = ICMP, `6` = TCP, `17` = UDP, `47` = GRE, `50` = IPsec ESP, `58` = ICMPv6, `89` = OSPF.
- **L4 `Port` (16-bit)**: `22` = SSH, `53` = DNS, `80` = HTTP, `443` = HTTPS/QUIC, `4791` = RoCE v2.
</details>

<details>
<summary>11. How many bytes of header overhead does VXLAN add, and what happens if the inner container/VM MTU is not reduced?</summary>
VXLAN adds **`50` bytes** of outer headers (`14`B outer Ethernet + `20`B outer IPv4 + `8`B UDP + `8`B VXLAN header; `70` bytes with outer IPv6). On a `1500`-MTU physical underlay, the inner virtual interface MTU must be reduced to **`1450` bytes** (or the physical underlay raised to jumbo `9000` MTU); otherwise full-size inner packets exceed the underlay MTU and are either fragmented or dropped.
</details>

<details>
<summary>12. Distinguish the Data Plane, Control Plane, and Management Plane, and explain `RIB` versus `FIB`.</summary>
The **Data Plane** forwards packets at line rate in switch ASICs or kernel/NIC fast paths using the **FIB** (*Forwarding Information Base*). The **Control Plane** runs protocols (`OSPF`, `IS-IS`, `BGP`, `STP`, `ARP`, or an InfiniBand Subnet Manager) to discover topology and populate candidate routes in the **RIB** (*Routing Information Base*), programming the best routes into the FIB. The **Management Plane** (`SSH`, `NETCONF`/`gNMI`, `SNMP`, `Prometheus`) configures and monitors the device.
</details>

<details>
<summary>13. Name the three families of control-plane algorithms used to build loop-free forwarding paths.</summary>
(1) **Distance Vector** (`RIP`, `EIGRP`: routers exchange distance vectors with immediate neighbors hop-by-hop); (2) **Link State** (`OSPF`, `IS-IS`: routers flood link-state advertisements across an area so every router runs Dijkstra's SPF algorithm on an identical topology graph); and (3) **Path Vector** (`BGP`: routes carry the explicit sequence of Autonomous Systems `AS_PATH` traversed to detect loops and enforce policy).
</details>

<details>
<summary>14. What is the \"hourglass\" (wasp-waist) model of the Internet, and how do AI RDMA fabrics intentionally violate it?</summary>
The Internet hourglass has many application protocols at the top and many physical/link media at the bottom, connected by **one narrow waist: `IP`**. This allows new applications and new link technologies to be deployed independently without knowing each other's internals. AI RDMA fabrics (`RoCE v2` and `InfiniBand`) intentionally cross layer boundaries—coupling NIC transport retry engines directly to L2 lossless flow control (`PFC`/credits) and L3 `ECN` marking—to achieve microsecond latency and zero host CPU overhead.
</details>

<details>
<summary>15. Explain Russ White's **State / Optimization / Surface (`SOS`)** trade-off triangle and the concept of path *stretch*.</summary>
Every network design balances three coupled quantities: **State** (amount of routing/flow state stored across devices), **Optimization** (how closely traffic follows the optimal path and utilizes links), and **Interaction Surface** (number of protocol touchpoints and failure interactions). **Stretch** is the difference between the shortest physical path and the path traffic actually takes; reducing stretch or engineering custom per-flow paths (higher Optimization) inevitably increases both State and Interaction Surfaces.
</details>

<details>
<summary>16. What is `sk_buff` inside the Linux kernel, and how does it avoid copying packet bytes as a packet moves through L4, L3, and L2?</summary>
`struct sk_buff` (*socket buffer*) is the kernel's metadata descriptor representing a network packet. It allocates headroom and tailroom around the payload buffer so each layer encapsulates or decapsulates headers simply by advancing or retreating data pointers (`skb_push` / `skb_pull`) without copying the payload in memory.
</details>

<details>
<summary>17. Where do `netfilter` (`iptables`/`nftables`), `tc qdisc`, and `XDP` sit in the Linux networking stack?</summary>
**`XDP`** (*eXpress Data Path*) runs eBPF programs at the earliest possible point inside the NIC driver's RX ring before an `sk_buff` is even allocated. **`netfilter`** hooks (`PREROUTING`, `INPUT`, `FORWARD`, `OUTPUT`, `POSTROUTING`) sit inside the L3 IP layer (`nftables`/`iptables` and `conntrack` NAT). **`tc qdisc`** (*queueing discipline*, such as `fq_codel` or `fq`) sits between L3 IP and the NIC driver's TX ring to schedule and shape outgoing packets.
</details>

<details>
<summary>18. Why can `ethtool -k` offloads (`TSO`, `GSO`, `GRO`) make `tcpdump` show packets that appear larger than the `1500`-byte MTU?</summary>
With **TSO** (*TCP Segmentation Offload*) and **GSO** on TX—and **GRO** (*Generic Receive Offload*) on RX—the kernel hands a single `64 KiB` super-segment to the NIC driver (where `libpcap`/`tcpdump` taps the packet), and the NIC hardware slices it into `1500`-byte MTU frames on the wire.
</details>

<details>
<summary>19. Compare how Ethernet+TCP, RoCE v2, InfiniBand, and NVLink/NVSwitch map onto L1–L4 in an AI cluster.</summary>
- **Ethernet + TCP**: L1/L2 Ethernet -> L3 IP -> L4 kernel TCP (used for management, HTTP/S3, and bootstrap).
- **RoCE v2**: L1/L2 Lossless Ethernet (`PFC`/`DCB`) -> L3 IP (`ECN`) -> L4 UDP (`port 4791`) + InfiniBand Base Transport Header (`BTH`) implemented in NIC hardware.
- **InfiniBand**: L1/L2 native IB link layer (credit-based flow control, Virtual Lanes, `LID`s) -> L3 IB Global Route Header (`GRH`/`GID`s) -> L4 IB transport (`RC`/`UD` Queue Pairs) in NIC hardware, managed by a Subnet Manager.
- **NVLink / NVSwitch**: high-speed GPU-to-GPU memory-semantic interconnect inside a node or rack (`NVL72`) used directly by CUDA/NCCL load/store and DMA engines without IP or Ethernet headers.
</details>

<details>
<summary>20. In the `tcpdump -nn -e -v` capture `frame length 74`, `IP length 60`, `Flags [S]`, `mss 1460`, `length 0`, account for every byte of the 74-byte frame.</summary>
`74` bytes total frame = **`14` bytes Ethernet II header** (`6`B dst MAC + `6`B src MAC + `2`B EtherType `0x0800`) + **`60` bytes IPv4 packet**. Inside the `60`-byte IPv4 packet: **`20` bytes IPv4 header** + **`40` bytes TCP SYN header** (`20`B base TCP header + `20`B TCP options: `mss 1460`, `sackOK`, `TS`, `nop`, `wscale 7`) + **`0` bytes TCP payload** (the 4-byte Ethernet `FCS` is stripped by the NIC before `tcpdump`).
</details>

## Sources and review notes

- **Sources read in full:**
  - `computer-networking-problems-and-solutions` — Russ White and Ethan Banks, *Computer Networking Problems and Solutions*, **Chapter 1: Fundamental Concepts** (art vs engineering, circuit switching and TDM vs packet switching and statistical multiplexing, ATM `53`-byte cells and label switching -> MPLS, flow control and TCP `1973`/`1974`, loop-free path algorithm families distance vector / link state / path vector, QoS `4 to 8` queues, centralized SDN control planes, the hourglass / wasp-waist model, and the State / Optimization / Surface `SOS` trade-off triangle and path *stretch*) and **Chapter 3: Modeling Network Transport** (the 4 jobs of a data-carrying protocol transport / multiplexing / error control / flow control, the 4-layer DoD TCP/IP model vs the 7-layer `1977` ISO OSI model vs the Recursive InterNetwork Architecture `RINA` model, and connection-oriented vs connectionless transport).
  - `how-linux-works-3rd-edition` — Brian Ward, *How Linux Works*, 3rd ed., **Chapter 9: Understanding Your Network and Its Configuration** (network layers, packets, hosts, routers, and Linux network interfaces).
- **Run here:** `python3 code/part02/layers_encapsulation_lab.py` (15 passed, 0 failed).
- **Explicitly labelled inferences:** The `1500` vs `9000` MTU goodput (`94.9%` vs `99.1%`) and `148.8`/`595.2 Mpps` frame-rate math, Linux `sk_buff`/`netfilter`/`qdisc`/`XDP` stack diagram, and AI fabric comparison table (`Ethernet/TCP`, `RoCE v2` UDP `4791`, `InfiniBand`, `NVLink/NVSwitch`, `PCIe`) connect foundational layering models to Part 8 and Part 9 AI cluster fabrics (cross-referenced with Chapters 1.28, 2.1, 2.3, 2.11, 2.13–2.16, 2.19, and 2.25, plus original study items 21, 22, 23, 24, 25, 26, 27, 28, 29, and 30).
- **Not verified on live hardware:** All interactive VM commands (`tcpdump`, `tshark`, `ethtool`, `ip -d link`, `ss`, `nstat`, `tc`, `nft`, `bpftool`, `ping -M do`, `tracepath`, `ib_write_bw`) are marked (untested here) and should be executed on a disposable Linux VM.
