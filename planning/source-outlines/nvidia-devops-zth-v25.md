# nvidia-devops-zth-v25


## Chapter 01 — Why MLOps: The Cost of Ungoverned ML  (chapter-01-why-mlops-the-cost-of-ungoverned-ml.md)
- Learning Outcome
- Beginner's Primer: The MLOps Reality Check
- WHY
- WHAT
- HOW
- WHEN
- TRADEOFFS
- PRODUCTION
- TROUBLESHOOTING
  - Scenario 1: "We got a great result, why can't we ship it?"
  - Scenario 2: "The model's features changed between two runs and nobody knows why"
- Interview Preparation
- Architecture Summary
- Related Chapters

## Chapter 02 — GPU Cloud Provisioning for Training Workloads  (chapter-02-gpu-cloud-provisioning-for-training-workloads.md)
- WHY
- Beginner's Primer: The Bare Metal Foundation
- WHAT
- HOW
  - Step 1 — Verify the driver and GPU are visible at all
  - Step 2 — Verify Docker can hand GPU access to a container
  - Step 3 — Provision persistent storage
  - Step 4 — Firewall: verify you don't lock yourself out
- WHEN
- TRADEOFFS
- PRODUCTION
- TROUBLESHOOTING
  - Scenario 1: `nvidia-container-toolkit` is installed but the GPU test container fails
  - Scenario 2: Enabling the firewall drops your session or blocks future access
- Interview Preparation
- Architecture Summary
- Related Chapters

## Chapter 03 — Data Versioning with DVC  (chapter-03-data-versioning-with-dvc.md)
- WHY
- Beginner's Primer: Git for Big Files
- WHAT
- HOW
  - Step 1 — Initialize DVC in the project
  - Step 2 — Point DVC at a remote
  - Step 3 — Track a real file and push it
- WHEN
- TRADEOFFS
- PRODUCTION
- TROUBLESHOOTING
  - Scenario 1: `.dvc` pointer files are invisible to Git
  - Scenario 2: A stale `.dvc` pointer file left after replacing a dataset version
- Interview Preparation
- Architecture Summary
- Related Chapters

## Chapter 04 — Experiment Tracking with MLflow  (chapter-04-experiment-tracking-with-mlflow.md)
- WHY
- Beginner's Primer: The Death of the Spreadsheet
- WHAT
- HOW
  - Step 1 — The Docker Compose stack
  - Step 2 — A real dependency bug, found on first boot
  - Step 3 — Prove persistence, don't just trust it
  - Step 4 — Nested runs for cross-validation
- WHEN
- TRADEOFFS
- PRODUCTION
- TROUBLESHOOTING
  - Scenario 1: MLflow server fails to start with a database driver error
  - Scenario 2: A run reachable from `mlflow ui` locally can't be found from a different machine
- Interview Preparation
- Architecture Summary
- Related Chapters

## Chapter 05 — Data Ingestion and Cleaning Pipeline Design  (chapter-05-data-ingestion-and-cleaning-pipeline-design.md)
- WHY
- Beginner's Primer: The Broken Vacuum Cleaner
- WHAT
- HOW
  - Step 1 — Gap detection as the single source of truth for "what to fetch"
  - Step 2 — Save after every chunk, not after the whole run
  - Step 3 — Distinguish "failed, retry it" from "confirmed empty, stop asking"
  - Step 4 — Rate-limit backoff, tuned to the API's actual signal
- WHEN
- TRADEOFFS
- PRODUCTION
- TROUBLESHOOTING
  - Scenario 1: A rerun keeps re-fetching the same "empty" days forever
  - Scenario 2: A day shows up as "complete" but the data looks wrong
- Interview Preparation
- Architecture Summary
- Related Chapters

## Chapter 06 — Building Leakage-Safe Training Datasets for Time-Series ML  (chapter-06-building-leakage-safe-training-datasets-for-time-series-ml.md)
- WHY
- Beginner's Primer: Time Traveling Models
- WHAT
- HOW
  - Part 1 — Leakage-safe label computation
  - Part 2 — Chronological, expanding-window walk-forward splits
  - Part 3 — A real bug: the holdout silently dropping the newest data
- WHEN
- TRADEOFFS
- PRODUCTION
- TROUBLESHOOTING
  - Scenario 1: Offline metrics look great, live performance doesn't match
  - Scenario 2: A pipeline's row counts silently change between two runs of "the same" split logic
- Interview Preparation
- Architecture Summary
- Related Chapters

## Chapter 07 — Model Architecture and Training Pipeline Design  (chapter-07-model-architecture-and-training-pipeline-design.md)
- WHY
- Beginner's Primer: Modular Neural Networks
- WHAT
- HOW
  - Step 1 — Three candidate single-timeframe architectures, one shared interface
  - Step 2 — Fusing multiple timeframes as encoder composition
  - Step 3 — A training function generic over "one timeframe" or "many"
  - Step 4 — Wiring the loop to MLflow (ties back to Chapter 4)
- WHEN
- TRADEOFFS
- PRODUCTION
- TROUBLESHOOTING
  - Scenario 1: A multi-timeframe model trains but produces suspiciously perfect metrics
  - Scenario 2: Shape mismatch error when adding a new architecture
- Interview Preparation
- Architecture Summary
- Related Chapters

## Chapter 08 — Scaling to Multi-Node Distributed Training  (chapter-08-scaling-to-multi-node-distributed-training.md)
- WHY
- Beginner's Primer: Do you actually need DDP?
- WHAT
- HOW
  - What actually would have to change for kind #1 (splitting one run across GPUs)
  - What actually would help kind #2 (this project's real situation)
- WHEN
- TRADEOFFS
- PRODUCTION
- TROUBLESHOOTING
  - Scenario 1: "We should add DDP to speed up training" for a model that already trains in under 2 minutes per fold
  - Scenario 2: Multi-GPU parallel independent runs (kind #2) silently contend for the same GPU
- Interview Preparation
- Architecture Summary
- Related Chapters

## Chapter 09 — The Model Promotion Gate: Governance Before the Registry  (chapter-09-the-model-promotion-gate-governance-before-the-registry.md)
- WHY
- Beginner's Primer: The Promotion Gate
- WHAT
- HOW
  - Check 1 — All folds evaluated
  - Check 2 — Cross-fold variance
  - Check 3 — Beats a logged baseline, fold-by-fold
  - Check 4 — Seed consistency: the direct fix for the original failure
  - Real output — the gate correctly blocking a real, good-looking run
- WHEN
- TRADEOFFS
- PRODUCTION
- TROUBLESHOOTING
  - Scenario 1: A genuinely good model fails the gate on cross-fold std
  - Scenario 2: Seed-consistency check fails even though each individual seed's aggregate looks reasonable
- Interview Preparation
- Architecture Summary
- Related Chapters

## Chapter 10 — End-to-End Case Study: BankNifty Big-Move Prediction Pipeline  (chapter-10-end-to-end-case-study-banknifty-big-move-prediction-pipeline.md)
- WHY
- Beginner's Primer: Tying It All Together
- The Problem
- Step 1 — Infrastructure (Chapter 2)
- Step 2 — The Two Tracking Systems (Chapters 3 & 4)
- Step 3 — Data Ingestion (Chapter 5) → Labeling & Splits (Chapter 6)
- Step 4 — Model Architecture (Chapter 7)
- Step 5 — The Promotion Gate (Chapter 9)
- Step 6 — The Real Sweep
- What This Case Study Actually Demonstrates
- Interview Preparation
- Architecture Summary
- Related Chapters

## Volume 25 — MLOps Engineering: Experiment Tracking, Data Versioning, and Training Pipelines  (index.md)
- Overview
- Why This Volume Exists
- What You'll Learn
- Key Concepts at a Glance
- Production Deployment Model
- How to Use This Volume
- Labs
- Related Volumes

## Lab 01 — Provision a GPU Node and Verify the Stack  (labs/lab-01-provision-a-gpu-node-and-verify-the-stack.md)
- 1. Objective
- 2. Target Audience
- 3. Prerequisites
- 4. Architecture Diagram
- 5. Environment Setup
- 6. Execution Specifications
- 7. Expected Evidence
- 8. Explanation of Behavior
- 9. Performance Benchmarking
- 10. Common Failures
- 11. Safe Failure Injection
- 12. Recovery Steps
- 13. Troubleshooting Guide
- 14. Validation
- 15. Real-World Pitfalls
- 16. Cleanup Procedures
- 17. Knowledge Check
- 18. Additional References

## Lab 02 — Stand Up a Self-Hosted MLflow + Postgres Tracking Server  (labs/lab-02-stand-up-a-self-hosted-mlflow-postgres-tracking-server.md)
- 1. Objective
- 2. Target Audience
- 3. Prerequisites
- 4. Architecture Diagram
- 5. Environment Setup
- 6. Execution Specifications
- 7. Expected Evidence
- 8. Explanation of Behavior
- 9. Performance Benchmarking
- 10. Common Failures
- 11. Safe Failure Injection
- 12. Recovery Steps
- 13. Troubleshooting Guide
- 14. Validation
- 15. Real-World Pitfalls
- 16. Cleanup Procedures
- 17. Knowledge Check
- 18. Additional References

## Lab 03 — Wire a DVC Remote Over SSH and Version a Dataset  (labs/lab-03-wire-a-dvc-remote-over-ssh-and-version-a-dataset.md)
- 1. Objective
- 2. Target Audience
- 3. Prerequisites
- 4. Architecture Diagram
- 5. Environment Setup
- 6. Execution Specifications
- 7. Expected Evidence
- 8. Explanation of Behavior
- 9. Performance Benchmarking
- 10. Common Failures
- 11. Safe Failure Injection
- 12. Recovery Steps
- 13. Troubleshooting Guide
- 14. Validation
- 15. Real-World Pitfalls
- 16. Cleanup Procedures
- 17. Knowledge Check
- 18. Additional References

## Lab 04 — Build a Leakage-Safe Label and Walk-Forward Split Pipeline  (labs/lab-04-build-a-leakage-safe-label-and-walk-forward-split-pipeline.md)
- 1. Objective
- 2. Target Audience
- 3. Prerequisites
- 4. Architecture Diagram
- 5. Environment Setup
- 6. Execution Specifications
- 7. Expected Evidence
- 8. Explanation of Behavior
- 9. Performance Benchmarking
- 10. Common Failures
- 11. Safe Failure Injection
- 12. Recovery Steps
- 13. Troubleshooting Guide
- 14. Validation
- 15. Real-World Pitfalls
- 16. Cleanup Procedures
- 17. Knowledge Check
- 18. Additional References

## Lab 05 — Implement a Promotion Gate and Watch It Correctly Block a Model  (labs/lab-05-implement-a-promotion-gate-and-watch-it-correctly-block-a-model.md)
- 1. Objective
- 2. Target Audience
- 3. Prerequisites
- 4. Architecture Diagram
- 5. Environment Setup
- 6. Execution Specifications
- 7. Expected Evidence
- 8. Explanation of Behavior
- 9. Performance Benchmarking
- 10. Common Failures
- 11. Safe Failure Injection
- 12. Recovery Steps
- 13. Troubleshooting Guide
- 14. Validation
- 15. Real-World Pitfalls
- 16. Cleanup Procedures
- 17. Knowledge Check
- 18. Additional References

## Lab 06 — Run a Multi-Configuration Sweep in Parallel Across GPUs  (labs/lab-06-run-a-multi-configuration-sweep-in-parallel-across-gpus.md)
- 1. Objective
- 2. Target Audience
- 3. Prerequisites
- 4. Architecture Diagram
- 5. Environment Setup
- 6. Execution Specifications
- 7. Expected Evidence
- 8. Explanation of Behavior
- 9. Performance Benchmarking
- 10. Common Failures
- 11. Safe Failure Injection
- 12. Recovery Steps
- 13. Troubleshooting Guide
- 14. Validation
- 15. Real-World Pitfalls
- 16. Cleanup Procedures
- 17. Knowledge Check
- 18. Additional References
