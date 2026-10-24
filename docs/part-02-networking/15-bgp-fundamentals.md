---
id: "c02-15"
title: "2.15 BGP fundamentals and control-plane policy"
sidebar_label: "2.15 BGP fundamentals and control-plane policy"
sidebar_position: 15
description: "BGP: sessions, attributes, best path, iBGP, route reflectors, policy"
status: "drafted"
tier: "2"
level: "I"
lab_venue: "GCP / GKE"
---

# 2.15 BGP fundamentals and control-plane policy

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 0 |
| Lab venue | Linux VM with FRR (namespaces/containerlab) |
| Part | Part 2: Networking, from first principles to AI fabrics |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

BGP is the protocol that connects the Internet, the cloud providers' edges (Direct Connect, Cloud Interconnect, ExpressRoute use it), and, since RFC 7938, most hyperscale and AI data-centre fabrics. It is also how Kubernetes advertises pod and service addresses (Calico, Cilium, MetalLB, kube-vip), how EVPN distributes MAC/IP reachability (chapter 2.17), and how bare-metal GPU nodes can run routed to the top-of-rack switch with ECMP across both uplinks. Interviews for infrastructure roles routinely ask about BGP sessions, attributes, the best-path algorithm, iBGP versus eBGP, route reflectors and why data centres use eBGP. This chapter teaches the protocol and its policy toolset; chapter 2.16 applies it to Clos fabrics.

## Prerequisites and outcomes

You should know routing fundamentals and path-vector concepts (chapter 2.13), TCP (2.6) and OSPF/IS-IS at a high level (2.14).

After this chapter you can:

- Explain autonomous systems, ASNs, IGP versus EGP, and what BGP's goals are (policy over shortest path).
- Describe BGP sessions: TCP/179, FSM states, OPEN/KEEPALIVE/UPDATE/NOTIFICATION messages, capabilities, hold timers, End-of-RIB, graceful restart, iBGP versus eBGP.
- Explain NLRI and path attributes (ORIGIN, AS_PATH, NEXT_HOP, MED, LOCAL_PREF, COMMUNITY, atomic aggregate, aggregator, large communities), mandatory versus optional, transitive versus non-transitive.
- Apply the best-path algorithm and predict outcomes of a given set of paths.
- Explain advertisement rules, why iBGP needs a full mesh or route reflectors/confederations, and next-hop-self.
- Write prefix lists, route-maps, communities and AS-path filters in FRR; implement hot-potato, cold-potato, resource segmentation and flow pinning policies conceptually.
- Secure and operate BGP (MD5/TCP-AO, GTSM, max-prefix, RPKI/ROV, bogon filters, graceful shutdown).
- Troubleshoot sessions and paths using `show bgp` commands.

## 1. Autonomous systems and why BGP exists

An **autonomous system (AS)** is a set of IP prefixes and routers under a single administrative policy, identified by an **AS number (ASN)**: 16-bit historically (1 to 65535), 32-bit now (RFC 6793, e.g. 4200000000 to 4294967294 private range; private 16-bit range 64512 to 65534). Interior gateway protocols (RIP, OSPF, IS-IS, EIGRP) find efficient paths inside one AS. The **Border Gateway Protocol, version 4** (RFC 4271, "BGP-4"), an Exterior Gateway Protocol, exchanges reachability *between* ASes. The design brief of an EGP differs from an IGP: ASes are businesses (service providers, content providers, enterprises) with commercial and political relationships, so the goal is not the shortest path but **policy**: whom I accept routes from, whom I announce routes to, which path I prefer for business reasons. BGP trades optimality for control.

```mermaid
flowchart LR
  subgraph AS65000["AS 65000 (enterprise / AI cluster)"]
    A[Border router]
  end
  subgraph AS65001["AS 65001 (transit provider)"]
    B[Edge]
  end
  subgraph AS65003["AS 65003 (transit provider 2)"]
    C[Edge]
  end
  subgraph AS65002["AS 65002 (content / cloud)"]
    D[Edge]
  end
  A -- "eBGP" --- B
  A -- "eBGP" --- C
  B -- "eBGP" --- D
  C -- "eBGP" --- D
  B -- "eBGP" --- C
```

BGP is a **path-vector** protocol: each advertisement for a prefix carries the list of ASes it has traversed (the AS_PATH). It is **proactive** (routes are advertised without waiting for traffic), learns reachable destinations from configuration (`network` statements), redistribution, and other protocols, advertises only **best paths** to neighbours, and relies on **TCP** instead of its own reliability layer.

## 2. Sessions (peering)

BGP does not discover neighbours; peers are **configured** (IP addresses or interfaces, remote ASN) on both ends. Because BGP runs over **TCP port 179**, the transport provides reliable, ordered delivery, flow control, MTU handling (path MTU discovery/MSS) and two-way connectivity proof from the three-way handshake, so BGP needs no hello discovery, retransmission or flooding logic of its own. Peers may be several hops apart (multihop; ebgp-multihop) or directly connected.

### Session establishment

```mermaid
stateDiagram-v2
  [*] --> Idle
  Idle --> Connect: start event, TCP SYN to peer:179
  Connect --> Active: TCP failed, retry
  Active --> Connect: retry timer
  Connect --> OpenSent: TCP up, send OPEN
  Active --> OpenSent: TCP up, send OPEN
  OpenSent --> OpenConfirm: OPEN received, send KEEPALIVE
  OpenConfirm --> Established: KEEPALIVE received
  Established --> Idle: NOTIFICATION / hold timer expiry / TCP reset
```

1. **Idle**: nothing; waiting for a start event.
2. **Connect/Active**: one side opens the TCP connection (the connection collision rule resolves both sides connecting at once: the connection initiated by the higher BGP identifier wins). If a firewall sits between the peers, the TCP open must originate from the side that the firewall permits; `Active` here means "TCP connect failed, trying again", not "established".
3. **OpenSent**: after TCP is up, each peer sends an **OPEN** message carrying: BGP version (4), the sender's **AS number** (and 4-byte ASN capability), **hold time** (the lower of the two values is used), the **BGP identifier** (router ID), and optional parameters: **capabilities** (multiprotocol extensions for IPv4/IPv6/VPN/EVPN address families, route refresh, 4-byte ASN, graceful restart, add-path, extended next hop).
4. **OpenConfirm** then **Established** after exchanging **KEEPALIVE**s. Timers: keepalive default 60 s, hold time 180 s in the protocol default (data-centre deployments use 3 s/9 s or rely on BFD, chapter 2.13).
5. Peers exchange their tables with **UPDATE** messages, which carry withdrawn prefixes, path attributes, and NLRI (network layer reachability information: the prefixes). After the initial exchange a peer sends **End-of-RIB (EOR)**. Afterwards only changes are sent. A **NOTIFICATION** message reports an error and closes the session. Soft resets use **route refresh** instead of tearing the session down.

Two kinds of sessions:

- **eBGP** (external): peers are in different ASes, normally directly connected; the next hop is rewritten to the sender's address; the local AS is **prepended** to the AS_PATH; TTL is 1 by default (security: GTSM).
- **iBGP** (internal): peers are in the same AS, usually loopback-to-loopback and multihop, carried over the IGP; AS_PATH is *not* modified; the next hop is *not* changed by default (so the IGP must reach the original eBGP next hop, or you set `next-hop-self`); LOCAL_PREF is carried.

## 3. Messages, NLRI and path attributes

An UPDATE advertises a set of prefixes (NLRI) that share the same path attributes. **Attribute categories:**

| Category | Meaning | Examples |
|---|---|---|
| Well-known mandatory | Must be understood and present in every UPDATE | ORIGIN, AS_PATH, NEXT_HOP |
| Well-known discretionary | Must be understood, may be omitted | LOCAL_PREF, ATOMIC_AGGREGATE |
| Optional transitive | May not be understood; passed along if unknown | COMMUNITY, AGGREGATOR, Large Community |
| Optional non-transitive | Dropped if not understood | MED (MULTI_EXIT_DISC), ORIGINATOR_ID, CLUSTER_LIST |

The key attributes:

- **ORIGIN**: how the route entered BGP: `i` (IGP / network statement), `e` (EGP, historical), `?` (incomplete, i.e. redistributed). Lower is preferred (i < e < ?).
- **AS_PATH**: ordered list (AS_SEQUENCE, plus AS_SET for aggregates) of ASes the route traversed. Used for loop prevention (reject when your own ASN appears) and as a metric (shorter is preferred). Operators **prepend** their ASN multiple times on outbound advertisements to make a path look longer and so less attractive.
- **NEXT_HOP**: the IP address to forward to; must be resolvable (recursively) through the IGP/connected routes or the route is unusable.
- **MED (multi-exit discriminator)**: a hint from a neighbour AS about which of multiple entry points to prefer (lower wins); compared only between routes from the same neighbouring AS (unless configured otherwise). It expresses the *neighbour's entrance policy*.
- **LOCAL_PREF**: carried only inside an AS (iBGP); higher wins; the standard tool for expressing *your exit policy* (default 100).
- **COMMUNITY** (32-bit tags `ASN:value`, e.g. `65000:100`), **extended communities** (route targets for VPNs) and **large communities** (96-bit `ASN:function:value`, RFC 8092, friendly to 4-byte ASNs) are labels attached to routes so that policy can be applied by matching them: "do not announce to peers" (`no-export` 65535:65281), "blackhole" (`65535:666`), "prefer this path" etc. They are the BGP configuration language for policy at scale.
- **WEIGHT**: a local, Cisco-originated, non-transmitted attribute (FRR supports it); highest wins; the first tiebreak step.
- **ATOMIC_AGGREGATE / AGGREGATOR**, **ORIGINATOR_ID / CLUSTER_LIST** (route reflection loop prevention).

### Loop prevention without split horizon

BGP has no split horizon. A router can advertise a route back to the AS it came from; loops are prevented because each AS prepends its ASN on eBGP advertisement and every router rejects routes whose AS_PATH already contains its own ASN. Example: A (AS65000) advertises 2001:db8:100::/64 to B and C. B (AS65001) re-advertises to D with path [65001, 65000]; D (AS65003) has [65003, 65001, 65000]. If this arrives back at A, A sees its own ASN in the path and drops it: the loop never enters A's table. Note that loop-freedom is a *property of the path attribute*, not part of the decision process.

## 4. The best-path decision process

When a router has several paths to the same prefix it picks one using an ordered list (vendor details differ slightly). The standard order:

1. Highest **WEIGHT** (local to the router; Cisco/FRR).
2. Highest **LOCAL_PREF** (exit policy of this AS).
3. Prefer **locally originated** routes (network/aggregate/redistributed on this router).
4. Shortest **AS_PATH**.
5. Lowest **ORIGIN** (i < e < ?).
6. Lowest **MED** (only among routes from the same neighbouring AS by default).
7. Prefer **eBGP over iBGP** paths.
8. Lowest **IGP cost** to the NEXT_HOP (hot potato: get the traffic out of my AS by the nearest exit).
9. If multipath is configured, install multiple equal paths (`maximum-paths`).
10. For eBGP paths, prefer the **oldest** (most stable) path to reduce churn.
11. Lowest **router ID** of the advertising peer.
12. Shortest **CLUSTER_LIST** length.
13. Lowest **neighbour address**.

Almost every real decision comes down to four factors: **LOCAL_PREF, AS_PATH length, MED, IGP cost**. BGP is intentionally flexible (custom decision processes exist) but the above is the common baseline. **Multipath** requires the paths to be equal up to step 8 (same LOCAL_PREF, AS_PATH length, origin, MED, IGP cost); in data centres `bestpath as-path multipath-relax` lets paths with the same length but different ASNs count as equal, which is how ECMP across spines with different ASNs works (chapter 2.16).

```bash
vtysh -c 'show bgp ipv4 unicast 10.1.0.0/24'     # shows all paths, the attributes and which is best/multipath ("=" "*>")
vtysh -c 'show bgp summary' -c 'show bgp neighbors 10.0.0.1 advertised-routes' -c 'show bgp neighbors 10.0.0.1 received-routes'
vtysh -c 'show ip bgp neighbors 10.0.0.1 routes' -c 'show bgp ipv4 unicast summary'
```

## 5. Advertisement rules, iBGP scaling and route reflectors

BGP's advertisement rules are two sentences: (1) advertise the **best path** to every eBGP peer; (2) advertise the best path **learned from an eBGP peer** to every iBGP peer. Consequence: a route learned from an iBGP peer is **not** advertised to another iBGP peer. This is how BGP avoids loops *inside* an AS (where the AS_PATH does not change and so cannot detect them). The side effect: iBGP needs a **full mesh** of sessions (n(n-1)/2), which does not scale. Two solutions:

- **Route reflectors (RR)** (RFC 4456): designate a router as an RR and the others as its **clients**; the RR may advertise iBGP-learned routes to clients (reflecting them). Loop prevention is via two new attributes: ORIGINATOR_ID (the router that first injected the route into the AS) and CLUSTER_LIST (RR cluster IDs traversed). Real networks run two or more RRs per cluster for redundancy. Caveat: RRs choose best paths from their own perspective (IGP-cost based), which can hide path diversity and cause suboptimal routing; **add-path** (advertise multiple paths) and optimal-route-reflection mitigate this.
- **Confederations**: split an AS into sub-ASes that behave like eBGP internally; used in very large networks.

Also needed in iBGP: `neighbor X next-hop-self` for routes learned from an eBGP peer, so that iBGP peers can resolve the next hop through the IGP without carrying the external link subnet; `update-source lo` to peer from loopbacks; and ensuring the **IGP carries loopbacks** (but not the external prefixes: never redistribute BGP into the IGP).

Data-centre designs (chapter 2.16) skip iBGP entirely and use **eBGP everywhere** with a per-rack or per-tier ASN scheme, trading ASN management for simpler failure domains, no IGP dependency, and policy at every hop.

## 6. Configuring BGP in FRR

```text
! Leaf in AS 65101 peering with two spines in AS 65000 (eBGP), advertising its loopback and server subnet
router bgp 65101
 bgp router-id 10.255.0.11
 no bgp ebgp-requires-policy               ! lab convenience; in production use explicit policy
 bgp bestpath as-path multipath-relax
 neighbor SPINES peer-group
 neighbor SPINES remote-as 65000
 neighbor SPINES bfd
 neighbor SPINES timers 3 9
 neighbor 10.0.1.0 peer-group SPINES
 neighbor 10.0.2.0 peer-group SPINES
 address-family ipv4 unicast
  network 10.255.0.11/32
  network 10.101.0.0/24
  neighbor SPINES activate
  neighbor SPINES soft-reconfiguration inbound
  maximum-paths 4
 exit-address-family
```

```bash
vtysh -c 'show bgp summary'                 # session state, uptime, prefixes received/sent
vtysh -c 'clear bgp 10.0.1.0 soft in'       # re-apply inbound policy without resetting the session
vtysh -c 'show bgp neighbors 10.0.1.0'      # state, capabilities, timers, last reset reason
```

Key BGP states in `show bgp summary`: `Idle` (not started or policy/administratively down), `Connect`/`Active` (TCP not established: reachability, firewall, wrong peer address, MD5 mismatch, ASN mismatch gives OPEN errors), `OpenSent`/`OpenConfirm` (stuck here: capability/hold-time/auth problems), a number in the prefix column means **Established**, `(Policy)` means eBGP without in/out policy under `ebgp-requires-policy`.

## 7. Policy tools

BGP policy is expressed with **filters and attribute changes** applied inbound or outbound per neighbour.

| Tool | Purpose | FRR/Cisco-like object |
|---|---|---|
| Prefix list | Match prefixes and length ranges | `ip prefix-list NAME seq 10 permit 10.0.0.0/8 le 24` |
| AS-path access list | Match AS_PATH with regexes | `bgp as-path access-list NAME permit ^65001_` |
| Community list | Match communities | `bgp community-list standard C1 permit 65000:100` |
| Route map | Ordered match/set rules: set LOCAL_PREF, MED, communities, prepend AS_PATH, next hop, weight | `route-map NAME permit 10` |
| Max-prefix | Limit prefixes accepted from a peer | `neighbor X maximum-prefix 1000` |
| Distribute/prefix filters on aggregates | Aggregate and suppress specifics | `aggregate-address 10.1.0.0/16 summary-only` |

```text
ip prefix-list CUSTOMER-IN seq 10 permit 203.0.113.0/24
ip prefix-list DEFAULT-ONLY seq 10 permit 0.0.0.0/0
bgp community-list standard BLACKHOLE permit 65535:666
route-map FROM-TRANSIT-A permit 10
 match ip address prefix-list DEFAULT-ONLY
 set local-preference 200
route-map TO-TRANSIT-B permit 10
 match ip address prefix-list CUSTOMER-IN
 set as-path prepend 65000 65000 65000
router bgp 65000
 address-family ipv4 unicast
  neighbor 192.0.2.1 route-map FROM-TRANSIT-A in
  neighbor 198.51.100.1 route-map TO-TRANSIT-B out
```

### What policy is for (use cases)

**Routing and potatoes.** *Hot-potato routing* hands traffic to the neighbour at the nearest exit (cheapest for me; achieved by the IGP-cost step or by LOCAL_PREF set on nearest peers). *Cold-potato routing* carries traffic inside my own network as far as possible and exits near the destination (better control of the user experience; used by content providers, achieved by high LOCAL_PREF on routes at the far exit, by honouring MED from neighbours, or by selective advertisement). Both choose a longer path than the minimum to serve a business policy: transit providers want to carry traffic across their backbone to maximise utilisation of the paid link; content providers want to control quality; a customer buying transit wants cheap and good exits.

**Resource segmentation.** Different tenants or services must reach only certain servers, sometimes along specific paths, and sometimes must not even *see* the routing information of the other. Packet filters alone can't meet requirements like "hide routes" or "force this path". A common solution is an **overlay**: tunnels (GRE, VXLAN, MPLS, SR) carry each segment through the shared underlay, with a separate overlay control plane (BGP VPNv4/EVPN, VRFs and route targets) pulling traffic into the tunnel. Underlay reachability and overlay policy are separated, which is why overlays pervade modern networks (chapter 2.17).

**Flow pinning.** *Elephant* flows (large, long-lived, e.g. >20% of a link for minutes) and *mouse* flows (small, short, latency-sensitive) hashed onto the same link interfere: a single 9000-byte elephant packet occupies a 100 Mb/s link for 0.72 ms, so a 64-byte mouse packet queued behind it waits far longer than its own serialisation (0.05 ms), which shows up as jitter and hurts flow control and error recovery. Mixing them is a performance problem even when average utilisation is low. Remedies: QoS to interleave, **pinning** the elephant to a chosen path and steering other traffic away from it (using the five-tuple to distinguish flows: source and destination IP, ports, protocol), segment routing or policy-based routing, or in AI fabrics adaptive routing and packet spraying (chapters 2.12 and 2.19). Pinning in a purely hash-based ECMP fabric is difficult because the ECMP hash decides paths; this is why flow-aware controllers and per-flow policies exist. Policy at this granularity carries **complexity cost**: more state, more interactions, and more ways to fail; each policy should justify itself against the extra operational risk (a recurring theme: adding policy trades network optimality and simplicity for control).

## 8. Security and operations

BGP trusts its peers; a mistaken or malicious announcement can divert or black-hole traffic globally (route leaks and hijacks). Controls:

- **Session protection**: TCP MD5 (`neighbor X password`) or TCP-AO (RFC 5925); **GTSM** (TTL security: eBGP peers send TTL 255 and accept only 254+/`ttl-security hops 1`); restrict TCP/179 with ACLs to known peers; authenticated, preferably over a private management or point-to-point interface.
- **Prefix and path filtering**: accept only what a peer should legitimately announce (customer prefix lists), reject bogons, private ASNs, overlong prefixes (/25+), your own space from outside, and default routes unless expected; `maximum-prefix` as a safety net; AS-path filters (reject paths containing private ASNs or too long); `bgp ebgp-requires-policy` in FRR forces explicit policy.
- **Origin validation**: **RPKI / ROV** (RFC 6811): validate that the origin AS is authorised (ROA) to announce the prefix; reject Invalid. ASPA (draft/RFC in progress) validates AS_PATH relationships.
- **Operational hygiene**: graceful restart / long-lived graceful restart (keep forwarding while the control plane restarts), `bgp graceful-shutdown` (GRACEFUL_SHUTDOWN community 65535:0 so neighbours move traffic away before maintenance), BFD for fast failure detection, route dampening (rarely recommended now), max-prefix, monitoring (session state, prefix counts, update rates; BMP streaming to a collector), looking glasses and route collectors (RIPE RIS, RouteViews) to observe how the world sees your prefixes.
- **Blackhole/RTBH**: announce a victim /32 with a blackhole community to the upstream to drop DDoS traffic at the edge.

## 9. BGP in AI/Kubernetes contexts (preview)

- **Fabric underlay/overlay**: eBGP between leaf and spine, loopback and server-subnet advertisement, ECMP with `multipath-relax`, BFD, EVPN address family for VXLAN overlays (chapter 2.16 and 2.17).
- **BGP to the host**: FRR/BIRD on GPU servers (or the DPU) peering with both ToRs gives ECMP, no MLAG, instant failover and a host that advertises its own /32 loopback and any pod/VM prefixes.
- **Kubernetes**: Calico (BIRD or the Go BGP library), Cilium BGP control plane, MetalLB (LoadBalancer VIPs in BGP mode), kube-vip. Typically the node (AS per node or one shared AS) peers with the ToR and announces pod CIDRs and service IPs, with `maximum-paths` at the ToR to spread ingress traffic.
- **Cloud**: Direct Connect / Cloud Interconnect / ExpressRoute and cloud routers exchange routes with on-prem via BGP (a private ASN on-prem, the cloud's ASN, MED/AS-path prepending for primary/backup); learn the vendor limits (max routes, BFD timers).

## 10. Lab: BGP sessions, attributes and policy (untested)

Use FRR in three or four namespaces/containers (containerlab, chapter 2.27): AS65001 --- AS65000 (transit) --- AS65002, plus a second link to create path choice.

1. **eBGP session**: configure peers, watch `show bgp summary` go Idle → Connect → Active → Established; capture with `tcpdump -ni any port 179` and decode OPEN/KEEPALIVE/UPDATE; set mismatched ASN to see the NOTIFICATION; test an ACL that blocks 179 in one direction.
2. **Advertise prefixes** with `network` and with `redistribute connected`; verify `received-routes`; compare AS_PATH, NEXT_HOP on each router.
3. **Loop prevention**: construct a triangle and show a route being rejected because of the local ASN; use `allowas-in` to demonstrate the override (and its risk).
4. **Best-path steering**: with two paths, change LOCAL_PREF inbound, then AS-path prepend outbound, then MED; for each, predict then confirm with `show bgp ipv4 unicast <prefix>`; test the "MED only compared within the same neighbour AS" rule.
5. **iBGP**: add a second router in AS65000, build an iBGP session over loopbacks with an IGP (OSPF); show the next-hop problem and fix with `next-hop-self`; demonstrate the iBGP-not-to-iBGP rule with three iBGP routers, then fix with a route reflector and observe ORIGINATOR_ID/CLUSTER_LIST.
6. **Communities**: tag routes, match them to set LOCAL_PREF or deny export (`no-export`), implement a blackhole community.
7. **Filters**: prefix-list inbound that rejects more-specifics and bogons; `maximum-prefix 5` trigger and recovery.
8. **Security**: enable MD5 and GTSM; test a mismatch; (optional) RPKI validation with a local `rtrd`/Routinator.
9. **Failure**: down a link and measure convergence with default timers, `timers 3 9`, and BFD; observe path exploration in updates (`debug bgp updates`).
10. **Clean up**.

Mark tested only after execution.

## 11. Common mistakes

- Forgetting `next-hop-self` or IGP reachability of next hops in iBGP; redistributing BGP into the IGP.
- Treating iBGP like eBGP (expecting AS_PATH changes) or forgetting the full-mesh/RR requirement.
- No inbound/outbound policy on eBGP sessions (accidental transit, route leaks).
- Using MED across different neighbour ASes; relying on weight as a network-wide tool (it is local).
- Overlooking `maximum-paths` and multipath-relax: only one path is used.
- Aggressive timers without BFD, causing flaps; not setting graceful-shutdown before maintenance.
- Not validating or filtering prefixes (hijack/leak exposure); no max-prefix.
- Confusing `Active` (retrying TCP) with a healthy session.

## 12. Interview angles

- "Walk through the BGP FSM. What does Active mean?"
- "eBGP vs iBGP: differences in next hop, AS_PATH, TTL, advertisement rules."
- "Why must iBGP routes not be re-advertised to iBGP peers? What are the fixes?"
- "List the BGP best-path steps; which four matter most?"
- "How does BGP prevent loops without split horizon?"
- "What are communities and large communities for? Give examples."
- "How do you steer inbound versus outbound traffic with BGP?" (Outbound: LOCAL_PREF; inbound: AS-path prepend, MED, communities, selective advertisement.)
- "How do you secure BGP sessions and prefixes?"
- "Why do data centres use eBGP? What do they change in the defaults?" (chapter 2.16.)
- "What is hot-potato versus cold-potato routing?"

## 13. Checkpoint questions (40)

1. What is an AS? **A:** A set of prefixes/routers under one administrative policy with an ASN.
2. What is the difference between IGP and EGP? **A:** Within an AS (efficiency) versus between ASes (policy).
3. Which transport does BGP use? **A:** TCP port 179.
4. What does TCP give BGP? **A:** Reliability, flow control, MTU handling, two-way connectivity.
5. List BGP message types. **A:** OPEN, UPDATE, KEEPALIVE, NOTIFICATION (plus ROUTE-REFRESH).
6. What is exchanged in OPEN? **A:** Version, ASN, hold time, BGP ID, capabilities.
7. How is hold time chosen? **A:** The lower of the two.
8. What does Active mean in the FSM? **A:** TCP connection failed; retrying.
9. What does End-of-RIB signal? **A:** The initial table exchange is complete.
10. Name the mandatory attributes. **A:** ORIGIN, AS_PATH, NEXT_HOP.
11. What does LOCAL_PREF express? **A:** Exit preference within an AS (higher wins).
12. What does MED express? **A:** The neighbour's preferred entry point (lower wins).
13. When is MED compared? **A:** Between paths from the same neighbouring AS.
14. What is a community? **A:** A tag attached to routes for policy matching.
15. Why large communities? **A:** Support 4-byte ASNs with function/value structure.
16. Which attribute carries path loop information? **A:** AS_PATH.
17. Is there split horizon in BGP? **A:** No.
18. What happens when a router sees its own ASN in the path? **A:** It rejects the route.
19. First step of best path? **A:** Highest weight (local).
20. Second? **A:** Highest LOCAL_PREF.
21. How does AS-path prepending work? **A:** Repeat your ASN outbound to lengthen the path and de-prefer it.
22. Why prefer eBGP over iBGP? **A:** Exit the AS sooner/more trustworthy.
23. What is hot-potato routing? **A:** Exit at the nearest egress (lowest IGP cost).
24. Rule 1 of advertisement? **A:** Advertise best path to every eBGP peer.
25. Rule 2? **A:** Advertise eBGP-learned best to every iBGP peer (not iBGP-learned to iBGP).
26. Why iBGP full mesh? **A:** iBGP-learned routes aren't re-advertised among iBGP peers.
27. What is a route reflector? **A:** A router allowed to reflect iBGP routes to clients.
28. What prevents RR loops? **A:** ORIGINATOR_ID and CLUSTER_LIST.
29. Why `next-hop-self`? **A:** iBGP preserves the external next hop, which may be unreachable inside the AS.
30. What does `multipath-relax` do? **A:** Allows ECMP across paths with equal AS-path length but different ASNs.
31. What is the BGP identifier? **A:** The router ID used in OPEN and tiebreaking.
32. How do you apply a policy change without resetting? **A:** Soft reconfiguration / route refresh.
33. What does `maximum-prefix` protect against? **A:** A peer flooding or leaking routes.
34. What is GTSM? **A:** TTL security: accept only packets with TTL 255 from directly connected peers.
35. What is RPKI ROV? **A:** Validating origin AS of prefixes against ROAs.
36. What is RTBH? **A:** Remote-triggered blackhole announced via community.
37. Why do overlays pull traffic with a separate control plane? **A:** Separate segments from the underlay; policy and path control.
38. Why do elephant and mouse flows interfere? **A:** Large packets delay small ones, increasing jitter.
39. Which BGP attribute influences inbound traffic from other ASes? **A:** AS-path prepend, MED, communities.
40. Which influences outbound traffic? **A:** LOCAL_PREF (and weight locally).

## 14. Sources and review notes

**Written in original words.** Principal sources:

- Russ White and Jeff Tantsura (with co-authors), *Computer Networking Problems and Solutions*, chapter 16 (BGP: history and role as an exterior gateway protocol, BGP peering and its state machine, the best-path decision process, advertisement rules, route reflectors, concluding classification) and chapter 17 (policy in the control plane: hot and cold potato routing, resource segmentation with overlays, flow pinning for elephant and mouse flows, policy complexity).
- FRR configuration, security and operations, AI/Kubernetes/cloud notes are the author's synthesis from RFCs 4271, 4456, 6793, 6811, 8092, 5925, 7938, and the FRR manual.

**Flagged for verification before publishing:** FRR syntax per version (`ebgp-requires-policy`, `neighbor ... bfd`), default timers, ASPA status, best-path step differences between vendors, and cloud BGP limits; all labs are **untested**.
