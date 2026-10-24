# nvidia-devops-zth-v15


## Chapter 01 — Why AI Storage Is Different  (chapter-01-why-ai-storage-is-different.md)
- Learning Objectives
- Beginner's Primer: The AI Factory Supply Chain
- The Core Problem: Capacity Is Not Throughput
- Workload Classes
- Architecture and Decision Points
- Command Evidence: Measuring Each Layer
  - Metadata Pressure
  - Storage Bandwidth and Saturation
  - Network and Client Throughput
  - CPU Preprocessing Pressure
- Production Story
- Troubleshooting Table: Diagnosis and Evidence
- Architecture Summary
- Interview-Ready Answers
- Practice

## Chapter 02 — The AI Data Path from Storage to GPU  (chapter-02-the-ai-data-path-from-storage-to-gpu.md)
- Beginner's Primer: The Bucket Brigade
- The Complete Data Path and Where Latency Hides
- Measuring Each Layer: Tools and Interpretation
  - 1. Storage Media Health (nvme0n1, sda, etc.)
  - 2. Storage Server Queue and Controller
  - 3. Network Fabric and Link Health
  - 4. Client Filesystem and Kernel Page Cache
  - 5. CPU Memory and NUMA Locality
  - 6. PCIe and GPU Fabric
  - 7. GPU Memory Pressure and Fragmentation
- Production Design: Optimizing the Path
  - The Critical Question for Each Layer
  - Real Scenario: Finding and Fixing a Hidden Copy Bottleneck
- Architecture Summary
- Practice

## Chapter 03 — Local NVMe and Data Staging  (chapter-03-local-nvme-and-data-staging.md)
- Beginner's Primer: Why Do We Still Need Local Disks?
- When to Use Local NVMe (and When Not To)
- Architecture: The Decision Path
- The Real Benefit: Numbers
- Production Design: Avoiding Pitfalls
  - Cache Consistency and Eviction
  - Checkpoint Staging
  - Cache Key and Checksum Validation
- Troubleshooting: Identifying Real vs False Benefits
- Architecture Summary
- Interview-Ready Answer
- Practice

## Chapter 04 — GPUDirect Storage Architecture  (chapter-04-gpudirect-storage-architecture.md)
- Beginner's Primer: Removing the Middleman
- The CPU Bounce Problem GDS Solves
- Architecture: Direct vs Fallback
- Verification: Proving GDS Is Actually Working
  - 1. Check Prerequisites
  - 2. Check Physical Topology (Critical!)
  - 3. Measure Actual Path: Is GDS Active?
  - 4. Compare CPU Overhead
- Production Checklist: When to Enable GDS
- Real Scenario: GDS Disabled by Silent Misconfiguration
- Troubleshooting Table
- Architecture Summary
- Interview-Ready Answers
- Practice

## Chapter 05 — Lustre for AI and HPC  (chapter-05-lustre-for-ai-and-hpc.md)
- Beginner's Primer: Shattering the Hard Drive
- Architecture: Where Metadata and Data Split
- Measurement: Identify Which Is Your Bottleneck
  - Metadata Pressure
  - Data Bandwidth and OST Balance
  - Striping Configuration
- Production Design: Scaling Metadata
  - Enabling Distributed Metadata (DNE)
- AI-Specific Tuning
  - For Training (parallel reads, periodic checkpoints)
  - For Checkpoints (synchronized writes)
- Troubleshooting Table: Diagnosis and Remediation
- Architecture Summary
- Interview-Ready Answers
- Practice

## Chapter 06 — BeeGFS for GPU Clusters  (chapter-06-beegfs-for-gpu-clusters.md)
- Beginner's Primer: The Simpler Parallel Filesystem
- Architecture: Decoupled Services
- Measurement Tools and Interpretation
  - Metadata Operations
  - Storage Targets and Fill Balance
  - Client Configuration and Locality
- Striping and File Layout
- AI-Specific Tuning
  - For Training (Parallel Dataset Reads)
  - For Checkpoints (Synchronized Writes)
- Comparing BeeGFS to Lustre
- Troubleshooting Table
- Architecture Summary
- Interview-Ready Answers
- Practice

## Chapter 07 — Object Storage and Dataset Pipelines  (chapter-07-object-storage-and-dataset-pipelines.md)
- Beginner's Primer: The S3 Trap
- Why Direct Object Storage Is Slow
- Architecture: A Production Pipeline
- Measurement: Bottleneck in the Pipeline
  - Object Download Latency and Throughput
  - Cache Hit Rate and Prefetch Effectiveness
- Production Patterns
  - Pattern 1: Dataset Versioning with Manifests
  - Pattern 2: Asynchronous Download with Backoff
- Troubleshooting Table
- Architecture Summary
- Interview-Ready Answers
- Practice

## Chapter 08 — Checkpoint Architecture and Recovery  (chapter-08-checkpoint-architecture-and-recovery.md)
- Beginner's Primer: The Cost of Saving
- The Checkpoint Lifecycle and Bottleneck Points
- Measurement and Diagnostics
  - Checkpoint Duration and Components
  - Finding the Straggler
- Production Pattern 1: Asynchronous Checkpoint via Staging
- Production Pattern 2: Checkpoint Retention and Cleanup
- Measurement: Recovery Time (RTO)
- Troubleshooting Table
- Architecture Summary
- Interview-Ready Answers
- Practice

## Chapter 09 — Metadata, Small Files, and Data Loading  (chapter-09-metadata-small-files-and-data-loading.md)
- Beginner's Primer: The Library Catalog Problem
- The Small-File Problem, Quantified
- Diagnosis: Where Is the Time Actually Going?
  - Measure File-Open Rate
  - Measure Batch Assembly Time
- Solutions: The Repackaging Approach
  - Solution 1: Tar Archives (Simplest)
  - Solution 2: WebDataset (Production-Grade)
  - Solution 3: HDF5 (For Structured Data)
- Production Checklist
- Troubleshooting Table
- Architecture Summary
- Interview-Ready Answers
- Practice

## Chapter 10 — Capacity, Performance, and Cost Planning  (chapter-10-capacity-performance-and-cost-planning.md)
- The Cost of Idle GPUs vs Storage Savings
- Planning Framework: Six Dimensions
  - 1. Usable Capacity
  - 2. Read Bandwidth
  - 3. Write Bandwidth
  - 4. Metadata Rate
  - 5. Burst Handling
  - 6. Cost Per GPU-Hour
- Tiering Strategy
- Capacity Planning Calculator
- Headroom Budgeting
- Interview-Ready Answer
- Practice

## Chapter 11 — Production Troubleshooting  (chapter-11-production-troubleshooting.md)
- The Troubleshooting Decision Tree
- Evidence Gathering: The 5-Minute Baseline
- Real Incident: Diagnosis in Practice
  - Step 1: Capture Current State
  - Step 2: Start with GPU Utilization
  - Step 3: Is the Loader CPU-Bound?
  - Step 4: Check Network and Metadata
  - Step 5: Investigate the Network
  - Step 6: Rebalance or Update Configuration
- Troubleshooting Tables: Symptoms to Diagnosis
  - Table 1: GPU Idle (Waiting for Data)
  - Table 2: Slow Metadata
  - Table 3: Slow Storage
  - Table 4: High CPU Load During I/O
- Interview-Ready Answers
- Practice

## Chapter 12 — Volume 15 Summary  (chapter-12-volume-15-summary.md)
- The Insight You Must Carry Forward
- Architecture Summary
  - The Data Path (Chapter 02) — Seven layers, each with latency and capacity
  - Local NVMe and GPUDirect Storage (Chapters 03–04) — Removing the CPU bounce
  - Lustre and BeeGFS (Chapters 05–06) — Distributed metadata is the real differentiator, not "single vs. multiple MDS"
  - Object Storage and Checkpointing (Chapters 07–08) — Durability vs. the critical path
  - Metadata, Small Files, and Capacity Planning (Chapters 09–10) — The 47-minute problem
  - Production Troubleshooting (Chapter 11) — Layered, ordered diagnosis
- Quick Revision
- Production Deployment Checklist
- Interview and Hiring Signal
- Related Volumes
- Summary Statement

## Volume 15 — AI Storage  (index.md)
- Big Picture
- Chapters
- Labs

## Lab 01 — Baseline an AI Storage Path  (labs/lab-01-baseline-an-ai-storage-path.md)
- Architecture: The Path We're Measuring
- Lab Steps
  - Step 1: Network and Topology Inventory
  - Step 2: Storage and Filesystem Inventory
  - Step 3: Measure Path Latency and Throughput
  - Step 4: CPU-NUMA-GPU Affinity Verification
  - Step 5: Memory and Cache Status
- Validation: Sanity Checks
- Cleanup
- Deliverable

## Lab 02 — Benchmark Local NVMe and Shared Storage  (labs/lab-02-benchmark-local-nvme-and-shared-storage.md)
- Workload Profiles We'll Test
- Lab Steps
  - Step 1: Local NVMe Baseline
  - Step 2: Shared Storage Baseline
  - Step 3: Compare and Interpret Results
  - Step 4: Validate Under Realistic Load
- Deliverables
- Interpretation Guide
- Cleanup

## Lab 03 — Validate a GPUDirect Storage Design  (labs/lab-03-validate-a-gpudirect-storage-design.md)
- What We're Validating
- Lab Steps
  - Step 1: Verify Prerequisites
  - Step 2: Benchmark Without GDS (CPU Bounce)
  - Step 3: Benchmark With GDS (If Available)
  - Step 4: Compare and Measure CPU Overhead
  - Step 5: Decision Framework
- Deliverables
- Cleanup

## Lab 04 — Troubleshoot Checkpoint and Data-Loading Bottlenecks  (labs/lab-04-troubleshoot-checkpoint-and-data-loading-bottlenecks.md)
- Setup: Create a Test Workload
- Lab Workflow
  - Step 1: Instrument the Application
  - Step 2: Capture Baseline Evidence
  - Step 3: Diagnose the Bottleneck
  - Step 4: Root-Cause Test
  - Step 5: Measure the Fix
- Resolution Checklist
  - If Data Loading is the Bottleneck:
  - If Checkpoint is the Bottleneck:
  - If Network is the Bottleneck:
  - If Metadata is the Bottleneck:
- Deliverables
- Cleanup
