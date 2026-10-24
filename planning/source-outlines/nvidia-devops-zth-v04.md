# nvidia-devops-zth-v04


## Chapter 1 — Why NVIDIA Has Multiple GPU Families  (chapter-01-why-nvidia-has-multiple-gpu-families.md)
- Introduction
- 1. The Three Tiers of NVIDIA GPUs
  - 1.1 GeForce (Gaming & Enthusiast)
  - 1.2 RTX Professional / Quadro (Workstation & Visualization)
  - 1.3 Data Center (The Heavy Iron)
- 2. The Technical Showstoppers for Gaming GPUs
  - Reason 1: The Networking Bottleneck (No GPUDirect)
  - Reason 2: The Interconnect Bottleneck (No NVLink)
  - Reason 3: No Error-Correcting Code (ECC) Memory
  - Reason 4: Thermal Design Power (TDP) and Physical Spacing
- 3. The Licensing Showstopper (The EULA)
- Customer Scenario (Senior Level)
- Interview Preparation
- Summary

## Chapter 2 — Workload-First GPU Selection  (chapter-02-workload-first-gpu-selection.md)
- Introduction
- 1. Workload Profile A: LLM Pre-Training (From Scratch)
- 2. Workload Profile B: LLM Inference (Serving)
- 3. Workload Profile C: Computer Vision & Video Processing
- Architectural Decision Matrix
- Customer Scenario (Senior Level)
- Interview Preparation

## Chapter 3 — Accelerator Generations and Design Shifts  (chapter-03-accelerator-generations-and-design-shifts.md)
- Introduction
- 1. Volta (V100) — The Dawn of the AI Era (2017)
- 2. Ampere (A100) — Enterprise Isolation and Sparsity (2020)
- 3. Hopper (H100) — The Era of the LLM (2022)
- 4. Blackwell (B200 / GB200) — Rack-Scale Compute (2024)
- Architectural Summary Matrix
- Customer Scenario (Senior Level)
- Interview Preparation

## Chapter 4 — Form Factors: PCIe vs. SXM  (chapter-04-pcie-sxm-and-platform-integration.md)
- Introduction
- 1. The PCIe Form Factor (The Standard Upgrade)
  - The Advantages
  - The Severe Limitations
- 2. The SXM Form Factor (The Heavy Iron)
  - The HGX Baseboard
  - The Advantages
  - The Severe Limitations
- Architectural Comparison Matrix
- Customer Scenario (Senior Level)
- Interview Preparation

## Chapter 5 — Inference Accelerators: T4, L4, and L40S  (chapter-05-inference-accelerators-t4-l4-and-l40s.md)
- Introduction
- 1. The T4 (Turing) — The Legacy Workhorse
- 2. The L4 (Ada Lovelace) — The Universal Edge Card
- 3. The L40S (Ada Lovelace) — The "H100 Alternative"
  - The L40S Use Case
- Architectural Decision Matrix: Inference
- Customer Scenario (Senior Level)
- Interview Preparation

## Chapter 6 — Training Accelerators: The Heavy Iron  (chapter-06-training-accelerators-v100-to-b200.md)
- Introduction
- 1. Ampere: A100 (The Workhorse)
- 2. Hopper: H100 & H200 (The LLM Standard)
  - The H100
  - The H200 Update
- 3. Blackwell: B200 (The Multi-Die Monster)
- Architectural Comparison Matrix
- Customer Scenario (Senior Level)
- Interview Preparation

## Chapter 7 — The Grace CPU and Superchips  (chapter-07-grace-cpu-and-superchips.md)
- Introduction
- 1. The Grace CPU (ARM Architecture)
- 2. The Superchip: NVLink-C2C
  - The Bandwidth Revolution
- 3. Unified Memory: The Death of cudaMemcpy
- Architectural Diagram: x86 vs. Superchip
- Customer Scenario (Senior Level)
- Interview Preparation

## Volume 04 — NVIDIA Hardware Portfolio  (index.md)
- The Portfolio Is a Decision Space
- Planned Chapter Sequence
- Labs
- Production Perspective

## Lab 01 — Build a GPU Selection Scorecard  (labs/lab-01-build-a-gpu-selection-scorecard.md)
- Lab metadata
- Objective
- Background
- Learning outcomes
- Architecture
- Prerequisites
- Environment
- Components
- Step 1 — Define the workload
- Step 2 — Create gate criteria
- Step 3 — Define weighted criteria
- Step 4 — Define the scoring scale
- Step 5 — Record evidence
- Step 6 — Calculate weighted scores
- Step 7 — Build a risk register
- Validation
- Verification
- Observability
- Performance measurements
- Failure injection
  - Failure 1 — Change the workload
  - Failure 2 — Remove trusted evidence
- Troubleshooting
  - Symptom: every candidate scores almost the same
  - Symptom: the preferred product wins regardless of weights
  - Symptom: the cheapest candidate always wins
- Cleanup
- Summary
- Challenge exercises
- Further reading

## Lab 02 — Benchmark an Inference Accelerator Shortlist  (labs/lab-02-benchmark-an-inference-accelerator-shortlist.md)
- Lab Metadata
- 1. Objective
- 2. Background
- 3. Learning Outcomes
- 4. Architecture
- 5. Prerequisites
- 6. Environment
- 7. Components
- 8. Deployment Steps
  - Step 1 — Verify the GPU environment
  - Step 2 — Capture a static baseline
  - Step 3 — Start telemetry
  - Step 4 — Warm the service
  - Step 5 — Run the benchmark matrix
  - Step 6 — Stop telemetry
- 9. Validation
- 10. Verification
- 11. Observability
- 12. Performance Measurements
- 13. Failure Injection
- 14. Troubleshooting
  - Symptom — Candidate B appears slower despite stronger specifications
  - Symptom — Results vary widely between runs
- 15. Cleanup
- 16. Summary
- 17. Challenge Exercises
- 18. Further Reading
