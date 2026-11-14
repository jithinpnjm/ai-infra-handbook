---
id: "c12-02"
title: "12.2 RDMA fundamentals: verbs, queue pairs and memory registration"
sidebar_label: "12.2 RDMA fundamentals: verbs, queue pairs and memory registration"
sidebar_position: 2
description: "RDMA fundamentals from first principles: kernel bypass vs TCP/IP, Verbs object hierarchy, Protection Domains, Memory Regions, lkey/rkey and MTT page pinning, Queue Pair state machine, Send/Receive vs one-sided RDMA Write/Read, and BTH/RETH/AETH packet decoding."
status: "drafted"
tier: "1"
level: "I"
lab_venue: "Nebius GPU"
---

# 12.2 RDMA fundamentals: verbs, queue pairs and memory registration

| | |
|---|---|
| Level | Intermediate |
| Priority tier | 1 |
| Lab venue | Nebius GPU |
| Part | Part 12: Complete AI networking |
| Coverage file | `planning/coverage/chapters/12-02.md` |
| Claim ledger | `planning/ledgers/12-02.md` |

## Why this matters for AI infrastructure

Here is a situation many multi-node GPU engineers meet. Every physical link on the fabric is Active at 400 Gbps, basic IP reachability succeeds across every node, and the switches show zero drop counters. Yet the distributed training job still crashes at startup with a generic network timeout, and you have nothing in the switch logs to explain it. The cables are fine, the switches are fine, and the job still fails. That gap between a healthy-looking network and a failing job is what this chapter is about.

This failure repeats on multi-node GPU clusters for one reason. Engineers treat Remote Direct Memory Access, or RDMA, as a faster version of TCP sockets. In traditional socket programming, an application writes bytes to a file descriptor. A file descriptor is the number the operating system gives your program for an open channel, such as a socket. The Linux kernel copies those bytes into kernel-space socket buffers, runs the TCP/IP state machine, and hands packets to the network interface card driver. That model hides the hardware behind the operating system, so you never see the adapter doing the work. The socket model is simple to use, and that simplicity is exactly why it does not carry over cleanly to RDMA.

At 100 Gbps to 400 Gbps line rates across hundreds of GPUs, that model breaks down. Per-packet system calls, context switches, buffer copies and software checksums saturate the host CPUs. A system call is a request from your program to the kernel, and each one costs time. Synchronous collective operations force every GPU rank to wait at a barrier for the slowest rank. One delayed transfer therefore stalls the entire training cluster, and you will see every GPU idle while it waits. Engineers call this effect straggler amplification, because a single slow participant gets multiplied across the whole job.

RDMA removes that software bottleneck. It moves transport execution into the Host Channel Adapter, or HCA, hardware through kernel bypass and zero-copy Direct Memory Access, or DMA. The HCA is the InfiniBand name for the network adapter, and DMA means the adapter reads and writes memory without the CPU copying each byte. The speed comes with a cost. Bypassing the kernel means the application and communication library must manage explicit hardware resources directly. Nothing is hidden anymore, so you have to understand the queues, the memory keys, and the states that the kernel used to manage for you.

The first failure lives in the endpoint queues. In the opening incident, the application created Queue Pairs on healthy ports. It did not move them through the required state machine with matching peer addresses and maximum transmission unit values. The maximum transmission unit, or MTU, is the largest packet the link will carry, and both ends have to agree on it. It also left Receive Queues unreplenished under burst traffic, and it discarded the detailed Completion Queue Entry error statuses. The software logged a generic network timeout, while the hardware had explicitly reported a receiver-not-ready fault and a local protection error. The detail was there the whole time. The application threw it away.

The second failure strikes before any traffic flows, so you may never see a packet go out. An RDMA adapter does DMA using physical memory addresses, which it translates through its on-NIC Memory Translation Table. The adapter cannot handle operating system page faults or swapped pages. A page fault is what happens when a program touches memory that is not yet in physical RAM, and the kernel has to fetch it first. The adapter has no way to wait for that, so the memory it uses has to be held in place in advance. Many containers keep the Linux locked-memory limit at its 64 KiB default, not unlimited. When the job tries to register gigabytes of host or GPU memory, registration fails before a single packet leaves the server.

The third failure appears only at scale. Each active Queue Pair consumes scarce on-NIC static RAM cache for its context and work queues. Uncontrolled Queue Pair growth across thousands of GPUs makes the NIC cache thrash over PCIe. Thrashing means the cache keeps throwing out entries it needs again a moment later, so every lookup becomes a slow trip across the bus. Communication libraries avoid this with shared transports, hierarchical rings and trees, or Dynamic Connected transport.

```text
Production Failure Signatures vs Hardware Reality (V8 Ch 3, V7 Ch 4, SCL Ch 24):
  - TCP/IP CPU Bottleneck:   100-node Ray cluster on 100GbE ConnectX-5 pins CPUs at 100% kernel system time, capping throughput at 30 Gbps
  - Endpoint Lifecycle Bug:  Active 400 Gbps ports fail INIT -> RTR when active_mtu mismatches (4096 vs 2048) or drop with IBV_WC_RNR_RETRY_EXC_ERR and IBV_WC_LOC_PROT_ERR
  - Container memlock Gate:  Default ulimit -l (memlock) of 64 KiB (65,536 bytes) blocks ibv_reg_mr() with ENOMEM unless set to unlimited
  - O(N^2) QP Scaling Wall:  128 nodes x 8 GPUs (1,024 ranks) in full-mesh RC requires 1,023 QPs/rank, 8,184 QPs/node, and 1,047,552 QPs cluster-wide
```

The block is a short list of the three failures above, each with the number that shows it. Read the signature first, then match it to the failure you are seeing in your own logs. Each line points at a different layer of the stack, so a match tells you where to look next.

This chapter builds the complete RDMA execution model from first principles. It starts with kernel bypass versus TCP/IP, then walks through the Verbs object hierarchy and the Memory Translation Table math. From there it covers Work Requests and Scatter-Gather Entries, two-sided versus one-sided operations, and the transport service types. It ends with the six-state Queue Pair state machine, the wire-level packet headers, and endpoint troubleshooting.

:::tip In one minute
- **Why RDMA exists:** Standard TCP/IP sends every message through system calls, CPU context switches, user-to-kernel buffer copies and software TCP processing. RDMA uses kernel bypass and zero-copy DMA, so the Host Channel Adapter reads and writes registered memory directly. Small-message latency drops from tens of microseconds to low single-digit microseconds.
- **Core Verbs objects:**
  - **Device Context:** Opens the adapter and queries hardware limits such as maximum Queue Pairs, Work Requests, and active MTU.
  - **Protection Domain:** Acts as a security boundary grouping Queue Pairs and Memory Regions. A Queue Pair in Protection Domain A cannot access a Memory Region in Protection Domain B.
  - **Memory Region:** Pins virtual pages in physical RAM, programs the HCA Memory Translation Table, and returns a 32-bit local key and remote key. Backing a 1 GiB buffer with 2 MiB hugepages instead of 4 KiB pages shrinks MTT footprint by 512x.
  - **Queue Pair and Completion Queue:** Each Queue Pair holds a Send Queue and a Receive Queue. Applications post Work Requests with Scatter-Gather Entries, and the HCA writes Completion Queue Entries to the Completion Queue.
- **Two-sided vs one-sided operations:**
  - **Two-sided Send and Receive:** Requires the remote peer to pre-post a matching Receive Work Request. Starving the Receive Queue triggers a receiver-not-ready completion error.
  - **One-sided RDMA Write, Read, and Atomics:** Targets a remote virtual address and remote key encoded in the 16-byte RDMA Extended Transport Header, completely bypassing the remote CPU and Receive Queue.
- **Queue Pair state machine:** Every Queue Pair steps through RESET, INIT, RTR, and RTS before sending data. When a Queue Pair hits a transport failure, it transitions to ERR and flushes all subsequent queued work with a flush error status. Always debug the first non-flush completion entry.
:::

When your job fails with a generic timeout, read the completion errors first. The first non-flush entry usually names the real cause. Everything else in the logs is usually a consequence of that first error, so the rest of this chapter teaches you to find it.

## Prerequisites and outcomes

*Suppose your first RDMA job fails at startup, and you need to know which earlier material to review before you start digging.*

**Prerequisites:** Review Linux networking and lossless QoS basics in Chapter 2.19, plus PCIe, NUMA, and pinned memory in Chapters 10.6 and 10.12. NUMA stands for Non-Uniform Memory Access, which means a CPU reaches memory on its own socket faster than memory on another socket. You should also know the NVIDIA Network Operator from Chapter 11.11 and AI collective traffic patterns from Chapter 12.1.

The chapter walks through five connected ideas, and each one builds on the one before it. It starts with the difference between the kernel path and the RDMA data path. Then it covers the core Verbs objects and the capability limits your software should read before it deploys anything. Next comes memory registration, which is where most startup failures come from. After that it moves into the work requests, the connection setup, and the Queue Pair states. The last part decodes the packets on the wire and shows how to trace a failure to its first cause.

Start with the first idea, and keep it in view as you read. The rest of the chapter builds on the difference between the two data paths.

---

## 1. Why TCP/IP Stalls AI Collectives and How RDMA Bypasses the Kernel

When a distributed training job synchronizes gradients across nodes, network latency and throughput decide how long you wait. That wait is called Job Completion Time, the total elapsed time from job start to job completion. Synchronous collective operations wait for every parallel worker to finish before the job moves to the next layer or step. A single slow transfer therefore stalls the entire cluster.

```text
Tail Latency Impact on Job Completion Time (ADC Ch 1, Figs 1-4 to 1-6):
  - Serial Execution (n = 10 tasks):   9 tasks take 1 ms each + taskX takes 1 s (1,000 ms) -> Total JCT = 1 s + (10 x 1 ms) = 1.010 seconds
  - Parallel Execution (100 threads):  99 threads finish in 1 ms (< 100 ms), 1 straggler takes 1 s -> 99 threads wait 999 ms at barrier, pinning JCT at 1 second
```

Consider the block above, which works the same tail-latency problem twice. In the serial run, one slow task adds almost a full second. In the parallel run, you find 99 fast threads still sitting at the barrier until the straggler finishes. The lesson carries into the rest of the chapter. The network stack you choose changes how much of each step is spent moving data, and a slow stack makes every barrier longer.

### 1.1 The 7-step TCP/IP kernel penalty vs RDMA kernel bypass

Standard TCP/IP adds high latency, jitter, and CPU saturation on 100 Gbps to 800 Gbps AI fabrics. The reason is simple, and you can see it in the steps. The host CPU and the operating system kernel mediate every packet. Picture one tensor sent over a standard Linux TCP socket. Seven steps occur across the sender and the receiver. A tensor here is one block of numbers, such as a gradient, that has to reach another GPU.

The sender does most of the work. First, the application prepares payload bytes in user-space virtual memory. Second, it invokes a send system call into the Linux kernel. Third, the CPU halts user-space execution and switches privilege rings into kernel mode. A privilege ring is the CPU's split between user code and kernel code, and crossing it costs time. Fourth, the CPU copies payload bytes from the user-space buffer into kernel-space socket and transport buffers. Fifth, the CPU runs the TCP/IP stack to build headers, compute software checksums, manage congestion windows, and fragment packets. Sixth, the kernel signals the NIC driver over PCIe.

The receiver pays too. Seventh, incoming packets on the destination server trigger hardware interrupts, kernel TCP reassembly, and another CPU copy into the receiving application buffer. Each of these steps uses CPU time, and that time is what the training job cannot spare.

On a 10 Gbps web server, host CPUs absorb this overhead easily. On a 100 Gbps to 400 Gbps GPU cluster, millions of TCP packets arrive every second. Processing them pins host CPU cores at 100 percent kernel utilization, and it caps a 100 Gbps ConnectX-5 link around 30 Gbps. The link is capable of more, but the CPU runs out of time first. Adding a faster link does not help when the bottleneck is the CPU doing the copies.

RDMA solves this bottleneck by combining two hardware mechanisms. First, Direct Memory Access lets the adapter hardware engine read and write physical host RAM or GPU BAR1 VRAM directly across the PCIe bus. BAR1 is the window through which the host can reach GPU memory, and VRAM is the GPU's own memory. No CPU copy loops are required. Second, kernel bypass and transport offload remove the operating system from the hot transfer path. Transport offload means the adapter does the packet work that the CPU used to do.

Under RDMA, the Linux kernel runs only during the control path. The control path is the setup phase. The kernel opens the device context, allocates a Protection Domain, pins and registers Memory Regions, and transitions Queue Pairs into the connected state. Once setup is complete, the data path bypasses the operating system kernel on both endpoints. Setup happens once and costs time, and the data path runs for the rest of the job.

The application writes a descriptor directly to a memory-mapped hardware doorbell register in user space. A doorbell is a register the application writes to say that new work is waiting. The local HCA reads the buffer via DMA, encapsulates packets in silicon, and transmits them across the fabric. The remote HCA then writes the payload straight into the destination registered physical memory without waking the remote kernel. Nothing on the receiving host has to run a copy loop, Here is what that looks like from start to finish for one message. The application writes its tensor into a registered buffer, which was set up at startup, and then it posts a Work Request that names the buffer's address and key. The user-space driver writes a descriptor into the Queue Pair ring and rings the doorbell. The HCA picks up the descriptor, reads the bytes from memory by DMA, cuts them into packets, and stamps each packet with a sequence number. Every packet carries the Queue Pair number and the opcode, so the far end knows where it belongs. When the far HCA has placed the bytes, it sends back an acknowledgement, and the near HCA posts a completion. At no point in that trip did either CPU copy the payload. The only CPU work was writing the descriptor and reading the completion.

```mermaid
flowchart LR
    subgraph TCP["1. Standard TCP/IP Path (CPU & Kernel Bound)"]
        TA["App Buffer (User)"] -->|"1. syscall + copy"| TK["Kernel Socket & TCP"]
        TK -->|"2. Driver DMA"| TN["Standard NIC"]
        TN -->|"3. Wire"| RN["Remote NIC"]
        RN -->|"4. IRQ + copy"| RK["Remote Kernel TCP"]
        RK -->|"5. Copy to user"| RA["Remote App Buffer"]
    end
    subgraph RDMA["2. RDMA Path (Kernel Bypass & Zero-Copy DMA)"]
        MA["Registered Memory"] <-->|"Direct PCIe DMA"| HA["HCA / ConnectX NIC"]
        HA <-->|"Lossless IB / RoCEv2"| HB["Remote HCA / NIC"]
        HB <-->|"Direct PCIe DMA"| MB["Remote Registered MR"]
        KC["Kernel Control Plane"] -. "Setup Only (MR / QP)" .-> HA
        KC -. "Setup Only (MR / QP)" .-> HB
    end
```

The two diagrams in one picture show the same trip twice. The top path touches the kernel at every hop, and the bottom path touches it only at setup. Read the dotted lines in the bottom path as the control plane, which is used once, and the solid lines as the data plane, which carries the traffic.

The table compares the two stacks one layer at a time. Read across a row, and you see where each cost moves when RDMA takes over.

| Architectural Layer | Standard TCP/IP Socket Stack | RDMA Verbs Stack (`InfiniBand` / `RoCEv2`) | Operational Impact on AI Workloads |
|---|---|---|---|
| **Control Path Setup** | `socket()`, `bind()`, `connect()` in kernel | `ibv_open_device()`, `ibv_alloc_pd()`, `ibv_reg_mr()`, `ibv_create_qp()`, `ibv_modify_qp()` via `/dev/infiniband/uverbsN` | Kernel validates permissions, pins pages, and configures HCA contexts once at startup |
| **Per-Message Submission** | `send()` / `recv()` system call per message | User-space `ibv_post_send()` / `ibv_post_recv()` ring MMIO doorbell directly | **Zero system calls** and **zero context switches** on the hot data path |
| **Memory Copy Path** | User buffer -> Kernel Socket Buffer -> Kernel Transport Buffer -> NIC (and reverse on RX) | Direct hardware DMA between registered application buffer (or GPU VRAM) and HCA | **Zero CPU bounce-buffer copies**; frees host CPUs for data loading and kernel launches |
| **Transport & Reliability** | Executed in software by host CPU threads (`TCP` sliding window, timers, ACKs) | Executed in silicon on the HCA (`PSN` tracking, hardware `ACK`/`NAK`, hardware retry) | Small-message latency drops from tens of microseconds to **low single-digit microseconds** (`~0.78–1.08 us` MPI PingPong) |
| **Fabric Requirement** | Tolerates lossy Ethernet via software TCP selective retransmission | Expects lossless or near-lossless fabric (InfiniBand link-layer credits or RoCEv2 with `PFC` + `ECN`/`DCQCN`) | Packet drops trigger hardware Go-Back-N or retry stalls unless fabric congestion control is active |

The main point of the table is the last two rows. RDMA moves reliability into silicon, but it asks the fabric to stay lossless. That trade is the heart of the whole chapter. You gain speed and free CPU time, and in return the network has to be built so that packets are almost never lost.

### 1.2 The five node-local RDMA layers and three RDMA transport protocols

When a collective operation hangs or drops throughput, you need to know which layer owns each stage of an RDMA transfer. Inside each server node, RDMA traffic passes through five distinct layers, from the application down to the physical cable. Think of them as floors in a building. A request starts on the top floor, and each floor hands it to the one below until the wire carries it out of the building.

First, the application or collective library, such as NCCL, MPI, or UCX, generates work requests for tensor buffers. Second, the Verbs API in `libibverbs` exposes standard C functions to manage resources, post work, and poll completions. Third, the provider and kernel drivers, `mlx5_ib`, `ib_uverbs`, and `ib_core`, translate user-space verbs into hardware Work Queue Elements and manage address translation tables. A Work Queue Element is the hardware form of a request, and an address translation table maps virtual memory to physical memory. Fourth, the Host Channel Adapter hardware executes DMA, packet segmentation, sequence numbering, invariant CRC generation, and hardware acknowledgements. Fifth, the physical wire transmits frames across copper or optical links.

Across the wire, three RDMA transport protocols exist. InfiniBand is governed by the InfiniBand Trade Association. It uses a native credit-based lossless link layer, an optional network layer for inter-subnet routing, and the InfiniBand transport layer. A link layer is the part of the stack that moves frames between two directly connected devices, and the network layer routes between subnets.

RDMA over Converged Ethernet defines two versions. RoCEv1 runs directly over Ethernet Layer 2 with EtherType `0x8915`, and it is confined to a single broadcast domain. A broadcast domain is the set of machines that hear each other's local broadcasts, and RoCEv1 cannot cross beyond it. RoCEv2 replaces the InfiniBand network layer with standard IPv4 or IPv6 and UDP destination port 4791. That is the reason RoCEv2 can be routed across the leaf-spine networks used in data centers.

Immediately after the UDP header come the 12-byte InfiniBand Base Transport Header, payload, 4-byte Invariant CRC, and 4-byte Ethernet Frame Check Sequence. The UDP source port is hashed from the Queue Pair Number to give ECMP routing entropy across spine switches. Entropy here means variety, so the switches have something to spread across different paths. Finally, iWARP runs RDMA over hardware-offloaded TCP/IP. That design avoids lossless Ethernet requirements, at the cost of higher latency and hardware complexity.

The block below lists link generations, encapsulation sizes, and addressing limits. Use it as a lookup when a number on the wire does not match what you expect.

```text
InfiniBand Link Generations, Coding, and Addressing Specs (SCL Ch 5 Table 5-1, ADC Ch 1):
  - SDR (8b/10b):    2.5 Gbps per lane  |   8 Gbps effective (4x) |    24 Gbps (12x)
  - DDR (8b/10b):    5.0 Gbps per lane  |  16 Gbps effective (4x) |    48 Gbps (12x)
  - QDR (8b/10b):   10.0 Gbps per lane  |  32 Gbps effective (4x) |    96 Gbps (12x)
  - FDR (64b/66b):  14.0625 Gbps/lane   |  54.4 Gbps (4x)         |   163.2 Gbps (12x)
  - EDR (64b/66b):  25.0 Gbps per lane  | 100 Gbps effective (4x)
  - HDR (64b/66b):  53.125 Gbps/lane    | 200 Gbps effective (4x) |   600 Gbps (12x)
  - NDR (256b/257b): 106.25 Gbps/lane   | 400 Gbps effective (4x) | 1,200 Gbps (12x)
  - XDR:            200 Gbps per lane   | 800 Gbps effective (4x) | 2,400 Gbps (12x)
  - GDR:            400 Gbps per lane   | 1,600 Gbps (4x)         | 4,800 Gbps (12x)
  - IB Encapsulation: LRH (8 B) + optional GRH (40 B) + BTH (12 B) + Payload + ICRC (4 B) + VCRC (2 B)
  - IB Subnet Scale:  Up to 2^15 + 2^14 - 1 = 49,151 ports/switches (16-bit LIDs: unicast 1..0xBFFF, multicast 0xC000..0xFFFE, permissive 0xFFFF)
  - RoCEv1 vs RoCEv2: RoCEv1 uses L2 EtherType 0x8915; RoCEv2 uses IPv4/IPv6 + UDP dst port 4791 + BTH (12 B) + Payload + ICRC (4 B) + FCS (4 B)
  - iWARP Stack:      RDMA over hardware-offloaded TCP/IP (MPA / DDP / RDMAP)
```

The 4x and 12x entries are lane counts, so each row shows the same per-lane rate multiplied across more lanes. When you compare two links, check the lane count first. A 4x link and a 12x link can run the same per-lane rate and still differ by a factor of three in total throughput. Many confusing benchmark results come from comparing a link that was trained at a narrower width than the one the team expected. A lane is one physical pair of wires inside the cable, and a link bundles several lanes together. When a collective stalls, first decide which of the five layers owns the stalled stage. Then check the numbers in this block against what the adapter reports, because a mismatch often points to a mismatch in the layer below.

---

## 2. The Verbs Object Hierarchy and Capability Inspection

If your application asks for more Queue Pairs, Work Requests, or Scatter-Gather Entries than the network adapter supports, allocation fails right at job startup. Before you post a single RDMA operation, your software must build a strict hierarchy of hardware-backed resource objects through the Verbs interface. It must also verify the hardware limits. Picture the hierarchy as a set of nested permits. You cannot get a Queue Pair until you have the right Protection Domain, and you cannot use a Memory Region until it is bound to that same domain.

The diagram shows which objects depend on which. Each arrow points from an object to the object it needs.

```mermaid
flowchart TD
    Ctx["1. Device Context (ibv_context)<br/>ibv_open_device(mlx5_0)"] --> PD["2. Protection Domain (ibv_pd)<br/>ibv_alloc_pd() Security Boundary"]
    Ctx --> CQ["3. Completion Queue (ibv_cq)<br/>ibv_create_cq() Shared by 1..N QPs"]
    PD --> MR["4. Memory Region (ibv_mr)<br/>ibv_reg_mr() -> Pins Pages, MTT, lkey/rkey"]
    PD --> QP["5. Queue Pair (ibv_qp)<br/>ibv_create_qp() -> Send Queue + Receive Queue"]
    CQ -. "Associated for TX/RX CQEs" .-> QP
    MR -. "Authorized via lkey / rkey" .-> QP
    QP -->|"ibv_post_send / ibv_post_recv"| HCA["6. ConnectX HCA Hardware<br/>Executes WQEs & Emits CQEs"]
```

The table works as a lookup for each object. Each row names the call that creates the object, what the hardware or kernel does with it, and the limits you can read back. Start at the top row, because every other object depends on the device context you open there.

| Verbs Object (`libibverbs`) | Creation API | Hardware / Kernel Function | Key Attributes & Limits (`mlx5_0` Example) |
|---|---|---|---|
| **Device Context (`ibv_context`)** | `ibv_open_device()` | Opens `/dev/infiniband/uverbsN` and maps user-space doorbell pages | Queried via `ibv_query_device()` / `ibv_devinfo -v` (`fw_ver: 28.39.2048`, `vendor_id: 0x02c9`, `vendor_part_id: 4129`) |
| **Protection Domain (`ibv_pd`)** | `ibv_alloc_pd()` | Hardware isolation container binding compatible `QPs` and `MRs` | Prevents a `QP` in `PD A` from performing DMA against an `MR` in `PD B` |
| **Memory Region (`ibv_mr`)** | `ibv_reg_mr()` | Pins virtual pages in physical RAM, populates NIC `MTT`, issues DMA keys | Returns `lkey` (`32`-bit local key) and `rkey` (`32`-bit remote key); `max_mr: 16777216`, `max_mr_size: 0xffffffffffffffff` |
| **Completion Queue (`ibv_cq`)** | `ibv_create_cq()` | Ring buffer where the HCA writes `64`-byte Completion Queue Entries (`CQEs`) | Polled via `ibv_poll_cq()` or armed via `ibv_req_notify_cq()`; `max_cq: 16777216`, `max_cqe: 4194303` |
| **Queue Pair (`ibv_qp`)** | `ibv_create_qp()` | Transport endpoint containing a **Send Queue (`SQ`)** and **Receive Queue (`RQ`)** | Identified by `24`-bit `qp_num` (`QPN`); `max_qp: 262144`, `max_qp_wr: 32768`, `max_sge: 30` |

### 2.1 Answering the seven capability questions before writing code

Production software should query adapter capabilities rather than hard-code assumptions. A hard-coded limit works on the machine you tested on and fails on the next one. Consider the output of `ibv_devinfo -v -d mlx5_0` from an NVIDIA ConnectX-7 HCA. The vendor part ID is 4129, which is the `MT4129` part, and the vendor ID is `0x02c9`. The vendor ID identifies the chip maker, and the part ID identifies the exact chip model.

```text
$ ibv_devinfo -v -d mlx5_0
hca_id: mlx5_0
    transport:                  InfiniBand (0)
    fw_ver:                     28.39.2048
    node_guid:                  08c0:eb03:00f1:a2c3
    sys_image_guid:             08c0:eb03:00f1:a2c3
    vendor_id:                  0x02c9
    vendor_part_id:             4129
    max_mr_size:                0xffffffffffffffff
    max_qp:                     262144
    max_qp_wr:                  32768
    max_sge:                    30
    max_cq:                     16777216
    max_cqe:                    4194303
    max_mr:                     16777216
    atomic_cap:                 ATOMIC_HCA (1)
        port:   1
            state:              PORT_ACTIVE (4)
            max_mtu:            4096 (5)
            active_mtu:         4096 (5)
            phys_state:         LINK_UP (5)
            link_layer:         InfiniBand
```

Every field in this output constrains application and collective-library design. First, `max_qp` caps how many total Queue Pairs can exist on the adapter, at 262,144. Second, `max_qp_wr` bounds the depth of any single Send Queue or Receive Queue, at 32,768. An application that requests 100,000 outstanding work requests on one Queue Pair will fail queue creation right away. The depth is the number of slots in the queue, so asking for more than the adapter supports is an immediate error.

Third, `max_sge` bounds how many discontiguous local memory segments one Work Request can gather or scatter, at 30. Passing 32 Scatter-Gather Entries triggers a local work-request submission failure. Fourth, `max_cq` and `max_cqe` determine how many Queue Pairs can share one Completion Queue without overflowing its ring buffer. A ring buffer that overflows loses completions, and the application then waits forever for an event that was dropped.

Fifth, `max_mr` and `max_mr_size` bound the number and size of registered memory buffers on the adapter. Sixth, `atomic_cap` confirms whether hardware 64-bit Compare-and-Swap and Fetch-and-Add operations are supported on the HCA. Compare-and-Swap and Fetch-and-Add are the two atomic operations that let a remote machine update a number safely. Seventh, `state`, `phys_state`, and `active_mtu` verify link readiness and negotiated payload size.

Suppose one endpoint has an active MTU of 4096 and its peer has 2048. Requesting a 4096-byte path MTU during connection setup causes `ibv_modify_qp` to fail the INIT to RTR transition with `EINVAL`. That failure occurs even though both ports report `PORT_ACTIVE`. EINVAL is the standard error for an invalid argument, and here the invalid argument is the MTU that the peer cannot accept. Read these seven fields before you write connection code, and size your queues to what the adapter reports. The MTU example shows why. Both ports look healthy in the status output, so the failure has nothing to do with whether the link is up. It has to do with a value that the two ends never agreed on. Reading the fields side by side on both hosts is the fastest way to find that kind of mismatch. A quick way to make this a habit is to write the seven values into a short report at the start of each job, next to the job's queue depth and scatter-gather count. If a later run fails, you can compare the report with the new adapter output and see at once whether the hardware changed, the firmware changed, or your configuration drifted.

---

## 3. Protection Domains, Memory Registration, Keys, and MTT Math

Suppose you assume that an RDMA NIC can read or write any standard pointer your allocator returns. That assumption is a common misconception among software engineers. Ordinary memory is fine for the CPU, because the CPU can fault pages in on demand. The NIC cannot do that. If you pass an unregistered pointer to an RDMA work request, the hardware immediately halts the Queue Pair with a local protection error.

### 3.1 What memory registration actually does in the kernel and on the NIC

When a CPU dereferences a virtual address, the CPU Memory Management Unit walks the process page tables in hardware. The Memory Management Unit is the part of the CPU that translates the addresses your program uses into real physical addresses. If the page is not resident in physical RAM, the CPU raises a page fault. The Linux kernel then allocates a physical frame, updates the page table, and resumes the instruction. The CPU can pause, wait, and try again, and that flexibility is what makes ordinary memory easy to use.

An RDMA HCA performing line-rate DMA across PCIe cannot stall the wire to wait for Linux kernel page faults. A packet that is arriving does not wait for anyone. It also cannot risk writing incoming network packets to a physical RAM frame that the operating system silently reassigned to another process. Calling `ibv_reg_mr` therefore executes four mandatory steps in the kernel and on the adapter. Registration is the moment you give the adapter a fixed, pre-checked map of memory it is allowed to touch.

First, the kernel either pins the virtual pages backing the buffer in physical RAM, or maps GPU BAR1 physical pages through `nvidia-peermem` or `dma-buf`. Pinning means the operating system can never swap or relocate those pages while the Memory Region exists. The dma-buf mechanism is a standard Linux way to share a buffer between devices, and nvidia-peermem is the NVIDIA module that makes GPU memory visible to the NIC.

Second, Linux enforces the locked-memory quota against the user process. Pinned pages cannot be paged out, so Linux charges them against `RLIMIT_MEMLOCK`, which you read and set with `ulimit -l`. On an unconfigured Linux host or container, that limit defaults to 64 KiB. Registering a 128 KiB buffer under a 64 KiB limit makes `ibv_reg_mr` fail with `ENOMEM`. ENOMEM means the system ran out of memory it was allowed to lock. On every HPC and AI compute node, `/etc/security/limits.conf` and container security contexts must set both soft and hard `memlock` limits to `unlimited`:

```text
# /etc/security/limits.conf (SCL Ch 24, V8 Ch 3)
# Default unconfigured Linux ulimit -l is 64 KiB (65,536 bytes); registering 128 KiB (131,072 bytes) fails with IBV_REG_MR_ENOMEM_MEMLOCK
* soft memlock unlimited
* hard memlock unlimited
```

The comment explains the failure, and the two lines below it set the fix. A soft limit is the default a process starts with, and a hard limit is the ceiling it may raise itself to. Setting both keeps the container from being capped by either one.

Third, the driver programs the HCA Memory Translation Table. It writes the virtual-to-physical page mappings into the adapter. The NIC hardware uses those entries to translate virtual addresses in incoming headers or local descriptors into PCIe physical DMA addresses. The adapter now holds its own copy of the map, so it never has to ask the kernel where a page is.

Fourth, the HCA issues hardware protection keys. It binds the Memory Region to the specified Protection Domain and stores the authorized access flags. Those flags include `IBV_ACCESS_LOCAL_WRITE`, `IBV_ACCESS_REMOTE_WRITE`, `IBV_ACCESS_REMOTE_READ`, and `IBV_ACCESS_REMOTE_ATOMIC`. The call then returns two 32-bit capability tokens. A key is a token that proves you are allowed to use the memory, and the flags say what you may do with it.

Think of the two keys as a visitor badge and a room key. The local key is the badge you wear on your own premises, and the HCA checks it on every local access. The remote key is a room key that you hand to a guest. A guest with the right key can enter the room and work inside it, but only within the access the key allows. The key does not expire on its own, so it has to be revoked by deregistering the memory. That is why deregistering too early causes errors on the peer. The local key, `lkey`, must be supplied in every local Scatter-Gather Entry, so the local HCA can verify Protection Domain membership and buffer bounds. The remote key, `rkey`, is exchanged out-of-band with a remote peer. Out-of-band means it travels over a side channel, such as the control connection, and not inside the RDMA data itself. The peer includes that remote key, together with the virtual address and DMA length, in one-sided RDMA packets. A remote peer that does not hold the right key gets refused, which is the point of the key.

### 3.2 MTT page-table scaling math and NIC cache thrashing

Even when memory registration succeeds, registering tens of gigabytes of standard 4 KiB pages can silently degrade multi-node training bandwidth. Each page pinned in a Memory Region needs an 8-byte physical address entry in the HCA Memory Translation Table. The table grows with the number of pages, so the page size you choose decides how big it gets.

```text
Memory Translation Table (MTT) Scaling Math (code/part12/rdma_fundamentals.py):
  Number of Pinned Pages = ceil(Buffer_Bytes / Page_Size_Bytes)
  MTT_Table_Bytes        = Number of Pinned Pages * 8 bytes (64-bit entry)

  Case 1: 64 KiB (65,536 B = 0x00010000) DMA buffer on 4 KiB (4,096 B) pages:
    65,536 / 4,096 = 16 pinned pages -> 16 x 8 B = 128 bytes of MTT entries

  Case 2: 1 GiB (1,073,741,824 B) tensor buffer on 4 KiB (4,096 B) pages:
    1,073,741,824 / 4,096 = 262,144 pinned pages -> 262,144 x 8 B = 2,097,152 bytes (2 MiB of MTT entries per GiB)

  Case 3: 1 GiB (1,073,741,824 B) tensor buffer on 2 MiB (2,097,152 B) hugepages:
    1,073,741,824 / 2,097,152 = 512 pinned hugepages -> 512 x 8 B = 4,096 bytes (4 KiB of MTT entries per GiB -> 512x reduction)
```

Work through the three cases in the block. Case 1 is the small one, and it shows the formula working on a buffer that fits in a few pages. Case 2 needs 262,144 pinned pages for one GiB of 4 KiB pages. Each page costs 8 bytes, so the table holds 2,097,152 bytes, or 2 MiB. Case 3 covers the same GiB with 2 MiB hugepages. That needs only 512 pinned hugepages, and the table shrinks to 4,096 bytes. That is the 512x reduction.

The 512x reduction matters for tail latency. ConnectX HCAs cache hot MTT entries and Queue Pair contexts in a small, fast on-NIC SRAM cache called Interconnect Context Memory. SRAM is fast memory that is small and expensive, so the NIC can only keep so much of the table on chip. When a node registers tens of gigabytes of fragmented 4 KiB pages, the MTT working set overflows that on-chip SRAM cache. Every cache miss then forces the HCA to fetch MTT page translations across the host PCIe bus before it can DMA the actual tensor payload. Backing large host buffers with 2 MiB or 1 GiB hugepages, and reusing a pre-registered buffer pool, removes both the registration latency and the NIC MTT cache misses. Pre-register your large buffers once, and reuse them. A useful habit is to size the buffer pool before the job starts and to write the sizes down. If the pool is too small, the application falls back to registering on the hot path, and that is exactly the slow path the pool was meant to avoid. If the pool is large, it uses up the locked memory budget that the container was given. Both problems show up in the same place, which is the memlock limit, so check that limit whenever registration gets slower than you expect.

### 3.3 Protection Domain and Memory Region failure semantics

When an application violates Protection Domain isolation, key permissions, or registered address bounds, the hardware halts the transfer immediately. The table below summarizes where each violation is caught and which completion status is reported. Each failure leaves a different trace, so the status is the first clue to read.

| Violation Type | Where Detected | Completion Queue Status (`ibv_wc_status`) | Root Cause |
|---|---|---|---|
| **Local `PD` Mismatch** | Local HCA before wire transmission | **`IBV_WC_LOC_PROT_ERR`** | QP belongs to `Protection Domain A`, but SGE references an `lkey` registered in `Protection Domain B` |
| **Local Out-of-Bounds / Invalid `lkey`** | Local HCA before wire transmission | **`IBV_WC_LOC_PROT_ERR`** or **`IBV_WC_LOC_LEN_ERR`** | Local SGE `addr + length` exceeds the registered MR bounds, or `MR` was prematurely deregistered (`ibv_dereg_mr`) while a WQE was still in flight |
| **Remote Invalid `rkey` / Missing Flag / Out-of-Bounds** | Remote HCA upon inspecting incoming `RETH` header; returns `NAK` (`AETH`) to initiator | **`IBV_WC_REM_ACCESS_ERR`** on initiator `CQ` | Initiator supplied a stale/wrong `rkey`, accessed `offset + length > buffer_bytes` (e.g., `32,768 + 65,536 > 65,536`), or targeted an MR registered without `IBV_ACCESS_REMOTE_WRITE` / `IBV_ACCESS_REMOTE_READ` |

The first two rows fail on the local side, before anything reaches the wire. The last row fails on the remote side, and the error appears on the initiator's Completion Queue. Read the status code first, because it tells you which side to debug. The status is written by the adapter at the moment it detected the problem, so it is more precise than any later message from your application. Many applications rewrite the status into a generic error string before logging it, and that rewrite throws away the one detail that points at the right side. Keep the raw status name in your logs. A local status means your own buffer or key is wrong. A remote status means the peer refused something you sent, and the fix may live on the other host. A quick test separates the two sides. If a single host can register and post a local loopback transfer, but the cross-host transfer fails with a remote status, the problem is in the remote key, the access flags, or the bounds on the peer. If even the local transfer fails, start with your own protection domain and key.

---

## 4. Work Requests, SGEs, Operation Types, and Transport Services

You can post RDMA operations without understanding completion signaling or Receive Queue replenishment. If you do, you risk one of two failures: a silent Send Queue overflow or a receiver-not-ready crash. You must match work request flags, verb semantics, and transport service types to the communication pattern of your workload. Get the pattern wrong and the job still runs for a while, which is why these failures often show up hours into a run.

### 4.1 Work Requests, Work Queue Elements, and Scatter-Gather Entries

Your application submits work by building a Send or Receive Work Request structure, `struct ibv_send_wr` or `struct ibv_recv_wr`. It then passes that structure to `ibv_post_send` or `ibv_post_recv`. The user-space provider driver turns the software Work Request into a hardware Work Queue Element descriptor inside the Queue Pair ring buffer, and it rings the HCA doorbell. Think of the Work Request as a form you fill in, the Work Queue Element as the same form written in the adapter's own language, and the doorbell as the bell that tells the adapter a new form is waiting.

Each Work Request has four essential fields. First, `wr_id` is an application-defined 64-bit tag, such as `1042` or a context pointer. The HCA echoes that tag verbatim in the resulting Completion Queue Entry. For example, a request tagged `1042` returns `1042` in its completion. The tag is how you match a finished completion back to the request that caused it.

Second, `opcode` selects the verb operation, such as `IBV_WR_SEND`, `IBV_WR_RDMA_WRITE`, `IBV_WR_RDMA_WRITE_WITH_IMM`, `IBV_WR_RDMA_READ`, `IBV_WR_ATOMIC_CMP_AND_SWP`, or `IBV_WR_ATOMIC_FETCH_AND_ADD`. Third, `sg_list` and `num_sge` specify an array of Scatter-Gather Entries, `struct ibv_sge`. Each entry holds a buffer address, a byte length, and a local key. A single Work Request can gather a protocol header, a tensor chunk, and trailing metadata from separate buffers into one wire transfer. That avoids copying discontiguous segments into a staging buffer first. Gathering is the trick that lets the adapter read three scattered pieces as one message.

Fourth, `send_flags` control completion generation and inline payload handling. Setting `IBV_SEND_SIGNALED` tells the HCA to generate a Completion Queue Entry when the request completes. To reduce Completion Queue pressure and PCIe DMA overhead, high-performance libraries post unsignaled requests for most sends. They mark only every 16th, 32nd, or 64th request as signaled. An unsignaled request still moves data, but it produces no completion of its own, so the cost of checking is paid once in a while.

Reliable Connected queues complete work in strict FIFO order. FIFO means first in, first out. Consuming the completion for request 64 therefore proves that requests 1 through 63 have also completed, and their Send Queue slots can be reused. Never post more than `max_qp_wr` unsignaled requests without a signaled request. Doing so overflows the Send Queue silently, because no completion ever arrives to free descriptors. The queue fills up, and the application keeps posting into a full ring with no error to tell it so.

For tiny payloads up to 64 or 256 bytes, setting `IBV_SEND_INLINE` copies the payload directly into the WQE descriptor when you ring the doorbell. Batching works in a similar spirit. Instead of ringing the doorbell once per request, a library can post a group of requests and ring the doorbell once for the whole group. Each ring costs a trip across PCIe, so fewer rings means less overhead per message. The trade-off is latency. A request sitting in a batch that has not been rung yet is waiting for the next ring, so batching suits throughput work and not the most latency-sensitive messages. That saves a separate PCIe DMA read. For a very small message, the fixed cost of the separate read is bigger than the message itself, so copying the bytes inline is faster.

### 4.2 Two-sided Send and Receive vs one-sided RDMA Write, Read, and Atomics

RDMA verbs split into two families: two-sided channel operations and one-sided memory operations. Whether the remote CPU and Receive Queue take part in a transfer matters for debugging hangs and data corruption. Suppose a burst arrives while the remote Receive Queue is empty. The remote HCA then returns an RNR NAK, as the table's risk column describes. RNR stands for receiver not ready, and a NAK is a negative acknowledgement that tells the sender to back off and try again. The table compares the four operations.

| Operation Type | Remote Receive WQE Required? | Remote CPU Involved in Data Path? | Wire Headers (`IB` / `RoCEv2`) | Primary AI / HPC Use Case & Operational Risk |
|---|---|---|---|---|
| **1. `Send` / `Receive` (Two-Sided Channel Semantics)** | **Yes** (Remote peer must pre-post `ibv_post_recv` before packet arrives) | Only to post RX buffer and poll RX `CQE` | `BTH` (`12` B) + Payload + `ICRC` (`4` B) | Control messages, RPC headers, and metadata exchange. **Risk:** If the receiver's `RQ` runs empty under a burst, the remote HCA returns an **RNR NAK**, eventually failing the sender with **`IBV_WC_RNR_RETRY_EXC_ERR`**. |
| **2. `RDMA Write` (One-Sided Memory Push)** | **No** (Unless using `WRITE_WITH_IMM`, which consumes 1 RX WQE for `32`-bit immediate notification) | **Zero** (Completely silent to remote CPU unless notified separately) | First packet: `BTH` (`12` B) + **`RETH` (`16` B)** + Payload + `ICRC` (`4` B); Middle/Last: `BTH` + Payload + `ICRC` | Bulk gradient/activation streaming (`NCCL` Ring/Tree channels, `ib_write_bw`). **Nuance:** An initiator's local `RDMA_WRITE` `CQE` proves the remote HCA acknowledged placement into remote RAM/VRAM—it does *not* prove the remote application noticed the data without a separate flag, immediate value, or follow-up `Send`. |
| **3. `RDMA Read` (One-Sided Memory Pull)** | **No** | **Zero** | Request: `BTH` (`12` B) + **`RETH` (`16` B)** + `ICRC` (`4` B) (`32` B total); Response: `BTH` + (`AETH` on First/Last/Only) + Payload + `ICRC` | Storage target pulls (`NVMe-oF`, `NFS-RDMA`) and KV-cache / parameter pulls. |
| **4. `Atomics` (`CAS` / `FAA`)** | **No** | **Zero** | Request: `BTH` (`12` B) + `AtomicETH` (`28` B) + `ICRC` (`4` B); Response: `BTH` + `AtomicAckETH` + `ICRC` | Distributed locks, queue-tail pointers, and barrier counters (`64`-bit aligned; requires `atomic_cap: ATOMIC_HCA`). |

The Nuance note in the RDMA Write row matters most here. A local completion does not mean the remote application has noticed the data. The remote adapter has placed the bytes, but the remote program may still be unaware that they arrived. Two-sided Send avoids that gap, because the receiver had to post a buffer and gets a completion of its own. One-sided Write is faster and quieter, and that quiet is exactly what makes it easy to misread.

Think of the difference as a delivery. A two-sided Send is a courier who needs someone at the door to sign for the parcel. A one-sided Write is a drop-off into a locker, which is fast, but the owner only knows it arrived if the courier also sends a text. The immediate value, a follow-up Send, or a polled flag is that text message.

### 4.3 Tracing the 13-step RDMA Write and 11-step RDMA Read CM sessions

Before one-sided RDMA Write or RDMA Read packets can cross the fabric, the endpoints must set up a Queue Pair connection and exchange target memory coordinates. The coordinates are the remote address and the remote key, and the peer needs both before it can touch the memory. An RDMA Connection Manager session does this in three phases: connection handshake, data transfer, and connection teardown.

In an RDMA Write session, the client and server exchange 13 messages across the three phases. First, the three-step Connection Manager handshake connects the Queue Pairs. Next, the data exchange takes six steps. The client sends transfer size and address metadata, then memory region metadata, before pushing the one-sided RDMA Write payload. Teardown takes the last four steps. The six data steps are mostly paperwork. Only one of them moves the payload itself.

In an RDMA Read session, the session completes in 11 steps. The client combines the transfer size, remote address, and memory region information into a single RDMA Read Request message. The server then answers directly with the requested data payload. Because the client asks for the data in one message, the data exchange is shorter than the Write version.

```text
RDMA Connection Manager (CM) Session Sequences (trace_rdma_cm_session_steps in code/part12/rdma_fundamentals.py, ADC Ch 1 Figs 1-12 & 1-13):

1. 13-Step RDMA Write Session (3 Handshake + 6 RDMA Write + 4 Terminate):
   Phase 1 — CM Handshake (3 steps):
     Step 1 (Client -> Server): CM: Connect request with client QPN
     Step 2 (Server -> Client): CM: Connect reply with server QPN
     Step 3 (Client -> Server): CM: Ready to use (Connection established)
   Phase 2 — RDMA Write Exchange (6 steps):
     Step 4 (Client -> Server): Transfer size and remote address information
     Step 5 (Server -> Client): Acknowledgement
     Step 6 (Client -> Server): Memory region information
     Step 7 (Server -> Client): Acknowledgement
     Step 8 (Client -> Server): Data (One-sided RDMA Write payload pushed directly to server memory)
     Step 9 (Server -> Client): Acknowledgement
   Phase 3 — CM Teardown (4 steps):
     Step 10 (Client -> Server): CM: Disconnect request with server QPN
     Step 11 (Server -> Client): CM: Disconnect reply
     Step 12 (Client -> Server): CM: Disconnect request with client QPN
     Step 13 (Server -> Client): CM: Disconnect reply

2. 11-Step RDMA Read Session (Client 20.0.0.2 and Server 60.0.0.2: 3 Handshake + 4 RDMA Read + 4 Terminate):
   Phase 1 — CM Handshake (3 steps):
     Step 1 (20.0.0.2 -> 60.0.0.2): CM: Connect request with client QPN
     Step 2 (60.0.0.2 -> 20.0.0.2): CM: Connect reply with server QPN
     Step 3 (20.0.0.2 -> 60.0.0.2): CM: Ready to use (Connection established)
   Phase 2 — RDMA Read Exchange (4 steps):
     Step 4 (Client -> Server): Transfer size, remote address, and memory region information (RDMA READ Request, BTH opcode 12 + RETH)
     Step 5 (Server -> Client): Acknowledgement
     Step 6 (Server -> Client): Data (RDMA READ Response, BTH opcode 13/14/15/16 carrying server memory payload back to client)
     Step 7 (Client -> Server): Acknowledgement
   Phase 3 — CM Teardown (4 steps):
     Step 8  (Client -> Server): CM: Disconnect request with server QPN
     Step 9  (Server -> Client): CM: Disconnect reply
     Step 10 (Server -> Client): CM: Disconnect request with client QPN
     Step 11 (Client -> Server): CM: Disconnect reply
```

Match each numbered step against your packet capture to find the phase where the session stops. Start from the bottom of the capture, not the top. The last message that arrived tells you how far the session got, and the step after it is the one that never happened. If a Write session reaches the acknowledgement at step 9 and then the teardown never starts, the data reached the server but the connection was not closed cleanly. That is a much smaller problem than a session that stalls at step 4, where the server never saw the transfer request at all. Reading from the end keeps you from debugging a step that already succeeded. If a capture stops after step 3, the handshake never finished. If it stops in the middle of the data phase, the failure is in the transfer itself. The phase tells you where to look, and the step number tells you which message was the last one sent.

### 4.4 Transport Service Types and Queue Pair Scaling Math

When you create a Queue Pair, you select a transport service type. That type governs reliability, ordering, supported verbs, and cluster-wide scaling. Full-mesh Reliable Connected Queue Pairs for an all-to-all workload on a large GPU cluster cause quadratic Queue Pair growth and NIC SRAM cache thrashing. Full mesh means every rank holds a dedicated Queue Pair to every other rank, so the count grows with the square of the cluster size.

| Transport Code | Full Name | Connection Model | Reliable (ACK / Retry)? | Ordered? | Supported Verbs | QPs per Rank for `N` Peers |
|---|---|---|---|---|---|---|
| **`RC`** | **Reliable Connected** | `1:1` dedicated logical peer QP per local QP | **Yes** (`PSN` + `AETH` `ACK`/`NAK`) | **Yes** | `Send`/`Recv`, `RDMA Write`, `RDMA Read`, `Atomics` | **`N - 1`** (`O(N^2)` cluster-wide) |
| **`UC`** | **Unreliable Connected** | `1:1` dedicated peer QP (no `ACK` or retransmission) | **No** (corrupted/lost packets dropped silently) | **Yes** | `Send`/`Recv`, `RDMA Write` *(No Read or Atomics)* | **`N - 1`** (`O(N^2)` cluster-wide) |
| **`UD`** | **Unreliable Datagram** | `1:M` connectionless; addressed per WQE via an **Address Handle (`AH`)** | **No** | **No** | `Send`/`Recv` only (`<= 1 MTU` payload + `40`-byte `GRH`) | **`1`** (single QP reaches any peer; supports multicast) |
| **`DC`** | **Dynamic Connected** *(Mellanox/NVIDIA extension)* | `1:M` reliable connected; a **DC Initiator (`DCI`)** dynamically connects to any remote **DC Target (`DCT`)** per packet burst | **Yes** | **Yes** | `Send`/`Recv`, `RDMA Write`, `RDMA Read`, `Atomics` | **`O(1)`** small pool of `DCI` QPs per process |

Read the table with one question in mind. Ask what each transport gives up to gain its scaling. RC is the most reliable, and it asks for a dedicated Queue Pair per peer. UD uses a single Queue Pair, but it gives up reliability and ordering. DC keeps reliability and still uses a small pool, but it depends on a vendor extension. The right choice depends on whether your workload needs reliability more than it needs a small Queue Pair count.

The worked example below applies that O(N^2) growth to a 128-node cluster. O(N^2) is the shorthand for growth with the square of the cluster size, so doubling the nodes roughly quadruples the Queue Pairs.

```text
Worked O(N^2) RC Queue Pair Scaling Calculation (evaluate_qp_scaling_and_perftest in code/part12/rdma_fundamentals.py):
  Cluster Configuration:     128 GPU nodes x 8 GPUs per node = 1,024 total GPU ranks (N = 1,024)
  RC QPs per GPU rank:       N - 1 = 1,024 - 1               = 1,023 RC QPs per rank
  RC QPs per 8-GPU node:     8 x 1,023                       = 8,184 RC QPs per node (vs mlx5_0 max_qp: 262144)
  Total cluster-wide RC QPs: 1,024 x 1,023                   = 1,047,552 RC QPs across the cluster
```

A node with 8,184 Queue Pairs stays below the hard `max_qp` ceiling of 262,144 on a single adapter. Scaling to thousands of nodes, with several Queue Pairs per peer, pushes each node past hardware limits. Long before it reaches that hard ceiling, a large active Queue Pair count exhausts the HCA Interconnect Context Memory SRAM cache. That exhaustion degrades throughput through PCIe context-fetch thrashing. The point is that the cache fills up well before the advertised limit does, so you can run into trouble with a count that looks safe on paper.

Production communication libraries avoid full-mesh explosion by using Ring and Tree topologies, where each rank connects only to a few neighbors. They also use Shared Receive Queues or Dynamic Connected transport for all-to-all Mixture-of-Experts communication. A Shared Receive Queue lets many Queue Pairs draw receive buffers from one pool. Choose the transport type with the Queue Pair count in mind, because that count grows quickly. A practical way to apply this is to count the peers each rank really talks to, not the peers that exist. A ring algorithm talks to its left and right neighbors, so each rank needs only a few Queue Pairs even when the cluster is large. An all-to-all Mixture-of-Experts layer talks to many more peers in a single step, which is why it is the workload that pushes teams toward Shared Receive Queues or Dynamic Connected transport. Write down the peer count for each communication pattern in your job before you pick a transport, and the choice becomes much easier.

---

## 5. Queue Pair State Machine, Completion Queues, and Wire-Level Packet Headers

A newly created Queue Pair cannot send or receive packets right away. If you skip a required state transition, or supply mismatched MTU or GID attributes during connection setup, the kernel verbs provider fails with `EINVAL`. That happens even when the physical links are up. The error is usually a mismatch in a setting that the two ends were supposed to agree on, not a broken cable.

### 5.1 The 6-state Queue Pair lifecycle

Every Queue Pair starts in the RESET state after `ibv_create_qp`. You then step it through a strict hardware state machine with `ibv_modify_qp` calls. A state machine means each state has a fixed set of allowed next states, and you cannot jump over them. In the INIT state, the application binds the local port and Partition Key, and it can pre-post initial Receive Work Requests, although wire packets are not yet accepted. The Partition Key is a tag that groups the endpoints allowed to talk to each other.

Moving to Ready to Receive binds the remote destination Queue Pair number, remote address handle, starting receive Packet Sequence Number, and path MTU. The remote address handle is the path description to the peer. Moving to Ready to Send configures the starting send Packet Sequence Number, ACK timeout, and retry counters, so full bidirectional transfers can begin. Each transition is a checkpoint where both ends learn a little more about the connection.

The diagram traces the same six states and the attributes that move a Queue Pair between them.

```mermaid
flowchart LR
    R["1. RESET<br/>Newly created QP"] -->|"local port, pkey_index"| I["2. INIT<br/>Post initial RX WRs"]
    I -->|"path_mtu, dest_qp_num, rq_psn"| RTR["3. RTR (Ready to Receive)<br/>Remote path bound"]
    RTR -->|"sq_psn, retry_cnt, rnr_retry"| RTS["4. RTS (Ready to Send)<br/>Full TX/RX active"]
    RTS -->|"Drain outbound SQ"| SQD["5. SQD (SQ Drained)<br/>Controlled pause"]
    SQD -->|"Resume"| RTS
    RTS -->|"Retry/Prot failure"| ERR["6. ERR (Error State)<br/>Flushes queued WRs"]
    ERR -->|"Reset to recover"| R
```

The table lists each state, the states it can move to, the attributes you must supply, and the failure you will see.

| QP State | Valid Next States | Mandatory `ibv_modify_qp()` Attributes | Operational Behavior & Failure Signature |
|---|---|---|---|
| **1. `RESET`** | `INIT` | None at creation | Queues are empty; posting `send` or `recv` WRs is rejected immediately. Skipping straight from `RESET -> RTS` fails with `EINVAL`. |
| **2. `INIT`** | `RTR`, `ERR`, `RESET` | `port_num >= 1`, `pkey_index >= 0` (`0xFFFF` default `P_Key`), `qp_access_flags` | **Receive WRs (`ibv_post_recv`) can now be pre-posted**, though packets are not yet accepted from the wire. |
| **3. `RTR` (Ready to Receive)** | `RTS`, `ERR`, `RESET` | `path_mtu` (`256`, `512`, `1024`, `2048`, or `4096`), `dest_qp_num` (`> 0`), `rq_psn` (`24`-bit starting RX PSN), `ah_attr` (peer `dlid` or `dgid` + `sgid_index`, `sl`) | Binds the QP to its remote peer and path. **Fails with `Failed to modify QP to RTR` (`EINVAL`)** if `requested_path_mtu` (`4096`) exceeds `local_active_mtu` (`2048`) or if RoCEv2 GID index (`-x 2`) fails handshake (`QPN 0x0000`). |
| **4. `RTS` (Ready to Send)** | `SQD`, `ERR`, `RESET` | `sq_psn` (`24`-bit starting TX PSN), `timeout` (`5`-bit local ACK timer), `retry_cnt` (`0..7`), `rnr_retry` (`0..7`), `max_rd_atomic` | Full bidirectional Send/Receive and one-sided RDMA Write/Read/Atomic execution active. |
| **5. `SQD` (Send Queue Drained)** | `RTS`, `ERR`, `RESET` | Drain notification | Halts new outbound sends while in-flight WQEs complete cleanly so path attributes can be modified safely. |
| **6. `ERR` (Error State)** | `RESET` | Triggered automatically by HCA on fatal WQE / retry failure | Immediately halts wire transmission and drains all remaining queued WQEs into the `CQ` with status **`IBV_WC_WR_FLUSH_ERR`**. Must transition `ERR -> RESET` (or destroy/recreate QP) before reuse. |

Notice that ERR is never a state you choose on purpose. The HCA enters it on a fatal failure, and the Queue Pair must return to RESET before you reuse it. Think of ERR as a tripped breaker. You do not turn it off on purpose, you find out why it tripped, reset it, and only then  In practice, the flow looks like this. A fatal retry failure moves the Queue Pair into ERR. Every queued request behind the failing one is flushed. The application logs the first non-flush error, returns the Queue Pair to RESET, and rebuilds the connection through the normal INIT, RTR, and RTS path. If the peer is still broken, the new connection fails in the same way, and the log shows the same first error again. That repetition is a useful signal, because it tells you the fault is still on the far side and not in the restart itself.

### 5.2 Completion Queue semantics, busy polling vs events, and flush cascades

When an RDMA transfer fails in production, operators are often flooded with hundreds of `IBV_WC_WR_FLUSH_ERR` log lines. They then mistakenly assume the entire fabric collapsed. Knowing how the HCA generates Completion Queue Entries and flushes errored queues prevents hours of misdirected debugging. The flood is a side effect of one failure, and the lines are not separate failures.

When the HCA finishes processing a signaled Work Queue Element, it writes a 64-byte Completion Queue Entry into the Completion Queue through DMA. It also writes a completion entry whenever a local or remote transport error occurs, even on an unsignaled element. Applications consume those entries in one of two ways. Either way, the application has to read the entries, or the ring fills up and the events are lost.

With busy polling via `ibv_poll_cq`, a dedicated thread spins in user space and checks the Completion Queue ring buffer in host RAM. Busy polling delivers sub-microsecond wake-up latency and deterministic 99th-percentile tail latency. For that reason, NCCL proxy threads and `perftest` benchmarks busy-poll by default, which pins 100 percent of that CPU core. The cost is paid in CPU time, and the gain is that the wake-up is almost immediate.

Event-driven completion works differently. With `ibv_req_notify_cq` and `ibv_get_cq_event`, the application arms the Completion Queue doorbell and sleeps on a file descriptor until the HCA fires an MSI-X interrupt. MSI-X is the interrupt mechanism that lets a device signal a specific CPU. Event mode saves CPU cycles during idle periods, but it costs 5 to 15 microseconds of kernel interrupt and thread wake-up latency. Production storage and RPC engines often use hybrid polling, which spins briefly before arming interrupts. Hybrid polling catches the common quick reply without paying the full wake-up cost.

Suppose a transfer fails in the middle of a job, and your log fills with flush errors. Consider the following captured sequence of five completions from `ibv_poll_cq`:

```text
wr_id=1042  status=IBV_WC_SUCCESS          opcode=RDMA_WRITE
wr_id=1043  status=IBV_WC_RETRY_EXC_ERR    opcode=RDMA_WRITE   vendor_err=0x81
wr_id=1044  status=IBV_WC_WR_FLUSH_ERR     opcode=RDMA_WRITE
wr_id=1045  status=IBV_WC_WR_FLUSH_ERR     opcode=SEND
wr_id=1046  status=IBV_WC_WR_FLUSH_ERR     opcode=SEND
```

Why do requests 1044, 1045, and 1046 all report `IBV_WC_WR_FLUSH_ERR`? Because request 1043 is the root cause. The local HCA transmitted `RDMA_WRITE` request 1043, then used all 7 hardware retransmission attempts without receiving a valid ACK from the peer. It reported `IBV_WC_RETRY_EXC_ERR` with vendor error `0x81` and NCCL error 12. As soon as request 1043 failed, the HCA moved the Queue Pair into the ERR state and flushed every later queued work request with `IBV_WC_WR_FLUSH_ERR`. Skip the flushed requests when you debug. Start with the first non-success, non-flush completion entry. The first row that failed is the one that tells you the story, and the rest are just the queue draining.

The same rule applies to teardown. Never call `ibv_dereg_mr`, or free a buffer, while a Queue Pair can still perform DMA against it. Deregistering while DMA is still running is like pulling a rug out from under a moving car. The mandatory lifecycle order is listed below:

```text
Mandatory 9-Step RDMA Resource Lifecycle and Safe Teardown Order (V8 Ch 3):
  1. Open & Query Device (ibv_open_device, ibv_query_device)
  2. Allocate PD & CQ    (ibv_alloc_pd, ibv_create_cq)
  3. Register Memory     (ibv_reg_mr -> pins pages, programs MTT, issues lkey/rkey)
  4. Create QP           (ibv_create_qp in RESET state)
  5. Transition QP       (ibv_modify_qp: RESET -> INIT -> RTR -> RTS)
  6. Post Work & Poll    (ibv_post_send / ibv_post_recv, drain CQEs via ibv_poll_cq)
  7. Quiesce New Work    (stop posting new WRs)
  8. Drain or Flush Work (transition QP to ERR/RESET and consume all remaining CQEs)
  9. Destroy Resources   (ibv_destroy_qp FIRST, then ibv_dereg_mr, then ibv_destroy_cq, then ibv_dealloc_pd)
```

Follow that order when you tear a resource down. The Queue Pair goes first, and the memory region is deregistered only after that. The steps run in the order they were built, but backwards, It helps to keep this order in a checklist beside the code, because the mistake is easy to make under pressure. A common case is a job that crashes during shutdown after a failure, when a thread frees a buffer that the Queue Pair still references. Following the teardown order avoids that crash, and it also keeps the logs clean, since the flush errors are drained before the resources they point to are gone.

### 5.3 Wire-level packet headers: BTH, RETH, AETH, and ICRC

When endpoint logs are inconclusive, network engineers capture packets on the wire. They inspect sequence numbers, opcodes, virtual addresses, and acknowledgement syndromes. Whether the traffic travels over native InfiniBand or RoCEv2 on UDP destination port 4791, every RDMA packet carries the same InfiniBand transport headers. The headers are the envelope and the address label that tell the receiver what the packet is for.

The Base Transport Header is 12 bytes long and appears in every RDMA packet. It carries the 8-bit Opcode, the Solicited Event bit, the Migration Request bit, the Pad Count, the Transport Header Version, the 16-bit Partition Key, the 24-bit Destination Queue Pair number, the Acknowledge Request bit, and the 24-bit Packet Sequence Number. The receiving HCA uses that 24-bit sequence counter in hardware to detect missing, duplicate, or out-of-order packets. The opcode is the most useful field to read first, because it names the operation the packet belongs to.

The RDMA Extended Transport Header is 16 bytes long. It appears only on the first or only packet of an RDMA Write, and on an RDMA Read Request. It carries the 64-bit target Virtual Address, the 32-bit Remote Key, and the 32-bit DMA Length. Those three fields are everything the remote HCA needs to place the data, so the header only has to appear once per message.

The ACK Extended Transport Header is 4 bytes long. It appears on RC Acknowledge packets, and on the first, last, or only packet of an RDMA Read Response. It carries an 8-bit Syndrome, which signals either a positive ACK with a credit count or a specific NAK reason, followed by a 24-bit Message Sequence Number. Every packet ends with a 4-byte Invariant CRC that covers all fields that do not change in transit from source HCA to destination HCA. A CRC is a checksum, and the invariant one skips the fields that routers are allowed to change. Routers may rewrite some fields as a packet crosses the fabric, such as the hop limit or the Ethernet addresses, so a checksum that covered those fields would fail on every hop. Leaving them out lets the receiving HCA check the packet against the one value that stays fixed from source to destination. A failed ICRC check means the payload was damaged in transit, and the receiver discards the packet without acknowledging it.

Read the block below as a decoder for the captures that follow. Think of it as a field guide. Each line names one header, its size, and the fields that matter for debugging. When you open a capture, find the opcode first, then look up which extended header should come next. Once you know those two things, the rest of the fields are easy to place, and you can check each one against the expected value.

```text
RDMA Transport Header Layout and Opcode Reference (decode_rdma_transport_headers in code/part12/rdma_fundamentals.py, ADC Ch 1 & Ch 7):
  - BTH (12 bytes, every RDMA packet):
      Opcode (8 bits): 12 (0x0c) = RC RDMA READ Request | 14 (0x0e) = RC RDMA READ Response Middle
                       17 (0x11) = RC Acknowledge       | 129 (0x81 = 10000001 binary) = RoCEv2 CNP
      Flags & Version: SE (1 bit), MigReq (1 bit), PadCnt (2 bits), TVer (4 bits)
      P_Key (16 bits): Default full-membership partition = 65535 (0xffff)
      Dest QP (24b):   Target Queue Pair on receiver (e.g., 0x000fe1, 0x00007b, 0x000123)
      AckReq + PSN:    AckReq (1 bit) + 24-bit Packet Sequence Number (0..0xffffff, e.g., 16548361, 16543980, 2592248)
  - RETH (16 bytes, on RDMA WRITE First/Only and RDMA READ Request opcode 12):
      Virtual Address (64 bits / 8 B, e.g., 0x00007ff9de5f4000) + rkey (32 bits / 4 B, e.g., 0x00207100) + DMA Length (32 bits / 4 B, e.g., 65536 = 0x00010000)
  - AETH (4 bytes, on RC Acknowledge opcode 17 and RDMA READ Response First/Last/Only):
      Syndrome (8 bits: bits 6:5 == 00 for positive ACK e.g. Syndrome 0, or NAK for RNR / PSN Sequence Error / Invalid Request / Remote Access Error)
      MSN (24 bits):   Message Sequence Number of last completed WR (e.g., MSN: 1)
  - ICRC (4 bytes):    32-bit end-to-end Invariant CRC
```

The table decodes three captured packets with those headers. Use it to check each field against your own capture. Start with the packet type, because that tells you how many bytes to expect. Then check the destination queue pair, the packet sequence number, and the partition key, since those three decide whether the packet belongs to your connection at all. The virtual address and remote key matter only for the request that carries them. A mismatch in the partition key usually means the two endpoints were placed in different partitions, which is a configuration problem and not a transport fault.

| Captured Packet Type | `BTH` (`12` B) Fields | Extended Header (`RETH` / `AETH`) | Payload & `ICRC` (`4` B) | IB Transport Total Bytes |
|---|---|---|---|---:|
| **1. `RC RDMA READ Request`** | `Opcode: 12`, `SE: False`, `MigReq: True`, `Pad: 0`, `TVer: 0`, `P_Key: 65535 (0xffff)`, `Dest QP: 0x000fe1`, `AckReq: True`, `PSN: 16548361` | **`RETH` (`16` B):** `VA: 0x00007ff9de5f4000`, `rkey: 0x00207100`, `DMA Length: 65536 (0x00010000)` | `0` B payload, `ICRC: 0xb87e1cbc` | **`32` B** (`12 + 16 + 0 + 4`) |
| **2. `RC RDMA READ Response Middle`** | `Opcode: 14`, `SE: False`, `MigReq: True`, `Pad: 0`, `TVer: 0`, `P_Key: 65535 (0xffff)`, `Dest QP: 0x00007b`, `AckReq: False`, `PSN: 16543980` | **None (`0` B)** (`Middle` packets omit `AETH`) | `1024` B payload (`a704e5c6...`), `ICRC: 0x5b522360` | **`1040` B** (`12 + 0 + 1024 + 4`) |
| **3. `RC Acknowledge`** | `Opcode: 17`, `SE: False`, `MigReq: True`, `Pad: 0`, `TVer: 0`, `P_Key: 65535 (0xffff)`, `Dest QP: 0x000123`, `AckReq: False`, `PSN: 2592248` | **`AETH` (`4` B):** `Syndrome: 0 (Ack, OpCode 0, Credit 0)`, `MSN: 1` | `0` B payload, `ICRC: 0x33e6e2af` | **`20` B** (`12 + 4 + 0 + 4`) |

The last column adds the header, payload, and CRC bytes for each packet. Those totals help with bandwidth math. A response packet carries most of its bytes as payload, so its overhead is small. An acknowledgement carries almost no payload, so its overhead looks large by comparison. Keep that in mind when you estimate how much of a link's capacity goes to protocol work and how much goes to the data itself. When a capture disagrees with the table, check the opcode first. The opcode tells you which header should follow, so a wrong opcode usually explains every other mismatch in the capture.

### 5.4 How transport congestion control protects RDMA Queue Pairs

A Reliable Connected Queue Pair treats any unacknowledged packet loss as a sequence error. Loss triggers hardware Go-Back-N retransmission, or it fails the Queue Pair with `IBV_WC_RETRY_EXC_ERR`. The fabric must therefore prevent buffer overflow at all six Clos congestion points: local leaf south-facing links, leaf-to-spine uplinks, spine-to-leaf downlinks, leaf-to-server egress links, spine-to-super-spine links, and super-spine-to-spine links. A Clos fabric is a multi-stage network where traffic passes through leaves, spines, and sometimes super-spines, and each of those stages can fill up.

InfiniBand prevents congestion drops natively at Layer 2, using credit-based flow control across Virtual Lanes. Virtual Lanes are separate channels that share one physical link, so one busy channel does not block the others. It pairs link-level credits with centralized Subnet Manager routing through OpenSM or UFM, Adaptive Routing, and optional NVIDIA SHARP in-network collective offloads. The Subnet Manager is the central controller that assigns addresses and computes routes for the InfiniBand fabric. OpenSM is the open-source subnet manager, and UFM is NVIDIA's fabric management platform.

RoCEv2 over Ethernet combines Explicit Congestion Notification, Congestion Notification Packets, and Priority Flow Control under the DCQCN algorithm. Switches order their queue thresholds strictly as `XON < ECN < XOFF`, so rate pacing resolves microbursts before hop-by-hop pause frames fire. Read that ordering as a ladder. The first rung marks packets, the next rung pauses the link, and the switch only pauses when marking was not enough.

Emerging standards complement DCQCN with Source Flow Control, which signals the switch-to-sender path directly, and Congestion Signaling, which carries in-band Layer 2 telemetry tags. Telemetry here means measurements the switch reports back. Chapters 12.3 and 12.4 cover RoCEv2 and switch tuning in full depth. Chapters 12.6 through 12.9 cover InfiniBand addressing, OpenSM, UFM, and SHARP.

```text
RoCEv2 Congestion Control Mechanics (ADC Ch 7 Table 7-1, Figs 7-10 to 7-21):
  - ECN (2-bit IP header field):   00 = Non-ECT | 01 / 10 = ECN-Capable Transport (set by sender) | 11 = Congestion Experienced (marked by switch)
  - CNP (Congestion Notification): Generated by receiving NIC on seeing ECN=11; sent on UDP port 4791 with ECN=01 and BTH opcode 129 (0x81 = 10000001)
  - PFC (IEEE 802.1Qbb L2 Pause):  EtherType 0x8808, opcode 0x0101, dst MAC 01:80:c2:00:00:01, class enable vector 0x0008 (lossless class C3 / Priority 3)
                                   XOFF pause timer = 65535 us vs XON timer = 0 us; guarded against deadlocks by a PFC Watchdog (e.g., 50 ms)
  - DCQCN Threshold Ordering:      XON < ECN < XOFF (e.g., Onyx traffic-class 3 ecn minimum-absolute 150 maximum-absolute 1500)
  - Emerging Standards:            Source Flow Control (SFC, IEEE 802.1Qdw) and Congestion Signaling (CSIG, draft-ravi-ippm-csig-01)
```

Before you tune a RoCEv2 fabric, confirm that the ECN and PFC thresholds sit in the order shown above. If the order is wrong, the pause fires before the marking can help, and the fabric pauses more than it needs to. To check the order on a real switch, read the thresholds for the lossless traffic class, and compare them against the marking and pause levels you expect. Do not check only one of them. A fabric can have correct ECN values and still pause early if the PFC threshold was set too low. When the pause counters climb while the marking counters stay flat, suspect the ordering first, because marking is supposed to act before pausing.

---

## Commands and configurations that matter

None of the commands below were run on a live fabric, because physical multi-node ConnectX InfiniBand and RoCEv2 hardware is not attached in the local build environment. The model logic is the part that was checked. The code in `code/part12/rdma_fundamentals_lab.py` runs every formula, state transition, and decoder in this chapter, so you can check the arithmetic even though the hardware steps are still unverified here.

### 1. Host OFED installation, locked memory limits, and BCM configuration (`untested here`)

Before you run any RDMA job on bare-metal Linux or NVIDIA Base Command Manager 11, verify three things. Locked memory must be unlimited, the DOCA-OFED kernel modules must be loaded, and the adapter link types must match the fabric. OFED is the OpenFabrics Enterprise Distribution, the bundle of RDMA drivers and tools. DOCA-OFED is NVIDIA's packaged version of it.

```bash
# 1. Configure unlimited locked memory for RDMA Memory Region page pinning (untested here)
cat << 'EOF' | sudo tee /etc/security/limits.d/99-rdma-memlock.conf
* soft memlock unlimited
* hard memlock unlimited
EOF
ulimit -l

# 2. Check installed DOCA-OFED / MLNX_OFED version and loaded kernel modules (untested here)
ofed_info -s
lsmod | egrep "mlx5_ib|mlx5_core|ib_uverbs|ib_core|rdma_cm|ib_ipoib"

# 3. BCM 11: Inspect supported DOCA-OFED versions (e.g., 2.9.4, 3.2.2) and install on head/image (untested here)
cat /cm/local/apps/cluster-tools/doca/etc/doca-ofed-versions.conf
/cm/local/apps/cluster-tools/bin/cm-doca-ofed-install.sh -v 3.2.2 -h
cat /etc/cm-ofed

# 4. BCM 11 cmsh: Configure ConnectX link type (IB vs ETH), SR-IOV VFs, OpenSM, and IPoIB (untested here)
cmsh -c "device; mlxconfig node001 --adapters"
cmsh -c "category use default; set -e MLX_link_type_p1 ETH; commit"
cmsh -c "device use node001; set -e MLX_num_vfs 16; interfaces; use ib0; set connectedmode yes; commit"
cmsh -c "device roles node001; assign subnetmanager; commit"
```

The first command writes the locked-memory limit to a file and then prints it, so you can confirm the change took effect. The OFED checks confirm the driver version and the kernel modules. The BCM commands are cluster-level, so run them from the head node, and check each change with a read-back before you move on.

### 2. Enumerating RDMA Verbs devices, port states, GIDs, and fabric counters (`untested here`)

Use the standard libibverbs and InfiniBand diagnostic utilities to verify device limits, port states, GID table indices, and hardware error counters. A GID is the global identifier that names a port, and on RoCEv2 it is the address the switches route on.

```bash
# 1. List RDMA verbs devices and inspect full HCA capability limits (untested here)
ibv_devices
ibv_devinfo -v -d mlx5_0

# 2. Inspect port logical state (Active), physical state (LinkUp), rate, Base LID, and SM LID (untested here)
ibstat
ibstatus
ibdev2netdev

# 3. Inspect RoCEv2 / InfiniBand GID tables (never hard-code GID index across heterogeneous hosts) (untested here)
show_gids

# 4. Query InfiniBand SM / SA records, link topology, optical BER (mlxlink), and error counters (untested here)
smpquery nodedesc 914
saquery 914
iblinkinfo
mlxlink -d mlx5_1 -c -m --json
perfquery -x 123 1
ibqueryerrors
ibdiagnet -c 1000
```

Run the first group to learn what the adapter is, the second group to learn whether its ports are ready, and the third to choose the right GID. The last group reads the optics and the error counters, which tell you about the cable and the switch side. A bit error rate, or BER, is the measure of how many bits arrive corrupted, and a rising BER points at the optics before it shows up as a job failure.

### 3. Validating Queue Pair transitions, latency, and line-rate bandwidth (`untested here`)

Before you launch a multi-node NCCL training job, run `ibv_rc_pingpong` and NUMA-pinned `perftest` benchmarks. They confirm that Queue Pairs transition cleanly to RTS and reach the expected line-rate bandwidth. Pinning the benchmark to the NUMA node that holds the HCA keeps the test from crossing the slow link between CPU sockets.

```bash
# 1. Minimal raw-verbs RC Queue Pair handshake test (surfaces INIT -> RTR MTU/GID mismatches) (untested here)
# Server (Node A):
ibv_rc_pingpong -d mlx5_0 -g 0
# Client (Node B):
ibv_rc_pingpong -d mlx5_0 -g 0 <node-a-ip>

# 2. NUMA-pinned RDMA Write latency sweep (2 B to 4 MiB) and bandwidth test (untested here)
# Server (Node A, pinned to HCA local NUMA node 0):
numactl --cpunodebind=0 --membind=0 ib_write_lat -d mlx5_0 -i 1 -a
numactl --cpunodebind=0 --membind=0 ib_write_bw -d mlx5_0 -i 1 --report_gbits

# Client (Node B, pinned to HCA local NUMA node 0):
numactl --cpunodebind=0 --membind=0 ib_write_lat -d mlx5_0 -i 1 -a <node-a-ip>
numactl --cpunodebind=0 --membind=0 ib_write_bw -d mlx5_0 -i 1 --report_gbits <node-a-ip>

# 3. Check RDMA hardware transport counters for PSN sequence errors, RNR NAKs, and timeouts (untested here)
head -n 20 /sys/class/infiniband/mlx5_0/ports/1/hw_counters/*
```

Run the ping-pong test first. If it fails with the RTR message, stop there, because the benchmarks cannot succeed on a Queue Pair that never reached RTS. The latency sweep and the bandwidth test come after it, and the counters at the end tell you whether the link is quietly dropping or retransmitting packets while the benchmark looks fine.

---

## How it fails

When an RDMA workload fails, you almost always see a generic job hang or startup crash. The generic message is the surface, and the real cause sits in a completion status or a counter. The diagnostic functions in `code/part12/rdma_fundamentals.py` model the six primary RDMA endpoint failure modes you are likely to meet in production AI clusters. They map each exact completion status or counter to its root cause and fix. Each row below is one of those failures, and you can match your logs against it.

The table shows you each failure mode's evidence, its root cause, and its fix.

| # | Failure Mode | Exact Symptom & Evidence | Root Cause Boundary | Deterministic Fix |
|---|---|---|---|---|
| **1** | **QP fails `INIT -> RTR` (`Failed to modify QP to RTR`, `EINVAL`)** | `rc_pingpong` or `ib_write_bw -x 2` prints `Failed to modify QP to RTR`; `ibstat` shows both ports `Active` and `ping` succeeds. | **Endpoint Path / MTU / GID Mismatch:** Either the requested `path_mtu` (`4096`) exceeds one port's `active_mtu` (`2048` in `ibv_devinfo -v`), or hard-coded GID index `-x 2` maps to `eth0.100` on Host A and a different VLAN/RoCEv1 entry on Host B (`QPN 0x0000`). | Compare `ibv_devinfo -v` (`active_mtu`) and `show_gids` (`VER v2`, netdev, VLAN) on both peers; standardize end-to-end jumbo MTU (`4096` IB / `9000` Ethernet) and select GIDs by semantic interface/version rather than raw index assumption. |
| **2** | **Receive Queue Starvation (`IBV_WC_RNR_RETRY_EXC_ERR`)** | Two-sided `Send`/`Receive` traffic stalls under burst load; sender `CQ` reports **`IBV_WC_RNR_RETRY_EXC_ERR`** and `hw_counters/rnr_nak_retry_err` increments. | **Remote Receive Queue Empty:** A `Send` arrived at the remote HCA when zero `ibv_post_recv()` WQEs were available in the Receive Queue, exhausting `rnr_retry` (`7`) RNR NAK backoff attempts. | Pre-post sufficient Receive WRs before transitioning to `RTR`, replenish RX descriptors in batches before hitting the low-water mark, or use a **Shared Receive Queue (`SRQ`)** / one-sided `RDMA Write`. |
| **3** | **Local or Remote Memory Protection Fault (`IBV_WC_LOC_PROT_ERR` / `IBV_WC_REM_ACCESS_ERR`)** | One specific buffer transfer fails immediately; `CQ` reports `IBV_WC_LOC_PROT_ERR` (local) or `IBV_WC_REM_ACCESS_ERR` (remote). | **PD Mismatch, Invalid Key, or Out-of-Bounds DMA:** QP and MR belong to different Protection Domains (`PD A` vs `PD B`), `addr + length` exceeds the registered MR size (`32768 + 65536 > 65536`), `MR` lacked `IBV_ACCESS_REMOTE_WRITE`, or `ibv_dereg_mr()` was called before in-flight WQEs completed. | Verify QP and MR share the same `ibv_pd`, check buffer bounds and `IBV_ACCESS_*` flags, and enforce the teardown rule: never deregister or free an MR until its completion entry (`CQE`) has been consumed. |
| **4** | **CQ Flush Storm (`1` `IBV_WC_RETRY_EXC_ERR` followed by `100s` of `IBV_WC_WR_FLUSH_ERR`)** | Application logs hundreds of `IBV_WC_WR_FLUSH_ERR` (`wr_id=1044..1046`) and blames a global fabric collapse. | **Secondary Queue Error Flushing:** `wr_id=1043` failed with `IBV_WC_RETRY_EXC_ERR` (`vendor_err=0x81`, peer crashed or path dropped ACKs), transitioning the QP to **`ERR`** and automatically flushing all subsequent queued WQEs. | Isolate the **first non-flush error (`wr_id=1043`)**; inspect `hw_counters/{packet_seq_err,local_ack_timeout_err}` and peer process health, then transition the QP `ERR -> RESET` (or recreate it) before resuming. |
| **5** | **`ibv_reg_mr()` fails at job startup with `ENOMEM` (`IBV_REG_MR_ENOMEM_MEMLOCK`)** | `NCCL` or `perftest` crashes during initialization before sending traffic: `Failed to register memory region` / `Cannot allocate memory`. | **Locked Memory Quota (`ulimit -l`) Too Low:** Container or host `memlock` limit is set to the Linux default of `64 KiB` (`65,536` bytes), blocking `ibv_reg_mr()` from pinning multi-megabyte or multi-gigabyte buffers. | Set `* soft memlock unlimited` and `* hard memlock unlimited` in `/etc/security/limits.conf` on hosts and `ulimits: memlock: -1` (or privileged / `IPC_LOCK`) in container runtimes. |
| **6** | **High Host CPU (`100%` core) or Bandwidth Collapse at Scale Despite RDMA** | Either `1` CPU core per rank is pegged at `100%`, or multi-node bandwidth degrades when scaling to `1,000+` GPUs with `4 KiB` pages. | **Busy Polling or HCA `MTT`/`ICM` Cache Thrashing:** Polling threads spin in `ibv_poll_cq()` continuously (intentional latency trade-off), or registering gigabytes of `4 KiB` pages (`262,144` MTT entries/GiB) plus `O(N^2)` `RC` QPs overflows NIC SRAM cache. | Bind busy-polling threads to the HCA's local NUMA node (`numactl`), register persistent **buffer pools backed by `2 MiB` hugepages** (`512x` fewer MTT entries), and use Ring/Tree or `DC` transport instead of full-mesh `RC` QPs. |

Start with the first row whose symptom matches your logs. Then check its root cause column before you change any setting. Work through the table in a fixed order, not by whichever row looks most familiar. Start by reading the status code or counter in your logs, because that single value narrows the list to one or two rows. Next, confirm the root cause on both ends of the connection, since most of these failures involve a mismatch between two hosts. Only then choose the fix. Changing a setting first and reading the logs afterward makes it hard to tell whether the change helped or merely hid the symptom. The memlock failure and the RNR starvation are the two rows whose log text is easiest to match.

---

## Hands-on lab

### Venue and scope
**Venue:** Local workstation or Nebius GPU VM with Python 3.10+ using `code/part12/rdma_fundamentals.py` and `code/part12/rdma_fundamentals_lab.py`.

The live InfiniBand and RoCEv2 hardware commands in the previous section are covered by the status above, because physical multi-node ConnectX fabrics are not attached in this build environment. You can still check the model side. `code/part12/rdma_fundamentals_lab.py` runs every formula, state transition, packet decode, and troubleshooting scenario in this chapter, and it checks each result deterministically. Deterministic here means the same inputs always give the same answers, so a rerun should match exactly.

### Step 1: Run the self-checking Chapter 12.2 RDMA fundamentals lab (`tested here`)

From the repository root, run the verification suite:

```bash
python3 code/part12/rdma_fundamentals_lab.py
```

The expected output reports 25 passed and 0 failed checks:

```text
=== Chapter 12.2 Lab: RDMA Fundamentals — Verbs, Queue Pairs & Memory Registration ===
  [PASS] V8 Ch3 & Lab 01: mlx5_0 capability profile matches ibv_devinfo -v (fw 28.39.2048, vendor 0x02c9, part 4129)
  [PASS] V8 Ch3 & Lab 01: mlx5_0 queue and MR limits (max_qp=262144, max_qp_wr=32768, max_sge=30, max_cq=16777216, max_cqe=4194303, max_mr=16777216)
  [PASS] V8 Ch3 & SCL Ch5: Transport service types RC, UC, UD, and DC are modeled with exact operation support
  [PASS] V8 Ch3 Fig 8.3.4: Valid QP lifecycle transitions RESET -> INIT -> RTR -> RTS -> SQD / ERR -> RESET succeed
  [PASS] V8 Ch3 Fig 8.3.4: Skipping INIT/RTR (RESET -> RTS directly) is rejected with EINVAL
  [PASS] V8 Ch3 Scenario 1 (rc_pingpong): Requesting path_mtu=4096 when port active_mtu=2048 fails INIT -> RTR with EINVAL
  [PASS] V9 Ch3 Scenario 1 (ib_write_bw -x 2): Mismatched GID index (QPN 0x0000, invalid peer GID) fails INIT -> RTR
  [INFO] V8 Ch3 CQ stream: first_fail=wr_id 1043 (IBV_WC_RETRY_EXC_ERR, vendor_err=0x81), flushed=[1044, 1045, 1046]
  [PASS] V8 Ch3 Scenario 4: wr_id=1043 (IBV_WC_RETRY_EXC_ERR, vendor_err=0x81) is isolated as root cause before 3 flushed WRs (1044..1046)
  [PASS] V8 Ch3 Scenario 2: IBV_WC_RNR_RETRY_EXC_ERR maps to REMOTE_RECEIVE_QUEUE_STARVATION
  [INFO] 65,536 B (64 KiB) MR on 4,096 B pages: pinned_pages=16, mtt_bytes=128 B, status=IBV_WC_SUCCESS
  [PASS] V8 Ch3 & ADC Ch1 Fig 1-14: 65,536 B (0x00010000) DMA region pins 16 x 4,096 B pages (128 B MTT entries) and succeeds
  [INFO] 1 GiB (1,073,741,824 B) MR MTT comparison: 4 KiB pages=262144 pages (2097152 B = 2 MiB MTT) vs 2 MiB hugepages=512 pages (4096 B = 4 KiB MTT)
  [PASS] MTT Scaling Math: 1 GiB (1,073,741,824 B) requires 262,144 x 4 KiB pages (2,097,152 B = 2 MiB MTT) vs 512 x 2 MiB pages (4,096 B = 4 KiB MTT, 512x reduction)
  [PASS] SCL Ch24 & VL10 Ch15: Registering 131,072 B when ulimit -l (memlock) is 65,536 B fails with IBV_REG_MR_ENOMEM_MEMLOCK
  [PASS] V8 Ch3 Fig 8.3.2 & Scenario 3: Protection Domain mismatch raises IBV_WC_LOC_PROT_ERR; remote bounds violation raises IBV_WC_REM_ACCESS_ERR
  [PASS] ADC Ch1 Fig 1-12: RDMA Write CM session has 13 total steps (3 handshake + 6 RDMA write + 4 terminate)
  [PASS] ADC Ch1 Fig 1-13: RDMA Read CM session (20.0.0.2 -> 60.0.0.2) has 11 total steps (3 handshake + 4 RDMA read + 4 terminate)
  [PASS] ADC Ch1 Fig 1-14: RDMA READ Request (opcode 12, P_Key 65535, Dest QP 0x000fe1, PSN 16548361) decodes 16B RETH (VA 0x00007ff9de5f4000, rkey 0x00207100, len 65536, ICRC 0xb87e1cbc)
  [PASS] ADC Ch1 Fig 1-15: RDMA READ Response Middle (opcode 14, Dest QP 0x00007b, PSN 16543980, 1024 B payload, ICRC 0x5b522360) has 1040 B transport frame
  [PASS] ADC Ch1 Fig 1-16: RC Acknowledge (opcode 17, Dest QP 0x000123, PSN 2592248) decodes 4B AETH (Syndrome 0 Ack, MSN 1, ICRC 0x33e6e2af)
  [PASS] ADC Ch7 & VL6 Ch1: RoCEv2 CNP uses BTH opcode 129 (0x81 = 10000001) over UDP destination port 4791
  [INFO] 128-node x 8-GPU (1,024 ranks) full RC mesh: qps_per_rank=1023, qps_per_node=8184, cluster_qps=1047552; VL6 ib_write_bw 65536B: avg=23450.5 MB/s (93.8% of 25000 MB/s HDR)
  [PASS] V8 Ch3 Customer Scenario: 128 nodes x 8 GPUs (1,024 ranks) full-mesh RC requires 1,023 QPs/rank, 8,184 QPs/node, and 1,047,552 cluster QPs
  [PASS] VL6 Ch1 §5.2 ib_write_bw (65,536 B, 5,000 iters, 200G HDR = 25,000 MB/s line rate): 23,450.5 MB/s is 93.8% of line rate
  [PASS] Rejects unknown QP state name in validate_qp_transition
  [PASS] Rejects empty completions list in analyze_cq_completion_stream
  [PASS] Rejects non-positive buffer_bytes in evaluate_memory_registration_and_mtt
  [PASS] Rejects opcode 12 (RDMA READ Request) without RETH fields

Summary: 25 passed, 0 failed (total 25)
```

The PASS lines are the checks, and the INFO lines report measured values. Read the summary at the bottom first. A result of 25 passed and 0 failed means every claim in this part of the chapter matched the code. If the count is different, the INFO line just above the failing check shows the value the check compared.

---

## Common first mistakes

1. **Discarding completion status codes and logging a generic network timeout:** Every non-success completion status, such as `IBV_WC_LOC_PROT_ERR`, `IBV_WC_REM_ACCESS_ERR`, `IBV_WC_RNR_RETRY_EXC_ERR`, or `IBV_WC_RETRY_EXC_ERR`, points to a specific fault domain. If you swallow that code, operators stay blind, and you can lose days to switch debugging. The fix is to log the status with the request that caused it.
2. **Investigating IBV_WC_WR_FLUSH_ERR completions instead of the first failing Work Request:** When a Queue Pair enters the ERR state, every later queued Work Queue Element flushes with `IBV_WC_WR_FLUSH_ERR`. Log and alert on the first non-flush error. The flush lines are loud, but they are the follow-on, not the cause.
3. **Hard-coding RoCEv2 GID index numbers across a cluster:** GID table ordering depends on the order in which the Linux kernel discovers base interfaces, VLANs, and IPv4 or IPv6 addresses. Resolve the GID index dynamically by matching RoCEv2 version, interface name, and subnet, so you never rely on a fixed number. A number that works on one host can point at a different interface on the next host.
4. **Assuming a local RDMA Write completion means the remote application processed the buffer:** A local `RDMA_WRITE` completion proves only that the remote HCA acknowledged DMA placement into remote memory. If the remote CPU or GPU kernel must know the buffer is ready, use `IBV_WR_RDMA_WRITE_WITH_IMM`. A follow-up Send or an atomic or polled completion flag also works. Pick one of these signals on purpose, rather than hoping the write is noticed.
5. **Deregistering or freeing memory before draining the Queue Pair:** Calling `ibv_dereg_mr` while outstanding Work Queue Elements still reference that buffer causes immediate local protection or remote access crashes. Transition the Queue Pair to ERR or RESET, and drain all Completion Queue Entries, before you destroy Memory Regions. The order matters more than the speed of the cleanup.
6. **Forgetting unlimited locked memory in container specs, or registering 4 KiB buffers on the hot path:** Calling `ibv_reg_mr` pins physical pages and performs a synchronous kernel call and MTT update. Configure `ulimit -l unlimited` in container specs, and pre-register a reusable hugepage-backed buffer pool at startup. Registration belongs in the setup phase, not in the middle of the training loop.

---

## Exercises

1. Start with a capability audit and an INIT to RTR triage. Using `V8_CH3_MLX5_PROFILE` and `validate_qp_transition` in `code/part12/rdma_fundamentals.py`, state the exact `mlx5_0` values for firmware version, vendor ID, part ID, queue limits, and active MTU. Then explain why `rc_pingpong` fails with `Failed to modify QP to RTR` (EINVAL) under the parameters you see below.
2. Next, work the MTT page-table scaling and the locked-memory gate. Using `evaluate_memory_registration_and_mtt`, calculate the number of pinned pages for the first buffer configuration below. Do the same for the second and third configurations. Then calculate the 8-byte MTT table size in bytes for each one. Explain why registering 131,072 bytes fails when `ulimit -l` is 65,536 bytes. Write the two lines in `/etc/security/limits.conf` that fix it.
3. Take the five-entry completion stream below and isolate the root cause. Using `analyze_cq_completion_stream`, identify the root-cause `wr_id`. Then name its status, its vendor error, the flushed list, and the fault domain. Finally, contrast how your remediation changes if the failing request instead reported IBV_WC_RNR_RETRY_EXC_ERR, IBV_WC_LOC_PROT_ERR, or IBV_WC_REM_ACCESS_ERR.
4. Compare the two Connection Manager sessions. Using `trace_rdma_cm_session_steps`, list the three phases for RDMA Write. Then list the three phases for RDMA Read. Next, give the exact step counts for each phase. Explain why the RDMA Write exchange takes 6 transfer steps while RDMA Read takes 4 transfer steps.
5. Decode the three captured packets. Using `decode_rdma_transport_headers`, compute the InfiniBand transport frame byte size for each captured packet. Then decode the header fields for each of the three captured packets you will find below.
6. Work the cluster-wide scaling numbers for the 128-node cluster below. Using `evaluate_qp_scaling_and_perftest`, compute the total ranks. Compute the RC Queue Pair count per rank, per node, and cluster-wide. Compare the RC, UC, UD, and DC transports. Finally, verify the line-rate utilization percentage for the `ib_write_bw` benchmark output below. Then verify the message rate for that same benchmark output.

```text
Exercise Input Parameters and Captured Evidence Reference:
  - Ex 1 (rc_pingpong):  LID 0x000c, QPN 0x00012a, PSN 0x3a1f2e -> LID 0x0051, QPN 0x0000e3, PSN 0x0091ab; path_mtu=4096 vs peer active_mtu=2048
  - Ex 2 (MTT & ulimit): (a) 65,536 B (64 KiB) on 4,096 B pages | (b) 1 GiB (1,073,741,824 B) on 4,096 B pages | (c) 1 GiB on 2 MiB (2,097,152 B) hugepages
                         Registration test: 131,072 B buffer when ulimit -l (memlock) = 65,536 B
  - Ex 3 (CQ Stream):    [(1042, "IBV_WC_SUCCESS", "RDMA_WRITE", 0x00), (1043, "IBV_WC_RETRY_EXC_ERR", "RDMA_WRITE", 0x81),
                          (1044, "IBV_WC_WR_FLUSH_ERR", "RDMA_WRITE", 0x00), (1045, "IBV_WC_WR_FLUSH_ERR", "SEND", 0x00), (1046, "IBV_WC_WR_FLUSH_ERR", "SEND", 0x00)]
  - Ex 4 (CM Sessions):  RDMA_WRITE (13 steps, Steps 4..9 transfer) vs RDMA_READ (11 steps between 20.0.0.2 and 60.0.0.2, Steps 4..7 transfer)
  - Ex 5 (Wire Packets): (a) RC RDMA READ Request: opcode 12, P_Key 65535, Dest QP 0x000fe1, PSN 16548361, RETH VA 0x00007ff9de5f4000, rkey 0x00207100, DMA len 65536, ICRC 0xb87e1cbc
                         (b) RC RDMA READ Response Middle: opcode 14, Dest QP 0x00007b, PSN 16543980, 1,024 B payload, ICRC 0x5b522360
                         (c) RC Acknowledge: opcode 17, Dest QP 0x000123, PSN 2592248, AETH Syndrome 0 Ack, MSN 1, ICRC 0x33e6e2af
  - Ex 6 (Scale & Perf): 128 nodes x 8 GPUs/node (1,024 ranks); ib_write_bw: 65,536 B messages, 5,000 iterations, TX depth 128,
                         23,450.5 MB/sec average (23,500.2 MB/sec peak, 0.375208 Mpps) on 200 Gbps (25,000 MB/sec) HDR link
```

Work through the six exercises in order, using the inputs above. Keep the captured values in front of you while you work, because each exercise checks one of them.

---

## Interview angles

1. **Whiteboard question: the end-to-end Verbs object graph and ownership transfer.**
   - *Prompt:* Draw the local and remote RDMA objects required for a Reliable Connected path. Mark where buffer ownership changes during a two-sided Send versus a one-sided RDMA Write.
   - *What to draw and say:* Place the Protection Domain at the top of each endpoint, with the Memory Region and Queue Pair both hanging off that same Protection Domain. Draw the Completion Queue as a sibling that serves one or more Queue Pairs, and place the HCA in the middle. For a two-sided Send, the remote peer must first post a Receive Work Request to its Receive Queue. Ownership of that remote buffer passes to the remote HCA when it is posted, and it returns to the remote application only when the receive completion entry fires. For a one-sided RDMA Write, the remote Receive Queue is untouched. The initiator puts the remote virtual address and remote key in the RETH header, and the remote HCA writes payload bytes straight into the remote Memory Region. The remote CPU never knows the write occurred unless it is notified through immediate data, a follow-up Send, or a polled memory flag.
2. **Scenario question: the network is healthy, ping works, the port is Active, but every QP fails.**
   - *Prompt:* After a VLAN or switch maintenance window, basic IP reachability and `ibstat` succeed on all nodes. Yet distributed jobs fail during connection setup with `Failed to modify QP to RTR`. How do you isolate the fault?
   - *Answer:* A standard ping only exercises the Linux kernel IP stack over `ib0` or `eth0`. Failing to modify the Queue Pair to RTR means the Queue Pair reached INIT locally. The kernel verbs provider then rejected the remote path attributes during the INIT to RTR transition. When you check, look at three things across both endpoints. First, compare `ibv_devinfo -v` to confirm that `active_mtu` matches on both ports and across every switch hop. Second, inspect `show_gids` to confirm that both hosts selected a GID index with matching RoCEv2 version, VLAN, and netdev. Do not hard-code index 2 across differently ordered tables. Third, verify Partition Key membership on InfiniBand.
3. **Architecture question: a reusable registered buffer pool and surviving quadratic QP scale.**
   - *Prompt:* Why should an AI framework never call `ibv_reg_mr` per message, and how do you prevent Queue Pair context thrashing on a 1,024-GPU or 16,384-GPU cluster?
   - *Answer:* Calling `ibv_reg_mr` invokes the operating system kernel to pin physical pages and writes physical page addresses into the HCA Memory Translation Table. Calling it per message brings back the exact kernel overhead RDMA was designed to bypass. Instead, you pre-register a fixed pool of 2 MiB hugepage-backed buffers at startup, which shrinks MTT entries by 512x. You track buffer slots with a lock-free free-list, and return a buffer to the free-list only after its Completion Queue Entry has been consumed. At cluster scale, avoid all-to-all dedicated RC Queue Pairs. Use NCCL Ring and Tree neighbor channels, Shared Receive Queues, or Dynamic Connected transport instead.

---

## Checkpoint questions (20)

<details>
<summary>**1. Why does standard Linux TCP/IP networking bottleneck a 100 Gbps–400 Gbps GPU cluster even when the NIC hardware is rated for line rate?**</summary>

Every socket send and receive needs a system call from user space into the kernel, a change of CPU privilege, and a buffer copy between user space and kernel socket buffers. The CPU also runs software TCP header and checksum work on transmit, and it handles hardware interrupts on receive. At 100 to 400 Gbps, millions of packets per second can pin host CPU cores at 100 percent kernel system time. That overhead caps a 100 Gbps ConnectX-5 cluster at around 30 Gbps and adds tens of microseconds of tail-latency jitter.
</details>

<details>
<summary>**2. Does RDMA eliminate the operating system kernel completely? Explain the difference between the RDMA control path and data path.**</summary>

No. RDMA removes the kernel from the per-message data path, not from the whole system. The control path still goes through the Linux kernel, via `/dev/infiniband/uverbsN`. There the kernel opens the device context, allocates Protection Domains, pins virtual pages in physical RAM, and moves Queue Pairs through RESET, INIT, RTR, and RTS. Once the connection is up, the data path uses memory-mapped doorbells in user space and hardware DMA. Packets then flow without system calls, context switches, or kernel buffer copies.
</details>

<details>
<summary>**3. In AI Data Center Network Design Chapter 1, how does a single slow thread affect Job Completion Time across 100 parallel GPU tasks versus 10 serial tasks?**</summary>

As you can see below, Job Completion Time is set by the slowest worker when tasks synchronize at a barrier. The block below compares the serial and parallel runs:

```text
Serial vs Parallel Job Completion Time (ADC Ch 1, Figs 1-4 to 1-6):
  - Serial (n = 10 tasks):     9 tasks x 1 ms + 1 taskX x 1 s (1,000 ms) = 1.010 seconds total JCT
  - Parallel (100 threads):    99 threads finish in 1 ms (< 100 ms), 1 thread takes 1 s -> 99 threads wait 999 ms at barrier, pinning JCT at 1 second
```
</details>

<details>
<summary>**4. What are the five node-local RDMA architectural layers from the application down to the physical wire?**</summary>

1. **Application or Collective Library:** Generates work requests in NCCL, MPI, or UCX.
2. **Verbs API:** Exposes standard queue, memory, and completion verbs through `libibverbs`.
3. **RDMA Driver:** Manages work queues and virtual-to-physical MTT address translation in `mlx5_ib`, `ib_uverbs`, and `ib_core`.
4. **RDMA NIC or Host Channel Adapter:** Executes DMA, packetization, PSN sequencing, and hardware ACK and NAK reliability.
5. **Physical Wire:** Carries InfiniBand or Ethernet frames across copper or optical media.
</details>

<details>
<summary>**5. Compare InfiniBand, RoCEv1, RoCEv2, and iWARP in terms of network and transport encapsulation and routing scope.**</summary>

Each protocol wraps the RDMA payload in different headers. The block lists the headers each one adds:

```text
RDMA Transport Protocol Comparison:
  - InfiniBand (IB): Native IB LRH (8 B, credit-based lossless) + optional GRH (40 B) + BTH (12 B) + Payload + ICRC (4 B) + VCRC (2 B)
  - RoCEv1:          Ethernet L2 header (EtherType 0x8915) + IB GRH + IB BTH + Payload + ICRC + Ethernet FCS (L2 broadcast domain only)
  - RoCEv2:          Ethernet L2 + IPv4/IPv6 + UDP (dst port 4791, src port hashed from QPN) + IB BTH (12 B) + Payload + ICRC (4 B) + FCS (L3 routable)
  - iWARP:           RDMA over hardware-offloaded TCP/IP (MPA / DDP / RDMAP); tolerates lossy Ethernet but adds latency and silicon complexity
```
</details>

<details>
<summary>**6. In the annotated mlx5_0 capability output, what do the six primary hardware limits tell an infrastructure architect?**</summary>

The six limits below show you what the adapter can take, and what it cannot:

```text
Annotated ibv_devinfo -v -d mlx5_0 Capability Limits:
  - max_qp:     262144         -> Maximum Queue Pairs supported on mlx5_0
  - max_qp_wr:  32768          -> Maximum Work Requests per QP queue (requesting 100,000 fails allocation)
  - max_sge:    30             -> Maximum Scatter-Gather Entries per Work Request
  - max_cqe:    4194303        -> Maximum entries per Completion Queue (with max_cq: 16777216)
  - atomic_cap: ATOMIC_HCA (1) -> Hardware supports 64-bit RDMA Atomic operations (CAS / FAA)
  - active_mtu: 4096 (5)       -> Negotiated payload MTU (must be >= requested_path_mtu on all hops or INIT -> RTR fails)
```
</details>

<details>
<summary>**7. What is a Protection Domain, and what happens if Queue Pair A in PD A references a Memory Region registered in PD B?**</summary>

A Protection Domain is the hardware isolation container that groups compatible Queue Pairs and Memory Regions. Suppose Queue Pair A, in Protection Domain A, posts a Work Request whose Scatter-Gather Entry uses a local key from a Memory Region in Protection Domain B. The local HCA blocks the DMA before it reaches the wire. Queue Pair A then moves to the ERR state, and the completion entry carries status `IBV_WC_LOC_PROT_ERR`.
</details>

<details>
<summary>**8. What four actions occur when an application calls ibv_reg_mr, and why is ulimit -l a frequent source of container startup failures?**</summary>

`ibv_reg_mr` does four things, in order. It pins the virtual pages in physical RAM, so the kernel cannot swap or move them during DMA. It checks the pinned byte count against the process `RLIMIT_MEMLOCK` quota. It programs the virtual-to-physical translations into the HCA Memory Translation Table. Last, it returns the 32-bit local key and remote key. Unconfigured Linux hosts and containers default `ulimit -l` to 64 KiB. Any larger registration, such as 128 KiB, then fails with `ENOMEM` until soft and hard `memlock` limits are set to `unlimited`.
</details>

<details>
<summary>**9. Calculate the number of pinned pages and 8-byte MTT table footprint for a 1 GiB Memory Region using 4 KiB pages versus 2 MiB hugepages. Why does this affect tail latency?**</summary>

You can work the 1 GiB example two ways. With 4 KiB pages, the Memory Region needs 262,144 pinned pages, and 262,144 pages at 8 bytes each comes to 2 MiB of table. With 2 MiB hugepages, it needs only 512 pages, and the table shrinks to 4 KiB, a 512x reduction. The block below shows the arithmetic:

```text
1 GiB (1,073,741,824 B) Memory Region MTT Footprint Comparison:
  - With 4 KiB (4,096 B) pages:     1,073,741,824 / 4,096     = 262,144 pages x 8 B = 2,097,152 bytes (2 MiB of MTT entries per GiB)
  - With 2 MiB (2,097,152 B) pages: 1,073,741,824 / 2,097,152 =     512 pages x 8 B =     4,096 bytes (4 KiB of MTT entries per GiB -> 512x reduction)
```

Tail latency suffers because hundreds of thousands of MTT entries overflow the HCA on-chip ICM SRAM cache. When that happens, the NIC must fetch page-table translations across the PCIe bus before it can run the payload DMA.
</details>

<details>
<summary>**10. What is the difference between a Work Request, a Work Queue Element, and a Scatter-Gather Entry?**</summary>

A Work Request is the user-space C structure you pass to `ibv_post_send` or `ibv_post_recv`. The provider driver turns it into a hardware Work Queue Element, a descriptor placed in the Queue Pair ring buffer, and then rings the HCA doorbell. Inside the Work Request, each Scatter-Gather Entry describes one contiguous registered memory segment by address, length, and local key. That lets one request gather or scatter up to 30 discontiguous buffers in a single hardware DMA operation.
</details>

<details>
<summary>**11. Contrast two-sided Send and Receive operations with one-sided RDMA Write and RDMA Read operations. What does a local RDMA Write completion prove and not prove?**</summary>

Two-sided Send and Receive use channel semantics. The remote application must pre-post a Receive Work Request before the packet arrives, and the remote CPU gets a completion entry. One-sided RDMA Write and Read use memory semantics. The initiator names the remote virtual address and remote key in the 16-byte RETH header, and the remote HCA does the DMA directly, with no remote CPU involvement. On a Reliable Connected Queue Pair, the initiator's local completion proves that the remote HCA placed the data into remote memory. It does not prove the remote application noticed the data, unless you notify it through `RDMA_WRITE_WITH_IMM`, a follow-up Send, or a polled memory flag.
</details>

<details>
<summary>**12. Why do high-performance RDMA applications use unsignaled Work Requests, and what happens if they never post a signaled Work Request?**</summary>

Building and DMA-writing a 64-byte Completion Queue Entry, then polling it in user space, adds PCIe and CPU cost to every Work Request. Instead, the application signals only every 16th or 32nd request with `IBV_SEND_SIGNALED`, and it relies on FIFO Send Queue ordering. When the completion for request 32 arrives, requests 1 through 31 are guaranteed complete. If your application never posts a signaled request, no completions reclaim Send Queue slots. The Send Queue then overflows after `max_qp_wr` posts.
</details>

<details>
<summary>**13. Compare the four RDMA transport service types across connection model, reliability, supported verbs, and Queue Pair scaling.**</summary>

- **RC (Reliable Connected):** Connects 1-to-1 with a dedicated peer Queue Pair, using hardware ACK, NAK, and retry. It supports Send, Receive, RDMA Write, RDMA Read, and Atomics, and it scales quadratically across a full mesh.
- **UC (Unreliable Connected):** Connects 1-to-1 without ACK or retry. It supports Send, Receive, and RDMA Write only, and it also scales quadratically.
- **UD (Unreliable Datagram):** Operates connectionlessly, 1-to-M, through per-message Address Handles, without reliability or ordering. It supports single-MTU Send and Receive, plus multicast, using just 1 Queue Pair per rank.
- **DC (Dynamic Connected):** Connects 1-to-M reliably by letting a Dynamic Connected Initiator target any remote Dynamic Connected Target per burst. It supports all verbs, including Read and Atomics, while keeping initiator Queue Pair counts constant.
</details>

<details>
<summary>**14. In a 128-node cluster with 8 GPUs per node, how many Queue Pairs are required per rank, per node, and cluster-wide for a full-mesh RC design?**</summary>

The block below works the full-mesh RC math for 128 nodes:

```text
Full-Mesh RC Queue Pair Scaling (128 nodes x 8 GPUs/node):
  - Total GPU ranks (N):       128 x 8       = 1,024 ranks
  - RC QPs per rank (N - 1):   1,024 - 1     = 1,023 QPs
  - RC QPs per 8-GPU node:     8 x 1,023     = 8,184 QPs
  - Total cluster-wide RC QPs: 1,024 x 1,023 = 1,047,552 QPs
```
</details>

<details>
<summary>**15. Walk through the six states of the Queue Pair state machine and the mandatory attributes for INIT to RTR and RTR to RTS.**</summary>

- **RESET:** The initial state after `ibv_create_qp`.
- **RESET to INIT:** Requires `port_num`, `pkey_index`, and `qp_access_flags`, and it lets you pre-post Receive Work Requests.
- **INIT to RTR:** Requires `path_mtu`, `dest_qp_num`, `rq_psn`, and `ah_attr`, which holds the remote LID or GID, `sgid_index`, and service level.
- **RTR to RTS:** Requires `sq_psn`, `timeout`, `retry_cnt`, `rnr_retry`, and `max_rd_atomic`.
- **RTS to SQD:** Drains in-flight sends cleanly before attributes are modified or the Queue Pair returns to RTS.
- **ERR:** Entered on a fatal transport or protection failure. It flushes remaining requests with `IBV_WC_WR_FLUSH_ERR`, and the Queue Pair must transition to RESET to recover.
</details>

<details>
<summary>**16. A polling loop returns success on request 1042, retry exceeded on request 1043, and flush errors on requests 1044 through 1046. Which request is the root cause, and why did 1044 through 1046 fail?**</summary>

Suppose your log shows this pattern. Request `wr_id=1043` (`IBV_WC_RETRY_EXC_ERR`, `vendor_err=0x81`) is the only root cause. Its local HCA exhausted the hardware retry counter while waiting for an ACK from the remote peer. That failure moved the Queue Pair into the ERR state. The HCA then drained every later queued request, `wr_id=1044..1046`, into the Completion Queue with `IBV_WC_WR_FLUSH_ERR`.
</details>

<details>
<summary>**17. Compare busy polling and event-driven completion. Why can 100 percent CPU utilization on one core be normal in an RDMA job?**</summary>

Busy polling via `ibv_poll_cq` spins in user space and checks the Completion Queue ring buffer. It detects completions in under a microsecond, with minimal tail-latency jitter, but it keeps the polling CPU core at 100 percent. Event-driven completion sleeps until a hardware interrupt wakes the thread. That saves CPU during idle periods, but it adds interrupt and scheduler wake-up latency. So 100 percent CPU on a dedicated polling thread is a deliberate low-latency choice, not a broken TCP fallback. Pin that polling thread to the local NUMA node of the HCA.
</details>

<details>
<summary>**18. Decode the fields and byte sizes of BTH, RETH, AETH, and ICRC in an RDMA READ Request, Response Middle, and RC Acknowledge.**</summary>

You can decode the three packets with the header layout below:

```text
Wire-Level RDMA Packet Header Breakdown (ADC Ch 1, Figs 1-14 to 1-16):
  - BTH (12 B):  Opcode (8b), SE/MigReq/PadCnt/TVer (8b), P_Key (16b, 65535), Reserved (8b), Dest QP (24b), AckReq+Reserved (8b), PSN (24b)
  - Packet 1 — RC RDMA READ Request (opcode 12, Dest QP 0x000fe1, PSN 16548361):
      12 B BTH + 16 B RETH (VA 0x00007ff9de5f4000, rkey 0x00207100, DMA len 65536 / 0x00010000) + 4 B ICRC (0xb87e1cbc) = 32 bytes total
  - Packet 2 — RC RDMA READ Response Middle (opcode 14, Dest QP 0x00007b, PSN 16543980):
      12 B BTH + 1,024 B payload + 4 B ICRC (0x5b522360) = 1,040 bytes total (no RETH or AETH)
  - Packet 3 — RC Acknowledge (opcode 17, Dest QP 0x000123, PSN 2592248):
      12 B BTH + 4 B AETH (Syndrome 0 = Ack, MSN = 1) + 4 B ICRC (0x33e6e2af) = 20 bytes total
```
</details>

<details>
<summary>**19. How do ECN, Congestion Notification Packets, Priority Flow Control, and DCQCN interact to keep RoCEv2 Queue Pairs from hitting retry timeouts?**</summary>

DCQCN depends on three steps, and the switch thresholds must be ordered as `XON < ECN < XOFF`. First, when a switch egress queue crosses the ECN threshold, the switch sets the 2-bit IP ECN field to `11` and forwards the packet. Second, the destination NIC sees `ECN = 11` and sends a RoCEv2 Congestion Notification Packet back to the sender. That packet uses UDP port 4791, BTH opcode 129 (`0x81`), and `ECN = 01`, and it slows the offending Queue Pair's injection rate. Third, if a microburst still pushes the buffer past the XOFF threshold, the switch sends an upstream Layer 2 PFC pause frame, which halts transmission before any packet is dropped. Transmission resumes once the queue drains below XON, and a PFC Watchdog guards against circular pause storms.
</details>

<details>
<summary>**20. How do Supercomputers for Linux SysAdmins Chapter 5 and BCM 11 distinguish GUIDs, LIDs, GIDs, Directed-Route SMPs, and IPoIB link-layer addresses?**</summary>

The block below lays out the InfiniBand addressing hierarchy and the two IPoIB modes, so you can compare them side by side:

```text
InfiniBand Addressing Hierarchy and IPoIB Modes (SCL Ch 5, BCM 11 Admin Manual):
  - GUID (64-bit):     Manufacturer-assigned hardware ID (NodeGUID, PortGUID, SystemImage GUID); identifies components, never used as routing header address
  - LID (16-bit):      Subnet-local forwarding address assigned by Subnet Manager (OpenSM/UFM): 1..0xBFFF unicast, 0xC000..0xFFFE multicast, 0xFFFF permissive
                       Supports up to 49,151 devices/subnet and 2^LMC consecutive LIDs per port for multipath routing
  - GID (128-bit):     IPv6-formatted global port address (0xFE80::/64 link-local + 64-bit PortGUID, 0xFEC0::/64 site-local, 0xFF00::/8 multicast) in 40-byte GRH
  - Directed-Route:    Used by Subnet Management Packets (SMPs, smpquery) before LIDs exist, listing explicit switch port hops (hop count, hop pointer, D bit 0/1)
  - IPoIB (ib0):       Runs TCP/IP over InfiniBand using a 20-byte hardware address (Flags + QPN + GID; requires ip addr rather than 6-byte ifconfig)
                       Operates in datagram mode (UD, up to 4K MTU) or connected mode (RC/UC, up to 64K MTU via set connectedmode yes in BCM cmsh)
```
</details>

---

## Sources and review notes

### Primary sources read in full for this chapter

The primary `nvidia-devops` notes and book chapters read in full and migrated into this chapter are cataloged in the reference block below.

```text
1. Author's nvidia-devops Notes (all mapped files for 12.2 read and migrated in full):
   - nvidia-zero-to-hero/volume-08/chapter-03-verbs-queue-pairs-and-completion-queues.md
     (Chapter 03 — Verbs, Queue Pairs, and Completion Queues, 4,826 words: opening production story, Figure 8.3.1 CQE decision tree,
      Verbs interface, ibv_devinfo -v -d mlx5_0 fw_ver 28.39.2048 vendor_id 0x02c9 part 4129 max_qp 262144 max_qp_wr 32768 max_sge 30
      max_cq 16777216 max_cqe 4194303 max_mr 16777216 atomic_cap ATOMIC_HCA (1) active_mtu 4096, Protection Domains, Memory Regions,
      Completion Queues, Queue Pairs, WRs/WQEs/SGEs, Send/Receive vs RDMA Write/Read/Atomics, RC/UC/UD transports,
      RESET -> INIT -> RTR -> RTS -> SQD / ERR state machine, signaled vs unsignaled WRs, busy polling vs event completion,
      safe teardown lifecycle, Scenarios 1-5 including rc_pingpong Failed to modify QP to RTR and wr_id=1042..1046
      IBV_WC_RETRY_EXC_ERR 0x81 + IBV_WC_WR_FLUSH_ERR, and O(N^2) QP scaling customer scenario)
   - nvidia-zero-to-hero/volume-08/chapter-12-volume-08-summary.md
     (Chapter 12 — Volume 08 Summary, 2,293 words: 8-layer Architecture Summary Table from Physical/Link/Subnet/Routing to Transport
      QP/CQ/MR/keys, GPU Direct, Collective, and Application; 10 Production Design Principles; layered troubleshooting sequence)
   - nvidia-zero-to-hero/volume-08/index.md
     (Volume 08 — InfiniBand, 1,406 words: 128-node >20% step-time variation production story, managed RDMA fabric model, learning path)
   - nvidia-zero-to-hero/volume-08/labs/lab-01-inventory-an-infiniband-fabric.md
     (Lab 01 — Inventory an InfiniBand Fabric, 1,244 words: ibv_devices, ibv_devinfo -v -d mlx5_0, ibstat MT4129 Rate: 400 Base lid: 12
      SM lid: 1, show_gids, lspci, numactl --hardware, iblinkinfo)
   - nvidia-zero-to-hero/volume-08/labs/lab-02-benchmark-infiniband-bandwidth-and-latency.md
     (Lab 02 — Benchmark InfiniBand Bandwidth and Latency, 1,072 words: numactl --cpunodebind --membind, ib_write_lat -a,
      ib_write_bw --report_gbits, bidirectional tests, and counter deltas)
   - nvidia-zero-to-hero/volume-08/labs/lab-03-inspect-subnet-routing-and-counters.md
     (Lab 03 — Inspect Subnet Routing and Counters, 1,088 words: iblinkinfo, ibstat, ibroute, ibqueryerrors before/after deltas)
   - nvidia-zero-to-hero/volume-08/labs/lab-04-troubleshoot-an-infiniband-path.md
     (Lab 04 — Troubleshoot an InfiniBand Path, 1,368 words: 7-step bottom-up decision tree and reversible remote-NUMA fault injection)
   - volume-06/01-ai-networking-rdma-masterclass.md / volume-06/01-rocev2-and-infiniband-architecture.md
     (AI Networking & RDMA Masterclass: Ethernet, InfiniBand, and RoCEv2, 3,225 words: straggler amplification, 6-step TCP/IP vs RDMA
      QP/WR/MR/CQ, IB LRH 8B/GRH 40B/BTH 12B/ICRC 4B/VCRC 2B vs RoCEv2 UDP 4791, ibstat MT4123 20.31.1014 Rate: 200 (HDR) Base lid: 32
      SM lid: 1 vs mlx5_1 Rate: 400 Base lid: 0, ib_write_bw 65536 B 5000 iters TX depth: 128 23500.2 MB/sec peak / 23450.5 MB/sec average /
      0.375208 Mpps, Onyx traffic-class 3 ecn minimum-absolute 150 maximum-absolute 1500, 50ms PFC Watchdog, tcpdump/ibdump 0x81, ibdiagnet -c 1000)
   - nvidia-zero-to-hero/volume-07/chapter-04-dma-rdma-and-peer-to-peer.md
     (Chapter 4 — DMA, RDMA, and Peer-to-Peer: 7-step TCP/IP penalty vs DMA and RDMA kernel bypass, 100-node Ray cluster 100GbE ConnectX-5
      scenario capped at 30 Gbps with 100% kernel CPU until switched to RoCEv2 RDMA)
   - nvidia-zero-to-hero/volume-09/chapter-03-rocev2-and-rdma-over-ethernet.md
     (Chapter 03 — RoCEv2 and RDMA over Ethernet: Figure 9.3.1 CQE triage, show_gids index 0..3 eth0 vs eth0.100,
      ib_write_bw -d mlx5_0 -x 2 Failed to modify QP to RTR, and mlnx_perf rx_prio3_congestion_events: 118 at 4.12 Gb/s RX / 3.98 Gb/s TX
      and 482991823104 bytes on 10.20.4.15)

2. Book Sources from the Local TOON-RAG Corpus (read in full):
   - Rajeshunga, AI Data Center Network Design and Technologies (ai-data-center-network-design-and-technologies), Ch 1 & Ch 7:
     Ch 1: JCT (100 threads with 99 < 100 ms and 1 delayed 1s; serial 1s + n x 1ms = 1.010s for n = 10 vs parallel 1s waiting 999ms),
     5 node RDMA layers, IB vs RoCEv1 vs RoCEv2 stacks (UDP dst port 4791, BTH, ICRC, FCS), 13-step RDMA Write CM exchange (Fig 1-12),
     11-step RDMA Read CM exchange (20.0.0.2 and 60.0.0.2, Fig 1-13), Wireshark decodes for RC RDMA READ Request (opcode 12, P_Key 65535,
     Dest QP 0x000fe1, PSN 16548361, RETH VA 0x00007ff9de5f4000, rkey 0x00207100, DMA Length 65536, ICRC 0xb87e1cbc, Fig 1-14),
     RC RDMA READ Response Middle (opcode 14, Dest QP 0x00007b, PSN 16543980, 1024 B data, ICRC 0x5b522360, Fig 1-15), and RC Acknowledge
     (opcode 17, Dest QP 0x000123, PSN 2592248, AETH Syndrome 0 Ack, MSN 1, ICRC 0x33e6e2af, Fig 1-16).
     Ch 7: Six Clos congestion points, ECN 2-bit table (00, 01, 10, 11) and CNP (BTH opcode 129 = 10000001 / 0x81), PFC (EtherType 0x8808,
     opcode 0x0101, MAC 01:80:c2:00:00:01, class enable vector 0x0008 C3, pause timer 65535 us XOFF vs 0 us XON, PFC watchdog),
     DCQCN (XON < ECN < XOFF), Source Flow Control (SFC, 802.1Qdw), and Congestion Signaling (CSIG, draft-ravi-ippm-csig-01).
   - Sergey Zhumatiy, Supercomputers for Linux SysAdmins (supercomputers-for-linux-sysadmins-managing-modern-hpc-clusters-and-supercomputers-from-software-to), Ch 5 & Ch 24:
     Ch 5: IB link generations (SDR 2.5G/8G 8b/10b, DDR 5G/16G, QDR 10G/32G, FDR 14.0625G/54.4G 64b/66b, HDR 53.125G/200G 4x / 600G 12x,
     NDR 106.25G/400G 4x / 1200G 12x 256b/257b, XDR 200G/800G 4x / 2400G 12x, GDR 400G/1600G 4x / 4800G 12x, Table 5-1), subnet limit
     2^15 + 2^14 - 1 = 49,151, 64-bit GUID, 16-bit LID (1..0xBFFF, 0xC000..0xFFFE, 0xFFFF) and LMC (2^LMC), 128-bit GID (0xFE80::/64,
     0xFEC0::/64, 0xFF00::/8), directed-route SMP, OpenSM/UFM/SHARP, IPoIB (ib0, 20-byte address), OFED tools (ibstat MT4113 fw 10.12.1100
     Rate: 56 Base lid: 913/1361 SM lid: 43/698, mlxlink BER 15E-255 850 nm VCSEL 38 C 3255.2 mV 6.750 mA, smpquery/saquery 914 n51001 HCA-1
     0x1011 0x2C9). Ch 24: /etc/security/limits.conf * soft/hard memlock unlimited.
   - NVIDIA Base Command Manager 11 Installation Manual (bcm11-install, Ch 10) & Administrator Manual (bcm11-admin, §3.6, §5.3.3, §9.6):
     DOCA OFED versions 2.9.4 and 3.2.2, cm-doca-ofed-install.sh, ibstat MT4123 20.31.2006, cmsh mlxconfig MCX653105A-HDA_Ax_Bx 0000:03:00.0,
     MLX_link_type_p1 ETH, MLX_num_vfs 16, ibnet 10.149.0.0/16 (4k datagram vs 64k connected mode), IMB-MPI1 PingPong (0.78 us at 0 B,
     1.08 us at 1..8 B), and doca_ofed_2.9.1-2 through 3.0.0.
```

### Explicitly labelled inferences
- The MTT page-count and byte-size comparisons and the InfiniBand transport frame byte totals are exact arithmetic derivations. The 128-node by 8-GPU full-mesh RC Queue Pair totals and the `ib_write_bw` HDR line-rate utilization percentage are likewise verified by `code/part12/rdma_fundamentals_lab.py`.

### Run here
- `python3 code/part12/rdma_fundamentals_lab.py` passes all 25 checks with 0 failures.

### Not verified on live hardware
- All InfiniBand, RoCEv2, and BCM commands in this chapter (`IBTA` Verbs, `TCA` Target Channel Adapters, `VLs`, `RQs`, `CNPs`, `DAC` vs `AOC` cables, `AllReduce`, `AllGather`, `ReduceScatter`, `NVSHMEM`, `DEVX`, `rdma-core` / `mlnx-ofed`, `ib_umad`, `ib_mad`, `ib_sa`, `ib_cm`, `rdma_ucm`, `get_user_pages` / `pin_user_pages` `IOVA` and `uint64_t` virtual addresses vs `Use-After-Deregister`, `sk_buff` and `IRQs` vs `p99` polling, `IBV_EVENT_CQ_ERR` and `ibv_wc.status`, `vendor_id_hex`, `total_ranks`, `rc_qps_per_rank`, `rc_qps_per_node`, `total_cluster_rc_qps`, `securityContext`, `/var/log/cm-doca-ofed.log`, `UBUNTU2404-dist-extrapackages.xml` on Ubuntu `2404`, `156` Gbps / `2025` examples) are marked `(untested here)`.

### Not in the corpus
- Low-level C code for `mlx5dv_*` Direct Verbs provider-specific hardware doorbell programming is outside the scope of the corpus. This chapter focuses on the standard `libibverbs` architecture, queue state machine, memory registration, and wire packet formats.

### Corrections to the author's notes
- In *AI Data Center Network Design and Technologies* Chapter 1 Table 1-2, InfiniBand HDR is expanded as Hundred Gigabit Data Rate and InfiniBand is described as slower than Ethernet. As shown in *Supercomputers for Linux SysAdmins* Chapter 5 Table 5-1, HDR is 200 Gbps across 4 lanes, NDR is 400 Gbps, XDR is 800 Gbps, and GDR is 1,600 Gbps. InfiniBand therefore matches Ethernet link speeds per generation while delivering lower switch and NIC latency.
