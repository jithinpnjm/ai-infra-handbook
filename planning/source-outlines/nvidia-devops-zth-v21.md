# nvidia-devops-zth-v21


## Chapter 01 — AI Factory Fundamentals and Design Principles  (chapter-01-ai-factory-fundamentals-and-design-principles.md)
- Chapter Metadata
- Beginner's Primer: The AI Factory
- PART 1: WHY DESIGN PRINCIPLES MATTER BEFORE INFRASTRUCTURE
  - The Factory Mindset
- PART 2: WORKLOAD CHARACTERIZATION
  - 2.1 The Five Dimensions of Workload
  - 2.2 Concrete Workload Profiles
    - Example A: LLM Training Cluster (Internal Research)
    - Example B: Production LLM Inference Service
    - Example C: Fine-tuning Service (LoRA, 100s of Customers)
  - 2.3 Workload Classification Flowchart
- PART 3: COST ANALYSIS AND TARGETS
  - 3.1 The Cost Tree
  - 3.2 Cost Per Output Calculation
    - Training Cost Per Compute-Day
    - Inference Cost Per Million Tokens
  - 3.3 Cost Target Setting
- PART 4: SERVICE-LEVEL AGREEMENTS (SLAs)
  - 4.1 Three SLA Tiers
  - 4.2 Concrete SLA Definition: Production LLM API
  - 4.3 Building SLAs Into Infrastructure Design
- PART 5: DECISION TREES FOR DESIGN TRADE-OFFS
  - 5.1 GPU Selection Decision Tree
  - 5.2 Interconnect Choice Decision Tree
- PART 6: INTERVIEW ANSWER: "HOW DO YOU CHOOSE INFRASTRUCTURE FOR A NEW WORKLOAD?"
- Architecture Summary
- SUMMARY

## Chapter 02 — GPU Compute Cluster Design  (chapter-02-gpu-compute-cluster-design.md)
- Chapter Metadata
- Beginner's Primer: Building the Mega-Node
- PART 1: GPU SELECTION MECHANICS
  - 1.1 GPU Landscape (selected data center GPUs)
  - 1.2 Cost Per TFLOP Analysis
- PART 2: SINGLE-NODE DESIGN
  - 2.1 Node Configurations
    - Configuration A: 8×H100 SXM5 Dense Training Node
    - Configuration B: 8×H100 PCIe Cluster Node + Storage
    - Configuration C: GB200 NVL72 Rack (reference only)
  - 2.2 Node Selection Decision Tree
- PART 3: MULTI-NODE TOPOLOGY DESIGN
  - 3.1 Topologies and Their Trade-offs
    - Topology 1: Single-Pod, Leaf Only (up to about 8 nodes, 64 GPUs)
    - Topology 2: Two-Tier Fat-Tree (leaf and spine, hundreds to thousands of GPUs)
    - Topology 3: Three-Tier or Dragonfly-Style (very large scale)
  - 3.2 Worked Example: 128-GPU Cluster (16 nodes)
- PART 4: INTERCONNECT SELECTION
  - 4.1 Interconnect Comparison Matrix
  - 4.2 Decision Tree: Which Interconnect?
- PART 5: TROUBLESHOOTING TABLE: GPU CLUSTER PERFORMANCE DEGRADATION
- PART 6: INTERVIEW ANSWER: "HOW DO YOU JUSTIFY PREMIUM INTERCONNECT COSTS?"
- Architecture Summary
- SUMMARY

## Chapter 03 — High-Speed Networking Architecture  (chapter-03-high-speed-networking-architecture.md)
- Chapter Metadata
- Beginner's Primer: The Communication Tax
- PART 1: COLLECTIVE COMMUNICATION FUNDAMENTALS
  - 1.1 Why Collectives Matter at Scale
  - 1.2 Key Collective Operations
- PART 2: COLLECTIVE ALGORITHMS
  - 2.1 Ring AllReduce (Linear Scaling at Scale)
  - 2.2 Recursive Doubling (Low-Latency Variant)
  - 2.3 Tree AllReduce (Moderate Latency)
- PART 3: COLLECTIVE LIBRARY IMPLEMENTATIONS
  - 3.1 NVIDIA NCCL (The Standard)
  - 3.2 Reducing Launch Overhead with CUDA Graphs
- PART 4: TOPOLOGY-SPECIFIC OPTIMIZATIONS
  - 4.1 Single-Pod NVLink Topology Optimization
  - 4.2 Multi-Rack Fat-Tree Optimization
  - 4.3 InfiniBand Specific: Lossless Credit-Based Flow Control vs RoCE PFC
- PART 5: BANDWIDTH OPTIMIZATION TECHNIQUES
  - 5.1 Gradient Compression
  - 5.2 Communication-Overlap: Computation-Communication Pipelining
- PART 6: MEASUREMENT & TUNING
  - 6.1 Measuring Collective Performance
  - 6.2 Tuning NCCL for Your Cluster
- PART 7: TROUBLESHOOTING TABLE
- Architecture Summary
- SUMMARY

## Chapter 04 — Storage Infrastructure for AI Pipelines  (chapter-04-storage-infrastructure-for-ai-pipelines.md)
- Chapter Metadata
- Beginner's Primer: Feeding the Beast
- PART 1: STORAGE BOTTLENECK ANALYSIS
  - 1.1 Data Throughput Demands
  - 1.2 Storage Tier Strategy
- PART 2: DATA PIPELINE DESIGN
  - 2.1 Reference Architecture: 64-GPU Training Cluster
  - 2.2 Data Loading Pipeline (PyTorch Example)
- PART 3: CHECKPOINT MANAGEMENT
  - 3.1 Checkpoint Strategy
  - 3.2 Checkpoint Resume & Validation
- PART 4: STORAGE FAILURE HANDLING
- Architecture Summary
- SUMMARY

## Chapter 05 — Power Delivery and Thermal Management  (chapter-05-power-delivery-and-thermal-management.md)
- Chapter Metadata
- Beginner's Primer: The Physics of AI
- PART 1: POWER CONSUMPTION ANALYSIS
  - 1.1 Component Power Budgets
  - 1.2 Cluster-Level Power Budget
- PART 2: COOLING DESIGN
  - 2.1 Cooling Technologies Comparison
  - 2.2 Reference Cooling Design: 64-GPU Air-Cooled Deployment
  - 2.3 Thermal Shutdown & Throttling
- PART 3: POWER DELIVERY ARCHITECTURE
  - 3.1 Power Distribution Tiers
  - 3.2 Power Consumption Forecasting
- PART 4: TROUBLESHOOTING TABLE
- Architecture Summary
- SUMMARY

## Chapter 06 — Software Stack Integration  (chapter-06-software-stack-integration.md)
- Chapter Metadata
- Beginner's Primer: The Software Glue
- PART 1: CUDA RUNTIME CONFIGURATION
  - 1.1 CUDA Version & Driver Alignment
  - 1.2 CUDA Memory Management
- PART 2: PYTORCH DISTRIBUTED TRAINING SETUP
  - 2.1 DDP (Distributed Data Parallel) Configuration
  - 2.2 DeepSpeed Integration (Production-Grade Training)
- PART 3: MULTI-FRAMEWORK ORCHESTRATION
  - 3.1 PyTorch + JAX Interop
  - 3.2 Kubernetes Orchestration for Distributed Training
- PART 4: TROUBLESHOOTING TABLE
- Architecture Summary
- SUMMARY

## Chapter 07 — Multi-Node Distributed Training  (chapter-07-multi-node-distributed-training.md)
- Beginner's Primer: Beyond a Single Server
- PART 1: SCALING STRATEGIES
  - 1.1 Data Parallelism (Batch Size Scaling)
  - 1.2 Pipeline Parallelism (Stage Splitting)
  - 1.3 Tensor Parallelism (Intra-Layer Sharding)
- PART 2: FAULT TOLERANCE & CHECKPOINTING
  - 2.1 Checkpoint Resume Strategy
  - 2.2 Detecting & Recovering from Failures
- PART 3: TROUBLESHOOTING PERFORMANCE DEGRADATION
- Architecture Summary
- SUMMARY

## Chapter 08 — Inference Serving at Scale  (chapter-08-inference-serving-at-scale.md)
- Beginner's Primer: The Inference Economics
- PART 1: INFERENCE ARCHITECTURE FUNDAMENTALS
  - 1.1 Throughput vs. Latency Trade-off
  - 1.2 vLLM Serving Architecture
- PART 2: MULTI-GPU INFERENCE SCALING
  - 2.1 Tensor Parallelism for Inference
  - 2.2 Multi-GPU Serving Cluster
- PART 3: SERVING CHALLENGES & SOLUTIONS
- Architecture Summary
- SUMMARY

## Chapter 09 — Multi-Region Deployment  (chapter-09-multi-region-deployment.md)
- Beginner's Primer: The Speed of Light
- PART 1: MULTI-REGION ARCHITECTURE
  - 1.1 Active-Active Inference Serving
  - 1.2 Disaster Recovery & Failover
- PART 2: CROSS-REGION TRAINING COORDINATION
  - 2.1 Asynchronous Model Synchronization
- Architecture Summary
- SUMMARY

## Chapter 10 — Monitoring and Operations  (chapter-10-monitoring-and-operations.md)
- Beginner's Primer: The AI Command Center
- PART 1: OBSERVABILITY STACK
  - 1.1 Key Metrics for Production Clusters
  - 1.2 Prometheus Scrape Configuration
- PART 2: ALERTING RULES
  - 2.1 SLO-Driven Alerts
- PART 3: OPERATIONAL PROCEDURES
  - 3.1 Incident Response Playbook
- Architecture Summary
- SUMMARY

## Chapter 11 — Capacity Planning and Forecasting  (chapter-11-capacity-planning-and-forecasting.md)
- Beginner's Primer: The Supply Chain Reality
- PART 1: DEMAND FORECASTING
  - 1.1 Forecasting Model
  - 1.2 Hardware Refresh Cycles
- PART 2: CAPACITY PLANNING DECISIONS
  - 2.1 Capacity vs. Cost Trade-off
- Architecture Summary
- SUMMARY

## Chapter 12 — Cost Optimization and Resource Efficiency  (chapter-12-cost-optimization-and-resource-efficiency.md)
- Beginner's Primer: The Price of Idle Silicon
- PART 1: UTILIZATION OPTIMIZATION
  - 1.1 GPU Utilization Strategies
  - 1.2 Cost per Output Metric
- PART 2: SPOT INSTANCES & CLOUD STRATEGY
  - 2.1 Spot Instance Pricing
  - 2.2 Implementing Spot Instance Resilience
- PART 3: COST BREAKDOWN ANALYSIS
- Architecture Summary
- SUMMARY

## Chapter 13 — Reference Architecture: 100-GPU Training Cluster  (chapter-13-reference-architecture-100-gpu-training-cluster.md)
- Beginner's Primer: Putting It All Together
- COMPLETE DESIGN: 70B-CLASS LLM TRAINING
  - Cluster Specification
  - Hardware Cost Breakdown
  - Deployment Procedure
  - AI Factory Commissioning and Acceptance
  - Operational Procedures
- Architecture Summary
- SUMMARY

## Chapter 14 — Reference Architecture: Multi-Region Inference Deployment  (chapter-14-reference-architecture-multi-region-inference-deployment.md)
- Beginner's Primer: The Global Cash Register
- COMPLETE DESIGN: GLOBAL LLAMA INFERENCE (2000 QPS, 99.9% SLA)
  - Global Deployment Spec
  - Kubernetes Deployment
  - Disaster Recovery Procedures
- SUMMARY
- Architecture Summary
- VOLUME 21 CONCLUSION

## Volume 21 — AI Factory: Building Large-Scale Production Systems  (index.md)
- Overview
- Chapters
  - Chapter 1: AI Factory Fundamentals and Design Principles
  - Chapter 2: GPU Compute Cluster Design
  - Chapter 3: High-Speed Networking Architecture
  - Chapter 4: Storage Infrastructure for AI Pipelines
  - Chapter 5: Power Delivery and Thermal Management
  - Chapter 6: Software Stack Integration
  - Chapter 7: Multi-Node Distributed Training
  - Chapter 8: Inference Serving at Scale
  - Chapter 9: Multi-Region Deployment
  - Chapter 10: Monitoring and Operations
  - Chapter 11: Capacity Planning and Forecasting
  - Chapter 12: Cost Optimization and Resource Efficiency
  - Chapter 13: Reference Architecture — 100-GPU Training Cluster
  - Chapter 14: Reference Architecture — Multi-Region Inference Deployment
- Labs
- How to Use
- Cross-References

## Lab 01 — Cluster Design Workshop  (labs/lab-01-cluster-design-workshop.md)
- Objective
- Scenario
- Design Phases (120 min total)
  - Phase 1: Workload Characterization (20 min)
  - Phase 2: Infrastructure Sizing (30 min)
  - Phase 3: Cost-Benefit Analysis (25 min)
  - Phase 4: Design Validation (25 min)
  - Phase 5: Presentation (20 min)
- Example Solution (Reference)
- Rubric & Scoring
- Success Criteria

## Lab 02 — Networking Simulation  (labs/lab-02-networking-simulation.md)
- Objective
- Setup
- Exercise 1: Ring AllReduce (20 min)
- Exercise 2: Tree vs Ring (20 min)
- Exercise 3: Topology Simulation (30 min)
- Exercise 4: Throughput Impact (20 min)
- Deliverables
- Success Criteria

## Lab 03 — Storage Pipeline Design  (labs/lab-03-storage-pipeline-design.md)
- Objective
- Scenario
- Exercise 1: Single-GPU Pipeline (20 min)
- Exercise 2: Distributed Loading (20 min)
- Exercise 3: Storage Tiering (30 min)
- Exercise 4: Checkpoint & Resume (30 min)
- Success Criteria

## Lab 04 — Capacity Planning Exercise  (labs/lab-04-capacity-planning-exercise.md)
- Objective
- Scenario
- Exercise 1: Demand Forecasting (30 min)
- Exercise 2: Hardware Refresh Planning (30 min)
- Exercise 3: TCO & Utilization Analysis (30 min)
- Exercise 4: Cost Optimization (30 min)
- Deliverables
- Success Criteria
