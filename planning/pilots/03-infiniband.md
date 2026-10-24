---
id: infiniband
title: "8.3 InfiniBand for AI Clusters"
sidebar_label: "8.3 InfiniBand"
description: "How InfiniBand works, how to read and operate an IB fabric, and how NCCL uses it: subnet manager, addressing, lossless flow control, routing, diagnostics and failure modes."
---

# 8.3 InfiniBand for AI Clusters

**Level:** intermediate → advanced · **Lab venue:** Nebius multi-node GPU cluster with InfiniBand if available; otherwise a Linux VM with software RDMA (soft-RoCE) to practise the tooling · **Status:** drafted, labs untested

## Why this matters for AI infrastructure

In large GPU training clusters the network that decides your scaling efficiency is the *compute fabric*, and in NVIDIA-based designs that fabric is very often InfiniBand (IB). Every gradient all-reduce, every tensor-parallel exchange across nodes, and a large share of checkpoint and dataset traffic crosses it. A degraded cable, a misconfigured subnet manager or a silent fallback from IB to TCP turns a 1,024-GPU job into an expensive space heater, and the symptom is just "training is slow." InfiniBand also looks and behaves unlike Ethernet: it is a centrally managed fabric with its own addressing, its own flow control and its own diagnostic tools. An infrastructure engineer who can read an IB fabric quickly is rare and valuable.

This chapter assumes the networking basics from Part 2 and the GPU and NIC topology ideas from chapter 7.1. RoCE (RDMA over Ethernet) is covered in 8.2, and NCCL tuning in 8.6; this chapter focuses on the native IB fabric and ties it to both.

## Prerequisites and outcomes

You should understand switched networks, IP addressing and basic Linux networking (chapter 2.5), and what RDMA is in one sentence: moving data directly between the memory of two machines without the CPU or kernel copying it. After this chapter you will be able to:

- explain what InfiniBand is, why it is lossless and centrally managed, and how it differs from Ethernet;
- describe the roles of the subnet manager, LIDs, GIDs, GUIDs, partitions and virtual lanes;
- read link speed names (NDR, XDR) and convert them to usable bandwidth;
- inspect and verify a fabric with `ibstat`, `ibv_devinfo`, `iblinkinfo`, `ibnetdiscover`, `perfquery` and the perftest tools;
- explain how GPUDirect RDMA and NCCL use the fabric, and prove NCCL is actually on IB;
- diagnose seven common failures.

## Concepts

### 1. Basics: what InfiniBand is

InfiniBand is an open network standard developed by the InfiniBand Trade Association. It was designed for clusters from the start, with three defining properties:

1. **Lossless by design.** Links use *credit-based flow control*: a sender may transmit only when the receiver has advertised free buffer space ("credits"). Packets are therefore not dropped for congestion at a hop; instead a congested link makes senders wait. Compare Ethernet, where switches drop packets when queues fill and TCP recovers by retransmitting.
2. **Centrally managed.** A **subnet manager (SM)** discovers the topology, assigns addresses and computes forwarding tables for every switch. Switches are not independent route-computing devices as in an IP network; they follow the tables the SM installs.
3. **RDMA-native.** The adapter (HCA, host channel adapter) executes transport in hardware and moves data between registered memory regions directly. Latency is in the low microseconds and CPU cost is near zero for bulk transfers.

The software stack is **OFED** (OpenFabrics Enterprise Distribution), the open-source set of drivers, libraries (`libibverbs`) and tools. Vendors ship their own builds of it (for NVIDIA adapters this is MLNX_OFED or the newer DOCA-OFED). Package version mismatches between kernel, driver and firmware are a recurring operational problem; treat the OFED version as part of a node's configuration baseline.

### 2. Basics: speed names and what bandwidth you actually get

An IB link is made of parallel *lanes*; the common port is **4x**, four lanes. The generation sets the per-lane signalling rate. The names to know:

| Generation | Per-4x-port data rate (approx.) | Notes |
|---|---|---|
| FDR | 56 Gb/s | older clusters |
| EDR | 100 Gb/s | |
| HDR | 200 Gb/s | very common in A100-era clusters |
| NDR | 400 Gb/s | standard on H100/H200-class systems |
| XDR | 800 Gb/s | next generation, appearing with Blackwell-era systems |

Two practical points. First, the headline figure is bits per second *per direction* on the wire; convert to bytes by dividing by eight, so a 400 Gb/s NDR port is roughly 50 GB/s each way before protocol overhead. Second, line encoding and headers mean usable throughput is somewhat lower than the nominal rate (older generations used 8b/10b encoding, which wastes 20 percent; newer ones use far more efficient encodings, but you should still expect about 90 to 95 percent of nominal in a good bulk-transfer test). Always measure with the perftest tools rather than trusting the label.

A modern 8-GPU server such as a DGX or HGX H100 node typically has **one 400 Gb/s NDR adapter per GPU** (eight compute-fabric HCAs), plus separate NICs for storage and management. That 1:1 GPU-to-NIC ratio and the way each NIC is wired is called a *rail* design and shapes the fabric topology (next sections).

### 3. Intermediate: addressing and the subnet manager

An IB subnet has several identifiers. You will see all of them in tool output.

- **GUID:** a 64-bit globally unique, factory-assigned identifier. Nodes, adapters and ports each have one (node GUID, port GUID). It is like a MAC address.
- **LID (local identifier):** a 16-bit address assigned by the SM to each port in the subnet. Switches forward by LID. Because LIDs are 16-bit and part of the space is reserved, one subnet has a ceiling of roughly 48,000 unicast addresses, a real constraint for the largest clusters and one reason multi-subnet or other designs exist at extreme scale.
- **GID (global identifier):** a 128-bit address formatted like an IPv6 address, used for routing between subnets and as the address in RoCE. Within one IB subnet, forwarding uses LIDs.
- **QPN (queue pair number):** identifies a *queue pair*, the send/receive queue endpoint of an RDMA connection, loosely analogous to a TCP port.
- **P_Key (partition key):** the partition membership identifier. Partitions isolate groups of nodes at the fabric level, similar in purpose to VLANs.
- **SL and VL (service level, virtual lane):** each link carries multiple virtual lanes with separate buffers and credits, so traffic classes do not block each other. The SL in a packet is mapped to a VL at each hop.

The **subnet manager** is a software entity that can run on a switch (a "managed" switch with an embedded SM), on a host (the open-source **OpenSM**), or in NVIDIA's **UFM** (Unified Fabric Manager), the commercial management platform that adds telemetry, health monitoring and a GUI. Its tasks:

1. *Discovery:* sweeps the fabric with subnet management packets to learn switches, ports and links.
2. *Assignment:* gives each port a LID and configures port parameters (MTU, VL mapping).
3. *Routing:* computes forwarding tables using a chosen **routing engine** (for example min-hop, up/down, fat-tree-aware, or adaptive-routing-capable engines) and programs them into the switches.
4. *Monitoring:* re-sweeps periodically and on change, rerouting around failures.

Because the SM is the brain of the fabric, its health is paramount. Run it redundantly (a master and standbys that take over by priority), monitor which node is the master, and treat "the SM is down or flapping" as a Sev-1 condition: existing paths keep working briefly, but new nodes cannot join and failures are not rerouted.

### 4. Intermediate: topologies, rails and routing

AI clusters use **fat-tree (Clos)** topologies: leaf switches connect to hosts, spine switches connect leaves, and capacity is provisioned so that any host can talk to any other at full rate (non-blocking, 1:1) or with a stated oversubscription. For GPU clusters the dominant pattern is **rail-optimised**: GPU *k* of every server connects to the same leaf-switch group (rail *k*). Collective operations between the *k*-th GPUs of many nodes then stay within a single rail and traverse only one switch hop; traffic between rails relies on NVLink inside the server. This is why NCCL builds its communication graph around local GPU and NIC pairing, and why a single mis-cabled NIC can cut a rail and hurt every job.

Routing is where IB differs from IP. Because the SM computes static forwarding tables, naive routing can place many flows on the same link while others sit idle (*hot spots*), especially when traffic patterns are the large, synchronised, few-flow patterns typical of AI. Remedies:

- **Fat-tree-aware routing engines** that spread destinations evenly across uplinks.
- **Adaptive routing (AR):** switches choose among several valid egress ports per packet or per flow based on current congestion, instead of one fixed port. This greatly improves link utilisation for AI traffic; it requires support in switches and adapters and care with in-order delivery requirements.
- **Congestion control** mechanisms that mark and throttle senders that are creating head-of-line blocking.
- **Careful job placement** that keeps tightly-coupled ranks under the same leaf where possible (see Slurm topology-aware scheduling in chapter 6.3).

### 5. Intermediate: in-network computing with SHARP

NVIDIA's **SHARP** (Scalable Hierarchical Aggregation and Reduction Protocol) lets the switches themselves perform parts of a reduction. Instead of every node sending its gradient to many others, nodes send data up the switch tree, the switches sum it on the way, and the result flows back down. For all-reduce this reduces the data crossing the network and the number of steps, improving large-scale collective performance. NCCL can use it through a plugin when the fabric, firmware and Aggregation Manager are set up for it. Treat it as an advanced optimisation to verify and benchmark, not a default.

### 6. Intermediate: how GPUs use the fabric (GPUDirect RDMA and NCCL)

**GPUDirect RDMA** lets the NIC read from and write to GPU memory directly over PCIe, skipping a bounce through host memory. It needs a kernel module that exposes GPU memory to the NIC driver (`nvidia-peermem` or the DMA-BUF path in recent kernels and drivers), and it works best when the GPU and NIC share a PCIe switch or at least a NUMA node (`PIX`/`PXB` in `nvidia-smi topo -m`).

**NCCL**, NVIDIA's collective communication library, discovers the topology and chooses transports: NVLink and shared memory inside a node, and IB verbs (or sockets) between nodes. It builds ring and tree schedules and splits data across *channels*. Two operational facts follow:

1. NCCL **silently falls back** to TCP sockets if it cannot use IB (missing `nvidia-peermem`, wrong HCA selection, a link down, wrong interface). Throughput then collapses by an order of magnitude with no error. Always confirm the transport.
2. Environment variables choose behaviour. The ones to know now: `NCCL_DEBUG=INFO` (log the chosen transports; use temporarily, not permanently), `NCCL_IB_HCA` (which adapters to use, for example `mlx5_0,mlx5_1`), `NCCL_SOCKET_IFNAME` (which interface for bootstrap and the socket transport), `NCCL_IB_DISABLE` (force IB off for debugging), and `NCCL_NET_GDR_LEVEL` (when GPUDirect RDMA is allowed). Leave performance-critical variables at defaults unless you have measured a benefit, and do not leave debugging overrides in production.

### 7. Advanced: operating the fabric

**Verify a host's view.**

```bash
ibstat                      # every port: State, Physical state, Rate, Base lid, SM lid, Link layer
ibv_devinfo -v | head -60   # verbs-level info: port state, active MTU, active speed and width, GIDs
rdma link show              # link status via iproute2's rdma tool
ls /sys/class/infiniband/   # device names: mlx5_0 ... mlx5_N
cat /sys/class/infiniband/mlx5_0/ports/1/rate   # e.g. "400 Gb/sec (4X NDR)"
```

What "good" looks like: `State: Active`, `Physical state: LinkUp`, `Rate` matching the expected generation and width (e.g. 400, 4X NDR), a non-zero `Base lid`, an `SM lid` that is valid and the same across nodes, and `Link layer: InfiniBand`. A port in `Initializing` means the physical link is up but the SM has not configured it, which points at the SM, not the cable. `Polling` or `Down` points at the cable, transceiver or the far end. Rate lower than expected (for example 200 instead of 400, or a width of 1x instead of 4x) means the link negotiated down because of a marginal cable or connector.

**Map the fabric.**

```bash
ibnetdiscover > fabric.topo      # dumps all switches, hosts and links
iblinkinfo                       # per-link speed, width, state across the fabric
ibdiagnet                        # comprehensive fabric health check, reports errors and misconfigurations
saquery                          # ask the SM for node, path and partition records
```

`iblinkinfo` is the quickest way to find the one link running below speed. `ibdiagnet` is the routine health sweep: run it after every cabling change and on a schedule, and archive the reports.

**Read the counters.** Errors on IB are visible in per-port counters.

```bash
perfquery -x <lid> <port>        # extended counters on a given port
perfquery -x -R <lid> <port>     # same, then reset (to measure a window)
```

Counters worth knowing: `SymbolErrorCounter` and `LinkErrorRecoveryCounter` (rising values mean a bad physical link: dirty fibre, damaged or poorly seated cable, failing optic), `LinkDownedCounter` (link flapping), `PortRcvErrors`, `PortXmitDiscards`, and `PortXmitWait`. The last one deserves special mention: it counts ticks during which the port had data to send but could not because it lacked credits, so a rapidly rising `PortXmitWait` is the clearest sign of **congestion** backing up into that port. As with Linux counters, always measure deltas over a known interval.

**Test bandwidth and latency end to end with perftest.**

```bash
# on server node
ib_write_bw -d mlx5_0 --report_gbits -a
# on client node
ib_write_bw -d mlx5_0 --report_gbits -a <server>
ib_write_lat -d mlx5_0 <server>       # latency test
```

Use `ib_write_bw` between pairs of nodes (and across racks) to find the one slow pair; use `-a` for all message sizes. Expect close to line rate for large messages. With GPUDirect, perftest builds with CUDA support accept `--use_cuda=<gpu>` to test the GPU-memory path. For multi-node collectives, `nccl-tests` (`all_reduce_perf`) is the realistic benchmark: compare the reported *bus bandwidth* against what your topology should deliver (chapter 8.6).

**IP over InfiniBand (IPoIB).** IB interfaces can also carry IP traffic (`ib0`), used for management, storage protocols and legacy applications. It runs through the kernel stack, so its throughput is far below native RDMA, and its address contains the port GID and QPN. Do not benchmark IPoIB and conclude anything about RDMA performance.

## Commands that matter

| Question | Command |
|---|---|
| Is the port up and at the right speed? | `ibstat`; `cat /sys/class/infiniband/<dev>/ports/1/rate` |
| Which device maps to which interface and NUMA node? | `ibdev2netdev`; `cat /sys/class/infiniband/<dev>/device/numa_node` |
| What does the fabric look like? | `ibnetdiscover`; `iblinkinfo` |
| Any links running slow or with errors? | `iblinkinfo`; `ibdiagnet`; `perfquery -x` |
| Who is the subnet manager? | `sminfo` |
| Is the point-to-point path at line rate? | `ib_write_bw`, `ib_write_lat` |
| Does NCCL use IB with GPUDirect? | run with `NCCL_DEBUG=INFO`, look for `NET/IB` and `GDRDMA`; `lsmod \| grep nvidia_peermem` |
| Is the collective at the expected bus bandwidth? | `all_reduce_perf -b 8 -e 8G -f 2 -g 1` from nccl-tests |
| Firmware and driver versions | `ibv_devinfo \| grep fw_ver`; `ofed_info -s`; `mst status` (NVIDIA MFT) |

## How it fails

### 1. Port stuck in "Initializing": subnet manager problem
**Symptom:** a new or rebooted node shows `Physical state: LinkUp` but `State: Initialize`; it never gets a LID. **Diagnose:** `sminfo` on any node (does an SM respond? which one is master?), check OpenSM/UFM logs, check that the partition (P_Key) configuration admits this node. **Fix:** restore or fail over the SM, correct partition membership, and re-sweep.

### 2. Link up but slow: negotiated below speed or width
**Symptom:** one node's `ib_write_bw` is half of its neighbours', or NCCL all-reduce is stuck below the expected bus bandwidth. **Diagnose:** `ibstat`/`iblinkinfo` show `Rate` 200 instead of 400, or width 1x/2x instead of 4x; `perfquery` shows symbol errors. **Fix:** clean or replace the fibre or DAC, reseat the optic, replace the transceiver or adapter; then bring the link back and confirm the negotiated rate. Drain the node until fixed.

### 3. Flapping link: intermittent job crashes
**Symptom:** random NCCL timeouts or `transport retry counter exceeded` errors; the same nodes recur. **Diagnose:** `LinkDownedCounter` and `LinkErrorRecoveryCounter` increase; `dmesg` shows port state transitions; the SM log shows repeated re-sweeps. **Fix:** replace the offending cable or optic; consider automatic link-flap detection that quarantines the port; check temperatures and airflow around optics.

### 4. NCCL silently on TCP: wrong or missing IB transport
**Symptom:** multi-node throughput 10x lower than expected while single-node is fine; no errors. **Diagnose:** run with `NCCL_DEBUG=INFO` and look for `NET/Socket` instead of `NET/IB`; check `NCCL_IB_HCA`, whether `nvidia-peermem` is loaded, whether containers can see `/dev/infiniband` devices, and whether `NCCL_SOCKET_IFNAME` selected a slow interface. **Fix:** load the module, expose devices to the container (for Kubernetes, the Network Operator and device plugin, chapter 7.6), select the right HCAs and interfaces, and add a startup check that asserts the transport.

### 5. Hot-spotted fabric: some links saturated, others idle
**Symptom:** inter-node collective bandwidth is below the fabric's capacity even though no link is faulty; counters show very high `PortXmitWait` on particular spine links. **Diagnose:** map which flows use which paths with the SM's routing output and counters over a test window; compare static to adaptive routing. **Fix:** switch to a fat-tree-aware or adaptive routing engine, improve job placement, tune congestion control, and re-test with a large `nccl-tests` run.

### 6. Partition or key mismatch: nodes cannot talk although both look healthy
**Symptom:** two nodes are Active with valid LIDs but connections between them fail. **Diagnose:** compare P_Key tables (`ibv_devinfo -v`, `saquery`) and the SM's partition configuration. **Fix:** align partition membership (and membership type) in the SM configuration, then re-sweep.

### 7. Version drift: driver, firmware and OFED out of step
**Symptom:** after a kernel or OS update, ports vanish, performance regresses, or `modprobe` errors appear. **Diagnose:** `ofed_info -s`, `uname -r`, `ibv_devinfo | grep fw_ver`; compare with a healthy node. **Fix:** pin and test a known-good combination of kernel, driver, firmware and OFED; roll out changes by canary (chapter 11.1).

## Hands-on lab

**Variant A (preferred, untested): a Nebius multi-node GPU cluster with InfiniBand.**

1. On two nodes, run Part A of this lab below, `ibstat`, and record the model, rate, LIDs and the SM LID of every port.
2. Run `ibnetdiscover > topo.txt` and `iblinkinfo`; draw the leaf/spine layout in your notes with Mermaid. Identify which leaf each of the eight NICs of a node connects to (rail check).
3. Run `ib_write_bw` between the two nodes for each rail, using `-d mlx5_<n>`. Expect near line rate per port. Note any outlier.
4. Install and run `nccl-tests`:

```bash
git clone https://github.com/NVIDIA/nccl-tests.git && cd nccl-tests && make MPI=1 CUDA_HOME=/usr/local/cuda
mpirun -np 16 -H nodeA:8,nodeB:8 -x NCCL_DEBUG=INFO ./build/all_reduce_perf -b 8 -e 4G -f 2 -g 1 2>&1 | tee run1.log
grep -E "NET/IB|NET/Socket|GDRDMA|busbw" run1.log | head -40
```

Confirm `NET/IB` is used, note the peak `busbw`, then rerun with `NCCL_IB_DISABLE=1` and record the collapse in bus bandwidth. Explain it using the concepts of this chapter.

5. Take one NIC offline for the test (admin only, test cluster): `sudo ip link set <netdev> down` or disable its port with `mlxlink`, rerun the all-reduce, and observe how a degraded rail changes results.

**Variant B (works on any Linux VM; untested): soft-RoCE to practise the verbs tooling.** This is not InfiniBand, but it exercises the same `libibverbs` stack and perftest workflow.

```bash
sudo apt-get install -y rdma-core ibverbs-utils perftest iproute2
sudo modprobe rdma_rxe
sudo rdma link add rxe0 type rxe netdev eth0
rdma link show
ibv_devinfo
# terminal 1:
ib_write_bw -d rxe0
# terminal 2:
ib_write_bw -d rxe0 127.0.0.1
```

Compare what `ibv_devinfo` reports (link layer Ethernet instead of InfiniBand, GIDs in use) with an IB port, and write down what is missing (no SM, no LIDs).

### Part A: baseline capture (do this on every cluster you operate)

```bash
ibstat > ibstat.$(hostname).txt
ibv_devinfo -v > ibv.$(hostname).txt
ofed_info -s; uname -r
```

Store these per node. Diffing them across nodes is the fastest way to find the odd one out.

## Checkpoint questions

1. What makes InfiniBand "lossless", and how does that differ from Ethernet's approach to congestion?
2. What are the roles of the subnet manager, and what breaks if it fails?
3. Differentiate GUID, LID, GID and QPN.
4. Convert a 400 Gb/s NDR port to approximate GB/s per direction, and explain why measured throughput is lower than nominal.
5. What is a rail-optimised topology and why does it suit AI collectives?
6. Why can a statically-routed fat tree be unevenly loaded, and what are two remedies?
7. What does SHARP do for an all-reduce?
8. How do you prove NCCL is using InfiniBand with GPUDirect RDMA, and what silent failure are you guarding against?
9. A port shows `State: Initialize` and `Physical state: LinkUp`. What does that tell you, and where do you look?
10. Which counter indicates congestion backing up into a port, and which indicate a bad physical link?

### Answers

1. Credit-based link-level flow control: a sender transmits only if the receiver advertised buffer credits, so packets are not dropped for congestion at a hop; congestion appears as senders waiting. Ethernet switches drop packets when queues overflow and rely on end-host retransmission (or on PFC pause frames when run lossless).
2. It discovers the topology, assigns LIDs and port settings, computes and installs forwarding tables, and re-sweeps on change. If it fails, existing paths run briefly but new nodes cannot join and failures are not rerouted.
3. GUID is a 64-bit permanent identifier of a node or port; LID is a 16-bit subnet-local address assigned by the SM and used for forwarding; GID is a 128-bit IPv6-style address used for inter-subnet routing and in RoCE; QPN identifies a queue pair endpoint, like a port number.
4. 400 Gb/s divided by 8 is about 50 GB/s per direction; encoding and header overhead and software limits mean a good test reaches roughly 90 to 95 percent of that.
5. GPU k of each server connects to the same group of leaf switches, so same-index GPUs communicate within one rail across one switch hop, while cross-rail traffic uses NVLink inside the server. Collectives such as all-reduce are structured to exploit exactly this.
6. The SM installs fixed forwarding tables, so synchronised, low-entropy AI flows can pile onto the same links. Remedies: fat-tree-aware or adaptive routing, congestion control, better job placement.
7. The switches sum partial data in the network, so less data crosses the fabric and fewer steps are needed.
8. Run with `NCCL_DEBUG=INFO` and look for `NET/IB` (and `GDRDMA`), confirm `nvidia-peermem` is loaded, and benchmark with `nccl-tests`. The silent failure is NCCL falling back to TCP sockets.
9. The physical link is up, but the SM has not configured the port. Look at the subnet manager (`sminfo`, SM logs) and partition configuration.
10. `PortXmitWait` (credit starvation, so congestion); `SymbolErrorCounter`, `LinkErrorRecoveryCounter` and `LinkDownedCounter` indicate a bad or flapping physical link.

## Sources and further reading

- Sergey Zhumatiy, *Supercomputers for Linux SysAdmins*, ch. 5 (InfiniBand overview, link speeds and encodings, OFED, `ibstat` output and port states, IPoIB addressing).
- Chris Fregly, *AI Systems Performance Engineering*, ch. 4 (NCCL transports, multi-NIC pitfalls and environment variables, in-network reduction, NIXL).
- *AI Data Center Network Design and Technologies*, ch. 8 and 9 (InfiniBand versus RoCE, shared BTH and RDMA semantics, typical IB topologies, limits of LID addressing and isolation), and ch. 7 for the RoCE counterpart.
- Fuheng Wu, *Distributed AI Systems*, ch. 2 (reading topology and affinity in multi-GPU nodes).
- NVIDIA public documentation: InfiniBand and OFED/DOCA manuals, UFM, SHARP, NCCL environment variable reference, nccl-tests.

*Flags for verification:* the 16-bit LID ceiling (about 48,000 unicast LIDs) and the exact adaptive-routing and SHARP feature sets depend on switch generation and firmware; confirm against your hardware's documentation. Efficiency figures (90 to 95 percent of nominal) are practitioner expectations, not guarantees. All lab commands are **untested** and need running on a real cluster (Variant A) or VM (Variant B) before this chapter is marked reviewed.
