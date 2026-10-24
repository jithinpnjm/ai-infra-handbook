# nvidia-devops-zth-v05


## Chapter 1 — Why DGX Exists: The Whitebox Fallacy  (chapter-01-why-dgx-exists.md)
- Introduction
- 1. The Physics of the Problem
- 2. The DGX Philosophy: The Reference Architecture
  - The NVSwitch Baseboard
  - The Network Topography
- Architectural Diagram: The Whitebox vs The DGX
- 3. The Software Verification Stack
- Customer Scenario (Senior Level)
- Interview Preparation

## Chapter 2 — Inside the DGX H100 System  (chapter-02-inside-a-dgx-system.md)
- Introduction
- 1. The Compute Tray (The Top Half)
  - The CPUs and System RAM
  - The Storage (NVMe)
  - The Data Processing Units (DPUs)
- 2. The GPU Tray (The Bottom Half)
  - The GPUs
  - The NVSwitches
- 3. The Networking (The Back Panel)
  - The Compute Network (OSFP)
  - The Storage/Management Network (QSFP112)
  - The In-Band and Out-of-Band (OOB) Management
- Architectural Diagram: Internal Topology
- Customer Scenario (Senior Level)
- Interview Preparation

## Chapter 3 — The DGX Management Plane and Redfish APIs  (chapter-03-dgx-management-plane.md)
- Introduction
- 1. The Baseboard Management Controller (BMC)
- 2. From IPMI to the Redfish API
  - Automating the AI Factory with Redfish
- 3. NVsm: NVIDIA System Management
- Architectural Diagram: OOB vs In-Band Management
- Customer Scenario (Senior Level)
- Interview Preparation

## Chapter 4 — Power, Cooling, and Facility Readiness  (chapter-04-power-cooling-and-rack-readiness.md)
- Introduction
- 1. The Power Crisis (High Density Compute)
  - The End of 120V Wall Power
- 2. The Cooling Crisis (The Limits of Air)
  - Standard Air Cooling (Failing)
  - Rear Door Heat Exchangers (RDHx)
  - Direct Liquid Cooling (DLC) - The B200 Era
- Architectural Diagram: The Transition to Liquid
- 3. Weight and Structural Integrity
- Customer Scenario (Senior Level)
- Interview Preparation

## Chapter 5 — Storage and Data Paths: Bypassing the CPU  (chapter-05-dgx-storage-and-data-paths.md)
- Introduction
- 1. The Legacy Storage Path (The CPU Bounce Buffer)
- 2. GPUDirect Storage (GDS)
- 3. Parallel File Systems (The Data Lakehouse)
- Customer Scenario (Senior Level)
- Interview Preparation

## Chapter 6 — Networking and Fabric Integration  (chapter-06-dgx-networking-and-fabric-integration.md)
- Introduction
- 1. The Four Planes of AI Networking
  - 1. The Compute Fabric (The Backend)
  - 2. The Storage Fabric
  - 3. The In-Band Management Fabric (The Frontend)
  - 4. The Out-Of-Band Management Fabric (OOB)
- 2. Rail-Optimized Topologies
- Architectural Diagram: Rail Optimization
- Customer Scenario (Senior Level)
- Interview Preparation

## Chapter 7 — Rack-Scale Computing: GH200 and GB200 NVL72  (chapter-07-dgx-gh200-and-gb200-systems.md)
- Introduction
- 1. Expanding the Domain: The NVLink Switch Tray
- 2. The GB200 NVL72 Architecture
  - Why Copper?
- 3. Total Direct Liquid Cooling (DLC)
- Customer Scenario (Senior Level)
- Interview Preparation

## Volume 05 — DGX Systems  (index.md)
- DGX as a System
- Planned Chapter Sequence
- Labs
- Production Perspective

## Lab 01 — Build a DGX Health Baseline  (labs/lab-01-build-a-dgx-health-baseline.md)
- Lab metadata
- Objective
- Background
- Learning outcomes
- Architecture
- Prerequisites
- Environment
- Step 1 — Capture host identity
- Step 2 — Capture PCIe and storage inventory
- Step 3 — Capture GPU inventory and telemetry
- Step 4 — Capture software versions
- Step 5 — Capture network state
- Step 6 — Capture error evidence
- Step 7 — Run a minimal functional check
- Step 8 — Create acceptance criteria
- Validation
- Verification
- Observability
- Performance measurements
- Failure injection
  - Failure 1 — Version drift
  - Failure 2 — Missing interface
- Troubleshooting
  - GPU count is lower than expected
  - Topology differs from peers
  - Functional container cannot access GPUs
- Cleanup
- Summary
- Challenge exercises
- Further reading

## Lab 02 — Validate DGX Data and Network Paths  (labs/lab-02-validate-dgx-data-and-network-paths.md)
- Lab Metadata
- 1. Objective
- 2. Background
- 3. Learning Outcomes
- 4. Architecture
- 5. Prerequisites
- 6. Environment Record
- 7. Components
- 8. Deployment Steps
  - Step 1 — Inspect block devices
  - Step 2 — Run a safe local write/read test
  - Step 3 — Inspect NIC health
  - Step 4 — Map devices to NUMA and PCIe topology
  - Step 5 — Validate host-to-host connectivity
  - Step 6 — Validate collectives
- 9. Validation
- 10. Verification
- 11. Observability
- 12. Performance Measurements
- 13. Failure Injection
- 14. Troubleshooting
  - Collectives hang
  - Storage throughput is unstable
  - One GPU group communicates more slowly
- 15. Cleanup
- 16. Summary
- 17. Challenge Exercises
- 18. Further Reading
