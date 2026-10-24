# designing-machine-learning-systems


<!-- file: afterword01.xhtml -->

## Epilogue

<!-- file: ch01.xhtml -->

## Chapter 1. Overview of Machine Learning Systems

## The Relationship Between MLOps and ML Systems Design

## When to Use Machine Learning
- Machine Learning Use Cases

## Understanding Machine Learning Systems
- Machine Learning in Research Versus in Production
  - Different stakeholders and requirements
  - Computational priorities

## Terminology Clash
  - Data
  - Fairness
  - Interpretability
  - Discussion
- Machine Learning Systems Versus Traditional Software

## Summary

<!-- file: ch02.xhtml -->

## Chapter 2. Introduction to Machine Learning Systems Design

## Business and ML Objectives

## Requirements for ML Systems
- Reliability
- Scalability
- Maintainability
- Adaptability

## Iterative Process

## Framing ML Problems
- Types of ML Tasks
  - Classification versus regression
  - Binary versus multiclass classification
  - Multiclass versus multilabel classification
  - Multiple ways to frame a problem
- Objective Functions
  - Decoupling objectives

## Mind Versus Data

## Summary

<!-- file: ch03.xhtml -->

## Chapter 3. Data Engineering Fundamentals

## Data Sources

## Data Formats
- JSON
- Row-Major Versus Column-Major Format
- Text Versus Binary Format

## Data Models
- Relational Model
- NoSQL
  - Document model
  - Graph model
- Structured Versus Unstructured Data

## Data Storage Engines and Processing
- Transactional and Analytical Processing
- ETL: Extract, Transform, and Load

## Modes of Dataflow
- Data Passing Through Databases
- Data Passing Through Services
- Data Passing Through Real-Time Transport

## Batch Processing Versus Stream Processing

## Summary

<!-- file: ch04.xhtml -->

## Chapter 4. Training Data

## Sampling
- Nonprobability Sampling
- Simple Random Sampling
- Stratified Sampling
- Weighted Sampling
- Reservoir Sampling
- Importance Sampling

## Labeling
- Hand Labels
  - Label multiplicity
  - Data lineage
- Natural Labels
  - Feedback loop length
- Handling the Lack of Labels
  - Weak supervision
  - Semi-supervision
  - Transfer learning
  - Active learning

## Class Imbalance
- Challenges of Class Imbalance
- Handling Class Imbalance
  - Using the right evaluation metrics
  - Data-level methods: Resampling
  - Algorithm-level methods
    - Cost-sensitive learning
    - Class-balanced loss
    - Focal loss

## Data Augmentation
- Simple Label-Preserving Transformations
- Perturbation
- Data Synthesis

## Summary

<!-- file: ch05.xhtml -->

## Chapter 5. Feature Engineering

## Learned Features Versus Engineered Features

## Common Feature Engineering Operations
- Handling Missing Values
  - Deletion
  - Imputation
- Scaling
- Discretization
- Encoding Categorical Features
- Feature Crossing
- Discrete and Continuous Positional Embeddings

## Data Leakage
- Common Causes for Data Leakage
  - Splitting time-correlated data randomly instead of by time
  - Scaling before splitting
  - Filling in missing data with statistics from the test split
  - Poor handling of data duplication before splitting
  - Group leakage
  - Leakage from data generation process
- Detecting Data Leakage

## Engineering Good Features
- Feature Importance
- Feature Generalization

## Summary

<!-- file: ch06.xhtml -->

## Chapter 6. Model Development and Offline Evaluation

## Model Development and Training
- Evaluating ML Models
  - Six tips for model selection
    - Avoid the state-of-the-art trap
    - Start with the simplest models
    - Avoid human biases in selecting models
    - Evaluate good performance now versus good performance later
    - Evaluate trade-offs
    - Understand your model’s assumptions
- Ensembles
  - Bagging
  - Boosting
  - Stacking
- Experiment Tracking and Versioning
  - Experiment tracking
  - Versioning
- Distributed Training
  - Data parallelism
  - Model parallelism
- AutoML
  - Soft AutoML: Hyperparameter tuning
  - Hard AutoML: Architecture search and learned optimizer

## Model Offline Evaluation
- Baselines
- Evaluation Methods
  - Perturbation tests
  - Invariance tests
  - Directional expectation tests
  - Model calibration
  - Confidence measurement
  - Slice-based evaluation

## Summary

<!-- file: ch07.xhtml -->

## Chapter 7. Model Deployment and Prediction Service

## Machine Learning Deployment Myths
- Myth 1: You Only Deploy One or Two ML Models at a Time
- Myth 2: If We Don’t Do Anything, Model Performance Remains the Same
- Myth 3: You Won’t Need to Update Your Models as Much
- Myth 4: Most ML Engineers Don’t Need to Worry About Scale

## Batch Prediction Versus Online Prediction

## Terminology Confusion

## Streaming Features Versus Online Features
- From Batch Prediction to Online Prediction
- Unifying Batch Pipeline and Streaming Pipeline

## Model Compression
- Low-Rank Factorization
- Knowledge Distillation
- Pruning
- Quantization

## ML on the Cloud and on the Edge
- Compiling and Optimizing Models for Edge Devices
  - Model optimization
  - Using ML to optimize ML models
- ML in Browsers

## Summary

<!-- file: ch08.xhtml -->

## Chapter 8. Data Distribution Shifts and Monitoring

## Causes of ML System Failures
- Software System Failures
- ML-Specific Failures
  - Production data differing from training data
  - Edge cases
  - Degenerate feedback loops
    - Detecting degenerate feedback loops
    - Correcting degenerate feedback loops

## Data Distribution Shifts
- Types of Data Distribution Shifts
  - Covariate shift
  - Label shift
  - Concept drift
- General Data Distribution Shifts
- Detecting Data Distribution Shifts
  - Statistical methods
  - Time scale windows for detecting shifts
- Addressing Data Distribution Shifts

## Monitoring and Observability
- ML-Specific Metrics
  - Monitoring accuracy-related metrics
  - Monitoring predictions
  - Monitoring features
  - Monitoring raw inputs
- Monitoring Toolbox
  - Logs
  - Dashboards
  - Alerts
- Observability

## Summary

<!-- file: ch09.xhtml -->

## Chapter 9. Continual Learning and Test in Production

## Continual Learning
- Stateless Retraining Versus Stateful Training
- Why Continual Learning?
- Continual Learning Challenges
  - Fresh data access challenge
  - Evaluation challenge
  - Algorithm challenge
- Four Stages of Continual Learning
  - Stage 1: Manual, stateless retraining
  - Stage 2: Automated retraining
    - Requirements

## Feature Reuse (Log and Wait)
  - Stage 3: Automated, stateful training
    - Requirements
  - Stage 4: Continual learning
    - Requirements
- How Often to Update Your Models
  - Value of data freshness
  - Model iteration versus data iteration

## Test in Production
- Shadow Deployment
- A/B Testing
- Canary Release
- Interleaving Experiments
- Bandits
  - Contextual bandits as an exploration strategy

## Summary

<!-- file: ch10.xhtml -->

## Chapter 10. Infrastructure and Tooling for MLOps

## Storage and Compute
- Public Cloud Versus Private Data Centers

## Development Environment
- Dev Environment Setup
  - IDE
- Standardizing Dev Environments
- From Dev to Prod: Containers

## Resource Management
- Cron, Schedulers, and Orchestrators
- Data Science Workflow Management

## ML Platform
- Model Deployment
- Model Store
- Feature Store

## Build Versus Buy

## Summary

<!-- file: ch11.xhtml -->

## Chapter 11. The Human Side of Machine Learning

## User Experience
- Ensuring User Experience Consistency
- Combatting “Mostly Correct” Predictions
- Smooth Failing

## Team Structure
- Cross-functional Teams Collaboration
- End-to-End Data Scientists
  - Approach 1: Have a separate team to manage production
  - Approach 2: Data scientists own the entire process

## Responsible AI
- Irresponsible AI: Case Studies
  - Case study I: Automated grader’s biases
    - Failure 1: Setting the wrong objective
    - Failure 2: Insufficient fine-grained model evaluation to discover biases
    - Failure 3: Lack of transparency
  - Case study II: The danger of “anonymized” data
- A Framework for Responsible AI
  - Discover sources for model biases
  - Understand the limitations of the data-driven approach
  - Understand the trade-offs between different desiderata
  - Act early
  - Create model cards
  - Establish processes for mitigating biases
  - Stay up-to-date on responsible AI

## Summary

<!-- file: colophon01.xhtml -->

## About the Author

<!-- file: colophon02.xhtml -->

## Colophon

<!-- file: copyright-page01.xhtml -->

## Designing Machine Learning Systems

## Revision History for the First Edition

<!-- file: dedication01.xhtml -->

## Praise for Designing Machine Learning Systems

<!-- file: ix01.xhtml -->

## Index
  - Symbols
  - A
  - B
  - C
  - D
  - E
  - F
  - G
  - H
  - I
  - J
  - K
  - L
  - M
  - N
  - O
  - P
  - Q
  - R
  - S
  - T
  - U
  - V
  - W
  - X
  - Z

<!-- file: preface01.xhtml -->

## Preface

## Who This Book Is For

## What This Book Is Not

## Navigating This Book

## GitHub Repository and Community

## Conventions Used in This Book

## Using Code Examples

## O’Reilly Online Learning

## How to Contact Us

## Acknowledgments

<!-- file: titlepage01.xhtml -->

## Designing Machine Learning Systems
