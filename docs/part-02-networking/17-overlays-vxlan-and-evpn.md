---
id: "c02-17"
title: "2.17 Overlays: tunnels, VXLAN, EVPN, segment routing and SD-WAN"
sidebar_label: "2.17 Overlays: tunnels, VXLAN, EVPN, segment routing and SD-WAN"
sidebar_position: 17
description: "Network virtualization: tunnels, VRFs, VXLAN, EVPN, segment routing, SD-WAN, complexity"
status: "drafted"
tier: "2"
level: "A"
lab_venue: "GCP / GKE"
---

# 2.17 Overlays: tunnels, VXLAN, EVPN, segment routing and SD-WAN

| | |
|---|---|
| Level | Advanced |
| Priority tier | 0 |
| Lab venue | Linux VM with namespaces; containerlab + FRR for EVPN |
| Part | Part 2: Networking, from first principles to AI fabrics |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

Overlays are how one physical fabric becomes many logical networks. A multi-tenant GPU cloud isolates customers with VXLAN/EVPN VRFs; Kubernetes CNIs (Flannel, Calico VXLAN/IPIP, Cilium, Antrea) build pod networks as overlays; cross-site connectivity runs over WireGuard, IPsec or SD-WAN; segment routing and SRv6 are being proposed to steer AI traffic over chosen paths. An overlay hides the physical topology from tenants and, at the same time, hides the tenants' traffic from the physical network, which is powerful and dangerous: MTU shrinks, ECMP hashing loses entropy, troubleshooting needs two views (overlay and underlay), and failures in the underlay appear as mysterious overlay loss. This chapter explains virtual networks in general (tunnels, VRFs, underlay/overlay), the two classic use cases (Ethernet over IP and private access), the requirements any virtualization must meet, VXLAN, EVPN, segment routing (MPLS and IPv6), SD-WAN, and the complexity that virtualization adds, with Linux and FRR labs.

## Prerequisites and outcomes

You should know routing (2.5, 2.13), BGP (2.15, 2.16), VLANs (2.11), MTU (2.7) and ECMP hashing (2.12).

After this chapter you can:

- Define tunnel, overlay, underlay, VRF, virtual interface, encapsulation and recursive lookup, and trace a packet through a tunnel hop by hop.
- State the two questions every virtualization solution answers (how is traffic encapsulated; how is reachability through the tunnel advertised) and the optional QoS requirement.
- Compare GRE, IPIP, GENEVE, VXLAN, MPLS, WireGuard and IPsec encapsulations, their overheads and ECMP entropy.
- Explain VXLAN (VNI, VTEP, flood-and-learn versus control plane) and EVPN (route types 1 to 5, RD/RT, IRB, anycast gateway, ARP suppression, multihoming) and configure a VXLAN overlay on Linux and an EVPN fabric in FRR.
- Explain segment routing: node and adjacency SIDs, SR-MPLS label stack operations (PUSH/POP/CONTINUE), SRv6, signalling.
- Explain SD-WAN's building blocks and when it is used.
- Reason about virtualization complexity: interaction surfaces, shared risk link groups, overlaid control planes, MTU and observability.
- Design and troubleshoot overlays for AI clusters and Kubernetes.

## 1. What is a virtual network?

Network virtualization creates **logical topologies on top of a physical topology**. A single logical link across a bigger network is a **tunnel**; a collection of virtual links that look like a complete network is an **overlay**; the physical (or lower-layer) network that carries the tunnels is the **underlay**. Why accept the complexity? Because the aim is to separate multiple traffic flows, or reachability domains, across one physical network. It is another kind of multiplexing, with two distinguishing properties: different **control planes** can operate with different reachability information on one topology, and different **sets of destinations** can coexist without interacting.

### A packet through a tunnel

```mermaid
flowchart LR
  A["Host A"] --> C["Router C\n(tunnel headend)"]
  C --> E["Router E\n(underlay transit)"]
  E --> H["Router H\n(tunnel tailend)"]
  H --> M["Host M"]
  C -. "virtual link [C,H] (tunnel)" .-> H
```

1. A sends a packet to M. C's routing table says the best path to M is through a **tunnel (virtual) interface** toward H.
2. The virtual interface has rewrite instructions: add a new **outer header** (destination H) to the **inner** packet (destination M).
3. C now looks up the *outer* destination H, a **recursive lookup**, finds it is reached via E, and builds the link-local (Ethernet) header toward E.
4. E strips the link header and forwards based on the *outer* header only; it never examines A's original packet.
5. H removes the link header, sees the outer header is destined for itself, removes it, and processes the inner packet: M is locally attached, so it forwards to M.

If **VRFs** are used instead of tunnel interfaces, the first lookup occurs in the VRF associated with the ingress link; the result points into a tunnel; after encapsulation, the outer packet is looked up in the base (underlay) routing table; at the tailend, the egress VRF is selected from the encapsulation (a VNI or label).

**Definition used here.** A tunnel is a virtual link where an outer header encapsulates an inner header and (a) the inner is at the same or a lower layer than the outer (e.g. Ethernet inside IPv6/UDP), and (b) at least some devices on the path forward on the outer header alone. Terms like underlay/overlay are normally used when there is a full virtual topology, not a single VPN session. Don't let edge cases ("platypus" definitions) distract: keep the general case clear and note the exceptions.

### Two classic use cases

**1. Ethernet services over an IP network.** Some applications assume Layer-2 adjacency: storage and database products with proprietary Ethernet protocols, hypervisors that assume the default-gateway ARP/ND cache is reliable, clusters that need to see each other in neighbour discovery, or VMs that must *move* (live migration) without changing IP/gateway. Some operators also prefer one large flat Ethernet. The IP network must provide an Ethernet-like service: (1) carry Ethernet frames inside an IP-routable encapsulation between edge routers/hypervisors; (2) learn which MAC addresses are reachable at which edge and draw traffic into the tunnel (a second control plane, or MAC reachability carried in an existing one); (3) optionally copy QoS markings (DSCP/PCP) from the inner to the outer header. This is VXLAN/EVPN.

**2. Virtual private access.** Remote workers and branch offices need access to corporate resources that can't be exposed to the Internet, with confidentiality of both contents and addresses and acceptable quality for real-time traffic. Solution: an (usually encrypted) tunnel from the remote host or site to the corporate edge, plus advertising reachability both ways so traffic is drawn into the tunnels, and path/quality control (SD-WAN). This is IPsec/WireGuard VPN and SD-WAN.

### What every virtualization solution must solve

1. **Encapsulation**: how is traffic placed inside the tunnel so packets and control-plane information are separated from the underlay? Considerations: **hardware forwarding support** in the underlay (can ASICs parse and hash the encapsulation?), and **overhead** (every added byte reduces payload; PMTUD handles encapsulated packets poorly, so MTUs must be tuned manually at the encapsulation point, chapter 2.7).
2. **Reachability advertisement**: how does the headend learn which destinations are behind which tunnel endpoint? Two models: *integrated* (the tunnel is "just another link" in the one routing table; recursive lookups) and *overlay/over-the-top* (a separate control plane or separate database/VRF carries overlay reachability; a classifier decides which table a packet uses, e.g. by ingress interface or VNI).
3. **Optionally QoS**: copy markings (DSCP, PCP, ECN) between inner and outer, or traffic-engineer the tunnel's path (chapter 2.19).

## 2. Encapsulation options

| Encapsulation | Layer carried | Overhead (IPv4 underlay) | Notes |
|---|---|---|---|
| **GRE** | L3 (or L2 as gretap) | 24 bytes (+ key option) | Simple, no built-in security or entropy (IP proto 47) |
| **IPIP / SIT / ip6tnl** | L3 in L3 | 20 / 40 | Minimal; used by Calico IPIP mode |
| **VXLAN** (RFC 7348) | L2 over UDP/4789 | 50 bytes (14 inner Ethernet header not counted: outer IP 20 + UDP 8 + VXLAN 8 + outer Ethernet 14) | 24-bit VNI (16M segments); UDP source port is a hash of inner flow → ECMP entropy |
| **GENEVE** (RFC 8926) | L2/L3 over UDP/6081 | 50+ (options) | Extensible TLV options; used by OVN, Antrea, AWS; successor to VXLAN/NVGRE |
| **MPLS** | Label stack | 4 per label | Used for L3VPN/EVPN in carriers; SR-MPLS |
| **SRv6** | IPv6 + SRH | 40 + 8 + 16/SID (less with uSID) | Segment routing over IPv6 |
| **WireGuard** | L3 over UDP | 60 (IPv4) / 80 (IPv6) | Modern, fast, small codebase |
| **IPsec ESP** | L3 (tunnel mode) | ~50 to 73 | Standard VPN; NAT-T uses UDP/4500 |

Notes: *encapsulation hides inner headers from the underlay*, so ECMP and ACLs see only outer headers. UDP-based encapsulations (VXLAN, GENEVE, WireGuard) derive the outer **source port from a hash of the inner flow**, giving the underlay ECMP entropy; GRE/IPIP/ESP have no ports so all traffic between two endpoints hashes to one path unless the hardware inspects inner headers (`encap3+4` bonding policy, `fib_multipath_hash_policy=2` for Linux, chapters 2.5, 2.12).

## 3. VXLAN

**Virtual eXtensible LAN** carries Ethernet frames over UDP so a routed L3 network provides L2 segments to hosts and VMs.

```text
| Outer Eth | Outer IP (VTEP src → VTEP dst) | UDP (src=hash, dst 4789) | VXLAN hdr (flags, VNI 24b) | Inner Ethernet frame | payload |
```

- **VNI** (VXLAN Network Identifier): 24-bit segment ID (versus 4094 VLANs).
- **VTEP** (VXLAN Tunnel Endpoint): the device (hypervisor vSwitch, leaf switch, Linux `vxlan` device, DPU) that encapsulates frames into UDP/IP and decapsulates them; has an underlay IP address (usually a loopback /32).
- **Mapping**: a local VLAN (or port, or bridge) maps to a VNI; frames with that VLAN become VXLAN with that VNI.
- **Forwarding of unknown/broadcast/multicast (BUM)**: original VXLAN used **flood-and-learn**: BUM frames are sent to a multicast group per VNI (needs PIM in the underlay) or replicated by **head-end replication** to a configured list of remote VTEPs; remote MACs are learned from the source of decapsulated frames (like a switch). This is simple but floods and scales poorly. Modern deployments use a **control plane** (EVPN) to distribute MAC/IP reachability and suppress flooding.
- **MTU**: add 50 bytes; use jumbo on the underlay (e.g. 9216) so tenants keep 1500 (or 9000 with 9100+ underlay).
- **Hardware**: ASIC support for VXLAN encap/decap at line rate is standard on data-centre switches and many NICs (offloads: `ethtool -k` `tx-udp_tnl-segmentation`, checksum offload for tunnels).

### Linux VXLAN

```bash
# Point-to-point VXLAN between two hosts (static), VNI 42
sudo ip link add vxlan42 type vxlan id 42 local 10.0.0.1 remote 10.0.0.2 dstport 4789 dev eth0
sudo ip addr add 192.168.42.1/24 dev vxlan42 ; sudo ip link set vxlan42 up mtu 1450
# Multi-peer with head-end replication using the all-zero FDB entry
sudo ip link add vxlan100 type vxlan id 100 local 10.0.0.1 dstport 4789 nolearning
sudo bridge fdb append 00:00:00:00:00:00 dev vxlan100 dst 10.0.0.2
sudo bridge fdb append 00:00:00:00:00:00 dev vxlan100 dst 10.0.0.3
# Attach to a bridge so VMs/containers on the bridge share the segment
sudo ip link add br100 type bridge ; sudo ip link set vxlan100 master br100 ; sudo ip link set br100 up ; sudo ip link set vxlan100 up
bridge fdb show dev vxlan100 ; ip -d link show vxlan100 ; tcpdump -ni eth0 udp port 4789
# Scalable "external/metadata" mode for EVPN/FRR: one device, many VNIs via bridge vlan_tunnel
sudo ip link add vxlan0 type vxlan dstport 4789 local 10.255.0.11 nolearning external vnifilter
```

Debug with `tcpdump -ni eth0 -vv udp port 4789` (Wireshark decodes the VXLAN header and inner frame), check MTU with `ping -M do`, and check the underlay path between VTEP loopbacks separately from the overlay.

## 4. EVPN: a control plane for Ethernet and IP overlays

**EVPN** (BGP Ethernet VPN, RFC 7432; for VXLAN RFC 8365) uses **MP-BGP** (address family `l2vpn evpn`) to advertise MAC and IP reachability between VTEPs, replacing flood-and-learn. It is the standard data-centre overlay control plane. Components:

- **Underlay**: IP reachability between VTEP loopbacks (eBGP/OSPF/IS-IS ECMP fabric, chapter 2.16).
- **Overlay BGP sessions**: typically eBGP between leaf and spine over the same links (an extra address family on the existing sessions), with spines as route servers (not tunnel endpoints), or iBGP to route reflectors. Next hops are VTEP IPs and must not be rewritten at the spine (`next-hop-unchanged` and route-server behaviour).
- **EVI** (EVPN instance) / **MAC-VRF** for L2 segments and **IP-VRF** for L3 routing; **RD** (route distinguisher, makes routes unique across VRFs) and **RT** (route target, an extended community selecting which VRFs import a route).

### Route types

| Type | Name | Purpose |
|---|---|---|
| **1** | Ethernet Auto-Discovery | Multihoming: per-Ethernet-Segment (ES) and per-EVI fast convergence and aliasing |
| **2** | MAC/IP Advertisement | Advertises a host MAC (and optionally its IP) with the VNI and VTEP next hop; the heart of L2/L3 host reachability; also carries MAC mobility sequence numbers |
| **3** | Inclusive Multicast Ethernet Tag | Builds the BUM replication list: each VTEP announces "I am in VNI x" |
| **4** | Ethernet Segment | Designated-forwarder election among multihomed leaves of the same ES |
| **5** | IP Prefix | Advertises IP prefixes (routing between tenants/outside, host /32s) into IP-VRFs |

### Behaviours that make EVPN practical

- **Host learning is local, advertisement is BGP**: a leaf learns a host MAC from the data plane or ARP/ND, originates a type 2 route, and all other VTEPs install it. **MAC mobility** (live migration) is handled by a sequence number so the latest location wins.
- **ARP/ND suppression**: since leaves know MAC-to-IP bindings from type 2 routes, they answer ARP requests locally and don't flood them. Reduces BUM traffic massively.
- **Integrated routing and bridging (IRB)**: the leaf routes between VNIs/VRFs. *Asymmetric IRB*: ingress leaf routes then bridges (needs all VNIs on all leaves). *Symmetric IRB* (preferred): ingress and egress both route, using an **L3 VNI** per tenant VRF; each leaf only needs the VNIs of its local hosts plus the tenant L3 VNI; scales better. Type 2 routes carry two labels/VNIs (L2 VNI and L3 VNI) and two route targets.
- **Distributed anycast gateway**: every leaf holds the same gateway IP/MAC for a subnet, so hosts have a first-hop gateway on their own leaf at any location (VM moves need no ARP change).
- **Multihoming (ESI-LAG)**: a server's LACP bond to two leaves (MLAG replacement) is represented by a 10-byte Ethernet Segment Identifier; type 4 routes elect the **designated forwarder** for BUM traffic, and type 1 routes provide fast withdrawal on link failure and **aliasing** (other leaves load-balance to both attached VTEPs).
- **Tenancy**: each tenant gets an IP-VRF (L3 VNI) with import/export route targets; type 5 routes carry prefixes (including the default route from a border leaf toward external networks). Route leaking between VRFs is by importing RTs.
- **Group-based policy (GBP)** tags in VXLAN headers allow microsegmentation within a VNI (chapter 2.16).

### FRR EVPN leaf (VXLAN with symmetric IRB, sketch)

```text
! Linux side: VLAN-aware bridge + single VXLAN device mapping VLAN 100 -> VNI 10100; VRF tenant1 with L3VNI 5001
ip link add br0 type bridge vlan_filtering 1 vlan_default_pvid 0
ip link add vxlan0 type vxlan dstport 4789 local 10.255.0.11 nolearning external vnifilter
ip link set vxlan0 master br0 ; bridge vlan add dev vxlan0 vid 100 ; bridge vni add dev vxlan0 vni 10100
! FRR
router bgp 65101
 neighbor swp1 interface remote-as external
 address-family l2vpn evpn
  neighbor swp1 activate
  advertise-all-vni
 exit-address-family
vrf tenant1
 vni 5001
router bgp 65101 vrf tenant1
 address-family ipv4 unicast
  redistribute connected
 address-family l2vpn evpn
  advertise ipv4 unicast
vtysh -c 'show evpn vni' -c 'show bgp l2vpn evpn route' -c 'show bgp l2vpn evpn summary' -c 'show evpn mac vni all' -c 'show evpn arp-cache vni all'
```

Verification: VTEP loopbacks reachable (underlay ECMP), BGP EVPN sessions established, every VTEP present in type-3 routes for each VNI, hosts' type-2 routes in all VTEPs, MAC/ARP tables populated, `bridge fdb show` entries toward remote VTEPs, symmetric IRB path ping between tenants on different leaves, and MTU (`ping -M do -s 8900`).

### Common EVPN/VXLAN pitfalls

Underlay MTU too small; VTEP loopbacks not advertised; route targets mismatched (routes arrive but are not imported); duplicate anycast gateway MAC conflicts; spine rewriting next hops; asymmetric IRB in a large fabric (every leaf needs every VNI); ARP suppression disabled and BUM storms; ECMP polarization because the hash ignores the outer UDP source port; missing resilient hashing; split brain on MLAG mixed with EVPN multihoming; tenant routes leaking due to default import `any`.

## 5. Overlays for AI clusters and containers

- **RoCE and overlays**: RDMA fabrics for GPU-to-GPU traffic are normally routed IP/Ethernet *without* VXLAN (native IP), because encapsulation costs MTU, hardware complexity and lossless-queue mapping; overlay-based multi-tenancy tends to be applied at the front end (storage, inference, management) or with NIC/DPU offload for the back end. When VXLAN carries RoCE, ensure ECN/PFC markings are copied (DSCP inner → outer) and queue mappings preserved; verify ASIC and NIC support.
- **Tenant isolation**: EVPN-VXLAN VRFs/MAC-VRFs per tenant, with GBP or ACLs for microsegmentation, combined with performance isolation (chapter 2.16 section 7, chapter 2.19).
- **Kubernetes CNIs**: Flannel (VXLAN mode), Calico (IPIP/VXLAN or native BGP), Cilium (VXLAN/Geneve or native routing, eBPF), Antrea (Geneve). Overlay mode lowers pod MTU, adds CPU cost, and hides pod IPs from the fabric; native routing (BGP) is preferred for performance-critical clusters (chapter 5 and 2.25). Debug with `ip -d link show flannel.1`, `bridge fdb`, `tcpdump -ni eth0 udp port 8472` (Flannel/Cilium default) or `4789`.
- **Site-to-site and hybrid**: WireGuard/IPsec tunnels between clouds and on-prem; BGP over the tunnel; mind MTU, key rotation, and throughput limits of single-flow encryption (single-core bound).
- **Observability**: monitor both layers: overlay (VNI counters, MAC tables, EVPN routes) and underlay (BFD, interface errors); synthetic probes between VTEPs *and* between workloads.

## 6. Segment routing

**Segment routing (SR)** is source routing with a twist: the ingress node encodes the path as a list of **segments**, each identified by a **SID**, and the network follows the instructions with no per-flow state in transit nodes. It may or may not count as a tunnel, depending on implementation (MPLS labels or IPv6 headers).

- **Node SID**: a globally unique label/identifier for each router (e.g. A=101, B=102 ... K=107), advertised with the router's loopback by the IGP. A path is a label stack of node SIDs: A to K via [B,E,F,H] = [101,104,105,107] (illustrative numbers), via [B,D,G,H] = [101,103,106,107]. Specifying fewer labels leaves the intermediate routing to the normal shortest path (so [103,107] means "go to D by shortest path, then to H").
- **Adjacency SID**: locally significant label for a specific link (needed to choose one of two parallel links between D and H).
- **Prefix SID / binding SID / anycast SID** exist for prefixes, policies, and groups.

### SR-MPLS

Uses MPLS labels: a 32-bit header with a 20-bit label, 3-bit traffic class, bottom-of-stack bit, and 8-bit TTL. MPLS operations: **PUSH** a label, **POP** the top label, **SWAP** the top label. SR maps these as PUSH (ingress imposes the stack), POP (each node removes its own label as the packet passes) and **CONTINUE** (swap with the same label so processing of this segment continues until the node SID's owner is reached). Labels come from the **SR Global Block (SRGB)** and are distributed in the IGP (IS-IS/OSPF extensions) or BGP-LS. Example forwarding of stack [103,104,202,105,106,109,110]: each hop pops the top label that names it or its adjacency and forwards. Packet recycling in ASICs makes multi-label processing possible.

### SRv6

Segments are 128-bit IPv6 addresses (SIDs) listed in a **Segment Routing Header (SRH)**, an IPv6 routing extension header; the active segment is copied into the IPv6 destination address, `segments left` counts down. A SID = **locator** (routable prefix of the node) + **function** (End, End.X adjacency, End.DT4/DT6 for VRF decap, End.DX2 for L2VPN...) + **argument**. **uSID** (micro-segment) packs several 16-bit SIDs into one 128-bit address to shrink headers. SRv6 can carry IPv4 or IPv6 and provides VPN services (L3VPN, EVPN) without MPLS.

### Signalling and control

SIDs and topology are flooded by the IGP; paths are computed on the headend or by a controller (PCE) using BGP-LS for topology and PCEP/BGP SR-TE for installing policies; **TI-LFA** gives sub-50 ms protection (chapter 2.13). Segment routing is common in carrier networks; its role in AI fabrics is under study (controller-driven path pinning, chapter 2.16).

## 7. SD-WAN

**Software-Defined WAN** applies overlay + central control to the wide-area problem: sites connect over multiple underlay transports (MPLS, broadband, LTE/5G), each site's edge builds encrypted tunnels (IPsec/WireGuard or vendor protocols) over every transport, a **central controller/orchestrator** distributes policy and reachability, edges measure path quality (loss, latency, jitter) with probes and steer applications per policy (voice on the best path, bulk on the cheap one), and zero-touch provisioning brings edges up. Underneath, it is the same ideas: encapsulation, a reachability control plane (often an overlay BGP/OMP), and policy-driven path selection. Relevance here: multi-site GPU clouds, hybrid cloud connectivity and edge inference sites often use SD-WAN or its cloud-native equivalents (cloud routers, transit gateways, Cloud Interconnect). Evaluate throughput per tunnel, MTU, key management, and failure behaviour.

## 8. Complexity and virtualization

Virtualization is a trade: simplified endpoints and policy at the price of more state, more layers and more failure modes.

- **Interaction surfaces**: where two systems (the underlay and overlay control planes, or two tunnels) touch, the behaviour of each can disturb the other. If the overlay reacts to an underlay event faster or slower than the underlay reconverges, flapping and blackholes can occur; if the overlay reroutes traffic into a tunnel that is itself carried over the failed path, you get loops or oscillation. Keep interactions few, narrow and documented; tune timers so the underlay converges (BFD, ECMP) before the overlay times out.
- **Shared fate and shared risk link groups (SRLGs)**: two logically separate overlay paths might traverse the same physical link, conduit or switch, so a single physical failure kills both "redundant" paths. Map overlay redundancy to the underlay's real diversity: separate switches/racks/power/fibre routes; model SRLGs in the controller; verify with topology data and tests.
- **Overlaid control planes**: each additional control plane (EVPN over BGP over IS-IS) adds convergence dependencies and operational skills; the failure of one can look like a failure of another. Run explicit end-to-end tests at each layer.
- **State**: tunnel meshes scale with endpoints; per-tenant VRFs multiply tables; hardware limits (VNIs, VTEPs, MAC/route scale) bind the design.
- **MTU and fragmentation**: every encapsulation shrinks the usable MTU; PMTUD is unreliable; set MTU at the encapsulation point.
- **Observability and troubleshooting**: you need tools that show inner and outer headers (tcpdump/Wireshark with decoders), overlay path tracing (`ping`/`traceroute` in the VRF, VXLAN OAM, `evpn` show commands), and correlation between layers.
- **Security**: tunnels hide traffic from underlay inspection; encryption protects confidentiality but blinds firewalls; segment boundaries must be enforced at the VRF/ACL layer, not only by "being in another VNI".
- **Performance**: encapsulation and encryption use CPU unless offloaded; ECMP entropy can fall; latency adds a little per hop; check NIC tunnel offloads.

Rule of thumb: virtualize only where the isolation, mobility or policy benefit justifies the added complexity, and prefer simpler options (routed hosts, VRF-lite, native routing) where they suffice.

## 9. Hands-on lab: tunnels, VXLAN, and EVPN

First, run the self-checking Python lab (`code/part02/overlays_vxlan_evpn_lab.py`) locally. It verifies EVPN Route Types `1`–`5`, Asymmetric vs Symmetric IRB per-leaf VNI state scaling (`200` vs `6` VNIs), SR-MPLS label-stack `POP` progression (`[101, 104, 105, 107]`), and Shared Risk Link Group (`SRLG`) overlay fate-sharing checks.

```bash
python3 code/part02/overlays_vxlan_evpn_lab.py
```

Next, on a disposable Linux VM using network namespaces and containerlab with FRR (all interactive VM commands below are `untested here`), work through these steps:

1. **GRE and IPIP with namespaces**: build the diamond topology from chapter 2.5; create a GRE tunnel between the end routers; observe the recursive lookup with `ip route get`, packet capture of outer and inner headers at the transit router; compute MTU; break PMTUD with an ICMP drop and fix with MSS clamping.
2. **VXLAN point-to-point**: two namespaces/VMs; VXLAN with static remote; capture UDP/4789; show source port variation across flows; inspect `bridge fdb`; change MTU and test large pings.
3. **Head-end replication**: three VTEPs with all-zero FDB entries; ARP across them; observe BUM replication count; then enable proxy ARP/`nolearning` and compare.
4. **Bridge + VXLAN segment**: attach namespaces to a bridge with VXLAN; move an IP between hosts (simulate migration) and watch MAC learning.
5. **EVPN in containerlab**: 2 spines, 3 leaves, FRR; underlay eBGP unnumbered (chapter 2.16 lab); enable `l2vpn evpn`, `advertise-all-vni`; create VNI 10100 across leaves; inspect type 3 and type 2 routes, ARP suppression, MAC mobility (move a host container between leaves); add symmetric IRB with L3VNI and anycast gateway; ping between subnets and check `show bgp l2vpn evpn route type prefix`.
6. **Multihoming (optional)**: dual-attach a host with an ESI and LACP to two leaves; fail one; observe type 1/4 routes and convergence.
7. **Tenant isolation**: two VRFs with overlapping IP ranges; show isolation; leak a route with RT import; add GBP/ACL microsegmentation conceptually.
8. **WireGuard**: a site-to-site tunnel between namespaces; measure throughput and MTU; add BGP over the tunnel.
9. **Segment routing demo**: use Linux `ip route add ... encap mpls` or `encap seg6` (SRv6) in namespaces to implement a two-segment path across a diamond topology; observe which transit routers see packets.
10. **Troubleshooting drill**: introduce faults (wrong RT, MTU 1500 underlay, missing VTEP route, duplicate gateway MAC) and diagnose with the layered method.
11. **Clean up**.

## 10. Common mistakes

- Forgetting the MTU tax; tunnels working for small pings but hanging for real traffic.
- No ECMP entropy for non-UDP encapsulations; hashing only on outer addresses.
- Treating the overlay as independent of the underlay (and not monitoring both).
- Mismatched route targets/VNI maps; non-unique RDs; not planning VNIs and VRFs.
- Using EVPN/VXLAN where routing would do; stretching L2 widely for convenience.
- Believing VNI separation equals security without ACL/VRF discipline.
- Ignoring shared risk groups when claiming path redundancy.
- Running RoCE through an overlay without verifying lossless queue handling.

## 11. Interview angles

- "What are underlay and overlay? What happens to a packet in a tunnel hop by hop?"
- "How does VXLAN differ from a VLAN; what is a VTEP; how is BUM traffic handled?"
- "What does EVPN add to VXLAN? Name the route types and their purposes."
- "Symmetric versus asymmetric IRB; what is an anycast gateway?"
- "How do you handle MTU in an overlay?"
- "How does the underlay get entropy for ECMP with VXLAN?"
- "Explain segment routing node and adjacency SIDs; what are PUSH/POP/CONTINUE?"
- "What are SD-WAN's building blocks?"
- "What is an SRLG and why does it matter for overlay redundancy?"
- "Why do GPU back-end fabrics usually avoid overlays?"

## Exercises

1. **Tunnels, Overlays, Underlays, Recursive Lookups, and the Two Core Virtualization Questions (`CN` Chapter 9):** (a) Trace the 5 steps of a packet sent from Host A through tunnel headend Router C, underlay transit Router E, and tunnel tailend Router H to Host M, explaining the **recursive lookup** at Router C and how **VRFs** change the lookup tables; (b) state the two mandatory questions (plus the optional QoS question) that every network virtualization solution must answer.
2. **Comparing Encapsulations (`GRE`, `IPIP`, `VXLAN`, `Geneve`, `MPLS`, `SRv6`, `WireGuard`, `IPsec`) and ECMP Entropy:** Compare the byte overhead and outer header structure of `GRE` (`24` B), `IPIP` (`20` B), `VXLAN` (`50` B, `UDP 4789`), `Geneve` (`50+` B, `UDP 6081`), `MPLS` (`4` B/label), `SRv6`, `WireGuard`, and `IPsec ESP`. Why do `VXLAN` and `Geneve` balance across underlay ECMP links automatically while `GRE` and `IPIP` pin to a single link unless inner-header hashing is enabled?
3. **VXLAN (`VNI`, `VTEP`, BUM Handling) and BGP `EVPN` Route Types `1`–`5`:** (a) Contrast VXLAN data-plane **flood-and-learn** (multicast or head-end replication `00:00:00:00:00:00` FDB entries) with the **BGP `l2vpn evpn` control plane** (`RFC 7432` / `RFC 8365`); (b) list the name and exact role of **EVPN Route Types `1`, `2`, `3`, `4`, and `5`** (`EVPN_ROUTE_TYPES` in `code/part02/overlays_vxlan_evpn.py`), and distinguish a **Route Distinguisher (`RD`)** from a **Route Target (`RT`)**.
4. **Distributed Anycast Gateway and Asymmetric vs. Symmetric `IRB`:** Explain how a **distributed anycast gateway** works on leaf switches, and use `compute_irb_vni_scaling_per_leaf()` to compare how many VNIs must be configured on a leaf switch when a cluster has `200` total tenant L2 subnets (`5` present locally on that leaf) under **Asymmetric IRB** (`200` VNIs) versus **Symmetric IRB** (`6` VNIs using an **L3 VNI**).
5. **Segment Routing (`SR-MPLS` and `SRv6` / `uSID`) and `SD-WAN` (`CN` Chapter 9):** (a) Distinguish a **Node SID** from an **Adjacency SID**, and trace `simulate_sr_mpls_label_stack([101, 104, 105, 107], [101, 104, 105, 107])` explaining MPLS `PUSH`, `POP`, and `CONTINUE` (`SWAP`); (b) describe the three parts of a `128`-bit **SRv6 SID** (`Locator : Function : Argument`) and `16`-bit **`uSID`s**, and summarize the core building blocks of **SD-WAN**.
6. **Virtualization Complexity: Interaction Surfaces, `SRLG` Shared Fate, and AI Back-End Fabrics:** (a) Using `check_overlay_srlg_diversity()`, explain why two logically separate overlay tunnels fail simultaneously if their underlay paths share a **Shared Risk Link Group (`SRLG`)** (`conduit-north`), and explain what happens if overlay failure detection timers are faster than underlay BFD/ECMP convergence; (b) give four reasons GPU back-end RoCEv2/InfiniBand fabrics avoid VXLAN overlays on the collective path.

## Checkpoint questions (20)

<details>
<summary>1. Define a Tunnel, an Overlay, an Underlay, and a Recursive Lookup (`CN` Chapter 9).</summary>
A **tunnel** is a virtual point-to-point link where an outer header encapsulates an inner packet and intermediate devices forward based on the outer header alone. An **overlay** is a complete virtual network topology built from tunnels, and the **underlay** is the physical/routed network that transports the tunnel packets. When a headend router routes an inner packet into a tunnel interface, it performs a **recursive lookup** in the underlay routing table to find the next hop and outgoing physical interface toward the tunnel tailend (`VTEP`) IP.
</details>

<details>
<summary>2. What two fundamental questions (plus one optional question) must every network virtualization technology answer?</summary>
(1) **Data encapsulation**: how are packets wrapped so virtual traffic is isolated from the underlay (accounting for MTU tax and ASIC/ECMP hash support)?\n(2) **Control-plane reachability advertisement**: how do tunnel headends learn which inner MAC/IP destinations sit behind which tunnel tailend (integrated into one routing table vs a separate overlay control plane / VRF)?\n(3) **Optional QoS / traffic engineering**: how are inner QoS markings (`DSCP`, `PCP`, `ECN`) copied to the outer header and mapped onto underlay queues?
</details>

<details>
<summary>3. Compare `VXLAN` (`RFC 7348`), `Geneve` (`RFC 8926`), `GRE`, and `IPIP` across header overhead, UDP ports, and underlay ECMP entropy.</summary>
- **`VXLAN`**: `50` bytes overhead on IPv4 (`14`B outer Eth + `20`B IP + `8`B UDP + `8`B VXLAN), **UDP destination port `4789`** (Linux legacy/Flannel default `8472`), fixed 8-byte header with a **24-bit `VNI` (`16,777,216` segments)**.\n- **`Geneve`**: `50+` bytes overhead, **UDP destination port `6081`**, 24-bit VNI plus **variable-length extensible TLV options** (used by OVN-Kubernetes, Cilium, Antrea).\n- **`GRE`**: `24` bytes overhead (`IP protocol 47`, no UDP port).\n- **`IPIP`**: `20` bytes overhead (`IP protocol 4`, no UDP port).\nBecause `VXLAN` and `Geneve` wrap packets in UDP and **set the outer UDP source port to a hash of the inner packet's 5-tuple**, standard underlay switches automatically distribute flows across ECMP links.
</details>

<details>
<summary>4. What are a `VNI` and a `VTEP` in VXLAN, and how does VXLAN handle `BUM` (*Broadcast, Unknown-unicast, Multicast*) traffic without EVPN?</summary>
The **`VNI`** (*VXLAN Network Identifier*) is the 24-bit segment ID that identifies the virtual L2/L3 domain; the **`VTEP`** (*VXLAN Tunnel Endpoint*) is the switch, hypervisor, DPU, or Linux kernel interface (`vxlan0`) that encapsulates and decapsulates VXLAN packets using its underlay IP (typically a `/32` loopback). Without a control plane (**flood-and-learn**), a VTEP floods **BUM** frames either via an **underlay IP multicast group** per VNI or via **head-end replication** (sending a separate unicast copy to every remote VTEP listed in its `00:00:00:00:00:00` FDB entry) and learns remote MACs from incoming data packets.
</details>

<details>
<summary>5. What does `BGP EVPN` (`RFC 7432` / `RFC 8365`, address family `l2vpn evpn`) replace in VXLAN?</summary>
**BGP EVPN** replaces data-plane flood-and-learn with a **proactive MP-BGP control plane**: each leaf VTEP learns attached host MAC and IP addresses locally (from port attachment, ARP, or ND) and advertises them to all other VTEPs in **`l2vpn evpn` BGP updates**, eliminating unknown-unicast flooding, enabling local ARP/ND suppression, and unifying L2 bridging and L3 routing (`IRB`) in one protocol.
</details>

<details>
<summary>6. Match all five `BGP EVPN` Route Types (`1` through `5`) to their exact functions.</summary>
- **Route Type `1` (*Ethernet Auto-Discovery*)**: advertises per-Ethernet-Segment (`ES`) and per-EVI reachability for **active-active multihoming aliasing** and **fast mass withdrawal** on link failure.\n- **Route Type `2` (*MAC/IP Advertisement*)**: advertises a specific host **MAC address** (and optional **IPv4/IPv6 address**), its `L2 VNI` (and `L3 VNI`), `VTEP` next hop, and **MAC mobility sequence number**.\n- **Route Type `3` (*Inclusive Multicast Ethernet Tag, `IMET`*)**: announces that a VTEP participates in a given `VNI`, automatically building the **head-end replication list for BUM traffic**.\n- **Route Type `4` (*Ethernet Segment*)**: discovers VTEPs attached to the same multihomed 10-byte **`ESI`** and elects the **Designated Forwarder (`DF`)** for BUM traffic toward the server.\n- **Route Type `5` (*IP Prefix*)**: advertises **IPv4/IPv6 subnet prefixes** (`RFC 9136`) and external routes into tenant `IP-VRF`s.
</details>

<details>
<summary>7. What is the difference between a Route Distinguisher (`RD`) and a Route Target (`RT`) in EVPN / VPNs?</summary>
- **Route Distinguisher (`RD`, 64-bit, e.g. `10.255.0.11:100`)**: prepended to a MAC or IP prefix solely to make overlapping tenant addresses **globally unique inside BGP update messages** so route reflectors/spines do not overwrite Tenant A's `10.0.0.0/24` with Tenant B's `10.0.0.0/24`.\n- **Route Target (`RT`, BGP Extended Community, e.g. `65000:10100`)**: controls **policy import and export**—determining which `MAC-VRF`s and `IP-VRF`s on receiving VTEPs import the route into their tables.
</details>

<details>
<summary>8. How does EVPN `ARP/ND Suppression` work, and how does EVPN handle VM/container live migration (`MAC Mobility`)?</summary>
Because EVPN **Route Type 2** distributes both `(MAC, IP)` bindings to every leaf in the VNI, a leaf switch receiving an ARP Request (or IPv6 Neighbor Solicitation) for a remote host intercepts the request and **replies locally from its EVPN ARP cache** (**ARP/ND suppression**) instead of flooding the broadcast across the fabric. When a VM or container live-migrates to a new leaf, the new leaf originates a Type 2 route with an incremented **MAC Mobility extended-community sequence number**; all VTEPs immediately update their FDB to point to the new VTEP.
</details>

<details>
<summary>9. Contrast `Asymmetric IRB` and `Symmetric IRB` (*Integrated Routing and Bridging*), and explain why Symmetric IRB scales better.</summary>
In **Asymmetric IRB** (*bridge-route-bridge*), the ingress leaf routes the packet directly into the destination subnet's **L2 VNI**, and the egress leaf simply bridges it—requiring **every leaf switch in the data center to configure every single L2 VNI/subnet** even if no local hosts belong to that subnet. In **Symmetric IRB** (*bridge-route-route-bridge*), the ingress leaf routes the packet into a per-tenant **L3 VNI** (`IP-VRF`), and the egress leaf routes from the L3 VNI into the local destination L2 VNI—so each leaf only needs its **locally attached L2 VNIs plus one L3 VNI per tenant**.
</details>

<details>
<summary>10. What is a Distributed Anycast Gateway in an EVPN fabric, and what must match across all leaf switches?</summary>
With a **Distributed Anycast Gateway**, every leaf switch serving a subnet configures the **exact same default gateway IP address AND the exact same virtual MAC address** on its local VLAN SVI. Every host or VM always routes through its local top-of-rack leaf in 1 hop, and if a VM live-migrates to another rack, its cached default-gateway IP and MAC remain 100% valid on the new leaf without re-ARPing.
</details>

<details>
<summary>11. Why must spine switches acting as EVPN route servers set `next-hop-unchanged` on `l2vpn evpn` eBGP sessions?</summary>
In an EVPN overlay, the BGP **`NEXT_HOP`** of a Type 2, Type 3, or Type 5 route is the originating leaf's **VTEP loopback IP**, which remote leaves use as the outer VXLAN destination IP. Normally, `eBGP` rewrites `NEXT_HOP` to the spine's own IP; unless the spine leaves `NEXT_HOP` unchanged (or terminates and re-originates VXLAN tunnels itself), spines would attract encapsulated VXLAN packets they do not know how to bridge.
</details>

<details>
<summary>12. How do you configure a scalable Single-VXLAN-Device (`vxlan0` with `external` / `vnifilter`) on Linux for FRR EVPN?</summary>
Instead of creating hundreds of separate `vxlanN` netdevs and `brN` bridges (one per VNI), create one VLAN-aware bridge (`ip link add br0 type bridge vlan_filtering 1`) and a single VXLAN device (`ip link add vxlan0 type vxlan dstport 4789 local 10.255.0.11 nolearning external vnifilter`), enslaving `vxlan0` to `br0` and mapping VLANs to VNIs (`bridge vlan add dev vxlan0 vid 100` and `bridge vni add dev vxlan0 vni 10100`).
</details>

<details>
<summary>13. What are a `Node SID` and an `Adjacency SID` in Segment Routing (`RFC 8402`)?</summary>
- **Node SID**: a globally unique Segment Identifier advertised in the IGP (`OSPF`/`IS-IS`) representing a specific router's loopback; any router forwards packets carrying a Node SID along the **shortest IGP path (including ECMP)** toward that node.\n- **Adjacency SID**: a locally significant Segment Identifier advertised by a router representing a **specific outgoing local interface/link** to a neighbor—allowing a path to force traffic over one specific link without ECMP hashing.
</details>

<details>
<summary>14. How do `PUSH`, `POP`, and `CONTINUE` work in `SR-MPLS` (`CN` Chapter 9)?</summary>
An `SR-MPLS` label is a 32-bit shim header (`20`-bit label from the **SR Global Block `SRGB`**, `3`-bit Traffic Class, `1`-bit Bottom-of-Stack, `8`-bit TTL). At the ingress router, **`PUSH`** imposes an ordered stack of Node/Adjacency SIDs onto the packet (e.g., `[103, 107]`). Transit routers along the shortest path to `103` perform **`CONTINUE`** (MPLS `SWAP` with the same label `103`); when the packet reaches Node `103` (or its penultimate hop via `PHP`), `103` is **`POP`ped**, exposing `107` as the new active top label toward Node `107`.
</details>

<details>
<summary>15. How does `SRv6` (`RFC 8754` / `RFC 8986`) encode segments without MPLS, and what are `Locator`, `Function`, `Argument`, and `uSID`?</summary>
`SRv6` encodes each segment as a **128-bit IPv6 address** inside a **Segment Routing Header (`SRH`)** (or directly in the IPv6 Destination Address with `uSID`s). Each 128-bit SRv6 SID is structured as **`Locator : Function : Argument`**, where the **Locator** is the routable IPv6 prefix of the target node, the **Function** specifies the local action to execute upon arrival (`End` = advance segment, `End.X` = cross-connect out adjacency, `End.DT4`/`End.DT6` = decapsulate and look up in IPv4/IPv6 VRF), and the **Argument** passes optional parameters. **`uSID` (*micro-SID*)** packs up to six 16-bit micro-segments into one 128-bit IPv6 address.
</details>

<details>
<summary>16. What are the core architectural components of an `SD-WAN` solution (`CN` Chapter 9)?</summary>
(1) Edge appliances (`vEdge` / `cEdge`) terminating multiple heterogeneous underlay transports (`MPLS`, broadband Internet, `5G`/LTE); (2) encrypted **IPsec / WireGuard overlay tunnels** built across all transports; (3) a **centralized control plane / orchestrator** (`OMP` / BGP over TLS) distributing routes, keys, and security policies without full-mesh IKE complexity; and (4) **continuous active/passive path-quality probing** (loss, latency, jitter) that steers applications dynamically onto transports meeting their SLA.
</details>

<details>
<summary>17. What are \"Interaction Surfaces\" and \"Shared Risk Link Groups\" (`SRLG`s) in virtualized networks (`CN` Chapter 9)?</summary>
**Interaction surfaces** are the touchpoints where the overlay control plane and underlay control plane interact (for example, if an overlay BFD/keepalive timer is shorter than the underlay's ECMP/BFD convergence time, a single underlay link flap causes the entire overlay to tear down and churn). A **Shared Risk Link Group (`SRLG`)** is a set of logically separate overlay links that share a **single physical failure domain** in the underlay (such as the same fiber trench, patch panel, line card, or spine switch), causing "redundant" overlay paths to fail simultaneously (**fate sharing**).
</details>

<details>
<summary>18. Why do high-performance AI GPU back-end fabrics (RoCE v2 and InfiniBand) generally avoid running VXLAN overlays on the collective path?</summary>
(1) **MTU and goodput tax** (`50` bytes per packet); (2) **Lossless QoS complexity** (inner `DSCP`/`ECN` bits must be copied to outer headers on encapsulation and restored on decapsulation, and `PFC` pause frames operate on the physical link); (3) **Hardware RDMA offload constraints** (NICs must support stateless RDMA + VXLAN encap/decap and BTH UDP source-port entropy simultaneously); and (4) **Two-layer troubleshooting overhead** during collective stalls.
</details>

<details>
<summary>19. If RoCE v2 traffic MUST traverse a VXLAN overlay, what three QoS/hardware requirements must be verified?</summary>
(1) The VTEP (switch ASIC or DPU/NIC) must copy the inner IP **`DSCP` and `ECN` bits to the outer VXLAN IP header** on encapsulation and **copy outer `ECN` (`CE = 11`) markings back to the inner IP header on decapsulation** so end-to-end `DCQCN` congestion control still works;\n(2) Outer UDP source ports must preserve **per-QP hash entropy**;\n(3) Underlay switches must honor the outer `DSCP`/`PCP` mapping into lossless **`PFC`** queues with sufficient MTU (`9216`).
</details>

<details>
<summary>20. Walk through the layered troubleshooting sequence when Host A in VNI `10100` on Leaf 1 cannot ping Host B in VNI `10100` on Leaf 3.</summary>
(1) **Check the underlay first**: from Leaf 1, `ping -M do -s 8900 <Leaf3-VTEP-loopback>` to verify underlay reachability and jumbo MTU between VTEPs;\n(2) **Check EVPN control-plane sessions**: `show bgp l2vpn evpn summary` (are sessions `Established`?);\n(3) **Check VNI membership (Type 3 routes)**: `show evpn vni 10100` (does Leaf 1 see Leaf 3's VTEP IP in the Type 3 BUM replication list, and do Route Targets match?);\n(4) **Check host MAC/IP learning (Type 2 routes)**: `show evpn mac vni 10100` and `show bgp l2vpn evpn route type macip` (was Host A learned locally on `br0` and advertised, and was Host B's Type 2 route received and installed in `bridge fdb show dev vxlan0`?); and\n(5) **Capture on the underlay**: `tcpdump -ni swp1 udp port 4789` to verify encapsulated packets leave and arrive.
</details>

## Sources and review notes

- **Sources read in full:**
  - `computer-networking-problems-and-solutions` — Russ White and Ethan Banks, *Computer Networking Problems and Solutions*, **Chapter 9: Network Virtualization** (understanding virtual networks, tunnels vs overlays vs underlays, VRFs and recursive lookups, Ethernet services over IP, virtual private access, segment routing with MPLS and IPv6, signaling, SD-WAN, complexity and virtualization, interaction surfaces, Shared Risk Link Groups `SRLG`s, and overlaid control planes).
  - `ai-data-center-network-design-and-technologies` — Dinakaran Setty et al., *AI Data Center Network Design and Technologies*, **Chapter 8: IP Routing for AI/ML Fabrics** (EVPN-VXLAN multi-tenancy, VXLAN Group-Based Policy `GBP` microsegmentation, and SRv6/uSID).
  - `networking-and-kubernetes` — James Strong and Vallery Lancey, *Networking and Kubernetes*, **Chapter 3: Container Networking Basics** (container networking overlays, VXLAN, Geneve, and IPIP; Linux `veth` and CNI plugin mechanics are covered in full in Chapter 2.25).
  - `how-linux-works-3rd-edition` — Brian Ward, *How Linux Works*, 3rd ed., **Chapter 9: Understanding Your Network and Its Configuration** (Linux `iproute2` interface and bridge fundamentals).
- **Run here:** `python3 code/part02/overlays_vxlan_evpn_lab.py` (10 passed, 0 failed).
- **Explicitly labelled inferences:** The Linux `ip link add type vxlan` (`external vnifilter`) and FRR `l2vpn evpn` Symmetric IRB (`L3VNI 5001`) configurations, EVPN Route Types `1`–`5` table, and layered VTEP-to-VTEP troubleshooting sequence synthesize RFCs 7348 (VXLAN), 7432 (EVPN), 8365 (EVPN Overlay), 8402 (Segment Routing), 8926 (Geneve), 8986 (SRv6), and 9136 (EVPN IP Prefix Route) and the FRR/containerlab documentation (cross-referenced with Chapters 2.5, 2.7, 2.11–2.16, 2.19, 2.25, and 2.27, plus original study items 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, and 40).
- **Not verified on live hardware:** All interactive VM and FRR commands (`ip link add type vxlan`, `bridge fdb`, `bridge vni`, `vtysh`, `show evpn vni`, `show bgp l2vpn evpn`, `tcpdump udp port 4789`) are marked (untested here) and must be executed on a disposable Linux VM or containerlab topology.
