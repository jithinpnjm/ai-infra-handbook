# nvidia-devops-zth-v14


## Chapter 01 — Why NVIDIA AI Enterprise Exists  (chapter-01-why-nvidia-ai-enterprise-exists.md)
- Learning Objectives
- Beginner's Primer: The "Red Hat" of AI
- The Problem Before an Enterprise Stack
- What Enterprise Support Changes
- What It Does Not Replace
- Customer Scenario
- Troubleshooting
- Interview Preparation
- Architecture Summary

## Chapter 02 — Platform Architecture and Support Boundary  (chapter-02-platform-architecture-and-support-boundary.md)
- Beginner's Primer: The AI Layer Cake
- Responsibility Map
- Architecture
- Production Anti-Pattern
- Customer Perspective
- Worked Scenario
- Architecture Summary

## Chapter 03 — NVIDIA NIM Architecture  (chapter-03-nvidia-nim-architecture.md)
- Beginner's Primer: What is a NIM?
- Architecture
- Why It Exists
- Operational Boundary
- Health Model: A Key NIM Design
- Troubleshooting
- Architecture Summary

## Chapter 04 — Deploying and Operating NIM Services  (chapter-04-deploying-and-operating-nim-services.md)
- Beginner's Primer: The Cold Start Problem
- Deployment Checklist
- Scaling
- Troubleshooting
- Architecture Summary

## Chapter 05 — NeMo Framework and Model Customization  (chapter-05-nemo-framework-and-model-customization.md)
- Beginner's Primer: NIM vs. NeMo
- Workflow
- Infrastructure and Cost Reality
- Governance and Lineage
- Troubleshooting Low GPU Utilization
- Architecture Summary

## Chapter 06 — NeMo Guardrails and Enterprise Controls  (chapter-06-nemo-guardrails-and-enterprise-controls.md)
- Beginner's Primer: AI is Unpredictable
- Control Architecture
- Engineering Trade-offs
- Policy Governance
- Security Boundary
- Troubleshooting
- Architecture Summary

## Chapter 07 — NGC Catalog, Containers, and Artifacts  (chapter-07-ngc-catalog-containers-and-artifacts.md)
- Beginner's Primer: The AI Supply Chain
- Artifact Lifecycle
- Production Principles — Why Each One Matters
- Governance Workflow
- Troubleshooting
- Architecture Summary

## Chapter 08 — Licensing and Entitlement Operations  (chapter-08-licensing-and-entitlement-operations.md)
- Beginner's Primer: AI Software isn't Free Anymore
- Entitlement Decision Tree
- Operational Design
- Security Best Practices
- Troubleshooting
- Architecture Summary

## Chapter 09 — Lifecycle, Compatibility, and Upgrades  (chapter-09-lifecycle-compatibility-and-upgrades.md)
- Beginner's Primer: The Dependency Hell of AI Upgrades
- Compatibility Matrix — What to Track
- Upgrade Workflow
- Production Upgrade Procedure
- Troubleshooting
- Architecture Summary

## Chapter 10 — Kubernetes and Virtualization Integration  (chapter-10-kubernetes-and-virtualization-integration.md)
- Beginner's Primer: Bare-Metal vs. Virtualization
- Integration Layers and Support Boundaries
- Architecture Decision Tree
- Production Guidance by Architecture
  - Bare-metal Kubernetes + GPU Operator (RECOMMENDED FOR NEW DEPLOYMENTS)
  - Kubernetes in VM (vSphere with vGPU)
  - Troubleshooting GPU Access Failures
- Network and Storage in Multi-Architecture Setups
- Production Checklist
- Architecture Summary

## Chapter 11 — Customer Architecture and Troubleshooting  (chapter-11-customer-architecture-and-troubleshooting.md)
- Beginner's Primer: The SA Discovery Process
- Discovery Framework
- Discovery Output — A Real Architecture
- Troubleshooting Tree — Ordered by Speed to Isolate Root Cause
- Customer Advice
- Architecture Summary

## Chapter 12 — Volume 14 Summary  (chapter-12-volume-14-summary.md)
- Beginner's Primer: The Value of NVAIE
- The Insight You Must Carry Forward
- Architecture Summary
  - NIM (Chapter 03–04) — Packaging model execution with operational defaults
  - NeMo (Chapter 05–06) — Framework for training, customization, and policy layers
  - NGC Catalog (Chapter 07) — Supply chain and artifact governance
  - Entitlement and Licensing (Chapter 08) — Operational availability dependency
  - Lifecycle and Upgrades (Chapter 09) — One layer at a time
  - Kubernetes and Virtualization (Chapter 10) — Integration layers determine risk
  - Customer Architecture (Chapter 11) — Nine discovery questions
- Quick Troubleshooting Reference
- Production Deployment Checklist
- Interview and Hiring Signal
- Related Volumes
- Summary Statement

## Volume 14 — NVIDIA AI Enterprise  (index.md)
- Big Picture
- Chapters
- Labs

## Lab 01 — Inspect an NGC and NIM Deployment Plan  (labs/lab-01-inspect-an-ngc-and-nim-deployment-plan.md)
- Objective
- Deliverables

## Lab 02 — Deploy and Validate a NIM Service  (labs/lab-02-deploy-and-validate-a-nim-service.md)
- Objective
- Prerequisites
- Step 1: Create Secret and Deploy
- Step 2: Validate Pod Startup and GPU Assignment
- Step 3: Validate Service and Model Readiness
- Step 4: Run Deterministic Inference Test
- Step 5: Measure Performance Metrics
- Step 6: Failure Injection Test
- Step 7: Collect Evidence and Cleanup
- Validation Checklist

## Lab 03 — Build a NeMo Customization Workflow  (labs/lab-03-build-a-nemo-customization-workflow.md)
- Objective
- Step 1: Record Base Model and License
- Step 2: Prepare and Version Dataset
- Step 3: Prepare Training Configuration
- Step 4: Run Training Job in Kubernetes
- Step 5: Save Checkpoint and Record Metadata
- Step 6: Evaluate Against Baseline
- Step 7: Package for Serving
- Step 8: Failure Injection — Checkpoint Recovery
- Final Evidence Collection
- Validation Checklist

## Lab 04 — Troubleshoot Entitlement and Runtime Failures  (labs/lab-04-troubleshoot-entitlement-and-runtime-failures.md)
- Objective
- Scenario: Pod cannot start, stuck in ImagePullBackOff
- Step 1: Extract Exact Image Reference and Digest
- Step 2: Verify Entitlement and Token Scope
- Step 3: Test Network, DNS, and Registry Reachability
- Step 4: Verify Image-Pull Secret or Workload Identity
- Step 5: Inspect Node Runtime and GPU
- Step 6: Check Pod Events and Logs
- Step 7: Compare with Known-Good Deployment
- Failure Injection: Intentionally Broken Credentials
- Resolution Procedure
- Evidence Collection Checklist
