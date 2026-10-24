# hands-on-llm-serving-and-optimization


<!-- file: ch01.xhtml -->

## Chapter 1. Introduction to Model Serving and Optimization

## Anatomy of a Model

## Models as Executable Programs, Not Static Data
- Model Architecture
- Model Data
- Model Execution Code

## We Recommend Storing Your Model’s Architecture and Data in Separate Files

## Model Lifecycle: From Training to Serving

## What Is Model Serving?

## LLM Knowledge Is Critical to LLM Serving

## Why Study Model Serving?

## There Is No One-Size-Fits-All Solution for Model Serving

## Why Optimize Model Serving (Especially for LLMs)?

## Optimization Is Critical for LLMs
- Example: Using a Model Serving Framework (vLLM) to Improve LLM Throughput

## Your Serving Framework’s Configuration Impacts Performance Significantly

## Model Serving Paradigms
- On-Device (Edge) Serving
  - On-device serving design
  - Preparing a model for on-device serving
  - When on-device serving is the right choice
- Single-Model Service

## Containerization Is the Foundation of Modern Model Serving
  - Routing choices in single-model serving
  - Horizontal and vertical scaling

## Prioritizing Intra-Node Serving (Multiple GPUs on One Machine) over Inter-Node Serving (Multiple Machines)
  - Why single-model service is the default starting point
- Multi-Model Service

## Triton Inference Server: A Unified, Multi-Model Serving Platform
  - Routing and autoscaling in multi-model service
  - When multi-model service becomes necessary
- Model Serving Platforms

## Summary

<!-- file: ch02.xhtml -->

## Chapter 2. Large Language Model Serving

## Inside the Mind of a Transformer
- LLM Evolution

## The Definition of LLMs Will Keep Evolving
- The Autoregressive Nature of Transformers
- Decoder-Only Transformer Architecture

## Why Demonstrate Decoder-Only Transformer Architecture?
  - Model architecture
  - Transformer (decoder) block
- Capture Token Context by Calculating Attention
  - Attention calculation
  - Multi-head attention

## You Just Need to Grasp the Transformer Concept—Not the Math

## Executing LLM Generation: A Step-by-Step Walkthrough
- Run the Qwen Model
- Model Prediction, Line by Line
- Enable the KV Cache to Boost Performance
- The Prefill and Decode Phases

## Why Does Learning About the Prefill and Decoding Phases Matter?
- Run the LLM with a Serving Framework
- Serve the LLM (Qwen) with vLLM
- Performance Comparison: vLLM Versus Hugging Face Transformers

## Best Practice: Start Simple, Then Optimize

## LLM Streaming Serving Basics

## LLM Batch Serving Basics

## Summary

<!-- file: ch03.xhtml -->

## Chapter 3. Model Serving System Design: A Deep Dive

## Code in the Chapter

## Build an Online LLM Serving Service from Scratch
- Design Goals
- Service Architecture
- Implement Single Generation Request Handling
- Batching

## Throughput Optimization in Batching

## Tracking Every Prompt’s Execution
- Streaming with Batching
- Batch Serving with vLLM

## A Serving Framework Can Run as a Standalone Web Server

## A General Design for Single-Model LLM Serving
- Requirements for Single-Model Serving

## LLM Serving Requirements Are Continuously Evolving
- General Design

## Build a Multi-Model Serving Service from Scratch
- Design Goals
- Service Architecture
- Core Implementation
- Using NVIDIA Triton as a Model Server

## Trade-offs in Multi-Model Serving Designs
- Challenges
- A Cost-Optimized Multi-Model Design
- A Latency-Optimized Multi-Model Design

## Multi-Model Serving Applies to LLMs, Too

## Summary

<!-- file: ch04.xhtml -->

## Chapter 4. Model Serving Best Practices

## Model Serving in an Agentic World
- Defining Agents
- A Sample Knowledge Agent
- The Agent’s Design
- The Agent’s Internal Workflow
- Agent Autonomy
  - Defining actions

## Model Context Protocol (MCP)
  - Planning with LLMs
- Retrieval-Augmented Generation (RAG)
  - Why RAG?
  - Index-building workflow (offline process)

## Fine (Small) Versus Coarse (Large) Chunking
  - The query/retrieval workflow (online process)

## Why Split Text into Small Chunks?
- Cache-Augmented Generation (CAG)

## RAG Versus CAG
- How Agents Use Model Serving

## LLM Serving in Enterprise Systems: An Overview
- Public API Layer
- Resource Management Layer
- Model Selection and Orchestration Layer

## Speculative Decoding
- Distributed Serving Layer
- Core Inference Layer
- Model Optimization Layer
- Model Layer

## Building with an Open Source Stack
- Implementing Public API
- Implementing Model Selection

## Speculative Decoding Has Many Forms of Implementation
- Implementing a Model Serving Endpoint
  - Single-model hosting on Ray
  - Multi-model hosting on Ray

## Building Your Own Serving Stack Is Not Difficult

## Building with a Cloud Vendor
- Option 1: Fully Managed Foundation-Model Serving
  - Limitations
  - When to use
- Option 2: One-Click Foundation-Model Deployment
  - Limitations
  - When to use
- Option 3: Bring Your Own Model
  - Limitations
  - When to use
- Option 4: Bring Your Own Code
  - Limitations
  - When to use
- Option 5: Bring Your Own Serving Image
  - Limitations
  - When to use
- Option 6: Build Your Own Serving Infrastructure
- Comparing the Options

## Build or Buy? Understanding Strategies
- Why Knowing How to Build Helps—Even If You Won’t Build
- Our Selection Strategy

## Measuring Performance in LLM Serving
- Latency Metrics
- Throughput Metrics
- Best Practices for Performance Measurement
  - Identify the trade-off between latency and throughput
  - Set acceptable latency goals based on specific use cases
  - Decompose E2E latency into TTFT and ITL
  - Simulate real-world traffic patterns as closely as possible
  - Maintain consistency in your experiments
  - Monitoring and tracking hardware utilization
  - Avoid manipulating or inflating performance metrics
  - Continuously monitor performance in production
  - Run test suites periodically

## Summary

<!-- file: ch05.xhtml -->

## Chapter 5. Challenges When Serving LLMs

## Why Optimizing LLM Serving is Important
- Customer Experience
- Cost Efficiency
- Scalability, Peak Load Handling, and Feasibility

## The Role of Accelerator Chips in LLM Serving
- Reading GPU specs
  - GPU compute attribute
  - GPU memory attributes
  - GPU interconnect attributes
    - Intra-node interconnects
    - Inter-node interconnects
  - GPU power consumption
- Comparing the Specs of Popular GPUs

## Bottlenecks in LLM Model Loading
- The Model Loading Process
- Estimating Model Size
- Estimating KV Cache Size

## Bottlenecks in LLM Model Execution
- Boundaries of GPU Compute and Memory Bandwidth
- Arithmetic Intensity in Matrix Multiplications
- Applying Arithmetic Intensity Analysis to the LLM Prefill and Decode Phases

## Other AI Accelerators and Trends

## Summary

<!-- file: ch06.xhtml -->

## Chapter 6. Essential LLM Optimization Techniques

## Request Batching and Scheduling-Level Optimizations
- Why Do We Need Batching in Real-Time Serving?
- Dynamic Batching in Online Inference
- Continuous Batching for LLM Online Inference
- Continuous Batching with Chunked Prefill

## Scaling Attention and Kernel Optimization
- Scalable Attention Mechanisms
- Kernel Fusion and Custom Attention Kernels
  - Kernel fusion
  - FlashAttention
  - PagedAttention

## Model Compression
- Quantization
  - Quantization error
  - Storing numbers
  - How does quantization help in model serving?
  - Weight-only versus weight-and-activation quantization strategies

## How to Choose a Quantization Strategy

## FP8 Is Not Always Applicable
  - Hands-on quantization
    - Find the quantized model
    - Quantize a model yourself
    - Running benchmarks
    - Performance analysis
  - Other quantization methods
    - KV cache quantization and attention quantization
    - GGUF quantization
  - Accuracy trade-offs
  - Quantization-aware training
- Distillation
- Pruning

## Prefix Caching
- RadixAttention
- Use Cases
- Best Practices
- Scaling Prefix Cache

## Summary

<!-- file: ch07.xhtml -->

## Chapter 7. Advanced LLM Optimization Techniques

## Speculative Decoding
- Detailed Steps
- Tuning and Usage
  - Choose an existing small model
  - Use self-drafting
  - N-gram
  - Tune the number of draft tokens
  - Limitations
- Hands-on Speculative Decoding
  - Enable speculative decoding
  - Run benchmarks
  - Performance analysis

## Multi-GPU and Multi-Node Inferencing
- Data Parallelism
- Tensor Parallelism and Pipeline Parallelism
- Expert Parallelism

## Prefill-Decode Disaggregation
- Overall Architecture
- KV Cache Transfer
- When to Use

## Advanced KV Caching
- Long-Context Serving
- Cost and Latency Calculations
- Self-Hosting LLMs
  - KV cache offloading
  - KV cache compression
  - KV cache blending
- Hands-on LMCache
  - Enable LMCache and CPU offloading
  - Run benchmarks
  - Performance analysis

## Summary

<!-- file: ch08.xhtml -->

## Chapter 8. LLM Serving Frameworks

## Why We Need Specialized LLM Serving Frameworks

## vLLM
- vLLM’s Architecture
  - LLMEngine and EngineCore
  - Scheduler
  - ModelExecutor, (GPU) Worker, and ModelRunner
- Model Initialization Workflow (with Multi-Process Worker)
- Generation-Request Execution Workflow
- Scheduler Deep Dive
  - Request scheduling workflow

## Separate Prioritization and Optimization
  - Applying model optimization techniques
- vLLM’s Layered Optimization Strategy

## TensorRT-LLM

## SGLang

## Llama.cpp

## Selecting the Right Framework

## Keep an Open Mind When Evaluating Serving Frameworks

## Summary

<!-- file: ch09.xhtml -->

## Chapter 9. LLM Optimization in Practice

## Lab Code

## LLM Serving Optimization Plan

## Trade-offs Between Throughput and Latency

## Optimize Qwen3-14B serving with vLLM
- Step 1: Examine the GPU hardware
- Step 2: Generate Benchmark Traffic
- Step 3: Define Evaluation Metrics
- Step 4: Set Up the Model Serving Server
- Step 5: Benchmark the Qwen3 Model with vLLM
- Step 6: Benchmark the Quantized Qwen3 Model with vLLM
- Step 7: Apply Additional Optimization Techniques

## Exercise: Fine-Tune Your vLLM Serving

## Don’t Overtune Your Configuration
- Step 8: Benchmark the Qwen3 Model with Distributed Serving
  - Host model in a distributed setup
  - Distributed serving performance analysis

## Distributed Serving Doesn’t Always Guarantee Better Performance

## Common Optimization Trade-0ffs

## Summary

## Optimization Is Iterative

<!-- file: ch10.xhtml -->

## Chapter 10. Advancements in LLM Serving

## Semantic Caching

## Performance Profiling Strategies

## Multimodal Serving
- Multimodal Input Processing
- Architectural and System Implications

## Edge AI: Drivers and Enablers
- Specialized Low-Power Hardware
- Model Compression and Optimization
- Heterogeneous Compute
- Thermal-Aware Scheduling
- Edge–Cloud Hybrid Compute

## Multi-LoRA Serving

## Model Serving in Reinforcement Learning
- LLM Serving in RL
- Determinism in RL Serving

## Summary

<!-- file: colophon01.xhtml -->

## About the Authors

<!-- file: colophon02.xhtml -->

## Colophon

<!-- file: copyright-page01.xhtml -->

## Hands-On LLM Serving and Optimization

## Revision History for the First Edition

<!-- file: dedication01.xhtml -->

## Praise for Hands-On LLM Serving and Optimization

<!-- file: foreword01.xhtml -->

## Foreword

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

## Why LLM Serving and Optimization?

## What This Book Aims to Do

## Who Should Read This Book

## What This Book Isn’t

## How This Book Is Organized

## How to Use This Book

## What You’ll Need

## Conventions Used in This Book

## Using Code Examples

## O’Reilly Online Learning

## How to Contact Us

## Acknowledgments

<!-- file: titlepage01.xhtml -->

## Hands-On LLM Serving and Optimization
