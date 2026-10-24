# nvidia-devops-zth-v17


## Chapter 1 — Performance Engineering Fundamentals  (chapter-01-performance-engineering-fundamentals.md)
- Introduction
- Beginner's Primer: The Iron Triangle of AI
- 1. Measurement Precedes Optimization
- 2. Throughput, Latency, and Utilization (The Iron Triangle)
- 3. The Evidence Ladder
- Customer Scenario (Senior Level)
- Interview Preparation
- Architecture Summary

## Chapter 2 — Profiling Tools Landscape  (chapter-02-profiling-tools-landscape.md)
- Introduction
- Beginner's Primer: The NVIDIA Toolbelt
- 1. Macro-Level Telemetry (The Thermometer)
- 2. System-Level Profiling (The X-Ray)
- 3. Kernel-Level Profiling (The Electron Microscope)
- 4. Application-Level Profiling
- Customer Scenario (Senior Level)
- Interview Preparation
- Architecture Summary

## Chapter 3 — Roofline Model and Analytical Performance  (chapter-03-roofline-model-and-analytical-performance.md)
- Introduction
- Beginner's Primer: The Kitchen Analogy
- 1. Arithmetic Intensity (The X-Axis)
- 2. The Roofline Graph
- 3. Applying the Roofline Model
- Customer Scenario (Senior Level)
- Interview Preparation
- Architecture Summary

## Chapter 4 — Bottleneck Identification and Diagnosis  (chapter-04-bottleneck-identification-and-diagnosis.md)
- Introduction
- Beginner's Primer: Finding the Clog
- 1. The Diagnostic Tree (Top-Down Isolation)
  - Step 1: Nsight Systems (The Timeline Check)
  - Step 2: Isolating Upstream Starvation (CPU vs PCIe)
  - Step 3: Isolating GPU Saturation (Compute vs Memory)
- Customer Scenario (Senior Level)
- Interview Preparation
- Architecture Summary

## Chapter 5 — GPU Compute Optimization  (chapter-05-gpu-compute-optimization.md)
- Introduction
- Beginner's Primer: How a GPU Thinks
- 1. The Anatomy of GPU Compute
  - Warps and Scheduling
- 2. The Compute Anti-Pattern: Warp Divergence
- 3. SM Occupancy and Tile Sizing
- Customer Scenario (Senior Level)
- Interview Preparation
- Architecture Summary

## Chapter 6 — Memory Optimization  (chapter-06-memory-optimization.md)
- Introduction
- Beginner's Primer: Coalesced Memory (The Bus Analogy)
- 1. Coalesced Memory Access
- 2. Kernel Fusion (Keeping Data in Cache)
- 3. FlashAttention: The Ultimate Memory Hack
- Customer Scenario (Senior Level)
- Interview Preparation
- Architecture Summary

## Chapter 7 — Communication and Collective Optimization  (chapter-07-communication-and-collective-optimization.md)
- Introduction
- Beginner's Primer: Hiding the Mailman
- 1. The Physics of Overlap
- 2. Tuning NCCL Buckets and Buffers
- 3. Sharp (Scalable Hierarchical Aggregation and Reduction Protocol)
- Customer Scenario (Senior Level)
- Interview Preparation
- Architecture Summary

## Chapter 8 — Inference Optimization  (chapter-08-inference-optimization.md)
- Introduction
- Beginner's Primer: The Bus Terminal
- 1. The Latency vs. Throughput Curve
- 2. Quantization (The Free Lunch and The Heavy Price)
- 3. KV Cache Optimization (LLMs)
- Customer Scenario (Senior Level)
- Interview Preparation
- Architecture Summary

## Chapter 9 — Training Optimization  (chapter-09-training-optimization.md)
- Introduction
- Beginner's Primer: The Physics of Training
- 1. Mixed Precision Training (AMP)
- 2. Escaping the Memory Wall
- 3. Dataloader Optimization
- Customer Scenario (Senior Level)
- Interview Preparation
- Architecture Summary

## Chapter 10 — System-Level Performance Tuning  (chapter-10-system-level-performance-tuning.md)
- Introduction
- Beginner's Primer: Tuning the Racecar
- 1. CPU Governors and C-States
- 2. PCIe Gen and ASPM
- 3. NUMA Pinning and Topology
- Customer Scenario (Senior Level)
- Interview Preparation
- Architecture Summary

## Chapter 11 — Production Performance Monitoring and SLOs  (chapter-11-production-performance-monitoring-and-slos.md)
- Introduction
- Beginner's Primer: The Silent Decay
- 1. The Threat of Silent Degradation
- 2. Setting Mathematical SLOs
- 3. Automated Regression Testing (CI/CD)
- Customer Scenario (Senior Level)
- Interview Preparation
- Architecture Summary

## Chapter 12 — Volume 17 Summary and Decision Trees  (chapter-12-volume-17-summary-and-decision-trees.md)
- Core Concepts Reviewed
- The Senior Architect's Mandate
- Beginner's Primer: Putting it all together
- Architecture Summary

## Volume 17 — Performance Engineering  (index.md)
- Big Picture
- Chapters
- Labs
