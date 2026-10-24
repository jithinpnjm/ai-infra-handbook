# ai-systems-performance-engineering


<!-- file: app01.xhtml -->

## Appendix. AI Systems Performance Checklist (175+ Items)

## Performance Tuning and Cost Optimization Mindset

## Reproducibility and Documentation Best Practices

## System Architecture and Hardware Planning

## Unified CPU-GPU “Superchip” Architecture

## Multi-GPU Scaling and Interconnect Optimizations

## Operating System and Driver Optimizations

## GPU Resource Management and Scheduling

## I/O Optimization

## Data Processing Pipelines

## Performance Profiling, Debugging, and Monitoring

## GPU Programming and CUDA Tuning Optimizations

## Kernel Scheduling and Execution Optimizations

## Arithmetic Optimizations and Reduced/Mixed Precision

## Advanced Tuning Strategies and Algorithmic Tricks

## Distributed Training and Network Optimization

## Efficient Inference and Serving

## Multinode Inference and Serving

## Power and Thermal Management

## Conclusion

<!-- file: ch01.xhtml -->

## Chapter 1. Introduction and AI System Overview

## The AI Systems Performance Engineer
- Benchmarking and Profiling
- Scaling Distributed Training and Inference
- Managing Resources Efficiently
- Cross-Team Collaboration
- Transparency and Reproducibility

## DeepSeek Scales to ~680-Billion Parameter Models Despite US Export Hardware Restrictions in China

## Toward 100-Trillion-Parameter Models

## NVIDIA’s “AI Supercomputer in a Rack”

## Mechanical Sympathy: Hardware-Software Codesign

## Measuring “Goodput” Useful Throughput

## Book Roadmap and Methodology

## Key Takeaways

## Conclusion

<!-- file: ch02.xhtml -->

## Chapter 2. AI System Hardware Overview

## The CPU and GPU Superchip
- NVIDIA Grace CPU
- NVIDIA Blackwell “Dual-Die” GPU
- NVIDIA GPU Tensor Cores and Transformer Engine
- Streaming Multiprocessor, Threads, and Warps

## Ultrascale Networking Treating Many GPUs as One
- NVLink and NVSwitch
- Multi-GPU Programming
- In-Network Aggregations with NVIDIA SHARP
- Multirack and Storage Communication
- Preintegrated Rack Appliance
- Co-Packaged Optics: Future of Networking Hardware

## Compute Density and Power Requirements

## Liquid Cooling Versus Air Cooling

## Performance Monitoring and Utilization in Practice

## Sharing and Scheduling

## ROI of Upgrading Your Hardware

## A Glimpse into the Future: NVIDIA’s Roadmap
- Blackwell Ultra and Grace Blackwell Ultra
- Vera Rubin Superchip (2026)
- Rubin Ultra and Vera Rubin Ultra (2027)
- Feynman GPU (2028) and Doubling Something Every Year

## Key Takeaways

## Conclusion

<!-- file: ch03.xhtml -->

## Chapter 3. OS, Docker, and Kubernetes Tuning for GPU-Based Environments

## Operating System

## NVIDIA Software Stack
- GPU Driver
- CUDA Toolkit and Runtime
- CUDA Forward and Backward Compatibility Across GPU Hardware Generations
- C++ and Python CUDA Libraries
- PyTorch and Higher-Level AI Frameworks

## Configuring the CPUs and OS for GPU Environments
- NUMA Awareness and CPU Pinning
- NUMA-Friendly Memory Allocation and Memory Pinning
- Transparent Hugepages
- Scheduler and Interrupt Affinity
- Virtual Memory and Swapping
- Filesystem Caching and Write-Back
- CPU Frequency and C-states
- Tune Host CPU Memory Allocator

## GPU Driver and Runtime Settings for Performance
- GPU Persistence Mode
- MPS
- MIG
- GPU Clock Speeds and ECC
- GPU Memory Oversubscription, Fragmentation, and Out-of-Memory Handling

## Container Runtime Optimizations for GPUs
- NVIDIA Container Toolkit and CUDA Compatibility
- NVIDIA Container Runtime
- Avoiding Container Overlay Filesystem Overhead
- Reduce Image Size for Faster Container Startup

## Kubernetes for Topology-Aware Container Orchestration and Networking
- Orchestrating Containers with Kubernetes Topology Manager
- Job Scheduling with Kubernetes and SLURM
- Slicing a GPU with MIG
- Optimizing Network Communication for Kubernetes
- Reducing Kubernetes Orchestration Jitter
- Improving Resource Guarantees
- Memory Isolation and Avoiding the OOM Killer
- Dealing with I/O Isolation

## Key Takeaways

## Conclusion

<!-- file: ch04.xhtml -->

## Chapter 4. Tuning Distributed Networking Communication

## Overlapping Communication and Computation (Pipelining)
- Asynchronous Execution with Streams
- Reducing Communication Frequency and Volume
- Achieving Maximal Overlap in Practice

## NVIDIA Magnum IO Optimization Stack

## High-Speed, Low-Overhead Data Transfers with RDMA
- Tuning Multinode Connectivity
- Multinode Communication Pitfalls
  - Pitfall #1: Using a CPU-bound Gloo backend instead of NCCL
  - Pitfall #2: Mismatched NCCL versions
  - Pitfall #3: TCP port exhaustion during NCCL bootstrap
  - Pitfall #4: Insufficient network bandwidth or misconfigured NICs
  - Pitfall #5: Straggler nodes or processes
  - Pitfall #6: GPU memory fragmentation under UCX/RDMA

## NCCL for Distributed Multi-GPU Communication
- Topology Awareness in NCCL
- NCCL Communication Algorithms
- Distributed Data Parallel Strategies
- NCCL Communicator Lifecycle and Environment Gotchas
  - Pitfall #1: Creating NCCL communicators too often
  - Pitfall #2: Do not create and destroy NCCL communicators on every iteration
  - Pitfall #3: Avoid overtuning or disabling NCCL features with environment variables
    - NCCL_NSOCKS_PERTHREAD and NCCL_SOCKET_NTHREADS (Socket/TCP transports)
    - NCCL_MIN_NCHANNELS and NCCL_MAX_NCHANNELS
    - NCCL_TOPO_FILE
    - NCCL_MNNVL_ENABLE
    - NCCL_SHARP_DISABLE
  - Pitfall #4: Verify CPU-GPU NUMA-node affinity for NCCL threads
  - Pitfall #5: Resist the temptation to ignore NCCL warnings and errors
  - Pitfall #6: NCCL communicator hangs, errors, or shuts down completely
- Profiling and Debugging NCCL
- In-Network SHARP Aggregation
- Persistent NCCL User Buffers and Zero-Copy Registration

## NVIDIA’s NIXL and Disaggregated Inference
- Separate Prefill and Decode Inference Stages
- Intelligent Interconnect Routing for KV Cache Transfers
- NIXL Asynchronous API with Callbacks
- KV Cache Offloading with NIXL
- NIXL and High-Performance Inference Systems Like NVIDIA Dynamo
- NCCL Versus NIXL

## Key Takeaways

## Conclusion

<!-- file: ch05.xhtml -->

## Chapter 5. GPU-Based Storage I/O Optimizations

## Fast Storage and Data Locality

## Sequential Versus Random Read Patterns

## Tuning NVMe and Filesystem for Throughput

## Using NVIDIA GDS

## Checkpointing GPU State with cuda-checkpoint

## Measuring GDS with gdsio

## DeepSeek’s Fire-Flyer File System

## Distributed, Parallel Filesystems and Object Stores

## Tuning, Replicating, and Compressing Data

## Monitoring Storage I/O

## Tuning the Data Pipeline
- Efficient Data Loading and Preprocessing
- Scaling Out Workers as You Scale Out Number of GPUs
- Multimodal Data Processing with NVIDIA DALI
- Creating High-Quality LLM Datasets with NVIDIA NeMo Curator

## Continuous Profiling and Tuning Workflow

## Diagnosing Communication- Versus Compute-Bound Workloads

## Key Takeaways

## Conclusion

<!-- file: ch06.xhtml -->

## Chapter 6. GPU Architecture, CUDA Programming, and Maximizing Occupancy

## Understanding GPU Architecture
- Threads, Warps, Blocks, and Grids
- Choosing Threads-per-Block and Blocks-per-Grid Sizes
- CUDA GPU Backward and Forward Compatibility Model

## CUDA Programming Refresher
- Configuring Launch Parameters: Blocks per Grid and Threads per Block
- 2D and 3D Kernel Inputs
- Asynchronous Memory Allocation and Memory Pools
- Understanding GPU Memory Hierarchy
- Unified Memory
- Maintaining High Occupancy and GPU Utilization
- Tuning Occupancy with Launch Bounds

## Debugging Functional Correctness with NVIDIA Compute Sanitizer

## Roofline Model: Compute-Bound or Memory-Bound Workloads

## Key Takeaways

## Conclusion

<!-- file: ch07.xhtml -->

## Chapter 7. Profiling and Tuning GPU Memory Access Patterns

## Coalesced Versus Uncoalesced Global Memory Access

## Vectorized Memory Access

## Tiling and Data Reuse Using Shared Memory

## Avoid Shared-Memory Bank Conflicts

## Warp Shuffle Intrinsics: Avoid Shared Memory and Explicit Synchronization

## Read-Only Data Caches

## Asynchronous Memory Prefetching and Tensor Memory Accelerator

## Key Takeaways

## Conclusion

<!-- file: ch08.xhtml -->

## Chapter 8. Occupancy Tuning, Warp Efficiency, and Instruction-Level Parallelism

## Profiling and Diagnosing GPU Bottlenecks
- Nsight Systems Timeline View
- Profiling and Tuning the Data Pipeline
- Nsight Compute and Roofline Analysis
- PyTorch Profiler and Visualization Tools
- Profiler-Guided Analysis

## Analyzing Warp Stall Reasons with Nsight Compute
- Memory-Related Stalls
- Execution-Dependency Stalls
- Execution Unit Contention
- Other Stall Reasons

## Inspecting Achieved Occupancy and GPU Utilization
- Kernel Memory Throughput Versus Peak HBM Memory Bandwidth
- Kernel Compute Throughput Versus Peak GPU FLOPS
- Iteratively Profiling and Determining the Kernel Bottleneck
- Optimizing the Kernel

## Tuning Occupancy
- Find the Right Occupancy for Your Workload
- Techniques for Occupancy Tuning
- Compiler Hints to Optimize Occupancy
- Determine Optimal Launch Configuration with the Occupancy API
- Tuning Occupancy with PyTorch

## Improving Warp Execution Efficiency (Warp Divergence)
- Causes of Warp Divergence
- Techniques to Avoid Warp Divergence
- Profiling and Detecting Warp Divergence
- Using Predication to Minimize Divergence
- Efficient Intrawarp Communication with Warp Intrinsics
- PyTorch Considerations for Warp-Level Efficiency

## Exposing Instruction-Level Parallelism
- Warp Scheduling and Dual Issue Instructions
- ILP and Occupancy
- Loop Unrolling, Interleaving, and Compiler Hinting
- Profiling and Mitigating Register Pressure

## Key Takeaways

## Conclusion

<!-- file: ch09.xhtml -->

## Chapter 9. Increasing CUDA Kernel Efficiency and Arithmetic Intensity

## Multilevel Microtiling and Software Prefetching

## Tiling with Thread Block Clusters

## Kernel Fusion

## Structured Sparsity

## Recomputation Versus Memory Trade-Off

## PyTorch and Arithmetic Intensity

## Mixed Precision and Utilizing Tensor Cores
- Feeding Tensor Cores with TMEM and TMA
- TF32 and Automatic Mixed Precision (PyTorch)
- BF16/FP16, FP8, and FP4 Reduced Precision
- INT8 Reduced Precision and DP4A Instructions for Inference
- Transformer Engine and TMEM in Depth

## Using CUTLASS for Optimal Arithmetic Intensity and Tensor Core Performance

## Inline PTX and SASS Tuning for Microoptimizations

## DeepSeek’s Use of Inline PTX for Memory Allocation Optimization

## Key Takeaways

## Conclusion

<!-- file: ch10.xhtml -->

## Chapter 10. Intra-Kernel Pipelining, Warp Specialization, and Cooperative Thread Block Clusters

## Intra-Kernel Pipelining Techniques
- Cooperative Tiling and Double-Buffering with the CUDA Pipeline API
- Warp Specialization and the Producer-Consumer Model
- Using CUDA Pipeline API for Warp Specialization
- PyTorch, CUDA Pipeline API, and Warp Specialization

## Persistent Kernels and Megakernels
- Common Workloads for Persistent Kernels
- Megakernels for Inference
- Persistent Kernels and Warp Specialization

## Cooperative Groups
- Cooperative Grid Synchronization and Persistent Kernels
- When to Combine Persistent Kernels and Cooperative Groups

## Thread Block Clusters and Distributed Shared Memory
- Thread Block Swizzling
- Distributed Shared Memory
- Scratch Memory
- Launching a Thread Block Cluster
- Coordinating Thread Block Clusters with Cooperative Groups API
- Thread Block Pair

## Reducing Global Memory Traffic with Thread Block Clusters

## Designing Efficient Algorithms with Thread Block Clusters

## Warp Specialization with Thread Block Clusters

## Key Takeaways

## Conclusion

<!-- file: ch11.xhtml -->

## Chapter 11. Inter-Kernel Pipelining, Synchronization, and CUDA Stream-Ordered Memory Allocations

## Overlapping Kernel Execution with CUDA Streams

## Using Streams to Overlap Compute with Data Transfers

## Stream-Ordered Memory Allocator

## Using CUDA Streams and Stream-Ordered Memory Allocator with LLMs

## Legacy Default Stream

## Modern Per-Thread Default Stream

## Default Versus Explicit (Nondefault) Streams

## Best Practices for Default Stream Usage

## Fine-Grained Synchronization with Events and Callbacks

## Using CUDA Events for Cross-Stream Synchronization

## Pipelining with Warp Specialization (Intra-Kernel) and CUDA Streams (Inter-Kernel)

## Warp Specialization with Thread Block Clusters and CUDA Streams

## Multi-GPU Compute and Data Transfer Overlap with CUDA Streams

## Programmatic Dependent Launch

## Combining PDL and Thread Block Clusters with Warp Specialization

## Key Takeaways

## Conclusion

<!-- file: ch12.xhtml -->

## Chapter 12. Dynamic Scheduling, CUDA Graphs, and Device-Initiated Kernel Orchestration

## Dynamic Scheduling with Atomic Work Queues
- Atomic Counters
- Atomic Queues

## CUDA Graphs
- PyTorch, Inference Engines, and CUDA Graphs
- Memory Pools for CUDA Graphs
- Capturing a CUDA Graph with a CUDA Stream
- Dynamic Graph Update
- Device-Initiated CUDA Graph Launch
- Atomic Queues and Device-Initiated CUDA Graphs for In-Kernel Persistent Scheduling
- Conditional Graph Nodes

## Dynamic Parallelism

## Orchestrate Across Multiple GPUs and Cluster Nodes (NVSHMEM)
- Fine-Grained GPU-to-GPU Memory Sharing with NVSHMEM
- Capturing Multi-GPU Collectives with NCCL and CUDA Graphs
- Pattern for N-GPU Scaling

## Roofline-Guided Scheduling and Orchestration Decisions

## Key Takeaways

## Conclusion

<!-- file: ch13.xhtml -->

## Chapter 13. Profiling, Tuning, and Scaling PyTorch

## NVTX Markers and Profiling Tools

## Profiling PyTorch to Identify Bottlenecks
- Using PyTorch Profiler
- System Profiling with Nsight Systems and NVTX Timelines
- Kernel Roofline Analysis for General Matrix Multiply (GEMM)
- CPU and GPU Profiling with Linux perf

## PyTorch Compiler (torch.compile)
- Using the PyTorch Compiler
- Compiling Versus Writing Custom Kernels
- Compilation Modes and Trade-Offs in Speed, Memory, and Compile Time
- Regional Compilation
- Profiling and Debugging Compiler Performance Issues

## PyTorch Optimized Attention Mechanisms

## PyTorch Architecture Optimization (torchao), Quantization, Sparsity, and Pruning

## Concurrency with CUDA Streams
- Overlapping Communication and Computation
- Stream Synchronization with Events
- Using CUDA Streams with MoE Models

## Reducing Kernel Launch Overhead with CUDA Graphs
- Capturing a CUDA Graph and Preallocating Memory
- Replaying the Graph
- Best Practices for CUDA Graphs
- CUDA Graph Trees (PyTorch Compiler Internal)

## Profiling and Tuning Memory in PyTorch
- Tuning the CUDA Memory Allocator
- Activation Checkpointing for Memory Savings
- Offloading Parameters to CPU and NVMe
- SuperOffload: Optimized CPU-GPU Superchip Offload
- FSDP Automatic Checkpointing and Offloading
- Combining FSDP with Tensor Parallel and Pipeline Parallel
- Pluggable Memory Allocators and Cross-GPU Data Transfers
- Enabling Peer-to-Peer DMA and UCX

## PyTorch Symmetric Memory

## Optimizing the Data Input Pipeline

## Scaling with PyTorch Distributed
- DDP with torch.compile
- FSDP with torch.compile
- Tensor and Pipeline Parallelism with torch.compile
- TorchTitan, AsyncTP, AutoParallel, and SimpleFSDP
- Multi-GPU Profiling with HTA

## Continuous Integration and Performance Benchmarking
- PyTorch HUD Performance Dashboard
- Performance Benchmarks and MLPerf Logging

## Key Takeaways

## Conclusion

<!-- file: ch14.xhtml -->

## Chapter 14. PyTorch Compiler, OpenAI Triton, and XLA Backends

## PyTorch Compiler Deep Dive
- TorchDynamo for Bytecode Capture and Graph Extraction
- AOT Autograd Fusion for Forward and Backward Passes
- PrimTorch IR (Prims) Simplified Operator Set
- TorchInductor Backend Code Generation
- Autotuning with TorchInductor
- Dynamic Shapes and Variable Sequence Lengths
- Disabling the PyTorch Compiler and Reverting Back to Eager Mode
- Performance Hints and Debugging Generated Code
- Debugging Numerical Correctness and Accuracy

## Explaining and Minimizing Graph Breaks
- Graph Breaks and TorchDynamo explain()
- Minimize Graph Recompilations
- Mark Functions and Code Blocks as Safe with allow_in_graph
- Tips for Handling Graph Breaks

## Debugging Compiler Phases, Graph Breaks, and Performance

## Writing Custom Kernels with OpenAI Triton
- Triton Programming Model
- Accessing Shared Memory in Triton
- Registering Custom Kernels with PyTorch
- Tuning Kernel-Launch Parameters
- Autotuning Triton Kernels

## Advanced Triton Kernel Implementations
- Warp Specialization with Triton
- Tiled and Persistent GEMM Kernel (Triton)
- Software Pipelining and Double Buffering with Triton
- Profiling with Triton Proton Profiler

## PyTorch XLA Backend

## Key Takeaways

## Conclusion

<!-- file: ch15.xhtml -->

## Chapter 15. Multinode Inference, Parallelism, Decoding, and Routing Optimizations

## Disaggregated Prefill and Decode Architecture
- Prefill-Decode Interference
- Scaling Prefill and Worker Nodes Independently
- Impact on Latency (TTFT) and Throughput (TPOT)
- KV Cache Data Transfer and NIXL
- Deploying Disaggregated Prefill and Decode with Kubernetes

## Parallelism Strategies for Serving Massive MoE Models
- Tensor Parallelism
- Pipeline Parallelism
- Expert Parallelism
- Data Parallelism
- Context (Sequence) Parallelism
- Hybrid Parallelism

## Speculative Decoding and Parallel Token Generation Techniques
- Two-Model, Draft-Based Speculative Decoding and EAGLE
- Single-Model Self-Speculative Decoding
- Multitoken Decoding with Medusa’s Multiple Heads
- Interleaving Decode Steps from Multiple Requests
- Combining Decoding Techniques and Evaluating Complexity

## Constrained Decoding Performance Implications

## Dynamic Routing Strategies for MoE Inference
- Expert Communication Optimization
- Load Balancing, Capacity Factor, and Expert Replication
- Adaptive Expert Routing and Real-Time Monitoring

## Key Takeaways

## Conclusion

<!-- file: ch16.xhtml -->

## Chapter 16. Profiling, Debugging, and Tuning Inference at Scale

## Profiling, Debugging, and Tuning Inference Performance
- Monitoring System Metrics and Counters
- Profiling with Nsight Systems and Nsight Compute
- Inference Troubleshooting Recipes
- Full-Stack Inference Optimizations
- Debugging Correctness Issues

## Dynamic Batching, Scheduling, and Routing
- Dynamic Batching
- Continuous Batching
- Continuous Scheduling
- Stall-Free Scheduling (Chunked Prefill)
- Latency-Aware Scheduling and Dynamic Routing

## Systems-Level Optimizations
- Overlapping Communication and Computation
- Maximizing GPU Utilization and Throughput Versus Latency Trade-Offs
- Power and Thermal Constraints
- Error Handling
- Memory
- KV Cache Offloading and Memory Pool Allocation

## Quantization Approaches for Real-Time Inference
- Reducing Precision from FP16 to FP8 and FP4
- Weight-Only Quantization (GPTQ, AWQ)
- Activation Quantization
- Post-Training Quantization Workflow
- Combining Weight and Activation Quantization
- Fusing Quantization-Dequantization Steps into the Execution Graph

## Application-Level Optimizations
- Prompt Compression
- Prompt Cleansing
- Prefix Caching
- Model Cascading and Tiered Model Deployment
- Streaming Responses
- Debouncing and Request Coalescing
- Token Output Limits and Timeouts

## Key Takeaways

## Conclusion

<!-- file: ch17.xhtml -->

## Chapter 17. Scaling Disaggregated Prefill and Decode for Inference

## Why Prefill-Decode Disaggregation?
- Advantages of Disaggregation
  - Reduced interference
  - Phase-specific optimizations
- Disaggregated Prefill and Decode Cluster Pools
  - Prefill workers design
    - Memory management
    - Optimizing for latency versus throughput
    - Latency-aware scheduling and batching
  - Decode workers design
    - KV cache transfer between prefill and decode
    - Continuous batching
    - Grouping variable-length sequences
    - Memory management for the KV cache
- Disaggregated Routing and Scheduling Policies
  - Routing factors
  - Example dynamic routing policy in code
  - Example dynamic routing policy configuration
  - Capacity-aware routing
  - Latency-aware routing
  - Multipath inference (racing)
  - Multibranch, parallel speculative decoding across workers
  - QoS and early rejection policies
- Scalability of Disaggregated Prefill and Decode

## Key Takeaways

## Conclusion

<!-- file: ch18.xhtml -->

## Chapter 18. Advanced Prefill-Decode and KV Cache Tuning

## Optimized Decode Kernels
- FlashMLA (DeepSeek)
- ThunderMLA (Stanford)
- FlexDecoding (PyTorch)

## Tuning KV Cache Utilization and Management
- Disaggregated KV Cache Pool
- KV Cache Reuse and Prefix Sharing
- Optimized KV Cache Memory Layout
- GPU and CPU-GPU Superchip Improvements

## Fast KV Cache Transfer Between Prefill and Decode
- KV Cache Size
- Zero-Copy GPU-to-GPU Transfer

## Connector and Data Path Design

## Heterogeneous Hardware and Parallelism Strategies for Prefill and Decode
- Compute-Optimized Versus Memory-Optimized Hardware
  - Throughput and cost benefits
  - Phase-specific model parallelism
  - Different precision for prefill and decode

## Hybrid Prefill with GPU-CPU Collaboration

## SLO-Aware Request Management and Fault Tolerance
- Early Rejection (Admission Control)
- Quality of Service
- Fault Tolerance

## Dynamic Scheduling and Load Balancing
- Adaptive Resource Scheduling and Hotspot Prevention
  - TetriInfer’s two-level scheduler
  - Arrow’s adaptive instance scaling
  - Mooncake adaptive strategies
  - Dynamic resource scaling

## Key Takeaways

## Conclusion

<!-- file: ch19.xhtml -->

## Chapter 19. Dynamic and Adaptive Inference Engine Optimizations

## Adaptive Parallelism Strategies (TP Versus PP Versus Hybrid)

## Dynamic Precision Changes

## Kernel Autotuning for Transformer Self-Attention and MLP Paths

## Dynamic Shared-Memory Allocation and Occupancy-Aware Kernel Selection

## Speculative KV Prefetching for Faster TTFT

## Real-Time KV Cache Compression and Policy Switching

## Reinforcement Learning Agents for Tuning AI Systems at Runtime

## Dynamic Memory-Allocation Switching (Slab Versus Caching Versus Stream-Ordered)

## Runtime Kernel Performance Improvements and Hot-Swappable Implementations

## Continuous Prewarming of CUDA Graphs and Caches Using Time-Series Prediction

## Adaptive Batching and Chunked Prefill Scheduling

## Congestion-Aware and Topology-Aware Scheduling with Multiple GPUs
- NVLink/NVSwitch Topology and Bandwidth Constraints
- Real-Time Link Telemetry and Monitoring
- Adaptive Process-GPU Mapping
- Optimizing Collective Communication with NCCL
  - Ring versus tree all-reduce
  - Rotating ring endpoints
  - Wave scheduling of collectives
- Multinode and Multirack Communication with GPUDirect RDMA
- MoE Expert Rebalancing and Regrouping
- Dynamic Congestion-Aware Scheduling
- Coordinating NVSwitch Transfers with Fine-Tuned Scheduling

## Additional Adaptive and Dynamic Optimization Techniques
- Dynamic Early-Exit Networks
- Input-Aware Layer Skipping (DASH)
- Speculative MoE Expert Routing and Communication Reduction
- Dynamic Token Pruning with LazyLLM
- Edge-Oriented MoE Memory Budgeting
- Dynamic Quantization and Activation Range Adjustment

## Key Takeaways

## Conclusion

<!-- file: ch20.xhtml -->

## Chapter 20. AI-Assisted Performance Optimizations and Scaling Toward Multimillion GPU Clusters

## AlphaTensor AI-Discovered Algorithms Boosting GPU Performance (Google DeepMind)
- Automated GPU Kernel Optimizations with DeepSeek-R1 (NVIDIA)
- Reinforcement Learning Approach to Generating Optimized GPU Kernels (Predibase)
- Self-Improving AI Agents (AI Futures Project)
- Smart Compilers and Automated Code Optimizations
- AI-Assisted Real-Time System Optimizations and Cluster Operations
- Scaling Toward Multimillion GPU Clusters and 100-Trillion-Parameter Models

## Key Takeaways

## Conclusion

<!-- file: colophon01.xhtml -->

## About the Author

<!-- file: colophon02.xhtml -->

## Colophon

<!-- file: copyright-page01.xhtml -->

## AI Systems Performance Engineering

## Revision History for the First Edition

<!-- file: dedication01.xhtml -->

## Praise for AI Systems Performance Engineering

<!-- file: ix01.xhtml -->

## Index
  - Symbols
  - A
  - B
  - C
  - D
  - E
  - F
  - G
  - H
  - I
  - J
  - K
  - L
  - M
  - N
  - O
  - P
  - Q
  - R
  - S
  - T
  - U
  - V
  - W
  - X
  - Z

<!-- file: preface01.xhtml -->

## Preface

## Conventions Used in This Book

## Using Code Examples

## O’Reilly Online Learning

## How to Contact Us

## Acknowledgments

<!-- file: titlepage01.xhtml -->

## AI Systems Performance Engineering
