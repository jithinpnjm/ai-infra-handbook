# Coverage: ai-systems-performance-engineering

Status values: `todo` · `covered` (name the section) · `moved` (name the chapter) · `skipped` (reason) · `gap-doc`.
Every row must leave `todo` before the mapped chapters are marked reviewed.


## ASP Appendix. AI Systems Performance Checklist (175+ items)  (`app01.xhtml`)
**Target handbook chapters:** 11.3 master checklist + a short checklist at the end of every related chapter

| Source heading | Status | Where covered / note |
|---|---|---|
| **Appendix. AI Systems Performance Checklist (175+ Items)** | todo | |
| **Performance Tuning and Cost Optimization Mindset** | todo | |
| **Reproducibility and Documentation Best Practices** | todo | |
| **System Architecture and Hardware Planning** | todo | |
| **Unified CPU-GPU “Superchip” Architecture** | todo | |
| **Multi-GPU Scaling and Interconnect Optimizations** | todo | |
| **Operating System and Driver Optimizations** | todo | |
| **GPU Resource Management and Scheduling** | todo | |
| **I/O Optimization** | todo | |
| **Data Processing Pipelines** | todo | |
| **Performance Profiling, Debugging, and Monitoring** | todo | |
| **GPU Programming and CUDA Tuning Optimizations** | todo | |
| **Kernel Scheduling and Execution Optimizations** | todo | |
| **Arithmetic Optimizations and Reduced/Mixed Precision** | todo | |
| **Advanced Tuning Strategies and Algorithmic Tricks** | todo | |
| **Distributed Training and Network Optimization** | todo | |
| **Efficient Inference and Serving** | todo | |
| **Multinode Inference and Serving** | todo | |
| **Power and Thermal Management** | todo | |
| **Conclusion** | todo | |

## ASP 1. Introduction and AI System Overview  (`ch01.xhtml`)
**Target handbook chapters:** 0.1, 7.4a, 11.3 (mindset, goodput, cost)

| Source heading | Status | Where covered / note |
|---|---|---|
| **Chapter 1. Introduction and AI System Overview** | todo | |
| **The AI Systems Performance Engineer** | todo | |
| Benchmarking and Profiling | todo | |
| Scaling Distributed Training and Inference | todo | |
| Managing Resources Efficiently | todo | |
| Cross-Team Collaboration | todo | |
| Transparency and Reproducibility | todo | |
| **DeepSeek Scales to ~680-Billion Parameter Models Despite US Export Hardware Restrictions in China** | todo | |
| **Toward 100-Trillion-Parameter Models** | todo | |
| **NVIDIA’s “AI Supercomputer in a Rack”** | todo | |
| **Mechanical Sympathy: Hardware-Software Codesign** | todo | |
| **Measuring “Goodput” Useful Throughput** | todo | |
| **Book Roadmap and Methodology** | todo | |
| **Key Takeaways** | todo | |
| **Conclusion** | todo | |

## ASP 2. AI System Hardware Overview  (`ch02.xhtml`)
**Target handbook chapters:** 7.1c, 7.4 (Grace Blackwell, NVL72, NVLink, precision)

| Source heading | Status | Where covered / note |
|---|---|---|
| **Chapter 2. AI System Hardware Overview** | todo | |
| **The CPU and GPU Superchip** | todo | |
| NVIDIA Grace CPU | todo | |
| NVIDIA Blackwell “Dual-Die” GPU | todo | |
| NVIDIA GPU Tensor Cores and Transformer Engine | todo | |
| Streaming Multiprocessor, Threads, and Warps | todo | |
| **Ultrascale Networking Treating Many GPUs as One** | todo | |
| NVLink and NVSwitch | todo | |
| Multi-GPU Programming | todo | |
| In-Network Aggregations with NVIDIA SHARP | todo | |
| Multirack and Storage Communication | todo | |
| Preintegrated Rack Appliance | todo | |
| Co-Packaged Optics: Future of Networking Hardware | todo | |
| **Compute Density and Power Requirements** | todo | |
| **Liquid Cooling Versus Air Cooling** | todo | |
| **Performance Monitoring and Utilization in Practice** | todo | |
| **Sharing and Scheduling** | todo | |
| **ROI of Upgrading Your Hardware** | todo | |
| **A Glimpse into the Future: NVIDIA’s Roadmap** | todo | |
| Blackwell Ultra and Grace Blackwell Ultra | todo | |
| Vera Rubin Superchip (2026) | todo | |
| Rubin Ultra and Vera Rubin Ultra (2027) | todo | |
| Feynman GPU (2028) and Doubling Something Every Year | todo | |
| **Key Takeaways** | todo | |
| **Conclusion** | todo | |

## ASP 3. OS, Docker and Kubernetes Tuning for GPU Environments  (`ch03.xhtml`)
**Target handbook chapters:** 1.9, 1.7, 5.1, 7.3, 7.6a-h, 7.9 (host tuning, containers, K8s GPU)

| Source heading | Status | Where covered / note |
|---|---|---|
| **Chapter 3. OS, Docker, and Kubernetes Tuning for GPU-Based Environments** | todo | |
| **Operating System** | todo | |
| **NVIDIA Software Stack** | todo | |
| GPU Driver | todo | |
| CUDA Toolkit and Runtime | todo | |
| CUDA Forward and Backward Compatibility Across GPU Hardware Generations | todo | |
| C++ and Python CUDA Libraries | todo | |
| PyTorch and Higher-Level AI Frameworks | todo | |
| **Configuring the CPUs and OS for GPU Environments** | todo | |
| NUMA Awareness and CPU Pinning | todo | |
| NUMA-Friendly Memory Allocation and Memory Pinning | todo | |
| Transparent Hugepages | todo | |
| Scheduler and Interrupt Affinity | todo | |
| Virtual Memory and Swapping | todo | |
| Filesystem Caching and Write-Back | todo | |
| CPU Frequency and C-states | todo | |
| Tune Host CPU Memory Allocator | todo | |
| **GPU Driver and Runtime Settings for Performance** | todo | |
| GPU Persistence Mode | todo | |
| MPS | todo | |
| MIG | todo | |
| GPU Clock Speeds and ECC | todo | |
| GPU Memory Oversubscription, Fragmentation, and Out-of-Memory Handling | todo | |
| **Container Runtime Optimizations for GPUs** | todo | |
| NVIDIA Container Toolkit and CUDA Compatibility | todo | |
| NVIDIA Container Runtime | todo | |
| Avoiding Container Overlay Filesystem Overhead | todo | |
| Reduce Image Size for Faster Container Startup | todo | |
| **Kubernetes for Topology-Aware Container Orchestration and Networking** | todo | |
| Orchestrating Containers with Kubernetes Topology Manager | todo | |
| Job Scheduling with Kubernetes and SLURM | todo | |
| Slicing a GPU with MIG | todo | |
| Optimizing Network Communication for Kubernetes | todo | |
| Reducing Kubernetes Orchestration Jitter | todo | |
| Improving Resource Guarantees | todo | |
| Memory Isolation and Avoiding the OOM Killer | todo | |
| Dealing with I/O Isolation | todo | |
| **Key Takeaways** | todo | |
| **Conclusion** | todo | |

## ASP 4. Tuning Distributed Networking Communication  (`ch04.xhtml`)
**Target handbook chapters:** 8.6a-c NCCL series, 8.1-8.3, 2.5c (NIC and socket tuning)

| Source heading | Status | Where covered / note |
|---|---|---|
| **Chapter 4. Tuning Distributed Networking Communication** | todo | |
| **Overlapping Communication and Computation (Pipelining)** | todo | |
| Asynchronous Execution with Streams | todo | |
| Reducing Communication Frequency and Volume | todo | |
| Achieving Maximal Overlap in Practice | todo | |
| **NVIDIA Magnum IO Optimization Stack** | todo | |
| **High-Speed, Low-Overhead Data Transfers with RDMA** | todo | |
| Tuning Multinode Connectivity | todo | |
| Multinode Communication Pitfalls | todo | |
| &nbsp;&nbsp;Pitfall #1: Using a CPU-bound Gloo backend instead of NCCL | todo | |
| &nbsp;&nbsp;Pitfall #2: Mismatched NCCL versions | todo | |
| &nbsp;&nbsp;Pitfall #3: TCP port exhaustion during NCCL bootstrap | todo | |
| &nbsp;&nbsp;Pitfall #4: Insufficient network bandwidth or misconfigured NICs | todo | |
| &nbsp;&nbsp;Pitfall #5: Straggler nodes or processes | todo | |
| &nbsp;&nbsp;Pitfall #6: GPU memory fragmentation under UCX/RDMA | todo | |
| **NCCL for Distributed Multi-GPU Communication** | todo | |
| Topology Awareness in NCCL | todo | |
| NCCL Communication Algorithms | todo | |
| Distributed Data Parallel Strategies | todo | |
| NCCL Communicator Lifecycle and Environment Gotchas | todo | |
| &nbsp;&nbsp;Pitfall #1: Creating NCCL communicators too often | todo | |
| &nbsp;&nbsp;Pitfall #2: Do not create and destroy NCCL communicators on every iteration | todo | |
| &nbsp;&nbsp;Pitfall #3: Avoid overtuning or disabling NCCL features with environment variables | todo | |
| &nbsp;&nbsp;&nbsp;&nbsp;NCCL_NSOCKS_PERTHREAD and NCCL_SOCKET_NTHREADS (Socket/TCP transports) | todo | |
| &nbsp;&nbsp;&nbsp;&nbsp;NCCL_MIN_NCHANNELS and NCCL_MAX_NCHANNELS | todo | |
| &nbsp;&nbsp;&nbsp;&nbsp;NCCL_TOPO_FILE | todo | |
| &nbsp;&nbsp;&nbsp;&nbsp;NCCL_MNNVL_ENABLE | todo | |
| &nbsp;&nbsp;&nbsp;&nbsp;NCCL_SHARP_DISABLE | todo | |
| &nbsp;&nbsp;Pitfall #4: Verify CPU-GPU NUMA-node affinity for NCCL threads | todo | |
| &nbsp;&nbsp;Pitfall #5: Resist the temptation to ignore NCCL warnings and errors | todo | |
| &nbsp;&nbsp;Pitfall #6: NCCL communicator hangs, errors, or shuts down completely | todo | |
| Profiling and Debugging NCCL | todo | |
| In-Network SHARP Aggregation | todo | |
| Persistent NCCL User Buffers and Zero-Copy Registration | todo | |
| **NVIDIA’s NIXL and Disaggregated Inference** | todo | |
| Separate Prefill and Decode Inference Stages | todo | |
| Intelligent Interconnect Routing for KV Cache Transfers | todo | |
| NIXL Asynchronous API with Callbacks | todo | |
| KV Cache Offloading with NIXL | todo | |
| NIXL and High-Performance Inference Systems Like NVIDIA Dynamo | todo | |
| NCCL Versus NIXL | todo | |
| **Key Takeaways** | todo | |
| **Conclusion** | todo | |

## ASP 5. GPU-Based Storage I/O Optimizations  (`ch05.xhtml`)
**Target handbook chapters:** 6.6a-e storage series, GPUDirect Storage chapter, 9.3 data loading

| Source heading | Status | Where covered / note |
|---|---|---|
| **Chapter 5. GPU-Based Storage I/O Optimizations** | todo | |
| **Fast Storage and Data Locality** | todo | |
| **Sequential Versus Random Read Patterns** | todo | |
| **Tuning NVMe and Filesystem for Throughput** | todo | |
| **Using NVIDIA GDS** | todo | |
| **Checkpointing GPU State with cuda-checkpoint** | todo | |
| **Measuring GDS with gdsio** | todo | |
| **DeepSeek’s Fire-Flyer File System** | todo | |
| **Distributed, Parallel Filesystems and Object Stores** | todo | |
| **Tuning, Replicating, and Compressing Data** | todo | |
| **Monitoring Storage I/O** | todo | |
| **Tuning the Data Pipeline** | todo | |
| Efficient Data Loading and Preprocessing | todo | |
| Scaling Out Workers as You Scale Out Number of GPUs | todo | |
| Multimodal Data Processing with NVIDIA DALI | todo | |
| Creating High-Quality LLM Datasets with NVIDIA NeMo Curator | todo | |
| **Continuous Profiling and Tuning Workflow** | todo | |
| **Diagnosing Communication- Versus Compute-Bound Workloads** | todo | |
| **Key Takeaways** | todo | |
| **Conclusion** | todo | |

## ASP 6. GPU Architecture, CUDA Programming and Maximizing Occupancy  (`ch06.xhtml`)
**Target handbook chapters:** 7.1a, 7.2a-b

| Source heading | Status | Where covered / note |
|---|---|---|
| **Chapter 6. GPU Architecture, CUDA Programming, and Maximizing Occupancy** | todo | |
| **Understanding GPU Architecture** | todo | |
| Threads, Warps, Blocks, and Grids | todo | |
| Choosing Threads-per-Block and Blocks-per-Grid Sizes | todo | |
| CUDA GPU Backward and Forward Compatibility Model | todo | |
| **CUDA Programming Refresher** | todo | |
| Configuring Launch Parameters: Blocks per Grid and Threads per Block | todo | |
| 2D and 3D Kernel Inputs | todo | |
| Asynchronous Memory Allocation and Memory Pools | todo | |
| Understanding GPU Memory Hierarchy | todo | |
| Unified Memory | todo | |
| Maintaining High Occupancy and GPU Utilization | todo | |
| Tuning Occupancy with Launch Bounds | todo | |
| **Debugging Functional Correctness with NVIDIA Compute Sanitizer** | todo | |
| **Roofline Model: Compute-Bound or Memory-Bound Workloads** | todo | |
| **Key Takeaways** | todo | |
| **Conclusion** | todo | |

## ASP 7. Profiling and Tuning GPU Memory Access Patterns  (`ch07.xhtml`)
**Target handbook chapters:** 7.2c, 7.8a

| Source heading | Status | Where covered / note |
|---|---|---|
| **Chapter 7. Profiling and Tuning GPU Memory Access Patterns** | todo | |
| **Coalesced Versus Uncoalesced Global Memory Access** | todo | |
| **Vectorized Memory Access** | todo | |
| **Tiling and Data Reuse Using Shared Memory** | todo | |
| **Avoid Shared-Memory Bank Conflicts** | todo | |
| **Warp Shuffle Intrinsics: Avoid Shared Memory and Explicit Synchronization** | todo | |
| **Read-Only Data Caches** | todo | |
| **Asynchronous Memory Prefetching and Tensor Memory Accelerator** | todo | |
| **Key Takeaways** | todo | |
| **Conclusion** | todo | |

## ASP 8. Occupancy Tuning, Warp Efficiency and ILP  (`ch08.xhtml`)
**Target handbook chapters:** 7.2d

| Source heading | Status | Where covered / note |
|---|---|---|
| **Chapter 8. Occupancy Tuning, Warp Efficiency, and Instruction-Level Parallelism** | todo | |
| **Profiling and Diagnosing GPU Bottlenecks** | todo | |
| Nsight Systems Timeline View | todo | |
| Profiling and Tuning the Data Pipeline | todo | |
| Nsight Compute and Roofline Analysis | todo | |
| PyTorch Profiler and Visualization Tools | todo | |
| Profiler-Guided Analysis | todo | |
| **Analyzing Warp Stall Reasons with Nsight Compute** | todo | |
| Memory-Related Stalls | todo | |
| Execution-Dependency Stalls | todo | |
| Execution Unit Contention | todo | |
| Other Stall Reasons | todo | |
| **Inspecting Achieved Occupancy and GPU Utilization** | todo | |
| Kernel Memory Throughput Versus Peak HBM Memory Bandwidth | todo | |
| Kernel Compute Throughput Versus Peak GPU FLOPS | todo | |
| Iteratively Profiling and Determining the Kernel Bottleneck | todo | |
| Optimizing the Kernel | todo | |
| **Tuning Occupancy** | todo | |
| Find the Right Occupancy for Your Workload | todo | |
| Techniques for Occupancy Tuning | todo | |
| Compiler Hints to Optimize Occupancy | todo | |
| Determine Optimal Launch Configuration with the Occupancy API | todo | |
| Tuning Occupancy with PyTorch | todo | |
| **Improving Warp Execution Efficiency (Warp Divergence)** | todo | |
| Causes of Warp Divergence | todo | |
| Techniques to Avoid Warp Divergence | todo | |
| Profiling and Detecting Warp Divergence | todo | |
| Using Predication to Minimize Divergence | todo | |
| Efficient Intrawarp Communication with Warp Intrinsics | todo | |
| PyTorch Considerations for Warp-Level Efficiency | todo | |
| **Exposing Instruction-Level Parallelism** | todo | |
| Warp Scheduling and Dual Issue Instructions | todo | |
| ILP and Occupancy | todo | |
| Loop Unrolling, Interleaving, and Compiler Hinting | todo | |
| Profiling and Mitigating Register Pressure | todo | |
| **Key Takeaways** | todo | |
| **Conclusion** | todo | |

## ASP 9. Increasing CUDA Kernel Efficiency and Arithmetic Intensity  (`ch09.xhtml`)
**Target handbook chapters:** 7.1b roofline, 7.2e

| Source heading | Status | Where covered / note |
|---|---|---|
| **Chapter 9. Increasing CUDA Kernel Efficiency and Arithmetic Intensity** | todo | |
| **Multilevel Microtiling and Software Prefetching** | todo | |
| **Tiling with Thread Block Clusters** | todo | |
| **Kernel Fusion** | todo | |
| **Structured Sparsity** | todo | |
| **Recomputation Versus Memory Trade-Off** | todo | |
| **PyTorch and Arithmetic Intensity** | todo | |
| **Mixed Precision and Utilizing Tensor Cores** | todo | |
| Feeding Tensor Cores with TMEM and TMA | todo | |
| TF32 and Automatic Mixed Precision (PyTorch) | todo | |
| BF16/FP16, FP8, and FP4 Reduced Precision | todo | |
| INT8 Reduced Precision and DP4A Instructions for Inference | todo | |
| Transformer Engine and TMEM in Depth | todo | |
| **Using CUTLASS for Optimal Arithmetic Intensity and Tensor Core Performance** | todo | |
| **Inline PTX and SASS Tuning for Microoptimizations** | todo | |
| **DeepSeek’s Use of Inline PTX for Memory Allocation Optimization** | todo | |
| **Key Takeaways** | todo | |
| **Conclusion** | todo | |

## ASP 10. Intra-Kernel Pipelining, Warp Specialization, Thread Block Clusters  (`ch10.xhtml`)
**Target handbook chapters:** 7.2f (advanced)

| Source heading | Status | Where covered / note |
|---|---|---|
| **Chapter 10. Intra-Kernel Pipelining, Warp Specialization, and Cooperative Thread Block Clusters** | todo | |
| **Intra-Kernel Pipelining Techniques** | todo | |
| Cooperative Tiling and Double-Buffering with the CUDA Pipeline API | todo | |
| Warp Specialization and the Producer-Consumer Model | todo | |
| Using CUDA Pipeline API for Warp Specialization | todo | |
| PyTorch, CUDA Pipeline API, and Warp Specialization | todo | |
| **Persistent Kernels and Megakernels** | todo | |
| Common Workloads for Persistent Kernels | todo | |
| Megakernels for Inference | todo | |
| Persistent Kernels and Warp Specialization | todo | |
| **Cooperative Groups** | todo | |
| Cooperative Grid Synchronization and Persistent Kernels | todo | |
| When to Combine Persistent Kernels and Cooperative Groups | todo | |
| **Thread Block Clusters and Distributed Shared Memory** | todo | |
| Thread Block Swizzling | todo | |
| Distributed Shared Memory | todo | |
| Scratch Memory | todo | |
| Launching a Thread Block Cluster | todo | |
| Coordinating Thread Block Clusters with Cooperative Groups API | todo | |
| Thread Block Pair | todo | |
| **Reducing Global Memory Traffic with Thread Block Clusters** | todo | |
| **Designing Efficient Algorithms with Thread Block Clusters** | todo | |
| **Warp Specialization with Thread Block Clusters** | todo | |
| **Key Takeaways** | todo | |
| **Conclusion** | todo | |

## ASP 11. Inter-Kernel Pipelining, Synchronization, Stream-Ordered Allocation  (`ch11.xhtml`)
**Target handbook chapters:** 7.2g

| Source heading | Status | Where covered / note |
|---|---|---|
| **Chapter 11. Inter-Kernel Pipelining, Synchronization, and CUDA Stream-Ordered Memory Allocations** | todo | |
| **Overlapping Kernel Execution with CUDA Streams** | todo | |
| **Using Streams to Overlap Compute with Data Transfers** | todo | |
| **Stream-Ordered Memory Allocator** | todo | |
| **Using CUDA Streams and Stream-Ordered Memory Allocator with LLMs** | todo | |
| **Legacy Default Stream** | todo | |
| **Modern Per-Thread Default Stream** | todo | |
| **Default Versus Explicit (Nondefault) Streams** | todo | |
| **Best Practices for Default Stream Usage** | todo | |
| **Fine-Grained Synchronization with Events and Callbacks** | todo | |
| **Using CUDA Events for Cross-Stream Synchronization** | todo | |
| **Pipelining with Warp Specialization (Intra-Kernel) and CUDA Streams (Inter-Kernel)** | todo | |
| **Warp Specialization with Thread Block Clusters and CUDA Streams** | todo | |
| **Multi-GPU Compute and Data Transfer Overlap with CUDA Streams** | todo | |
| **Programmatic Dependent Launch** | todo | |
| **Combining PDL and Thread Block Clusters with Warp Specialization** | todo | |
| **Key Takeaways** | todo | |
| **Conclusion** | todo | |

## ASP 12. Dynamic Scheduling, CUDA Graphs, Device-Initiated Orchestration  (`ch12.xhtml`)
**Target handbook chapters:** 7.2h

| Source heading | Status | Where covered / note |
|---|---|---|
| **Chapter 12. Dynamic Scheduling, CUDA Graphs, and Device-Initiated Kernel Orchestration** | todo | |
| **Dynamic Scheduling with Atomic Work Queues** | todo | |
| Atomic Counters | todo | |
| Atomic Queues | todo | |
| **CUDA Graphs** | todo | |
| PyTorch, Inference Engines, and CUDA Graphs | todo | |
| Memory Pools for CUDA Graphs | todo | |
| Capturing a CUDA Graph with a CUDA Stream | todo | |
| Dynamic Graph Update | todo | |
| Device-Initiated CUDA Graph Launch | todo | |
| Atomic Queues and Device-Initiated CUDA Graphs for In-Kernel Persistent Scheduling | todo | |
| Conditional Graph Nodes | todo | |
| **Dynamic Parallelism** | todo | |
| **Orchestrate Across Multiple GPUs and Cluster Nodes (NVSHMEM)** | todo | |
| Fine-Grained GPU-to-GPU Memory Sharing with NVSHMEM | todo | |
| Capturing Multi-GPU Collectives with NCCL and CUDA Graphs | todo | |
| Pattern for N-GPU Scaling | todo | |
| **Roofline-Guided Scheduling and Orchestration Decisions** | todo | |
| **Key Takeaways** | todo | |
| **Conclusion** | todo | |

## ASP 13. Profiling, Tuning and Scaling PyTorch  (`ch13.xhtml`)
**Target handbook chapters:** 9.4, 9.5, 7.8b (PyTorch profiling, DDP/FSDP scaling)

| Source heading | Status | Where covered / note |
|---|---|---|
| **Chapter 13. Profiling, Tuning, and Scaling PyTorch** | todo | |
| **NVTX Markers and Profiling Tools** | todo | |
| **Profiling PyTorch to Identify Bottlenecks** | todo | |
| Using PyTorch Profiler | todo | |
| System Profiling with Nsight Systems and NVTX Timelines | todo | |
| Kernel Roofline Analysis for General Matrix Multiply (GEMM) | todo | |
| CPU and GPU Profiling with Linux perf | todo | |
| **PyTorch Compiler (torch.compile)** | todo | |
| Using the PyTorch Compiler | todo | |
| Compiling Versus Writing Custom Kernels | todo | |
| Compilation Modes and Trade-Offs in Speed, Memory, and Compile Time | todo | |
| Regional Compilation | todo | |
| Profiling and Debugging Compiler Performance Issues | todo | |
| **PyTorch Optimized Attention Mechanisms** | todo | |
| **PyTorch Architecture Optimization (torchao), Quantization, Sparsity, and Pruning** | todo | |
| **Concurrency with CUDA Streams** | todo | |
| Overlapping Communication and Computation | todo | |
| Stream Synchronization with Events | todo | |
| Using CUDA Streams with MoE Models | todo | |
| **Reducing Kernel Launch Overhead with CUDA Graphs** | todo | |
| Capturing a CUDA Graph and Preallocating Memory | todo | |
| Replaying the Graph | todo | |
| Best Practices for CUDA Graphs | todo | |
| CUDA Graph Trees (PyTorch Compiler Internal) | todo | |
| **Profiling and Tuning Memory in PyTorch** | todo | |
| Tuning the CUDA Memory Allocator | todo | |
| Activation Checkpointing for Memory Savings | todo | |
| Offloading Parameters to CPU and NVMe | todo | |
| SuperOffload: Optimized CPU-GPU Superchip Offload | todo | |
| FSDP Automatic Checkpointing and Offloading | todo | |
| Combining FSDP with Tensor Parallel and Pipeline Parallel | todo | |
| Pluggable Memory Allocators and Cross-GPU Data Transfers | todo | |
| Enabling Peer-to-Peer DMA and UCX | todo | |
| **PyTorch Symmetric Memory** | todo | |
| **Optimizing the Data Input Pipeline** | todo | |
| **Scaling with PyTorch Distributed** | todo | |
| DDP with torch.compile | todo | |
| FSDP with torch.compile | todo | |
| Tensor and Pipeline Parallelism with torch.compile | todo | |
| TorchTitan, AsyncTP, AutoParallel, and SimpleFSDP | todo | |
| Multi-GPU Profiling with HTA | todo | |
| **Continuous Integration and Performance Benchmarking** | todo | |
| PyTorch HUD Performance Dashboard | todo | |
| Performance Benchmarks and MLPerf Logging | todo | |
| **Key Takeaways** | todo | |
| **Conclusion** | todo | |

## ASP 14. PyTorch Compiler, OpenAI Triton, XLA  (`ch14.xhtml`)
**Target handbook chapters:** 9.4c (compilers), 7.2i (Triton)

| Source heading | Status | Where covered / note |
|---|---|---|
| **Chapter 14. PyTorch Compiler, OpenAI Triton, and XLA Backends** | todo | |
| **PyTorch Compiler Deep Dive** | todo | |
| TorchDynamo for Bytecode Capture and Graph Extraction | todo | |
| AOT Autograd Fusion for Forward and Backward Passes | todo | |
| PrimTorch IR (Prims) Simplified Operator Set | todo | |
| TorchInductor Backend Code Generation | todo | |
| Autotuning with TorchInductor | todo | |
| Dynamic Shapes and Variable Sequence Lengths | todo | |
| Disabling the PyTorch Compiler and Reverting Back to Eager Mode | todo | |
| Performance Hints and Debugging Generated Code | todo | |
| Debugging Numerical Correctness and Accuracy | todo | |
| **Explaining and Minimizing Graph Breaks** | todo | |
| Graph Breaks and TorchDynamo explain() | todo | |
| Minimize Graph Recompilations | todo | |
| Mark Functions and Code Blocks as Safe with allow_in_graph | todo | |
| Tips for Handling Graph Breaks | todo | |
| **Debugging Compiler Phases, Graph Breaks, and Performance** | todo | |
| **Writing Custom Kernels with OpenAI Triton** | todo | |
| Triton Programming Model | todo | |
| Accessing Shared Memory in Triton | todo | |
| Registering Custom Kernels with PyTorch | todo | |
| Tuning Kernel-Launch Parameters | todo | |
| Autotuning Triton Kernels | todo | |
| **Advanced Triton Kernel Implementations** | todo | |
| Warp Specialization with Triton | todo | |
| Tiled and Persistent GEMM Kernel (Triton) | todo | |
| Software Pipelining and Double Buffering with Triton | todo | |
| Profiling with Triton Proton Profiler | todo | |
| **PyTorch XLA Backend** | todo | |
| **Key Takeaways** | todo | |
| **Conclusion** | todo | |

## ASP 15. Multinode Inference, Parallelism, Decoding, Routing  (`ch15.xhtml`)
**Target handbook chapters:** 9.9a

| Source heading | Status | Where covered / note |
|---|---|---|
| **Chapter 15. Multinode Inference, Parallelism, Decoding, and Routing Optimizations** | todo | |
| **Disaggregated Prefill and Decode Architecture** | todo | |
| Prefill-Decode Interference | todo | |
| Scaling Prefill and Worker Nodes Independently | todo | |
| Impact on Latency (TTFT) and Throughput (TPOT) | todo | |
| KV Cache Data Transfer and NIXL | todo | |
| Deploying Disaggregated Prefill and Decode with Kubernetes | todo | |
| **Parallelism Strategies for Serving Massive MoE Models** | todo | |
| Tensor Parallelism | todo | |
| Pipeline Parallelism | todo | |
| Expert Parallelism | todo | |
| Data Parallelism | todo | |
| Context (Sequence) Parallelism | todo | |
| Hybrid Parallelism | todo | |
| **Speculative Decoding and Parallel Token Generation Techniques** | todo | |
| Two-Model, Draft-Based Speculative Decoding and EAGLE | todo | |
| Single-Model Self-Speculative Decoding | todo | |
| Multitoken Decoding with Medusa’s Multiple Heads | todo | |
| Interleaving Decode Steps from Multiple Requests | todo | |
| Combining Decoding Techniques and Evaluating Complexity | todo | |
| **Constrained Decoding Performance Implications** | todo | |
| **Dynamic Routing Strategies for MoE Inference** | todo | |
| Expert Communication Optimization | todo | |
| Load Balancing, Capacity Factor, and Expert Replication | todo | |
| Adaptive Expert Routing and Real-Time Monitoring | todo | |
| **Key Takeaways** | todo | |
| **Conclusion** | todo | |

## ASP 16. Profiling, Debugging and Tuning Inference at Scale  (`ch16.xhtml`)
**Target handbook chapters:** 9.10a, 11.2

| Source heading | Status | Where covered / note |
|---|---|---|
| **Chapter 16. Profiling, Debugging, and Tuning Inference at Scale** | todo | |
| **Profiling, Debugging, and Tuning Inference Performance** | todo | |
| Monitoring System Metrics and Counters | todo | |
| Profiling with Nsight Systems and Nsight Compute | todo | |
| Inference Troubleshooting Recipes | todo | |
| Full-Stack Inference Optimizations | todo | |
| Debugging Correctness Issues | todo | |
| **Dynamic Batching, Scheduling, and Routing** | todo | |
| Dynamic Batching | todo | |
| Continuous Batching | todo | |
| Continuous Scheduling | todo | |
| Stall-Free Scheduling (Chunked Prefill) | todo | |
| Latency-Aware Scheduling and Dynamic Routing | todo | |
| **Systems-Level Optimizations** | todo | |
| Overlapping Communication and Computation | todo | |
| Maximizing GPU Utilization and Throughput Versus Latency Trade-Offs | todo | |
| Power and Thermal Constraints | todo | |
| Error Handling | todo | |
| Memory | todo | |
| KV Cache Offloading and Memory Pool Allocation | todo | |
| **Quantization Approaches for Real-Time Inference** | todo | |
| Reducing Precision from FP16 to FP8 and FP4 | todo | |
| Weight-Only Quantization (GPTQ, AWQ) | todo | |
| Activation Quantization | todo | |
| Post-Training Quantization Workflow | todo | |
| Combining Weight and Activation Quantization | todo | |
| Fusing Quantization-Dequantization Steps into the Execution Graph | todo | |
| **Application-Level Optimizations** | todo | |
| Prompt Compression | todo | |
| Prompt Cleansing | todo | |
| Prefix Caching | todo | |
| Model Cascading and Tiered Model Deployment | todo | |
| Streaming Responses | todo | |
| Debouncing and Request Coalescing | todo | |
| Token Output Limits and Timeouts | todo | |
| **Key Takeaways** | todo | |
| **Conclusion** | todo | |

## ASP 17. Scaling Disaggregated Prefill and Decode  (`ch17.xhtml`)
**Target handbook chapters:** 9.9b

| Source heading | Status | Where covered / note |
|---|---|---|
| **Chapter 17. Scaling Disaggregated Prefill and Decode for Inference** | todo | |
| **Why Prefill-Decode Disaggregation?** | todo | |
| Advantages of Disaggregation | todo | |
| &nbsp;&nbsp;Reduced interference | todo | |
| &nbsp;&nbsp;Phase-specific optimizations | todo | |
| Disaggregated Prefill and Decode Cluster Pools | todo | |
| &nbsp;&nbsp;Prefill workers design | todo | |
| &nbsp;&nbsp;&nbsp;&nbsp;Memory management | todo | |
| &nbsp;&nbsp;&nbsp;&nbsp;Optimizing for latency versus throughput | todo | |
| &nbsp;&nbsp;&nbsp;&nbsp;Latency-aware scheduling and batching | todo | |
| &nbsp;&nbsp;Decode workers design | todo | |
| &nbsp;&nbsp;&nbsp;&nbsp;KV cache transfer between prefill and decode | todo | |
| &nbsp;&nbsp;&nbsp;&nbsp;Continuous batching | todo | |
| &nbsp;&nbsp;&nbsp;&nbsp;Grouping variable-length sequences | todo | |
| &nbsp;&nbsp;&nbsp;&nbsp;Memory management for the KV cache | todo | |
| Disaggregated Routing and Scheduling Policies | todo | |
| &nbsp;&nbsp;Routing factors | todo | |
| &nbsp;&nbsp;Example dynamic routing policy in code | todo | |
| &nbsp;&nbsp;Example dynamic routing policy configuration | todo | |
| &nbsp;&nbsp;Capacity-aware routing | todo | |
| &nbsp;&nbsp;Latency-aware routing | todo | |
| &nbsp;&nbsp;Multipath inference (racing) | todo | |
| &nbsp;&nbsp;Multibranch, parallel speculative decoding across workers | todo | |
| &nbsp;&nbsp;QoS and early rejection policies | todo | |
| Scalability of Disaggregated Prefill and Decode | todo | |
| **Key Takeaways** | todo | |
| **Conclusion** | todo | |

## ASP 18. Advanced Prefill-Decode and KV Cache Tuning  (`ch18.xhtml`)
**Target handbook chapters:** 9.9c

| Source heading | Status | Where covered / note |
|---|---|---|
| **Chapter 18. Advanced Prefill-Decode and KV Cache Tuning** | todo | |
| **Optimized Decode Kernels** | todo | |
| FlashMLA (DeepSeek) | todo | |
| ThunderMLA (Stanford) | todo | |
| FlexDecoding (PyTorch) | todo | |
| **Tuning KV Cache Utilization and Management** | todo | |
| Disaggregated KV Cache Pool | todo | |
| KV Cache Reuse and Prefix Sharing | todo | |
| Optimized KV Cache Memory Layout | todo | |
| GPU and CPU-GPU Superchip Improvements | todo | |
| **Fast KV Cache Transfer Between Prefill and Decode** | todo | |
| KV Cache Size | todo | |
| Zero-Copy GPU-to-GPU Transfer | todo | |
| **Connector and Data Path Design** | todo | |
| **Heterogeneous Hardware and Parallelism Strategies for Prefill and Decode** | todo | |
| Compute-Optimized Versus Memory-Optimized Hardware | todo | |
| &nbsp;&nbsp;Throughput and cost benefits | todo | |
| &nbsp;&nbsp;Phase-specific model parallelism | todo | |
| &nbsp;&nbsp;Different precision for prefill and decode | todo | |
| **Hybrid Prefill with GPU-CPU Collaboration** | todo | |
| **SLO-Aware Request Management and Fault Tolerance** | todo | |
| Early Rejection (Admission Control) | todo | |
| Quality of Service | todo | |
| Fault Tolerance | todo | |
| **Dynamic Scheduling and Load Balancing** | todo | |
| Adaptive Resource Scheduling and Hotspot Prevention | todo | |
| &nbsp;&nbsp;TetriInfer’s two-level scheduler | todo | |
| &nbsp;&nbsp;Arrow’s adaptive instance scaling | todo | |
| &nbsp;&nbsp;Mooncake adaptive strategies | todo | |
| &nbsp;&nbsp;Dynamic resource scaling | todo | |
| **Key Takeaways** | todo | |
| **Conclusion** | todo | |

## ASP 19. Dynamic and Adaptive Inference Engine Optimizations  (`ch19.xhtml`)
**Target handbook chapters:** 9.8, 9.9d

| Source heading | Status | Where covered / note |
|---|---|---|
| **Chapter 19. Dynamic and Adaptive Inference Engine Optimizations** | todo | |
| **Adaptive Parallelism Strategies (TP Versus PP Versus Hybrid)** | todo | |
| **Dynamic Precision Changes** | todo | |
| **Kernel Autotuning for Transformer Self-Attention and MLP Paths** | todo | |
| **Dynamic Shared-Memory Allocation and Occupancy-Aware Kernel Selection** | todo | |
| **Speculative KV Prefetching for Faster TTFT** | todo | |
| **Real-Time KV Cache Compression and Policy Switching** | todo | |
| **Reinforcement Learning Agents for Tuning AI Systems at Runtime** | todo | |
| **Dynamic Memory-Allocation Switching (Slab Versus Caching Versus Stream-Ordered)** | todo | |
| **Runtime Kernel Performance Improvements and Hot-Swappable Implementations** | todo | |
| **Continuous Prewarming of CUDA Graphs and Caches Using Time-Series Prediction** | todo | |
| **Adaptive Batching and Chunked Prefill Scheduling** | todo | |
| **Congestion-Aware and Topology-Aware Scheduling with Multiple GPUs** | todo | |
| NVLink/NVSwitch Topology and Bandwidth Constraints | todo | |
| Real-Time Link Telemetry and Monitoring | todo | |
| Adaptive Process-GPU Mapping | todo | |
| Optimizing Collective Communication with NCCL | todo | |
| &nbsp;&nbsp;Ring versus tree all-reduce | todo | |
| &nbsp;&nbsp;Rotating ring endpoints | todo | |
| &nbsp;&nbsp;Wave scheduling of collectives | todo | |
| Multinode and Multirack Communication with GPUDirect RDMA | todo | |
| MoE Expert Rebalancing and Regrouping | todo | |
| Dynamic Congestion-Aware Scheduling | todo | |
| Coordinating NVSwitch Transfers with Fine-Tuned Scheduling | todo | |
| **Additional Adaptive and Dynamic Optimization Techniques** | todo | |
| Dynamic Early-Exit Networks | todo | |
| Input-Aware Layer Skipping (DASH) | todo | |
| Speculative MoE Expert Routing and Communication Reduction | todo | |
| Dynamic Token Pruning with LazyLLM | todo | |
| Edge-Oriented MoE Memory Budgeting | todo | |
| Dynamic Quantization and Activation Range Adjustment | todo | |
| **Key Takeaways** | todo | |
| **Conclusion** | todo | |

## ASP 20. AI-Assisted Performance Optimizations, Toward Multimillion GPU Clusters  (`ch20.xhtml`)
**Target handbook chapters:** 11.3, 12.x

| Source heading | Status | Where covered / note |
|---|---|---|
| **Chapter 20. AI-Assisted Performance Optimizations and Scaling Toward Multimillion GPU Clusters** | todo | |
| **AlphaTensor AI-Discovered Algorithms Boosting GPU Performance (Google DeepMind)** | todo | |
| Automated GPU Kernel Optimizations with DeepSeek-R1 (NVIDIA) | todo | |
| Reinforcement Learning Approach to Generating Optimized GPU Kernels (Predibase) | todo | |
| Self-Improving AI Agents (AI Futures Project) | todo | |
| Smart Compilers and Automated Code Optimizations | todo | |
| AI-Assisted Real-Time System Optimizations and Cluster Operations | todo | |
| Scaling Toward Multimillion GPU Clusters and 100-Trillion-Parameter Models | todo | |
| **Key Takeaways** | todo | |
| **Conclusion** | todo | |

Total rows: 550
