# nvidia-devops-zth-v06


## Chapter 1 — Why HGX Exists: The Merchant Silicon Strategy  (chapter-01-why-hgx-exists.md)
- Introduction
- 1. What is HGX?
  - What is Missing?
- 2. Why Hyperscalers and OEMs Need HGX
  - 2.1 The Hyperscaler Reality (AWS, Azure, GCP)
  - 2.2 The Enterprise OEM Reality (Dell, HPE, Supermicro)
- Architectural Diagram: DGX vs. OEM HGX
- 3. The Trade-offs of the HGX Approach
- Customer Scenario (Senior Level)
- Interview Preparation

## Chapter 2 — Inside an HGX Platform  (chapter-02-inside-an-hgx-platform.md)
- Introduction
- 1. The Anatomy of the HGX Tray
  - 1.1 The SXM Modules
  - 1.2 The NVSwitches
  - 1.3 The PCIe Retimers
- Architectural Diagram: The HGX Tray Topography
- 2. Power Delivery: The 54V Shift
- 3. Form Factors: 4-GPU vs 8-GPU (Delta vs Redstone)
- Customer Scenario (Senior Level)
- Interview Preparation

## Chapter 3 — OEM Integration and Support Boundaries  (chapter-03-oem-integration-and-support-boundaries.md)
- Introduction
- 1. The Physical Boundary
- 2. The Firmware Boundary (The Danger Zone)
  - The "Frankenstein" Risk
- 3. NVIDIA-Certified Systems and NVIDIA Qualification Testing
- Customer Scenario (Senior Level)
- Interview Preparation

## Chapter 4 — HGX Topology and Data Paths  (chapter-04-hgx-topology-and-data-paths.md)
- Introduction
- 1. The Ideal Topology: Symmetrical and Balanced
- 2. The Nightmare Topology: Unbalanced and CPU-Bound
- Architectural Diagram: Balanced vs. Unbalanced OEM Layouts
- 3. Detecting the Topology (`nvidia-smi topo -m`)
  - Identifying a Balanced Server (GPUDirect Enabled)
  - Identifying an Unbalanced Server (CPU Bottlenecked)
- Customer Scenario (Senior Level)
- Interview Preparation

## Chapter 5 — Power, Cooling, and Rack Integration  (chapter-05-hgx-power-cooling-and-rack-integration.md)
- Introduction
- 1. Power Delivery: The 54-Volt Transition
  - The OEM 54V Power Architecture
- 2. Air Cooling: The Shadowing Problem
  - Airflow Shadowing
- 3. Direct Liquid Cooling (DLC) at the Edge
  - Closed-Loop Liquid Cooling (CLLC)
- Architectural Diagram: The OEM Cooling Challenge
- Customer Scenario (Senior Level)
- Interview Preparation

## Chapter 6 — HGX Networking, Storage, and Cluster Integration  (chapter-06-hgx-networking-storage-and-cluster-integration.md)
- Introduction
- 1. The Compute Fabric (The NIC-to-GPU Ratio)
  - The 1:1 Rule
  - The PCIe Switch Proximity Rule
- 2. Rail-Optimized Cabling in OEM Clusters
- 3. Storage Integration and GDS (GPUDirect Storage)
  - The NVMe Placement
  - E1.S and U.2 Form Factors
- Architectural Diagram: The Perfect OEM Integration
- Customer Scenario (Senior Level)
- Interview Preparation

## Chapter 7 — GB200 NVL72: The Rack-Scale Era  (chapter-07-gb200-nvl72-rack-scale-architecture.md)
- Introduction
- 1. Deconstructing the HGX: Compute Trays and Switch Trays
  - 1.1 The Compute Tray
  - 1.2 The Switch Tray
- 2. The Copper Backplane (The Magic Link)
- Architectural Diagram: The NVL72 Rack
- 3. The End of the Standard OEM Server
- Customer Scenario (Senior Level)
- Interview Preparation

## Volume 06 — HGX Platforms & OEM Integration  (index.md)
- Introduction
- What You Will Learn
- Why This Matters for Senior Architects
- Chapter Progression

## Lab 01 — Compare HGX-Based Server Designs  (labs/lab-01-compare-hgx-server-designs.md)
- Lab metadata
- Objective
- Background
- Learning outcomes
- Architecture
- Prerequisites
- Environment
- Step 1 — Write the customer requirement
- Step 2 — Separate platform boundaries
- Step 3 — Build the technical comparison
- Step 4 — Draw each topology
- Step 5 — Evaluate facility fit
- Step 6 — Evaluate lifecycle and support
- Step 7 — Define acceptance tests
- Validation
- Verification
- Observability
- Performance measurements
- Failure injection
  - Failure 1 — Remove topology evidence
  - Failure 2 — Change the facility constraint
- Troubleshooting
  - Proposals appear identical
  - Vendor data uses different terminology
  - No candidate satisfies every preference
- Cleanup
- Summary
- Challenge exercises
- Further reading

## Lab 02 — Review an HGX Rack Design  (labs/lab-02-review-an-hgx-rack-design.md)
- Lab Metadata
- 1. Objective
- 2. Background
- 3. Learning Outcomes
- 4. Architecture
- 5. Prerequisites
- 6. Environment
- 7. Components
- 8. Deployment Steps
  - Step 1 — Build the rack elevation
  - Step 2 — Calculate power
  - Step 3 — Calculate thermal load
  - Step 4 — Review weight and logistics
  - Step 5 — Review network fabrics
  - Step 6 — Trace failure domains
  - Step 7 — Define commissioning tests
- 9. Validation
- 10. Verification
- 11. Observability
- 12. Performance Measurements
- 13. Failure Injection
- 14. Troubleshooting
  - Rack passes power review but overheats
  - Redundant feed test shuts down servers
  - Collective tests underperform
- 15. Cleanup
- 16. Summary
- 17. Challenge Exercises
- 18. Further Reading
