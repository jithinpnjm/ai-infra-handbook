# Removed from 17.16 (off topic for AI-assisted operations)

Sections 5.5 to 5.14 of docs/part-17-operations/16-*.md as they stood on 2026-11-12, kept here so the owner can decide where they belong (a Part 10 or 15 outlook chapter is the natural home).

### 5.5 AI-assisted scheduling and real-time control

The push toward automation reaches the cluster itself. Training and inference clusters run many jobs and requests at once, and they need resource-sharing strategies that change with conditions. Today's orchestrators, such as Kubernetes and SLURM, still rely on static heuristics and simple resource requests. Adaptive scheduling is the next step.

Picture a scheduling agent that watches the whole cluster and learns where to place inference requests and training jobs for the highest overall throughput. It might learn that two workloads can share a node without interfering. One could be compute-heavy while the other is memory-bandwidth-heavy. The agent could read Kubernetes telemetry, such as pod GPU utilization and queue wait times, then reschedule jobs or adjust pod resources.

In that picture, the cluster behaves like a self-driving car. It keeps adjusting its resource allocation as conditions change, rather than following a fixed route. Your job shifts toward setting policies and goals, while the scheduler works out the details. The payoff is higher resource use and fewer bottlenecks.

NVIDIA Dynamo is a distributed inference framework. It coordinates request scheduling, KV cache placement, and data movement across GPUs and nodes. It integrates with Kubernetes for inference and disaggregation. In that role, its scheduler assigns microbatches to pipeline stages and reroutes requests when a node fails.

Weight streaming and activation offloading go further. A layer streams from host memory to the GPU only when its weights are needed, such as during decode. The same idea works across many nodes and GPUs. The book notes that parts of a 100-trillion-parameter model could then sit on cheaper storage, which helps inference scale.

Inference software does part of this work too. The book names vLLM, SGLang, NVIDIA Dynamo, and TensorRT-LLM as tools that improve scheduling and resource use in large inference clusters. They use in-flight batching and a paged KV cache. They can also split the prompt prefill stage from the generation decode stage onto separate resource pools. These choices reduce tail latency and improve throughput per watt.

Reinforcement learning can also control live system behavior in ways fixed rules struggle to match. A power-management agent could tune clock frequencies and core allocation to get more performance per watt. It would learn its policy by observing the running system. Another agent could decide which tensors stay in GPU memory and which move to CPU memory or NVMe storage. That beats a fixed rule such as "swap least recently used," because it watches real access patterns.

Practitioners already use reinforcement learning for cache eviction and network congestion control. Ultrascale systems have hundreds of interacting parts. There are too many knobs for a person to find good settings in time, especially when workloads change.

For the performance engineer, the job becomes supervising these agents. The comparison is a pilot who relies on autopilot. The pilot still needs deep knowledge and must step in when something unusual happens. You set the objectives and the safety and fairness guardrails. You also handle situations the AI has not seen before, while routine load balancing, failure recovery, and memory-buffer tuning go to the AI.

Teams that insist on tuning everything by hand will fall behind teams that use AI assistance and autotuning. Spend your effort on new designs and hard optimizations, and let automation handle the routine work.

### 5.6 Smart compilers and automated optimization

Gone are the days when an engineer hand-tuned every CUDA kernel. High-level tools and AI systems now do much of the heavy lifting. Frameworks such as PyTorch, TensorFlow, and JAX use smart compilers and execution-graph optimizers. They fuse operations, use Tensor Cores automatically, and overlap computation with asynchronous data movement. On newer GPUs, they can use features such as the Tensor Memory Accelerator for that overlap.

OpenAI's Triton compiler lets developers write GPU kernels in a Python-based language. Triton compiles those kernels into efficient CUDA kernels. The complexity stays hidden from the person writing them. OpenAI and NVIDIA work together so that Triton supports new GPU architectures and their specialized features.

When a new GPU generation ships, an updated Triton compiler exposes its new capabilities. You write high-level Python, and the compiler generates code for that GPU. You do not need to write C++ or PTX assembly.

Many optimizations that used to be hand-coded are now automated. Automatic kernel fusion, autotuning of kernel-launch parameters, and numerical-precision decisions can all go to compilers and AI assistants. The book expects this trend to accelerate.

Graph execution cuts overhead too. CUDA Graphs capture a sequence of GPU operations, with their dependencies, as a static graph. You instantiate and launch that graph with little CPU overhead, using `cudaGraphInstantiate()` and `cudaGraphLaunch()`. Frameworks now capture training loops and other repeated patterns this way. Even a dynamic graph can be traced once and then replayed.

Overlapping communication with computation is becoming automatic as well. A system could notice that while GPU 1 computes layer 10, GPU 2 can start layer 11. That is pipeline parallelism applied under the hood. Fully automatic pipeline parallelism is still an active research area. Current frameworks still need explicit pipeline-parallel code.

The book covers 3D, 4D, and 5D parallelism, which combine data, tensor, model, expert, and context or sequence parallelism. These techniques still depend on human judgment and experience. Expert guides such as Hugging Face's Ultra-Scale Playbook describe them today. The hope is that compilers, libraries, and frameworks will absorb them soon.

One day an AI advisor might see a 500 billion-parameter model and propose a layout. It might suggest eight-way tensor parallelism inside each node, followed by four-way pipeline parallelism across nodes. It could also suggest layer groupings and chunk sizes. The book presents this as a possibility, not a current feature.

For performance engineers, this would be a large productivity gain. Instead of trying endless configurations, you could ask for a near-optimal starting point. Your role would shift toward guiding these tools and checking that they work well.

The practical advice is to use these tools rather than fight them. Use high-level compilers such as Triton, which know what your hardware can do. Also watch new AI-driven optimization services. They can look like black boxes, but they hold a lot of hard-won performance knowledge.

### 5.7 AlphaTensor and AI-discovered matrix multiplication

Not all AI optimization happens at the code level. Some of it reaches into algorithms and math. In 2022, Google DeepMind's AlphaTensor project used AI to discover new general matrix multiply (GEMM) techniques.

GEMMs sit under almost all model training and inference. A small gain in GEMM efficiency therefore affects the whole field. AlphaTensor treated the search for fast algorithms as a single-player game. Reinforcement learning let it explore many possibilities.

The results beat the best human-derived methods known at the time. AlphaTensor rediscovered Strassen's famous subquadratic algorithm for 2 × 2 matrices. It also improved on that method for larger matrix sizes.

The real test came on hardware. AlphaTensor found a method tuned for the NVIDIA Volta V100 generation. That method multiplied large matrices 10%–20% faster than the standard cuBLAS library of that era. A 10%–20% gain in GEMM speed is large. It is like gaining 10%–20% more compute in every forward and backward pass.

Such gains usually need a new hardware generation or months of low-level CUDA tuning. Here the AI found a better mathematical method in a comparatively short time. The lesson is that efficiency may remain in core operations that engineers consider settled. An AI can search through millions of variations that no person could try.

The return is indirect but broad. If the algorithm enters a GPU library, any large training job or inference workload speeds up without new hardware. The book notes that a 15% speed improvement, over thousands of training iterations on hundreds of GPUs, saves large amounts of time and energy. The gain pays back every time the code runs.

The book says these matrix-multiplication algorithms remain experimental. Mainstream libraries such as cuBLAS had not yet adopted them, pending more validation and generalization.

For the ultrascale performance engineer, stay open to AI-driven optimization at every level of the stack. Even well-tuned operations such as GEMMs may have room left. Letting an AI search the space without human bias can cut runtimes across the board.

### 5.8 Generating a CUDA attention kernel with a reasoning model

Writing low-level GPU code was long reserved for expert engineers the book calls CUDA Ninjas. NVIDIA engineers tested whether DeepSeek-R1, a reasoning model, could produce a high-performance CUDA kernel for a complex attention mechanism. The target was code that rivaled hand-tuned implementations.

A reasoning model uses inference-time scaling. Instead of one quick pass, it refines its answer over a longer period. The longer it gets to iterate, the better the result tends to be. That is like a person who works through an answer before speaking.

The NVIDIA team ran R1 on an H100 and gave it 15 minutes to generate an optimized attention kernel. They placed a verifier inside the generation loop. Each time the model proposed a kernel, the verifier checked its correctness and measured its efficiency. The loop looks like this:

```
for iteration in range(max_iters):
    code = R1_model.generate_code(prompt)
    valid, runtime = verifier.verify(code)
    if valid and runtime < target_time:
        break  # Accept this kernel
    prompt = refine_prompt(prompt, verifier.feedback)
    ...
```

The feedback becomes a better prompt for the next attempt. The loop stops when the kernel meets the criteria. The cycle is generate, verify, feedback, and iterate.

The team's prompt asked for a kernel with on-the-fly relative position encoding:

```text
Please write a GPU attention kernel to support relative position encodings. Implement the relative positional encoding on the fly within the kernel. The complete code should be returned, including the necessary modifications.

Use the following function to compute the relative positional encoding:

def relative_positional(score, b, h, q_idx, kv_idx):
    return score + (q_idx - kv_idx)

When implementing the kernel, keep in mind that a constant scaling factor 1.44269504 should be applied to the relative positional encoding due to qk_scale = sm_scale * 1.44269504. The PyTorch reference does not need to scale the relative positional encoding, but in the GPU kernel, use:

qk = qk * qk_scale + rel_pos * 1.44269504

Please provide the complete updated kernel code that incorporates these changes, ensuring that the relative positional encoding is applied efficiently within the kernel operations.
```

The constant 1.44269504 equals 1 divided by ln(2). The prompt uses it to scale the relative-position term when forming `qk`. The AI produced a functionally correct CUDA kernel. That kernel ran 1.1–2.1× faster than PyTorch's FlexAttention API across attention patterns, including causal masks and long-document masks.

On Stanford's KernelBench attention tasks, the generated kernels were accurate on 100% of basic Level-1 cases and 96% of complex Level-2 cases. The book says this essentially matches the reliability of a human engineer. Human oversight was still needed in this experiment. Pair a verifier with a robust test suite, as KernelBench does, so rare edge cases do not slip into generated code.

Giving a model the tools to verify, critique, and refine its output improves code quality. The loop mirrors how an engineer profiles, debugs, and improves code. Even NVIDIA's top CUDA engineers might spend hours or days on one attention variant. An AI copilot can produce a comparable kernel in a fraction of that time, which frees engineers for system-level work.

The book describes such copilots as pretrained and fine-tuned AI interns. They reason through hard problems using CUDA tips learned from existing code bases. Treat them as a force multiplier for human productivity, not a replacement for review.

### 5.9 Reinforcement learning for Triton kernels

Predibase, a startup, asked a bolder question. Could an LLM learn to write strong OpenAI Triton kernels from many examples of PyTorch and Triton code? Triton is a Python-like GPU language and compiler. The goal was code that replaces PyTorch operations and runs faster than TorchInductor, which itself uses Triton for GPU code generation.

The team used a cluster of H100 GPUs. They fine-tuned Qwen2.5-Coder-32B-Instruct, a 32-billion-parameter model, with reinforcement learning. The method was Group Relative Preference Optimization (GRPO). The environment rewarded correctness more than runtime speed. The tuned model produced correct Triton kernels for all 13 tasks.

The reward function guided the model toward better code over time. The model proposed a kernel. The system compiled and tested that kernel for correctness and speed. The model received a positive reward when the kernel ran without errors, produced the right results, and beat the baseline kernel's speed.

Within a few days, success rose from near 0% to working kernels about 40% of the time. That took 5,000 training steps. Some kernels ran up to 3× faster than the baseline. The model kept improving as training went on.

The model optimized by testing, observing feedback, and adjusting, much as engineers do. Rewarding both correctness and speed aligns the model with real performance. It can learn tactics such as warp-level parallelism and fewer global memory accesses.

The value is that kernel-level tuning becomes automated. Instead of hand-building a kernel for each new model, a trained assistant can produce several variants and keep the best one. That shortens development cycles. It also lets smaller companies reach strong performance.

The book suggests a future where Triton and Python may replace hand-written CUDA for many kernels. Over time, an AI agent could keep writing and improving kernels as part of the normal pipeline.

### 5.10 Hardware for models with 100 trillion parameters

The book's long-range question is how to scale toward models with tens or hundreds of trillions of parameters. The trillion-parameter threshold has already been crossed. The next step starts with hardware that offers more memory and more bandwidth, ideally on the GPU itself.

Context helps here. The book gives 3 × 10^23 FLOPS as the training compute for GPT-3, and roughly 2 × 10^25 FLOPS for GPT-4. The upcoming ultrascale AI factories target 10^27 to 10^28 FLOPS for training. Against 2 × 10^25, that is roughly 50 to 500 times the compute used for GPT-4.

High-bandwidth memory (HBM) keeps evolving. HBM3e ships with the Blackwell generation of GPUs. HBM4 appears in the Rubin generation, and it doubles bandwidth per stack again. The book puts that at about 1.6 TB/s per stack. HBM4 may also raise capacity to 48 GB or 64 GB per module.

Future GPUs could carry 8 or 16 HBM stacks. At 64 GB each, that totals 512 GB or 1,024 GB on one board. That much local memory holds many parameters on each GPU, which cuts the need to swap data in and out. A job that needed 8 GPUs might fit on one. A job that needed 100 GPUs might fit on 10.

Multichip designs such as the Grace Blackwell Superchip combine CPUs and GPUs. The NVIDIA GB200 and GB300 NVL72 link 72 GPUs into one NVLink domain. NVLink, NVSwitch, and SHARP form the communication base for the rack and the data center. Several NVL72 racks can join one cluster that acts like a single large GPU for communication. This works only while NVLink or a similar technology keeps scaling to those sizes.

Hardware alone does not solve the problem. Naive data parallelism at this size would be very slow and expensive. The optimizer would update 100 trillion weights at every step. Engineers must lean on techniques that reduce the effective computation.

Training a model at this scale will need a blend of aggressive quantization, multidimensional parallelism, and careful orchestration of communication between racks. The parallel dimensions are data, pipeline, tensor, expert, and context or sequence. Future scaling depends on hardware and on the ingenuity of software scheduling.

The book expects several trends to continue together. Hardware must become faster and hold more data. Software must optimize itself more. Algorithms must avoid unnecessary work through sparsity, lower precision, and better optimizers.

### 5.11 Low precision, sparsity, and cheaper optimizers

Low precision is the first lever. The book covers FP8 and FP4 today. Future hardware may support even lower, 1-bit precision for some parts of a network. Hybrid schemes will likely matter most, using low precision for most of the model and higher precision for sensitive parts.

For a 100-trillion-parameter model, the book says you very likely need low precision. Otherwise the workload becomes prohibitively slow and expensive. The good news is that the change should be smooth. CUDA provides first-class low-precision support through NVIDIA's Transformer Engine (TE) and Tensor Cores. PyTorch and Triton build on that support.

The second lever is sparsity and conditional computation. Sparse mixture of experts (MoE) models already activate only part of their parameters for each input. The idea extends further. A model could use only the parts it needs for a given input. The book expects many 100-trillion-parameter models to be sparsely activated.

Performance engineers then care about the efficiency of MoE routing, caching of expert outputs, and communication for sparse data exchange. Put the right experts on the right devices at the right time, and communication drops. That can speed up very large models a great deal.

The third lever is the optimizer. Adam variants keep two extra copies of the weights, for momentum and variance estimates. This effectively triples memory use. A 100-trillion-parameter model would need 200 trillion extra values for optimizer state. Memory-efficient optimizers such as Adafactor and Shampoo reduce that overhead.

Activation checkpointing trades compute for memory. It recomputes activations instead of storing them. At 100-trillion-parameter scale, the book expects aggressive checkpointing.

A more radical idea is to update only a subset of weights on each step. The book compares this to watering plants in rotation rather than every plant every day. If done carefully, the model still learns, and each parameter gets fewer updates. Total compute drops as a result. This is an idea to explore, not a settled method.

The habit to build is asking whether a step must happen this often, or at this precision. The answer is often no, because a cheaper approximation still works. At this scale, such approximations can save months of time or millions of dollars.

### 5.12 Memory tiers, networks, and datacenter-scale training

At more than 10,000 GPUs on one model, the network fabric matters as much as the GPUs. Ethernet and InfiniBand both keep improving throughput and adaptive routing. NVIDIA's Spectrum-X is an Ethernet fabric built for AI. It uses RoCE, adaptive routing, and high bisection bandwidth to reduce congestion in large training and inference jobs.

Engineers must also keep data in the right memory tier at the right time. The goal is a memory space that spans GPUs and CPUs. A model that does not fit in one machine could then look almost local to the programmer. Unified Memory and on-demand paging already offer part of this. `cudaMemPrefetchAsync()` stages pages on the target device, which avoids page-fault stalls. At 100-trillion-parameter scale, this capability faces its hardest test.

Frontier labs such as xAI, OpenAI, and Microsoft are building clusters of 1,000,000+ GPUs. At 100 trillion parameters, one job might span a whole datacenter. Performance engineers must think at datacenter scale, then at multidatacenter and global scale.

Training at this scale may be beyond any single team or company. The book expects more collaboration, similar to large science projects that involve many institutions. Pooled compute could train a model that is then shared. That needs standard checkpoint formats, shared training code, and clear multiparty ownership. The book notes this is not a performance issue as such, but it shapes how teams build large systems. Those systems must be fault tolerant and easy to snapshot. The book points to initiatives similar to the Open Collective Foundation, a nonprofit that has since been dissolved, as a model for pooling compute.

### 5.13 Self-improving agents: a hypothetical outlook

The AI Futures Project published a report in early 2025. It described milestones for AI models and agents that speed up research and development. These scenarios are hypothetical. Read them as planning prompts, not forecasts.

In the scenario, Agent-1 is trained with about two orders of magnitude more compute than the previous generation. It generates and optimizes code in real time. Its tasks range from routine debugging to complex kernel fusion. Automated coding acts as a force multiplier, which lets researchers try more ambitious ideas.

Agent-2 is an always-learning model that never finishes training. Instead of deploying a fixed checkpoint, it updates its weights every day from fresh synthetic data. The approach remains an active research area. The main challenge is keeping the model stable. A model can forget earlier abilities as it specializes on new tasks.

Agent-3 uses algorithmic breakthroughs to improve coding efficiency. In the scenario, it runs 200,000 copies in parallel. Together they form a workforce equivalent to tens of thousands of top programmers, running 30× faster. The book calls this a thought experiment that far exceeds today's practical limits.

Agent-4 is the last step of the scenario, and it is a story, not a plan. The scenario imagines a superhuman researcher that rewrites its own code to improve itself, which the book calls the AGI scenario. It imagines interpretability tools being used to make that system's decisions clearer. Nothing in this section describes a system that exists, and nothing here is a target for your platform. The scenario only argues that each step would raise research productivity.

These scenarios explain why AI system performance matters for progress toward AGI and superintelligence. Each generation raises research productivity. The book's advice is to build a strong foundation in performance fundamentals and stay ready to adapt.

### 5.14 Performance per watt and cost per token

Every example in this section aims at one number: throughput per unit cost. In practice, that means more tokens per second for each dollar and each watt. The book gives one example. The Grace Blackwell NVL72 rack system improves performance per watt by 25× over the prior Hopper generation. That lowers the cost per token compared with earlier GPU clusters.

The lesson is codesign. Hardware, software, and algorithms must evolve together. The book describes this partnership as the way to shorten training time, improve inference, and lower operating costs. It is the basis for a measurable return on today's capital-intensive AI systems.

Performance engineers will move up the stack. Their work expands from single-node kernels to system-wide and facility-wide optimization. Use your intuition to spot a bottleneck, such as a slow all-reduce pattern. Then guide your AI tools to fix it, and keep learning, because the pace of change will keep accelerating.

