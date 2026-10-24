# generative-ai-on-kubernetes


<!-- file: afterword01.xhtml -->

## Afterword

## What We Covered

## Final Words

<!-- file: ch01.xhtml -->

## Chapter 1. Deploying Models

## Transformer Architecture and Attention Mechanism

## “It Works on My Machine”

## Model Server

## Multimodal Models
- vLLM

## LLM Inference Optimization
- Hugging Face Text Generation Inference
- Other Model Servers
  - llama.cpp
  - NVIDIA NIM
  - SGLang

## Deploying Models to Kubernetes Manually

## Model Server Controller
- KServe
  - From InferenceService to LLMInferenceService
- Ray Serve and KubeRay

## Lessons Learned

<!-- file: ch02.xhtml -->

## Chapter 2. Model Data

## Model Data Storage Formats
- Weight-Only Formats
- Self-Contained Formats

## tokenizer.json and config.json

## The Quest for True Model Portability
- ONNX
- Safetensors
- GGUF and GGML
- Current State and Gaps

## Model Registry

## Model Experimentation and Feature Stores
- Hugging Face Model Hub
- MLflow Model Registry
- Kubeflow Model Registry
- OCI Registry

## What Is OCI?

## Accessing Model Data in Kubernetes

## Init Containers and Sidecars

## Shared Storage with PersistentVolumes

## OCI Image for Storing Model Data

## CNCF ModelPack Specification
- Modelcars
- OCI Image Volume Mounts

## Lessons Learned

<!-- file: ch03.xhtml -->

## Chapter 3. Kubernetes and GPUs

## GPU Discovery
- Node Feature Discovery
- GPU Feature Discovery

## Kubernetes GPU Device Plug-Ins

## GPU Workload Scheduling
- Label-Based Scheduling
  - nodeSelector
  - Node affinity
  - Taints and tolerations
- Resource-Based Scheduling
- Dynamic Resource Allocation

## NVIDIA GPU Operator
- Operator Configuration with ClusterPolicy
- Sub-GPU Allocation
  - Time slicing
  - Multi-Instance GPU

## GPU Diagnostics with nvidia-smi

## Multi-GPU Inference
- Data Parallelism
- Model Parallelism

## NVLink and NVSwitch: NVIDIA GPU Interconnects
  - Tensor parallelism
  - Pipeline parallelism
  - Hybrid parallelism

## Controlling Pod Placement for Multi-GPU Workloads
- Single-Node Versus Multinode Inference

## What Is NCCL and RDMA?
- GPU Resource Optimizations

## Lessons Learned

<!-- file: ch04.xhtml -->

## Chapter 4. Running in Production

## Model and Runtime Tuning
- Language Model Evaluation
- Language Model Compression

## Quantization
- Model Performance Benchmark
- vLLM Runtime Parameters Tuning

## How to Calculate Model Memory Requirements

## Autoscaling

## Optimize vLLM Startup Time

## Optimize Model Loading

## LLM-Aware Routing

## Gateway API
- From API Gateway to AI Gateway
  - Token-based rate limiting and user management
  - Evolution of AI gateway capabilities
- Gateway API Inference Extension

## Disaggregated Serving

## Lessons Learned

<!-- file: ch05.xhtml -->

## Chapter 5. Model Observability

## Observability Stack and Configuration
- Logs
- Metrics
- Tracing

## Prometheus, OpenMetrics, and OpenTelemetry

## Model Server Metrics
- Time To First Token
- Time Per Output Token or Inter-Token Latency
- Throughput
- Latency
- Request Queue Metrics

## SLI, SLO, and SLA

## GPU Usage Monitoring

## Quality Metrics

## Responsible AI
- Explainability
- Fairness

## Model Safety: Hallucination and Guardrails
- Understanding and Detecting Hallucinations
- Runtime Guardrails
  - NVIDIA NeMo Guardrails
  - FMS Guardrails Orchestrator
  - Guardrails AI
  - Llama Stack and moderation APIs

## Lessons Learned

<!-- file: ch06.xhtml -->

## Chapter 6. Model Customization

## Introduction to LLM Creation

## Model Tuning, Model Customization, and Post-Training

## Prompt and Context Engineering

## When to Use Model Customization

## Tuning a Model

## What Is Supervised Fine-Tuning?
- Fine-Tuning
- Parameter-Efficient Fine-Tuning
- Low-Rank Adaptation

## Advanced Tuning Techniques

## Running Tuning Jobs on Kubernetes
- Kubeflow Trainer

## Some YAML Magic
- Other Frameworks
  - DeepSpeed
  - Ray
  - Unsloth

## Lessons Learned

<!-- file: ch07.xhtml -->

## Chapter 7. Job Scheduling Optimization

## Kubernetes Scheduler Optimization
- Core Kubernetes Scheduler
- Resource Bin Packing Strategy
- Dynamic Scheduling with Descheduler

## Gang Scheduling
- PyTorch Rendezvous and Gang Scheduling
- Comparing Gang Scheduling Solutions
  - Coscheduling plug-in (PodGroup CRD)
  - Kueue
  - NVIDIA KAI Scheduler
  - Volcano
  - Making the right choice

## Topology-Aware Scheduling

## Communication Patterns in Distributed Training
- Comparing Topology-Aware Scheduling Solutions
  - Coscheduling plug-in (PodGroup CRD)
  - Kueue
  - NVIDIA KAI Scheduler
  - Volcano
  - Making the right choice

## Kubernetes Topology Manager
- Quota Management and Multitenancy: GPU as a Service
- Comparing Quota Management and Multitenancy Solutions
  - Kueue
  - NVIDIA KAI Scheduler
  - Volcano
  - Making the right choice

## Kueue Priority Classes and ResourceFlavor

## Network Optimization for Distributed Training

## Collective Communication Operations

## East-West and North-South Network Traffic
- Comparing Network Technologies for GPU Communication
  - NVLink and AMD Infinity Fabric
  - NVSwitch
  - InfiniBand
  - RoCE
  - Standard Ethernet
  - GPUDirect RDMA
  - Making the right choice
- Using Secondary Network Interfaces in Kubernetes

## Secondary Network Optimization and Troubleshooting
- Bridging HPC and Kubernetes: Slurm and Slinky

## Storage for Training

## Training Job Security
- Security Guidelines for Ray
- Security Guidelines for PyTorch

## Observability of Training Jobs
- Metrics Collection for Distributed Training
- Logging Across Distributed Workers
- Tracing Distributed Training Operations

## Lessons Learned

<!-- file: ch08.xhtml -->

## Chapter 8. AI-Driven Applications

## Architectural Patterns
- Kubernetes Workload Types
- Chat Applications
- Backend AI Services
  - Scheduled batch jobs
  - Continuous control loops
  - Multistep tool automation

## Retrieval-Augmented Generation
- RAG Components

## Vector Databases in a Nutshell
- Document Ingestion
- User Query Processing
- RAG on Kubernetes

## Agentic Workflows

## The ReAct Loop
- Agentic Frameworks and Runtimes
- OpenAI’s Responses API
- Agents on Kubernetes

## Emerging Kubernetes Agent Experiments
- Multiagent Systems
- Ambient Agents

## Human in the Loop

## Lessons Learned

<!-- file: ch09.xhtml -->

## Chapter 9. Running Agentic Applications in Production

## The Agentic AI Foundation

## The Model Context Protocol

## MCP Security
- Agent Impersonation (Token Passthrough)
- Service Account Delegation
  - ServiceAccounts as workload identity
  - Server identity versus agent identity
  - ServiceAccount usage
  - Making authenticated requests
  - Authentication via token validation
  - Authorization with SubjectAccessReview
  - External validation via OIDC/JWT

## OAuth2 and the Model Context Protocol
- Delegated Identity via OAuth2 Token Exchange
- Mutual TLS with SPIFFE/SPIRE (Zero-Trust)
  - How SPIFFE works for MCP
  - Deploying SPIRE on Kubernetes
  - Using SPIFFE

## MCP Gateways
  - Choosing the right security pattern

## Agent-to-Agent Protocol
- A2A complements MCP
- A2A in a Nutshell
- Running A2A on Kubernetes

## Agent State Management
- State Storage Patterns
- Choosing Between Key-Value Stores and Databases
- Checkpointing for Long-Running Agents

## Lessons Learned

<!-- file: colophon01.xhtml -->

## About the Authors

<!-- file: colophon02.xhtml -->

## Colophon

<!-- file: copyright-page01.xhtml -->

## Generative AI on Kubernetes

## Revision History for the First Edition

<!-- file: dedication01.xhtml -->

## Praise for Generative AI on Kubernetes

<!-- file: introduction01.xhtml -->

## Introduction

## Challenges of Running Generative AI at Scale

## Generative AI and LLMs

## Kubernetes for AI Workloads

## Understanding LLM Fundamentals
- How LLMs Process Text
- Tokenization and Embeddings

## Prompt, Sentence, Word, and Token
  - Tokenizer implementation
  - Embeddings
- The Two Phases of Inference
  - Prefill
  - Decode

## Overview
- Inference
- Production Readiness
- Tuning
- AI-Driven Applications

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
  - Y

<!-- file: part01.xhtml -->

## Part I. Inference

<!-- file: part02.xhtml -->

## Part II. Production Readiness

<!-- file: part03.xhtml -->

## Part III. Tuning

<!-- file: part04.xhtml -->

## Part IV. AI-Driven Apps

<!-- file: preface01.xhtml -->

## Preface

## Why We Wrote This Book

## Kubernetes

## Generative AI

## How This Book Is Structured

## Who This Book Is For

## What You Will Learn

## Conventions Used in This Book

## O’Reilly Online Learning

## How to Contact Us

## Acknowledgments

<!-- file: titlepage01.xhtml -->

## Generative AI on Kubernetes
