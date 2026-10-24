# nvidia-devops-zth-v16


## Chapter 01 — Why GPU Observability Is Fundamentally Different  (chapter-01-why-gpu-observability-is-fundamentally-different.md)
- Learning Objectives
- Beginner's Primer: Why standard monitoring tools fail for AI
- The Core Problem: GPU Metrics Are Not CPU Metrics
- The Three Categories of GPU Signals
  - Why this three-way view is mandatory
- The Observability Stack for GPUs
  - Myth vs. Reality
- Evidence: Reading GPU Health in One Command
- Worked Example: The Diagnosis Hierarchy
- Interview Questions Worth Preparing
- Architecture Summary
- Key Takeaways
- Cross-References

## Chapter 02 — Signals, Metrics, Logs, Traces, and Evidence  (chapter-02-signals-metrics-logs-traces-and-evidence.md)
- Learning Objectives
- Beginner's Primer: The 3 Pillars of Observability
- Three Signal Types, Three Purposes
  - Metrics: "What is the steady state?"
  - Logs: "What went wrong?"
  - Traces: "Why is this kernel slow?"
- The Observability Stack: How to Collect All Three
  - Level 1: Metrics via DCGM + Prometheus
  - Level 2: Logs via DCGM Events and Kernel Logs
  - Level 3: Traces for Deep Profiling
- Combining Signals: The Diagnosis Workflow
  - Worked Example: "Training Job Is Slower Than Yesterday"
- Architecture Summary
- Key Takeaways
- Cross-References

## Chapter 03 — Core GPU Metrics and Interpretation  (chapter-03-core-gpu-metrics-and-interpretation.md)
- Learning Objectives
- Beginner's Primer: Deceptive Metrics
- Metric 1: GPU Utilization
  - The Three Utilization Scenarios
  - Reading GPU Utilization Correctly
  - Utilization Over Time: Steady vs. Oscillating
  - Alert Thresholds for Utilization
- Metric 2: Memory
  - Three Memory Numbers You Need
  - The Hidden Layer: Fragmentation and Allocation Stalls
  - Memory Pressure and the Reclaim Path
  - Alert Thresholds for Memory
- Metric 3: Temperature
  - Temperature Vs. Thermal Throttling
  - Temperature Trends and Headroom
  - Detecting Thermal Throttling in Metrics
- Metric 4: Clock Frequencies
  - Clock Rates Tell You What's Happening
  - Alert Thresholds for Clocks
- Metric 5: Power Consumption
  - Power and Thermal Interaction
- Putting It Together: Multi-Metric Diagnosis
- Architecture Summary
- Key Takeaways
- Cross-References

## Chapter 04 — DCGM: The GPU Metrics Foundation  (chapter-04-dcgm-the-gpu-metrics-foundation.md)
- Learning Objectives
- Beginner's Primer: What is DCGM?
- What DCGM Does
  - Embedded versus standalone
  - Fields and watches: why DCGM stays cheap
- Installing and Starting DCGM
  - Step 1: Install the DCGM 4 packages
  - Step 2: Start the host engine
  - Step 3: Sample live fields and run a quick diagnostic
- Core DCGM Metrics
  - Execution Metrics
  - Memory Metrics
  - Reliability Metrics
- Querying DCGM
  - Method 1: `dcgmi`
  - Method 2: Language bindings
  - Method 3: The Prometheus exporter (production default)
- DCGM in Production: Reliability and Recovery
  - Monitor the monitor
  - Logging for problem reports
  - GPUs that detach or disappear
- Worked Example: DCGM Does Not List a GPU That `nvidia-smi` Shows
- Architecture Summary
- Key Takeaways
- Cross-References

## Chapter 05 — Prometheus, Grafana, and Observability Dashboards  (chapter-05-prometheus-grafana-and-observability-dashboards.md)
- Learning Objectives
- Beginner's Primer: Exporters, Prometheus, and Grafana
- The Prometheus + DCGM Pipeline
- Configuring Prometheus for GPU Metrics
  - Step 1: Add DCGM Scrape Config
  - Step 2: Verify Metrics Are Flowing
- Building Effective GPU Dashboards in Grafana
  - Dashboard 1: GPU Fleet Health (Cluster-Level)
  - Dashboard 2: Individual GPU Deep Dive (Per-GPU)
- Alert Rules for GPUs
- Real Dashboard Screenshots (Scenarios)
  - Scenario 1: Healthy GPU Cluster
  - Scenario 2: One GPU Idle (Possible Problem)
  - Scenario 3: Data Starvation (Classic Problem)
- Architecture Summary
- Key Takeaways
- Cross-References

## Chapter 06 — Distributed Observability: Multi-GPU and Multi-Node Systems  (chapter-06-distributed-observability-multi-gpu-and-multi-node.md)
- Learning Objectives
- Beginner's Primer: The Convoy Problem
- The Observability Layers in Distributed Systems
- Multi-GPU Observability on a Single Node
  - Scenario: Two A100s on the Same Node
  - Metrics for Detecting Multi-GPU Contention
  - Real Example: Diagnosing NVLink Saturation
- Multi-Node Observability
  - Scenario: 8-GPU Cluster (2 nodes, 4 GPUs each)
  - Distributed Metrics Collection
- Collective Communication and NCCL
  - Detecting NCCL Bottlenecks
  - Real Evidence: NCCL Performance
- Worked Example: Diagnosing Multi-Node Training Slowdown
- Architecture Summary
- Key Takeaways
- Cross-References

## Chapter 07 — Traces, Profiling, and Deep Performance Diagnosis  (chapter-07-traces-profiling-and-deep-performance-diagnosis.md)
- Learning Objectives
- Beginner's Primer: Metrics vs Traces
- Three Profiling Tools and When to Use Them
- Method 1: nvidia-smi Profiling (Quick Orientation)
- Method 2: Nsight Compute (Detailed Kernel Analysis)
  - Real Example: Comparing Two Kernels
- Method 3: Nsys (System-Wide Tracing)
- Interpreting Memory-Bound vs. Compute-Bound
  - Memory-Bound Kernel
  - Compute-Bound Kernel
  - Instruction-Bound Kernel
- Profiling Workflows
  - Workflow 1: Identifying Regressions
  - Workflow 2: Profiling Under Load
- Architecture Summary
- Key Takeaways
- Cross-References

## Chapter 08 — Common GPU Failure Modes and Detection  (chapter-08-common-gpu-failure-modes-and-detection.md)
- Learning Objectives
- Beginner's Primer: Xid Errors
- Failure Mode 1: GPU Thermal Throttling (Overheating)
- Failure Mode 2: ECC Error Spike
- Failure Mode 3: GPU Fell Off the Bus (Hardware Disconnection)
- Failure Mode 4: Memory Allocation Stall (Fragmentation or OOM)
- Failure Mode 5: Straggler GPU (One GPU Much Slower Than Others)
- Summary: Failure Signatures
- Architecture Summary
- Key Takeaways
- Cross-References

## Chapter 09 — Health Checks and SLOs for GPU Clusters  (chapter-09-health-checks-and-slos-for-gpu-clusters.md)
- Learning Objectives
- Beginner's Primer: SLI vs SLO vs SLA
- SLIs: What to Measure
- SLOs: The Commitments
- Automated Health Checks
  - Check 1: Per-GPU Readiness
  - Check 2: Distributed Health (Multi-Node)
- Error Budgets: Balancing Reliability and Velocity
- SLO Violation and Impact
- Architecture Summary
- Cross-References

## Chapter 10 — Production Troubleshooting Frameworks  (chapter-10-production-troubleshooting-frameworks.md)
- Learning Objectives
- Beginner's Primer: The MTTR Metric
- Framework 1: GPU Job Slow/Failed
  - Real Example: Slow Training Job
- Framework 2: GPU Temperature Rising
- Framework 3: ECC Errors Appearing
- Framework 4: Multi-GPU Job Stall (One GPU Slow)
- Key Commands in Order of Frequency
- Anti-Patterns (Slow Paths)
- Architecture Summary
- Key Takeaways
- Cross-References

## Chapter 11 — Observability for Inference at Scale  (chapter-11-observability-for-inference-at-scale.md)
- Learning Objectives
- Beginner's Primer: Inference vs Training Metrics
- Inference Workload Characteristics
- Inference Metrics and SLIs
- Inference Server Observability
  - Real Example: Monitoring LLM Inference
- Inference Bottleneck Diagnosis
- Inference Cost Optimization
- Architecture Summary
- Key Takeaways
- Cross-References

## Chapter 12 — Incident Response and Postmortems  (chapter-12-incident-response-and-postmortems.md)
- Learning Objectives
- Beginner's Primer: The Value of a Runbook
- Incident Response Runbooks
  - Runbook 1: GPU Thermal Throttle Alert
  - Runbook 2: GPU Memory OOM Alert
  - Runbook 3: Cluster Availability &lt; SLO
- Postmortem Template
- Preventing Recurrence
- Architecture Summary
- Key Takeaways
- Cross-References

## Volume 16 — GPU Observability and Operational Health  (index.md)
- Volume at a Glance
- Learning Arc
- Chapters
  - Foundations
  - Architecture
  - Operations
- Labs
- Structure and Content
  - Depth-Rework Principles Applied
- How to Use This Volume
- Key Concepts You'll Understand
- Prerequisites
- Cross-References
- Estimated Time Commitment

## Lab 01 — Setting Up DCGM and Prometheus for GPU Monitoring  (labs/lab-01-setting-up-dcgm-and-prometheus-for-gpu-monitoring.md)
- Step 1: Install DCGM 4
- Step 2: Start the DCGM host engine
- Step 3: Run a quick diagnostic
- Step 4: Run the DCGM Prometheus exporter
- Step 5: Verify Metrics Are Exported
- Step 6: Install and Configure Prometheus
- Step 7: Query Your First Metric
- Step 8: Generate Some GPU Load (to see metrics change)
- Verification Checklist
- Troubleshooting
- Self-Assessment
- Key Concepts Reinforced
- Cleanup

## Lab 02 — Building and Interpreting GPU Dashboards  (labs/lab-02-building-and-interpreting-gpu-dashboards.md)
- Step 1: Install Grafana
- Step 2: Add Prometheus Data Source
- Step 3: Create Dashboard from Scratch
  - Panel 1: GPU Utilization (Gauge)
  - Panel 2: Temperature (Graph)
  - Panel 3: Memory Usage (Gauge)
  - Panel 4: GPU Clock Rate (Graph)
- Step 4: Load Test and Observe
  - Scenario A: Idle GPU
  - Scenario B: Light Compute Load
  - Scenario C: Heavy Compute Load
  - Scenario D: Memory Pressure
- Step 5: Create Alert Rules
- Dashboard Interpretation Scenarios
  - Scenario 1: Healthy Training Job
  - Scenario 2: Thermal Throttle Imminent
  - Scenario 3: Data Pipeline Starvation
  - Scenario 4: One GPU in Multi-GPU Job Slower
- Verification Checklist
- Key Takeaways
- Cleanup

## Lab 03 — Profiling GPU Performance and Optimization  (labs/lab-03-profiling-gpu-performance-and-optimization.md)
- Step 1: Write a Matrix Multiply Kernel
- Step 2: Profile with nvidia-smi
- Step 3: Deep Profile with Nsight Compute
- Step 4: Measure Memory Bandwidth
- Step 5: Compare Compute-Bound vs. Memory-Bound
- Step 6: Measure Impact of Optimization
- Verification Checklist
- Key Takeaways

## Lab 04 — Incident Response Simulation  (labs/lab-04-incident-response-simulation.md)
- Setup: Running Simulated Workloads
- Scenario 1: Thermal Throttle Incident
- Scenario 2: GPU Memory OOM
- Scenario 3: Data Pipeline Starvation (One GPU Slow)
- Scenario 4: Multi-GPU Load Imbalance
- Verification Checklist
- Self-Assessment: Incident Response Competency
- Key Takeaways
