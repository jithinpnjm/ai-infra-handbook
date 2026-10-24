# distributed-ai-systems


<!-- file: Chapter_1.xhtml -->

## 1

## Introduction to Modern Distributed AI

## Overview

## Why modern AI requires distribution
- The scale challenge
- Estimating model resource requirements
  - Training memory requirements
  - Inference memory requirements
  - GPU requirements estimation
  - Real-World considerations
- The evolution from classic ML to foundation models

## The modern AI model lifecycle
- Training: the learning phase
- Inference: the prediction/generation phase
- Serving: the production system

## Decision framework: when do you need distributed systems?
- Decision tree: quick reference
- Understanding the decision tree

## Hands-On: running distributed training
- Environment setup
- Single-GPU baseline
- Multi-GPU distributed training
- Extended training: CIFAR-10 with 20 epochs
- Distributed inference: throughput scaling

## Distributed AI fundamentals with PyTorch
- The distributed AI stack
- Process Groups and Ranks
- Initializing the process group
- Collective operations
  - AllReduce
  - AllGather
  - Broadcast
  - Reduce
  - Gather
  - Scatter
  - ReduceScatter
  - AlltoAll
  - Choosing the right operation
- DistributedDataParallel (DDP)
- DistributedSampler
- Launching distributed jobs

## Code summary

## References

## Exercises
- Process group initialization
- Manual AllReduce implementation
- Broadcast with verification
- DistributedSampler wrapper
- Gradient synchronization timing
- Expected learning outcomes

## Get this book's PDF version and more

<!-- file: Chapter_10.xhtml -->

## 10

## Distributed Benchmarking and Performance Optimization

## The performance gap in distributed systems

## Why benchmarking matters

## Benchmarking fundamentals
- Understanding percentile latencies
- Efficiency metrics
- Benchmarking methodology

## Training benchmarking
- Key training metrics
- PyTorch profiler
- NVIDIA Nsight Systems
- Custom training benchmark
- Measuring scaling efficiency
- Validating distributed training accuracy
- Network and communication profiling
- Scaling bottleneck analysis

## Inference benchmarking
- Key inference metrics
- Benchmarking tools: genai-bench
- Custom inference benchmarks
- Cold start vs warm performance
- Reasoning and multi-step models
- Validating inference accuracy

## Summary

## Code summary

## Useful links

## Reference

## Exercises
- Multiple choice questions
- Short answer questions
- Answer Key
- Expected learning outcomes

<!-- file: Chapter_11.xhtml -->

## 11

## The Evolving Landscape of Distributed AI

## The evolution of distributed AI
- Where we stand today
- The new bottlenecks
- Emerging trends at a glance

## Mixture of experts: the dominant architecture

## The Edge-cloud continuum
- Why edge AI matters now
- Practical On-device models
- Edge-cloud coordination

## Parallelism at scale
- The communication revolution
- Hierarchical parallelism
- Sequence parallelism for long contexts
- Ring attention

## When things go wrong: fault tolerance
- The checkpointing challenge
- Detecting and handling failures
- Elastic training

## Beyond text: multimodal distributed training
- The Cross-modal challenge
- Handling multiple modalities

## Federated learning: an alternative paradigm
- The federated paradigm
- Where federated learning thrives
- The challenges of heterogeneity
- Modern federated techniques
- Federated learning for LLMs
- The flower framework
- When to consider federated learning

## Agentic AI: the next frontier
- Why agents need distribution
- Multi-agent patterns
- Distributed tool execution
- Reasoning agents

## The economics of scale
- Workload distribution
- Resource management
- Multi-tenant GPU sharing
- Gradient compression

## Preparing for the future
- Skills to develop
- Staying current

## Summary

## Code summary

## Useful links

## References

## Exercises
- Multiple choice questions
- Short answer questions
- Hands-on exercise
  - Implement basic MoE routing

## Get this book's PDF version and more

<!-- file: Chapter_12.xhtml -->

## 12

## Unlock Your Exclusive Benefits

## Unlock this Book's Free Benefits in 3 Easy Steps
- Step 1
- Step 2
- Step 3
- Need Help

## Appendix

## OpenAI-Compatible API Endpoints

<!-- file: Chapter_2.xhtml -->

## 2

## GPU Hardware, Networking, and Parallelism Strategies

## Computational power: AI clusters and metrics
- What is computational power?
- Why clusters?
- AI clusters: built for training and inference
- Key metrics for AI clusters

## Central Processing Unit (CPU)
- CPU Architecture Basics
- CPU-GPU Interaction
- NUMA and CPU affinity
- CPU requirements for distributed training

## Graphics Processing Unit (GPU)
- Understanding GPU memory and compute architecture
- Key architecture milestones
- What these numbers mean for training
- Graphics Processing Unit (GPU) product families
- Choosing the right GPU
- Architecture features that matter

## Tensor Processing Unit (TPU)
- Why TPUs exist
- TPU architecture: systolic arrays
- TPU generations
- TPU pod architecture
- TPU vs GPU: when to use which
- TPU programming model
- Sparse core (since v4)

## Neural Processing Unit (NPU)
- What makes NPUs different
- NPU architecture: AI cores and memory
- Training vs inference NPUs
- NPU software stack
- NPU vs. GPU: when to choose which
- NPU interconnects and scaling
- The NPU landscape

## High-Speed interconnects: the network backbone

## Chip programming systems: SPMD and CUDA
- Programming models vs. execution models
- SPMD: single program, multiple data
- CUDA's execution model: SIMT
- Why SIMT over SIMD?
- CUDA thread indexing
- Memory hierarchy in CUDA
- How frameworks use CUDA
- SPMD in distributed training
- AMD and other alternatives

## Distributed communication: patterns and primitives

## Parallelism: core strategies
- Parallelism taxonomy table
- The three questions for parallelism determination
- Data parallelism: replicated and sharded
- Model parallelism: compute sharding
- Combining Strategies
- Composition patterns (hybrid parallelism)

## Strategy selection: choosing the right approach
- Training strategy decision tree
- Key considerations for training
- Inference strategy decision tree
- Key considerations for inference
- Practical tips

## Hands-On: hardware inspection and bandwidth testing
- Environment Setup
- Step 1: inspect GPU hardware
- Step 2: inspect hardware topology
- Step 3: measure Single-GPU memory bandwidth
- Step 4: benchmark Inter-GPU communication
- Step 5: analyze results

## Code summary

## Notes and references

## Exercises
- GPU hardware inspector
- Memory requirement calculator
- Topology detection and analysis
- Parallelism strategy selector
- Expected learning outcomes

<!-- file: Chapter_3.xhtml -->

## 3

## Distributed Training with PyTorch DDP

## How DDP works internally
- The basic flow
- Data Parallel (DP) vs. Distributed Data Parallel (DDP)
- Gradient bucketing: why it matters
- Communication–Computation overlap
- The AllReduce operation
- Mixed precision and gradient scaling
- Buffer Synchronization
- DDP forward pass implementation details
- DDP Computation–Communication overlap implementation

## Setting up Single-Node DDP
- Using torchrun (recommended)
- Understanding the environment variables
- Using DistributedSampler
- DataLoader internals for distributed training
- Device selection best practices
- A complete single node example

## Setting up Multi-Node DDP
- Multi-Node rchitecture
- Launching Multi-Node training
  - Using SLURM for Multi-Node launch
- Network configuration
- Environment variables for Multi-Node
- A complete Multi-Node example

## Debugging and troubleshooting
- Hangs: the most common problem
- Wrong results or inconsistent gradients
- CUDA out of memory
- Performance issues
- Network debugging

## Profiling DDP performance
- Using torch.profiler.profile for DDP analysis
- Analyzing Computation–Communication overlap
- Profiling Multi-Node DDP

## Optimizing DDP performance
- Mixed precision training
- Gradient accumulation
- Communication overlap optimization
- Tuning bucket sizes
- Finding unused parameters
- Static graph optimization

## Checkpointing and resuming distributed jobs
- Saving checkpoints
- Loading checkpoints
- Saving RNG state for reproducibility
- Atomic checkpointing
- Checkpointing best practices

## Advanced DDP features
- Gradient hooks
- Communication hooks
- Handling uneven inputs with join()

## Best practices and common patterns

## Elastic data parallelism
- How elastic training works
- Launching elastic training
- When to use elastic training

## Complete example: DDP with a transformer

## Summary

## Code summary

## References

## Exercises
- Implement manual gradient synchronization
- Compare DP vs DDP performance
- Implement gradient bucketing
- Implement Fault-Tolerant DDP training
- Analyze communication patterns with NCCL
- Expected learning outcomes

## Get this book's PDF version and more

<!-- file: Chapter_4.xhtml -->

## 4

## Scaling with Fully Sharded Data Parallel (FSDP)

## From DDP to FSDP

## Why FSDP enables Larger-Than-Memory models
- How FSDP works
- FSDP1 vs FSDP2: the evolution
- Original FSDP (FSDP1)

## FSDP2: the per-parameter sharding API
- Device mesh: the foundation
- Key parameters
- Hierarchical sharding

## A complete working example: T5 summarization with FSDP

## Checkpointing with FSDP2
- Using the DCP API (recommended)
- Manual sharded checkpointing
- Full state dict for evaluation

## Prefetching: optimizing communication
- Forward prefetching
- Backward prefetching
- When to use prefetching

## Activation checkpointing and offloading
- Why activation checkpointing matters with FSDP
- Using activation checkpointing
- CPU offloading
- When to use offloading

## Performance optimization
- Profiling FSDP training
- Optimizing communication
- Optimizing activation memory
- Memory profiling

## Multi-node FSDP training
- Setting up multi-node FSDP
- Network configuration for multi-node
- Checkpointing on multi-node
- SLURM integration
- Scaling considerations

## Debugging FSDP issues
- Out of Memory (OOM)
- Hanging or deadlocked
- Slow training
- Incorrect results
- Debugging tools

## Comparing FSDP2 with ZeRO and DDP
- Memory and performance
- When to use what

## Practical tips
- Initialization best practices
- Data loading and gradient clipping
- Mixed precision
- Progressive Optimization

## Advanced topics
- Hybrid sharding (HSDP)
- Compiler integration
- Other integrations
- FSDP via SPMD for TPU/XLA

## Summary

## Code Summary

## Useful links

## Notes and references

## Exercises
- Implement manual parameter sharding
- Compare FSDP sharding strategies
- Implement custom FSDP wrapping policy
- Implement mixed precision with FSDP
- Implement FSDP checkpointing
- Expected learning outcomes

<!-- file: Chapter_5.xhtml -->

## 5

## Beyond State Sharding with DeepSpeed and Megatron

## Beyond state sharding

## ZeRO stage 1: optimizer state partitioning

## ZeRO stage 2: optimizer state and gradient partitioning

## ZeRO stage 3: full sharding (like FSDP)

## ZeRO-Offload: CPU memory extension

## ZeRO-Infinity: NVMe offload for massive models

## ZeRO++: Communication-Optimized ZeRO

## Megatron: computation parallelism as a second axis
- State sharding vs. computation sharding
- Tensor Parallelism: sharding the layer
- Pipeline Parallelism: sharding the depth
- Sequence parallelism and context parallelism: long contexts
- DeepSpeed-Ulysses: an alternative to ring attention
- Expert Parallelism: scaling MoE models
- Why FSDP2 cannot replace Megatron
- Hybrid Parallelism: combining state and computation sharding
- Megatron core: Production-Ready library
- Megatron-FSDP: optimized state sharding
- Distributed optimizer: Memory-Efficient optimization
- FP8 training: Next-Generation precision
- When do you need Megatron?
- Real-World training configurations
- Complete training example with Megatron

## Hybrid Parallelism in practice
- The Two-Axis view
- Building a hybrid configuration
- Why this works
- Choosing your configuration
- Operational realities
- Performance optimization best practices
- Configuration patterns

## Choosing the right strategy
- A decision framework
- Understanding the Trade-Offs
- Concrete memory example

## Summary

## Code summary

## Useful links

## References

## Exercises
- Compare ZeRO stages
- Implement CPU offloading
- Implement Tensor Parallelism
- Implement Pipeline Parallelism
- Configure Hybrid Parallelism
- Expected learning outcomes

## Get this book's PDF version and more

<!-- file: Chapter_6.xhtml -->

## 6

## Distributed Inference and vLLM

## From training to inference

## Introduction to vLLM
- Prerequisites
- Installation
  - Docker Setup
  - Install and run from package manager (uv, conda, pip)
  - Compile, install, and run from local source
  - Offline inference
  - Online inference

## KV cache
- Decoder-Only transformer architecture
- Text generation process: prefill and decode
- The decode phase and its inefficiencies
- KV cache solution

## PagedAttention: solving KV cache fragmentation
- The KV cache fragmentation problem
- How PagedAttention works
- Eliminating padding FLOPs
- Connection to distributed inference

## Motivation: the "out of memory" problem

## Overview of the vLLM architecture

## Overview of parallelism strategies in vLLM

## Tensor Parallelism (TP)
- The linear algebra foundations
- Benefits of Tensor Parallelism
- When to use Tensor Parallelism

## Data Parallelism (DP) for throughput scaling
- Combining Data Parallelism with other strategies
- Deployment modes
- Benefits and Trade-Offs

## Pipeline Parallelism (PP)
- The pipeline bubble problem
- Chunked prefill for smoother pipelines

## Expert Parallelism (EP): A modifier flag for MoE models
- Understanding MoE architecture
  - Decoder layer structure
  - Expert structure
  - Routing mechanism
- How Expert Parallelism modifies behavior

## Combining parallelism strategies
- TP + PP: the standard Multi-Node configuration
- Expert Parallelism combinations
- TP + DP: scaling both ways
- The EP activation constraint

## Hands-On examples
- Basic vLLM setup with Tensor Parallelism
- Multi-Node with TP and PP
- Custom chunked prefill configuration
- Profiling with Nsight Systems
- Best practices

## Summary

## Code summary

## Useful links

## References

## Exercises
- Implement KV cache management
- Implement continuous batching
- Benchmark vLLM throughput
- Implement speculative decoding
- Deploy vLLM with OpenAI-Compatible API
- Expected learning outcomes

## Subscribe to Deep Engineering

<!-- file: Chapter_7.xhtml -->

## 7

## Cross-Request Optimization with SGLang

## A different philosophy for distributed inference
- Prerequisites
- Installation
  - Docker Setup

## Overview of the SGLang architecture

## SGLang core theory
- RadixAttention: prefix cache reuse
- Structured output decoding with XGrammar
- Operator fusion
- Zero-overhead scheduler

## Router-based distributed architecture
- SGLang model gateway architecture
- When Router-based architecture excels

## Prefill/Decode disaggregation
- PD disaggregation architecture
- Transfer engines
- PD disaggregation setup

## Distributed inference architecture and parallelism strategies
- Tensor Parallelism: weight sharding
- Pipeline Parallelism: layer sharding
- Data Parallelism: Request-level replication
- Hybrid Parallelism: combining strategies
- Communication patterns

## Multi-node SGLang deployment
- Multi-node with Tensor Parallelism
- Router-based multi-node deployment
- Router policies and load balancing
- Session affinity and cache locality
- Fault tolerance

## Expert for MoE models

## Speculative Decoding

## Data-Parallel attention

## Production deployment patterns

## Hands-on examples
- Basic multi-node deployment
- PD disaggregation with Mooncake
- Testing session affinity
- MoE model with EP+TP

## Summary

## Code summary

## Useful links

## Reference

## Exercises
- Implement RadixAttention cache
- Benchmark prefix caching
- Implementing constrained decoding
- Implement Multi-turn conversation with state
- Implement parallel generation with fork
- Expected learning outcomes

## Get this book's PDF version and more

<!-- file: Chapter_8.xhtml -->

## 8

## Running Distributed Training with SLURM

## Introduction to clusters for HPC and AI training
- Why SLURM for AI training?
- SLURM architecture: A brief overview

## Setting up SLURM for Multi-GPU training
- Simulating a Multi-Node cluster
- Quick setup and verification

## Submitting distributed training jobs

## Interactive execution with srun
- Batch submission with sbatch
- Understanding SLURM environment variables

## Launching distributed training frameworks with SLURM
- DDP with SLURM
- FSDP with SLURM {#sec:slurm-fsdp-example}
- DeepSpeed with SLURM
- Megatron-LM with SLURM

## Advanced SLURM features for training
- Job arrays for hyperparameter tuning
- Interactive jobs with salloc
- Job dependencies
- Checkpointing and job resumption

## Monitoring and debugging
- Job monitoring
- Logging and output
- Profiling distributed training

## Best practices
- Resource allocation
- Checkpointing strategy
- Handling failures

## Troubleshooting common issues
- Nodes not available
- GPU allocation issues
- Communication Errors
- Job hanging

## Code summary

## Useful links

## References

## Exercises
- Write a basic SLURM job script
- Implement automatic checkpointing with SLURM
- Configure Multi-Node NCCL communication
- Implement job array for hyperparameter search
- Monitor and profile SLURM jobs
- Expected learning outcomes

<!-- file: Chapter_9.xhtml -->

## 9

## Production LLM Serving Stack

## Anatomy of a production LLM serving system

## Request routing and traffic management
- Routing strategies
- Load balancing
- Canary deployments and A/B testing

## Operations: observability, reliability, and cost
- Observability
- Reliability and fault tolerance
- Cost optimization

## Deploying LLM serving on kubernetes
- Local development with k3d
- Deploying vLLM on k3d
- Cleanup
- Multi-Model and Multi-Engine serving
  - Multi-Model routing
  - Multi-Engine routing

## Kubernetes deployment with llm-d
- What is llm-d?
- Key features
- Deployment architecture
- Getting started with llm-d
- Well-Lit paths
- Monitoring and observability
- Choosing Your Path
- Multi-Model serving
- Comparing k3d and llm-d approaches

## Summary

## Code summary

## Useful links

## References

## Exercises
- Build an API gateway with model routing
- Implement rate limiting middleware
- Implement canary deployment with automated rollback
- Add distributed tracing with OpenTelemetry
- Deploy multi-model serving on k3d
- Expected learning outcomes

## Get this book's PDF version and more

<!-- file: Index.xhtml -->

## Index

<!-- file: Other_books_you_may_enjoy.xhtml -->

## Why subscribe?

## Other Books You May Enjoy

## Packt is searching for authors like you

## Share your thoughts

## Subscribe to Deep Engineering

<!-- file: Preface.xhtml -->

## Preface

## Who this book is for

## What this book covers

## To get the most out of this book
- Download the example code files
- Download the color images
- Conventions used

## Get in touch

## Free benefits with your book
- How to unlock

## Share your thoughts

<!-- file: Title_Pages.xhtml -->

## Distributed AI Systems

## A practical guide to building scalable training, inference, and serving systems for production AI

## Distributed AI Systems

## Foreword

## Contributors

## About the author

## About the reviewer

<!-- file: nav.xhtml -->
- Distributed AI Systems

<!-- file: toc.xhtml -->

## Table of Contents
