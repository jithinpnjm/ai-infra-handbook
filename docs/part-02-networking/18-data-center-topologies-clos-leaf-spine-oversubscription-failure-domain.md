---
id: "c02-18"
title: "2.18 Data-center topologies: Clos, leaf-spine, oversubscription, failure domains and resilience"
sidebar_label: "2.18 Data-center topologies: Clos, leaf-spine, oversubscription, failure domains and resilience"
sidebar_position: 18
description: "Design patterns, fabrics, leaf-spine and Clos sizing, rail-optimised AI topologies, dragonfly, torus, multi-planar, resilience"
status: "drafted"
tier: "2"
level: "A"
lab_venue: "GCP / GKE"
---

# 2.18 Data-center topologies: Clos, leaf-spine, oversubscription, failure domains and resilience

| | |
|---|---|
| Level | Advanced |
| Priority tier | 0 |
| Lab venue | Paper design + containerlab for validation |
| Part | Part 2: Networking, from first principles to AI fabrics |
| Status | Drafted, labs **untested** |

## Why this matters for AI infrastructure

The topology is the one decision that is hard to change after racks are cabled. It fixes how many GPUs a cluster can hold, the latency between any two of them, how much bandwidth survives a failure, whether collectives run at line rate or stall behind a hot link, and how much the whole thing costs in switches, optics and cables. NVIDIA, Meta, Google, Microsoft and others publish reference designs (rail-optimised leaf-spine, multi-plane Clos, dragonfly variants); you need to read them, size them (ports, switches, oversubscription), and defend or critique them in a design review or interview. This chapter covers general network design patterns, what makes a network a fabric, leaf-spine and Clos scaling math, oversubscription and contention, the AI-specific variants (rail-optimised, rail-unified, rail-only, scheduled fabrics, dragonfly, torus, multi-planar), rack and cabling layout, failure domains and information hiding examples, and resilience (redundancy, SRLGs, graceful restart, multi-plane cores).

## Prerequisites and outcomes

You should know ECMP/LAG (2.12), routing (2.13 to 2.16), overlays (2.17) and how a switch moves a packet (2.11).

After this chapter you can:

- Translate business requirements into network requirements and judge a design by cost, performance, resilience, operability and growth.
- Describe hierarchical designs and ring, mesh, hub-and-spoke, planar/nonplanar and regular topologies with their trade-offs.
- Define a fabric (regular topology, scale-out, specific performance goals) and distinguish it from a hierarchical network; define leaf, spine, super-spine, stage count, oversubscription, non-blocking versus non-contending.
- Size a 3-stage and 5-stage Clos (radix, number of leaves/spines, GPUs supported, links, optics) and compute oversubscription and failure-case capacity.
- Describe rail-optimised, rail-unified and rail-only designs, intra-rail versus inter-rail traffic, ToR/MoR/EoR rack layouts.
- Describe scheduled/cell-based fabrics with VOQ, dragonfly (and sparse dragonfly), torus, and multi-planar architectures and their trade-offs for AI.
- Apply information hiding (summarisation, aggregation, layering, exponential backoff, flooding reduction) as examples and design failure domains.
- Define MTBF, MTTR, availability ("nines"), single points of failure, SRLGs, ISSU, graceful restart, dual/multi-plane cores and modularity.
- Produce and critique a topology design for a given GPU count.

## 1. Network design patterns

### From business needs to a network

Networks exist to support applications, which support the business; design starts with *requirements*, not products. A workable translation:

| Business statement | Technical requirement |
|---|---|
| "Training a 70B model must finish in N days" | Sustained collective bandwidth per GPU, tail latency of all-reduce, job-completion-time SLO |
| "We sell GPU time to three customers" | Tenant isolation, per-tenant bandwidth, auditability |
| "Outage costs $X per minute" | Availability target (nines), failure-recovery time, redundancy, maintenance without downtime |
| "Budget is fixed; plan 3-year growth" | Cost per port, oversubscription decisions, expansion by adding pods without recabling |
| "Run in two regions" | Inter-site bandwidth, latency, failure domains, replication |

A **good network design** satisfies the requirements at acceptable cost while being *operable* (simple enough to understand, automate, troubleshoot and upgrade), *scalable* (grows by adding repeatable units), *resilient* (failure handled automatically and locally), *secure*, and *measurable*. The recurring theme is trade-offs among **state, optimality, surface and cost**: more optimal paths need more state; more resilience needs more redundancy and complexity; simple designs may waste capacity. Avoid designs only the author can operate.

### Hierarchical design

The classic campus/enterprise model: **access** (hosts attach), **distribution/aggregation** (policy, summarisation, L2/L3 boundary), **core** (fast transport). Benefits: summarisation points limit failure domains, policy is applied at known layers, modular growth, and a clear mental model. Costs: capacity must grow *up* (bigger core links and boxes), oversubscription compounds layer by layer, and east-west traffic hairpins through upper layers.

### Common topologies

- **Ring**: each node has two neighbours; cheap, simple; survives one cut (traffic reverses direction) but latency grows with ring size and a second failure partitions. Metro/transport networks and some campus backbones. **Torus** extends rings into multiple dimensions.
- **Mesh**: full mesh gives direct paths between every pair (n(n-1)/2 links; not scalable); **partial mesh** links selected pairs. Great for small cores and for the groups inside a dragonfly.
- **Hub-and-spoke**: sites connect to a hub; cheap and easy to control (policy at the hub) but the hub is a bottleneck/single point of failure and spoke-to-spoke traffic hairpins; typical WAN/branch designs; dual-hub mitigates.
- **Planar vs non-planar, regular**: a planar topology can be drawn without crossing links (rings, trees); non-planar ones (meshes, hypercubes, Clos) cannot. **Regular** topologies repeat identical units, which simplifies configuration, automation and spares.

## 2. What makes a fabric?

"Fabric" is overused in marketing. The useful definition has three parts:

1. **Topological regularity**: the topology consists of many identical, interchangeable sub-topologies (every pod, every leaf-spine block looks the same), designed for replicable hardware, software and configuration.
2. **Scale-out growth**: bandwidth and port count grow by adding more equipment of the same kind (another pod, another spine), not by replacing devices with bigger ones. (Hierarchical networks scale *up*: bigger aggregation/core boxes and links; fabrics scale *out*, within the port-count limit of each device.)
3. **Specific performance goals**: failures are measured and handled at pod/rack/link granularity (applications tolerate being moved); workload mobility must converge very quickly; the metric of interest is **oversubscription** (edge bandwidth versus fabric bandwidth), and the goal is low *jitter* and low queueing delay as well as low latency, usually by avoiding contention rather than elaborate QoS.

Not a fabric by themselves: any overlay, any high-bandwidth network, any network with lots of ECMP, any network treated as one "thing". The disaggregation trend (below) is why fabrics became important: storage, memory and compute became network-attached or distributed, so *east-west* traffic dwarfs north-south.

### East-west, disaggregation and the jitter problem

In converged servers, all component traffic runs on an internal bus and the network sees mostly north-south traffic. With disaggregated storage, virtualised services, microservices and distributed training, processors fetch data across the network: hyperscale operators see roughly ten bits of east-west traffic per bit of north-south. Consequently application performance becomes tied to network **delay and jitter**: congestion that adds fractions of a second to data transfer slows the whole application, and one slow service cascades. AI training is an extreme case: synchronous collectives make every step wait for the slowest transfer. The network is part of the computer.

Terms: *converged* (all resources in one server), *disaggregated* (storage/memory/network reachable as virtual resources across the network; white-box hardware, because standardised virtual interfaces make brands interchangeable), *hyperconverged* (resources stay with the compute node but are virtualised and shared across nodes), *composable* (resources assembled on demand). Disaggregation also reached networking (white-box switches running open NOS such as SONiC or Cumulus on merchant silicon, separating hardware, NOS and applications) and enables the "network as software" operating models discussed in chapters 2.28 and 2.29.

## 3. Leaf-spine (folded Clos)

A **Clos network** (Charles Clos, 1953, for telephone switching) builds a large non-blocking switch from stages of smaller ones. Data-centre **leaf-spine** is a folded Clos:

- **Leaf / ToR** switches: servers and other devices attach here; all external connectivity enters through leaves.
- **Spine** switches: connect leaves; **no connections between spines** and **no devices attached to spines** (standard rule; cross-links add complexity).
- Every leaf connects to every spine (in a 3-stage fabric). Any two leaves are exactly two hops apart via any of S spines: S equal-cost paths.
- **Stages**: a leaf-spine counted unfolded is a 3-stage Clos (leaf-spine-leaf); adding a super-spine tier gives a **5-stage** fabric (leaf-spine-superspine-spine-leaf); 7-stage adds another tier. More stages give more ports but more hops and latency.

The control plane need not be complex (equal paths, no loops by construction); the complexity in real fabrics comes from compensating for cross-links, overlays and traffic engineering.

### Sizing a 3-stage fabric

Let switches have R ports (radix) of equal speed. For a non-oversubscribed (1:1) leaf: R/2 ports down (servers), R/2 up (spines). Then:

- Number of spines = R/2 (one uplink to each spine per leaf).
- Each spine has R ports; one to each leaf, so the maximum number of leaves = R.
- Maximum servers (endpoints) = R leaves × R/2 = **R²/2**.

For 64-port 400G switches: 32 downlinks + 32 uplinks per leaf; 32 spines; up to 64 leaves; up to 2,048 endpoint ports. In AI terms, each GPU NIC is an endpoint, so 2,048 GPUs (256 eight-GPU servers) with 2,048 spine-facing links, 64 leaves + 32 spines = 96 switches. Cabling: 2,048 server cables + 2,048 leaf-spine links.

Oversubscription changes the split: a leaf with d downlinks and u uplinks has ratio d:u (e.g. 48 down, 16 up = 3:1). Hyperscale general compute often runs 3:1; AI back-ends target **1:1** (no oversubscription) at the leaf-spine tier because collectives saturate NICs simultaneously.

### Five-stage fabrics

Beyond R²/2, build **pods** (a 3-stage fabric each) and connect pods with **super-spines**. With R-port switches, each pod uses half the spine ports downward (to leaves) and half upward (to super-spines). Maximum endpoints for a 1:1 5-stage Clos is R³/4 (for R=64: 65,536 endpoints). Intermediate sizes use partial pods and fewer super-spines. Illustrative sizing from a design reference (64 × 400G switches, rail-optimised):

| Config | GPUs | Leaves | Spines | Super-spines | Oversubscription |
|---|---|---|---|---|---|
| 1 row (one rail group) | 256 | 8 | 4 | none | 1:1 |
| 2 rows | 512 | 16 | 8 | none | 1:1 |
| 8 rows (3-stage, 64-port) | 2,048 | 64 | 32 | none | 1:1 |
| 5-stage, 1K-GPU blocks | 2,048 | 64 | 64 | 32 | 1:1 |
| 5-stage, 4 blocks | 4,096 | 128 | 128 | 32 | 2:1 at super-spine |
| 5-stage, 8 blocks | 8,192 | 256 | 256 | 32 | 4:1 at super-spine |

Observations: (a) beyond one 3-stage fabric you must either add stages, use **chassis** spines/super-spines (e.g. 256×400G chassis reduces the number of spines to a quarter), or oversubscribe the upper tier; (b) some operators evaluate **oversubscription up to 7:1** at the super-spine because most collectives are scheduled to stay inside a block, but higher ratios raise congestion probability, which then requires DCQCN/ECN/PFC and adaptive load balancing (chapter 2.19); (c) a 32K-GPU cluster at one NIC per GPU needs thousands of leaves, so multi-stage or multi-plane designs are unavoidable (section 7); (d) everything scales by adding the same unit. Treat these figures as arithmetic you should be able to reproduce, not as vendor guarantees.

### Oversubscription and contention

**Oversubscription ratio** = (aggregate bandwidth offered to endpoints) / (aggregate bandwidth into the fabric); equivalently, worst-case contention if all endpoints transmit at line rate across the tier. Example: a ToR with 320 Gb/s of server ports and 180 Gb/s of uplinks is 1.78:1 (about 2:1) oversubscribed.

**Non-blocking vs non-contending.**

- A **non-blocking** fabric has enough internal capacity that no *connection pattern* is blocked by fabric internals; packet-switched networks cannot be truly non-blocking, because several sources can send to one destination and the destination's link is the bottleneck even if the fabric is rich.
- A **non-contending** fabric (a stronger scheduling property) avoids any two flows competing for a link at the same time, as in circuit-switched networks where scheduling on the inbound side prevents conflicts.

For packet-switched fabrics one resolves *incast* either by scheduling (source-side admission, credit-based or request-grant flow control) or by adequate buffers, congestion signalling (ECN/DCQCN, PFC) and load balancing. Collectives create deterministic, synchronous, many-to-one patterns, so AI fabrics combine a 1:1 topology with congestion control and load balancing; and they exploit the fact that all-reduce algorithms (ring, tree) are designed to use bandwidth-optimal patterns.

### Capacity under failure

Always size for the failure case. With S spines and one spine failure, remaining uplink capacity per leaf is (S-1)/S (for 32 spines, 96.9%; for 4 spines, 75%). Since 1:1 designs have no slack, a failure makes the fabric oversubscribed until repaired; therefore: spare capacity (N+1 spines or rails), fast detection (BFD), rerouting, and job-level resilience (checkpointing, elastic training) are part of the design. Compute: "what fraction of leaf-to-leaf bandwidth survives losing a spine, a leaf, a link, a whole rail group, a power domain?"

## 4. AI back-end designs: rails

A server such as DGX/HGX H100 has 8 GPUs, an internal NVSwitch fabric for GPU-to-GPU traffic within the server, and typically one NIC per GPU (compute fabric) plus storage and management NICs. Inside the server communication is fastest; once a job spans servers, traffic crosses the network. How NICs attach to leaves defines the topology:

### Rail-optimised design (ROD)

GPU i of every server connects to leaf i of a group of 8 leaves (a **stripe** or **row**). All GPUs with the same index in different servers are *one hop apart* via the shared leaf: this is a **rail**. Collective algorithms (NCCL) are written to exploit it: reduce inside the server over NVLink first, then communicate across servers along rails, minimising inter-rail traffic.

- **Intra-rail** traffic (same GPU index on different servers) goes through one leaf: minimal latency.
- **Inter-rail** traffic (different GPU index) goes leaf → spine → leaf: twice the hops/latency; it should be rare (PXN, a NCCL feature, uses NVLink to send via the GPU on the destination's rail to avoid inter-rail hops).
- **Sizing example**: 64×400G leaf, 1:1: 32 down + 32 up ⇒ 32 servers per rail group; 8 leaves + 4 spines (if each leaf's 32 uplinks go to 4 spines with 8 links each) support 32 servers = 256 GPUs; two rows (16 leaves, 8 spines) support 64 servers = 512 GPUs; scale further with more spines, chassis spines or a super-spine.
- **Failure**: a leaf failure removes one rail for all servers in the stripe (each server loses 1/8 of its bandwidth, a degraded but functioning job, or the job restarts depending on library behaviour); a server NIC/cable failure removes one rail of one server.

### Rail-only design

If inter-rail traffic can be carried inside the servers over NVLink/NVSwitch (reach the target rail's GPU in-server, then go out its NIC), the fabric need not connect rails to each other at all: rails are independent networks, cheaper, simpler to troubleshoot (a fault in one rail doesn't affect others). The trade-off is dependence on in-server forwarding capacity and software, and less flexibility for non-collective traffic; adoption is still being evaluated.

### Rail-unified design (RUD)

Multiple GPUs of a server connect to the same leaf (all 8 to one leaf, or 4+4 to two leaves). Advantages: simple cabling, easy scaling, well-understood (a classic ToR design), copper DAC/AEC for short reaches, one-hop communication among up to a handful of servers (e.g. four servers on one leaf), potentially using the external leaf instead of the internal NVSwitch for in-server traffic if a higher-throughput switch is available. Disadvantages: a leaf failure isolates whole servers; per-rail traffic isolation inside the leaf needs additional features (e.g. deterministic path forwarding/colored fabrics, chapter 2.16); latency between servers on different leaves is two hops for everything.

### Rack and cable layout

| Layout | Description | Pros | Cons |
|---|---|---|---|
| **Top-of-rack (ToR)** | Leaf in each rack | Shortest server cables (DAC/AEC copper), simple; ideal for rail-unified | Needs more rack space/power/cooling in server racks; rail-optimised needs one server connected to 8 different leaves, so not natural |
| **Middle-of-row (MoR)** | Leaves in the middle racks of the row | Leaves do not add to server rack power; cable spans ~6 racks | More rack space; longer, varied cable lengths; no in-rack cabling |
| **End-of-row (EoR)** | Leaves in racks at the end | Same as MoR; can group leaves in 1+ racks for failure isolation | Longest cables (~10 racks) → optics or AOC; more space |

For rail-optimised builds, MoR/EoR is common because each server needs 8 leaf connections; cabling plans (pre-terminated MPO trunks, patch panels, labelling schemes, length standardisation) are a first-class design output. Power (each 8-GPU server draws ~10 kW; racks 20 to 40+ kW; liquid cooling), cooling and weight constraints often determine servers per rack more than the network does; the network is built around the physical plan.

## 5. Scheduled (cell-based) fabrics

Instead of per-packet hashing across equal paths, a **scheduled fabric** treats leaves as line cards and spines as the backplane of a giant chassis: packets arriving at the ingress leaf are cut into small **cells** (64 to 256 bytes) that are sprayed evenly across all fabric links, reassembled at the egress leaf, and forwarded. Implementations: Broadcom Jericho3-AI with Ramon3 fabric elements; Cisco Silicon One. Advantages: near-perfect link utilisation (cell spraying removes ECMP imbalance), **virtual output queues across the fabric** (the ingress holds packets per egress port, and a scheduler grants credits so the fabric is not oversubscribed: contention is avoided before it occurs, approaching non-contending behaviour), reduced tail latency, and simpler congestion handling than DCQCN alone. Constraints to evaluate: scale limits of the scheduled domain, behaviour on link/node failure (cell loss, reassembly), latency under congestion, vendor lock-in for the pod ("brick"), and operations model.

**VOQ** recap: each input keeps a virtual queue per output port, so congestion at one output does not block traffic to others (head-of-line blocking removed); with a fabric-wide VOQ the principle extends across the whole network.

## 6. Dragonfly, torus and other low-diameter topologies

Clos has diameter 2 (3-stage) or 4 (5-stage) switch hops. For cluster sizes in the tens of thousands, each extra stage adds latency and cost. Low-diameter topologies reduce hops and long links:

- **Dragonfly (DF, DF+)**: groups (also called blocks, bricks, pods) of switches, each group internally richly connected (full mesh, or a small Clos in DF+/sparse variants), and groups connected to every other group by global links, often all-to-all at the group level. Diameter is about three hops regardless of size. Benefits: fewer hops and lower latency, fewer spine layers and links, modular growth by adding groups, tolerant of group/component failures at reduced capacity. Costs: complex cabling between groups, **non-shortest-path routing** (valiant/UCMP) and adaptive routing needed for uniform traffic, uneven bandwidth for adversarial traffic patterns (all nodes in a group talking to another group over limited global links); applications/collectives should communicate mostly inside groups. A **sparse dragonfly** keeps each group as a leaf-spine Clos and connects only the top-of-group spines between groups.
- **Torus (1D/2D/3D, with wraparound)**: nodes connect to neighbours in each dimension. Diameter = sum over dimensions of ⌊size/2⌋. Cost-effective at very large scale (low port count per node), easy to scale out, excellent when applications use nearest-neighbour communication (stencils, some model-parallel layouts); poor for random all-to-all. Google's TPU pods use 3D torus interconnects (with optical circuit switching); in Ethernet fabrics a 1D torus of leaves can provide inter-rail connectivity instead of spines.
- **Hypercube, fat tree (see Clos), Slim Fly, HyperX**: other low-diameter topologies from HPC literature; relevant for comparison and papers.
- **Hybrid**: Clos inside a pod, dragonfly between pods; NVLink "scale-up" domains (NVL72) as a separate very-high-bandwidth tier inside the rack, with IP/IB scale-out above.

Trade-off table:

| Topology | Diameter | Cabling | Routing | Best for | Risk |
|---|---|---|---|---|---|
| 3-stage Clos | 2 | Moderate | ECMP (simple) | ≤ R²/2 endpoints; general AI | Port-count limit |
| 5-stage Clos | 4 | High | ECMP | Large clusters | Latency, super-spine oversubscription |
| Multi-plane Clos | 2 per plane | High (breakouts) | NIC spraying | 100K+ GPUs, reliability | NIC complexity |
| Dragonfly | ~3 | Group-to-group optics | Adaptive/non-minimal | Very large, low latency | Routing complexity, hot global links |
| Torus | Σ⌊n/2⌋ | Neighbour links | Dimension-ordered | Nearest-neighbour workloads | Poor bisection for all-to-all |
| Rail-only | 2 within a rail | Simple | ECMP per rail | Collectives w/ NVLink forwarding | Dependence on in-server routing |

## 7. Multi-planar scale-out

A single 3-tier Clos has one control plane and one data plane: a bug or failure can affect the entire fabric, and a 5-stage path adds a hop for jobs that span blocks. **Multi-planar** architectures replace one deep fabric with **several independent 2-tier planes**: each GPU NIC breaks out (400G/800G ports split into 2 or 4 lower-speed links) and connects to 2 or 4 planes simultaneously; the NIC (hardware and firmware) **sprays packets of a single queue pair across all planes** and reorders at the receiver so the application sees a single in-order flow. Properties:

- **Fault isolation**: planes have disjoint control and data planes; if one plane is down, a path to the GPU still exists at reduced capacity.
- **Latency**: two-tier planes keep inter-leaf traffic at spine depth; large jobs can be placed within a plane or across planes with only NIC spraying, while super-spines remain only to interconnect plane sets.
- **Complexity moves to the host**: packet spraying, reordering, and failure handling are NIC and library features (this is also the direction of Ultra Ethernet and vendor "multi-plane" NICs). Bridging on the server side must avoid Ethernet loops (EVPN-VXLAN MAC-VRF bridging over the IP underlay, or pure IP planes with ACL/RADIUS-based tenant control).
- **Example**: two planes with two rails each; a server's NIC1..8 connect to Rail A/B leaves in both planes; GPU-to-GPU traffic between servers in the same rail stays in the leaf; across rails uses plane spines; super-spines connect plane sets only for the largest jobs.

## 8. Inference data centres and the front-end

Inference does not usually need rail alignment: a model fits on one GPU or a few GPUs in a server, and traffic is client-server (north-south) plus storage and model-weight loading. The design is a conventional collapsed 3-stage or 5-stage Clos like an enterprise/cloud DC, with load balancers and Kubernetes ingress (chapter 2.20). Multi-node inference (very large models, expert parallelism) is the exception: RDMA traffic returns and rail-based or Clos back-end designs must be considered. Storage fabrics are separate networks (or logically separated) sized for checkpoint bursts and dataset reads. Overall, a server connects to three fabrics: **front-end** (inference/clients, management), **storage**, and **back-end/training** (compute collectives); each has its own topology and SLO.

## 9. Information hiding and failure domains: worked examples

Chapter 2.16 introduced the techniques; here are concrete instances.

- **Summarising topology**: IS-IS levels hide an area's internal topology behind L1/L2 routers; OSPF areas hide intra-area links behind ABRs (type 3 summaries). The price: suboptimal inter-area routing and blindness to detail (a TE controller needs BGP-LS or a hierarchical view).
- **Aggregation**: advertise `10.10.0.0/16` for 256 racks; inside, specifics are used. Failure of one rack's /24 doesn't ripple outward; the cost is blackholing if the aggregate is advertised while a specific is unreachable.
- **Layering**: BGP as a *reachability overlay*: the IGP carries only loopbacks and link reachability, BGP carries the bulk (customer, service or server prefixes). A change in a server prefix never triggers IGP SPF. EVPN is the same idea for MAC/IP. **Segment routing with a controller overlay**: the network's own control plane provides only node/adjacency SIDs; a controller computes and installs paths for policies, so the number of states in the network remains small while policy richness is centralised.
- **Slowing down state velocity**: **exponential backoff** (delay each successive recomputation or advertisement after repeated events: the first change is handled immediately, the next after 50 ms, then 100, 200 ... up to a cap; resets after quiet time) prevents flapping from saturating the control plane. **Link-state flooding reduction**: elect a subset of links for flooding in dense topologies (IS-IS distributed optimised flooding, OSPF flood reduction RFC 8099/mesh groups) so each LSA is not re-received dozens of times; essential in dense Clos link-state fabrics.
- **Design rule**: define a scope for every piece of state (who must know?), define a rate limit for every source of change, and verify these in failure tests.

## 10. Resilience and redundancy

### What failures look like to applications

A link failure can cause (not just "down"): complete flow failure (if filters or policy block the alternate path), a step change in **delay** (more hops, queues and serialisation), a burst of **jitter**, **dropped** packets (in flight at the failure moment), **duplicate** packets (microloops combined with short retransmit timers), and **reordering** (a microloop resolving as a later packet passes an earlier one). These can't be fully eliminated in packet networks; technologies that try often add complexity that hurts more than it helps. Tools: fast reroute, exponential backoff, graceful restart, ECMP, and application tolerance (retries, idempotency, checkpointing).

### Measures

- **MTBF** (mean time between failures) = total time / number of failures; **MTTR** (mean time to repair) = total outage time / number of outages; **Availability** = MTBF / (MTBF + MTTR) = uptime / (uptime + downtime).
- "Nines": 99.9% (three nines) ≈ 8.8 h/year downtime; 99.99% ≈ 52.6 min/year (the source describes about an hour); 99.999% ≈ 5.3 min/year. Define *what* counts as down: whole network, a service, a tenant, a rail, or a percentage of capacity; for AI a degraded fabric (e.g. 7/8 rails) may be "available" for a job but not for the SLO.
- **Informal measures**: **MTBM** (mean time between mistakes: driven by configuration complexity and change processes; the "2 a.m. rule" says don't build what you can't fix at 2 a.m.), **MTTI** (mean time to innocence: how long to prove the network isn't at fault; requires before/after telemetry).

### Redundancy as a tool

Redundancy creates resilience only if there is **no hidden single point of failure**: two paths that share a middle switch, a power feed, a fibre conduit or a control-plane process are not redundant. Rules: eliminate single points (device, link, power, cooling, software/config), then map **shared risk link groups (SRLGs)**: sets of links that fail together (same cable bundle, same line card, same ASIC, same optical amplifier, same data-hall breaker). Overlays and LAGs can hide SRLGs; verify with the physical plan.

Further tools:

- **In-service software upgrade (ISSU)** and **graceful restart** (forwarding continues while the control plane restarts; neighbours keep stale routes for a while) reduce maintenance downtime, but carry risk (stale routes, bugs); data-centre practice often prefers *drain, upgrade, undrain* with ECMP rather than ISSU, using graceful shutdown (chapter 2.16).
- **Dual and multi-planar cores** (A/B fabrics, planes) give independent failure domains and control planes; the cost is double hardware and host connectivity.
- **Modularity and resilience**: modules (pods, blocks) limit blast radius and enable independent upgrades, but the *interfaces* between modules are where failures interact; keep interfaces simple and well-tested. Over-modularising increases the number of interfaces and operational overhead.
- **Application-level resilience**: for training, checkpoint frequency and elastic/fault-tolerant frameworks shape how much network failure costs: a 5-minute fabric incident with checkpoints every 30 minutes can waste up to 30 minutes of cluster time; so network resilience, job resilience and checkpoint cost are one design.

## 11. A design exercise and calculator

**Task**: design a back-end fabric for 4,096 H100 GPUs (512 servers × 8 GPUs, one 400G NIC per GPU), 1:1 at the leaf-spine tier, rail-optimised, with a target of surviving the loss of any single spine with ≤ 5% capacity loss.

Worked arithmetic with 64×400G switches:

1. **Leaves.** Each rail leaf serves 32 servers (32 downlinks, 32 uplinks). 512 servers / 32 = 16 server groups ("rows"), each with 8 rail leaves, so 16 × 8 = **128 leaves**. A single 3-stage fabric with R = 64 supports at most 64 leaves, so a 3-stage design does not fit: use a 5-stage design (or chassis spines).
2. **Blocks.** Split into 4 blocks of 1,024 GPUs. A block has 32 leaves and 32 spines; each leaf has 32 uplinks, one to each of the block's 32 spines.
3. **Spines.** Each spine uses 32 ports down (one per leaf) and 32 up, so 4 blocks × 32 spines = **128 spines** with 128 × 32 = 4,096 uplinks toward the super-spine tier.
4. **Super-spines.** At 1:1 they would need 4,096 / 64 = 64 switches; at 2:1 they receive 2,048 links and need **32 super-spines** (this is the oversubscription decision: acceptable only if most jobs are placed inside one block).
5. **Totals.** 128 + 128 + 32 = **288 switches**; cables: 4,096 server links, 4,096 leaf-spine links, 2,048 spine-super-spine links (server side usually DAC/AEC copper or short AOC; switch-to-switch tiers need optics or AOC).
6. **Failure check.** Losing one spine removes 1 of 32 uplinks per leaf, 1/32 = 3.1% capacity (within the 5% target); add BFD and fast ECMP rerouting so the loss is a few hundred milliseconds. Also tabulate leaf, rail-group, super-spine and power-domain failures and the expansion path (add blocks, super-spines, or move to a multi-plane design).

A small calculator (use in the lab):

```python
def clos3(R, gpus_per_leaf_down=None, oversub=1.0):
    """3-stage Clos: R-port switches; returns (leaves, spines, endpoints)."""
    down = int(R * oversub / (1 + oversub)) if gpus_per_leaf_down is None else gpus_per_leaf_down
    up = R - down
    spines = up                    # one uplink to each spine
    leaves = R                     # each spine port connects one leaf
    return leaves, spines, leaves * down

for R in (32, 64, 128):
    print(R, clos3(R))             # (leaves, spines, endpoints) at 1:1
def survive_spine_loss(spines): return (spines - 1) / spines
```

## 12. Lab: validate topologies (untested)

1. **Paper**: complete the design exercise above; produce a bill of materials (switches, optics, cables) and a failure table (spine, leaf, link, rail group, power domain) with the percentage of bandwidth surviving.
2. **Build a 2-spine × 4-leaf Clos in containerlab** with FRR (reuse the lab in chapter 2.16); run `iperf3` all-to-all with 16 flows and measure per-link utilisation; fail a spine and measure the throughput and recovery time.
3. **Rail emulation**: create 8 rail namespaces per "server" and 8 leaf bridges (or an FRR leaf per rail); show intra-rail one-hop vs inter-rail two-hop with `traceroute` and latency (`netem` delays per hop).
4. **Oversubscription**: configure uplink shaping (`tc tbf`) to 2:1 and run synchronized iperf bursts (incast) to see drops/queueing; add ECN marking with `fq_codel`/`red` and observe the effect.
5. **Shared risk**: model two "redundant" paths that traverse the same intermediate bridge/namespace and show a double failure from one fault; fix and re-test.
6. **Availability math**: compute availability for a component list (series/parallel) using MTBF/MTTR values in a spreadsheet or script; relate to downtime per year.
7. **Torus/dragonfly toy**: create a 4×4 torus of namespaces with static/OSPF routes, measure hops and latency distribution; compare with a 2-spine Clos of the same node count.
8. **Clean up.**

Mark tested only after execution.

## 13. Common mistakes

- Choosing a topology from a diagram without computing ports, switches, optics, power and failure-case capacity.
- Calling a hierarchical network a fabric; scaling up when scale-out was available.
- Oversubscription decided by habit (3:1) for collectives that need 1:1; ignoring oversubscription at the top tier.
- Connecting devices to spines or cross-linking spines without understanding control-plane consequences.
- Forgetting shared risk (power feed, cable tray, line card, optic vendor/firmware bug) behind "redundant" links.
- Rail-optimised cabling errors that put two rails on one leaf or swap rails between servers (check with LLDP, `ibnetdiscover`, NCCL tests).
- Treating inter-rail traffic as unimportant without measuring it (PXN, all-to-all in MoE).
- Ignoring MTU, optics reach and breakout rules; ordering the wrong cable types.
- Designing for the average, not the failure case; no maintenance and drain plan.

## 14. Interview angles

- "Why leaf-spine? How many servers can you attach with R-port switches at 1:1?"
- "What is oversubscription? What would you choose for an AI back-end and why?"
- "Rail-optimised versus rail-unified: pros, cons, failure impact."
- "How do you scale to 32K GPUs? What are the trade-offs of 5-stage, multi-plane, dragonfly?"
- "What is a scheduled fabric / VOQ and why does it help incast?"
- "Define availability; compute downtime for four nines. What hides single points of failure?"
- "What is an SRLG? Give examples in a data centre."
- "What distinguishes a fabric from a hierarchical network?"
- "Where would you place leaves: ToR, MoR or EoR, and why?"

## 15. Checkpoint questions (40)

1. Translate "low job completion time" to network requirements. **A:** Bandwidth per GPU, low tail latency, non-oversubscribed paths, congestion control.
2. Name the layers of a hierarchical design. **A:** Access, distribution, core.
3. What is a ring's weakness? **A:** Latency grows; two failures partition.
4. Hub-and-spoke weakness? **A:** Hub bottleneck/single point of failure; spoke-to-spoke hairpin.
5. Three marks of a fabric? **A:** Regular topology, scale-out, specific performance goals.
6. Scale up vs scale out? **A:** Bigger boxes/links vs more of the same units.
7. What is east-west traffic? **A:** Server-to-server traffic inside the data centre.
8. Define oversubscription. **A:** Edge bandwidth versus fabric bandwidth ratio.
9. Rules for spines in standard leaf-spine? **A:** No spine-to-spine links; no devices attached.
10. In a 3-stage Clos with R-port switches at 1:1, spines? **A:** R/2.
11. Max leaves? **A:** R (one port per leaf on each spine).
12. Max endpoints? **A:** R²/2.
13. 64-port: endpoints? **A:** 2,048.
14. 5-stage max at 1:1? **A:** R³/4.
15. Capacity loss when one of 32 spines fails? **A:** 1/32 ≈ 3.1%.
16. Non-blocking vs non-contending? **A:** No pattern blocked vs no two flows competing for a link.
17. Why can't packet networks be non-blocking? **A:** Many senders may target one destination link.
18. What is a rail? **A:** The set of same-index GPUs across servers sharing a leaf.
19. Intra-rail vs inter-rail hops? **A:** One leaf hop vs leaf-spine-leaf.
20. What is rail-only? **A:** No fabric links between rails; inter-rail routing via NVLink inside servers.
21. Rail-unified downside? **A:** Leaf failure isolates servers; harder rail isolation.
22. Why ToR for rail-unified? **A:** Short cables, low rack space, copper.
23. Why MoR/EoR for rail-optimised? **A:** Each server must reach 8 leaves; leaves grouped centrally.
24. Describe a scheduled fabric. **A:** Cells sprayed across fabric with fabric-wide VOQ, leaves as line cards.
25. What is VOQ? **A:** Per-egress queues at each input to avoid head-of-line blocking.
26. Dragonfly in one sentence. **A:** Meshed groups connected by global links, giving low diameter.
27. Dragonfly routing challenge? **A:** Non-minimal/adaptive routing for balance.
28. Torus diameter formula? **A:** Sum of ⌊n_i/2⌋ per dimension.
29. When is a torus good? **A:** Nearest-neighbour communication.
30. What is multi-planar? **A:** Several independent 2-tier planes with NIC-level spraying across them.
31. Who reorders packets in multi-plane? **A:** The receiving NIC/host software.
32. Inference DC topology? **A:** Conventional collapsed 3-/5-stage Clos.
33. Name three fabrics a GPU server connects to. **A:** Front-end, storage, back-end (training).
34. Explain exponential backoff. **A:** Increasing delays between repeated recomputations/advertisements.
35. What does flooding reduction do? **A:** Limits redundant LSA flooding in dense topologies.
36. MTBF vs MTTR? **A:** Time between failures vs time to repair.
37. Availability formula? **A:** MTBF/(MTBF+MTTR).
38. What is an SRLG? **A:** Links sharing a failure cause.
39. What is MTTI? **A:** Mean time to innocence: proving the network isn't at fault.
40. Why drain-upgrade-undrain instead of ISSU? **A:** Lower risk with ECMP/redundancy, avoids stale-state bugs.

## 16. Sources and review notes

**Written in original words.** Principal sources:

- *AI Data Center Network Design and Technologies*, chapter 3 ("Network Design Considerations"): AI workload stages and fabrics, training data-centre architecture, rail-optimised, rail-only and rail-unified designs and the scale tables, rack layouts (ToR/MoR/EoR), scheduled fabric and VOQ, dragonfly and torus topologies, inference data-centre architecture, multi-planar scale-out.
- Russ White and Jeff Tantsura (with co-authors), *Computer Networking Problems and Solutions*: chapter 19 (failure domains and information hiding), chapter 20 (examples of information hiding: summarising topology in IS-IS and OSPF, aggregation, layering with BGP as a reachability overlay, segment routing with a controller overlay, exponential backoff, link-state flooding reduction), chapter 22 (network design patterns: business problems to technical requirements, hierarchical design, ring/mesh/hub-and-spoke/planar topologies), chapter 23 (resilience: failures as seen by applications, MTBF/MTTR/availability, other measures, redundancy, SRLGs, ISSU and graceful restart, dual and multi-planar cores, modularity), chapter 25 (disaggregation and hyperconvergence, east-west traffic, jitter, packet-switched fabrics, spine and leaf, traffic engineering on spine-and-leaf, non-blocking versus non-contending, disaggregation in networks).
- Sizing formulas, failure-case calculations, the design exercise and the calculator are the author's own derivations from standard Clos arithmetic.

**Flagged for verification before publishing:** all sizing numbers in tables are illustrative (derive your own from the actual switch radix); vendor claims about scheduled fabrics and multi-plane NICs; PXN behaviour per NCCL version; availability-to-downtime conversions (recompute); super-spine oversubscription figures; all labs are **untested**.
