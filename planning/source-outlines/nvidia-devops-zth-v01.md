# nvidia-devops-zth-v01


## Chapter 7 — The NVIDIA Ecosystem: From Silicon to NIMs  (04-nvidia-ecosystem-overview.md)
- 1. Introduction (The "Why")
- 2. The Silicon: Generations and Specifications (The "What")
  - 2.1 Ampere (A100) — The Baseline
  - 2.2 Hopper (H100 / H200) — The Workhorse
  - 2.3 Blackwell (B200 / GB200) — The Rack-Scale Era
- 3. The Interconnect Ecosystem (The "Arteries")
- 4. The Software Ecosystem (The "Brain")
  - 4.1 CUDA & cuDNN (The Foundation)
  - 4.2 NCCL (The Orchestrator of the Network)
  - 4.3 TensorRT & Triton (The Serving Engines)
  - 4.4 NIM (NVIDIA Inference Microservices)
- 5. Customer Scenario (Senior Level)
- Interview Preparation
- Summary

## Chapter 8 — Enterprise AI Platforms & Orchestration  (05-enterprise-ai-platforms.md)
- 1. Introduction (The "Why")
- 2. Bare-Metal Provisioning: Base Command Manager (BCM)
- 3. Cloud-Native Orchestration: Kubernetes & The GPU Operator
- 4. Virtualization and Sharing: vGPU and MIG
  - 4.1 Multi-Instance GPU (MIG)
  - 4.2 NVIDIA vGPU (Virtual GPU)
- 5. The Commercial Layer: NVIDIA AI Enterprise (NVAIE)
- 6. Serverless AI: DGX Cloud
- 7. Customer Scenario (Senior Level)
- Interview Preparation
- Summary

## Chapter 9 — Volume 01 Summary: The Architecture of Accelerated Computing  (06-volume-01-summary.md)
- Introduction
- 1. The Core Architectural Tenets
  - 1.1 The Shift in the Bottleneck
  - 1.2 The Silicon Reality: CPU vs. GPU
  - 1.3 The Tensor Core Revolution
  - 1.4 The Two Phases of LLM Inference
  - 1.5 The Network is the Computer
  - 1.6 The Facility Wall
  - 1.7 Enterprise Orchestration
- 2. The Senior Engineer Mindset
- 3. What Comes Next: Volume 02

## What Is AI Infrastructure?  (chapter-01-what-is-ai-infrastructure.md)
- Introduction (The "Why")
- The Anatomy of an AI Request (The "What")
  - 1. The Preprocessing Phase (CPU)
  - 2. The Data Transfer (PCIe)
  - 3. The Execution Phase (GPU and HBM)
  - 4. The Autoregressive Loop
- Architectural Diagram
- The Bottlenecks (The "How" and "Trade-offs")
  - Bottleneck 1: Memory Bandwidth (The "Memory Wall")
  - Bottleneck 2: Interconnects (PCIe and NVLink)
  - Bottleneck 3: Host Starvation (CPU and Preprocessing)
- Production Deployment & Operations
- Customer Scenario (Senior Level)
- Interview Preparation
- Summary
- Key Takeaways
- Related Chapters

## Chapter 2 — Why CPUs Became Insufficient  (chapter-02-why-cpus-became-insufficient.md)
- Introduction (The "Why")
- The Limits of CPU Architecture (The "What")
  - The Problem with Matrix Math
- Architectural Diagram: The Resource Allocation Mismatch
- Advanced Concepts (The "How" & "Trade-offs")
  - 1. Context Switching vs. Warp Scheduling
  - 2. The Vector Extension Trade-off (AVX-512)
  - 3. The Memory Bandwidth Wall
- Production Deployment & Operations
- Customer Scenario (Senior Level)
- Interview Preparation
- Summary
- Key Takeaways

## Chapter 3 — CPU vs. GPU: Silicon, Threads, and Tensor Cores  (chapter-03-cpu-vs-gpu.md)
- Introduction (The "Why")
- The Core Difference: Thread Management (The "What")
  - The CPU Approach: Context Switching
  - The GPU Approach: SIMT and Warp Scheduling
- Architectural Diagram: CUDA Cores vs Tensor Cores
- The Evolution: CUDA Cores vs. Tensor Cores (The "How")
  - The Standard CUDA Core (FP32/FP64)
  - The Tensor Core
  - The Trade-off: Precision
- Production Deployment & Operations
- Customer Scenario (Senior Level)
- Interview Preparation
- Summary
- Key Takeaways

## Chapter 4 — The Anatomy of an LLM Inference Request  (chapter-04-what-happens-when-chatgpt-answers.md)
- Introduction (The "Why")
- The Two Phases of LLM Inference (The "What")
  - Phase 1: The Prefill Phase (Reading the Prompt)
  - Phase 2: The Decode Phase (Generating the Answer)
- Architectural Diagram: Prefill vs Decode
- The New SLIs: TTFT and TPOT (The "How")
  - The KV Cache Memory Crisis
- Advanced Optimizations: Continuous Batching & PagedAttention
  - Continuous Batching
  - PagedAttention
- Customer Scenario (Senior Level)
- Interview Preparation
- Summary

## Chapter 5 — The AI Infrastructure Landscape: Kubernetes vs. Slurm  (chapter-05-ai-infrastructure-landscape.md)
- Introduction (The "Why")
- Kubernetes: The Cloud-Native Microservices Approach (The "What")
  - How Kubernetes Adapts to AI
  - The Kubernetes Advantage
- Slurm: The High-Performance Computing Approach
  - How Slurm Operates
  - The Slurm Advantage
- Architectural Diagram: Slurm vs Kubernetes
- The Architectural Trade-offs
- Advanced: The Convergence (Run:ai, Kueue, Pyxis)
- Customer Scenario (Senior Level)
- Interview Preparation
- Summary

## Chapter 6 — The Modern AI Factory: Power, Cooling, and Facility Scale  (chapter-06-modern-ai-factory.md)
- Introduction (The "Why")
- Facility Constraints: The Three Pillars (The "What")
  - 1. Power Density (Kilowatts per Rack)
  - 2. Cooling (Air vs. Direct Liquid Cooling)
  - 3. Cable Lengths (The Speed of Light)
- Architectural Diagram: The AI Factory Layout
- The NVIDIA DGX SuperPOD (The "How")
  - The Storage Bottleneck
- Customer Scenario (Senior Level)
- Interview Preparation
- Summary

## Lab 01 — Inspect an AI Infrastructure Host  (labs/lab-01-inspect-an-ai-infrastructure-host.md)
- Objective
- Background
- Learning Outcomes
- Architecture
- Prerequisites
- Environment
- Components
- Deployment Steps
  - Step 1 — Identify the Operating System
  - Step 2 — Inspect Kernel Version
  - Step 3 — Inspect CPU Topology
  - Step 4 — Inspect Memory
  - Step 5 — List PCI Devices
  - Step 6 — Search for NVIDIA Devices
  - Step 7 — Check NVIDIA Management Tooling
  - Step 8 — Query NVIDIA Driver and GPU State
- Validation
- Verification
- Observability
- Performance Measurements
- Failure Injection
  - Failure Case 1 — No NVIDIA Hardware Visible
  - Failure Case 2 — NVIDIA Hardware Visible but `nvidia-smi` Missing
  - Failure Case 3 — `nvidia-smi` Exists but Cannot Communicate
- Troubleshooting
  - Problem
  - Symptoms
  - Detection
  - Diagnosis
  - Logs
  - Root Cause
  - Resolution
  - Verification
  - Prevention
- Cleanup
- Summary
- Challenge Exercises
- Further Reading
- Production Relevance

## Lab 02 - Trace an AI Request Through the Infrastructure Stack  (labs/lab-02-trace-an-ai-request-path.md)
- Lab Metadata
- 1. Objective
- 2. Background
- 3. Learning Outcomes
- 4. Architecture
- 5. Prerequisites
- 6. Environment
- 7. Components
- 8. Deployment Steps
  - Step 1: Create the request-path service
  - Step 2: Start the healthy service
  - Step 3: Send a request
  - Step 4: Measure client-visible latency
- 9. Validation
- 10. Verification
- 11. Observability
- 12. Performance Measurements
- 13. Failure Injection
  - Inject a preprocessing bottleneck
- 14. Troubleshooting
  - Symptoms
  - Detection
  - Diagnosis
  - Root Cause
  - Resolution
  - Verification
  - Prevention
- 15. Cleanup
- 16. Summary
- 17. Challenge Exercises
- 18. Production Mapping
- Further Reading
