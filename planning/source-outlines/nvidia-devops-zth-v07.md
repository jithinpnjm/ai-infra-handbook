# nvidia-devops-zth-v07


## Chapter 1 — Why GPU Networking Exists  (chapter-01-why-gpu-networking-exists.md)
- Introduction
- 1. The Distributed Training Paradigm
- 2. The Legacy Networking Problem
  - The Latency of TCP/IP
  - The Jitter of Deep Buffers
- 3. The GPU Networking Mandate
- Customer Scenario (Senior Level)
- Interview Preparation

## Chapter 2 — PCIe, NUMA, and Host Data Paths  (chapter-02-pcie-numa-and-host-data-paths.md)
- Introduction
- 1. The PCIe Gen5 Bottleneck
- 2. The CPU Root Complex vs. PCIe Switches
  - Bad Design: Direct CPU Attachment
  - Good Design: PCIe Switches (PLX/Broadcom chips)
- 3. The Deadliest Bottleneck: NUMA Boundaries
  - The Cross-NUMA Penalty
- Architectural Diagram: Internal Topology
- 4. Verifying Topology (`nvidia-smi topo -m`)
- Customer Scenario (Senior Level)
- Interview Preparation

## Chapter 3 — NVLink and NVSwitch  (chapter-03-nvlink-and-nvswitch.md)
- Introduction
- 1. NVLink: The Point-to-Point Wire
  - The Generational Leap
  - The Physical Implementation (NVLink Bridges)
- 2. NVSwitch: The Non-Blocking Fabric
  - The HGX Baseboard Architecture
- Architectural Diagram: PCIe vs NVSwitch
- 3. NVLink C2C (Chip-to-Chip)
- Customer Scenario (Senior Level)
- Interview Preparation

## Chapter 4 — DMA, RDMA, and Peer-to-Peer  (chapter-04-dma-rdma-and-peer-to-peer.md)
- Introduction
- 1. The TCP/IP Penalty
- 2. Direct Memory Access (DMA)
- 3. Remote Direct Memory Access (RDMA)
  - The Magic of Kernel Bypass
  - RDMA Fabrics
- Architectural Diagram: TCP/IP vs. RDMA
- Customer Scenario (Senior Level)
- Interview Preparation

## Chapter 5 — GPUDirect RDMA  (chapter-05-gpudirect-rdma.md)
- Introduction
- 1. The GPUDirect RDMA Pipeline
  - How it Works (BAR1 Memory)
- 2. The Physical Motherboard Requirement
- Architectural Diagram: The Host Bounce Buffer vs GPUDirect
- Customer Scenario (Senior Level)
- Interview Preparation

## Chapter 6 — GPUDirect Storage (GDS)  (chapter-06-gpudirect-storage.md)
- Introduction
- 1. How GDS Works (The `cufile` API)
- 2. GDS Over the Network (NVMe-oF)
- Architectural Diagram: The Evolution of Storage Paths
- Customer Scenario (Senior Level)
- Interview Preparation

## Chapter 7 — ConnectX and GPU Network Adapters  (chapter-07-connectx-and-gpu-network-adapters.md)
- Introduction
- 1. The ConnectX Generations
  - ConnectX-6 (The Ampere A100 Era)
  - ConnectX-7 (The Hopper H100 Era)
  - ConnectX-8 (The Blackwell B200 Era)
- 2. The Physics of the PCIe Bottleneck
- 3. Beyond Basic Networking (Hardware Offloads)
- Customer Scenario (Senior Level)
- Interview Preparation

## Chapter 8 — Topology Aware Placement  (chapter-08-topology-aware-placement.md)
- Introduction
- 1. The Anatomy of Misalignment
- 2. The Kubernetes Topology Manager
  - Topology Policies
- 3. Configuring the Stack (The NVIDIA GPU Operator)
- Architectural Diagram: Topology Manager Alignment
- Customer Scenario (Senior Level)
- Interview Preparation

## Chapter 9 — Multi-Node Collectives and NCCL  (chapter-09-multi-node-collectives-and-nccl-paths.md)
- Introduction
- 1. What is a Collective?
- 2. NCCL Topologies: Rings and Trees
  - The Ring Topology (Ring AllReduce)
  - The Tree Topology (Tree AllReduce)
- Architectural Diagram: Ring vs Tree Collectives
- 3. SHARP: Math in the Network Switch
- Customer Scenario (Senior Level)
- Interview Preparation

## Chapter 10 — Performance Bottlenecks and Benchmarking  (chapter-10-performance-bottlenecks-and-benchmarking.md)
- Introduction
- 1. Validating the Motherboard (`nvbandwidth`)
- 2. Validating the Physical Network (`ib_write_bw`)
- 3. Validating the AI Fabric (`nccl-tests`)
  - Interpreting the NCCL Test
- Architectural Diagram: The Troubleshooting Hierarchy
- Customer Scenario (Senior Level)
- Interview Preparation

## Chapter 11 — Production Design Scenarios  (chapter-11-production-design-scenarios.md)
- Introduction
- Scenario 1: The Non-Blocking Fat-Tree
- Scenario 2: The Multi-Tenant Bandwidth Trap
- Scenario 3: The Storage Subnet Collision
- Interview Preparation

## Chapter 12 — Volume 07 Summary: The GPU Network  (chapter-12-volume-07-summary.md)
- Introduction
- 1. The Core Architectural Tenets
  - 1.1 The Motherboard Bottlenecks
  - 1.2 The Intra-Node Fabric (NVLink)
  - 1.3 Bypassing the Kernel
  - 1.4 GPUDirect Technology
  - 1.5 The Multi-Plane Network
  - 1.6 NCCL and Collectives
  - 1.7 Senior Troubleshooting Hierarchy
- 2. What Comes Next: Volume 08

## Volume 07 — GPU Networking and Data Paths  (index.md)
- Introduction
- What You Will Learn
- Why This Matters for Senior Architects
- Chapter Progression

## Lab 01 — Inspect PCIe, NUMA, and GPU Topology  (labs/lab-01-inspect-pcie-numa-and-gpu-topology.md)
- 1. Objective
- 2. Background
- 3. Learning Outcomes
- 4. Architecture
- 5. Prerequisites
  - Hardware
  - Software
  - Permissions
- 6. Environment
- 7. Components
- 8. Deployment Steps
  - Step 1 — Inspect CPU and NUMA layout
  - Step 2 — Inspect the PCIe tree
  - Step 3 — Map GPU identities
  - Step 4 — Inspect GPU topology
  - Step 5 — Resolve device NUMA nodes
  - Step 6 — Inspect PCIe link negotiation
  - Step 7 — Inspect network-adapter locality
  - Step 8 — Build the topology worksheet
- 9. Validation
- 10. Verification
- 11. Observability
- 12. Performance Measurements
- 13. Failure Injection
- 14. Troubleshooting
  - Symptom: GPU missing from `nvidia-smi`
  - Symptom: Link width lower than expected
  - Symptom: Correct devices but poor locality
- 15. Cleanup
- 16. Summary
- 17. Challenge Exercises
- 18. Further Reading

## Lab 02 — Validate Peer Access and NVLink  (labs/lab-02-validate-peer-access-and-nvlink.md)
- 1. Objective
- 2. Background
- 3. Learning Outcomes
- 4. Architecture
- 5. Prerequisites
- 6. Environment
- 7. Components
- 8. Deployment Steps
  - Step 1 — Inspect expected connectivity
  - Step 2 — Inspect NVLink state
  - Step 3 — Obtain CUDA samples
  - Step 4 — Run peer-access validation
  - Step 5 — Repeat for stability
  - Step 6 — Observe while testing
- 9. Validation
- 10. Verification
- 11. Observability
- 12. Performance Measurements
- 13. Failure Injection
  - Option A — Select a weaker pair
  - Option B — Remote CPU affinity
- 14. Troubleshooting
  - Peer access unavailable
  - One pair is much slower
  - Data-integrity validation fails
- 15. Cleanup
- 16. Summary
- 17. Challenge Exercises
- 18. Further Reading

## Lab 03 — Benchmark RDMA and GPUDirect Paths  (labs/lab-03-benchmark-rdma-and-gpudirect-paths.md)
- 1. Objective
- 2. Background
- 3. Learning Outcomes
- 4. Architecture
- 5. Prerequisites
- 6. Environment
- 7. Components
- 8. Deployment Steps
  - Step 1 — Prove basic reachability
  - Step 2 — Snapshot counters
  - Step 3 — Run host-memory RDMA bandwidth
  - Step 4 — Run host-memory latency
  - Step 5 — Validate GPU-aware software support
  - Step 6 — Run GPU-buffer or NCCL validation
  - Step 7 — Capture transport evidence
- 9. Validation
- 10. Verification
- 11. Observability
- 12. Performance Measurements
- 13. Failure Injection
- 14. Troubleshooting
  - Host RDMA is slow
  - Host RDMA is healthy but GPU-aware traffic is slow
  - Results vary heavily
  - Test hangs
- 15. Cleanup
- 16. Summary
- 17. Challenge Exercises
- 18. Further Reading

## Lab 04 — Troubleshoot a Multi-GPU Data Path  (labs/lab-04-troubleshoot-a-multi-gpu-data-path.md)
- 1. Objective
- 2. Background
- 3. Learning Outcomes
- 4. Architecture
- 5. Prerequisites
- 6. Environment
- 7. Components
- 8. Deployment Steps
  - Step 1 — Run the healthy baseline
  - Step 2 — Prove the healthy placement
  - Step 3 — Select one safe failure
    - Failure A — Remote CPU and memory binding
    - Failure B — Nonpreferred network interface
    - Failure C — Weaker GPU pair
  - Step 4 — Confirm the failure changed only the intended path
- 9. Validation
- 10. Verification
- 11. Observability
- 12. Performance Measurements
- 13. Failure Injection
- 14. Troubleshooting
  - Step 1 — Inventory
  - Step 2 — Local peer path
  - Step 3 — Host RDMA
  - Step 4 — GPU-aware transport
  - Step 5 — Collective construction
  - Step 6 — Application
  - Root-cause statement template
- 15. Cleanup
- 16. Summary
- 17. Challenge Exercises
- 18. Further Reading
