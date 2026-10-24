---
id: "c02-13"
title: "2.13 IP routing: static routes, dynamic routing and convergence"
sidebar_label: "2.13 IP routing: static routes, dynamic routing and convergence"
sidebar_position: 13
description: "Static routes, dynamic routing algorithms, loop-free paths and convergence"
status: "drafted"
tier: "0"
level: "I"
lab_venue: "GCP / GKE"
---

# 2.13 IP routing: static routes, dynamic routing and convergence

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 0 |
| Lab venue | Linux VM with network namespaces and FRR (or containerlab) |
| Part | Part 2: Networking, from first principles to AI fabrics |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

Every large AI fabric is routed. Leaf-spine data centres run BGP or OSPF between switches (and increasingly to the host), so that every link is active under ECMP and a failure is absorbed in milliseconds rather than the tens of seconds of spanning tree. To operate, design or debug such a fabric you need to know how routers *learn* where things are, how they avoid forwarding loops, how they notice failures and how quickly they converge, what happens when two routing systems are stitched together (redistribution), and which behaviour is protocol-specific and which is fundamental. This chapter is the theory chapter for routing: it explains the algorithms (distance vector, link state, path vector), the guarantees they give (loop freedom), failure detection (polling, event-driven, BFD), change distribution (flooding, hop by hop, centralised stores), fast-reroute techniques (loop-free alternates, disjoint paths) and the practical decisions (static versus dynamic, administrative distance, redistribution). The protocol-specific chapters (OSPF/IS-IS in 2.14, BGP in 2.15 and 2.16) build on it.

## Prerequisites and outcomes

You should know host routing and longest-prefix match (2.5), neighbour discovery and the control/data plane distinction (2.11).

After this chapter you can:

- Decide between static and dynamic routing and configure static routes, floating static routes and default routes on Linux and in FRR.
- Explain the control plane's job: learn topology, learn reachable destinations, compute loop-free paths, install forwarding state, react to change.
- Contrast reactive and proactive reachability learning, and the ways reachability is advertised (flooding, hop-by-hop, centralised).
- Explain distance-vector (Bellman-Ford) routing, count-to-infinity, split horizon, poison reverse and DUAL's feasibility condition.
- Explain link-state routing, Dijkstra's algorithm, partial and incremental SPF, areas and hierarchy.
- Explain path-vector routing and why BGP uses it.
- Explain loop-free paths: trees, loop-free alternates, remote LFAs, P/Q space, disjoint paths (Suurballe), maximally redundant trees.
- Explain how topology changes are detected (polling, event-driven, BFD) and distributed (flooding, hop-by-hop, central store) and the consistency trade-offs.
- Explain route redistribution: metric translation, routing loops, tags and filters, administrative distance.
- Reason about convergence time and tune it.

## 1. Static versus dynamic routing

**Static routes** are configured by hand (or by automation): `ip route add 10.30.0.0/16 via 10.20.0.254`. They are simple, deterministic, consume no CPU or bandwidth, and are a good fit for stub networks (a leaf with one uplink, a default route out of a site), for management networks, and for pinning specific flows. Their weakness is that they do not react: if the next hop fails the route stays installed and traffic blackholes, they do not scale (O(n^2) touch points for n networks), and errors are discovered by outage. Mitigations: static routes tracked by BFD/IP SLA so they are withdrawn when the next hop is unreachable, **floating static routes** with a higher administrative distance/metric as a backup, and configuration generated and verified by automation.

**Dynamic routing** uses a routing protocol so routers exchange reachability and adapt to failures: **IGPs** inside one administrative domain (RIP, OSPF, IS-IS, EIGRP) and the **EGP** BGP between domains and, with eBGP, inside modern data centres. Dynamic routing scales, converges after failure, supports ECMP and policy, but adds protocol complexity, convergence behaviour to understand, and attack surface (authenticate sessions, filter routes).

**Administrative distance (AD) / route preference.** When several sources (connected, static, OSPF, BGP, ...) offer a route to the same prefix, the router prefers the source with the lowest AD before comparing metrics (metrics from different protocols are not comparable). Typical defaults (vendor-specific): connected 0, static 1, eBGP 20, EIGRP 90, OSPF 110, IS-IS 115, RIP 120, iBGP 200 (Cisco-style); Linux/FRR `proto` and `metric` fields serve a similar role, and FRR's zebra applies distance values when several daemons offer the same prefix. A floating static route has AD 200+ so it only appears when the dynamic route disappears.

```bash
# Linux static and floating static
ip route add 10.30.0.0/16 via 10.20.0.254 metric 100
ip route add 10.30.0.0/16 via 10.20.0.253 metric 200       # backup (only used when the first is gone)
# FRR (zebra) static route and a floating backup, with BFD tracking
vtysh -c 'conf t' -c 'ip route 10.30.0.0/16 10.20.0.254 bfd' -c 'ip route 10.30.0.0/16 10.20.0.253 200'
```

A routing protocol is only as good as the underlying questions each control plane must answer. Sections 2 to 7 take them in turn.

## 2. What a control plane does

The data plane forwards packets using tables; the **control plane** builds those tables. It must:

1. **Learn the topology**: who are my neighbours and over which links (chapter 2.11 sections on neighbour detection and two-way connectivity).
2. **Learn reachable destinations**: which hosts, prefixes and services are attached where.
3. **Advertise** the information to other nodes, reliably, so everyone's view converges.
4. **Compute loop-free paths** (and optionally multiple paths and backups).
5. **Install** the results as forwarding state.
6. **React to change** (detect, distribute, recompute, reinstall) as quickly and safely as possible.

### Learning reachable destinations

- **Reactively** (on demand): when a router lacks a path it asks. Examples: ARP/ND (ask who owns an address), a controller/map-server lookup (LISP-style or SDN: the router queries a central controller that learned about every attached host), source-routing **explorer** packets (flood a probe that records the path; the destination or source then uses the recorded path as a source route). Reactive systems keep little state but add latency to the first packet and make the lookup service critical.
- **Proactively**: reachability is distributed as soon as it is known, so every node has what it needs before traffic arrives. Everything in this chapter is mainly proactive. The challenge is reliable, consistent distribution: a dropped update can create permanent loops or blackholes. Mechanisms: **sequence numbers** on packets or per-item NLRI with acknowledgements, **database descriptions** (lists or ranges of sequence numbers, sequence numbers paired with hashes so receivers can verify content, or a hash over a block of entries) exchanged on neighbour up and periodically so neighbours detect and repair missing or corrupted entries (OSPF database exchange and IS-IS CSNP/PSNP behave this way); and **keepalives** so that routes learned from a neighbour remain valid only while that neighbour is alive.
- **Hybrid**: a proactive control plane for infrastructure with reactive learning for hosts (e.g. EVPN advertises MAC/IP bindings when learned; ARP is reactive on the segment).

### Distribution models

| Model | How information spreads | Examples |
|---|---|---|
| **Flooding** | Each node forwards new information to all neighbours except the source, with sequence numbers to stop duplicates | OSPF LSAs, IS-IS LSPs |
| **Hop by hop** | Each node computes its own best result then tells neighbours only that result (summary of what it uses) | RIP, EIGRP, BGP |
| **Centralised store** | Nodes publish to and read from a database/controller that everyone reaches | SDN controllers, etcd/Kubernetes API, route reflectors (partly), LISP map servers |

## 3. Loop-free paths: trees, shortest paths and the algorithms

A path is loop-free if no packet can visit the same node twice. The simplest loop-free structure is a **tree** (spanning tree: the network is pruned so there is exactly one path between any two nodes); the cost is that redundant links are unused. Routing algorithms instead compute a **shortest-path tree rooted at each destination (or source)** over the full graph, which yields loop-free forwarding with all links usable by some destination.

Packets loop when two routers have inconsistent views of the topology at the same moment: A believes the best path to X is via B, and B (not yet updated) believes the best path is via A. Different algorithm families avoid or limit this differently.

### Distance vector (Bellman-Ford)

Each router knows its directly attached destinations and tells its neighbours its *distance* (metric) to every destination. Each router picks, for each destination, the neighbour that offers the lowest total (neighbour's advertised distance + cost of the link to that neighbour), and then advertises its own resulting distances. Information moves hop by hop; routers know only distance and next hop, not the topology. Pros: simple, low state, low CPU. Cons: slow convergence; **count to infinity** after a failure.

Count-to-infinity example: A–B–C in a line, and C attaches network N. B learns N at distance 1 from C, A learns N at 2 via B. If C's link to N fails, C removes N; before C's withdrawal reaches B, B hears from A "N at distance 2" (learned from B itself) and concludes N is reachable via A at 3; then A updates to 4 via B, and so on, counting upward until the metric reaches the protocol's "infinity" (16 in RIP). Meanwhile packets loop between A and B. Remedies:

- **Split horizon**: never advertise a route back out the interface you learned it from. **Poison reverse**: advertise it back with infinite metric. They stop two-node loops, but not longer loops.
- **Triggered updates**, **hold-down timers** (ignore worse information for a while after a withdrawal) and a small maximum diameter (RIP's 15 hops) are blunt tools.
- **DUAL (Diffusing Update Algorithm, Garcia-Luna-Aceves; EIGRP)** keeps distance-vector's low state but guarantees loop freedom at every instant. Key idea: for each destination a router tracks its *feasible distance* (FD, the best metric it has) and, for each neighbour, that neighbour's *reported distance* (RD). A neighbour is a **feasible successor** (a safe backup) if its RD is **less than my FD**: it is strictly closer to the destination than I am, so its path cannot go through me. If the successor fails and a feasible successor exists, switch to it instantly (local computation, no loops). If none exists the router goes **active**: it sends queries to its neighbours (a *diffusing computation*), waits for replies, and only then chooses a new path. This is why EIGRP converges in milliseconds when a feasible successor exists, but can suffer "stuck in active" if replies never return.
- **Path vector** (below) avoids loops by carrying the whole path.

Used today: RIP (obsolete, but a clear teaching case), EIGRP (Cisco/open since 2013), and the distance-vector *mechanics* inside BGP's best-path selection.

### Link state (Dijkstra)

Each router describes its own links (neighbours and costs) in a **link-state advertisement** and *floods* it to every router in the area, so all routers hold the same **link-state database** (LSDB) describing the whole topology. Each router then independently runs **Dijkstra's shortest path first (SPF)** with itself as root:

1. Start with the root in the "tree" set at cost 0, all else unknown (infinite).
2. Repeatedly take the closest node not yet in the tree (using a priority queue), add it, and relax its neighbours: if cost(root→n) + link cost to m < current cost to m, update m and record the first hop.
3. At the end each destination has a cost and a next hop; install the lowest-cost next hops (all equal-cost ones for ECMP).

Because every router computes from an identical database, the result is consistent and loop-free **once the databases are synchronised**; while a change is still flooding, routers can briefly disagree (micro-loops, section 6). Properties: fast convergence (flood plus SPF in tens to hundreds of ms), full topology knowledge (enables traffic engineering, fast reroute computation, and tools like LFA), but higher memory and CPU, and a need for **hierarchy** (areas/levels) in large networks to bound the LSDB and flooding scope. Optimisations: **partial SPF** (when only a leaf prefix changes, don't recompute the tree), **incremental SPF** (update only the part of the tree affected by a link change), SPF throttling/backoff timers (to avoid churn), and LSA/LSP pacing. OSPF and IS-IS are link-state (chapter 2.14). Data-centre variants of link state (e.g. OpenFabric, RIFT) adapt flooding to Clos fabrics.

### Path vector

A path-vector protocol advertises, for each destination, the **sequence of domains (AS numbers) the route has traversed** rather than just a metric. A router rejects any advertisement whose path already contains its own identifier: loops are impossible by construction. Policy is easy (prefer or reject paths through particular ASes), and the path is a human-readable record of how the route got here. Cost: slow convergence on failure ("path exploration": routers try successively longer alternatives), and more state per route. This is **BGP** (chapters 2.15 and 2.16); in data-centre eBGP with the same ASN-per-tier plans (and "allowas-in" or per-rack ASNs), the loop-prevention logic still shapes the design.

### Comparing families

| | Distance vector | Link state | Path vector |
|---|---|---|---|
| Knows | Distances and next hops | Whole topology | Paths (AS lists) |
| State per router | Low | High (LSDB) | Per-prefix per-path |
| Loop avoidance | Split horizon / DUAL | Consistent database; SPF | Own ID in path |
| Convergence | Slower (RIP) / fast (DUAL) | Fast | Slow without tuning |
| Policy | Limited | Limited | Rich |
| Examples | RIP, EIGRP | OSPF, IS-IS | BGP |

## 4. Alternate paths and fast reroute

Convergence after a failure takes time: detect, flood/advertise, recompute, update the FIB. To cut loss during that window, routers precompute **backup next hops** locally and switch instantly when the primary fails (**fast reroute**, sub-50 ms).

- **Loop-free alternate (LFA)**: for destination D, a neighbour N is a safe backup if N's own shortest path to D does not go back through me: *dist(N,D) < dist(N,me) + dist(me,D)* (the loop-free condition). The same idea as DUAL's feasibility condition, computed from the link-state database. LFA is simple but coverage is topology-dependent (full coverage in some rings/triangles, none in a simple ring of equal links).
- **The waterfall (continental divide) model** explains coverage graphically: think of the shortest-path tree toward D as water flowing downhill to D; a neighbour is a loop-free alternate only if it is "on the other side of the ridge", i.e., its flow reaches D without passing through me.
- **P space and Q space.** For a failed link, **P-space** is the set of nodes I can still reach by my shortest paths without using the failed link; **Q-space** is the set of nodes that can reach the destination's side without using it. If a node exists in both, a packet can be tunnelled there (**remote LFA, rLFA**) and from it continue normally to D: the tunnel (MPLS/LDP, SR) jumps over the unsafe region. Extending the idea to guarantee 100% coverage using the post-convergence path with segment-routing label stacks is **TI-LFA** (topology-independent LFA).
- **Disjoint paths**: for protection or multi-path load sharing, find two paths that share no link/node. Naively taking the shortest path then removing its links can fail even when disjoint pairs exist (a "trap"). **Suurballe's algorithm** finds the minimum-total-cost pair of link-disjoint paths in a two-connected network (compute shortest-path tree, reweight edges, remove path edges reversing direction, run again, combine). **Maximally redundant trees (MRT)** compute two spanning trees such that for any failure at least one tree still reaches every node, giving a topology-independent fast-reroute scheme. A *two-connected* network is one where no single link or node failure disconnects any node; design goal for fabrics.
- **ECMP as protection**: in Clos fabrics with many equal-cost paths, "fast reroute" is simply removing a failed next hop from the ECMP group in the forwarding hardware, which is hardware-fast and needs no fancy algorithm (cost: the traffic of that hop shifts onto others; resilient hashing limits flow reshuffling, chapter 2.12).

## 5. Detecting and reacting to topology changes

Reacting has three stages: detect the change, distribute information about it, and recompute/install.

### Detection

- **Polling (hello/dead-timer based)**: neighbours exchange periodic hellos; failure is declared after missing N in a row (OSPF default hello 10 s/dead 40 s; BGP keepalive 60 s/hold 180 s; tuned to seconds or sub-second in data centres). Cost: detection time is bounded below by the interval × N, and shortening intervals multiplies CPU load.
- **Event-driven**: the hardware or lower layer reports the failure directly (loss of light/carrier, interface down interrupt, Ethernet OAM, SONET alarms). Fast (microseconds to milliseconds) but only sees *local* link-state; it misses failures that don't drop carrier (remote switch crashed, forwarding plane stuck, a misconfiguration, a unidirectional fibre problem, a failure behind a transparent optical or L2 device). Physical-layer flaps also need **dampening** so a flapping link doesn't churn the network.
- **Comparing**: event-driven is faster but less complete; polling is universal but slower. Use both, with BFD as the fast general-purpose poll.
- **Bidirectional Forwarding Detection (BFD, RFC 5880)** is a lightweight hello protocol independent of any routing protocol, sent at 50 to 300 ms intervals (often offloaded to line cards/ASIC) over UDP (3784 single hop, 4784 multihop). It detects failure of the *forwarding path* between two endpoints in under a second and reports to clients (OSPF, IS-IS, BGP, static routes, LAGs) that tear down the adjacency at once, triggering reconvergence. Modes: asynchronous (continuous packets), with optional echo mode; sessions must be bidirectionally verified (the packets themselves carry what the sender sees: this is the two-way check from chapter 2.11). Tuning: aggressive timers and many sessions load control CPUs; flapping on congestion can cause outages if BFD packets are dropped (prioritise them in QoS).

```bash
# FRR example: BFD with BGP and OSPF
router bgp 65101
 neighbor 10.0.0.1 remote-as 65000
 neighbor 10.0.0.1 bfd
interface eth0
 ip ospf bfd
bfd
 peer 10.0.0.1
  receive-interval 100
  transmit-interval 100
  detect-multiplier 3
vtysh -c 'show bfd peers'
```

### Distributing change

Whichever model (flooding, hop by hop, centralised) distributes the change, the design questions are the same: reliability (retransmit until acknowledged), ordering and staleness (sequence numbers, timestamps), scope (flood only within the area or level), and the rate (throttle and batch to avoid storms). **Flooding** is robust and fast but every node processes every change; a flapping link in a huge flat domain consumes everyone's CPU, which is why hierarchy and flooding reduction exist. **Hop by hop** limits scope (a node only tells neighbours about its best path), at the price of path exploration. A **centralised store** gives a single consistent view and simple logic, but its failure or partition is a global problem and every node needs a reliable path *to* it (a bootstrapping problem).

**Consistency, accessibility, partitionability.** A routing system is a distributed database, so it faces the usual trade-off (CAP-like): during a partition you can keep forwarding with possibly stale data (available but inconsistent, risking loops/blackholes) or stop forwarding until consistent. Link-state IGPs favour availability with eventual consistency and rely on short convergence windows; centralised controllers favour consistency and need redundancy (clustered controllers, fallback to local routing if the controller is unreachable). Practical consequences: design for a fallback when the controller dies, keep control traffic prioritised, and test partitions.

### Convergence timeline

Time to restore forwarding after a link failure = detection + origination (hold-down/throttle) + propagation/flooding + computation + FIB installation (hardware programming, sometimes the largest term at scale) + (for BGP) advertisement timers (MRAI) and best-path recomputation. Typical ranges: carrier detection ~10 ms, BFD 150 to 900 ms, LSA throttle 50 to 500 ms, SPF 10 to 100 ms, FIB programming tens of ms to seconds for large tables. Tuning knobs: faster detection (BFD), event-driven (carrier-delay 0), SPF/LSA throttle timers, prefix-independent convergence (PIC: hierarchical FIB so one change updates thousands of prefixes at once), graceful restart/NSF to hide control-plane restarts, and ECMP with fast reroute for sub-50 ms local repair.

**Micro-loops.** While the network is converging, routers close to the failure may update before routers far from it, briefly forwarding packets back and forth. Mitigations: ordered FIB updates (update far routers first), local micro-loop avoidance (delay the update after the SPF), and segment-routing based post-convergence protection. In ECMP Clos fabrics micro-loops are rare because paths are shortest-path symmetrical.

## 6. Redistribution between control planes

Often one protocol must learn routes from another: merging two organisations' networks, running different protocols per business unit, migrating from one IGP to another, injecting static or connected routes, or injecting BGP-learned prefixes into an IGP. **Redistribution** (import/export) takes routes from protocol X's table and originates them into protocol Y. Two problems arise: **metrics** and **loops**.

### Metrics

Each protocol defines its own metric semantic: protocol X may use 1000 / speed in Gb (10G link = 100, 100G link = 10), protocol Y a hand-built table (10G = 20, 100G = 10). Summing or comparing them is meaningless. Three approaches:

1. **Set a metric at the redistribution point** (administrator assigns a seed metric such as 5 for everything from X, carried as an ordinary metric in Y). Simple; ignores which exit is best for the external destination.
2. **Accept the source protocol's metric** as the new metric (works only if ranges are compatible; a metric above Y's maximum is unusable).
3. **Carry the external metric in a separate field** (OSPF external type 2/E2 or E1; EIGRP external; BGP MED/local-pref), so each router can use both the internal cost to the exit point and the external cost. This costs more state but allows better steering. Implementations then must choose: nearest exit (hot-potato, minimising your own network's usage) or the exit with the lowest external metric (cold-potato, minimising the external network's usage).

### Loops

If routes are redistributed from X into Y at router A, and back from Y into X at router B (two redistribution points, two-way), a route can circle: A injects N into Y; B, hearing N from Y, injects it back into X (now looking like a new route with a worse or better metric), and A prefers that version, because administrative distance or metric made it look better than the original. The result is a routing loop or a suboptimal path. Mitigation:

- **Redistribute one way only where possible** (default routes down, aggregates up) and use summaries/defaults instead of full redistribution.
- **Route tags**: tag routes when they enter a protocol and filter out anything carrying that tag when redistributing back (`route-map`, `prefix-list`, tag matching in FRR).
- **Prefix filters** (permit only the prefixes you intend to exchange) and **administrative distance** manipulation so the original source is always preferred.
- **Single redistribution point** or controlled pair, with documentation.
- Make **external routes lower priority than internal** by design (OSPF's rule of E routes losing to intra-area routes).

```text
! FRR sketch: one-way redistribution from OSPF into BGP with tags and a prefix filter
route-map OSPF-TO-BGP permit 10
 match ip address prefix-list ALLOWED-SERVICES
 set tag 1001
route-map OSPF-TO-BGP deny 20
router bgp 65101
 address-family ipv4 unicast
  redistribute ospf route-map OSPF-TO-BGP
route-map BGP-TO-OSPF deny 5
 match tag 1001
route-map BGP-TO-OSPF permit 10
 match ip address prefix-list FROM-BGP
```

In AI data centres, typical redistribution is limited to connected/loopback/host routes into BGP (`redistribute connected` with a route-map), static defaults from border routers, and occasionally Kubernetes (Calico/Cilium/MetalLB speak BGP to the fabric, advertising pod CIDRs and service VIPs).

## 7. Choosing a protocol (preview)

| Environment | Typical choice | Reason |
|---|---|---|
| Small site, few routers | Static routes + a default | Simplicity |
| Enterprise campus / medium DC | OSPF (single or multi-area) or IS-IS | Fast, topology-aware, standard |
| Service provider backbone | IS-IS or OSPF + BGP (+ MPLS/SR) | Scale, TE |
| Large data-centre fabric | eBGP (each leaf/rack its own ASN or one ASN per tier) or OSPF/IS-IS underlay + BGP overlay | Simplicity of one protocol, policy, ECMP, scale of BGP (RFC 7938) |
| Between organisations | BGP | Policy, path vector |
| Server/pod prefix advertisement | BGP to the host (FRR, BIRD, Calico, Cilium) | No L2 stretch, ECMP to hosts |

## 8. Hands-on: routing on Linux with FRR

FRR (Free Range Routing; daemons `zebra`, `ospfd`, `bgpd`, `isisd`, `bfdd`) turns a Linux host or container into a router and is the standard for labs and for Cumulus/SONiC-class switches. Install from the FRR packages, enable the daemons in `/etc/frr/daemons`, and use `vtysh`:

```bash
sudo apt install frr frr-pythontools ; sudo sed -i 's/^ospfd=no/ospfd=yes/;s/^bgpd=no/bgpd=yes/;s/^bfdd=no/bfdd=yes/' /etc/frr/daemons ; sudo systemctl restart frr
sudo vtysh
  show ip route ; show ip route ospf ; show ip ospf neighbor ; show bgp summary ; show bfd peers
  conf t
   router ospf
    ospf router-id 10.255.0.1
    network 10.1.0.0/24 area 0
```

Zebra installs the winning routes in the kernel FIB with the appropriate `proto` (`proto ospf`, `proto bgp`): `ip route show proto bgp`. Netlink events (`ip monitor route`) show convergence in real time, a good way to measure it.

## 9. Lab: static routes, a distance-vector failure, link state and convergence (untested)

Use a four-router ring/diamond of namespaces (or containerlab, chapter 2.27) with loopbacks and host namespaces at the edges.

1. **Static**: configure static routes to reach every loopback; break a link and show the blackhole; add a floating route and BFD tracking; measure recovery.
2. **Distance vector**: run a RIP-like daemon (FRR `ripd`) on a line topology; fail the edge network and watch count-to-infinity with `ip route` polling and `ping`; enable split horizon/poison reverse and compare; shorten timers.
3. **Link state**: run OSPF (FRR) in the diamond; examine `show ip ospf database`, flood a change (bring a link down) and watch the LSA update; compute the SPF tree by hand for one router and compare with `show ip route`; observe ECMP (equal-cost paths).
4. **BFD**: attach BFD to OSPF and measure failover with a continuous 10 ms-interval ping when you `tc netem loss 100%` a link versus when you `ip link set down` it; compare with default 40 s dead timers.
5. **LFA**: enable `fast-reroute lfa` (if supported by the FRR version) or reason on paper: in a triangle topology compute LFA candidates with the loop-free condition and show the ring case that has none.
6. **Redistribution**: run OSPF in one half and RIP (or a second OSPF instance) in the other, redistribute two-way at two routers without filters and produce a loop (watch TTL expiry in `tcpdump`); fix with tags and filters.
7. **Convergence measurement**: script a loop with `ip monitor route | ts` and a timestamped ping; record detection, convergence and packet loss for each configuration and tabulate.
8. **Clean up**.

Mark tested only after execution.

## 10. Common mistakes

- Static routes without health tracking (blackholes after a next-hop failure), or without a documented owner.
- Two-way redistribution at multiple points without tags and filters.
- Comparing metrics across protocols; forgetting administrative distance.
- Enabling aggressive BFD timers everywhere without control-plane protection and then causing flaps under load.
- Assuming "converged" means "FIB programmed": hardware programming time is part of convergence.
- Large flat link-state domains with unstable links and no throttling.
- Treating LFA as a guarantee; not checking coverage.
- Leaving default hello/dead timers in latency-critical fabrics.

## 11. Interview angles

- "Static versus dynamic routing: when would you choose each?"
- "Distance vector vs link state vs path vector: how does each avoid loops?"
- "What is count to infinity and how is it mitigated? What does DUAL's feasibility condition guarantee?"
- "Explain Dijkstra's algorithm in the context of OSPF; what is partial SPF?"
- "What is a loop-free alternate; when does a ring have none?"
- "How does BFD speed up convergence? What are the risks?"
- "What problems arise when redistributing between protocols and how do you prevent them?"
- "Break down convergence time after a link failure."

## 12. Checkpoint questions (35)

1. Give two good uses of static routes. **A:** Stub networks/defaults; pinned or management routes.
2. What is a floating static route? **A:** A static route with higher AD/metric used only as backup.
3. What is administrative distance? **A:** Preference between route sources, compared before metrics.
4. Name the six jobs of a control plane. **A:** Learn topology and destinations, advertise, compute paths, install, react to change.
5. Reactive versus proactive learning? **A:** On demand (ARP, controller lookup) versus advertised in advance.
6. What is an explorer packet? **A:** A probe that records the path to build a source route.
7. How does a proactive protocol ensure reliability? **A:** Sequence numbers/ACKs, database descriptions, keepalives.
8. Name three distribution models. **A:** Flooding, hop by hop, centralised store.
9. What is distance-vector routing? **A:** Routers share distances to destinations with neighbours and pick the lowest total.
10. What is count to infinity? **A:** Metrics increase incrementally while routers loop info about a failed destination.
11. What do split horizon and poison reverse do? **A:** Don't advertise (or advertise infinite) a route back where it was learned.
12. What is DUAL's feasibility condition? **A:** A neighbour is a safe successor if its reported distance < my feasible distance.
13. What does "active" mean in EIGRP? **A:** No feasible successor; the router queries neighbours.
14. What does link state flood? **A:** Each router's local links and costs.
15. What does each router run on the LSDB? **A:** Dijkstra's SPF rooted at itself.
16. What is partial SPF? **A:** Recompute only affected prefixes, not the tree.
17. Why use areas/levels? **A:** Bound LSDB size and flooding scope.
18. What defines a path-vector protocol? **A:** Advertisements carry the full path of domains; own ID in path means reject.
19. Why is BGP slow to converge? **A:** Path exploration and timers.
20. What is an LFA? **A:** A neighbour whose shortest path to D doesn't go through me.
21. State the loop-free condition. **A:** dist(N,D) < dist(N,me) + dist(me,D).
22. What are P and Q spaces? **A:** Nodes reachable from me / that can reach D without the failed link; intersection allows tunnelled repair.
23. What does TI-LFA add? **A:** Guaranteed coverage using segment routing along the post-convergence path.
24. What does Suurballe's algorithm find? **A:** Min-cost pair of link-disjoint paths.
25. What is a two-connected network? **A:** No single failure disconnects any node.
26. Polling versus event-driven detection? **A:** Timers/hellos versus lower-layer notifications; event-driven is faster but only local.
27. What is BFD and its typical interval? **A:** Lightweight forwarding-path liveness protocol, 50 to 300 ms.
28. Which UDP ports does BFD use? **A:** 3784 single hop, 4784 multihop.
29. What are the phases of convergence? **A:** Detect, originate, propagate, compute, install.
30. What is a micro-loop? **A:** Transient loop while routers update at different times.
31. Why redistribute? **A:** Interconnect domains, migration, inject static/connected routes.
32. What metric problems arise in redistribution? **A:** Incompatible semantics and ranges.
33. Three ways to handle metrics? **A:** Seed metric, accept source metric, carry external metric separately.
34. How do you prevent redistribution loops? **A:** One-way, tags, prefix filters, AD, single point.
35. Why does Clos ECMP act as fast reroute? **A:** Failed next hop is removed from the ECMP group in hardware.

## 13. Sources and review notes

**Written in original words.** Principal sources:

- Russ White and Jeff Tantsura (with co-authors), *Computer Networking Problems and Solutions*: chapter 11 (topology discovery: learning reachable destinations reactively and proactively, advertising and distributing reachability, redistribution between control planes with metrics and loops), chapter 12 (unicast loop-free paths 1: trees, alternate loop-free paths, the waterfall model, P/Q space, remote LFAs, Bellman-Ford, DUAL), chapter 13 (unicast loop-free paths 2: Dijkstra, partial and incremental SPF, LFA/rLFA calculation, path vector, disjoint paths, Suurballe, maximally redundant trees, two-way connectivity), chapter 14 (reacting to topology changes: polling and event-driven detection, BFD, flooding, hop-by-hop and centralised distribution, consistency and partitionability).
- Brian Ward, *How Linux Works*, 3rd ed., chapter 9: routes and the kernel routing table, default gateways, routers.
- FRR usage, administrative distance defaults, convergence timelines and AI-fabric notes are the author's synthesis from RFCs 2328, 5880, 5286 (LFA), 7490 (rLFA), 7938 (BGP in the data centre), Cisco EIGRP documentation and FRR manuals.

**Flagged for verification before publishing:** administrative distance defaults per vendor, FRR command syntax and LFA support by version, BFD/OSPF default timers, convergence time ranges, and TI-LFA/segment-routing support; all labs are **untested**.
