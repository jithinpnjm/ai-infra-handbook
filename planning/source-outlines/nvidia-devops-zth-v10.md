# nvidia-devops-zth-v10


## Chapter 01 — Why Kubernetes Needs a GPU Platform Layer  (chapter-01-why-kubernetes-needs-a-gpu-platform-layer.md)
- Learning Objectives
- Beginner's Primer: CPU vs. GPU in Kubernetes
- Two Paths Must Agree
- Why a Count Is Not a GPU Service
- The Operational Failure of Manual Configuration
- What the GPU Operator Changes—and What It Does Not
- Production Checklist: Before a GPU Node Accepts Work
- Troubleshooting Model
- Customer Architecture Discussion
- Interview Questions
- Architecture Summary
- Key Takeaways
- Cross References

## Chapter 02 — GPU Software Lifecycle in Kubernetes  (chapter-02-gpu-software-lifecycle-in-kubernetes.md)
- Learning Objectives
- Beginner's Primer: Drivers in Containers?
- The Lifecycle Is a Dependency Graph
- Compatibility Is Policy, Not a Spreadsheet Afterthought
- A Production Change Model
- Node Acceptance Gates
- Production Story: Green Nodes, Failed GPUs
- Troubleshooting by Layer
- Customer Architecture Discussion
- Interview Questions
- Architecture Summary
- Key Takeaways
- Cross References

## Chapter 03 — NVIDIA Container Toolkit, RuntimeClass, and CDI  (chapter-03-container-toolkit-runtimeclass-and-cdi.md)
- Learning Objectives
- Beginner's Primer: Docker, containerd, and CDI
- From Allocation to Process
- Three Mechanisms, Three Different Questions
- Design the Runtime Contract
- Production Story: Schedulable but Unusable
- Security and Isolation
- Troubleshooting the Runtime Boundary
- Customer Architecture Discussion
- Interview Questions
- Architecture Summary
- Key Takeaways
- Cross References

## Chapter 04 — Device Plugin and Kubernetes Resource Model  (chapter-04-device-plugin-and-kubernetes-resource-model.md)
- Learning Objectives
- Beginner's Primer: Extended Resources
- The Kubelet Contract
- Read the Resource States Precisely
- The Resource Model’s Productive Limitation
- Production Story: Correct Count, Wrong Outcome
- Operate the Plugin as Infrastructure
- Troubleshooting in Dependency Order
- Customer Architecture Discussion
- Interview Questions
- Architecture Summary
- Key Takeaways
- Cross References

## Chapter 05 — Node and GPU Feature Discovery  (chapter-05-node-and-gpu-feature-discovery.md)
- Learning objectives
- Beginner's Primer: Labels, NFD, and GFD
- The problem: quantity is not a platform contract
- From host evidence to a scheduling decision
- Facts, assertions, and classes
- A practical label contract
- Security and integrity boundary
- Drift is an availability issue
- Scheduling patterns and trade-offs
- Troubleshooting: the selector is correct, yet no Pod schedules
- Production checklist
- Customer architecture discussion
- Interview preparation
- Architecture Summary
- Key takeaways
- Cross references and further reading

## Chapter 06 — GPU Operator Architecture  (chapter-06-gpu-operator-architecture.md)
- Learning objectives
- Beginner's Primer: What is a Kubernetes Operator?
- Architecture: desired state becomes node-local work
- Responsibilities and boundaries
- Reconciliation is not a serial installer
- Deployment models: choose one owner per layer
- A release is a compatibility decision
- Production story: the policy that spread too far
- Security model
- Troubleshooting: find the first broken contract
- NVIDIA Network Operator and RDMA Enablement
- Customer architecture discussion
- Interview preparation
- Architecture Summary
- Key takeaways
- Cross references and further reading

## Chapter 07 — Driver Containers and Node Operands  (chapter-07-driver-containers-and-node-operands.md)
- Learning objectives
- Beginner's Primer: The Driver Container Magic
- One node, several host-facing contracts
- Driver containers are a delivery model, not an abstraction escape hatch
- Readiness has gates, not one boolean
- Privilege and supply-chain controls
- Recovery and maintenance behavior
- Troubleshooting sequence
- Customer architecture discussion
- Interview preparation
- Architecture Summary
- Key takeaways
- Cross references and further reading

## Chapter 08 — GPU Scheduling and Topology  (chapter-08-gpu-scheduling-and-topology.md)
- Learning objectives
- Beginner's Primer: The NUMA / PCIe Locality Problem
- The scheduler sees a staged decision
- Four placement questions
- Core controls and what they do not do
- Topology is a path, not a label
- Coordinated-start workloads
- Fragmentation is the price of specificity
- Production story: a successful placement that missed the objective
- Fairness, preemption, and disruption
- Troubleshooting placement and performance
- Customer architecture discussion
- Interview preparation
- Architecture Summary
- Key takeaways
- Cross references and further reading

## Chapter 09 — GPU Observability with DCGM  (chapter-09-gpu-observability-with-dcgm.md)
- Learning objectives
- Beginner's Primer: From `nvidia-smi` to DCGM
- Start with an operational question
- The evidence path
- Metrics with an owner and a response
- Build a monitoring contract
- Correlation during an incident
- Failure patterns that mislead operators
- Production design review
- Senior-level design questions
- Architecture Summary
- Key takeaways
- Cross references

## Chapter 10 — Production Installation and Configuration  (chapter-10-production-installation-and-configuration.md)
- Learning objectives
- Beginner's Primer: Installing the GPU Operator
- Define the platform boundary first
- Ownership decisions that determine the design
- Treat Helm values as an interface
- Install in an intentionally small blast radius
- Acceptance is an end-to-end proof
- Operational guardrails
- Troubleshooting installation without guesswork
- Senior-level design questions
- Architecture Summary
- Key takeaways
- Cross references

## Chapter 11 — Upgrades and Production Troubleshooting  (chapter-11-upgrades-and-production-troubleshooting.md)
- Learning objectives
- Beginner's Primer: The Dangers of In-Place GPU Upgrades
- Change the compatibility set, not a component in isolation
- Design the canary as a production experiment
- A layered incident method
- Failure patterns and first safe checks
  - A node does not advertise GPUs
  - A GPU Pod remains Pending
  - A Pod fails before its application starts
  - CUDA initialization fails in a Running Pod
  - Metrics disappear or report an implausible fleet state
  - An operator upgrade stalls
- Containment, rollback, and forward recovery
- Evidence package for escalation
- Senior-level design questions
- Architecture Summary
- Key takeaways
- Cross references

## Chapter 12 — Volume 10 Summary  (chapter-12-volume-10-summary.md)
- The platform lifecycle
- What each component is responsible for
- The production operating model
- A reusable diagnosis sequence
- Revision prompts
- Continue the practice
- Next volume

## Volume 10 — Kubernetes GPU Platform  (index.md)
- The Platform Contract
- How to Read This Volume
- Chapter Sequence
- Operating Perspective
- Planned Labs
- Further Reading

## Lab 01 — Inspect a Kubernetes GPU Node  (labs/lab-01-inspect-a-kubernetes-gpu-node.md)
- 1. Objective
- 2. Production Story
- 3. Learning Outcomes
- 4. Architecture
- 5. Prerequisites
- 6. Safety and Change Boundaries
- 7. Environment and Variables
- 8. Components and Data Flow
- 9. Procedure: Inspect Kubernetes State
- 10. Procedure: Inspect the Host (Hardware Only)
- 11. Validation Workload
- 12. Verification and Acceptance Criteria
- 13. Observability and Evidence Collection
- 14. Measurements and Baseline
- 15. Safe Failure Exercise
- 16. Troubleshooting Decision Table
- 17. Cleanup and Operational Handoff
- 18. Summary, Challenges, and Further Reading

## Lab 02 — Install and Validate GPU Operator  (labs/lab-02-install-and-validate-gpu-operator.md)
- 1. Objective
- 2. Production Story
- 3. Learning Outcomes
- 4. Architecture
- 5. Prerequisites
- 6. Safety and Rollback Boundary
- 7. Environment and Variables
- 8. Components and Ownership Decision
- 9. Preflight Evidence
- 10. Procedure: Add and Inspect the Chart
- 11. Procedure: Install the Pinned Release
- 12. Validation: Reconciliation and Operands
- 13. Validation: Resource Advertisement
- 14. Validation: Workload Execution
- 15. Observability and Measurements
- 16. Safe Failure Exercise and Troubleshooting
- 17. Cleanup and Handoff
- 18. Summary, Challenges, and Further Reading

## Lab 03 — Diagnose a Missing Allocatable GPU  (labs/lab-03-diagnose-a-missing-allocatable-gpu.md)
- 1. Objective
- 2. Production Story
- 3. Learning Outcomes
- 4. Architecture
- 5. Prerequisites
- 6. Safety and Incident Boundary
- 7. Environment and Variables
- 8. Components and Evidence Map
- 9. Procedure: Preserve Initial Evidence
- 10. Validate the Symptom and Compare
- 11. Procedure: Hardware and Driver (Hardware Only)
- 12. Procedure: Device Plugin and Discovery
- 13. Procedure: Kubelet and Runtime (Hardware Only)
- 14. Scheduler Policy Check
- 15. Recovery Plan and Acceptance Gates
- 16. Safe Failure Exercise and Troubleshooting Matrix
- 17. Cleanup and Handoff
- 18. Summary, Challenges, and Further Reading

## Lab 04 — Perform a Controlled GPU Platform Upgrade  (labs/lab-04-perform-a-controlled-gpu-platform-upgrade.md)
- 1. Objective
- 2. Production Story
- 3. Learning Outcomes
- 4. Architecture
- 5. Prerequisites
- 6. Safety, Scope, and Stop Conditions
- 7. Environment and Variables
- 8. Compatibility Matrix and Acceptance Gates
- 9. Components and Change Ownership
- 10. Baseline and Rollback Evidence
- 11. Quarantine and Drain the Canary
- 12. Upgrade the Pinned Release
- 13. Platform Validation
- 14. Workload and Observability Validation
- 15. Measurements and Decision Record
- 16. Failure Exercise and Rollback
- 17. Cleanup and Operational Handoff
- 18. Summary, Challenges, and Further Reading
