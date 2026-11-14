---
id: "c19-08"
title: "19.8 Capstone: MIG multi-tenancy"
sidebar_label: "19.8 Capstone: MIG multi-tenancy"
sidebar_position: 8
description: "Capstone for sharing GPUs between tenants with Multi-Instance GPU: when MIG beats time-slicing and whole GPUs, a tested partition planner for a tenant mix, mig-parted and GPU Operator configuration, Kueue quotas per slice, cost per slice, failure and fragmentation modes, what MIG isolates, and per-instance DCGM monitoring. Every manifest is validated and the cost arithmetic is tested. Nothing was run on a GPU."
status: "drafted"
tier: "2"
level: "A"
lab_venue: "GCP / GKE"
---

# 19.8 Capstone: MIG multi-tenancy

| Field | Value |
|---|---|
| Level | Advanced |
| Priority tier | 2 |
| Lab venue | GCP / GKE for the cloud notes, GPU Operator for the manifests. No GPU was available while writing. |
| Part | Part 19: Capstones, design and interview readiness |
| Primary sources | NVIDIA MIG User Guide (pages last updated 2026-11-04, fetched 2026-11-10); GPU Operator "GPU Operator with MIG" and "Time-Slicing GPUs"; mig-parted v0.15.1; dcgm-exporter 4.9.0; Kueue v0.20.5; GKE multi-instance GPU page; AI Systems Performance Engineering ch. 3; Kubernetes for Generative AI Solutions ch. 10; Production Kubernetes ch. 12; Supercomputers for Linux SysAdmins ch. 15 |
| Cross-references | 11.4, 11.5, 11.8, 11.24, 11.25, 11.26, 11.29, 16.14, 17.4, 18.5, 19.1, 19.2, 19.7, 19.9 |
| Coverage file | `planning/coverage/chapters/19-08.md` |
| Claim & number ledger | `planning/ledgers/19-08.md` |

## Why this matters for AI infrastructure

It is Monday morning, and the chat team posts in the platform channel. Their new model server has been Pending for two hours. Pending is the state a pod enters when Kubernetes cannot yet place it on a node. The server is waiting for one slice of 3g.40gb, which is a fixed-size piece of a GPU. The dashboard shows twelve idle slices of 1g.10gb on the very same nodes. Nothing is broken. The platform simply holds the right amount of GPU in the wrong shapes.

That gap between free capacity and usable capacity is the whole subject of this capstone. A whole GPU is easy to schedule and easy to bill. The trouble is that a small service uses only a sliver of it, so most of the card sits idle. Splitting the GPU fixes that waste, but it creates new problems. Some shapes do not fit anywhere. Some slices sit unused because nobody needs that size. Changing the layout means draining a node first, which means emptying it of work. And the bill must now be divided by slice, not by card.

Multi-Instance GPU, called MIG here, is NVIDIA's hardware method for cutting one GPU into separate instances. Each instance gets its own slice of memory and compute, and a tenant sees only its own slice. This chapter builds a small multi-tenant platform on top of it. Along the way you choose profiles for a tenant mix, check the layout with a tested planner, load the layout with mig-parted, give each tenant a Kueue quota in slices, and price those slices. Last, you set up per-instance monitoring and learn which questions MIG answers and which it leaves open.

The machine used to write this chapter had no GPU, so no MIG command ran and no pod was scheduled. The lab says what ran here and what did not. Output shown for the steps that did not run is the expected shape from NVIDIA's documentation, not a capture from a real node.

## Prerequisites and outcomes

### Prerequisites

Each item below names the earlier chapter that teaches the idea, so you can go back if a step feels unfamiliar.

- Chapter 11.24 covers the MIG hardware model and the six-layer validation chain.
- Chapters 11.25 and 11.26 cover time-slicing, MPS and the sharing decision tree.
- Chapters 11.4 and 11.5 cover the GPU Operator, and Chapter 11.8 covers Kueue.
- Chapter 17.4 covers the DCGM exporter, and Chapter 18.5 covers the security view of GPU sharing.
- Chapter 16.14 covers the chargeback model that this chapter fills in for MIG slices.

### Outcomes

Think about the afternoon a platform team decides how to share its H100 GPUs between several teams that do not trust one another. This chapter follows that decision from start to finish. It begins with the choice between MIG, time-slicing, MPS and whole GPUs for each tenant. It then designs a MIG layout for the tenant mix and asks a tool to prove that the hardware can create it. Next comes the mig-parted configuration and the GPU Operator steps that apply it. Each tenant gets a Kueue quota counted in slices, backed by a native ResourceQuota as a second guard. The chapter prices a slice and separates idle cost from the cost lost to geometry. It ends with the failure modes of a sliced fleet and the way to watch each instance with DCGM.

---
## 1. Choosing the isolation tool

A research team asks for "a quarter of a GPU" for a notebook service. The platform engineer has four ways to say yes. The team will quietly notice which one was chosen the first time a neighbour's job slows them down. So the choice is really about what each tenant is allowed to do to the others, and how much one tenant's work can disturb another's.

NVIDIA's MIG guide compares three concurrency mechanisms in one table. Concurrency here means several pieces of work running on one GPU at the same time. CUDA streams live inside a single process and share everything in it. The Multi-Process Service, MPS, lets cooperating processes share the SMs, which are the streaming multiprocessors that do the arithmetic. It offers no error isolation, though, and the memory bandwidth, caches and capacity are still shared. MIG is a physical partition. It gives each instance its own SM slices, memory slices and engines, and it isolates errors.

Time-slicing is a fourth option, and it comes from the GPU Operator rather than from the CUDA guide. The device plugin is the component that tells Kubernetes which GPUs a node has. With time-slicing, it advertises each GPU as several replicas and hands them to different pods. The GPU Operator documentation says plainly that, unlike MIG, there is no memory or fault isolation between the replicas. The pods take turns on the same GPU, so one heavy pod can slow the others down.

It helps to think about the choice as a question of trust and fairness. If two tenants trust each other and their jobs are small, sharing a GPU loosely may be fine. If they do not trust each other, or one of them runs jobs that can crash the whole card, then the sharing has to be stronger. The four options sit along that line, from loosest to strictest. Whole GPUs sit at the strict end, because nothing is shared at all.

The table below sets the four options side by side. Read the columns as questions. Does a neighbour's work slow this tenant down? Can a neighbour read this tenant's memory? Does a neighbour's error reach this tenant? The MIG, MPS and streams rows come from the MIG guide, and the time-slicing row comes from the GPU Operator guide.

| Mechanism | Partition type | SM isolation | Memory protection and bandwidth QoS | Error isolation |
|---|---|---|---|---|
| CUDA streams | Single process | No | No | No |
| MPS | Logical, up to 48 clients | By percentage, not partitioning | Memory protection yes, bandwidth QoS no | No |
| MIG | Physical, up to 7 instances | Yes | Yes | Yes |
| Time-slicing | Replicas of one GPU | No, pods take turns | No | No |

Before you choose MIG, it is worth knowing what it gives up. Once the layout is set, the boundaries are fixed. A tenant that suddenly needs more memory cannot take it from an idle neighbour, even if that neighbour is sitting on a large, empty slice. The boundaries that protect a tenant are the same ones that trap spare capacity.

Whole GPUs have no slicing loss, no reconfiguration and no fragmentation. Those are the three costs that the rest of this chapter spends its time on. Anything that spans GPUs belongs on whole GPUs. The MIG guide lists no peer-to-peer transfers between instances on different GPUs and no CUDA IPC across GPU instances. CUDA IPC is the mechanism for sharing memory between processes on the GPU. The guide also gives only experimental NCCL support. NCCL is the library that multi-GPU training uses to talk between cards.

AI Systems Performance Engineering reaches the same conclusion from the performance side. Its chapter 3 says MIG suits multi-tenant, small-model inference, and that it is usually the wrong tool for large distributed training. It also states the price. An idle instance cannot lend its resources to another, because the partition is hard. Capacity that nobody is using stays stranded inside its slice.

The rule that follows is short. Use whole GPUs for training that spans GPUs and for tenants that fill a GPU. Use MIG for small tenants that distrust each other or need a predictable share. Use time-slicing or MPS only inside one trust domain, which means one team or one group that trusts itself. The flowchart below turns that rule into questions you can ask a tenant.

```mermaid
flowchart TD
    A["Tenant asks for GPU capacity"] --> B{"Needs more than one GPU or fast GPU to GPU traffic?"}
    B -->|"Yes"| W["Whole GPUs, no sharing"]
    B -->|"No"| C{"Can it fill a whole GPU most of the day?"}
    C -->|"Yes"| W
    C -->|"No"| D{"Tenants distrust each other or need predictable latency?"}
    D -->|"Yes"| M["MIG slice sized to the workload peak"]
    D -->|"No"| E{"One team, tolerates a noisy neighbour?"}
    E -->|"Yes"| T["Time-slicing or MPS"]
    E -->|"No"| M
```

Size the slice for the concurrent peak, not for the size of the weight file. Here is why. A model that loads in 7 GB can need much more memory once its cache fills during real traffic. A slice that fits the weights alone will fail under load.

Two combinations are documented. MPS can run on top of MIG, with a lower client limit. Time-slicing can also let several processes share one MIG partition. Both give back some of the isolation that made MIG attractive in the first place, so use them with the same care as before.

**Decision rule:** Give whole GPUs to anything that spans GPUs or fills one. Give MIG slices to small tenants that need isolation. Keep time-slicing and MPS inside a single trust domain.

**In one minute:** MIG is the only option in the table that isolates SMs, memory bandwidth and errors at once. It costs flexibility, because idle slices cannot be lent. Whole GPUs stay the answer for large jobs.

---
## 2. What NVIDIA documents about MIG profiles

A planner on the platform team writes "split every H100 into two halves" in a design document. A reviewer asks which profile that means, and nobody can say whether it is 3g.40gb or 4g.40gb. The two profiles differ in compute, and the hardware allows different combinations of each. A profile is a named recipe for one instance. The names carry the answer, so it pays to read them properly before you agree to anything.

A MIG-capable GPU is cut into two kinds of slice. A memory slice is roughly one eighth of the GPU's memory resources, including capacity and bandwidth. The MIG User Guide says so. An SM slice is roughly one seventh of the SMs when the GPU is in MIG mode. Here, SM means streaming multiprocessor, the unit that runs the arithmetic. A GPU instance combines some memory slices with some SM slices. The profile name `Ng.Mgb` reads as N SM slices and about M gigabytes of memory. So 3g.40gb is three SM slices with about 40 GB of memory.

Here is a way to read a profile name without memorising it. Take the first number before the g. That is the count of SM slices, and the SM slices are the compute. Take the number after the dot and before the gb. That is the memory in gigabytes, rounded. A 2g.20gb instance therefore has two compute slices and about 20 GB of memory, and it sits on two of the eight memory positions. Read that way, the names stop looking random, and the fractions become easy to check by hand.

A GPU instance can be divided further into compute instances. Those share the instance's memory but get their own SMs. This chapter uses one compute instance per GPU instance, which is what `-C` and mig-parted create. Keep that in mind, because the two levels are easy to confuse.

The MIG User Guide has a page called "Supported MIG Profiles", with one table per product. This chapter uses the H100 80 GB table. Its columns for hardware units and copy engines live in the data file, and the first columns are shown here. A copy engine moves data between memory regions, so it matters for slices that copy a lot.

| Profile | Fraction of memory | Fraction of SMs | Instances per GPU |
|---|---|---|---|
| 1g.10gb | 1/8 | 1/7 | 7 |
| 1g.10gb+me | 1/8 | 1/7 | 1 |
| 1g.20gb | 1/4 | 1/7 | 4 |
| 2g.20gb | 2/8 | 2/7 | 3 |
| 3g.40gb | 4/8 | 3/7 | 2 |
| 4g.40gb | 4/8 | 4/7 | 1 |
| 7g.80gb | Full | 7/7 | 1 |

The profile names follow the memory, so they change from one product to the next. The MIG User Guide says the A100 80 GB names are 1g.10gb, 1g.20gb, 2g.20gb, 3g.40gb, 4g.40gb and 7g.80gb, which are the same names as the H100. The 40 GB A100 uses 1g.5gb, 1g.10gb, 2g.10gb, 3g.20gb, 4g.20gb and 7g.40gb. The H200 uses 1g.18gb, 1g.35gb, 2g.35gb, 3g.71gb, 4g.71gb and 7g.141gb. The B200 uses 1g.23gb, 1g.45gb, 2g.45gb, 3g.90gb, 4g.90gb and 7g.180gb. All of them share the same fractions. A layout designed in slices therefore carries across products, even though the gigabyte labels change. Designing in slices is the habit to build.

The `+me` profile adds media engines, which handle video encoding and decoding, and only one such 1g instance fits per GPU. The A30, the RTX PRO cards and the Thor iGPU have four or two slices, so the planner refuses them. A planner that refuses a GPU it does not know is safer than one that guesses.

The MIG User Guide gives SM counts only for the A100 40 GB listing: 14 for a 1g slice, 42 for 3g, 56 for 4g and 98 for 7g. The GPU Operator guide prints H100 labels of 16, 32 and 60 multiprocessors for 1g.10gb, 2g.20gb and 3g.40gb. Those labels come from a configuration example, not from a table of hardware. This chapter does not extrapolate SM counts to other GPUs, because the MIG User Guide does not publish them for those GPUs.

The MIG User Guide lists minimum drivers: R450 for the A100, R525 for the H100, R550 for the H200 and R570 for the B200. A driver is the kernel module that lets the operating system talk to the GPU, and the minimum is the oldest one that supports the card. From Hopper on, which means the H100 and newer, enabling MIG mode needs no GPU reset. The mode does not persist across a driver reload, though. Created instances never survive a reboot, so MIG Manager or mig-parted must recreate them each time the node starts.

The table is long, and it is easy to misread one row. A useful habit is to check a row against the fractions before you copy it. If a profile shows more SM slices than its name implies, or more memory than its fraction allows, stop and look at the source page again. That check takes a minute and prevents a layout built on a typo.

The full table lives in data, not in prose. The file `code/part19/c08_mig_profiles.json` holds all 99 rows from 14 tables, with the source page and dates, and a test counts them. Two oddities are kept as printed, because changing them would hide a question. The H100 1g.20gb row shows memory 1/4 but L2 1/8. Copy engines are 7 for the A100 7g.40gb and 8 for the H100 7g.80gb. L2 is the GPU's shared second-level cache.

**Decision rule:** Design layouts in slices of one eighth memory and one seventh SM, then translate them to profile names for each product. Take every number from the MIG User Guide's table for that exact GPU.

**In one minute:** A profile name is a pair of slice counts plus a rounded memory size. The slice fractions are the same on every seven-slice GPU, and the names change with memory. The data file holds the whole NVIDIA table.

---
## 3. Designing a layout for a tenant mix

The chat team needs four copies of a model with a peak of about 30 GB. Search needs ten small embedding servers. Notebooks need six medium slices, fine-tuning needs two large ones, and a nightly batch job wants a whole GPU. An engineer adds up the slices, counts 49 of the 56 available on an eight-GPU node, and declares that the plan fits. It does not. The reason is geometry, which means where each slice is allowed to sit on the chip, not how many slices there are.

Imagine you are placing furniture in a narrow room, where a wide sofa can only go against certain walls. Each profile has its own walls. Some are flexible, such as the 1g profile, which can start in many places. Others are rigid, such as the 4g profile, which has only one wall. The planner's job is to fit every piece of furniture without leaving a gap that nothing can use.

A GPU instance cannot start just anywhere. Think of the memory slices as a row of numbered seats, and of each profile as a group that must sit in certain seats. The MIG User Guide shows the legal start positions with `nvidia-smi mig -lgipp` for the A100 40 GB. A start position is counted in memory slices from 0 to 7. The 1g.5gb profile can start at any of positions 0 to 6. The 1g.10gb profile can start at 0, 2, 4 or 6. The 2g.10gb profile can start at 0, 2 or 4. The 3g.20gb profile can start at 0 or 4. The 4g.20gb profile can start only at 0, and the 7g.40gb profile can start only at 0.

Three consequences follow from those positions. Each one explains a failure that surprises new operators, so they are worth reading slowly.

1. Why can a second 4g request fail with memory free? Only one 4g instance fits on a GPU, because it can start only at 0. A second 4g request is refused even if memory is free.
2. What strands an SM slice in a two-3g layout? Two 3g instances fill all eight memory slices, so nothing else fits beside them. They use 6 of the 7 SM slices, so one SM slice is stranded.
3. Why do seven 1g instances give only 70 GB? Seven 1g instances use all seven SM slices but only seven of the eight memory slices. One memory slice is stranded, which is why seven 1g.10gb slices give 70 GB of an 80 GB card.

Creation order matters too. The MIG User Guide shows that asking for 3g.20gb last fails with "Insufficient Resources", while asking for it first succeeds. The planner therefore prints the largest profile first. mig-parted retries orderings on its own, so you rarely need to fix the order by hand.

Does the same table hold for the H100 and later GPUs? That is the honest question to ask. The MIG User Guide prints the listing only for the A100 40 GB, and it draws the other products as figures. The planner reuses the A100 positions for every seven-slice GPU. A test checks that choice against the H100 figure of 19 valid configurations. Every row of the figure is feasible under the planner, and every maximal mix the planner finds appears in the figure. Still, this is an inference and not a published fact. Confirm the positions with `nvidia-smi mig -lgipp` on the real GPU before you rely on them.

Here is what the planner does, in plain steps. It takes the largest request first, because a large instance is the hardest to place. It looks for a GPU where that instance can start at a legal position. If it finds one, it places the instance and moves on to the next request. If none of the GPUs has room, it reports the request as unplaced, so the platform team sees a shortfall instead of a silent failure. The exact search over start positions is what keeps the planner honest. A simpler rule that only counted slices would say the layout fits when it does not.

The planner packs the largest profiles first. For each instance, it tries the first GPU where an exact search over start positions still succeeds. Anything that fits nowhere gets reported rather than silently dropped. Here is the tenant mix from the story, on H100 80 GB, produced by `python3 code/part19/c08_mig_planner.py`.

| Tenant | Profile | Instances | SM slices |
|---|---|---|---|
| search-embeddings | 1g.10gb | 10 | 10 |
| chat-llm | 3g.40gb | 4 | 12 |
| notebooks | 2g.20gb | 6 | 12 |
| finetune | 4g.40gb | 2 | 8 |
| batch-eval | 7g.80gb | 1 | 7 |

The SM slices sum to 49, which would be 7 GPUs with perfect packing. The memory slices sum to 54, which is also 7 GPUs. The planner needs 8, though, and with 7 one search instance has no home. The nvidia-devops capstone says a layout is valid when the slices sum to at most 7 and the memory fits. The planner shows that this rule is necessary and not sufficient. Passing it does not prove that the layout can be built.

The planner uses a first-fit-decreasing heuristic. That is a simple rule that places the biggest items first and takes the first place that fits. It found 8 GPUs, and the lower bound is 7. This chapter does not prove that 8 is the best possible answer.

```mermaid
flowchart LR
    G0["GPU 0: 7g.80gb"] --> T5["batch-eval"]
    G1["GPU 1 and 2: 4g.40gb + 3g.40gb"] --> T4["finetune"]
    G1 --> T2["chat-llm"]
    G3["GPU 3: 3g.40gb x2"] --> T2
    G4["GPU 4 and 5: 2g.20gb x3 + 1g.10gb"] --> T3["notebooks"]
    G4 --> T1["search-embeddings"]
    G6["GPU 6 and 7: 1g.10gb x7"] --> T1
    G6 --> S["spare, held by the platform"]
```

Read the table below as the view from the node. It lists how each GPU is cut and what each one offers.

| GPUs | Layout | Slices offered | Stranded on each GPU |
|---|---|---|---|
| 0 | 7g.80gb | 1 whole GPU | none |
| 1 and 2 | 4g.40gb + 3g.40gb | 2 of 4g, 2 of 3g | none |
| 3 | 3g.40gb x 2 | 2 of 3g | 1 SM slice |
| 4 and 5 | 2g.20gb x 3 + 1g.10gb | 6 of 2g, 2 of 1g | 1 memory slice |
| 6 and 7 | 1g.10gb x 7 | 14 of 1g | 1 memory slice |

The totals offered by the node are one 7g.80gb, two 4g.40gb, four 3g.40gb, six 2g.20gb and sixteen 1g.10gb. Search needs ten of the sixteen small slices. The other six are headroom. The Kueue design in section 5 holds them in a shared queue, so any tenant that needs them can borrow them.

The planner can also write the same layout as a mig-parted config. It does this with the function `mig_parted_yaml`. A test compares the output with the checked-in file, and the upstream parser of mig-parted v0.15.1 accepts it. The format follows the GPU Operator guide. The `all-disabled` entry lets a node return to whole GPUs with one label change, which is useful when you need the node back for training.

```yaml
version: v1
mig-configs:
  all-disabled:
    - devices: all
      mig-enabled: false

  tenant-mix-v1:
    - devices: [0]
      mig-enabled: true
      mig-devices:
        "7g.80gb": 1
    - devices: [1,2]
      mig-enabled: true
      mig-devices:
        "3g.40gb": 1
        "4g.40gb": 1
    - devices: [3]
      mig-enabled: true
      mig-devices:
        "3g.40gb": 2
    - devices: [4,5]
      mig-enabled: true
      mig-devices:
        "2g.20gb": 3
        "1g.10gb": 1
    - devices: [6,7]
      mig-enabled: true
      mig-devices:
        "1g.10gb": 7
```

In the GPU Operator, the same text lives inside a ConfigMap. A ConfigMap is a Kubernetes object that holds plain configuration text. NVIDIA says the key must be named `config.yaml`. A test checks that the ConfigMap's text equals the standalone file, so the two copies cannot drift apart.

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: c08-custom-mig-config
  namespace: gpu-operator
data:
  config.yaml: |
    version: v1
    mig-configs:
      all-disabled:
        - devices: all
          mig-enabled: false

      tenant-mix-v1:
        - devices: [0]
          mig-enabled: true
          mig-devices:
            "7g.80gb": 1
        - devices: [1,2]
          mig-enabled: true
          mig-devices:
            "3g.40gb": 1
            "4g.40gb": 1
        - devices: [3]
          mig-enabled: true
          mig-devices:
            "3g.40gb": 2
        - devices: [4,5]
          mig-enabled: true
          mig-devices:
            "2g.20gb": 3
            "1g.10gb": 1
        - devices: [6,7]
          mig-enabled: true
          mig-devices:
            "1g.10gb": 7
```

From GPU Operator v26.3.0, MIG Manager can also generate per-node configs by itself, such as `all-1g.10gb` and `all-balanced`. Custom entries are for layouts like this one.

The node advertises its MIG devices differently depending on the strategy. A strategy is the rule for naming the resources. With `single`, every MIG device appears as `nvidia.com/gpu`, and all GPUs must use MIG with one profile. Otherwise GPU Feature Discovery labels the product `-MIG-INVALID`. With `mixed`, each profile is its own resource, and this five-profile node needs it.

GKE does this differently. It partitions per node pool, using `gpu-partition-size`, so every GPU in one pool gets the same size. Nodes carry the label `cloud.google.com/gke-gpu-partition-size`. A node pool is a group of nodes with the same settings, and GKE manages them as one unit. GKE's H100 80 GB list omits 4g.40gb, so this layout cannot be built there as written. GKE also says that splitting H100 and newer GPUs rules out GPUDirect, which is NVIDIA's direct path for moving data between GPUs and other devices. GKE says the feature is not recommended for untrusted workloads.

**Decision rule:** Plan layouts with a tool that knows start positions. Keep one or two layouts per node pool, and confirm the placements with `nvidia-smi mig -lgipp` on the real hardware.

**In one minute:** Slice arithmetic gives a lower bound, and geometry adds loss. The tenant mix needs 8 H100s, one more than the SM slices suggest. The mig-parted config is generated from the plan and parsed by the upstream code.

---
## 4. Running the layout: reconfiguration, pending pods and fragmentation

On Thursday the platform team relabels node 3 from "balanced" to "all-3g.40gb" for a new tenant. The label change looks like a small edit. MIG Manager starts, and the pods on the node stop. The batch team's run dies at hour nine. The change itself was correct. The damage came from treating a layout change as a label edit, when it is really a maintenance task.

Applying a layout is disruptive, and you should plan for that before you start. The GPU Operator guide says MIG Manager sets `nvidia.com/mig.config.state`, terminates all GPU pods on the node, and moves the state from `pending` to `success`. With the reboot option, the state can go to `rebooting` instead. A daemon that holds a driver handle can also block enabling MIG, with the message "In use by another client". DCGM and NVSM are examples of such daemons. The MIG User Guide's remedy is to stop that daemon first. The BCM administration manual adds one more rule: only one MIG management tool may configure a node at a time. That tool can be BCM, the DGX service or the GPU Operator's MIG Manager, but never two of them at once.

A sliced fleet has six common failure modes, and they are worth knowing before the first page arrives. The table lists the symptom you see, the likely cause and the first check to run.

| Symptom | Cause | First check |
|---|---|---|
| Pod Pending, node has free slices of another profile | Slice shape mismatch, the free slices are the wrong size | Compare `kubectl describe node` allocatable for each `nvidia.com/mig-*` resource with the request |
| Pod Pending, no `nvidia.com/mig-*` resource on the node | Strategy is `single`, or the layout is still `pending` | Read `nvidia.com/mig.strategy` and `nvidia.com/mig.config.state` labels |
| Node product label ends in `-MIG-INVALID` | Single strategy with mixed profiles or GPUs without MIG | Check that every GPU has the same profile, or switch to `mixed` |
| Free memory but a large profile will not start | Running instances sit at starts that block it | `nvidia-smi mig -lgi` shows each instance's start and size |
| Layout lost after reboot | MIG devices are not persistent, and on Hopper the mode is not either | Confirm MIG Manager reapplied the config and the state label is `success` |
| Workload admitted by Kueue but Pending in the scheduler | Quota is larger than what the node really offers | Compare ClusterQueue quota with node allocatable |

Consider what a reconfiguration looks like from the tenants' side. A notebook user sees a session drop. A batch job that was halfway through a run is killed, and its checkpoint, if it has one, is the only thing left. A chat service may lose a replica and need time to recover. None of these is a bug in MIG. They are the cost of changing the shape of a shared machine. The job of the platform is to plan that cost, announce it, and schedule it at a quiet time.

Stranded slices come in two kinds, and the difference matters. The first kind is built into the layout. Two 3g profiles always strand one SM slice, and seven 1g profiles always strand one memory slice. You can see that coming on paper. The second kind comes from history. The MIG User Guide says that fragmentation occurs as instances are created and destroyed over time. A node that looks fine on its first day can get stuck later.

The planner shows the second kind with instances that cannot move. Suppose two 1g.10gb instances sit at starts 0 and 4. Six memory slices are free, but a 4g.40gb needs start 0, and a 3g.40gb needs 0 or 4. Both are blocked. Only a 2g.20gb still starts, so fragmentation is 0.667 in this example. A planner that may move the existing instances finds room for the 3g.40gb. That gap is the difference between a layout on paper and a live node, and the tests cover both cases.

One process sees only a little of the picture. CUDA lists one compute instance per GPU instance, and it lists at most 64 MIG instances across all GPUs. So a script that expects eight MIG devices may not get them, even when the node has them. The same sort of surprise applies to pods. A pod that needs two slices stays Pending if no single node supplies both of them.

Think of a reconfiguration window as a short maintenance shift. Before it starts, you reduce the work that can arrive. During it, the node is empty of GPU pods and the layout changes. After it, you check the result and reopen the quota. The order matters, because the quota must never promise more slices than the node currently offers. That is the reason the procedure moves the quota first and the layout second.

A reconfiguration window needs a written procedure. The steps below are derived from the documented behaviour. NVIDIA does not publish them as a procedure, so treat them as a draft to adapt to your site.

1. Cordon the node, which means marking it so that no new pods land there, and let its Kueue workloads finish or be preempted.
2. Lower the ClusterQueue quotas for the affected profiles, so Kueue stops admitting work to slices that are about to disappear.
3. Label the node with the new `nvidia.com/mig.config` value, and wait for the state to read `success`.
4. Check the allocatable counts with `kubectl`, restore the quotas to match them, and uncordon the node.

**Decision rule:** Treat every layout change as a drained-node maintenance task. Move the quota first and the layout second, and keep the number of live layouts small.

**In one minute:** Applying a MIG config stops the GPU pods on the node, and monitoring agents can block it. Slices are lost in two ways. One is the layout, which is fixed by design. The other is history, which is fixed by discipline. Most Pending pods trace back to shape, strategy or quota disagreeing with the node.

---
## 5. Quotas and chargeback per slice

At quarter end, the finance partner asks which team used how much GPU. Two teams with the same pod count have very different invoices, and nobody can explain why. The platform has pod counts, but no way to price a 1g slice against a 3g slice. A slice becomes money only after someone defines a price for it. This section covers the quota side first, then the price.

To see why the price matters, imagine two tenants that each run a model for the same number of hours. One uses a 1g.10gb slice and the other uses a 3g.40gb slice. A pod count says they are equal, and an invoice based on pods charges them the same. Yet one has taken far more of the card. A price per slice, built from the share of the card each slice takes, makes the invoice match the use.

Quotas come first. Kueue counts extended resources, which are custom resources such as a MIG slice, the same way it counts CPU and memory. A ClusterQueue sets `nominalQuota`, `borrowingLimit` and `lendingLimit` for each resource and each ResourceFlavor. A ResourceFlavor describes a kind of node, and it maps to nodes through `nodeLabels`. The label `nvidia.com/mig.config` is a good key, because it names the layout that the node has.

The Kueue source refuses a pod that requests a resource the ClusterQueue does not cover. The reason it gives is "resource unavailable in ClusterQueue". A tenant queue must therefore list `cpu` and `memory` as well as its MIG resource, or the pod is refused. Listing only one MIG resource also pins a tenant to that profile. That may be exactly what you want, or it may not.

The design has one ClusterQueue per tenant, plus one more queue that holds the six spare 1g.10gb slices. All of them sit in one cohort, which is a group of queues that can lend to each other. Each tenant holds its own profile and lends nothing. The spare queue lends its slices, and search may borrow up to six of them. The loan covers only the spare slices, so no tenant's reserved slices can be taken.

A CRD, or custom resource definition, is the schema that tells Kubernetes which fields an object may have. The file is checked against the Kueue v0.20.5 CRDs with `check_crd_yaml.py`, and the checker rejects unknown fields. The current API is `v1beta2`. In that API the cohort field is `cohortName`. The checker also rejects the older field names `flavorQuotas` and `cohort`, so a file copied from an old example fails before it reaches the cluster.

```yaml
# Kueue objects for the MIG tenant mix (Chapter 19.8).
# Validated against the Kueue v0.20.5 CRDs (kueue.x-k8s.io/v1beta2) by tools/check_crd_yaml.py.
# cpu and memory quotas are placeholders: size them from your node pool.
apiVersion: kueue.x-k8s.io/v1beta2
kind: ResourceFlavor
metadata:
  name: h100-mig-tenant-mix
spec:
  nodeLabels:
    nvidia.com/mig.config: tenant-mix-v1
---
apiVersion: kueue.x-k8s.io/v1beta2
kind: ClusterQueue
metadata:
  name: cq-search
spec:
  cohortName: gpu-mig-pool
  namespaceSelector:
    matchLabels:
      kubernetes.io/metadata.name: team-search
  resourceGroups:
    - coveredResources: ["cpu", "memory", "nvidia.com/mig-1g.10gb"]
      flavors:
        - name: h100-mig-tenant-mix
          resources:
            - name: cpu
              nominalQuota: 32
            - name: memory
              nominalQuota: 128Gi
            - name: nvidia.com/mig-1g.10gb
              nominalQuota: 10
              borrowingLimit: 6
---
apiVersion: kueue.x-k8s.io/v1beta2
kind: ClusterQueue
metadata:
  name: cq-chat
spec:
  cohortName: gpu-mig-pool
  namespaceSelector:
    matchLabels:
      kubernetes.io/metadata.name: team-chat
  resourceGroups:
    - coveredResources: ["cpu", "memory", "nvidia.com/mig-3g.40gb"]
      flavors:
        - name: h100-mig-tenant-mix
          resources:
            - name: cpu
              nominalQuota: 64
            - name: memory
              nominalQuota: 256Gi
            - name: nvidia.com/mig-3g.40gb
              nominalQuota: 4
---
apiVersion: kueue.x-k8s.io/v1beta2
kind: ClusterQueue
metadata:
  name: cq-notebooks
spec:
  cohortName: gpu-mig-pool
  namespaceSelector:
    matchLabels:
      kubernetes.io/metadata.name: team-notebooks
  resourceGroups:
    - coveredResources: ["cpu", "memory", "nvidia.com/mig-2g.20gb"]
      flavors:
        - name: h100-mig-tenant-mix
          resources:
            - name: cpu
              nominalQuota: 48
            - name: memory
              nominalQuota: 192Gi
            - name: nvidia.com/mig-2g.20gb
              nominalQuota: 6
---
apiVersion: kueue.x-k8s.io/v1beta2
kind: ClusterQueue
metadata:
  name: cq-finetune
spec:
  cohortName: gpu-mig-pool
  namespaceSelector:
    matchLabels:
      kubernetes.io/metadata.name: team-finetune
  resourceGroups:
    - coveredResources: ["cpu", "memory", "nvidia.com/mig-4g.40gb"]
      flavors:
        - name: h100-mig-tenant-mix
          resources:
            - name: cpu
              nominalQuota: 64
            - name: memory
              nominalQuota: 256Gi
            - name: nvidia.com/mig-4g.40gb
              nominalQuota: 2
---
apiVersion: kueue.x-k8s.io/v1beta2
kind: ClusterQueue
metadata:
  name: cq-batch
spec:
  cohortName: gpu-mig-pool
  namespaceSelector:
    matchLabels:
      kubernetes.io/metadata.name: team-batch
  resourceGroups:
    - coveredResources: ["cpu", "memory", "nvidia.com/mig-7g.80gb"]
      flavors:
        - name: h100-mig-tenant-mix
          resources:
            - name: cpu
              nominalQuota: 32
            - name: memory
              nominalQuota: 128Gi
            - name: nvidia.com/mig-7g.80gb
              nominalQuota: 1
---
# Holds the spare 1g.10gb slices and lends them to the cohort. No workload uses it directly.
apiVersion: kueue.x-k8s.io/v1beta2
kind: ClusterQueue
metadata:
  name: cq-platform-spare
spec:
  cohortName: gpu-mig-pool
  namespaceSelector:
    matchLabels:
      kubernetes.io/metadata.name: gpu-platform
  resourceGroups:
    - coveredResources: ["nvidia.com/mig-1g.10gb"]
      flavors:
        - name: h100-mig-tenant-mix
          resources:
            - name: nvidia.com/mig-1g.10gb
              nominalQuota: 6
              lendingLimit: 6
---
apiVersion: kueue.x-k8s.io/v1beta2
kind: LocalQueue
metadata:
  name: main
  namespace: team-search
spec:
  clusterQueue: cq-search
---
apiVersion: kueue.x-k8s.io/v1beta2
kind: LocalQueue
metadata:
  name: main
  namespace: team-chat
spec:
  clusterQueue: cq-chat
---
apiVersion: kueue.x-k8s.io/v1beta2
kind: LocalQueue
metadata:
  name: main
  namespace: team-notebooks
spec:
  clusterQueue: cq-notebooks
---
apiVersion: kueue.x-k8s.io/v1beta2
kind: LocalQueue
metadata:
  name: main
  namespace: team-finetune
spec:
  clusterQueue: cq-finetune
---
apiVersion: kueue.x-k8s.io/v1beta2
kind: LocalQueue
metadata:
  name: main
  namespace: team-batch
spec:
  clusterQueue: cq-batch
```

A native ResourceQuota is a second fence. The API server enforces it at pod creation, and it is a separate check that does not depend on Kueue. Kubernetes accepts only the `requests.` prefix for extended resources, so the quota names must start that way. The file gives each namespace its ClusterQueue count, plus the six borrowable slices for search. A test checks that the two agree.

```yaml
# Namespaces and native ResourceQuota guard for the MIG tenants (Chapter 19.8).
# Extended resources accept only the requests. prefix in a ResourceQuota.
---
apiVersion: v1
kind: Namespace
metadata:
  name: team-search
  labels:
    c08/tenant: search
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: mig-slices
  namespace: team-search
spec:
  hard:
    requests.nvidia.com/mig-1g.10gb: "16"
---
apiVersion: v1
kind: Namespace
metadata:
  name: team-chat
  labels:
    c08/tenant: chat
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: mig-slices
  namespace: team-chat
spec:
  hard:
    requests.nvidia.com/mig-3g.40gb: "4"
---
apiVersion: v1
kind: Namespace
metadata:
  name: team-notebooks
  labels:
    c08/tenant: notebooks
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: mig-slices
  namespace: team-notebooks
spec:
  hard:
    requests.nvidia.com/mig-2g.20gb: "6"
---
apiVersion: v1
kind: Namespace
metadata:
  name: team-finetune
  labels:
    c08/tenant: finetune
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: mig-slices
  namespace: team-finetune
spec:
  hard:
    requests.nvidia.com/mig-4g.40gb: "2"
---
apiVersion: v1
kind: Namespace
metadata:
  name: team-batch
  labels:
    c08/tenant: batch
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: mig-slices
  namespace: team-batch
spec:
  hard:
    requests.nvidia.com/mig-7g.80gb: "1"
---
apiVersion: v1
kind: Namespace
metadata:
  name: gpu-platform
```

A workload asks for a slice by name, and a queue label hands admission to Kueue. The Job below asks for one 3g.40gb slice for the chat tenant. The pod asks for the slice in its limits, and Kueue decides when it may start.

```yaml
# A Kueue-managed Job that asks for one 3g.40gb slice (Chapter 19.8).
# The queue label hands admission to Kueue. The image is the vectorAdd sample used in NVIDIA's GPU Operator MIG guide.
apiVersion: batch/v1
kind: Job
metadata:
  name: chat-llm-smoke
  namespace: team-chat
  labels:
    kueue.x-k8s.io/queue-name: main
spec:
  parallelism: 1
  completions: 1
  backoffLimit: 0
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: vectoradd
          image: nvidia/samples:vectoradd-cuda11.2.1
          resources:
            requests:
              cpu: "2"
              memory: 4Gi
            limits:
              nvidia.com/mig-3g.40gb: 1
```

Pricing is also a policy decision. The arithmetic is simple once the weights are set, but the weights reflect what the platform wants to encourage. A team that values small slices can lower their weight. A team that wants to discourage fragmentation can raise the price of awkward shapes. The chapter keeps the rule simple on purpose, so that the discussion about policy stays visible.

Now the price. The pricing rule has to be additive, so that the shares of one GPU never add up to more than that GPU. This is a design choice of this chapter, not an NVIDIA rule. A slice's weight is the average of its memory share and its SM share. A 7g.80gb slice weighs 1. A 3g.40gb slice weighs 0.4643, and a 4g.40gb slice weighs 0.5357. Those two together make one GPU.

Memory alone would charge a 3g.40gb and a 4g.40gb the same amount, although the 4g tenant gets a third more SMs. SM alone would undercharge the 1g.20gb slice, which holds a larger share of memory than its compute suggests. Teams with strong views can change one function, and the invariant test will still check the additive rule.

Each GPU's cost then splits three ways, and the split is the heart of the chargeback. Tenants pay for the slices they reserve. Idle cost is the price of slices that nobody holds. Layout loss is the share that no profile can use, such as the SM slice left beside two 3g instances. The three parts add up to the node cost, and a test checks that they do.

The worked example uses a placeholder price of 4.00 USD per GPU-hour. The price is illustrative, not a quote, and the calculation runs over 730 hours in a month. At that price, the 8-GPU node costs 23,360 USD per month. The values come from `python3 code/part19/c08_finops.py`, so you can change the price and watch the table move.

| Line | Monthly cost in USD | How it arises |
|---|---|---|
| search-embeddings | 3,910.71 | 10 slices of 1g.10gb at 0.536 USD per hour |
| chat-llm | 5,422.86 | 4 slices of 3g.40gb at 1.857 USD per hour |
| notebooks | 4,692.86 | 6 slices of 2g.20gb at 1.071 USD per hour |
| finetune | 3,128.57 | 2 slices of 4g.40gb at 2.143 USD per hour |
| batch-eval | 2,920.00 | 1 whole GPU at 4.000 USD per hour |
| Idle slices | 2,346.43 | the 6 spare slices of 1g.10gb |
| Layout loss | 938.57 | one SM slice on GPU 3, one memory slice on GPUs 4 to 7 |

Two chargeback styles use the same table in different ways. Under allocated chargeback, the platform absorbs the idle line, and tenants pay only for what they reserve. Under fully loaded chargeback, idle cost is spread across tenants in proportion to what each one pays. The calculator offers both. Layout loss stays with the platform in either style, because no tenant chose it. Production Kubernetes chapter 12 makes the point that quotas are what let tenants share a cluster safely.

A reservation is not use, and the difference shows up on the invoice. A slice at 1.857 USD per hour that is busy a quarter of the time costs 7.43 USD per busy hour. The calculator computes that figure from the utilisation in section 7. Chapter 19.1 shows the Slurm view of the same idea, where accounting tracks GRES and fairshare falls as an account consumes it.

**Decision rule:** Count quota in slices per tenant with Kueue, mirror it in a native ResourceQuota, charge by a published weight per profile, and show idle cost and layout loss as separate lines.

**In one minute:** A slice becomes billable once a weight per profile exists. The tenant mix on one node costs 23,360 USD per month at the placeholder price, of which 3,285 USD is idle or lost to geometry. Fully loaded chargeback is a policy on top of the same numbers.

---
## 6. What MIG isolates and what it does not

Security reviews often go wrong in one of two ways. Some reviewers accept a single vendor sentence as the whole answer, and stop reading. Others reject the whole design because one sentence is unclear. A better review reads each documented control, names what it covers, and lists the gaps for the platform team to fill. The rest of this section follows that method.

A security reviewer asks whether tenant A can read tenant B's memory on the same H100. The honest answer depends on which sentence of the vendor documentation you rely on, and on what else the stack shares. Start with what the vendor documents, and then list what the documents leave out.

NVIDIA's guide says each instance has separate and isolated paths through the memory system. The crossbar, which is the switch that links compute to memory, together with the L2 cache banks, memory controllers and DRAM buses, is assigned to instances uniquely. That gives predictable throughput, even when other instances thrash their caches. Thrashing means the caches are constantly evicting one another's data. The guide also describes fault isolation and says one client cannot impact the work of others. Its concurrency table marks memory protection, bandwidth QoS and error isolation as yes for MIG.

The guide also documents limits and controls, and they are the part to read most carefully.

- Who can change the layout? Toggling MIG mode needs `CAP_SYS_ADMIN`, which is a powerful Linux capability. Creating instances needs the `mig-config` capability, which root holds and which can be delegated to others.
- Can instances talk directly? Peer-to-peer transfers between instances on different GPUs are unsupported, and so is CUDA IPC across GPU instances. The concurrency table lists cross-partition interop as "Limited IPC".
- Which features work inside an instance? GPUDirect RDMA works from GPU instances. Graphics APIs work only on `+gfx` profiles of some Blackwell cards.
- Can you profile the shared parts? Profiling of shared GPU resources is unsupported.

What stays shared is an inference, because the MIG User Guide is silent on it. One driver serves all instances, so a bad driver update reaches every tenant on the node. The board has one power budget and one firmware image, and a GPU reset affects the whole GPU. Chapter 11.24 lists the same shared items.

Kubernetes isolation is a separate layer, and MIG does not provide it. Namespaces, RBAC, network policies and storage credentials keep tenant A away from tenant B's secrets. RBAC is the role-based access control that decides who may do what. Production Kubernetes chapter 12 separates soft multitenancy, where tenants share some trust, from hard multitenancy, where they are treated as adversaries. It also notes that requests and limits are weaker than a hypervisor, which is the layer that separates virtual machines.

GKE's page says multi-instance GPUs are not recommended for untrusted workloads. For adversarial tenants, MIG is one layer among several. Combine it with the controls in Chapter 18.5, and keep such tenants on separate node pools. The older advice in AI Systems Performance Engineering says NCCL does not work with MIG. The MIG User Guide supersedes that advice, and it now gives experimental support from NCCL 2.31 with conditions.

**Decision rule:** Tell reviewers that MIG isolates the SMs, memory paths and errors of each instance, and that the driver, board, host and Kubernetes layers are separate controls that you must provide.

**In one minute:** NVIDIA documents separate memory paths, fault isolation and quality of service per instance. It does not document MIG as a replacement for tenant controls elsewhere. Providers such as GKE add their own warning for untrusted workloads.

---
## 7. Monitoring each instance

Per-instance monitoring is what turns a vague complaint into a short investigation. Start with the instance that belongs to the complaining tenant, check its activity and its memory, and compare them with the node total. If the instance is quiet and the node is busy, the cause is a neighbour. If the instance is busy and its memory is nearly full, the cause is the slice itself, and the fix may be a larger profile.

On Friday the notebooks tenant reports slow cells. The node dashboard shows the GPU 40 percent busy, and the memory looks fine. The engineer needs to know whether the notebooks slice is the busy one, or whether the work comes from a neighbour. The GPU-level view cannot answer that question, because it blends all the slices into one number.

On Ampere, NVML and `nvidia-smi` do not attribute utilisation to MIG devices, and they show N/A instead. NVML is the NVIDIA library that those tools are built on. The MIG User Guide recommends DCGM, version 3 or later, for per-instance numbers. GKE says that GPU utilisation metrics such as `duty_cycle` are not available for multi-instance GPUs.

The DCGM exporter 4.9.0 repository documents what is reported per instance. On a MIG GPU, fields that DCGM declares at GPU level are read once per GPU, and they carry no `GPU_I_ID`, `GPU_I_PROFILE` or `GPU_CI_ID` labels. Fields declared at instance level carry those MIG labels. The table below lists the ones that matter here, with the level at which each one is reported.

| Metric | What it tells you | Level on a MIG GPU |
|---|---|---|
| `DCGM_FI_DEV_FB_USED_BYTES` | Framebuffer memory in use | Per instance |
| `DCGM_FI_DEV_FB_FREE_BYTES` | Framebuffer memory free | Per instance |
| `DCGM_FI_PROF_GR_ENGINE_UTIL_RATIO` | Ratio of time the graphics engine is active | Per instance |
| `DCGM_FI_PROF_TENSOR_UTIL_RATIO` | Ratio of cycles the tensor pipe is active | Per instance |
| `DCGM_FI_PROF_DRAM_UTIL_RATIO` | Ratio of cycles the memory interface moves data | Per instance |
| `DCGM_FI_DEV_BOARD_POWER_WATTS` | Board power draw | Per physical GPU |
| `DCGM_FI_DEV_GPU_TEMP_CELSIUS` | GPU temperature | Per physical GPU |

Two warnings come with this table. First, version 4.9.0 names metrics with their units, and its repository tells users to update dashboards to the new names. A panel that goes blank after an upgrade is therefore likely a rename, not a broken GPU. Second, power and temperature are per physical GPU. You cannot bill or alert on power for one tenant from these fields, and this chapter does not invent a per-instance energy figure.

Each per-instance series carries the `gpu`, `GPU_I_ID` and `GPU_I_PROFILE` labels. With Kubernetes enrichment, it also carries `namespace`, `pod` and `container`, so you can point a panel at one tenant's pod. Pick the right identifier when you map a job to a GPU. The HPC job mapping uses the GPU instance ID, not the `Device N` ordinal that `nvidia-smi -L` prints, because the ordinal names a physical device and not an instance.

The platform adds a second family of metrics. kube-state-metrics exports allocatable and requested amounts per resource, and it sanitises the name, so `nvidia.com/mig-1g.10gb` appears as `nvidia_com_mig_1g_10gb`. Kueue exports reservation, nominal quota and pending workloads per queue. The per-resource ones need `metrics.enableClusterQueueResources` turned on, so check that option before you build the panels.

The dashboard has ten panels. Each expression was parsed with `promtool`, which is the only check that ran on them. Parsing catches syntax errors, but it cannot tell you whether a metric returns data, so read the panels with that gap in mind.

| Panel | Question it answers | Source metrics |
|---|---|---|
| Cost per tenant | What does each queue's reservation cost per hour | Kueue reservation times the price rule |
| Reserved slices | Who holds which profile | Kueue reservation |
| Quota minus reservation | Quota nobody holds | Kueue nominal quota and reservation |
| Free slices per profile | Slices on nodes nobody requested | Kube-state-metrics allocatable minus requests |
| SM activity per instance | Is the tenant using its slice | DCGM graphics engine ratio |
| Memory used per instance | How much of the slice is filled | DCGM framebuffer used |
| Memory pressure | Is the slice near out-of-memory | Framebuffer used over used plus free |
| Pending workloads | Which queues are waiting | Kueue pending workloads |
| Weighted share | Who is borrowing | Kueue weighted share |
| Idle slice cost | Monthly price of unreserved quota | Kueue plus price rule |

The price rule is a Prometheus rules file with one constant series per profile, labelled by `resource`. That lets the cost panels join each reservation to its price. A constant series is a fixed value that never changes, which makes it a convenient price list. The file holds three alerts. The first fires when an instance stays under 5 percent graphics activity for six hours. The second fires when an instance stays above 90 percent of its memory for ten minutes. The third fires when workloads are pending while MIG slices are free. The third alert is crude on purpose, because no metric says which profile a pending workload needs.

**Decision rule:** Monitor GPU-level health per physical GPU, and activity and memory per instance. Read the exporter version's metric names from its own file, and price slices in a rules file that a test regenerates.

**In one minute:** `nvidia-smi` cannot show per-instance utilisation on Ampere, and GKE hides it too. DCGM exporter 4.9.0 reports memory, graphics, tensor and memory-interface activity per instance, and power and temperature per GPU. Kueue and kube-state-metrics add the quota and allocation views.

---
## 8. Hands-on lab

Work through the lab in order. Each step leaves behind a result that the next step relies on, so a failure early on makes later steps meaningless. Keep a short log of what you ran and what you saw, because the record is part of the lesson.

Picture a laptop with no GPU and an afternoon to spare. That is enough to check most of this chapter, and the checks catch the mistakes that cost the most later. The first half of the lab runs on any laptop. The second half needs a MIG-capable node, which this chapter's author did not have while writing. Both halves use the same files.

### What was run here and what was not

A reader who jumps straight to the lab wants to know which results are real. On macOS arm64 with no GPU, these ran: the tests, the planner, the cost calculator, the upstream mig-parted parser, kubeconform, the Kueue CRD check and promtool. These did not run: MIG mode, instance creation, the GPU Operator, Kueue admission and DCGM scraping. The expected shapes below come from NVIDIA documentation, not from a real node.

### Step 1: set up the validators (run here)

Start by building the two validators that the checks need. Clone Kueue at v0.20.5 and mig-parted at v0.15.1. Copy `code/part19/c08_validate_mig_parted.go.txt` to `cmd/c08validate/main.go` in the mig-parted checkout. Then build it with `GOFLAGS=-mod=vendor go build -o c08validate ./cmd/c08validate`. The validator calls the upstream `Spec` parser, so it judges the config the way mig-parted itself does. Last, set `KUEUE_CRDS` to `config/components/crd/bases` in the Kueue checkout, and set `MIGPARTED_VALIDATOR` to the built binary.

What to record: the two tags, and the commit hashes. Here they were `v0.20.5` at `7e71578` and `v0.15.1` at `a24171d`.

### Step 2: run the local checks (run here)

The script below runs all six local checks in order, and it stops at the first failure. Read the numbered comments as a list of the checks themselves.

```bash
#!/usr/bin/env bash
# Chapter 19.8 local checks. Needs no GPU and no cluster.
# Run from the repository root. KUEUE_CRDS points at config/components/crd/bases of a Kueue v0.20.5 checkout.
# MIGPARTED_VALIDATOR is the binary built from c08_validate_mig_parted.go.txt inside a mig-parted v0.15.1 checkout.
set -euo pipefail

: "${KUEUE_CRDS:?set KUEUE_CRDS to the Kueue CRD directory}"
: "${MIGPARTED_VALIDATOR:?set MIGPARTED_VALIDATOR to the built validator}"

cd code/part19

# 1. Planner, cost calculator and file-consistency tests
C08_MIGPARTED_VALIDATOR="$MIGPARTED_VALIDATOR" python3 -m pytest test_c08_mig_planner.py test_c08_finops_and_configs.py -q

# 2. Print the planner and cost worked examples quoted in the chapter
python3 c08_mig_planner.py
python3 c08_finops.py

# 3. mig-parted config against the upstream parser
"$MIGPARTED_VALIDATOR" c08_mig_parted_config.yaml

# 4. Core Kubernetes objects against the Kubernetes schemas
kubeconform -strict -ignore-missing-schemas -summary \
  c08_namespaces_quota.yaml c08_mig_workload.yaml c08_mig_config_configmap.yaml

# 5. Kueue objects against the upstream CRDs
python3 -I ../../tools/check_crd_yaml.py \
  "$KUEUE_CRDS/kueue.x-k8s.io_clusterqueues.yaml" \
  "$KUEUE_CRDS/kueue.x-k8s.io_localqueues.yaml" \
  "$KUEUE_CRDS/kueue.x-k8s.io_resourceflavors.yaml" \
  -- c08_kueue_mig.yaml

# 6. Prometheus rules
promtool check rules c08_mig_rules.yml
```

Expected result: 68 tests pass. The planner prints 8 GPUs for the tenant mix and shows the shortfall with 7. The cost table matches section 5. The mig-parted file is accepted, and kubeconform, the CRD check and promtool report no problems. In the run for this chapter, kubeconform reported 13 resources valid, the CRD check reported 12 resources and 0 problems, and promtool found 9 rules.

What to record: the test count and the three validator summaries.

### Step 3: break something on purpose (run here)

This step proves that the checks can fail, and that the parser alone is not enough. Rename the first `cohortName` in `c08_kueue_mig.yaml` to `cohort`. The CRD check reports "Additional properties are not allowed ('cohort' was unexpected)". Restore the name. Next, add `"4g.40gb": 2` to the GPU 0 entry of `c08_mig_parted_config.yaml`. That layout is impossible, yet the upstream parser still prints OK. The parser checks structure and name format, not geometry. Three tests fail instead: the generator comparison, the ConfigMap comparison and the per-GPU feasibility check. Restore the file.

What to record: the CRD message, the three failing test names, and the fact that the upstream parser accepted the impossible layout. This step proves that the checks can fail, and it shows why the planner is needed on top of the parser.

### Step 4: apply the layout (not run: needs a MIG-capable node)

This step needs a MIG-capable node, so read it as a plan. Install the GPU Operator with `--set mig.strategy=mixed`, as the NVIDIA guide shows. Install Kueue v0.20.5 and turn on `metrics.enableClusterQueueResources`. Then run the cluster script. Set `NODE` to an 8-GPU H100 node that you are willing to drain, because the script empties it of GPU work.

```bash
#!/usr/bin/env bash
# Chapter 19.8 cluster steps. NOT RUN in the handbook: they need MIG-capable GPUs.
# Assumes the GPU Operator is installed with --set mig.strategy=mixed and Kueue v0.20.5 is installed.
# NODE is one 8-GPU H100 node that you are willing to drain.
set -euo pipefail

: "${NODE:?set NODE to the node name}"

# 1. Give MIG Manager the custom layout and point the ClusterPolicy at it
kubectl apply -f c08_mig_config_configmap.yaml
kubectl patch clusterpolicies.nvidia.com/cluster-policy --type='json' \
  -p='[{"op":"replace","path":"/spec/migManager/config/name","value":"c08-custom-mig-config"}]'

# 2. Apply the layout. MIG Manager terminates the GPU pods on the node first.
kubectl label nodes "$NODE" nvidia.com/mig.config=tenant-mix-v1 --overwrite
kubectl get node "$NODE" -L nvidia.com/mig.config,nvidia.com/mig.config.state

# 3. Check what the node now advertises
kubectl get node "$NODE" -o json | jq '.status.allocatable | with_entries(select(.key | startswith("nvidia.com/")))'
kubectl exec -n gpu-operator ds/nvidia-driver-daemonset -- nvidia-smi -L

# 4. Tenants, quotas and queues
kubectl apply -f c08_namespaces_quota.yaml
kubectl apply -f c08_kueue_mig.yaml

# 5. Submit one workload and watch Kueue admit it
kubectl apply -f c08_mig_workload.yaml
kubectl get workloads -n team-chat
kubectl get pods -n team-chat -o wide
```

Expected shape of the output, taken from the GPU Operator guide and not produced here: right after the label step, the state label reads `pending`. After MIG Manager finishes, it reads `success`. The node then advertises its MIG resources as allocatable. Expect 16 of `nvidia.com/mig-1g.10gb` and 6 of `nvidia.com/mig-2g.20gb`. Expect 4 of `nvidia.com/mig-3g.40gb` and 2 of `nvidia.com/mig-4g.40gb`. Expect 1 of `nvidia.com/mig-7g.80gb`. The command `nvidia-smi -L` lists each GPU, followed by its MIG devices.

What to record: the final value of `nvidia.com/mig.config.state`, the allocatable counts, and how long the node was unschedulable.

### Step 5: check that quota matches the node (not run)

This step asks whether the quota and the hardware agree. Compare the allocatable counts with the sum of the nominal quotas. A test proves that the files agree with the plan, so any difference means the hardware produced a different layout from the one you planned. Run `nvidia-smi mig -lgi`, compare the start positions with the plan, and fix the layout before you touch the quota.

What to record: the two number lists and any difference.

### Step 6: admit a workload and read the metrics (not run)

This step follows the Job from step 4 through the stack. After the Job is admitted, `kubectl get workloads -n team-chat` should show it admitted by `cq-chat`. In Prometheus, `kueue_cluster_queue_resource_reservation` for `nvidia.com/mig-3g.40gb` should read 1 for that queue. The per-instance DCGM series for that pod should carry `GPU_I_PROFILE="3g.40gb"`. Last, import `c08_finops_mig_dashboard.json` into Grafana and load `c08_mig_rules.yml` into Prometheus.

What to record: the reservation value, the DCGM labels you actually saw, and any panel that returned no data. A panel with no data is most often a metric rename or a missing Kueue option.

### Step 7: GKE variant (not run)

This variant is for teams on GKE. On GKE the layout is set per node pool. Use one pool per profile, with `gpu-partition-size`, and select the pool by the label `cloud.google.com/gke-gpu-partition-size`. The GKE page shows pods requesting `nvidia.com/gpu` for a partition, so Kueue flavors would key off that label. No manifest was written here, because it could not be tested.

What to record: the partition sizes available for your GPU type, since GKE's list for the H100 omits 4g.40gb.

---
## Exercises

Work the exercises with a notebook beside you. Each answer should come from a run of the code, not from memory, and the solution sketches are there to check your reasoning after you have made a prediction.

Picture a platform engineer who has just been asked to change the tenant plan for next quarter. The exercises below are the same kind of request, and each one builds on the code from this chapter.

1. **Add a profile to the demand.** A tenant needs three `1g.20gb` slices. Predict the GPU count before you run anything, then run the planner. *Solution sketch:* add the line to `TENANT_MIX`. Each slice takes 2 memory slices and 1 SM slice. Three slices therefore add 6 memory slices and 3 SM slices. The planner treats `1g.20gb` as its own profile. Its legal starts are the even positions between 0 and 6.
2. **Waste less.** Two GPUs each hold seven `1g.10gb` slices and strand a memory slice apiece. Try replacing one of those GPUs with three `2g.20gb` slices and one `1g.10gb` slice. Then decide which layout is better for the demand you expect. *Solution sketch:* check `layout_stats`. The SM slices become full, but search loses spare capacity, so the right answer depends on demand.
3. **Change the cost rule.** Change the cost rule so that the charge depends on memory share only. *Solution sketch:* make `blended_weight` return `Fraction(mem_slices, 8)`. The 4g.40gb and 3g.40gb slices now cost the same. The invariant test still passes, which shows the rule is policy and not physics.
4. **Alert on stranded geometry.** Write an alert that fires when slices of one profile sit free while another profile is short. *Solution sketch:* use allocatable minus requests, per `resource`, and compare the result with Kueue pending workloads. Check the rule with `promtool check rules`. No metric says which profile a pending workload needs, so you must add a label yourself.
5. **Plan a reconfiguration.** Plan a move of node 3 to `all-3g.40gb`. *Solution sketch:* follow the four steps in section 4. The config gives 2 slices per GPU, so the quotas must add up to 16 for the node.
6. **Argue for whole GPUs.** The batch tenant runs a 7g.80gb slice for two hours a night. Argue for or against a whole GPU for that tenant. *Solution sketch:* the weight is 1, so the allocated cost equals a whole GPU. The difference is the other 22 hours, which a dedicated slice cannot lend to anyone. Use `cost_per_busy_hour` to show the gap.

---

## Checkpoint questions

<details><summary>1. What does the 3g.40gb profile name tell you?</summary>
It has 3 of 7 SM slices and about 40 GB of memory, which is 4 of the 8 memory slices on an H100 80 GB. The name follows the memory, so other GPUs use other names for the same fractions.
</details>

<details><summary>2. Why can an H100 hold only one 4g.40gb instance?</summary>
The profile has one legal start position, 0, in the A100 listing the MIG User Guide prints. A second instance would need the same start.
</details>

<details><summary>3. Why do two 3g.40gb instances leave one SM slice unused?</summary>
Each uses 3 of the 7 SM slices, and together they fill all 8 memory slices, so the seventh SM slice has no memory left to pair with.
</details>

<details><summary>4. Why do seven 1g.10gb instances give only 70 GB on an 80 GB GPU?</summary>
They use all 7 SM slices but only 7 of 8 memory slices, because 1g.10gb can start only at positions 0 to 6.
</details>

<details><summary>5. When is time-slicing better than MIG?</summary>
When all tenants share one trust domain or the GPU has no MIG support. The GPU Operator guide says time-slicing has no memory or fault isolation between replicas.
</details>

<details><summary>6. Why should multi-node training not use MIG?</summary>
The MIG User Guide lists no peer-to-peer between instances on different GPUs, no CUDA IPC across GPU instances, and only experimental NCCL support. Training also wants whole GPUs and their interconnects.
</details>

<details><summary>7. What is the difference between the single and mixed strategies?</summary>
With single, every MIG device appears as `nvidia.com/gpu` and all GPUs use MIG with one profile. With mixed, each profile is its own resource such as `nvidia.com/mig-1g.10gb`.
</details>

<details><summary>8. What happens to running pods when you label a node with a new `nvidia.com/mig.config`?</summary>
MIG Manager sets the state label, terminates the GPU pods on the node and then applies the layout. Plan a drained-node window.
</details>

<details><summary>9. Why can a DCGM agent block enabling MIG mode?</summary>
A process holding a driver handle can stop the GPU reset. The MIG User Guide reports "In use by another client" and says to stop services such as DCGM first.
</details>

<details><summary>10. Do MIG instances survive a reboot?</summary>
No. The MIG User Guide says created instances are not persistent, and on Hopper and later the mode itself does not persist across a driver reload. MIG Manager or mig-parted recreates the layout.
</details>

<details><summary>11. Why does the ClusterQueue list cpu and memory beside the MIG resource?</summary>
Kueue refuses a pod that requests a resource the queue does not cover. Listing only one MIG resource also pins a tenant to that profile.
</details>

<details><summary>12. Why add a ResourceQuota when Kueue has quota?</summary>
The API server enforces it at pod creation and another team can own it. Extended resources accept only the `requests.` prefix, for example `requests.nvidia.com/mig-3g.40gb`.
</details>

<details><summary>13. What is a slice's weight in the cost model?</summary>
The average of its memory share and SM share. A 3g.40gb slice is 0.4643 and a 4g.40gb slice is 0.5357. It is a design choice, not an NVIDIA rule.
</details>

<details><summary>14. What is layout loss and who pays for it?</summary>
It is the GPU share no profile in the layout can use, such as one SM slice beside two 3g instances. No tenant chose it, so the platform carries it.
</details>

<details><summary>15. How do idle cost and layout loss differ?</summary>
Idle cost is slices nobody reserved, and quota or scheduling changes reduce it. Layout loss is built into the geometry and only a different layout reduces it.
</details>

<details><summary>16. What does the MIG guide say MIG isolates?</summary>
Separate paths through the memory system, including crossbar ports, L2 banks, memory controllers and DRAM buses, plus fault isolation and defined quality of service. It does not present MIG as a replacement for other tenant controls.
</details>

<details><summary>17. Why is a node-level GPU busy graph not enough for a tenant complaint?</summary>
Power and temperature are per physical GPU, and `nvidia-smi` shows N/A for utilisation on Ampere. You need per-instance DCGM series labelled with `GPU_I_ID` and `GPU_I_PROFILE`.
</details>

<details><summary>18. Why might a panel go blank after a DCGM exporter upgrade?</summary>
Version 4.9.0 names metrics with units such as `DCGM_FI_DEV_FB_USED_BYTES` and tells users to update dashboards from the 1.x names.
</details>

<details><summary>19. How does kube-state-metrics spell `nvidia.com/mig-1g.10gb`?</summary>
As `nvidia_com_mig_1g_10gb`. It replaces invalid characters in the resource name with underscores.
</details>

<details><summary>20. What did the capstone run here and what did it not run?</summary>
It ran the planner and cost tests, the upstream mig-parted parser, kubeconform, the Kueue CRD check and promtool. It did not run MIG, the GPU Operator, Kueue admission or DCGM scraping, because the host has no GPU.
</details>

---

## Sources and review notes

### Sources

- NVIDIA MIG User Guide: Introduction, Supported GPUs, Concepts, Deployment Considerations, MIG Device Names, Supported MIG Profiles, Getting Started with MIG. All pages show "last updated Nov 04, 2026" and were fetched 2026-11-10 from `docs.nvidia.com/datacenter/tesla/mig-user-guide/`.
- NVIDIA GPU Operator documentation "GPU Operator with MIG" (v26.7.2 examples) and "Time-Slicing GPUs", and the k8s-device-plugin README, fetched 2026-11-10.
- mig-parted v0.15.1 (commit `a24171d`), dcgm-exporter 4.9.0 (commit `4e663a5`), Kueue v0.20.5 (commit `7e71578`) with its documentation and CRDs, kube-state-metrics v2.20.0, Kubernetes "Resource Quotas", and GKE "Running multi-instance GPUs", all fetched or cloned 2026-11-10.
- *AI Systems Performance Engineering*, chapter 3, "OS, Docker, and Kubernetes Tuning for GPU-Based Environments".
- *Kubernetes for Generative AI Solutions*, chapter 10, "Optimizing GPU Resources for GenAI Applications in Kubernetes".
- *Production Kubernetes*, chapter 12, "Multitenancy".
- *NVIDIA Base Command Manager 11 Administrator Manual*, section 3.17.3 "MIG Configuration": one MIG management tool per node.
- *Supercomputers for Linux SysAdmins*, chapter 15, "Slurm".
- *AI Factory* was read and has no MIG or GPU-sharing content, so no claim here draws on it.

### Cross-references to other handbook chapters

Chapters 11.4, 11.5, 11.8, 11.24, 11.25, 11.26, 11.29, 16.14, 17.4, 18.5, 19.1, 19.2, 19.7 and 19.9, as named in the metadata table.

### Migrated from `nvidia-devops`

- `docs/nvidia-zero-to-hero/volume-24/chapter-06-mig-configuration-multi-tenant.md`: the H100 profile names and the "slices sum to at most 7" rule, which section 3 shows is necessary and not sufficient. Numbers were re-derived from the NVIDIA guide, and its TFLOPS estimates were not reused.

### Explicitly labelled inferences

- The planner reuses the A100 40 GB start positions for every seven-slice GPU. A test checks it against the H100 figure.
- The blended weight, the idle and layout-loss split, and the fully loaded policy are this chapter's design.
- The price of 4.00 USD per GPU-hour, the cpu and memory quotas, and the alert thresholds are placeholders.
- That the driver, board power and firmware stay shared, and the reconfiguration procedure, are inferred, not documented.

### Not verified or not run, and why

- No MIG command, GPU Operator step, Kueue admission or DCGM scrape was run, because the host has no GPU.
- The PromQL was only parsed with `promtool`, so label joins such as the price multiplication are unverified against live data.
- The `resource` label value of `kueue_cluster_queue_resource_reservation` comes from the metrics documentation and was not seen in a real scrape.
- Whether MIG Manager builds the five-profile mix in one pass is untested. mig-parted retries orderings, which is visible in its source.
- The GKE variant is documentation only, with no manifest.
- The `nvidia-smi` output formats in the MIG User Guide come from older drivers.

### Verification log

| Item | Count |
|---|---|
| Claims checked against a source or a tool | 56 |
| Confirmed | 49 |
| Labelled as inference | 7 |
| Still unverified, listed above | 6 |

The corrections were these. The Kueue YAML uses `cohortName` and only fields the CRD defines, and the CRD checker confirms that. MIG and time-slicing are in chapters 11.24 and 11.25. NVIDIA publishes no 5g.40gb profile, and the H100 resource name is `nvidia.com/mig-1g.10gb`. Profile IDs passed to `-cgi` are GPU-specific. A layout change needs the drain in section 4, so serving does not continue through it. The chapter makes no claim about a hardware root of trust or a cost drop with no source. The removed groups are in the ledger.
