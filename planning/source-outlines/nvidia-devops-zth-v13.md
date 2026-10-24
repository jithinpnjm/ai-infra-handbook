# nvidia-devops-zth-v13


## Chapter 1: Why Distributed Training Exists  (chapter-01-why-distributed-training-exists.md)
- Learning Outcome
- Beginner's Primer: The "Too Big to Fit" Problem
- Why Distributed Training Exists
- The Training Memory Breakdown
- The Decision Diagram: When Distributed Training Becomes Mandatory
- The Compute Scaling Argument
- The Troubleshooting Decision Tree: Diagnosing Single-GPU Failures
- Production Monitoring: The Signals That Matter
- Interview Preparation
- Architecture Summary
- Related Chapters

## Chapter 2: Training Memory and Compute Anatomy  (chapter-02-training-memory-and-compute-anatomy.md)
- Learning Outcome
- Beginner's Primer: The AI Math Class
- The Five Memory Consumers During a Training Step
  - 1. Forward Pass
  - 2. Loss Computation
  - 3. Backward Pass (Gradient Computation)
  - 4. Optimizer Step
  - 5. Temporary Buffers
- Full Memory Timeline for a Single Step
- Profiling Real Memory Usage: PyTorch Memory Profiler
- Decision Flowchart: When Each Optimization Matters
- Mixed Precision (AMP) in Action
- The Troubleshooting Decision Tree: OOM at Which Phase?
- Production Monitoring: Memory Trends Over Time
- Interview Preparation
- Architecture Summary
- Related Chapters

## Chapter 3: Data Parallelism and DDP  (chapter-03-data-parallelism-and-ddp.md)
- Learning Outcome
- Beginner's Primer: The Factory Floor
- What Is Data Parallelism?
- The DDP Training Loop: Step by Step
- Annotated Real Training Output: The First DDP Training Run
- The All-Reduce Collective Operation: The Synchronization Bottleneck
- The Decision Flowchart: Debugging DDP Hangs
- Real Troubleshooting: The Unused Parameters Bug
- Production Monitoring: DDP-Specific Signals
- Interview Preparation
- Architecture Summary
- Related Chapters

## Chapter 04 — FSDP and Parameter Sharding  (chapter-04-fsdp-and-parameter-sharding.md)
- Learning Outcome
- Beginner's Primer: Shattering the Dictionary
- Why FSDP Exists: The Math Behind Parameter Sharding

## Chapter 05 — DeepSpeed and ZeRO  (chapter-05-deepspeed-and-zero.md)
- Learning Outcome
- Beginner's Primer: Microsoft's Answer to the Memory Problem
- Why ZeRO Exists: Elimination of Redundancy
- ZeRO Stage 1: Shard Optimizer States
- ZeRO Stage 2: Shard Gradients + Optimizer States
- ZeRO Stage 3: Shard Everything
- The Memory Reduction Math: Side-by-Side Comparison
- ZeRO-Offload: When GPU Memory Isn't Enough
- Configuring ZeRO: The Config Dictionary
- Troubleshooting: ZeRO-3 Communication Hangs
- The NVMe Thrashing Problem
- Production Monitoring: ZeRO-Specific Metrics
- Interview Preparation
- Architecture Summary
- Related Chapters

## Chapter 06 — Tensor, Pipeline, and Expert Parallelism  (chapter-06-tensor-pipeline-and-expert-parallelism.md)
- Learning Outcome
- Beginner's Primer: Model Parallelism vs. Data Parallelism
- Why Model Parallelism Exists: When Single-GPU Memory Isn't the Problem
- The Three Flavors of Model Parallelism
  - Tensor Parallelism (TP): Shard Inside Layers
  - Pipeline Parallelism (PP): Shard Across Layers
  - Expert Parallelism (EP): Shard Across Experts in MoE
- Real-World TP Failure: Inter-Node Misconfiguration
- Real-World PP Failure: Bubble Starvation
- Choosing Between TP, PP, DP, and Combinations
- Production Monitoring: Parallelism-Specific Signals
- Interview Preparation
- Architecture Summary
- Related Chapters

## Chapter 07 — Megatron-LM Architecture  (chapter-07-megatron-lm-architecture.md)
- Beginner's Primer: What is Megatron-LM?
- WHY
- WHAT
- HOW
  - Worked Example: Sizing a 175B-Parameter Training Run
- WHEN
- TRADEOFFS
- PRODUCTION
- TROUBLESHOOTING
  - Scenario 1: The "Hanging on Initialization" Issue
  - Scenario 2: Pipeline Stage Imbalance ("The Ghost Straggler")
- Interview Preparation
- Architecture Summary
- Related Chapters

## Chapter 08 — NCCL Collectives and Communication Paths  (chapter-08-nccl-collectives-and-communication-paths.md)
- Beginner's Primer: What is NCCL?
- WHY
- WHAT
- HOW
  - Ring Topology
  - Tree Topology
  - Worked Example: Comparing Ring vs. Tree Cost at Two Cluster Sizes
- WHEN
- TRADEOFFS
- PRODUCTION
- TROUBLESHOOTING
  - Scenario 1: NCCL Timeout (The Slowest Rank Problem)
  - Scenario 2: Unexpected Fallback to PCIe
  - Scenario 3: All-to-All Collapse in MoE Training
- Interview Preparation
- Architecture Summary
- Related Chapters

## Chapter 09 — Checkpointing and Recovery  (chapter-09-checkpointing-and-recovery.md)
- Beginner's Primer: Saving the Game
- WHY
- WHAT
- HOW
  - Worked Example: Sizing a Checkpoint Write for a 70B Model
- WHEN
- TRADEOFFS
- PRODUCTION
- TROUBLESHOOTING
  - Scenario 1: Corrupted Checkpoint on Crash
  - Scenario 2: OOM During Asynchronous Checkpoint
  - Scenario 3: Resharding Mismatch After Cluster Resize
- Interview Preparation
- Architecture Summary
- Related Chapters

## Chapter 10 — Multi-Node Training Architecture  (chapter-10-multi-node-training-architecture.md)
- Beginner's Primer: The 8-Lane Highway
- WHY
- WHAT
- HOW
  - Worked Example: Cross-Node Bandwidth vs. Intra-Node NVLink
- WHEN
- TRADEOFFS
- PRODUCTION
- Running NVIDIA Training Workloads with Slurm
  - Architecture, from a Training Job's Point of View
  - The Job-Launch Workflow
  - Enroot: Unprivileged Containers for HPC Nodes
  - Pyxis: Slurm-Native Container Launch
  - End-to-End Worked Workflow
  - Interview Answer
- Interview Preparation
- TROUBLESHOOTING
  - Scenario 1: Suboptimal Routing (The Noisy Neighbor)
  - Scenario 2: GPU to NIC Affinity Mismatch
  - Scenario 3: Node Drains Mid-Job, Distributed Job Hangs Then Dies
- Architecture Summary

## Chapter 11 — Performance Engineering and Troubleshooting  (chapter-11-performance-engineering-and-troubleshooting.md)
- Beginner's Primer: The "Utilization" Lie
- WHY
- WHAT
  - Model Flops Utilization (MFU)
  - Worked Example: Computing MFU for a 70B Model on 8 H100s
  - Hardware Flops Utilization (HFU)
- HOW
  - Level 1: System Metrics (Prometheus/Grafana)
  - Level 2: Micro-Profiling with Nsight Systems
- WHEN
- TRADEOFFS
- PRODUCTION
- TROUBLESHOOTING
  - Scenario 1: The Dataloader Bottleneck
  - Scenario 2: Severe Straggler Node
  - Scenario 3: High GPU Utilization, Low MFU
- Interview Preparation
- Architecture Summary
- Related Chapters

## Chapter 12 — Volume 13 Summary  (chapter-12-volume-13-summary.md)
- The Journey So Far
- Core Concepts Reviewed
  - Parallelism Strategies (Chapters 3-7)
  - Data Movement and NCCL (Chapter 8)
  - Checkpointing and Recovery (Chapter 9)
  - Architecture at Scale (Chapter 10)
  - Performance Engineering (Chapter 11)
- Quick-Reference: Symptom to First Diagnostic Step
- The Ops Perspective
- TROUBLESHOOTING
  - Scenario 1: GPU ECC Memory Errors
  - Scenario 2: Broken NVLink Bridge
- Ready for the Next Volume

## Volume 13: Distributed Training Foundations  (index.md)
- Introduction
- What You'll Learn
- Key Concepts at a Glance
- Production Deployment Model
- How to Use This Volume
- Related Materials

## Lab 01 — Run Multi-GPU DDP Training  (labs/lab-01-run-multi-gpu-ddp-training.md)
- 1. Objective
- 2. Target Audience
- 3. Prerequisites
- 4. Architecture Diagram
- 5. Environment Setup
- 6. Execution Specifications
- 7. Expected Evidence
- 8. Explanation of Behavior
- 9. Performance Benchmarking
- 10. Common Failures
- 11. Safe Failure Injection
- 12. Recovery Steps
- 13. Troubleshooting Guide
- 14. Validation
- 15. Real-World Pitfalls
- 16. Cleanup Procedures
- 17. Knowledge Check
- 18. Additional References

## Lab 02 — Benchmark NCCL Collectives  (labs/lab-02-benchmark-nccl-collectives.md)
- 1. Objective
- 2. Target Audience
- 3. Prerequisites
- 4. Architecture Diagram
- 5. Environment Setup
- 6. Execution Specifications
- 7. Expected Evidence
- 8. Explanation of Behavior
- 9. Performance Benchmarking
- 10. Common Failures
- 11. Safe Failure Injection
- 12. Recovery Steps
- 13. Troubleshooting Guide
- 14. Validation
- 15. Real-World Pitfalls
- 16. Cleanup Procedures
- 17. Knowledge Check
- 18. Additional References

## Lab 03 — Test Sharded Training with FSDP  (labs/lab-03-test-sharded-training-with-fsdp.md)
- 1. Objective
- 2. Target Audience
- 3. Prerequisites
- 4. Architecture Diagram
- 5. Environment Setup
- 6. Execution Specifications
- 7. Expected Evidence
- 8. Explanation of Behavior
- 9. Performance Benchmarking
- 10. Common Failures
- 11. Safe Failure Injection
- 12. Recovery Steps
- 13. Troubleshooting Guide
- 14. Validation
- 15. Real-World Pitfalls
- 16. Cleanup Procedures
- 17. Knowledge Check
- 18. Additional References

## Lab 04 — Recover a Distributed Training Job  (labs/lab-04-recover-a-distributed-training-job.md)
- 1. Objective
- 2. Target Audience
- 3. Prerequisites
- 4. Architecture Diagram
- 5. Environment Setup
- 6. Execution Specifications
- 7. Expected Evidence
- 8. Explanation of Behavior
- 9. Performance Benchmarking
- 10. Common Failures
- 11. Safe Failure Injection
- 12. Recovery Steps
- 13. Troubleshooting Guide
- 14. Validation
- 15. Real-World Pitfalls
- 16. Cleanup Procedures
- 17. Knowledge Check
- 18. Additional References
