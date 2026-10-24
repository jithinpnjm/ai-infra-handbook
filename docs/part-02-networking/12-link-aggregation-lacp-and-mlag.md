---
id: "c02-12"
title: "2.12 Link aggregation, LACP, MLAG and ECMP"
sidebar_label: "2.12 Link aggregation, LACP, MLAG and ECMP"
sidebar_position: 12
description: "Link aggregation, LACP, MLAG, ECMP and cluster network roles"
status: "drafted"
tier: "0"
level: "I"
lab_venue: "GCP / GKE"
---

# 2.12 Link aggregation, LACP, MLAG and ECMP

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 0 |
| Lab venue | Linux VM with network namespaces; optional containerlab/FRR |
| Part | Part 2: Networking, from first principles to AI fabrics |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

A GPU server needs bandwidth *and* resilience: a management or storage connection that survives a switch reboot, a leaf pair that can be upgraded without draining racks, and a fabric whose parallel links all carry traffic. The tools are link aggregation (bonding/LACP) on the host and the first hop, multi-chassis variants (MLAG, vPC, EVPN multihoming) to span two switches, and ECMP at layer 3 across spines. The catch is hashing: aggregated links do not scale linearly, flows pin to one member, and a handful of elephant flows (all-reduce, checkpoint writes) can saturate one link while its siblings sit idle. Understanding the hash and the failure behaviour is the difference between 800 Gb/s of useful bandwidth and a congested link nobody can explain.

## Prerequisites and outcomes

You should know Ethernet/VLANs/STP (2.3, 2.11) and host routing (2.5).

After this chapter you can:

- Explain why parallel links need a flow-to-member mapping, why per-packet round robin is avoided, and how hash inputs determine balance.
- Describe LACP (802.1AX/802.3ad): actors, partners, system priority, keys, active/passive, fast/slow timers, aggregation selection, and failure detection.
- Configure Linux bonding (modes 0 to 6, `xmit_hash_policy`, `miimon`, `lacp_rate`, `min_links`), netplan/NetworkManager/systemd-networkd bonds, and inspect `/proc/net/bonding`.
- Explain MLAG/vPC and EVPN multihoming, their failure modes, and why modern fabrics prefer routed designs.
- Explain routed ECMP, hash fields, polarization, resilient/consistent hashing, flowlets and adaptive routing, and elephant-versus-mouse flows.
- Design host attachment for management, storage, front-end and compute networks of an AI cluster, and know the classic cluster node roles and networks.

## 1. The problem: many parallel links, one conversation

Two switches are joined by two 100G links. Intuitively traffic should alternate: frame 1 on link A, frame 2 on link B. That is **round-robin**, and it maximises utilisation, but frames can arrive out of order (frame 2 overtakes frame 1 on a faster or less congested path), which forces receivers to reorder and TCP to mistake reordering for loss (duplicate ACKs, spurious fast retransmits, collapsed throughput). A few implementations use round robin where reordering is tolerated (Linux `balance-rr`, some RDMA fabrics with packet spraying and reordering-aware NICs), but almost everything else uses **flow hashing**: compute a hash over fields that are constant for a flow, take it modulo the number of members, and send every packet of that flow down the same member. Ordering is preserved; utilisation is statistical.

```mermaid
flowchart LR
  F["Frame / packet\nsrc MAC, dst MAC, src IP, dst IP, proto, src port, dst port"] --> H["Hash(selected fields)"]
  H --> M["hash mod N (or consistent/resilient table)"]
  M --> L1["Member link 1"]
  M --> L2["Member link 2"]
  M --> L3["Member link N"]
```

### Hash functions and why balance is imperfect

A hash maps a large input to a small fixed output deterministically, spreading inputs roughly evenly across the buckets. A toy hash (sum the digits) shows the properties: the same input always yields the same output (so a flow sticks to one link), you cannot recover the input from the output, and different inputs can *collide* into the same bucket. For load sharing you want collisions to be evenly spread, not avoided. Real switches and the kernel use CRC variants, XOR folds or Jenkins/Toeplitz-style hashes, often with a per-device seed.

Balance is statistical and depends on:

- **Entropy of the hash inputs.** Many hosts in one broadcast domain talking to each other have varied MACs; a few hosts talking to a single server have little MAC or IP variety, so hashing on L4 ports (src/dst port) adds the entropy. A single TCP connection between two hosts has exactly one 5-tuple and therefore uses **one** member, no matter how many links exist.
- **Flow sizes.** *Elephant flows* (storage transfers, backups, collective communication, checkpoint writes) carry most of the bytes; *mouse flows* (web requests, RPCs) are small. Two elephants hashed to the same link saturate it while others idle. Aggregated bandwidth "scales" only statistically with many flows.
- **Layer mismatch.** Hashing only on MACs (L2) is useless when all traffic goes to one gateway MAC (everything leaves via the router's MAC); hashing on L3/L4 fields fixes that.
- **Polarization.** If successive tiers (leaf then spine) use the same hash function and seed on the same fields, the flows that were selected for one link at the first tier all select the same link at the second, leaving paths unused. Vendors add per-device seeds, different hash functions/fields per tier, or use packet fields that change (e.g., inner headers).

The network engineer's task is to understand the traffic mix and pick the available hash fields that spread it best: L2 (src/dst MAC) for many hosts in one domain, L3 (src/dst IP) for routed traffic with many endpoints, L3+L4 (5-tuple) for few hosts with many connections; encapsulated traffic (VXLAN, GRE, IPsec) needs *inner-header* hashing or varied outer UDP source ports to create entropy (chapter 2.17). RDMA (RoCE v2) deliberately varies the UDP source port per queue pair, and NCCL uses multiple QPs per connection, precisely to give ECMP hashing something to spread.

## 2. Link aggregation and LACP

**Link aggregation** (IEEE 802.1AX, formerly 802.3ad; vendor names: EtherChannel, port-channel, bond, LAG, trunk (confusingly), team) bundles several physical links between two devices into one logical link. The bundle appears to spanning tree and routing as a single link (so STP does not block the members), carries more aggregate bandwidth than one member, and survives member failures (traffic rehashes onto remaining members).

**LACP** (Link Aggregation Control Protocol) negotiates and maintains the bundle:

- Each end is an **actor**; it advertises to its **partner** a system ID (system priority + MAC), a port key, port priority and state flags, in LACPDUs sent to the slow-protocols multicast address 01:80:C2:00:00:02.
- **Active** mode sends LACPDUs proactively; **passive** only responds. At least one side must be active. (Static "on" mode creates a bundle without protocol and is dangerous: a miswired or misconfigured member silently blackholes traffic.)
- A member joins the aggregate if its partner presents a consistent system ID and key, and the ports have matching speed/duplex/VLAN configuration. The side with the lower system priority decides which members are active when limits (maximum 8 active, up to 16 members with hot standby) are exceeded.
- **Timers**: slow (30 s hellos, 90 s timeout) or fast (1 s hellos, 3 s timeout). LACP detects failures that link-state alone cannot (a switch that is up but not forwarding on that port, mis-patching, a unidirectional fibre fault), so it tells the OS to rehash away from a failed member quickly. Use fast timers for servers.
- Collecting and distributing states: frames are only sent/accepted on members in "collecting/distributing" state after negotiation, preventing traffic from being sent into a bundle the other side has not accepted.

The hash applies independently in each direction: the switch chooses the member for server-bound traffic with its own hash, and the host chooses for switch-bound traffic with its own policy. A flow can leave on member 1 and return on member 2; this is normal and OK as long as both are in the bundle.

## 3. Linux bonding

The kernel `bonding` driver creates a bond device (`bond0`) that enslaves physical NICs.

| Mode | Name | Behaviour | Switch support needed |
|---|---|---|---|
| 0 | `balance-rr` | Round robin per packet | Static bundle; risk of reordering |
| 1 | `active-backup` | One active member; failover on link loss; MAC may move (`fail_over_mac`) | None (works with any switches, even two independent ones) |
| 2 | `balance-xor` | Hash of src/dst MAC (or per `xmit_hash_policy`) | Static bundle |
| 3 | `broadcast` | Transmit on all members | Rare, fault-tolerant |
| 4 | `802.3ad` | **LACP** | LACP on the switch; same speed/duplex |
| 5 | `balance-tlb` | Adaptive transmit load balancing, receives on one | None |
| 6 | `balance-alb` | Adaptive TLB plus receive balancing via ARP replies | None |

For servers, modes 1 (active-backup) and 4 (LACP) are the practical choices: active-backup when the two NICs go to two unrelated switches (no MLAG), LACP when they go to one switch or to an MLAG pair.

Key parameters:

- `miimon=100` (ms): link-state polling interval; `arp_interval`/`arp_ip_target` for ARP-probe monitoring (detects upstream failures that carrier cannot, but conflicts with LACP).
- `lacp_rate=fast|slow`, `ad_select`, `min_links` (minimum active members before the bond is considered up, so a bond doesn't stay "up" with too little bandwidth), `updelay`/`downdelay` (damping).
- `xmit_hash_policy`: `layer2` (src/dst MAC, default), `layer2+3` (adds IP), `layer3+4` (IP + ports; best spread for routed traffic though it may reorder fragments), `encap2+3`/`encap3+4` (hash on inner headers for tunnelled traffic), `vlan+srcmac`. The default is a poor choice for traffic going to one gateway.
- `primary` (preferred active member in active-backup), `fail_over_mac`, `arp_validate`.

```bash
# Netplan (Ubuntu)
network:
  version: 2
  ethernets: { ens1f0: {}, ens1f1: {} }
  bonds:
    bond0:
      interfaces: [ens1f0, ens1f1]
      parameters:
        mode: 802.3ad
        lacp-rate: fast
        mii-monitor-interval: 100
        transmit-hash-policy: layer3+4
        min-links: 1
      addresses: [10.30.4.45/24]
      mtu: 9000

# Runtime inspection
cat /proc/net/bonding/bond0              # mode, hash policy, per-slave state, LACP partner info, aggregator IDs
ip -d link show bond0 ; ip -s link show bond0
ethtool -i bond0 ; ethtool ens1f0        # speed/duplex must match across members
sudo nmcli con add type bond ifname bond0 bond.options "mode=802.3ad,miimon=100,lacp_rate=fast,xmit_hash_policy=layer3+4"
sudo nmcli con add type ethernet ifname ens1f0 master bond0
```

In `/proc/net/bonding/bond0` look for: `Aggregator ID` equal for all members (members in different aggregators means the partner presents different keys/system IDs, e.g., a miscabled port), `Partner Mac Address` (should be the switch/MLAG virtual MAC; `00:00:00:00:00:00` means no LACP partner), `MII Status: up`, `Actor/Partner Churn State` (non-zero churn means flapping negotiation), and per-slave failure counts. Verify balance by watching per-member counters during a multi-flow test (`ip -s link`, `sar -n DEV`, `iperf3 -P 16`).

Teaming (`teamd`) and OVS bonds are alternatives; modern distributions are returning to bonding. SR-IOV and DPDK have their own bonding approaches (VF LAGs, mlx5 "LAG" in hardware with `devlink`); GPU servers with ConnectX NICs may offload LAG to the NIC (`mlx5` hardware LAG) so RDMA traffic survives a bond; check your NIC documentation.

**Bonding and RDMA/GPU fabrics.** Do not bond the rails of a compute fabric: NCCL expects one NIC per GPU rail, with independent paths for each (and failover handled in the collective library or by the fabric's adaptive routing). Bond only the management, front-end and storage connections, and keep back-end rails independent so that the rail-optimised topology (chapter 2.18) is preserved.

## 4. Multi-chassis link aggregation (MLAG, vPC, EVPN multihoming)

LACP bundles terminate on one switch, so the switch is a single point of failure for the server (and for any upgrade). **MLAG** lets a bundle's members connect to *two* switches which present themselves to the server (and to STP and LACP) as one logical switch: Cisco vPC, Arista MLAG, Juniper MC-LAG/ESI-LAG, Cumulus/NVIDIA MLAG (CLAG), Dell VLT. Implementation: a proprietary control protocol and **peer link** between the two switches synchronise MAC tables, LACP state and ARP/ND; both use a common virtual system ID so the server sees one LACP partner; a keepalive path (often via the management network) detects peer failure to avoid split brain.

Properties and cautions:

- Server-facing: active/active forwarding over both switches; an entire switch can fail or be upgraded one at a time while servers stay connected.
- Complexity and failure modes: peer-link failure (split brain protection rules disable one side's ports), inconsistent configuration between peers (type-1/type-2 consistency errors), orphan ports (single-attached devices lose connectivity when the peer link or one peer fails), larger blast radius for software bugs, and difficult upgrades (ISSU limits).
- Proprietary: there is no multivendor MLAG; both peers must be the same product line.
- The standards-based replacement is **EVPN multihoming (ESI-LAG, RFC 7432)**: BGP EVPN type-1/type-4 routes coordinate a shared Ethernet Segment Identifier across leaves, giving active-active multihoming without a peer link (chapter 2.17).
- Design direction: shrink L2 domains and run **routed** connections to servers (BGP on the host or ECMP with `/32` loopbacks), which needs no MLAG at all. Many hyperscale and AI designs have dropped MLAG in favour of L3 to the host or to the leaf, keeping MLAG only for legacy/appliance attachment and management networks.

A typical GPU-server attachment table:

| Network | Typical attachment | Why |
|---|---|---|
| BMC / OOB management | Single 1G to an OOB switch (sometimes redundant) | Rarely needs bandwidth; isolated |
| In-band management / SSH | Bond (active-backup or LACP) to a leaf pair | Survives switch loss |
| Front-end / inference / client | LACP to MLAG pair or routed uplinks | Resilience + bandwidth |
| Storage | LACP or independent NICs with multipath (NFS nconnect, Lustre multi-rail, NVMe-oF multipath) | Higher storage throughput |
| Compute fabric (IB/RoCE) | One NIC per GPU, no bonding, rail-optimised leaves | Deterministic collectives |

## 5. Routed parallel links: ECMP

When parallel paths are **routed**, routing protocols install multiple equal-cost next hops for a prefix (chapter 2.13). Example: A can reach D through three different paths of cost 10 (A-B-D, A-D, A-C-D); all three go into the forwarding table, and a hash chooses one per flow. Unlike link aggregation, ECMP paths need not connect the same two devices, and no negotiation protocol is needed beyond the routing protocol itself.

Details:

- **Hash fields**: typically src/dst IP, protocol, src/dst port (the 5-tuple), sometimes the IPv6 flow label or inner headers for tunnels. The same hash function applies at every router, so seeds/fields differ per tier to avoid polarization.
- **Resilient (consistent) hashing**: with plain `hash mod N`, removing one next hop changes N and remaps almost all flows, reordering and disrupting them. Resilient hashing allocates a fixed table of buckets mapped to next hops so only the flows on the failed hop are reassigned; essential for stateful backends (load balancers, anycast services, firewalls) and desirable for TCP.
- **Elephant flows and flowlets**: standard ECMP cannot split one flow. Techniques: *flowlet switching* (re-hash when a gap in the flow exceeds the path-delay difference, so reordering is impossible), *packet spraying* with reordering-tolerant endpoints, *adaptive routing* (the switch picks the least-loaded path per packet or flowlet, as in InfiniBand AR and NVIDIA Spectrum-X for Ethernet), and *host-side multipathing* (multiple connections/QPs with varied ports, which is what NCCL and MPTCP do). These are central to AI fabric performance (chapter 2.19, Part 11).
- **Linux**: `ip route` multipath (chapter 2.5), `fib_multipath_hash_policy`, `ip route get ... ` with different source ports (`ip route get 10.200.0.1 ipproto tcp sport 40000 dport 443`) to see which next hop a given flow uses; `ethtool -N`/RSS hash functions (`ethtool -x`, `-X`) do the analogous job inside the NIC across receive queues.
- **Verifying distribution**: counters per interface on the switch (`show interface counters`), sFlow/IPFIX sampling, `ip -s link`, and synthetic tests with many flows of varied ports. A fabric with 8 spine uplinks should show nearly equal utilisation under many flows, and imbalance under few large flows is expected unless adaptive routing is on.

## 6. Cluster roles and networks (a practical map)

HPC/AI clusters have a stable set of node roles and networks that determine where aggregation, ECMP and bonding appear.

**Nodes.** *Compute nodes* (the counting field; keep them homogeneous and lean: sshd, network file-system client, monitoring agent, the scheduler daemon; minimise services such as cron, mail or NetworkManager where practical); *control/management node(s)* (cluster manager, scheduler controller, provisioning, databases; have at least two for resilience); *login/access nodes* (user-facing; strictly resource-limited because IDE remote plugins and heavy interactive use can paralyse them); *service nodes* (compilation, data-copy/transfer, licence servers, pre/post-processing with large RAM, visualisation with GPUs, storage servers, backup, authentication, logging, monitoring). Do not combine compute and service roles (for example an NFS server on a compute node): job interference and failures follow.

**Networks.** (1) A **compute/communication network** (InfiniBand or high-speed Ethernet/RoCE) for MPI/NCCL traffic: the most demanding in bandwidth and latency; (2) a **control/service network** (Ethernet) for SSH, scheduler traffic, provisioning, monitoring; (3) **management network** (IPMI/BMC/Redfish, out-of-band); (4) a **storage network** (often shared with or separated from compute); (5) the **external network** for users, with compute and storage nodes typically having no direct Internet access (NAT or proxies, chapter 2.9). Compare technologies by throughput *and* latency: Gigabit Ethernet roughly 30 to 100 µs, 10G Ethernet single-digit-to-tens of µs MPI latency, 100G RoCE/Ethernet and InfiniBand about 1 to 3 µs MPI latency, with real application throughput typically 1.5 to 2 times below the peak figure. Table figures vary by generation; re-measure with `ib_write_bw`/`ib_write_lat`/`osu_latency` for your hardware.

**Topologies** (details in chapter 2.18): *tree/star* (Ethernet; STP would block redundant links), *fat tree* (multiple root switches each connected to every switch at the next level; InfiniBand's workhorse; uses duplicate links, tolerant of switch failures except at the leaf), *hypercube* (N-dimensional, at most N hops, complex cabling), *multidimensional torus* (each dimension closes into a ring; max hops = sum of half-dimensions; used in some supercomputers), *dragonfly/dragonfly+* (all-to-all within groups, groups connected globally; reduces ports and cables while keeping hop counts low). Topology bottlenecks cancel fast links (two 1G switches joined by a single link); parallel inter-switch links must be aggregated consistently with compatible standards on both ends (EtherChannel/bonding/trunking implementations differ between vendors).

Storage hardware attachment (DAS, NAS, SAN, RAID levels, multipath) is covered in the storage part of the handbook; NUMA and CPU pinning in chapters 1.18 and 1.28.

## 7. Failure behaviour and troubleshooting

| Symptom | Likely cause | Check |
|---|---|---|
| One member carries all traffic | Hash policy too coarse (layer2 to one gateway), few flows, polarization | `xmit_hash_policy`, per-member counters, test with `-P 16` |
| Bond up but no connectivity | LACP mismatch (static on one side), wrong VLAN on member, MLAG peer inconsistency | `/proc/net/bonding/bond0` partner MAC, switch `show lacp`, `tcpdump -ni ens1f0 ether proto 0x8809` |
| Bond flaps | Bad optics/cable, LACP fast timers on a busy CPU, `miimon` too aggressive, link negotiation | `dmesg`, `ethtool -S`, churn counters |
| Throughput half of expected | Single flow pinned to one member; members at different speeds; MTU mismatch | `iperf3 -P`, `ethtool` speed, MTU on all hops |
| Packet reordering | `balance-rr`, ECMP flaps, per-packet spraying without tolerant endpoints | `nstat \| grep -i reorder`, `ss -ti` |
| Traffic blackholed after a switch failure | No `min_links`, MLAG split brain, wrong failover mode (ARP monitor with LACP), hash not updated | switch logs, keepalive path, `lacp_rate` |
| Some destinations unreachable via ECMP | One path blackholed (missing route/ACL/MTU), no BFD, sticky hash hides the fault | probe each path with varied source ports; BFD; `traceroute -T` with ports; paris-traceroute |
| After upgrade, flows shuffle | Plain modulo hashing remapped all flows | enable resilient/consistent hashing |

Procedure for host bonds: (1) physical (`ethtool`, optics, cabling, LLDP neighbours), (2) bond state (`/proc/net/bonding`), (3) switch-side LACP/MLAG state, (4) hash and flow distribution, (5) MTU/VLAN consistency, (6) failover test by downing each member and measuring recovery time with a continuous ping (`ping -i 0.1`) or `iperf3` with interval reporting.

## 8. Lab: build and break bonds and ECMP (untested)

1. **LACP in software**: in two namespaces (or two VMs) create a bond on each side with two veth pairs between them (`mode=802.3ad`); inspect `/proc/net/bonding`, see the partner MAC, then set one side to `active-backup` or remove LACP to see negotiation fail.
2. **Hashing**: with `xmit_hash_policy=layer2`, run `iperf3 -P 8`; note one member carries everything when src/dst MACs are fixed; switch to `layer3+4` and watch the spread (`ip -s link`, `watch -d`); use different destination ports to show the hash effect; repeat with a single flow.
3. **Failover**: bring a member down (`ip link set veth1 down`), measure packet loss with a fast ping; adjust `miimon`/`lacp_rate fast`; test `min_links`.
4. **Round-robin reordering**: set `mode=balance-rr` and add `tc netem delay 5ms` on one member only; capture reordering (`nstat`, tcpdump) and the throughput collapse versus a hashed mode.
5. **ECMP**: use namespaces `a`, `r1`, `r2`, `b` with two equal-cost paths from `a` to `b`; add a multipath route; test distribution with `iperf3 -P 16`; query the path for different ports with `ip route get ... sport ... dport ...`; set `fib_multipath_hash_policy` 0, then 1; remove a next hop and count how many flows moved; compare with FRR's ECMP in a containerlab leaf-spine (chapter 2.27).
6. **Elephant flows**: run two large flows with engineered 5-tuples that collide (search ports until `ip route get` shows the same next hop) and observe 50% utilisation per path; discuss flowlet/adaptive routing.
7. **MLAG design exercise (paper)**: draw a rack with dual-homed servers and an MLAG pair; list the failure cases (peer link, keepalive, orphan port, single switch reboot) and expected behaviour; compare with a routed (BGP-to-host) alternative.
8. **Clean up**.

Mark tested only after execution.

## 9. Common mistakes

- Expecting a bond to speed up a single TCP stream (it won't); testing with one flow and concluding the bond is broken.
- Leaving the default `layer2` hash policy for routed traffic; ignoring polarization across tiers.
- Static (non-LACP) bundles; mismatched LACP modes; members of different speeds in one bond.
- Using `balance-rr` for TCP traffic across an unknown network.
- Bonding compute-fabric rails, or placing two rails on one switch failure domain without understanding the topology.
- MLAG without a tested peer-link and keepalive design; forgetting orphan ports.
- Plain modulo ECMP behind stateful services (rehash storms on every change).
- Never testing failover and recovery time.

## 10. Interview angles

- "Why doesn't link aggregation scale linearly? How would you improve balance?"
- "Difference between LACP and a static port-channel; why prefer LACP?"
- "Which bonding mode would you use with one switch? With two independent switches? With an MLAG pair?"
- "What is MLAG? What can go wrong? What are the alternatives?"
- "Explain ECMP, hashing fields and polarization. What is resilient hashing?"
- "An elephant flow saturates one link while others are idle. What can you do?" (Entropy, multiple QPs/streams, flowlets, adaptive routing, flow-aware load balancing.)
- "How is a GPU server's networking attached and why are the compute rails not bonded?"
- "How would you test a bond's failover?"

## 11. Checkpoint questions (30)

1. Why isn't per-packet round robin typically used across links? **A:** Reordering.
2. What is flow hashing? **A:** Mapping a flow's constant fields to one member link.
3. Why are hash functions good for load sharing? **A:** Deterministic per flow and evenly spread across buckets.
4. What are elephant and mouse flows? **A:** Large long-lived versus small short flows.
5. How many links does a single TCP flow use in a bond? **A:** One.
6. Which hash fields help when few hosts talk to one server? **A:** L3 + L4 (IPs and ports).
7. What is hash polarization? **A:** Successive tiers choosing the same path due to identical hashing, leaving others idle.
8. What standard defines LACP? **A:** IEEE 802.1AX (formerly 802.3ad).
9. Which multicast address do LACPDUs use? **A:** 01:80:C2:00:00:02 (slow protocols).
10. Active versus passive LACP? **A:** Active initiates LACPDUs; passive only replies.
11. Fast versus slow LACP timers? **A:** 1 s versus 30 s hellos.
12. Why LACP rather than static? **A:** Detects misconfiguration and failures; prevents blackholing.
13. Which bonding mode is LACP? **A:** Mode 4, `802.3ad`.
14. Which mode needs no switch support and survives two separate switches? **A:** Mode 1 active-backup.
15. What does `xmit_hash_policy=layer3+4` hash? **A:** IPs and L4 ports.
16. What does `min_links` do? **A:** Keeps the bond down if fewer than N members are active.
17. Where do you see LACP partner info in Linux? **A:** `/proc/net/bonding/<bond>`.
18. What does a partner MAC of zeros mean? **A:** No LACP partner negotiated.
19. What is MLAG? **A:** A bundle spanning two switches that act as one logical switch for LACP/STP.
20. What are MLAG failure risks? **A:** Peer-link/keepalive failure, split brain, inconsistent configs, orphan ports.
21. What is EVPN multihoming? **A:** Standards-based active-active multi-switch attachment using BGP EVPN ESIs.
22. Why prefer routed designs? **A:** Smaller failure domains, all links active, no proprietary MLAG.
23. How does ECMP differ from link aggregation? **A:** Routed paths need not be between the same two devices and need no negotiation protocol.
24. What is resilient hashing? **A:** Fixed bucket table so only affected flows move when members change.
25. What is a flowlet? **A:** A burst of packets separated by a gap large enough to reroute without reordering.
26. What is adaptive routing? **A:** Switch picks less-loaded paths dynamically per packet/flowlet.
27. Why should compute rails not be bonded? **A:** NCCL expects independent rails; bonding breaks rail-optimised paths.
28. What does RoCE do to help ECMP? **A:** Varies the UDP source port per QP.
29. How do you see which ECMP next hop a flow uses? **A:** `ip route get ... ipproto tcp sport X dport Y`.
30. Name four node roles in an HPC cluster. **A:** Compute, control/management, login/access, service (storage, licence, etc.).

## 12. Sources and review notes

**Written in original words.** Principal sources:

- Russ White and Jeff Tantsura (with co-authors), *Computer Networking Problems and Solutions*, chapter 7: equal cost multipath, link aggregation, hash algorithms, LACP, multichassis link aggregation, routed parallel links.
- Sergey Zhumatiy, *Supercomputers for Linux SysAdmins*, chapter 4: control, compute, login and service nodes; service/communication/storage networks; network technology comparison; topologies (tree, fat tree, hypercube, torus, dragonfly).
- Linux bonding, netplan, MLAG/EVPN multihoming, resilient hashing and AI-fabric notes are the author's synthesis from the kernel bonding documentation, IEEE 802.1AX, RFC 7432 and vendor documentation.

**Flagged for verification before publishing:** the latency/throughput table values (hardware-generation dependent), bonding parameter availability per kernel, vendor MLAG feature names and limits, NIC hardware-LAG support, and adaptive routing product details; all labs are **untested**.
