# ai-engineering


<!-- file: afterword01.xhtml -->

## Epilogue

<!-- file: ch01.xhtml -->

## Chapter 1. Introduction to Building AI Applications with Foundation Models

## The Rise of AI Engineering
- From Language Models to Large Language Models
  - Language models
  - Self-supervision
- From Large Language Models to Foundation Models
- From Foundation Models to AI Engineering

## Why the Term “AI Engineering?”

## Foundation Model Use Cases
- Coding
- Image and Video Production
- Writing
- Education
- Conversational Bots
- Information Aggregation
- Data Organization
- Workflow Automation

## Planning AI Applications
- Use Case Evaluation
  - The role of AI and humans in the application
  - AI product defensibility
- Setting Expectations
- Milestone Planning
- Maintenance

## The AI Engineering Stack
- Three Layers of the AI Stack
- AI Engineering Versus ML Engineering
  - Model development
    - Modeling and training

## On the Differences Among Training, Pre-Training, Finetuning, and Post-Training
    - Dataset engineering
    - Inference optimization
  - Application development
    - Evaluation
    - Prompt engineering and context construction
    - AI interface
- AI Engineering Versus Full-Stack Engineering

## Summary

<!-- file: ch02.xhtml -->

## Chapter 2. Understanding Foundation Models

## Training Data
- Multilingual Models
- Domain-Specific Models

## Modeling
- Model Architecture
  - Transformer architecture
    - Attention mechanism
    - Transformer block
  - Other model architectures
- Model Size

## Inverse Scaling
  - Scaling law: Building compute-optimal models
  - Scaling extrapolation

## Parameter Versus Hyperparameter
  - Scaling bottlenecks

## Post-Training
- Supervised Finetuning
- Preference Finetuning
  - Reward model
  - Finetuning using the reward model

## Sampling
- Sampling Fundamentals
- Sampling Strategies
  - Temperature
  - Top-k
  - Top-p
  - Stopping condition
- Test Time Compute
- Structured Outputs
  - Prompting
  - Post-processing
  - Constrained sampling
  - Finetuning
- The Probabilistic Nature of AI
  - Inconsistency
  - Hallucination

## Summary

<!-- file: ch03.xhtml -->

## Chapter 3. Evaluation Methodology

## Challenges of Evaluating Foundation Models

## Understanding Language Modeling Metrics
- Entropy
- Cross Entropy
- Bits-per-Character and Bits-per-Byte
- Perplexity
- Perplexity Interpretation and Use Cases

## How to Use a Language Model to Compute a Text’s Perplexity

## Exact Evaluation
- Functional Correctness
- Similarity Measurements Against Reference Data
  - Exact match
  - Lexical similarity
  - Semantic similarity
- Introduction to Embedding

## AI as a Judge
- Why AI as a Judge?
- How to Use AI as a Judge
- Limitations of AI as a Judge
  - Inconsistency
  - Criteria ambiguity
  - Increased costs and latency
  - Biases of AI as a judge
- What Models Can Act as Judges?

## Ranking Models with Comparative Evaluation
- Challenges of Comparative Evaluation
  - Scalability bottlenecks
  - Lack of standardization and quality control
  - From comparative performance to absolute performance
- The Future of Comparative Evaluation

## Summary

<!-- file: ch04.xhtml -->

## Chapter 4. Evaluate AI Systems

## Evaluation Criteria

## Evaluation-Driven Development
- Domain-Specific Capability
- Generation Capability
  - Factual consistency
  - Safety
- Instruction-Following Capability
  - Instruction-following criteria
  - Roleplaying
- Cost and Latency

## Model Selection
- Model Selection Workflow
- Model Build Versus Buy
  - Open source, open weight, and model licenses
  - Open source models versus model APIs
    - Data privacy
    - Data lineage and copyright
    - Performance
    - Functionality
    - API cost versus engineering cost
    - Control, access, and transparency
    - On-device deployment
- Navigate Public Benchmarks
  - Benchmark selection and aggregation
    - Public leaderboards
    - Custom leaderboards with public benchmarks

## Are OpenAI’s Models Getting Worse?
  - Data contamination with public benchmarks
    - How data contamination happens
    - Handling data contamination

## Design Your Evaluation Pipeline
- Step 1. Evaluate All Components in a System
- Step 2. Create an Evaluation Guideline
  - Define evaluation criteria
  - Create scoring rubrics with examples
  - Tie evaluation metrics to business metrics
- Step 3. Define Evaluation Methods and Data
  - Select evaluation methods
  - Annotate evaluation data
  - Evaluate your evaluation pipeline
  - Iterate

## Summary

<!-- file: ch05.xhtml -->

## Chapter 5. Prompt Engineering

## Introduction to Prompting
- In-Context Learning: Zero-Shot and Few-Shot

## Terminology Ambiguity: Prompt Versus Context
- System Prompt and User Prompt
- Context Length and Context Efficiency

## Prompt Engineering Best Practices
- Write Clear and Explicit Instructions
  - Explain, without ambiguity, what you want the model to do
  - Ask the model to adopt a persona
  - Provide examples
  - Specify the output format
- Provide Sufficient Context

## How to Restrict a Model’s Knowledge to Only Its Context
- Break Complex Tasks into Simpler Subtasks
- Give the Model Time to Think
- Iterate on Your Prompts
- Evaluate Prompt Engineering Tools
- Organize and Version Prompts

## Defensive Prompt Engineering
- Proprietary Prompts and Reverse Prompt Engineering
- Jailbreaking and Prompt Injection
  - Direct manual prompt hacking
  - Automated attacks
  - Indirect prompt injection
- Information Extraction
- Defenses Against Prompt Attacks
  - Model-level defense
  - Prompt-level defense
  - System-level defense

## Summary

<!-- file: ch06.xhtml -->

## Chapter 6. RAG and Agents

## RAG
- RAG Architecture
- Retrieval Algorithms

## Sparse Versus Dense Retrieval
  - Term-based retrieval
  - Embedding-based retrieval
  - Comparing retrieval algorithms
  - Combining retrieval algorithms
- Retrieval Optimization
  - Chunking strategy
  - Reranking
  - Query rewriting
  - Contextual retrieval

## Evaluating Retrieval Solutions
- RAG Beyond Texts
  - Multimodal RAG
  - RAG with tabular data

## Agents
- Agent Overview
- Tools
  - Knowledge augmentation
  - Capability extension
  - Write actions
- Planning
  - Planning overview
  - Foundation models as planners

## Foundation Model (FM) Versus Reinforcement Learning (RL) Planners
  - Plan generation
    - Function calling
    - Planning granularity
    - Complex plans
  - Reflection and error correction
  - Tool selection
- Agent Failure Modes and Evaluation
  - Planning failures
  - Tool failures
  - Efficiency

## Memory

## Summary

<!-- file: ch07.xhtml -->

## Chapter 7. Finetuning

## Finetuning Overview

## When to Finetune
- Reasons to Finetune
- Reasons Not to Finetune

## Finetuning Domain-Specific Tasks
- Finetuning and RAG

## Memory Bottlenecks

## Key Takeaways for Understanding Memory Bottlenecks
- Backpropagation and Trainable Parameters
- Memory Math
  - Memory needed for inference
  - Memory needed for training
- Numerical Representations
- Quantization

## Quantization Versus Reduced Precision
  - Inference quantization
  - Training quantization

## Finetuning Techniques
- Parameter-Efficient Finetuning
  - PEFT techniques
  - LoRA
    - Why does LoRA work?
    - LoRA configurations
    - Serving LoRA adapters
    - Quantized LoRA
- Model Merging and Multi-Task Finetuning
  - Summing
    - Linear combination
    - Spherical linear interpolation (SLERP)
    - Pruning redundant task-specific parameters
  - Layer stacking
  - Concatenation
- Finetuning Tactics
  - Finetuning frameworks and base models
    - Base models
    - Finetuning methods
    - Finetuning frameworks
  - Finetuning hyperparameters
    - Learning rate
    - Batch size
    - Number of epochs
    - Prompt loss weight

## Summary

<!-- file: ch08.xhtml -->

## Chapter 8. Dataset Engineering

## A Data-Centric View of AI

## Data Curation
- Data Quality
- Data Coverage
- Data Quantity
- Data Acquisition and Annotation

## Resources for Publicly Available Datasets

## Data Augmentation and Synthesis
- Why Data Synthesis
- Traditional Data Synthesis Techniques
  - Rule-based data synthesis
  - Simulation
- AI-Powered Data Synthesis
  - Instruction data synthesis
  - Data verification
  - Limitations to AI-generated data
    - Quality control
    - Superficial imitation
    - Potential model collapse
    - Obscure data lineage
- Model Distillation

## Data Processing
- Inspect Data
- Deduplicate Data
- Clean and Filter Data
- Format Data

## Summary

<!-- file: ch09.xhtml -->

## Chapter 9. Inference Optimization

## Understanding Inference Optimization
- Inference Overview
  - Computational bottlenecks

## Terminology Ambiguity: Memory-Bound Versus Bandwidth-Bound
  - Online and batch inference APIs
- Inference Performance Metrics
  - Latency, TTFT, and TPOT
  - Throughput and goodput
  - Utilization, MFU, and MBU
- AI Accelerators
  - What’s an accelerator?
  - Computational capabilities
  - Memory size and bandwidth
  - Power consumption

## Selecting Accelerators

## Inference Optimization
- Model Optimization
  - Model compression
  - Overcoming the autoregressive decoding bottleneck
    - Speculative decoding
    - Inference with reference
    - Parallel decoding
  - Attention mechanism optimization

## Calculating the KV Cache Size
    - Redesigning the attention mechanism
    - Optimizing the KV cache size
    - Writing kernels for attention computation
  - Kernels and compilers

## Inference Optimization Case Study from PyTorch
- Inference Service Optimization
  - Batching
  - Decoupling prefill and decode
  - Prompt caching
  - Parallelism

## Summary

<!-- file: ch10.xhtml -->

## Chapter 10. AI Engineering Architecture and User Feedback

## AI Engineering Architecture
- Step 1. Enhance Context
- Step 2. Put in Guardrails
  - Input guardrails
  - Output guardrails
  - Guardrail implementation
- Step 3. Add Model Router and Gateway
  - Router
  - Gateway
- Step 4. Reduce Latency with Caches
  - Exact caching
  - Semantic caching
- Step 5. Add Agent Patterns
- Monitoring and Observability

## Monitoring Versus Observability
  - Metrics
  - Logs and traces
  - Drift detection
- AI Pipeline Orchestration

## User Feedback
- Extracting Conversational Feedback
  - Natural language feedback
    - Early termination
    - Error correction
    - Complaints
    - Sentiment
  - Other conversational feedback
    - Regeneration
    - Conversation organization
    - Conversation length
    - Dialogue diversity
- Feedback Design
  - When to collect feedback
    - In the beginning
    - When something bad happens
    - When the model has low confidence
  - How to collect feedback
- Feedback Limitations
  - Biases
  - Degenerate feedback loop

## Summary

<!-- file: colophon01.xhtml -->

## About the Author

<!-- file: colophon02.xhtml -->

## Colophon

<!-- file: copyright-page01.xhtml -->

## AI Engineering

## Revision History for the First Edition

<!-- file: dedication01.xhtml -->

## Praise for AI Engineering

<!-- file: ix01.xhtml -->

## Index
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
  - Z

<!-- file: preface01.xhtml -->

## Preface

## What This Book Is About

## Reading AI Engineering (AIE) with Designing Machine Learning Systems (DMLS)

## What This Book Is Not

## Who This Book Is For

## Navigating This Book

## Conventions Used in This Book

## Using Code Examples

## O’Reilly Online Learning

## How to Contact Us

## Acknowledgments

<!-- file: titlepage01.xhtml -->

## AI Engineering
