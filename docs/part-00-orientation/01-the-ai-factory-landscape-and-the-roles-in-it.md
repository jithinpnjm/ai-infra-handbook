---
id: "c00-01"
title: "0.1 The AI factory landscape and the roles in it"
sidebar_label: "0.1 The AI factory landscape and the roles in it"
sidebar_position: 1
description: "The AI factory landscape: what an AI factory is, the layers from power to product, and the roles that run each layer."
status: "drafted"
tier: "2"
level: "B"
lab_venue: "Mac"
---

# 0.1 The AI factory landscape and the roles in it

Picture your first week on a new team. A manager points at a long row of racks, says the room is expensive to run every hour, and asks you to make sure the machines do useful work. The answer is an AI factory.

An **AI factory** is a data center built to turn electricity and data into tokens: trained models and answered requests. A token is a small piece of text that a model reads or writes, so even a short answer is made of several tokens. Everything in this book hangs off that one idea. The unit of output is a token, the unit of cost is the GPU-hour, meaning one GPU running for one hour, and your job as an infrastructure engineer is to keep the expensive part, the GPUs, busy and healthy.

A GPU server costs far more than the rest of its rack combined, and it earns nothing while it waits. It waits for data from storage, for a message from another node, for a failed neighbour to be replaced, or for a person to notice an alert. Almost every chapter that follows is about removing one of those waits.

## What a GPU server is

Your colleague has just pulled one server out of the rack and asks what each part is for.

Picture one server in a rack. It holds eight GPUs, a pair of CPUs, a few network cards and some local disks. A GPU, or graphics processing unit, is the chip that does most of the arithmetic in AI work. A CPU, or central processing unit, is the general-purpose chip that runs the operating system and prepares the work for the GPUs. The GPUs are joined to each other by a fast internal link called NVLink, so that eight of them behave like one large accelerator. An accelerator is any chip built to speed up one kind of work. The network cards, or NICs for network interface cards, connect the server to other servers and to shared storage. A small separate computer on the motherboard, the baseboard management controller, lets you power the server on and off and read its sensors without logging in to the operating system.

One server is rarely enough. A large training job spreads over hundreds or thousands of GPUs, and a popular model is served from many servers at once. The factory is therefore a very large number of identical servers, joined by a network, managed by software that treats them as one pool.

## The layers

A user reports that a job is slow, and the report says nothing more. Where do you start? The answer is to walk the stack from the floor up, because a problem in a lower layer often looks like a problem in a higher one.

Here is the stack from the physical floor up to the product.

```mermaid
flowchart TB
  P["Power, cooling, floor space"] --> H["Hardware: GPU servers, CPUs, NICs, storage"]
  H --> N["Fabric: NVLink, InfiniBand / RoCE Ethernet, storage network"]
  N --> O["Node OS and drivers: Linux, GPU driver, CUDA, fabric manager"]
  O --> M["Cluster management: BCM, Slurm, Kubernetes, BMC / Redfish"]
  M --> F["Frameworks: PyTorch, NCCL, Megatron, vLLM, Triton"]
  F --> S["Platform and product: MLOps, serving, observability, security"]
```

A fault at any layer shows up at the top as "the job is slow" or "the job died". The handbook is ordered bottom-up so you can learn to find which layer a fault lives in. The fabric is the network that joins the servers. A bad cable in the fabric slows the collective operations, which are the steps where many GPUs exchange data together, and the user sees only a slow answer.

| Layer | Where in this handbook |
|---|---|
| Linux, networking, Python, automation | Parts 1-4 |
| Kubernetes and containers | Part 5 |
| HPC and Slurm | Part 6 |
| BMC, Redfish, Base Command Manager | Parts 7-8 |
| NVIDIA systems (DGX, HGX, SuperPOD) | Part 9 |
| GPU and CUDA, GPUs on Kubernetes | Parts 10-11 |
| AI networking and storage | Parts 12-13 |
| Training, fine-tuning, inference | Parts 14-15 |

Use the table to find the part that covers the layer you suspect.

## Training versus inference

Two teammates both tell you the AI system is broken. One means a training run stopped over a long weekend. The other means a chat answer took too long to start. They are describing two different kinds of work, and each one fails in its own way.

Two kinds of work run on the factory floor, and they fail in different ways.

Training teaches a model by showing it data. Think of a student who works through practice problems, checks the answers and adjusts. Training runs for days or weeks across many nodes, and it is limited by how fast the GPUs can exchange results, how fast they can save progress, and how well the job survives a failure. One slow or failing GPU stalls everyone.

Inference uses a trained model to answer requests. Inference is latency-sensitive, which means a user notices every delay, and bursty, which means requests arrive in sudden waves. It is limited by memory bandwidth while the model writes its answer, by the memory that holds the conversation so far, and by how well requests are routed and scaled.

HPC jobs, scheduled with Slurm and MPI, came before both. HPC means high-performance computing, the older world of large scientific simulations. Slurm is a job scheduler that decides which jobs run on which machines. MPI, the Message Passing Interface, is a common way for those machines to send messages to each other. They still supply many of the scheduling and cluster-management habits used in AI factories.

## A training job, end to end

Your teammate's training job is about to start, and you want to know what happens between the submit button and the saved result. The example is a team that wants to train a language model on 512 GPUs, which is 64 servers of eight. Follow the job from submission to a saved result.

A person submits the job to a scheduler, either Slurm or a Kubernetes batch system. The scheduler waits until 64 servers are free at once, because the job cannot start with fewer. It then places one process on every GPU. Each process is called a rank, a number that names one process in the job, and every rank has a number from 0 to 511.

Each rank loads the same model and reads a different slice of the training data from shared storage. Slow storage shows up here first. Ranks sit idle, GPU utilisation drops, and nothing looks broken. When the GPUs look quiet but no error appears, check the storage path first.

One training step then runs. Every rank computes how the model should change to do better on its own slice of data. Before anyone updates the model, all 512 ranks must agree on one combined answer. They average their results with an operation called all-reduce, so every copy of the model moves in the same direction. Inside a server the data travels over NVLink. Between servers it travels over InfiniBand or RoCE Ethernet, through a library called NCCL that picks the routes. RoCE stands for RDMA over Converged Ethernet, where RDMA is remote direct memory access, a way to move data between machines without extra copying. NCCL, the NVIDIA Collective Communications Library, is the software that runs collectives such as all-reduce.

All-reduce is a barrier. No rank continues until the last rank has delivered its part. If one GPU runs hot and slows down, or one cable drops packets, the other 511 wait for it at every step.

Every so often the job writes a checkpoint, a file holding the model and the optimiser state, so that a failure does not lose days of work. The optimiser state is the set of running numbers the training method keeps. A checkpoint of a large model is hundreds of gigabytes, and every rank writes at the same moment. Storage that handled data reading well can still choke on this burst. While the write runs, the GPUs are idle, so checkpoint time is a direct tax on useful work.

When the job ends, or fails, the scheduler releases the servers. After a failure someone must find the cause, replace or repair the bad node, and restart from the last checkpoint. The work lost is whatever ran since that checkpoint.

## An inference request, end to end

Now follow one request to a deployed model, say a user typing a question into a chat window.

The request reaches a load balancer, which picks one of many replicas of the model server. A replica is one running copy of the model. Engines such as vLLM or TensorRT-LLM run on each replica. An engine is the software that loads the model and runs it on the GPU. The replica first tokenises the text, which means splitting it into the numbered pieces the model understands.

The model then works in two phases. In the prefill phase it reads the whole prompt at once. This is heavy arithmetic and keeps the GPU busy. In the decode phase it writes the answer one token at a time. Each new token needs the model weights, the learned numbers that make up the model, to be read from GPU memory again. So decode is limited by memory bandwidth, not by arithmetic.

To avoid recomputing the conversation for every new token, the engine keeps intermediate results for all earlier tokens in a store called the KV cache. KV stands for key and value, the two kinds of intermediate results kept for each token. The KV cache grows with the length of the conversation and with the number of requests in flight. It lives in the same GPU memory as the model weights, so it limits how many requests one GPU can serve at once.

Because decode wastes most of the GPU's arithmetic on a single request, the engine batches many requests together and moves a token forward for all of them in one pass. A bigger batch means more tokens per second and a lower cost per token, but each user waits a little longer. Tuning that trade-off is most of an inference engineer's work.

The tokens stream back through the load balancer to the user. The numbers that matter are the time to the first token, the time between tokens, and the share of requests that meet the target for both.

## What goes wrong at scale

Your job ran cleanly on a single server last month. Now the same kind of job on a large cluster is restarted every few hours, and the team starts to wonder whether the code is broken.

At eight GPUs a hardware failure is an event. At thousands it is a schedule. Meta reported that during a 54-day stretch of training the Llama 3 405B model on 16,384 H100 GPUs, the job was interrupted 466 times. Of these, 419 were unexpected, and about 78 percent of the unexpected ones were traced to hardware, most often GPUs and their memory. That is roughly one unplanned interruption every three hours.

Two facts follow. First, a job that needs every GPU to keep stepping is only as reliable as its weakest part, so the failure rate of the whole job is the sum of the failure rates of every GPU, cable and switch port. Second, each interruption costs more than the failed part. All ranks stop, the job restarts, and work since the last checkpoint is redone. The teams that keep this overhead low checkpoint often, detect bad nodes within minutes, and keep spare servers ready to swap in.

The same pressure applies to inference at a smaller scale. A single replica that is slow but not dead can pull down the tail latency of a service, and a load balancer that does not notice keeps sending it traffic.

This is why the factory needs site reliability engineering, or SRE, which is the discipline of keeping services healthy with measurements and rehearsed responses. Good utilisation is not a matter of fast hardware alone. It depends on finding the slow or failing component quickly, taking it out of service, and putting the work somewhere else. Fleets that are run well measure goodput, the share of GPU time that goes into progress that is kept, and not only utilisation, which also counts work that is later thrown away.

## The roles

Your pager goes off at night, and the alert points at a slow network link. Who should look at it? In an AI factory the answer depends on the layer, and each role owns a different layer. The table lists who owns what and which tools each one reaches for.

| Role | Owns | Typical tools |
|---|---|---|
| Datacenter / hardware engineer | Racks, power, cabling, firmware, BMC | Redfish, IPMI, vendor tools |
| Cluster / HPC administrator | Provisioning, Slurm, users, health | BCM, Slurm, Ansible |
| Network engineer | InfiniBand / RoCE fabric, congestion, telemetry | UFM, switch OS, perftest |
| Platform / Kubernetes engineer | GPU operator, scheduling, multi-tenancy | Kubernetes, Helm, Kueue |
| MLOps / LLMOps engineer | Pipelines, registries, evaluation, release | Argo, MLflow, observability stack |
| Inference engineer | Engines, batching, quantisation, SLOs | vLLM, TensorRT-LLM, Triton |
| Site reliability / operations | Alerts, incidents, capacity, cost | Prometheus, DCGM, runbooks |

Small teams combine several roles in one person, so the names are a guide to who to ask rather than a fixed box. Part 0.3 maps each role to a reading order.

## Common failure at this level

A dashboard shows the GPUs at a low utilisation figure, and the first instinct is to blame the GPUs.

The common mistake is treating the GPU as the only component that matters. In practice a stalled job is most often a NIC, a cable, a storage stall or a misconfigured driver. A driver is the software that lets the operating system talk to the GPU. GPU utilisation alone will not tell you which of these it is.

## Checkpoint questions

These questions check whether the big picture has settled. Answer each one in your head first, then open it to compare.

<details><summary>1. What is the unit of output of an AI factory, and what is the main unit of cost?</summary>

Tokens; GPU-hours.

</details>

<details><summary>2. Why does one slow GPU hurt a whole training job?</summary>

Collectives such as all-reduce wait for the slowest rank.

</details>

<details><summary>3. Which resource usually limits inference decode?</summary>

Memory bandwidth, plus KV-cache capacity.

</details>

<details><summary>4. Name three layers beneath the framework that can make a job slow.</summary>

Fabric, driver / firmware, storage, thermal or power limits.

</details>

## Sources and review notes

- **Llama 3 interruption figures:** Dubey et al., *The Llama 3 Herd of Models*, arXiv 2407.21783 (2024), section on reliability during pre-training. The figures are quoted from memory of the paper and were not re-fetched when this chapter was rewritten.
- **Training and inference mechanics:** general descriptions of data-parallel training with all-reduce, checkpointing, prefill and decode, KV cache and continuous batching. Later parts give each one in depth.
- **Earlier draft:** an earlier version summarised a business-book chapter on AI transformation in manufacturing and policy. That material was removed because it is not infrastructure content and used a different meaning of "AI factory". The source remains `ai-factory` chapter 11 (DOI 10.1201/9781003208686-11).
