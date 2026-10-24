# llmops


<!-- file: ch01.xhtml -->

## Chapter 1. Introduction to Large Language Models

## Some Key Terms

## Transformer Models

## Large Language Models

## LLM Architectures
- Encoder-Only LLMs
- Decoder-Only LLMs
- Encoder–Decoder LLMs
- State Space Architectures
- Small Language Models

## Choosing an LLM
- Considerations in the Selection of an LLM
- The Big Debate: Open Source Versus Proprietary LLMs
  - Open source and open weight LLMs
  - Closed-source LLMs

## Enterprise Use Cases for LLMs
- Knowledge Retrieval
- Translation
- Speech Synthesis
- Recommender Systems
- Autonomous AI Agents
- Agentic Systems

## Ten Challenges of Building with LLMs
- 1. Size and Complexity
- 2. Training Scale and Duration
- 3. Prompt Engineering
- 4. Inference Latency and Throughput
- 5. Ethical Considerations
- 6. Resource Scaling and Orchestration
- 7. Integrations and Toolkits
- 8. Broad Applicability
- 9. Privacy and Security
- 10. Costs

## Conclusion

## References

<!-- file: ch02.xhtml -->

## Chapter 2. Introduction to LLMOps

## What Are Operational Frameworks?
- From MLOps to LLMOps: Why Do We Need a New Framework?
- Four Goals for LLMOps

## LLMOps Teams and Roles
- The LLMOps Engineer Role
- A Day in the Life
- Hiring an LLMOps Engineer Externally
- Hiring Internally: Upskilling an MLOps Engineer into an LLMOps Engineer

## LLMs and Your Organization

## The Four Goals of LLMOps
- Reliability
- Scalability
- Robustness
- Security

## The LLMOps Maturity Model

## Conclusion

## References

## Further Reading

<!-- file: ch03.xhtml -->

## Chapter 3. LLM-Based Applications

## Using AI Models in Applications

## Build Versus Buy

## Infrastructure Applications
- Agentic Workflows
- Model Context Protocol
  - MCP components
  - MCP implementation
  - Example MCP project
  - MCP and the future of large language models
- Agent-to-Agent Protocol

## The Rise of vLLMs and Multimodal LLMs

## The LLMOps Question
- Monitoring Application Performance
- Measuring a Consumer LLM Application’s Performance
- Choosing the Best Model for Your Application
- Other Application Metrics

## What Can You Control in an LLM-Based Application?
- Prompt Engineering Is “Hard”
- Did Our Prompt Engineering Produce Better Results?

## LLM-Based Infrastructure Systems Are “Harder”

## Conclusion

## References

<!-- file: ch04.xhtml -->

## Chapter 4. Data Engineering for LLMs

## Data Engineering and the Rise of LLMs

## The DataOps Engineer Role

## Data Management
- Synthetic Data
- LLM Pipelines
- Training an LLM
  - The original data engineering lifecycle
  - Emerging questions in data engineering
- Data Composition
- Scaling Laws
- Data Repetition
- Data Quality

## A General Data-Preprocessing Pipeline for LLMs
- Step 1: Catalog Your Data
- Step 2: Check Privacy and Legal Compliance
- Step 3: Filter the Data

## Cleaning Data: A Few Core Rules
- Step 4: Perform Data Deduplication

## Methods for Deduplication
- Step 5: Collect Data
- Step 6: Detect Encoding
- Step 7: Detect Languages
- Step 8: Chunking
- Step 9: Back Up Your Data
- Step 10: Perform Maintenance and Updates

## Vectorization
- Vector Databases
- Maintaining Fresh Data

## LlamaIndex
- Generating the Fine-Tuning Dataset
- Automatically Generating an Instruction Fine-Tuning Dataset

## What If Your Data Isn’t Static?

## Conclusion

## References

## Further Reading

<!-- file: ch05.xhtml -->

## Chapter 5. Model Domain Adaptation for LLM-Based Applications

## Training LLMs from Scratch
- Step 1: Pick a Task
- Step 2: Prepare the Data
- Step 3: Decide on the Model Architecture
- Step 4: Set Up Your Training Infrastructure
- Step 5: Implement Training

## Model Ensembling Approaches
- Model Averaging and Blending
- Weighted Ensembling
- Stacked Ensembling (Two-Stage Model)
- Diverse Ensembles for Robustness
- Multi-Step Decoding and Voting Mechanisms
- Composability
- Soft Actor–Critic

## Model Domain Adaptation

## Prompt Engineering
- One-Shot Prompting
- Few-Shot Prompting
- Chain-of-Thought Prompting
- Retrieval-Augmented Generation
- Semantic Kernel

## Fine-Tuning
- Adaptive Fine-Tuning
- Adapters (Single, Parallel, and Scaled Parallel)
- Behavioral Fine-Tuning
- Prefix Tuning
- Parameter-Efficient Fine-Tuning
- Instruction Tuning and Reinforcement Learning from Human Feedback
- Choosing Between Fine-Tuning and Prompt Engineering

## Mixture of Experts

## Model Optimization for Resource-Constrained Devices

## Lessons for Effective LLM Development
- Scaling Law
- Chinchilla Models
- Learning-Rate Optimization
- Speculative Sampling

## Conclusion

## References

<!-- file: ch06.xhtml -->

## Chapter 6. API-First LLM Deployment

## Quick Recommendations

## Deploying Your Model
- Step 1: Set Up Your Environment
- Step 2: Containerize the LLM
- Step 3: Automate Pipelines with Jenkins
- Step 4: Workflow Orchestration
- Step 5: Set Up Monitoring

## Developing APIs for LLMs
- API-Led Architecture Strategies
- REST APIs

## API Implementation
- Step 1: Define Your API’s Endpoints
- Step 2: Choose an API Development Framework
- Step 3: Test the API

## Credential Management

## API Gateways

## API Versioning and Lifecycle Management

## LLM Deployment Architectures
- Modular and Monolithic Architectures
- Implementing a Microservices-Based Architecture
  - Step 1: Decompose the application into its components
  - Step 2: Establish communication between services
  - Step 3: Coordinate the microservices to keep the workflows seamless
  - Step 4: Create a Dockerfile for each microservice

## Automating RAG with Retriever Re-ranker Pipelines

## Automating Knowledge Graph Updates

## Deployment Latency Optimization

## Orchestrating Multiple Models

## Choosing Between Kubernetes and Docker Swarm

## Optimizing RAG Pipelines
- Asynchronous Querying
- Combining Dense and Sparse Retrieval Methods
- Cache Embeddings
- Key–Value Caching

## Scalability and Reusability

## Conclusion

<!-- file: ch07.xhtml -->

## Chapter 7. Evaluation for LLMs

## Why Evaluation Is a Hard Problem

## Evaluating Performance
- Evaluating What Breaks Before It Breaks Everything
  - Hallucinations
  - Prompt regressions
  - Latency spikes
  - Data drift
  - Inconsistent behavior
  - Ethical and compliance risks
- Metrics for RAG Applications
- Metrics for Agentic Systems
  - Stage 1: Model development and training and integration into the agentic system
  - Stage 2: Agentic system deployment
  - Stage 3: Production

## General Evaluation Considerations
- The Value of Automated Metrics
- Model Drift

## Traditional Metrics Aren’t Enough
- The Observability Pipeline
- Preprocessing and Prompt Construction
- Retrieval in RAG Pipelines
- LLM Inference
- Postprocessing and Output Validation
- Capturing Feedback

## Conclusion

## References

<!-- file: ch08.xhtml -->

## Chapter 8. Governance: Monitoring, Privacy, and Security

## The Data Issue: Scale and Sensitivity

## Security Risks
- Prompt Injection
- Jailbreaking
- Other Security Risks

## Defensive Measures: LLMSecOps

## Conducting an LLMSecOps Audit
- Step 1: Define Scope and Objectives
  - Code maturity
  - Vulnerability management
- Step 2: Gather Information
- Step 3: Perform Risk Analysis and Threat Modeling
- Step 4: Evaluate Security Controls and Compliance
- Step 5: Perform Penetration Testing and/or Red Teaming
  - Penetration testing
  - Red teaming
- Step 6: Review the Training Data
- Step 7: Assess Model Performance and Bias
- Step 8: Document the Audit’s Findings and Recommendations
- Step 9: Plan Ongoing Monitoring and Review
- Step 10: Create a Communication and Remediation Plan

## Safety and Ethical Guardrails

## Conclusion

## References

<!-- file: ch09.xhtml -->

## Chapter 9. Scaling: Hardware, Infrastructure, and Resource Management

## Choosing the Right Approach

## Scaling and Resource Allocation

## Monitoring

## A/B Testing and Shadow Testing for LLMs

## Automatic Infrastructure Provisioning and Management
- Provisioning and Management in Cloud Architectures
- Provisioning and Management on Owned Hardware
- Best Practices for Automatic Infrastructure Management
- Scaling Law and the Compute-Optimal Argument
  - Scenario 1: Overprioritize model size
  - Scenario 2: Compute-optimal strategy

## Optimizing LLM Infrastructure
- Kernel Fusion
- Precision Scaling
- Hardware Utilization

## Parallel and Distributed Computing for LLMs
- Data Parallelism
- Model Parallelism
- Pipeline Parallelism

## Advanced Frameworks: ZeRO and DeepSpeed
- Backup and Failsafe Processes for LLM Applications
- Types of Backup Strategies
- The Most Important Practice: Test Restores Regularly

## Conclusion

## References

<!-- file: ch10.xhtml -->

## Chapter 10. The Future of LLMs and LLMOps

## Scaling Beyond Current Boundaries

## Hybrid Architectures: Merging Neural Networks with Symbolic AI
- Sparse and Mixture-of-Experts Models
- Memory-Augmented Models: Toward Persistent, Context-Rich AI
- Interpretable and Self-Optimizing Models
- Cross-Model Collaboration, Meta-Learning, and Multi-Modal Fine-Tuning
- RAG

## The Future of LLMOps
- Advances in GPU Technology
- Data Management and Efficiency
- Privacy and Security
- Comprehensive Evaluation Frameworks

## How to Succeed as an LLMOps Engineer

## Conclusion

## References

## Further Reading

<!-- file: colophon01.xhtml -->

## About the Author

<!-- file: colophon02.xhtml -->

## Colophon

<!-- file: copyright-page01.xhtml -->

## LLMOps

## Revision History for the First Edition

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

## Conventions Used in This Book

## O’Reilly Online Learning

## How to Contact Us

## Acknowledgments

<!-- file: titlepage01.xhtml -->

## LLMOps
